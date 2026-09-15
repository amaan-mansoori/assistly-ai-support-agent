"""Generate a small, explicitly limited grounded-reply experiment."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.agent.reply_generator import configured_llm_call, generate_reply
from src.agent.reply_generator import ReplyGenerationError
from src.retrieval.historical_retriever import HistoricalRetriever

GOLDEN = Path("data/golden/golden_set.csv")
OUTPUT = Path("reports/evaluation/golden_reply_generations.jsonl")
REQUIRED_OUTPUT_FIELDS = {
    "example_id", "customer_tweet_id", "customer_text", "human_intent",
    "retrieved_examples", "draft_reply", "grounding_confidence",
    "needs_human_review", "reason",
}


def load_existing_records(path: Path = OUTPUT) -> dict[str, dict[str, Any]]:
    """Load valid prior records, retaining the first record for each ID."""
    records: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return records
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (isinstance(record, dict)
                    and isinstance(record.get("example_id"), str)
                    and REQUIRED_OUTPUT_FIELDS.issubset(record)):
                records.setdefault(record["example_id"], record)
    return records


def atomic_write_records(path: Path, records: dict[str, dict[str, Any]]) -> None:
    """Replace the JSONL checkpoint atomically after a successful generation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            for record in records.values():
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def classify_failure(exc: Exception) -> tuple[bool, dict[str, Any]]:
    """Classify only errors with clear transient signals as retryable."""
    status = getattr(exc, "status_code", getattr(exc, "code", None))
    text = str(exc)
    upper = f"{type(exc).__name__} {text}".upper()
    retryable = (
        status == 429 or (isinstance(status, int) and 500 <= status <= 599)
        or "RESOURCE_EXHAUSTED" in upper or "RATE LIMIT" in upper
        or isinstance(exc, (TimeoutError, ConnectionError))
        or any(token in upper for token in ("TIMEOUT", "TIMED OUT", "NETWORK", "TRANSPORT"))
    ) and not isinstance(exc, ReplyGenerationError)
    safe_message = text
    for secret in (os.getenv("GEMINI_API_KEY"), os.getenv("OPENAI_API_KEY")):
        if secret:
            safe_message = safe_message.replace(secret, "[REDACTED]")
    return retryable, {
        "exception_type": type(exc).__name__,
        "status_code": status,
        "message": safe_message[:500],
        "retryable": retryable,
    }


def generate_rows(rows: list[dict[str, str]], retriever: Any, llm_call: Any,
                  output_path: Path = OUTPUT, k: int = 5,
                  sleep_fn: Any = time.sleep) -> tuple[int, dict[str, Any] | None]:
    """Resume generation, checkpointing each success and returning any failure ID."""
    records = load_existing_records(output_path)
    for row in rows:
        example_id = row["example_id"]
        if example_id in records:
            continue
        retrieved = retriever.retrieve(row["customer_text"], k)
        for attempt in range(3):
            try:
                reply = generate_reply(row["customer_text"], row["human_intent"], retrieved, llm_call)
                records[example_id] = {
                    "example_id": example_id, "customer_tweet_id": row["customer_tweet_id"],
                    "customer_text": row["customer_text"], "human_intent": row["human_intent"],
                    "retrieved_examples": retrieved, **reply,
                }
                atomic_write_records(output_path, records)
                break
            except Exception as exc:
                retryable, diagnostic = classify_failure(exc)
                diagnostic["attempts"] = attempt + 1
                if not retryable or attempt == 2:
                    return len(records), {"example_id": example_id, **diagnostic}
                sleep_fn(2 ** attempt)
    return len(records), None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    if args.limit < 1 or args.k < 1:
        raise SystemExit("--limit and --k must be positive")
    with GOLDEN.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))[:args.limit]
    retriever, _ = HistoricalRetriever.build()
    llm_call = configured_llm_call()
    count, failure = generate_rows(rows, retriever, llm_call, OUTPUT, args.k)
    if failure is not None:
        print(json.dumps({"records": count, "failure": failure, "output": str(OUTPUT)}),
              file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({"records": count, "k": args.k, "output": str(OUTPUT)}))


if __name__ == "__main__":
    main()

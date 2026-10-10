"""Generate a small, explicitly limited grounded-reply experiment."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
import re
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.agent.reply_generator import configured_llm_call, generate_reply
from src.agent.reply_generator import ReplyGenerationError
from src.retrieval.historical_retriever import HistoricalRetriever

GOLDEN = Path("data/golden/golden_set.csv")
OUTPUT = Path("reports/evaluation/golden_reply_generations.jsonl")
GENERATION_SCHEMA_VERSION = "assistly-reply-generation-v2"
REQUIRED_OUTPUT_FIELDS = {
    "example_id", "human_intent",
    "retrieved_examples", "draft_reply", "grounding_confidence",
    "needs_human_review",
}
SAFE_GENERATION_FIELDS = {
    "example_id",
    "human_intent",
    "retrieved_examples",
    "draft_reply",
    "grounding_confidence",
    "needs_human_review",
}
SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]+=*", re.IGNORECASE),
    re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)"),
)
SAFE_EVIDENCE_FIELDS = {
    "response_tweet_id",
    "amazonhelp_response",
    "similarity",
    "score_components",
    "retrieval_backend",
    "candidate_count",
    "candidate_count_scope",
}


def _sanitize_text(value: Any, private_text: tuple[str, ...]) -> Any:
    if not isinstance(value, str):
        return value
    sanitized = value
    for private_value in private_text:
        if private_value:
            sanitized = sanitized.replace(private_value, "[REDACTED]")
    for pattern in SENSITIVE_TEXT_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    return sanitized


def sanitize_generation_record(
    record: dict[str, Any],
    customer_text: str = "",
    conversation_context: str = "",
) -> dict[str, Any]:
    """Keep evaluation evidence while excluding customer text and identifiers."""
    if not REQUIRED_OUTPUT_FIELDS.issubset(record):
        raise ValueError("generation record is missing required evaluation fields")
    confidence = record.get("grounding_confidence")
    if (
        not isinstance(record.get("human_intent"), str)
        or not record["human_intent"]
        or not isinstance(record.get("draft_reply"), str)
        or isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not math.isfinite(confidence)
        or not 0 <= confidence <= 1
        or not isinstance(record.get("needs_human_review"), bool)
    ):
        raise ValueError("generation record contains invalid evaluation fields")
    sanitized = {
        key: value for key, value in record.items()
        if key in SAFE_GENERATION_FIELDS
    }
    evidence = sanitized.get("retrieved_examples")
    if not isinstance(evidence, list) or any(
        not isinstance(row, dict) for row in evidence
    ):
        raise ValueError("generation records must contain retrieved_examples")
    private_text = tuple(
        value for value in (customer_text, conversation_context) if value
    )
    sanitized["retrieved_examples"] = [
        {
            key: _sanitize_text(value, private_text)
            for key, value in row.items()
            if key in SAFE_EVIDENCE_FIELDS
        }
        for row in evidence
    ]
    sanitized["draft_reply"] = _sanitize_text(
        sanitized["draft_reply"], private_text
    )
    sanitized["artifact_schema_version"] = GENERATION_SCHEMA_VERSION
    return sanitized


def _record_fields(record: Any) -> set[str]:
    fields: set[str] = set()
    if isinstance(record, dict):
        fields.update(record)
        for value in record.values():
            fields.update(_record_fields(value))
    elif isinstance(record, list):
        for value in record:
            fields.update(_record_fields(value))
    return fields


def sanitize_legacy_artifact(
    input_path: Path,
    output_path: Path,
    customer_text_by_id: dict[str, str] | None = None,
) -> dict[str, int]:
    """Migrate JSONL atomically, preserving every unique, valid record."""
    if output_path.resolve() != input_path.resolve() and output_path.exists():
        raise ValueError(
            f"{output_path} already exists; migration will not replace an existing artifact"
        )
    records: dict[str, dict[str, Any]] = {}
    removed_fields: set[str] = set()
    with input_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{input_path}:{line_number} is not valid JSON; input was not changed"
                ) from exc
            if (
                not isinstance(record, dict)
                or not isinstance(record.get("example_id"), str)
                or not record["example_id"]
                or not REQUIRED_OUTPUT_FIELDS.issubset(record)
            ):
                raise ValueError(
                    f"{input_path}:{line_number} is not a supported generation record"
                )
            example_id = record["example_id"]
            if example_id in records:
                raise ValueError(
                    f"{input_path}:{line_number} duplicates an example_id; input was not changed"
                )
            sanitized = sanitize_generation_record(
                record,
                customer_text=(customer_text_by_id or {}).get(example_id, ""),
            )
            removed_fields.update(
                _record_fields(record) - _record_fields(sanitized)
            )
            records[example_id] = sanitized
    if not records:
        raise ValueError(f"{input_path} contains no generation records")
    atomic_write_records(output_path, records)
    return {"records": len(records), "removed_field_names": len(removed_fields)}


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
                records.setdefault(record["example_id"], sanitize_generation_record(record))
    return records


def atomic_write_records(path: Path, records: dict[str, dict[str, Any]]) -> None:
    """Replace the JSONL checkpoint atomically after a successful generation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            for record in records.values():
                safe_record = sanitize_generation_record(record)
                handle.write(json.dumps(safe_record, ensure_ascii=False) + "\n")
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
    if status is not None and (
        isinstance(status, bool) or not isinstance(status, int)
    ):
        status = None
    category = (
        "rate_limited" if status == 429 or "RESOURCE_EXHAUSTED" in upper
        or "RATE LIMIT" in upper
        else "provider_server_error" if isinstance(status, int) and status >= 500
        else "provider_client_error" if isinstance(status, int) and 400 <= status < 500
        else "timeout" if isinstance(exc, TimeoutError)
        or "TIMEOUT" in upper or "TIMED OUT" in upper
        else "network_error" if isinstance(exc, ConnectionError)
        or "NETWORK" in upper or "TRANSPORT" in upper
        else "generation_error"
    )
    return retryable, {
        "exception_type": type(exc).__name__,
        "status_code": status,
        "category": category,
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
                records[example_id] = sanitize_generation_record({
                    "example_id": example_id,
                    "human_intent": row["human_intent"],
                    "retrieved_examples": retrieved,
                    **reply,
                }, row["customer_text"], row.get("conversation_context", ""))
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
    parser.add_argument(
        "--sanitize-legacy",
        action="store_true",
        help="Safely remove customer text from an existing generation JSONL artifact.",
    )
    parser.add_argument("--input", type=Path, default=OUTPUT)
    parser.add_argument(
        "--output",
        type=Path,
        help="Sanitized artifact destination; defaults to atomically replacing --input.",
    )
    args = parser.parse_args()
    if args.sanitize_legacy:
        customer_text_by_id: dict[str, str] = {}
        if args.input == OUTPUT and GOLDEN.exists():
            with GOLDEN.open(encoding="utf-8", newline="") as handle:
                customer_text_by_id = {
                    row["example_id"]: row["customer_text"]
                    for row in csv.DictReader(handle)
                    if row.get("example_id") and row.get("customer_text")
                }
        summary = sanitize_legacy_artifact(
            args.input, args.output or args.input, customer_text_by_id
        )
        print(json.dumps({
            "sanitized": True,
            "artifact_schema_version": GENERATION_SCHEMA_VERSION,
            **summary,
        }))
        return
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

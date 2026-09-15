"""Offline, deterministic reply-quality metrics for generated reply JSONL."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable

from src.evaluation.grounding import evaluate_evidence

DEFAULT_INPUT = Path("reports/evaluation/golden_reply_generations.jsonl")
DEFAULT_OUTPUT = Path("reports/evaluation/reply_quality_offline.json")
DEFAULT_REFERENCES = Path("data/golden/golden_set.csv")
TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSON objects from JSONL, rejecting malformed records clearly."""
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} is not valid JSON") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            rows.append(value)
    return rows


def load_reference_replies(path: Path = DEFAULT_REFERENCES) -> dict[str, str]:
    """Load optional human/historical reply text keyed by example ID."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            row["example_id"]: row.get("amazonhelp_response", "")
            for row in csv.DictReader(handle)
            if row.get("example_id")
        }


def _tokens(text: Any) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(str(text or ""))}


def _overlap(reply: str, reference: str) -> float:
    reply_tokens = _tokens(reply)
    reference_tokens = _tokens(reference)
    return len(reply_tokens & reference_tokens) / len(reply_tokens) if reply_tokens else 0.0


def evaluate_reply_quality(
    records: Iterable[dict[str, Any]],
    references: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compute simple reference-free metrics and optional lexical reference overlap."""
    records = list(records)
    evidence = evaluate_evidence(records)
    per_example = {row["example_id"]: row for row in evidence["per_example"]
                   if row.get("example_id") is not None}
    overlaps: list[float] = []
    for record in records:
        draft = str(record.get("draft_reply") or "").strip()
        if references and record.get("example_id") in references:
            overlaps.append(_overlap(draft, references[record["example_id"]]))
        row = per_example.get(record.get("example_id"))
        if row is not None:
            row["word_count"] = len(str(draft).split())
            row["grounding_confidence"] = record.get("grounding_confidence")
            row["needs_human_review"] = bool(record.get("needs_human_review", False))
    n = len(records)
    non_empty = sum(bool(str(row.get("draft_reply") or "").strip()) for row in records)
    reviewed = sum(bool(row.get("needs_human_review", False)) for row in records)
    confidences = [
        float(row["grounding_confidence"]) for row in records
        if isinstance(row.get("grounding_confidence"), (int, float))
    ]
    word_counts = [len(str(row.get("draft_reply") or "").split()) for row in records]
    result: dict[str, Any] = {
        "metric_version": "offline-v1",
        "input_examples": n,
        "non_empty_reply_rate": round(non_empty / n, 6) if n else 0.0,
        "mean_reply_word_count": round(sum(word_counts) / n, 6) if n else 0.0,
        "mean_reported_grounding_confidence": (
            round(sum(confidences) / len(confidences), 6) if confidences else None
        ),
        "human_review_rate": round(reviewed / n, 6) if n else 0.0,
        "reference_replies_available": len(overlaps),
        "mean_reference_token_overlap": (
            round(sum(overlaps) / len(overlaps), 6) if overlaps else None
        ),
        "evidence": {
            key: value for key, value in evidence.items() if key != "per_example"
        },
        "per_example": list(per_example.values()),
    }
    return result


def write_report(metrics: dict[str, Any], output: Path = DEFAULT_OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute offline reply-quality metrics.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--references", type=Path, default=DEFAULT_REFERENCES)
    parser.add_argument("--no-references", action="store_true")
    args = parser.parse_args()
    records = load_jsonl(args.input)
    references = {} if args.no_references else load_reference_replies(args.references)
    metrics = evaluate_reply_quality(records, references)
    write_report(metrics, args.output)
    print(json.dumps({key: value for key, value in metrics.items() if key != "per_example"}, indent=2))


if __name__ == "__main__":
    main()


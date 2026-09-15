"""Agreement metrics for a primary and an independent annotation export."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

DEFAULT_PRIMARY = Path("data/golden/golden_set.csv")
DEFAULT_OUTPUT = Path("reports/evaluation/human_agreement.json")
ID_FIELDS = ("example_id", "id", "customer_tweet_id")
LABEL_FIELDS = ("human_intent", "intent", "label", "annotation")


def _field(rows: list[dict[str, Any]], candidates: tuple[str, ...], explicit: str | None) -> str:
    if explicit:
        if rows and explicit not in rows[0]:
            raise ValueError(f"annotation field {explicit!r} is not present")
        return explicit
    for candidate in candidates:
        if rows and candidate in rows[0]:
            return candidate
    raise ValueError(f"could not find annotation field; tried {', '.join(candidates)}")


def load_annotations(
    path: Path, id_field: str | None = None, label_field: str | None = None
) -> dict[str, str]:
    """Load labels from CSV or JSONL, requiring a stable example identifier."""
    rows: list[dict[str, Any]] = []
    if path.suffix.lower() == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number} is not valid JSON") from exc
                if not isinstance(row, dict):
                    raise ValueError(f"{path}:{line_number} must contain an object")
                rows.append(row)
    else:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = [dict(row) for row in csv.DictReader(handle)]
    if not rows:
        return {}
    id_name = _field(rows, ID_FIELDS, id_field)
    label_name = _field(rows, LABEL_FIELDS, label_field)
    result: dict[str, str] = {}
    for row in rows:
        key = str(row.get(id_name, "")).strip()
        label = str(row.get(label_name, "")).strip()
        if not key or not label:
            raise ValueError(f"{path} contains a missing ID or label")
        if key in result:
            raise ValueError(f"{path} contains duplicate ID {key!r}")
        result[key] = label
    return result


def cohen_kappa(first: list[str], second: list[str]) -> float | None:
    """Compute unweighted Cohen kappa, returning None for a degenerate case."""
    if len(first) != len(second):
        raise ValueError("annotation vectors must have equal length")
    if not first:
        return None
    observed = sum(a == b for a, b in zip(first, second)) / len(first)
    first_counts, second_counts = Counter(first), Counter(second)
    labels = set(first_counts) | set(second_counts)
    expected = sum(
        (first_counts[label] / len(first)) * (second_counts[label] / len(second))
        for label in labels
    )
    if expected == 1.0:
        return None
    return (observed - expected) / (1.0 - expected)


def measure_agreement(primary: Mapping[str, str], secondary: Mapping[str, str]) -> dict[str, Any]:
    """Align annotations by ID and report raw agreement and Cohen kappa."""
    common_ids = sorted(set(primary) & set(secondary))
    first = [primary[key] for key in common_ids]
    second = [secondary[key] for key in common_ids]
    disagreements = [
        {"example_id": key, "primary": a, "secondary": b}
        for key, a, b in zip(common_ids, first, second) if a != b
    ]
    agreed = sum(a == b for a, b in zip(first, second))
    return {
        "examples_primary": len(primary),
        "examples_secondary": len(secondary),
        "matched_examples": len(common_ids),
        "unmatched_primary": len(set(primary) - set(secondary)),
        "unmatched_secondary": len(set(secondary) - set(primary)),
        "raw_agreement_count": agreed,
        "raw_agreement": agreed / len(common_ids) if common_ids else None,
        "cohen_kappa": cohen_kappa(first, second),
        "labels": sorted(set(first) | set(second)),
        "disagreements": disagreements,
    }


def write_report(report: dict[str, Any], output: Path = DEFAULT_OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure agreement between two annotation exports.")
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY)
    parser.add_argument("--secondary", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--primary-id-field")
    parser.add_argument("--primary-label-field")
    parser.add_argument("--secondary-id-field")
    parser.add_argument("--secondary-label-field")
    args = parser.parse_args()
    primary = load_annotations(args.primary, args.primary_id_field, args.primary_label_field)
    secondary = load_annotations(args.secondary, args.secondary_id_field, args.secondary_label_field)
    report = measure_agreement(primary, secondary)
    write_report(report, args.output)
    print(json.dumps({key: report[key] for key in (
        "matched_examples", "raw_agreement", "cohen_kappa"
    )}, indent=2))


if __name__ == "__main__":
    main()


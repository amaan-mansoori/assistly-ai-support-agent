"""Evaluate a deterministic majority-class baseline on the finalized golden set."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, cast

from numpy.typing import NDArray
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from src.evaluation.dataset_manifest import DEFAULT_MANIFEST, verify_dataset

GOLDEN_SET = Path("data/golden/golden_set.csv")
JSON_REPORT = Path("reports/evaluation/trivial_baseline.json")
MARKDOWN_REPORT = Path("reports/evaluation/trivial_baseline.md")
EXPECTED_ROWS = 220
ALLOWED_LABELS = (
    "delivery_status_delay",
    "delivery_marked_delivered_missing",
    "return_refund",
    "item_condition_or_fulfilment",
    "order_cancellation_or_change",
    "prime_membership",
    "account_access_security",
    "payment_charge_issue",
    "product_availability_pricing",
    "marketplace_seller",
    "other_unclear",
)


def load_labels(path: Path = GOLDEN_SET) -> list[str]:
    """Load and validate the provisional evaluation labels."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} evaluation examples, found {len(rows)}")
    labels = [row.get("human_intent", "") for row in rows]
    if any(not label for label in labels):
        raise ValueError("Golden set contains missing human_intent values")
    invalid = sorted(set(labels) - set(ALLOWED_LABELS))
    if invalid:
        raise ValueError(f"Golden set contains invalid labels: {invalid}")
    return labels


def majority_class(labels: Iterable[str]) -> tuple[str, int]:
    """Return the most frequent label and count, with deterministic tie-breaking."""
    counts = Counter(labels)
    if not counts:
        raise ValueError("Cannot select a majority class from empty labels")
    label, count = min(counts.items(), key=lambda item: (-item[1], item[0]))
    return label, count


def evaluate(labels: list[str]) -> dict[str, object]:
    """Evaluate constant majority predictions and return serializable metrics."""
    label, count = majority_class(labels)
    predictions = [label] * len(labels)
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, predictions, labels=list(ALLOWED_LABELS), average=None, zero_division=0
    )
    if support is None:
        raise RuntimeError("per-intent metrics did not return class-level values")
    precision_values = cast(NDArray[Any], precision)
    recall_values = cast(NDArray[Any], recall)
    f1_values = cast(NDArray[Any], f1)
    support_values = cast(NDArray[Any], support)
    per_intent: dict[str, dict[str, float | int]] = {
        intent: {
            "precision": float(precision_values[index]),
            "recall": float(recall_values[index]),
            "f1": float(f1_values[index]),
            "support": int(support_values[index]),
        }
        for index, intent in enumerate(ALLOWED_LABELS)
    }
    return {
        "number_of_evaluation_examples": len(labels),
        "majority_class": label,
        "majority_class_count": count,
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, labels=list(ALLOWED_LABELS), average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(labels, predictions, labels=list(ALLOWED_LABELS), average="weighted", zero_division=0)),
        "per_intent": per_intent,
    }


def write_reports(metrics: dict[str, object], json_path: Path = JSON_REPORT,
                  markdown_path: Path = MARKDOWN_REPORT) -> None:
    """Write machine-readable and concise human-readable evaluation reports."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    per_intent = metrics["per_intent"]
    if not isinstance(per_intent, dict):
        raise TypeError("majority baseline per_intent metrics must be an object")
    lines = [
        "# Trivial Majority-Class Baseline",
        "",
        "This baseline predicts the single most frequent `human_intent` for every example.",
        "It uses no customer text, context, candidate stratum, or other feature.",
        "",
        f"- Evaluation examples: **{metrics['number_of_evaluation_examples']}**",
        f"- Majority class: **`{metrics['majority_class']}`**",
        f"- Majority-class count: **{metrics['majority_class_count']}**",
        f"- Accuracy: **{metrics['accuracy']:.6f}**",
        f"- Macro F1: **{metrics['macro_f1']:.6f}**",
        f"- Weighted F1: **{metrics['weighted_f1']:.6f}**",
        "",
        "## Per-intent metrics",
        "",
        "| Intent | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for intent in ALLOWED_LABELS:
        values = per_intent[intent]
        lines.append(
            f"| `{intent}` | {values['precision']:.6f} | {values['recall']:.6f} | "
            f"{values['f1']:.6f} | {values['support']} |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    _, rows = verify_dataset(GOLDEN_SET, DEFAULT_MANIFEST)
    labels = [row["human_intent"] for row in rows]
    metrics = evaluate(labels)
    write_reports(metrics)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

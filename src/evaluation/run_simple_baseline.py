"""Evaluate a deterministic TF-IDF plus Logistic Regression text baseline."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.intents.final_taxonomy_audit import classify_intent
from src.intents.refine_taxonomy import clean_customer_text, detect_language

INTERIM = Path("data/interim/amazonhelp_conversations.csv")
GOLDEN_SET = Path("data/golden/golden_set.csv")
JSON_REPORT = Path("reports/evaluation/simple_baseline.json")
MARKDOWN_REPORT = Path("reports/evaluation/simple_baseline.md")
EXPECTED_EVALUATION_ROWS = 220
ALLOWED_LABELS = (
    "delivery_status_delay", "delivery_marked_delivered_missing", "return_refund",
    "item_condition_or_fulfilment", "order_cancellation_or_change", "prime_membership",
    "account_access_security", "payment_charge_issue", "product_availability_pricing",
    "marketplace_seller", "other_unclear",
)


def _normalise(text: str) -> str:
    text = re.sub(r"@\S+|https?://\S+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def load_evaluation_rows(path: Path = GOLDEN_SET) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_EVALUATION_ROWS:
        raise ValueError(f"Expected {EXPECTED_EVALUATION_ROWS} evaluation examples, found {len(rows)}")
    labels = [row.get("human_intent", "") for row in rows]
    if any(not label for label in labels):
        raise ValueError("Golden set contains missing human_intent values")
    invalid = sorted(set(labels) - set(ALLOWED_LABELS))
    if invalid:
        raise ValueError(f"Golden set contains invalid labels: {invalid}")
    return rows


def load_training_rows(
    path: Path = INTERIM, evaluation_rows: list[dict[str, str]] | None = None
) -> tuple[list[str], list[str], dict[str, int]]:
    """Build pseudo-labelled, non-golden training data using the existing local taxonomy."""
    evaluation_rows = evaluation_rows or load_evaluation_rows()
    held_out_ids = {row["customer_tweet_id"] for row in evaluation_rows}
    held_out_text = {_normalise(row["customer_text"]) for row in evaluation_rows}
    texts: list[str] = []
    labels: list[str] = []
    filtered = {"total_interim_rows": 0, "golden_id_excluded": 0, "duplicate_text_excluded": 0,
                "non_english_or_unusable_excluded": 0, "unmapped_label_excluded": 0}
    seen: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            filtered["total_interim_rows"] += 1
            text = row.get("customer_text", "")
            if row.get("customer_tweet_id", "") in held_out_ids:
                filtered["golden_id_excluded"] += 1
                continue
            key = _normalise(text)
            if key in held_out_text or key in seen:
                filtered["duplicate_text_excluded"] += 1
                continue
            clean, usable = clean_customer_text(text)
            if not usable or detect_language(text) != "en":
                filtered["non_english_or_unusable_excluded"] += 1
                continue
            label = classify_intent(text)
            if label not in ALLOWED_LABELS:
                filtered["unmapped_label_excluded"] += 1
                continue
            seen.add(key)
            texts.append(clean)
            labels.append(label)
    if len(set(labels)) < 2:
        raise ValueError("Training data must contain at least two mapped classes")
    return texts, labels, filtered


def evaluate(
    training_texts: list[str], training_labels: list[str],
    evaluation_rows: list[dict[str, str]],
) -> tuple[dict[str, Any], list[str]]:
    vectorizer = TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2))
    x_train = vectorizer.fit_transform(training_texts)
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(x_train, training_labels)
    predictions = model.predict(vectorizer.transform([row["customer_text"] for row in evaluation_rows])).tolist()
    truth = [row["human_intent"] for row in evaluation_rows]
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predictions, labels=list(ALLOWED_LABELS), zero_division=0
    )
    per_intent = {
        intent: {"precision": float(precision[i]), "recall": float(recall[i]),
                 "f1": float(f1[i]), "support": int(support[i])}
        for i, intent in enumerate(ALLOWED_LABELS)
    }
    matrix = confusion_matrix(truth, predictions, labels=list(ALLOWED_LABELS)).tolist()
    return {
        "number_of_training_examples": len(training_texts),
        "number_of_evaluation_examples": len(evaluation_rows),
        "number_of_classes_used_for_training": len(model.classes_),
        "training_classes": list(model.classes_),
        "accuracy": float(accuracy_score(truth, predictions)),
        "macro_f1": float(f1_score(truth, predictions, labels=list(ALLOWED_LABELS), average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(truth, predictions, labels=list(ALLOWED_LABELS), average="weighted", zero_division=0)),
        "per_intent": per_intent,
        "confusion_matrix_labels": list(ALLOWED_LABELS),
        "confusion_matrix": matrix,
    }, predictions


def write_reports(metrics: dict[str, Any], filtered: dict[str, int],
                  json_path: Path = JSON_REPORT, markdown_path: Path = MARKDOWN_REPORT) -> None:
    metrics = dict(metrics)
    metrics["training_filtering"] = filtered
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Simple TF-IDF + Logistic Regression Baseline", "",
        "The finalized golden set was held out entirely from training and used only for final evaluation.",
        f"Training data came from `{INTERIM}`. The interim file has no human label column, so labels were",
        "derived only for training by the existing deterministic local taxonomy heuristic; these are not golden labels.",
        "", f"- Training examples: **{metrics['number_of_training_examples']}**",
        f"- Evaluation examples: **{metrics['number_of_evaluation_examples']}**",
        f"- Training classes: **{metrics['number_of_classes_used_for_training']}**",
        f"- Accuracy: **{metrics['accuracy']:.6f}**", f"- Macro F1: **{metrics['macro_f1']:.6f}**",
        f"- Weighted F1: **{metrics['weighted_f1']:.6f}**", "",
        "## Preprocessing and filtering", "",
        "Customer text was lightly cleaned (mentions/URLs removed, whitespace normalized), then represented",
        "with word-level unigram/bigram TF-IDF. A LogisticRegression classifier used `random_state=42`.",
        "Rows were filtered for English/usable text, duplicate text, golden IDs/text, and labels outside the approved taxonomy.",
        "", "## Per-intent metrics", "", "| Intent | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for intent in ALLOWED_LABELS:
        v = metrics["per_intent"][intent]
        lines.append(f"| `{intent}` | {v['precision']:.6f} | {v['recall']:.6f} | {v['f1']:.6f} | {v['support']} |")
    lines += ["", "## Confusion matrix", "", "Rows are true labels and columns are predicted labels, in this order:",
              ", ".join(f"`{x}`" for x in ALLOWED_LABELS), "", "```json",
              json.dumps(metrics["confusion_matrix"], indent=2), "```"]
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    evaluation_rows = load_evaluation_rows()
    training_texts, training_labels, filtered = load_training_rows(evaluation_rows=evaluation_rows)
    metrics, _ = evaluate(training_texts, training_labels, evaluation_rows)
    write_reports(metrics, filtered)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

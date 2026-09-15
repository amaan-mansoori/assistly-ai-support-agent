"""Focused tests for the leakage-safe text baseline."""
import json
from pathlib import Path

from src.evaluation.run_simple_baseline import (
    ALLOWED_LABELS,
    evaluate,
    load_evaluation_rows,
    load_training_rows,
    write_reports,
)


def test_golden_set_and_training_are_disjoint():
    evaluation = load_evaluation_rows()
    texts, _, _ = load_training_rows(evaluation_rows=evaluation)
    golden_texts = {row["customer_text"].lower() for row in evaluation}
    assert len(evaluation) == 220
    assert not any(text.lower() in golden_texts for text in texts)


def test_evaluation_labels_are_valid():
    rows = load_evaluation_rows()
    assert all(row["human_intent"] in ALLOWED_LABELS for row in rows)


def test_predictions_cover_all_evaluation_examples():
    rows = load_evaluation_rows()
    train_texts, train_labels, _ = load_training_rows(evaluation_rows=rows)
    metrics, predictions = evaluate(train_texts, train_labels, rows)
    assert len(predictions) == 220
    assert metrics["number_of_evaluation_examples"] == 220


def test_reports_and_metrics_are_consistent(tmp_path: Path):
    metrics, _ = evaluate(
        ["late package", "refund requested", "late delivery"],
        ["delivery_status_delay", "return_refund", "delivery_status_delay"],
        [{"customer_text": "late package", "human_intent": "delivery_status_delay"}],
    )
    # The helper is tested with a real evaluation-sized dataset elsewhere; this
    # check focuses on report serialization and metric shape.
    metrics["number_of_evaluation_examples"] = 1
    json_path, md_path = tmp_path / "result.json", tmp_path / "result.md"
    write_reports(metrics, {"total_interim_rows": 3}, json_path, md_path)
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["accuracy"] == metrics["accuracy"]
    assert len(loaded["confusion_matrix"]) == len(ALLOWED_LABELS)
    assert md_path.exists()

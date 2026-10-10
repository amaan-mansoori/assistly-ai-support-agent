"""Focused tests for the leakage-safe text baseline."""
import csv
import json
from pathlib import Path

from src.evaluation.run_simple_baseline import (
    ALLOWED_LABELS,
    evaluate,
    load_evaluation_rows,
    load_training_rows,
    write_reports,
)


def _write_training_fixture(path: Path, evaluation_rows: list[dict[str, str]]) -> None:
    """Write synthetic training rows; CI must not require ignored source data."""
    fields = (
        "customer_tweet_id",
        "customer_author_id",
        "customer_created_at",
        "customer_text",
        "brand_tweet_id",
        "brand_created_at",
        "brand_text",
        "brand_reply_count",
    )
    rows = [
        {
            "customer_tweet_id": "fixture-delivery",
            "customer_text": "My package delivery is late and I need help",
        },
        {
            "customer_tweet_id": "fixture-refund",
            "customer_text": "I need a refund after returning my item please",
        },
        {
            "customer_tweet_id": "fixture-duplicate",
            "customer_text": "MY package delivery is late and I need help",
        },
        {
            "customer_tweet_id": evaluation_rows[0]["customer_tweet_id"],
            "customer_text": evaluation_rows[0]["customer_text"],
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_golden_set_and_training_are_disjoint(tmp_path: Path):
    evaluation = load_evaluation_rows()
    training_path = tmp_path / "synthetic_training.csv"
    _write_training_fixture(training_path, evaluation)
    texts, labels, filtered = load_training_rows(
        path=training_path, evaluation_rows=evaluation
    )
    golden_texts = {row["customer_text"].lower() for row in evaluation}
    assert len(evaluation) == 220
    assert not any(text.lower() in golden_texts for text in texts)
    assert len(texts) == 2
    assert len(set(labels)) == 2
    assert filtered["golden_id_excluded"] == 1
    assert filtered["duplicate_text_excluded"] == 1


def test_evaluation_labels_are_valid():
    rows = load_evaluation_rows()
    assert all(row["human_intent"] in ALLOWED_LABELS for row in rows)


def test_predictions_cover_all_evaluation_examples(tmp_path: Path):
    rows = load_evaluation_rows()
    training_path = tmp_path / "synthetic_training.csv"
    _write_training_fixture(training_path, rows)
    train_texts, train_labels, _ = load_training_rows(
        path=training_path, evaluation_rows=rows
    )
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
    metrics["run_metadata"] = {
        "dataset_sha256": "dataset-hash",
        "dataset_manifest_sha256": "manifest-hash",
        "timestamp_utc": "2026-10-01T00:00:00+00:00",
        "dataset_provenance_status": "unresolved_provisional",
    }
    json_path, md_path = tmp_path / "result.json", tmp_path / "result.md"
    write_reports(metrics, {"total_interim_rows": 3}, json_path, md_path)
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["accuracy"] == metrics["accuracy"]
    assert len(loaded["confusion_matrix"]) == len(ALLOWED_LABELS)
    assert md_path.exists()
    assert "manifest-hash" in md_path.read_text(encoding="utf-8")

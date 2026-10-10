"""Focused tests for the trivial majority-class evaluation baseline."""
from pathlib import Path

import pytest

from src.evaluation.run_trivial_baseline import (
    ALLOWED_LABELS,
    evaluate,
    load_labels,
    majority_class,
    write_reports,
)


def test_majority_class_is_deterministic_on_ties():
    assert majority_class(["z", "a", "z", "a"]) == ("a", 2)


def test_evaluate_constant_predictions():
    labels = ["delivery_status_delay"] * 3 + ["return_refund"]
    metrics = evaluate(labels)
    assert metrics["majority_class"] == "delivery_status_delay"
    assert metrics["majority_class_count"] == 3
    assert metrics["number_of_evaluation_examples"] == 4
    assert metrics["accuracy"] == 0.75
    assert metrics["per_intent"]["return_refund"]["support"] == 1


def test_load_final_golden_set():
    labels = load_labels()
    assert len(labels) == 220
    assert all(label in ALLOWED_LABELS for label in labels)
    assert all(labels)


def test_load_labels_rejects_missing_and_invalid(tmp_path: Path):
    path = tmp_path / "golden.csv"
    path.write_text("human_intent\n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Expected 220"):
        load_labels(path)


def test_reports_are_written(tmp_path: Path):
    metrics = evaluate(["delivery_status_delay", "return_refund"])
    metrics["run_metadata"] = {
        "dataset_sha256": "dataset-hash",
        "dataset_manifest_sha256": "manifest-hash",
        "timestamp_utc": "2026-10-01T00:00:00+00:00",
        "dataset_provenance_status": "unresolved_provisional",
    }
    json_path = tmp_path / "result.json"
    markdown_path = tmp_path / "result.md"
    write_reports(metrics, json_path, markdown_path)
    assert json_path.exists()
    assert markdown_path.exists()
    assert "majority_class" in json_path.read_text(encoding="utf-8")
    assert "Per-intent metrics" in markdown_path.read_text(encoding="utf-8")
    assert "manifest-hash" in markdown_path.read_text(encoding="utf-8")

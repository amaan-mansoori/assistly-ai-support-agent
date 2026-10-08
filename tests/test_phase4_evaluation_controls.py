import csv
import json
from pathlib import Path

import pytest

from src.evaluation.dataset_manifest import (
    EXPECTED_COLUMNS,
    sha256_file,
    verify_dataset,
)
from src.evaluation.regression_gate import compare_reports


def _manifest(dataset: Path) -> dict:
    return {
        "dataset_version": "fixture-v1",
        "dataset_path": dataset.as_posix(),
        "sha256": sha256_file(dataset),
        "row_count": 1,
        "schema_version": "1",
        "columns": list(EXPECTED_COLUMNS),
        "provenance_status": "unresolved_provisional",
    }


def test_repository_frozen_dataset_matches_manifest():
    manifest, rows = verify_dataset(
        Path("data/golden/golden_set.csv"),
        Path("reports/evaluation/evaluation_dataset_manifest.json"),
    )
    assert manifest["row_count"] == len(rows) == 220
    assert manifest["provenance_status"] == "unresolved_provisional"
    assert len(manifest["sha256"]) == 64


def test_dataset_hash_drift_fails_closed(tmp_path: Path):
    dataset = tmp_path / "golden.csv"
    with dataset.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerow(dict.fromkeys(EXPECTED_COLUMNS, ""))
    manifest = _manifest(dataset)
    manifest["sha256"] = "0" * 64
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_dataset(dataset, manifest_path)


def _run_report(*, accuracy=0.8, recall=0.5, run_mode="deterministic_mock"):
    return {
        "run_metadata": {
            "dataset_sha256": "frozen-hash",
            "dataset_version": "fixture-v1",
            "evaluator_version": "integrated-evaluator-v2",
            "prompt_version": "assistly-support-prompt-v2",
            "retrieval_backend": "tfidf",
            "run_mode": run_mode,
            "provider": "deterministic_mock",
            "model": None,
            "examples_evaluated": 10,
            "configuration": {"limit": 10},
        },
        "metrics": {
            "intent_accuracy": {"value": accuracy},
            "retrieval_same_intent_recall_proxy_at_k": {
                "5": {"value": recall}
            },
            "unsupported_claim_rate": {"value": 0.1},
        },
    }


def test_regression_gate_passes_within_configured_tolerance():
    thresholds = {
        "metrics": {
            "accuracy": {
                "path": "metrics.intent_accuracy",
                "direction": "higher_is_better",
                "max_degradation": 0.05,
            }
        }
    }
    result = compare_reports(
        _run_report(accuracy=0.8),
        _run_report(accuracy=0.76),
        thresholds,
    )
    assert result["compatible"] is True
    assert result["passed"] is True


def test_regression_gate_fails_for_degradation_and_missing_metric():
    thresholds = {
        "metrics": {
            "accuracy": {
                "path": "metrics.intent_accuracy",
                "direction": "higher_is_better",
                "max_degradation": 0.02,
            },
            "required": {
                "path": "metrics.not_measured",
                "direction": "higher_is_better",
                "max_degradation": 0,
            },
        }
    }
    result = compare_reports(
        _run_report(accuracy=0.8),
        _run_report(accuracy=0.7),
        thresholds,
    )
    assert result["passed"] is False
    assert result["checks"][0]["status"] == "threshold_exceeded"
    assert result["checks"][1]["status"] == "required_metric_missing"


def test_regression_gate_rejects_incompatible_dataset_or_run_mode():
    thresholds = {
        "metrics": {
            "accuracy": {
                "path": "metrics.intent_accuracy",
                "direction": "higher_is_better",
                "max_degradation": 0.02,
            }
        }
    }
    candidate = _run_report(run_mode="live_provider")
    result = compare_reports(_run_report(), candidate, thresholds)
    assert result["compatible"] is False
    assert result["passed"] is False
    assert "run_mode" in result["identity_mismatches"]


def test_regression_gate_rejects_provider_or_configuration_mismatch():
    thresholds = {
        "metrics": {
            "accuracy": {
                "path": "metrics.intent_accuracy",
                "direction": "higher_is_better",
                "max_degradation": 0.02,
            }
        }
    }
    candidate = _run_report()
    candidate["run_metadata"]["provider"] = "gemini"
    candidate["run_metadata"]["configuration"]["top_k"] = 8

    result = compare_reports(_run_report(), candidate, thresholds)

    assert result["compatible"] is False
    assert "provider" in result["identity_mismatches"]
    assert result["identity_mismatches"]["configuration"]["different_keys"] == [
        "top_k"
    ]

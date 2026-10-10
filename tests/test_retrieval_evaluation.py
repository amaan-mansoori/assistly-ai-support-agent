import json
from pathlib import Path

from src.evaluation.evaluate_retrieval import _failure_summary
from src.evaluation.evaluate_retrieval import MARKDOWN_REPORT, JSON_REPORT


def test_retrieval_report_shape_if_generated():
    if not JSON_REPORT.exists():
        return
    data = json.loads(JSON_REPORT.read_text(encoding="utf-8"))
    assert data["golden_examples_evaluated"] == 220
    assert data["evaluation_mode"] == "heuristic_proxy"
    assert data["dataset_sha256"]
    assert data["dataset_provenance_status"] == "unresolved_provisional"
    assert 0 <= data["intent-match@1"] <= data["intent-match@3"] <= data["intent-match@5"] <= 1
    assert MARKDOWN_REPORT.exists()


def test_retrieval_failure_summary_does_not_copy_query_or_historical_text():
    failure = _failure_summary(
        "golden-set-0001",
        "delivery_status_delay",
        [{
            "customer_text": "private query text",
            "amazonhelp_response": "private historical response",
            "response_tweet_id": "evidence-1",
            "similarity": 0.2,
        }],
        False,
    )

    assert failure["example_id"] == "golden-set-0001"
    assert failure["top1_evidence_id"] == "evidence-1"
    assert "private query text" not in json.dumps(failure)
    assert "private historical response" not in json.dumps(failure)

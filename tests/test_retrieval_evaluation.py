import json
from pathlib import Path

from src.evaluation.evaluate_retrieval import MARKDOWN_REPORT, JSON_REPORT


def test_retrieval_report_shape_if_generated():
    if not JSON_REPORT.exists():
        return
    data = json.loads(JSON_REPORT.read_text(encoding="utf-8"))
    assert data["golden_examples_evaluated"] == 220
    assert 0 <= data["intent-match@1"] <= data["intent-match@3"] <= data["intent-match@5"] <= 1
    assert MARKDOWN_REPORT.exists()

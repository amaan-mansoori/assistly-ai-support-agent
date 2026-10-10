import json
from pathlib import Path
import sys

import pytest

from src.agent.evidence import assess_evidence
from src.agent.grounding import validate_grounding
from src.agent.models import AgentEvidence
from src.evaluation.evaluate_integrated_agent import _failure_category
from src.evaluation.evaluate_integrated_agent import main as evaluate_main
from src.evaluation.compare_baselines import _write_markdown, run_comparison
from src.evaluation.llm_judge import main as judge_main


def _evidence(customer: str, resolution: str, score: float = 0.9) -> AgentEvidence:
    return AgentEvidence(
        customer_message=customer,
        support_response=resolution,
        source_id=f"response-{score}",
        retrieval_score=score,
    )


def test_empty_evidence_exposes_unavailable_match_signals():
    assessment = assess_evidence((), minimum_similarity=0.1)

    assert assessment.status == "none"
    assert not assessment.evidence_sufficient
    assert not assessment.evidence_conflict
    assert assessment.evidence_intent_match is None
    assert assessment.evidence_resolution_match is None


def test_conflicting_refund_outcomes_are_detected_as_heuristic_conflict():
    assessment = assess_evidence(
        (
            _evidence(
                "My refund is missing after my return.",
                "Your refund has been processed.",
            ),
            _evidence(
                "My refund is missing after my return.",
                "Your refund has not been processed.",
                0.8,
            ),
        ),
        minimum_similarity=0.1,
        expected_intent="return_refund",
    )

    assert assessment.status == "conflicting"
    assert assessment.evidence_conflict
    assert not assessment.evidence_sufficient
    assert assessment.evidence_intent_match is True
    assert assessment.evidence_resolution_match is False
    assert assessment.resolution_match_status == "heuristic_conflict_detected"


def test_opposite_outcomes_on_unrelated_topics_are_not_a_conflict():
    assessment = assess_evidence(
        (
            _evidence(
                "My refund is missing.",
                "Your refund was processed.",
            ),
            _evidence(
                "My refund is missing.",
                "Your refund issue was noted; your package failed inspection.",
                0.8,
            ),
        ),
        minimum_similarity=0.1,
        expected_intent="return_refund",
    )

    assert assessment.status == "sufficient"
    assert not assessment.evidence_conflict


def test_wrong_intent_evidence_does_not_pass_the_gate():
    assessment = assess_evidence(
        (
            _evidence(
                "My Prime membership renewal was charged.",
                "Review the Prime membership settings.",
            ),
        ),
        minimum_similarity=0.1,
        expected_intent="delivery_status_delay",
    )

    assert assessment.status == "weak"
    assert assessment.evidence_intent_match is False
    assert assessment.evidence_resolution_match is False


def test_grounding_uses_resolution_not_historical_customer_text():
    evidence = (
        _evidence(
            "Your refund has been processed.",
            "Please review the order page for the latest status.",
        ),
    )
    result = validate_grounding(
        "Your refund has been processed.",
        evidence,
        minimum_token_support=0.1,
    )

    assert not result.supported
    assert any("completed order action" in claim for claim in result.unsupported_claims)


def test_grounding_escalates_unsafe_credential_requests_but_allows_warning():
    evidence = (_evidence("Where can I track my order?", "Please check the order page."),)
    unsafe = validate_grounding(
        "Please share your password so I can help.",
        evidence,
    )
    safe_warning = validate_grounding(
        "Never share your password or one-time code.",
        evidence,
    )

    assert not unsafe.supported
    assert any("unsafe credential request:" in claim for claim in unsafe.unsupported_claims)
    assert not any(
        "unsafe credential request:" in claim
        for claim in safe_warning.unsupported_claims
    )


@pytest.mark.parametrize(
    ("predicted", "has_context", "expected"),
    [
        ("return_refund", False, "wrong_intent"),
        ("return_refund", True, "context_confusion"),
        ("delivery_status_delay", False, "conflicting_evidence"),
        ("delivery_status_delay", False, "unsupported_claim"),
    ],
)
def test_failure_categories_preserve_distinct_quality_modes(
    predicted: str,
    has_context: bool,
    expected: str,
):
    if expected == "conflicting_evidence":
        result = _failure_category(
            "delivery_status_delay", predicted, "conflicting", "escalate",
            None, None, has_context,
        )
    elif expected == "unsupported_claim":
        result = _failure_category(
            "delivery_status_delay", predicted, "sufficient", "escalate",
            None, False, has_context,
        )
    else:
        result = _failure_category(
            "delivery_status_delay", predicted, "sufficient", "escalate",
            None, None, has_context,
        )

    assert result == expected


def test_annotation_schema_is_versioned_categorical_and_does_not_modify_golden_set():
    schema_path = Path("reports/evaluation/annotation_schema_v1.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest = json.loads(
        Path("reports/evaluation/evaluation_dataset_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["$id"] == "assistly-annotation-record-v1"
    assert "dataset_version" in schema["required"]
    assert "dataset_sha256" in schema["required"]
    assert (
        schema["properties"]["dataset_version"]["const"]
        == manifest["dataset_version"]
    )
    assert (
        schema["properties"]["dataset_sha256"]["const"] == manifest["sha256"]
    )
    assert "expected_escalation" in schema["required"]
    assert "evidence_relevance" in schema["required"]
    assert "unsupported_claim_flags" in schema["required"]
    assert schema["additionalProperties"] is False
    assert not Path("reports/evaluation/annotations_v1.jsonl").exists()


def test_live_evaluation_requires_explicit_bounded_example_limit(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["evaluate_integrated_agent", "--live"])

    with pytest.raises(SystemExit) as error:
        evaluate_main()

    assert error.value.code == 2
    monkeypatch.setattr(sys, "argv", ["llm_judge", "--live"])
    with pytest.raises(SystemExit) as judge_error:
        judge_main()
    assert judge_error.value.code == 2

    with pytest.raises(ValueError, match="limit between 1 and 20"):
        run_comparison(
            Path("missing.csv"),
            Path("missing-manifest.json"),
            mode="live",
            limit=None,
        )


def test_baseline_comparison_markdown_preserves_system_labels(tmp_path):
    report = {
        "run_metadata": {
            "run_id": "fixture-run",
            "dataset_version": "fixture-v1",
            "dataset_sha256": "fixture-hash",
            "examples_evaluated": 1,
            "code_revision": "fixture-revision",
            "working_tree_dirty": True,
        },
        "results": {
            name: {
                "run_class": "deterministic_baseline",
                "metrics": {
                    "intent_accuracy": {"value": 0.5},
                    "intent_macro_f1": {"value": 0.4},
                },
            }
            for name in (
                "majority",
                "tfidf_logistic_regression",
                "assistly_runtime",
            )
        },
    }
    destination = tmp_path / "comparison.md"

    _write_markdown(report, destination)

    markdown = destination.read_text(encoding="utf-8")
    assert "| majority |" in markdown
    assert "| tfidf_logistic_regression |" in markdown
    assert "| assistly_runtime |" in markdown
    assert "| macro_f1 |" not in markdown

import pytest

from src.agent.models import (
    AgentDecision,
    AgentEvidence,
    AgentResponse,
    GroundingResult,
)
from src.evaluation.evaluate_integrated_agent import evaluate_examples


class FixedAgent:
    def handle(self, request):
        intent = "account_access_security" if "hacked" in request.message else "delivery_status_delay"
        escalated = intent == "account_access_security"
        return AgentResponse(
            request_id="eval-request",
            intent=intent,
            intent_confidence=None,
            intent_reason="test",
            intent_source="test",
            evidence=(
                AgentEvidence(
                    request.message,
                    "Please contact support.",
                    "response-1",
                    0.9,
                ),
            ),
            evidence_status="sufficient",
            evidence_reason="test evidence",
            draft_reply="Please contact support.",
            model_grounding_confidence=0.9,
            needs_human_review=escalated,
            grounding=GroundingResult(True, 1.0, 1.0, (), "supported"),
            decision=AgentDecision(
                "escalate" if escalated else "auto_handle", "test policy"
            ),
            processing_metadata={
                "duration_ms": 12,
                "stage_timings_ms": {
                    "retrieval_latency_ms": 2,
                    "generation_latency_ms": 5,
                },
            },
        )


def test_integrated_evaluation_reports_provisional_metrics_without_customer_text():
    examples = [
        {
            "example_id": "example-1",
            "customer_text": "My account was hacked.",
            "human_intent": "account_access_security",
        },
        {
            "example_id": "example-2",
            "customer_text": "My order is late.",
            "human_intent": "delivery_status_delay",
        },
    ]

    summary, rows = evaluate_examples(FixedAgent(), examples)

    assert summary["provenance"].startswith("Provisional:")
    assert summary["intent_accuracy"] == 1
    assert summary["intent_macro_f1"] == 1
    assert summary["intent_confusion_matrix"] == {
        "labels": ["account_access_security", "delivery_status_delay"],
        "counts": [[1, 0], [0, 1]],
    }
    assert summary["retrieval_intent_recall_at_k"] == {"1": 1, "3": 1, "5": 1}
    assert summary["retrieval_intent_mrr"] == 1
    assert summary["auto_handle_precision_proxy"] == 1
    assert summary["escalation_recall_proxy"] == 1
    assert summary["escalation_precision_proxy"] == 1
    assert summary["sensitive_case_recall"] == 1
    assert summary["evidence_sufficiency_accuracy"] is None
    assert summary["unsupported_claim_rate"] is None
    assert summary["average_retrieval_latency_ms"] == 2
    assert rows[0]["example_id"] == "example-1"
    assert "customer_text" not in rows[0]


def test_integrated_evaluation_rejects_empty_examples():
    with pytest.raises(ValueError, match="No labeled evaluation examples"):
        evaluate_examples(FixedAgent(), [])

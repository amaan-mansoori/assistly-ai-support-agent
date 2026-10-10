import json
import logging

import pytest

from src.agent.config import AgentConfig
from src.agent.intent import IntentDetector
from src.agent.models import AgentRequest
from src.agent.orchestrator import SupportAgent

EVIDENCE = {
    "customer_tweet_id": "old-customer-1",
    "response_tweet_id": "old-response-1",
    "customer_text": "My late order is still in transit.",
    "amazonhelp_response": "Please check tracking for the delivery status of your order.",
    "similarity": 0.9,
}
GROUNDED_REPLY = "Please check tracking for the delivery status of your order."


class StubRetriever:
    def __init__(self, rows=None, error=None):
        self.rows = [EVIDENCE] if rows is None else rows
        self.error = error
        self.calls = []

    def retrieve(self, query, k=5):
        self.calls.append((query, k))
        if self.error:
            raise self.error
        return self.rows


def reply_json(
    draft=GROUNDED_REPLY, confidence=0.9, needs_review=False, reason="Evidence supports this draft."
):
    return json.dumps(
        {
            "draft_reply": draft,
            "grounding_confidence": confidence,
            "needs_human_review": needs_review,
            "reason": reason,
        }
    )


def create_agent(retriever=None, llm_call=None, **config_values):
    config = AgentConfig(**config_values)
    return SupportAgent(
        retriever or StubRetriever(),
        llm_call or (lambda _system, _prompt: reply_json()),
        config,
    )


def test_end_to_end_grounded_delivery_draft_can_auto_handle():
    retriever = StubRetriever()
    agent = create_agent(retriever)

    result = agent.handle(
        AgentRequest(
            message="My order is late. Where can I check delivery status?",
            request_id="e2e-17",
        )
    )

    assert result.request_id == "e2e-17"
    assert result.intent == "delivery_status_delay"
    assert result.intent_confidence is None
    assert result.evidence_status == "sufficient"
    assert result.evidence[0].source_id == "old-response-1"
    assert result.draft_reply == GROUNDED_REPLY
    assert result.grounding is not None
    assert result.grounding.supported
    assert result.decision.decision == "auto_handle"
    assert result.processing_metadata["grounding_diagnostics"][
        "grounding_status"
    ] == "supported"
    assert result.processing_metadata["grounding_diagnostics"][
        "unsupported_claim_detected"
    ] is False
    assert result.processing_metadata["duration_ms"] >= 0
    timings = result.processing_metadata["stage_timings_ms"]
    assert {
        "intent_detection_latency_ms",
        "retrieval_latency_ms",
        "evidence_gate_latency_ms",
        "generation_latency_ms",
        "provider_call_latency_ms",
        "grounding_latency_ms",
    } <= timings.keys()
    assert all(value >= 0 for value in timings.values())
    assert result.processing_metadata["provider_retry_count"] is None
    assert (
        result.processing_metadata["provider_retry_count_status"]
        == "provider_sdk_retries_not_exposed"
    )
    assert "current request: My order is late." in retriever.calls[0][0]


def test_unclear_intent_escalates_without_retrieval_or_generation():
    retriever = StubRetriever()
    calls = []
    agent = create_agent(retriever, lambda *args: calls.append(args) or reply_json())

    result = agent.handle({"message": "Can someone help me?"})

    assert result.intent == "other_unclear"
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None
    assert retriever.calls == []
    assert calls == []


def test_empty_retrieval_escalates_without_requesting_a_draft():
    calls = []
    result = create_agent(
        StubRetriever(rows=[]), lambda *args: calls.append(args) or reply_json()
    ).handle({"message": "My order is late."})

    assert result.evidence_status == "none"
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None
    assert calls == []


def test_zero_score_results_are_not_counted_as_useful_evidence():
    result = create_agent(
        StubRetriever(rows=[{**EVIDENCE, "similarity": 0.0}])
    ).handle({"message": "My order is late."})

    assert result.evidence_status == "none"
    assert result.decision.decision == "escalate"


def test_weak_retrieval_escalates_under_configured_similarity_floor():
    result = create_agent(
        StubRetriever(rows=[{**EVIDENCE, "similarity": 0.04}]),
        minimum_retrieval_similarity=0.1,
    ).handle({"message": "My order is late."})

    assert result.evidence_status == "weak"
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None


def test_wrong_intent_retrieval_is_not_treated_as_sufficient():
    wrong_intent = {
        **EVIDENCE,
        "customer_text": "My Prime membership renewal was charged.",
        "similarity": 0.99,
    }
    provider_calls = []
    result = create_agent(
        StubRetriever(rows=[wrong_intent]),
        lambda *args: provider_calls.append(args) or reply_json(),
    ).handle({"message": "My order is late."})

    assert result.evidence_status == "weak"
    assert result.processing_metadata["retrieval_diagnostics"][
        "evidence_intent_match"
    ] is False
    assert result.decision.decision == "escalate"
    assert provider_calls == []


def test_conflicting_intent_matched_resolutions_escalate_before_provider():
    rows = [
        {
            **EVIDENCE,
            "customer_text": "My refund is missing after my return.",
            "amazonhelp_response": "Your refund has been processed.",
            "similarity": 0.9,
        },
        {
            **EVIDENCE,
            "customer_text": "My refund is missing after my return.",
            "amazonhelp_response": "Your refund has not been processed.",
            "similarity": 0.85,
        },
    ]
    provider_calls = []
    result = create_agent(
        StubRetriever(rows=rows),
        lambda *args: provider_calls.append(args) or reply_json(),
    ).handle({"message": "My refund is missing after my return."})

    assert result.evidence_status == "conflicting"
    assert result.processing_metadata["retrieval_diagnostics"][
        "evidence_conflict"
    ] is True
    assert result.decision.decision == "escalate"
    assert provider_calls == []


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("I cannot access my hacked account.", "account_access_security"),
        ("I was charged twice for this order.", "payment_charge_issue"),
        (
            "Tracking says delivered but I did not receive the package.",
            "delivery_marked_delivered_missing",
        ),
    ],
)
def test_sensitive_intents_always_escalate(message, intent):
    calls = []
    result = create_agent(
        llm_call=lambda *args: calls.append(args) or reply_json()
    ).handle({"message": message})

    assert result.intent == intent
    assert result.decision.decision == "escalate"
    assert "Sensitive intent" in result.decision.reason
    assert result.draft_reply is None
    assert calls == []


def test_sensitive_intent_remains_explanatory_when_retrieval_fails():
    calls = []
    result = create_agent(
        StubRetriever(error=RuntimeError("retrieval unavailable")),
        lambda *args: calls.append(args) or reply_json(),
    ).handle({"message": "I cannot access my hacked account."})

    assert result.intent == "account_access_security"
    assert result.error == "retrieval_failed"
    assert "Sensitive intent" in result.decision.reason
    assert result.draft_reply is None
    assert calls == []


def test_explicit_model_human_review_escalates():
    result = create_agent(
        llm_call=lambda _system, _prompt: reply_json(needs_review=True)
    ).handle({"message": "My order is late."})

    assert result.needs_human_review
    assert result.decision.decision == "escalate"
    assert result.decision.reason == "The draft marked this case for human review."


@pytest.mark.parametrize(
    "draft",
    [
        "Your order will arrive within 48 hours.",
        "Your order will arrive on Friday.",
        "Your order number is 123456.",
        "Track your package at https://example.invalid/track",
        "You are eligible for a refund.",
        "We have processed your refund.",
        "We guarantee the replacement will arrive.",
    ],
)
def test_unsupported_specific_claims_force_human_review(draft):
    result = create_agent(llm_call=lambda _system, _prompt: reply_json(draft=draft)).handle(
        {"message": "My order is late."}
    )

    assert result.grounding is not None
    assert not result.grounding.supported
    assert result.grounding.unsupported_claims
    assert result.decision.decision == "escalate"
    assert result.decision.reason.startswith("Independent grounding gate:")


def test_unsafe_credential_request_is_grounding_failure_and_escalates():
    result = create_agent(
        llm_call=lambda *_: reply_json(
            draft="Please share your password so I can help."
        )
    ).handle({"message": "My order is late."})

    assert result.grounding is not None
    assert not result.grounding.supported
    assert any(
        claim.startswith("unsafe credential request:")
        for claim in result.grounding.unsupported_claims
    )
    assert result.processing_metadata["grounding_diagnostics"][
        "unsupported_claim_detected"
    ] is True
    assert result.decision.decision == "escalate"


def test_malformed_model_output_returns_safe_escalation():
    result = create_agent(llm_call=lambda *_: "{bad").handle(
        {"message": "My order is late.", "request_id": "bad-json"}
    )

    assert result.error == "malformed_model_output"
    assert result.request_id == "bad-json"
    assert result.draft_reply is None
    assert result.decision.decision == "escalate"
    assert "JSON" not in result.decision.reason


def test_provider_failure_does_not_return_a_success_shaped_reply():
    result = create_agent(
        llm_call=lambda *_: (_ for _ in ()).throw(
            RuntimeError("provider failure and private credential")
        )
    ).handle({"message": "My order is late."})

    assert result.error == "provider_failed"
    assert result.draft_reply is None
    assert "private credential" not in result.decision.reason
    assert result.decision.decision == "escalate"


@pytest.mark.parametrize(
    ("input_value", "error"),
    [
        ({"message": ""}, "empty_message"),
        ({"message": 12}, "invalid_request"),
        (AgentRequest(message="My order is late.", request_id=""), "invalid_request"),
        ({"message": "My order is late.", "conversation_history": ["ok", 4]}, "invalid_request"),
        ({"message": "My order is late.", "requested_intent": "not-a-real-intent"}, "invalid_requested_intent"),
    ],
)
def test_malformed_and_empty_requests_fail_safely(input_value, error):
    result = create_agent().handle(input_value)

    assert result.error == error
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None


def test_conversation_history_is_used_for_intent_retrieval_and_generation():
    retriever = StubRetriever()
    prompts = []
    agent = create_agent(retriever, lambda _system, prompt: prompts.append(prompt) or reply_json())

    result = agent.handle(
        {
            "message": "Thanks for checking.",
            "conversation_history": ["My order has been late for two days."],
            "request_id": "history-2",
        }
    )

    assert result.intent == "delivery_status_delay"
    assert "My order has been late for two days." in retriever.calls[0][0]
    assert json.dumps(["My order has been late for two days."]) in prompts[0]
    assert result.request_id == "history-2"


def test_clear_current_message_dominates_stale_history_in_retrieval_query():
    retriever = StubRetriever()
    result = create_agent(retriever).handle(
        {
            "message": "The seller won't respond to me.",
            "conversation_history": [
                "My order is late and tracking has not updated."
            ],
        }
    )

    assert result.intent == "marketplace_seller"
    query = retriever.calls[0][0]
    assert query.index("current request:") < query.index("The seller")
    assert "recent context:" not in query


def test_retrieval_metadata_exposes_scores_without_customer_content():
    result = create_agent().handle({"message": "My order is late."})

    diagnostics = result.processing_metadata["retrieval_diagnostics"]
    assert diagnostics["retrieval_backend"] == "unknown"
    assert diagnostics["candidate_count"] == 1
    assert diagnostics["selected_evidence_ids"] == ["old-response-1"]
    assert diagnostics["evidence_sufficient"] is True
    assert diagnostics["evidence_intent_match"] is True
    assert diagnostics["evidence_resolution_match"] is True
    assert "customer_text" not in str(diagnostics)


def test_current_sensitive_intent_takes_precedence_over_delivery_history():
    result = create_agent().handle(
        {
            "message": "I cannot access my hacked account.",
            "conversation_history": [
                "My order is late. Where can I check delivery status?",
                GROUNDED_REPLY,
            ],
        }
    )

    assert result.intent == "account_access_security"
    assert result.decision.decision == "escalate"


def test_clear_current_delivery_intent_takes_precedence_over_security_history():
    result = create_agent().handle(
        {
            "message": "My order is late and tracking has not updated.",
            "conversation_history": ["My account was hacked; I cannot sign in."],
        }
    )

    assert result.intent == "delivery_status_delay"


def test_retrieval_failure_fails_safely():
    result = create_agent(StubRetriever(error=OSError("private path"))).handle(
        {"message": "My order is late."}
    )

    assert result.error == "retrieval_failed"
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None
    assert "private path" not in result.decision.reason


def test_provider_timeout_fails_safely_without_exposing_exception():
    def timeout(*_args):
        raise TimeoutError("provider request timed out with secret details")

    result = create_agent(llm_call=timeout).handle(
        {"message": "My order is late.", "request_id": "timeout-1"}
    )

    assert result.error == "provider_failed"
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None
    assert "secret details" not in result.decision.reason
    assert result.processing_metadata["provider_error_category"] == "provider_timeout"


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (TimeoutError("provider secret timeout"), "provider_timeout"),
        (type("RateLimitError", (Exception,), {"status_code": 429})("secret"), "rate_limited"),
        (type("ServerError", (Exception,), {"code": 503})("secret"), "provider_server_error"),
        (type("AuthenticationError", (Exception,), {"code": 403})("secret"), "provider_auth_error"),
        (type("BadRequestError", (Exception,), {"code": 400})("secret"), "provider_client_error"),
    ],
)
def test_provider_error_categories_are_sanitized_and_fail_closed(error, category):
    def fail(*_args):
        raise error

    result = create_agent(llm_call=fail).handle({"message": "My order is late."})

    assert result.error == "provider_failed"
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None
    assert result.processing_metadata["provider_error_category"] == category
    assert "secret" not in result.decision.reason


def test_classifier_failure_fails_safely():
    class BrokenIntentDetector(IntentDetector):
        def detect(self, *_args):
            raise RuntimeError("private internal details")

    result = SupportAgent(
        StubRetriever(),
        lambda *_: reply_json(),
        AgentConfig(),
        BrokenIntentDetector(),
    ).handle({"message": "My order is late."})

    assert result.error == "intent_detection_failed"
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None
    assert "private internal details" not in result.decision.reason


def test_completion_log_has_correlation_but_not_customer_text(caplog):
    customer_message = "PRIVATE CUSTOMER MESSAGE 845913"
    with caplog.at_level(logging.INFO, logger="src.agent.orchestrator"):
        result = create_agent().handle(
            {"message": customer_message, "request_id": "log-1"}
        )

    assert result.request_id == "log-1"
    assert any(record.request_id == "log-1" for record in caplog.records)
    assert customer_message not in caplog.text


def test_retrieval_result_with_wrong_shape_fails_safely():
    result = create_agent(StubRetriever(rows={"unexpected": "mapping"})).handle(
        {"message": "My order is late."}
    )

    assert result.error == "retrieval_failed"
    assert result.decision.decision == "escalate"
    assert result.draft_reply is None


def test_escalation_policy_reason_and_request_id_are_propagated():
    result = create_agent(
        llm_call=lambda _system, _prompt: reply_json(confidence=0.69)
    ).handle({"message": "My order is late.", "request_id": "trace-99"})

    assert result.request_id == "trace-99"
    assert result.decision.decision == "escalate"
    assert result.decision.reason == "Evidence confidence is below the review threshold."


def test_caller_intent_hint_cannot_override_taxonomy_for_auto_handling():
    result = create_agent().handle(
        {
            "message": "I was charged twice for this order.",
            "requested_intent": "delivery_status_delay",
        }
    )

    assert result.intent == "other_unclear"
    assert result.intent_source == "taxonomy_conflict"
    assert result.decision.decision == "escalate"


def test_retriever_failure_or_non_numeric_score_is_reported_as_safe_escalation():
    result = create_agent(
        StubRetriever(rows=[{**EVIDENCE, "similarity": "high"}])
    ).handle({"message": "My order is late."})

    assert result.error == "retrieval_failed"
    assert result.decision.decision == "escalate"

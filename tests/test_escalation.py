import pytest

from src.agent.escalation import decide_escalation


@pytest.mark.parametrize("intent", [
    "account_access_security", "payment_charge_issue",
    "delivery_marked_delivered_missing", "other_unclear",
])
def test_sensitive_and_unclear_intents_escalate(intent):
    assert decide_escalation("I need help", intent)["decision"] == "escalate"


@pytest.mark.parametrize("intent", [
    "marketplace_seller", "return_refund", "item_condition_or_fulfilment",
    "prime_membership", "product_availability_pricing",
])
def test_ordinary_cases_auto_handle(intent):
    assert decide_escalation("Please provide the usual guidance.", intent)["decision"] == "auto_handle"


def test_marketplace_seller_boundaries():
    assert decide_escalation("The seller won't respond.", "marketplace_seller")["decision"] == "escalate"
    assert decide_escalation("I need an A-to-Z claim.", "marketplace_seller")["decision"] == "escalate"


def test_order_change_requires_clear_pre_dispatch():
    assert decide_escalation("Please cancel; it has not shipped.", "order_cancellation_or_change")["decision"] == "auto_handle"
    assert decide_escalation("Please cancel; it already shipped.", "order_cancellation_or_change")["decision"] == "escalate"
    assert decide_escalation("Please change my order.", "order_cancellation_or_change")["decision"] == "escalate"


def test_exception_boundaries():
    assert decide_escalation("My refund never arrived.", "return_refund")["decision"] == "escalate"
    assert decide_escalation("The package is weeks late.", "delivery_status_delay")["decision"] == "escalate"
    assert decide_escalation("This keeps failing every time.", "delivery_status_delay")["decision"] == "escalate"
    assert decide_escalation("The item is hazardous and leaking.", "item_condition_or_fulfilment")["decision"] == "escalate"
    assert decide_escalation("Prime charged me for renewal.", "prime_membership")["decision"] == "escalate"
    assert decide_escalation("The price listing is inaccurate.", "product_availability_pricing")["decision"] == "escalate"


def test_existing_reply_review_fields_escalate():
    assert decide_escalation("Ordinary question", "marketplace_seller",
                             needs_human_review=True)["decision"] == "escalate"
    assert decide_escalation("Ordinary question", "marketplace_seller",
                             grounding_confidence=0.69)["decision"] == "escalate"


def test_output_contract_is_exact():
    result = decide_escalation("Where is my package?", "delivery_status_delay")
    assert set(result) == {"decision", "reason"}
    assert result["decision"] in {"auto_handle", "escalate"}
    assert result["reason"]

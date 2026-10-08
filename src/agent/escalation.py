"""Deterministic escalation policy for the support-agent draft workflow."""
from __future__ import annotations

import re
from typing import Any, TypedDict

from src.agent.models import DecisionKind

DECISIONS = ("auto_handle", "escalate")
ESCALATION_CONFIDENCE_THRESHOLD = 0.7
SENSITIVE_INTENTS = frozenset(
    {
        "account_access_security",
        "payment_charge_issue",
        "delivery_marked_delivered_missing",
    }
)


def _matches(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


class EscalationResult(TypedDict):
    decision: DecisionKind
    reason: str


def _result(decision: DecisionKind, reason: str) -> EscalationResult:
    return {"decision": decision, "reason": reason}


def decide_escalation(
    customer_text: str,
    predicted_intent: str,
    *,
    grounding_confidence: float | None = None,
    needs_human_review: bool = False,
    confidence_threshold: float = ESCALATION_CONFIDENCE_THRESHOLD,
) -> EscalationResult:
    """Choose ``auto_handle`` or ``escalate`` using explicit local rules."""
    text = str(customer_text or "")
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence_threshold must be between 0 and 1")
    if needs_human_review:
        return _result("escalate", "The draft marked this case for human review.")
    if grounding_confidence is not None and grounding_confidence < confidence_threshold:
        return _result("escalate", "Evidence confidence is below the review threshold.")

    if predicted_intent in SENSITIVE_INTENTS:
        return _result("escalate", "This intent requires account-specific human handling.")

    if predicted_intent == "marketplace_seller":
        if (
            _matches(
                text,
                r"\b(?:seller|vendor).{0,30}\b(?:refus|won't|wont|doesn't respond|doesnt respond|no response|ignore)",
            )
            or _matches(text, r"\b(?:a[- ]?to[- ]?z|a2z)\b")
        ):
            return _result("escalate", "Seller refusal, non-response, or an A-to-Z claim requires review.")
        return _result("auto_handle", "Ordinary marketplace-seller guidance can be handled from the draft.")

    if predicted_intent == "order_cancellation_or_change":
        if (
            (
                _matches(text, r"\b(?:shipped|dispatched|out for delivery|already sent)\b")
                and not _matches(text, r"\bnot\s+(?:shipped|dispatched)\b")
            )
            or _matches(text, r"\b(?:unable to cancel|can't cancel|cannot cancel|system error)\b")
            or not _matches(text, r"\b(?:cancel|change|modify|update)\b")
        ):
            return _result("escalate", "The order change is not clearly a simple pre-dispatch request.")
        if _matches(text, r"\b(?:not shipped|pre[- ]?dispatch|before shipping|hasn't shipped|hasnt shipped|just ordered)\b"):
            return _result("auto_handle", "This is a clear pre-dispatch order change request.")
        return _result("escalate", "Dispatch status is unclear for this order change request.")

    if predicted_intent == "return_refund":
        if _matches(text, r"\b(?:missing refund|refund (?:never|not|hasn't|hasnt)|didn't get (?:my )?refund|exception|rejected|denied|lost return|return (?:missing|stuck))\b"):
            return _result("escalate", "A missing or exceptional return/refund case needs review.")
        return _result("auto_handle", "Ordinary return or refund guidance can be handled.")

    if predicted_intent == "delivery_status_delay":
        materially_overdue = _matches(text, r"\b(?:weeks?|month|months|overdue|significantly late|more than \d+ days late)\b")
        repeated_failure = _matches(text, r"\b(?:again|repeatedly|every time|multiple times|second time|third time|keeps? failing)\b")
        if materially_overdue or repeated_failure:
            return _result("escalate", "Materially overdue or repeated delivery failures need review.")
        return _result("auto_handle", "Ordinary tracking or delivery-status guidance can be handled.")

    if predicted_intent == "item_condition_or_fulfilment":
        if _matches(text, r"\b(?:hazard(?:ous)?|danger|dangerous|leak(?:ing)? chemical|fire|smoke|non[- ]?returnable|cannot return|can't return|exception)\b"):
            return _result("escalate", "A hazardous, non-returnable, or exceptional item case needs review.")
        return _result("auto_handle", "Ordinary replacement or return guidance can be handled.")

    if predicted_intent == "prime_membership":
        if _matches(text, r"\b(?:billing|billed|charged|charge|payment|renewal).{0,25}\b(?:prime|membership)\b|\bprime\b.{0,25}\b(?:billing|billed|charged|charge|payment|renewal)\b"):
            return _result("escalate", "An account-specific Prime billing dispute needs review.")
        return _result("auto_handle", "Ordinary Prime membership or benefit guidance can be handled.")

    if predicted_intent == "product_availability_pricing":
        if _matches(text, r"\b(?:misleading|inaccurate|incorrect|wrong|false|fake)\b.{0,25}\b(?:listing|price|pricing|description|availability)\b|\b(?:listing|price|pricing|description)\b.{0,25}\b(?:misleading|inaccurate|incorrect|wrong|false|fake)\b"):
            return _result("escalate", "An inaccurate listing or price requires review.")
        return _result("auto_handle", "Ordinary stock or pricing guidance can be handled.")

    if predicted_intent == "other_unclear":
        return _result("escalate", "The request requires clarification or additional context.")

    return _result("escalate", "The intent is not recognized by the approved escalation policy.")


def decide_for_record(record: dict[str, Any]) -> EscalationResult:
    """Apply the policy to an existing generated-reply record."""
    return decide_escalation(
        str(record.get("customer_text", "")),
        str(record.get("human_intent", "")),
        grounding_confidence=record.get("grounding_confidence"),
        needs_human_review=bool(record.get("needs_human_review", False)),
    )

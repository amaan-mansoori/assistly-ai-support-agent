"""Evidence sufficiency checks for historical retrieval results."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Sequence

from src.agent.models import AgentEvidence, EvidenceStatus
from src.intents.final_taxonomy_audit import classify_intent


@dataclass(frozen=True)
class EvidenceAssessment:
    status: EvidenceStatus
    reason: str
    evidence: tuple[AgentEvidence, ...]
    evidence_sufficient: bool
    evidence_conflict: bool
    evidence_intent_match: bool | None
    evidence_resolution_match: bool | None
    resolution_match_status: str


def convert_evidence(rows: Sequence[dict[str, Any]]) -> tuple[AgentEvidence, ...]:
    evidence = []
    for row in rows:
        score = row.get("similarity")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("retrieval result has no numeric similarity")
        if not 0 <= score <= 1:
            raise ValueError("retrieval similarity must be between 0 and 1")
        components = row.get("score_components", {})
        if not isinstance(components, dict) or any(
            not isinstance(key, str)
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
            for key, value in components.items()
        ):
            raise ValueError("retrieval score_components must contain unit scores")
        customer_id = str(row.get("customer_tweet_id", ""))
        response_id = str(row.get("response_tweet_id", ""))
        evidence.append(
            AgentEvidence(
                customer_message=str(row.get("customer_text", "")),
                support_response=str(row.get("amazonhelp_response", "")),
                source_id=response_id or customer_id,
                retrieval_score=float(score),
                provenance={
                    key: value
                    for key, value in {
                        "customer_tweet_id": customer_id,
                        "response_tweet_id": response_id,
                    }.items()
                    if value
                },
                score_components={
                    key: float(value) for key, value in components.items()
                },
                retrieval_backend=str(row.get("retrieval_backend", "unknown")),
            )
        )
    return tuple(evidence)


def assess_evidence(
    evidence: tuple[AgentEvidence, ...],
    minimum_similarity: float,
    expected_intent: str | None = None,
) -> EvidenceAssessment:
    if not evidence:
        return _assessment(
            "none",
            "No historical evidence was retrieved.",
            (),
            None,
            None,
            "not_available",
        )

    checked = tuple(
        AgentEvidence(
            **{
                **item.__dict__,
                "intent_match": (
                    classify_intent(item.customer_message) == expected_intent
                    if expected_intent is not None and item.customer_message.strip()
                    else None
                ),
            }
        )
        for item in evidence
    )
    best = max(item.retrieval_score for item in checked)
    if best <= 0:
        return _assessment(
            "none",
            "Retrieved examples have no usable similarity signal.",
            checked,
            any(item.intent_match is True for item in checked)
            if expected_intent is not None else None,
            None,
            "not_available",
        )
    if best < minimum_similarity:
        return _assessment(
            "weak",
            "Best historical match is below the configured lexical similarity floor.",
            checked,
            any(item.intent_match is True for item in checked)
            if expected_intent is not None else None,
            None,
            "not_available",
        )

    intent_matched = tuple(
        item for item in checked
        if item.intent_match is True or item.intent_match is None
    )
    if expected_intent is not None and not intent_matched:
        return _assessment(
            "weak",
            "Retrieved examples do not match the predicted intent.",
            checked,
            False,
            False,
            "heuristic_intent_mismatch",
        )
    usable = tuple(
        item for item in intent_matched
        if item.retrieval_score >= minimum_similarity
        and item.support_response.strip()
    )
    if not usable:
        return _assessment(
            "weak",
            "No intent-compatible retrieved example contains a usable support resolution.",
            checked,
            True if expected_intent is not None else None,
            False,
            "heuristic_no_usable_resolution",
        )
    if _has_conflicting_resolutions(usable):
        return _assessment(
            "conflicting",
            "Intent-compatible historical resolutions contain conflicting outcomes.",
            checked,
            True if expected_intent is not None else None,
            False,
            "heuristic_conflict_detected",
        )
    return _assessment(
        "sufficient",
        "At least one intent-compatible historical resolution meets the similarity floor; this remains a heuristic, not a factuality guarantee.",
        checked,
        True if expected_intent is not None else None,
        True,
        "heuristic_nonempty_intent_compatible_resolution_proxy",
    )


def _assessment(
    status: EvidenceStatus,
    reason: str,
    evidence: tuple[AgentEvidence, ...],
    intent_match: bool | None,
    resolution_match: bool | None,
    resolution_match_status: str,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        status,
        reason,
        evidence,
        evidence_sufficient=status == "sufficient",
        evidence_conflict=status == "conflicting",
        evidence_intent_match=intent_match,
        evidence_resolution_match=resolution_match,
        resolution_match_status=resolution_match_status,
    )


_OUTCOME_TOPICS = {
    "refund", "replacement", "return", "delivery", "package", "shipment",
    "order", "charge", "payment", "claim", "account",
}
_POSITIVE_OUTCOMES = {
    "approved", "eligible", "processed", "issued", "completed", "delivered",
    "available", "shipped", "accepted", "refunded",
}
_NEGATIVE_OUTCOMES = {
    "denied", "ineligible", "declined", "failed", "unavailable", "rejected",
}
_NEGATIONS = {"not", "never", "cannot", "can't", "unable", "won't", "isn't", "no"}
_WORD = re.compile(r"[a-z]+")


def _has_conflicting_resolutions(evidence: tuple[AgentEvidence, ...]) -> bool:
    for index, first in enumerate(evidence):
        first_polarities = _topic_outcome_polarities(first.support_response)
        for second in evidence[index + 1:]:
            second_polarities = _topic_outcome_polarities(second.support_response)
            if any(
                first_polarities.get(topic) in {"positive", "negative"}
                and second_polarities.get(topic) in {"positive", "negative"}
                and first_polarities[topic] != second_polarities[topic]
                for topic in first_polarities.keys() & second_polarities.keys()
            ):
                return True
    return False


def _topic_outcome_polarities(text: str) -> dict[str, str | None]:
    words = _WORD.findall(text.lower())
    outcomes: dict[str, set[str]] = {}
    topic_positions = [
        (index, word) for index, word in enumerate(words)
        if word in _OUTCOME_TOPICS
    ]
    for index, word in enumerate(words):
        if word not in _POSITIVE_OUTCOMES | _NEGATIVE_OUTCOMES:
            continue
        nearby_topics = [
            (abs(index - topic_index), topic)
            for topic_index, topic in topic_positions
            if abs(index - topic_index) <= 4
        ]
        if not nearby_topics:
            continue
        _, topic = min(nearby_topics)
        preceding = set(words[max(0, index - 2):index])
        polarity = (
            "negative"
            if word in _NEGATIVE_OUTCOMES or preceding & _NEGATIONS
            else "positive"
        )
        outcomes.setdefault(topic, set()).add(polarity)
    return {
        topic: next(iter(polarities)) if len(polarities) == 1 else None
        for topic, polarities in outcomes.items()
    }

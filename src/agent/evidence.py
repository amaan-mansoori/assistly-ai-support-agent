"""Evidence sufficiency checks for historical retrieval results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from src.agent.models import AgentEvidence, EvidenceStatus


@dataclass(frozen=True)
class EvidenceAssessment:
    status: EvidenceStatus
    reason: str
    evidence: tuple[AgentEvidence, ...]


def convert_evidence(rows: Sequence[dict[str, Any]]) -> tuple[AgentEvidence, ...]:
    evidence = []
    for row in rows:
        score = row.get("similarity")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("retrieval result has no numeric similarity")
        if not 0 <= score <= 1:
            raise ValueError("retrieval similarity must be between 0 and 1")
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
            )
        )
    return tuple(evidence)


def assess_evidence(
    evidence: tuple[AgentEvidence, ...], minimum_similarity: float
) -> EvidenceAssessment:
    if not evidence:
        return EvidenceAssessment("none", "No historical evidence was retrieved.", ())
    best = max(item.retrieval_score for item in evidence)
    if best <= 0:
        return EvidenceAssessment(
            "none", "Retrieved examples have no lexical overlap with the query.", evidence
        )
    if best < minimum_similarity:
        return EvidenceAssessment(
            "weak",
            "Best historical match is below the configured lexical similarity floor.",
            evidence,
        )
    return EvidenceAssessment(
        "sufficient",
        "At least one historical match meets the configured lexical similarity floor; this is not a factuality guarantee.",
        evidence,
    )

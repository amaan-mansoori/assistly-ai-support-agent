"""Conservative runtime claim checks built on the offline lexical diagnostic.

These checks can detect unsupported literal details and weak lexical support;
they do not prove entailment or factual correctness.
"""
from __future__ import annotations

import re
from typing import Sequence

from src.agent.models import AgentEvidence, GroundingResult
from src.evaluation.grounding import evaluate_grounding

_CLAIM_PATTERNS = (
    ("URL", re.compile(r"https?://[^\s)>\]}]+", re.IGNORECASE)),
    ("number", re.compile(r"\b\d+(?:[./:-]\d+)*\b")),
    (
        "timeline",
        re.compile(
            r"\b(?:within|in|after|by)\s+(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|a|an)\s+(?:business\s+)?(?:minutes?|hours?|days?|weeks?|months?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "date",
        re.compile(
            r"\b(?:(?:mon|tues|wednes|thurs|fri|satur|sun)day|"
            r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
            r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
            r"dec(?:ember)?)\s+\d{1,2}(?:,?\s+\d{4})?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "guarantee",
        re.compile(r"\b(?:guarantee[ds]?|promise[ds]?|will definitely|certainly)\b", re.IGNORECASE),
    ),
    (
        "policy",
        re.compile(
            r"\b(?:eligible for (?:a )?refund|entitled to (?:a )?refund|"
            r"covered by (?:the )?warranty|non-refundable|policy allows|"
            r"policy guarantees|guaranteed refund)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "completed action",
        re.compile(
            r"\b(?:we|i)\s+(?:have\s+|already\s+|just\s+)?"
            r"(?:issued|processed|refunded|cancelled|canceled|replaced|escalated|"
            r"contacted|sent|updated|changed|approved|shipped|dispatched|received)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "future commitment",
        re.compile(
            r"\b(?:we|i)\s+(?:will|shall|can)\s+"
            r"(?:refund|replace|cancel|ship|deliver|contact|escalate|process|issue|"
            r"update|change|approve|resolve|credit|investigate|review|look into)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "completed order action",
        re.compile(
            r"\b(?:your|the)\s+(?:refund|replacement|order|package)\s+"
            r"(?:has been|was|is being)\s+"
            r"(?:processed|approved|issued|shipped|dispatched|cancelled|canceled|replaced)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "promised order action",
        re.compile(
            r"\b(?:your|the)\s+(?:refund|replacement|order|package)\s+"
            r"(?:will be|is guaranteed to be)\s+"
            r"(?:processed|approved|issued|shipped|dispatched|cancelled|canceled|replaced)\b",
            re.IGNORECASE,
        ),
    ),
)


def validate_grounding(
    draft_reply: str,
    evidence: Sequence[AgentEvidence],
    minimum_token_support: float = 0.5,
) -> GroundingResult:
    if not 0 <= minimum_token_support <= 1:
        raise ValueError("minimum_token_support must be between 0 and 1")
    evidence_rows = [
        {
            "customer_text": item.customer_message,
            "amazonhelp_response": item.support_response,
            "similarity": item.retrieval_score,
        }
        for item in evidence
    ]
    diagnostic = evaluate_grounding(
        {"draft_reply": draft_reply, "retrieved_examples": evidence_rows}
    )
    evidence_text = " ".join(
        f"{item.customer_message} {item.support_response}" for item in evidence
    ).lower()
    unsupported = []
    seen: set[str] = set()
    for label, pattern in _CLAIM_PATTERNS:
        for match in pattern.finditer(draft_reply):
            claim = match.group(0).strip()
            if claim.lower() not in evidence_text:
                value = f"{label}: {claim}"
                if value not in seen:
                    seen.add(value)
                    unsupported.append(value)

    token_rate = float(diagnostic["evidence_token_support_rate"])
    if not evidence:
        reason = "No evidence is available to ground the draft."
    elif unsupported:
        reason = "One or more specific claims are not present in the retrieved evidence."
    elif token_rate < minimum_token_support:
        reason = "Draft lexical support is below the configured grounding floor."
    else:
        reason = (
            "No unsupported literal claim was detected and lexical support meets "
            "the configured floor; this check does not prove factual correctness."
        )
    return GroundingResult(
        supported=bool(evidence) and not unsupported and token_rate >= minimum_token_support,
        score=float(diagnostic["grounding_score"]),
        evidence_token_support_rate=token_rate,
        unsupported_claims=tuple(unsupported),
        reason=reason,
    )

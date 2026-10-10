"""Small, deterministic checks for whether a reply is supported by its evidence.

These checks deliberately measure lexical support, not factual truth.  They are
useful offline diagnostics for the generated JSONL and do not require an API
call or an embedding model.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?")
URL_RE = re.compile(r"https?://[^\s)>\]}]+", re.IGNORECASE)
NUMBER_RE = re.compile(r"\b\d+(?:[./:-]\d+)*\b")

# Words which occur in almost every polite support reply and are not useful
# evidence of a claim.
STOPWORDS = {
    "a", "about", "also", "am", "an", "and", "are", "as", "at", "be", "been",
    "but", "by", "can", "could", "dear", "for", "from", "get", "getting", "go",
    "have", "help", "here", "hi", "i", "if", "in", "is", "it", "just", "know",
    "let", "like", "me", "my", "need", "of", "on", "or", "our", "please", "so",
    "some", "sorry", "support", "tell", "thank", "thanks", "that", "the", "their",
    "there", "this", "to", "us", "we", "what", "when", "will", "with", "you",
    "your",
}


def _tokens(text: Any) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(str(text or ""))]


def _content_tokens(text: Any) -> set[str]:
    return {token for token in _tokens(text) if len(token) > 2 and token not in STOPWORDS}


def _evidence_texts(record: dict[str, Any]) -> list[str]:
    """Only historical support resolutions count as evidence for a reply."""
    values: list[str] = []
    retrieved = record.get("retrieved_examples") or []
    if isinstance(retrieved, list):
        for item in retrieved:
            if isinstance(item, dict):
                values.append(item.get("amazonhelp_response", ""))
    return [str(value) for value in values if value]


def _specific_claims(text: str) -> list[str]:
    """Return URLs and numeric claims, preserving their original spelling."""
    claims = URL_RE.findall(text or "") + NUMBER_RE.findall(text or "")
    # A number which is part of a URL was already represented by the URL.
    urls = set(URL_RE.findall(text or ""))
    return [claim for claim in claims if not any(claim in url for url in urls)]


def evaluate_grounding(record: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one generated reply using only its record and retrieved evidence."""
    draft = str(record.get("draft_reply") or "").strip()
    evidence = _evidence_texts(record)
    evidence_text = " ".join(evidence).lower()
    draft_tokens = _content_tokens(draft)
    evidence_tokens = set().union(*(_content_tokens(value) for value in evidence)) if evidence else set()
    supported_tokens = draft_tokens & evidence_tokens
    token_rate = len(supported_tokens) / len(draft_tokens) if draft_tokens else 0.0

    claims = _specific_claims(draft)
    supported_claims = [claim for claim in claims if claim.lower().rstrip(".,") in evidence_text]
    unsupported_claims = [claim for claim in claims if claim not in supported_claims]
    claim_rate = len(supported_claims) / len(claims) if claims else 1.0
    score = (token_rate + claim_rate) / 2 if draft and evidence else 0.0
    return {
        "metric_version": "offline-grounding-v2",
        "example_id": record.get("example_id"),
        "has_reply": bool(draft),
        "evidence_count": len(record.get("retrieved_examples") or []),
        "draft_content_tokens": len(draft_tokens),
        "supported_content_tokens": len(supported_tokens),
        "evidence_token_support_rate": round(token_rate, 6),
        "specific_claim_count": len(claims),
        "supported_specific_claim_count": len(supported_claims),
        "unsupported_specific_claims": unsupported_claims,
        "unsupported_claim_rate": round(1.0 - claim_rate, 6),
        "grounding_score": round(score, 6),
    }


def evaluate_evidence(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Return per-example evidence checks and deterministic aggregate values."""
    rows = [evaluate_grounding(record) for record in records]
    n = len(rows)
    average = lambda key: sum(float(row[key]) for row in rows) / n if n else 0.0
    return {
        "examples_evaluated": n,
        "evidence_available_rate": (
            sum(row["evidence_count"] > 0 for row in rows) / n if n else 0.0
        ),
        "mean_grounding_score": round(average("grounding_score"), 6),
        "mean_evidence_token_support_rate": round(
            average("evidence_token_support_rate"), 6
        ),
        "unsupported_claim_rate": round(average("unsupported_claim_rate"), 6),
        "per_example": rows,
    }

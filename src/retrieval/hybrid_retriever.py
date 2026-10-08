"""Deterministic weighted fusion of lexical and semantic support evidence."""
from __future__ import annotations

import math
from typing import Any

from src.retrieval.interfaces import Retriever


class HybridRetriever:
    def __init__(
        self,
        lexical: Retriever,
        semantic: Retriever,
        *,
        lexical_weight: float = 0.5,
        semantic_weight: float = 0.5,
    ) -> None:
        weights = (lexical_weight, semantic_weight)
        if any(not math.isfinite(weight) or weight < 0 for weight in weights):
            raise ValueError("retrieval weights must be finite and non-negative")
        total = sum(weights)
        if total == 0:
            raise ValueError("at least one retrieval weight must be positive")
        self.lexical = lexical
        self.semantic = semantic
        self.lexical_weight = lexical_weight / total
        self.semantic_weight = semantic_weight / total

    def retrieve(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if k < 1:
            raise ValueError("k must be at least 1")
        merged: dict[str, dict[str, Any]] = {}
        for backend, score_name in (
            (self.lexical, "lexical_similarity"),
            (self.semantic, "semantic_similarity"),
        ):
            for row in backend.retrieve(query, k=k):
                key = _record_key(row)
                candidate = merged.setdefault(
                    key,
                    {
                        **row,
                        "lexical_similarity": 0.0,
                        "semantic_similarity": 0.0,
                    },
                )
                score = _validated_score(row.get("similarity", 0.0))
                candidate[score_name] = max(candidate[score_name], score)
                for field, value in row.items():
                    if field not in {
                        "similarity",
                        "lexical_similarity",
                        "semantic_similarity",
                    }:
                        candidate.setdefault(field, value)

        ranked = []
        candidate_count = len(merged)
        for key, row in merged.items():
            score = (
                self.lexical_weight * row["lexical_similarity"]
                + self.semantic_weight * row["semantic_similarity"]
            )
            ranked.append(
                {
                    **row,
                    "similarity": score,
                    "response_tweet_id": row.get("response_tweet_id", key),
                    "score_components": {
                        "lexical_similarity": row["lexical_similarity"],
                        "semantic_similarity": row["semantic_similarity"],
                        "lexical_weight": self.lexical_weight,
                        "semantic_weight": self.semantic_weight,
                    },
                    "retrieval_backend": "hybrid",
                    "candidate_count": candidate_count,
                    "candidate_count_scope": "union_of_component_top_k",
                }
            )
        ranked.sort(
            key=lambda row: (
                -row["similarity"],
                str(row["response_tweet_id"]),
            )
        )
        return ranked[:k]


def _record_key(row: dict[str, Any]) -> str:
    for field in ("response_tweet_id", "source_id", "customer_tweet_id"):
        value = row.get(field)
        if isinstance(value, str) and value:
            return value
    customer = row.get("customer_text", "")
    response = row.get("amazonhelp_response", "")
    if not isinstance(customer, str) or not isinstance(response, str):
        raise ValueError("retrieval records must include a stable ID or text pair")
    return f"{customer}\0{response}"


def _validated_score(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("retrieval scores must be numeric")
    score = float(value)
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("retrieval scores must be finite values between 0 and 1")
    return score

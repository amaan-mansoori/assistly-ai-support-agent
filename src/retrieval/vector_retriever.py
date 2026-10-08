"""Optional PostgreSQL pgvector retrieval backend."""
from __future__ import annotations

import math
from typing import Protocol, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import KnowledgeRecord

EMBEDDING_DIMENSIONS = 384


class EmbeddingProvider(Protocol):
    def encode(self, text: str) -> Sequence[float]:
        """Encode a query into a normalized fixed-size vector."""
        ...

    def encode_many(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Encode a batch of texts for reproducible knowledge ingestion."""
        ...


class FastEmbedEmbeddingProvider:
    """CPU-only local ONNX embeddings; tests may inject an offline fake provider."""

    def __init__(self, model_name: str) -> None:
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError(
                "Install requirements-embeddings.txt to use semantic retrieval."
            ) from exc
        self._model = TextEmbedding(
            model_name=model_name,
            providers=["CPUExecutionProvider"],
        )

    def encode(self, text: str) -> Sequence[float]:
        result = next(iter(self._model.query_embed(text)))
        return result.tolist()

    def encode_many(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        result = self._model.passage_embed(
            list(texts), batch_size=32
        )
        return [item.tolist() for item in result]


class VectorRetriever:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.session_factory = session_factory
        self.embedding_provider = embedding_provider

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        if k < 1:
            raise ValueError("k must be at least 1")
        vector = _validated_vector(self.embedding_provider.encode(query))
        distance = KnowledgeRecord.embedding.cosine_distance(vector).label("distance")
        statement = (
            select(KnowledgeRecord, distance)
            .order_by(distance, KnowledgeRecord.source_id)
            .limit(k)
        )
        with self.session_factory() as session:
            rows = session.execute(statement).all()
        candidate_count = len(rows)
        return [
            {
                "customer_tweet_id": row.customer_tweet_id,
                "response_tweet_id": row.source_id,
                "customer_text": row.customer_message,
                "amazonhelp_response": row.support_response,
                "similarity": max(0.0, min(1.0, 1.0 - float(distance_value))),
                "score_components": {
                    "semantic_similarity": max(
                        0.0, min(1.0, 1.0 - float(distance_value))
                    )
                },
                "retrieval_backend": "vector",
                "candidate_count": candidate_count,
                "candidate_count_scope": "database_top_k_rows_returned",
            }
            for row, distance_value in rows
        ]


def _validated_vector(vector: Sequence[float]) -> list[float]:
    if len(vector) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Embedding provider must return {EMBEDDING_DIMENSIONS} dimensions"
        )
    values = [float(value) for value in vector]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Embedding provider returned non-finite values")
    return values

"""Leakage-aware, repeatable import from validated historical conversation pairs."""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import KnowledgeRecord
from src.retrieval.vector_retriever import (
    EmbeddingProvider,
    _validated_vector,
)


def ingest_records(
    records: Sequence[dict[str, str]],
    session_factory: sessionmaker[Session],
    embedding_provider: EmbeddingProvider,
    *,
    batch_size: int = 128,
) -> dict[str, int]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    stats = {"records_seen": len(records), "inserted": 0, "updated": 0, "skipped": 0}
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        valid = [
            row for row in batch
            if row.get("customer_text", "").strip()
            and row.get("amazonhelp_response", "").strip()
            and row.get("response_tweet_id", "").strip()
            and row.get("customer_tweet_id", "").strip()
        ]
        stats["skipped"] += len(batch) - len(valid)
        if not valid:
            continue
        embeddings = embedding_provider.encode_many(
            [row["customer_text"] for row in valid]
        )
        if len(embeddings) != len(valid):
            raise ValueError("Embedding provider returned a different number of vectors than inputs")
        with session_factory() as session:
            try:
                for row, embedding in zip(valid, embeddings, strict=True):
                    vector = _validated_vector(embedding)
                    existing = session.scalar(
                        select(KnowledgeRecord).where(
                            KnowledgeRecord.source_id == row["response_tweet_id"]
                        )
                    )
                    values = {
                        "customer_tweet_id": row["customer_tweet_id"],
                        "customer_message": row["customer_text"],
                        "support_response": row["amazonhelp_response"],
                        "provenance": {
                            "customer_tweet_id": row["customer_tweet_id"],
                            "response_tweet_id": row["response_tweet_id"],
                        },
                        "embedding": vector,
                    }
                    if existing is None:
                        session.add(
                            KnowledgeRecord(
                                source_id=row["response_tweet_id"], **values
                            )
                        )
                        stats["inserted"] += 1
                    else:
                        for name, value in values.items():
                            setattr(existing, name, value)
                        stats["updated"] += 1
                session.commit()
            except Exception:
                session.rollback()
                raise
    return stats

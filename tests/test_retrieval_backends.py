from __future__ import annotations

import math
from typing import Any, cast

import numpy as np
import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.application.knowledge_ingestion import ingest_records
from src.db.database import Base, make_engine, make_session_factory
from src.db.models import KnowledgeRecord
from src.platform.config import PlatformSettings
from src.retrieval.historical_retriever import HistoricalRetriever
from src.retrieval import factory as retriever_factory
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.tfidf_retriever import TfidfRetriever
from src.retrieval.vector_retriever import FastEmbedEmbeddingProvider, VectorRetriever


def vector(value: float = 0.0) -> list[float]:
    return [value] + [0.0] * 383


class FakeEmbeddingProvider:
    def __init__(self):
        self.batches = []

    def encode(self, text):
        return vector(1.0 if "delivery" in text.lower() else 0.5)

    def encode_many(self, texts):
        self.batches.append(tuple(texts))
        return [self.encode(text) for text in texts]


def test_tfidf_adapter_preserves_existing_historical_retriever():
    assert issubclass(TfidfRetriever, HistoricalRetriever)
    retriever = TfidfRetriever([], np.zeros((0, 1)), None)

    assert retriever.retrieve("any message") == []


def test_knowledge_ingestion_is_idempotent_and_skips_invalid_records(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'knowledge.sqlite'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    provider = FakeEmbeddingProvider()
    records = [
        {
            "customer_tweet_id": "c1",
            "response_tweet_id": "r1",
            "customer_text": "Delivery status is late",
            "amazonhelp_response": "Check tracking",
        },
        {
            "customer_tweet_id": "c2",
            "response_tweet_id": "r2",
            "customer_text": "",
            "amazonhelp_response": "Empty customer row",
        },
    ]
    try:
        first = ingest_records(records, factory, provider, batch_size=1)
        changed = [dict(records[0], amazonhelp_response="Updated tracking instructions")]
        second = ingest_records(changed, factory, provider, batch_size=1)
        with factory() as session:
            rows = list(session.query(KnowledgeRecord).all())
        assert first == {
            "records_seen": 2,
            "inserted": 1,
            "updated": 0,
            "skipped": 1,
        }
        assert second["inserted"] == 0
        assert second["updated"] == 1
        assert rows[0].source_id == "r1"
        assert rows[0].support_response == "Updated tracking instructions"
        assert rows[0].embedding == vector(1.0)
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_vector_retriever_converts_cosine_distance_to_similarity():
    record = KnowledgeRecord(
        source_id="r1",
        customer_tweet_id="c1",
        customer_message="Late delivery",
        support_response="Check tracking",
        provenance={},
        embedding=vector(1.0),
    )

    class SessionContext:
        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> None:
            del _args

        def execute(self, _statement: object):
            del _statement
            return self

        def all(self):
            return [(record, 0.25)]

    factory = cast(sessionmaker[Session], lambda: SessionContext())
    retriever = VectorRetriever(factory, FakeEmbeddingProvider())

    result = retriever.retrieve("delivery status", k=1)

    assert result[0]["response_tweet_id"] == "r1"
    assert result[0]["similarity"] == 0.75
    assert result[0]["retrieval_backend"] == "vector"
    assert result[0]["score_components"]["semantic_similarity"] == 0.75
    assert result[0]["candidate_count_scope"] == "database_top_k_rows_returned"
    with pytest.raises(ValueError, match="at least 1"):
        retriever.retrieve("query", k=0)


def test_vector_backend_requires_postgresql(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-longer-than-32-bytes")
    monkeypatch.setenv("RETRIEVER_BACKEND", "vector")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///local.sqlite")

    with pytest.raises(ValueError, match="requires a PostgreSQL"):
        PlatformSettings.from_env()


def test_semantic_backend_requires_postgresql(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-longer-than-32-bytes")
    monkeypatch.setenv("RETRIEVER_BACKEND", "hybrid")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///local.sqlite")

    with pytest.raises(ValueError, match="requires a PostgreSQL"):
        PlatformSettings.from_env()


def test_hybrid_retriever_merges_deduplicates_and_ranks_weighted_scores():
    shared = {
        "response_tweet_id": "shared",
        "customer_text": "late delivery",
        "amazonhelp_response": "Check tracking.",
    }

    class StubRetriever:
        def __init__(self, rows):
            self.rows = rows

        def retrieve(self, query: str, k: int = 5) -> list[dict[str, Any]]:
            del query
            return self.rows[:k]

    retriever = HybridRetriever(
        StubRetriever([
            {**shared, "similarity": 0.6},
            {
                "response_tweet_id": "lexical",
                "customer_text": "tracking status",
                "amazonhelp_response": "Check the order page.",
                "similarity": 0.99,
            },
        ]),
        StubRetriever([
            {**shared, "similarity": 0.9},
            {
                "response_tweet_id": "semantic",
                "customer_text": "delivery progress",
                "amazonhelp_response": "Review shipment status.",
                "similarity": 0.8,
            },
        ]),
        lexical_weight=0.25,
        semantic_weight=0.75,
    )

    results = retriever.retrieve("where is my package", k=3)

    assert [item["response_tweet_id"] for item in results] == [
        "shared",
        "semantic",
        "lexical",
    ]
    assert results[0]["similarity"] == pytest.approx(0.825)
    assert results[0]["lexical_similarity"] == 0.6
    assert results[0]["semantic_similarity"] == 0.9
    assert results[0]["retrieval_backend"] == "hybrid"
    assert results[0]["score_components"] == {
        "lexical_similarity": 0.6,
        "semantic_similarity": 0.9,
        "lexical_weight": 0.25,
        "semantic_weight": 0.75,
    }
    assert results[0]["candidate_count_scope"] == "union_of_component_top_k"


def test_hybrid_retriever_handles_empty_results_and_rejects_bad_scores():
    class StubRetriever:
        def __init__(self, rows):
            self.rows = rows

        def retrieve(self, query: str, k: int = 5) -> list[dict[str, Any]]:
            del query
            return self.rows[:k]

    empty = HybridRetriever(StubRetriever([]), StubRetriever([]))
    assert empty.retrieve("missing") == []
    with pytest.raises(ValueError, match="at least 1"):
        empty.retrieve("missing", k=0)
    with pytest.raises(ValueError, match="between 0 and 1"):
        HybridRetriever(
            StubRetriever([{"response_tweet_id": "bad", "similarity": math.nan}]),
            StubRetriever([]),
        ).retrieve("bad")
    with pytest.raises(ValueError, match="at least one retrieval weight"):
        HybridRetriever(StubRetriever([]), StubRetriever([]), lexical_weight=0, semantic_weight=0)


def test_fastembed_provider_uses_cpu_query_and_passage_paths(monkeypatch):
    calls = {}

    class FakeVector:
        def __init__(self, value):
            self.value = value

        def tolist(self):
            return vector(self.value)

    class FakeModel:
        def __init__(self, model_name, providers):
            calls["model_name"] = model_name
            calls["providers"] = providers

        def query_embed(self, text):
            calls["query"] = text
            return iter([FakeVector(1.0)])

        def passage_embed(self, texts, batch_size):
            calls["passages"] = texts
            calls["batch_size"] = batch_size
            return iter([FakeVector(0.5) for _ in texts])

    import sys
    import types

    monkeypatch.setitem(
        sys.modules,
        "fastembed",
        types.SimpleNamespace(TextEmbedding=FakeModel),
    )
    provider = FastEmbedEmbeddingProvider("BAAI/bge-small-en-v1.5")

    query = provider.encode("delivery query")
    passages = provider.encode_many(["delivery passage", "other passage"])

    assert calls["providers"] == ["CPUExecutionProvider"]
    assert calls["model_name"] == "BAAI/bge-small-en-v1.5"
    assert calls["query"] == "delivery query"
    assert calls["passages"] == ["delivery passage", "other passage"]
    assert calls["batch_size"] == 32
    assert len(query) == len(passages[0]) == 384


def test_hybrid_factory_wires_configured_backends(monkeypatch):
    lexical = object()
    semantic = object()
    monkeypatch.setattr(
        retriever_factory, "_build_lexical_retriever", lambda: lexical
    )
    monkeypatch.setattr(
        retriever_factory,
        "_build_vector_retriever",
        lambda _settings, _factory: semantic,
    )
    settings = PlatformSettings(
        app_env="test",
        database_url="postgresql+psycopg://test:test@localhost/test",
        redis_url=None,
        jwt_secret="test-secret",
        log_level="INFO",
        retriever_backend="hybrid",
        hybrid_lexical_weight=0.3,
        hybrid_semantic_weight=0.7,
    )

    result = retriever_factory.build_retriever(settings, sessionmaker())

    assert isinstance(result, HybridRetriever)
    assert result.lexical is lexical
    assert result.semantic is semantic
    assert result.lexical_weight == pytest.approx(0.3)
    assert result.semantic_weight == pytest.approx(0.7)


def test_hybrid_retrieval_configuration_reads_and_validates_weights(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-longer-than-32-bytes")
    monkeypatch.setenv("RETRIEVER_BACKEND", "hybrid")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://support:support@localhost/support",
    )
    monkeypatch.setenv("HYBRID_LEXICAL_WEIGHT", "0.25")
    monkeypatch.setenv("HYBRID_SEMANTIC_WEIGHT", "0.75")

    settings = PlatformSettings.from_env()

    assert settings.retriever_backend == "hybrid"
    assert settings.hybrid_lexical_weight == 0.25
    assert settings.hybrid_semantic_weight == 0.75

    monkeypatch.setenv("HYBRID_LEXICAL_WEIGHT", "nan")
    with pytest.raises(ValueError, match="finite"):
        PlatformSettings.from_env()


def test_embedding_shape_and_non_finite_values_are_rejected():
    from src.retrieval.vector_retriever import _validated_vector

    with pytest.raises(ValueError, match="384 dimensions"):
        _validated_vector([1.0])
    with pytest.raises(ValueError, match="non-finite"):
        _validated_vector([math.nan] + [0.0] * 383)

"""Construct the configured retrieval backend for application/runtime use."""
from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from src.platform.config import PlatformSettings
from src.retrieval.historical_retriever import HistoricalRetriever
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.interfaces import Retriever
from src.retrieval.tfidf_retriever import TfidfRetriever
from src.retrieval.vector_retriever import FastEmbedEmbeddingProvider, VectorRetriever


def _build_lexical_retriever() -> TfidfRetriever:
    historical, _ = HistoricalRetriever.build()
    return TfidfRetriever(
        historical.records,
        historical.embeddings,
        historical.encoder,
    )


def _build_vector_retriever(
    settings: PlatformSettings,
    session_factory: sessionmaker[Session],
) -> VectorRetriever:
    return VectorRetriever(
        session_factory,
        FastEmbedEmbeddingProvider(settings.embedding_model),
    )


def build_retriever(
    settings: PlatformSettings,
    session_factory: sessionmaker[Session],
) -> Retriever:
    if settings.retriever_backend == "vector":
        return _build_vector_retriever(settings, session_factory)
    if settings.retriever_backend == "hybrid":
        return HybridRetriever(
            _build_lexical_retriever(),
            _build_vector_retriever(settings, session_factory),
            lexical_weight=settings.hybrid_lexical_weight,
            semantic_weight=settings.hybrid_semantic_weight,
        )
    return _build_lexical_retriever()

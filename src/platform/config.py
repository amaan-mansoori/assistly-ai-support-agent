"""Validated environment configuration for the HTTP platform."""
from __future__ import annotations

import os
import secrets
import math
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class PlatformSettings:
    app_env: str
    database_url: str
    redis_url: str | None
    jwt_secret: str
    log_level: str
    rate_limit_per_minute: int = 60
    cors_origins: tuple[str, ...] = ()
    retriever_backend: str = "tfidf"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    hybrid_lexical_weight: float = 0.5
    hybrid_semantic_weight: float = 0.5
    conversation_history_window: int = 12
    conversation_history_max_chars: int = 12_000

    @classmethod
    def from_env(cls) -> PlatformSettings:
        load_dotenv()
        app_env = os.getenv("APP_ENV", "development").strip().lower()
        if app_env not in {"development", "test", "production"}:
            raise ValueError("APP_ENV must be development, test, or production")
        jwt_secret = os.getenv("JWT_SECRET", "")
        if app_env == "production" and len(jwt_secret) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters in production")
        if not jwt_secret:
            jwt_secret = secrets.token_urlsafe(48)
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL is not a supported logging level")
        database_url = os.getenv("DATABASE_URL", "sqlite:///./support_agent.db")
        if not database_url.startswith(("sqlite:", "postgresql+psycopg://")):
            raise ValueError("DATABASE_URL must use SQLite or PostgreSQL with psycopg")
        try:
            rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        except ValueError as exc:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be a positive integer") from exc
        if rate_limit < 1:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be a positive integer")
        try:
            history_window = int(os.getenv("SUPPORT_AGENT_HISTORY_WINDOW", "12"))
            history_max_chars = int(
                os.getenv("SUPPORT_AGENT_HISTORY_MAX_CHARS", "12000")
            )
        except ValueError as exc:
            raise ValueError("Conversation history limits must be positive integers") from exc
        if history_window < 1 or history_max_chars < 1:
            raise ValueError("Conversation history limits must be positive integers")
        configured_origins = os.getenv("CORS_ORIGINS", "")
        cors_origins = tuple(
            origin.strip().rstrip("/")
            for origin in configured_origins.split(",")
            if origin.strip()
        )
        if "*" in cors_origins:
            raise ValueError("CORS_ORIGINS must not contain a wildcard")
        if app_env == "development" and not cors_origins:
            cors_origins = ("http://localhost:3000",)
        retriever_backend = os.getenv("RETRIEVER_BACKEND", "tfidf").strip().lower()
        if retriever_backend not in {"tfidf", "vector", "hybrid"}:
            raise ValueError("RETRIEVER_BACKEND must be tfidf, vector, or hybrid")
        embedding_model = os.getenv(
            "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"
        ).strip()
        if retriever_backend in {"vector", "hybrid"} and not embedding_model:
            raise ValueError("EMBEDDING_MODEL must be set for semantic retrieval")
        if retriever_backend in {"vector", "hybrid"} and not database_url.startswith(
            "postgresql+psycopg://"
        ):
            raise ValueError("Semantic retrieval requires a PostgreSQL DATABASE_URL")
        try:
            lexical_weight = float(os.getenv("HYBRID_LEXICAL_WEIGHT", "0.5"))
            semantic_weight = float(os.getenv("HYBRID_SEMANTIC_WEIGHT", "0.5"))
        except ValueError as exc:
            raise ValueError("Hybrid retrieval weights must be finite non-negative numbers") from exc
        if any(
            not math.isfinite(weight) or weight < 0
            for weight in (lexical_weight, semantic_weight)
        ) or lexical_weight + semantic_weight == 0:
            raise ValueError(
                "Hybrid retrieval weights must be finite, non-negative, and not both zero"
            )
        return cls(
            app_env=app_env,
            database_url=database_url,
            redis_url=os.getenv("REDIS_URL") or None,
            jwt_secret=jwt_secret,
            log_level=log_level,
            rate_limit_per_minute=rate_limit,
            cors_origins=cors_origins,
            retriever_backend=retriever_backend,
            embedding_model=embedding_model,
            hybrid_lexical_weight=lexical_weight,
            hybrid_semantic_weight=semantic_weight,
            conversation_history_window=history_window,
            conversation_history_max_chars=history_max_chars,
        )

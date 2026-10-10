"""Runtime agent configuration loaded from the repository YAML and environment."""
from __future__ import annotations

import os
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

DEFAULT_CONFIG = Path("configs/default.yaml")


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _unit_interval(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number between 0 and 1")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be a number between 0 and 1")
    return float(value)


@dataclass(frozen=True)
class AgentConfig:
    top_k: int = 5
    minimum_retrieval_similarity: float = 0.1
    minimum_grounding_token_support: float = 0.5
    escalation_confidence_threshold: float = 0.7
    provider: str = "gemini"
    model: str = "gemini-3.8-flash"
    provider_timeout_seconds: float = 30.0
    provider_max_retries: int = 2
    history_window: int = 12
    history_max_chars: int = 12_000

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG) -> AgentConfig:
        load_dotenv()
        values: dict[str, Any] = {}
        if path.exists():
            with path.open(encoding="utf-8") as handle:
                config = yaml.safe_load(handle) or {}
            if not isinstance(config, dict):
                raise ValueError(f"{path} must contain a YAML mapping")
            retrieval = config.get("retrieval", {})
            agent = config.get("agent", {})
            if not isinstance(retrieval, dict) or not isinstance(agent, dict):
                raise ValueError("retrieval and agent configuration must be mappings")
            values = {
                "top_k": retrieval.get("top_k", cls.top_k),
                "minimum_retrieval_similarity": retrieval.get(
                    "minimum_similarity", cls.minimum_retrieval_similarity
                ),
                "minimum_grounding_token_support": agent.get(
                    "minimum_grounding_token_support",
                    cls.minimum_grounding_token_support,
                ),
                "escalation_confidence_threshold": agent.get(
                    "escalation_threshold", cls.escalation_confidence_threshold
                ),
                "provider": agent.get("llm_provider", cls.provider),
                "model": agent.get("model_name", cls.model),
                "provider_timeout_seconds": agent.get(
                    "provider_timeout_seconds", cls.provider_timeout_seconds
                ),
                "provider_max_retries": agent.get(
                    "provider_max_retries", cls.provider_max_retries
                ),
                "history_window": agent.get("history_window", cls.history_window),
                "history_max_chars": agent.get(
                    "history_max_chars", cls.history_max_chars
                ),
            }
        env_values = {
            "top_k": os.getenv("SUPPORT_AGENT_TOP_K"),
            "minimum_retrieval_similarity": os.getenv(
                "SUPPORT_AGENT_MIN_RETRIEVAL_SIMILARITY"
            ),
            "minimum_grounding_token_support": os.getenv(
                "SUPPORT_AGENT_MIN_GROUNDING_TOKEN_SUPPORT"
            ),
            "escalation_confidence_threshold": os.getenv(
                "SUPPORT_AGENT_ESCALATION_THRESHOLD"
            ),
            "provider": os.getenv("SUPPORT_AGENT_PROVIDER"),
            "model": os.getenv("SUPPORT_AGENT_MODEL"),
            "provider_timeout_seconds": os.getenv(
                "SUPPORT_AGENT_TIMEOUT_SECONDS"
            ),
            "provider_max_retries": os.getenv(
                "SUPPORT_AGENT_MAX_RETRIES"
            ),
            "history_window": os.getenv("SUPPORT_AGENT_HISTORY_WINDOW"),
            "history_max_chars": os.getenv("SUPPORT_AGENT_HISTORY_MAX_CHARS"),
        }
        for key, value in env_values.items():
            if value is not None:
                try:
                    if key in {
                        "top_k",
                        "provider_max_retries",
                        "history_window",
                        "history_max_chars",
                    }:
                        values[key] = int(value)
                    elif key in {
                        "minimum_retrieval_similarity",
                        "minimum_grounding_token_support",
                        "escalation_confidence_threshold",
                        "provider_timeout_seconds",
                    }:
                        values[key] = float(value)
                    else:
                        values[key] = value
                except ValueError as exc:
                    raise ValueError(f"Invalid {key} environment setting") from exc

        config = cls(**values)
        _positive_int(config.top_k, "top_k")
        if (
            isinstance(config.provider_max_retries, bool)
            or not isinstance(config.provider_max_retries, int)
            or not 0 <= config.provider_max_retries <= 5
        ):
            raise ValueError("provider_max_retries must be an integer between 0 and 5")
        if (
            isinstance(config.provider_timeout_seconds, bool)
            or not isinstance(config.provider_timeout_seconds, (int, float))
            or not math.isfinite(config.provider_timeout_seconds)
            or config.provider_timeout_seconds <= 0
        ):
            raise ValueError("provider_timeout_seconds must be a positive finite number")
        _positive_int(config.history_window, "history_window")
        _positive_int(config.history_max_chars, "history_max_chars")
        _unit_interval(
            config.minimum_retrieval_similarity, "minimum_retrieval_similarity"
        )
        _unit_interval(
            config.minimum_grounding_token_support,
            "minimum_grounding_token_support",
        )
        _unit_interval(
            config.escalation_confidence_threshold,
            "escalation_confidence_threshold",
        )
        if config.provider not in {"gemini", "openai"}:
            raise ValueError("provider must be 'gemini' or 'openai'")
        if not isinstance(config.model, str) or not config.model.strip():
            raise ValueError("model must be a non-empty string")
        return config

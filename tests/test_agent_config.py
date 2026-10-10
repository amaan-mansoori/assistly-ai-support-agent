import pytest

from src.agent.config import AgentConfig


def test_default_gemini_model_is_current_flash_model(tmp_path, monkeypatch):
    monkeypatch.delenv("SUPPORT_AGENT_MODEL", raising=False)

    config = AgentConfig.load(tmp_path / "missing.yaml")

    assert config.provider == "gemini"
    assert config.model == "gemini-3.8-flash"


def test_yaml_configuration_is_overridden_by_environment(tmp_path, monkeypatch):
    config_path = tmp_path / "agent.yaml"
    config_path.write_text(
        "retrieval:\n"
        "  top_k: 4\n"
        "  minimum_similarity: 0.2\n"
        "agent:\n"
        "  llm_provider: openai\n"
        "  model_name: yaml-model\n"
        "  provider_timeout_seconds: 12\n"
        "  provider_max_retries: 4\n"
        "  minimum_grounding_token_support: 0.6\n"
        "  escalation_threshold: 0.8\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SUPPORT_AGENT_TOP_K", "7")
    monkeypatch.setenv("SUPPORT_AGENT_MODEL", "environment-model")
    monkeypatch.setenv("SUPPORT_AGENT_TIMEOUT_SECONDS", "8")

    config = AgentConfig.load(config_path)

    assert config.top_k == 7
    assert config.minimum_retrieval_similarity == 0.2
    assert config.provider == "openai"
    assert config.model == "environment-model"
    assert config.provider_timeout_seconds == 8
    assert config.provider_max_retries == 4
    assert config.minimum_grounding_token_support == 0.6
    assert config.escalation_confidence_threshold == 0.8


def test_invalid_environment_configuration_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPPORT_AGENT_TOP_K", "0")

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        AgentConfig.load(tmp_path / "missing.yaml")


def test_unknown_provider_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPPORT_AGENT_PROVIDER", "unsupported")

    with pytest.raises(ValueError, match="provider must be"):
        AgentConfig.load(tmp_path / "missing.yaml")


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("SUPPORT_AGENT_TIMEOUT_SECONDS", "nan", "positive finite"),
        ("SUPPORT_AGENT_TIMEOUT_SECONDS", "0", "positive finite"),
        ("SUPPORT_AGENT_MAX_RETRIES", "6", "between 0 and 5"),
        ("SUPPORT_AGENT_MAX_RETRIES", "-1", "between 0 and 5"),
        ("SUPPORT_AGENT_HISTORY_WINDOW", "0", "history_window must be"),
        ("SUPPORT_AGENT_HISTORY_MAX_CHARS", "-1", "history_max_chars must be"),
    ],
)
def test_invalid_provider_resilience_settings_are_rejected(
    tmp_path, monkeypatch, name, value, message
):
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=message):
        AgentConfig.load(tmp_path / "missing.yaml")

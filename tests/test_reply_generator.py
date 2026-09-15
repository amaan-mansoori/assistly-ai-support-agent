import json
import sys
import types
import pytest

from src.agent.reply_generator import (
    SYSTEM_PROMPT, GeminiRateLimiter, ReplyGenerationError, build_prompt, configured_llm_call,
    generate_reply, gemini_call, antigravity_call, parse_model_output
)

EVIDENCE = [{"similarity": 0.8, "customer_text": "late order",
             "amazonhelp_response": "Please check tracking.", "customer_tweet_id": "1",
             "response_tweet_id": "2"}]


def test_valid_output_is_parsed_without_retrieval_metadata():
    result = generate_reply("Where is my order?", "delivery_status_delay", EVIDENCE,
                            lambda s, u: json.dumps({"draft_reply": "Please check tracking.",
                            "grounding_confidence": .8, "needs_human_review": False, "reason": "Supported."}))
    assert result["draft_reply"] == "Please check tracking."
    assert "tweet" not in result["draft_reply"].lower()


def test_malformed_json_is_rejected():
    with pytest.raises(ReplyGenerationError, match="malformed"):
        parse_model_output("{bad")


def test_invalid_confidence_and_missing_reply_are_rejected():
    with pytest.raises(ReplyGenerationError, match="confidence"):
        parse_model_output(json.dumps({"draft_reply": "x", "grounding_confidence": 2,
                                       "needs_human_review": False, "reason": "x"}))
    with pytest.raises(ReplyGenerationError, match="draft_reply"):
        parse_model_output(json.dumps({"grounding_confidence": .5,
                                       "needs_human_review": False, "reason": "x"}))


def test_prompt_contains_evidence_and_safety_instructions():
    prompt = build_prompt("Where is my order?", "delivery_status_delay", EVIDENCE)
    assert "late order" in prompt
    assert "Please check tracking." in prompt
    assert "Historical evidence" in prompt
    assert "passwords, OTPs, CVVs" in SYSTEM_PROMPT


def test_gemini_call_uses_configured_model_without_network(monkeypatch):
    calls = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.update(kwargs)
            return types.SimpleNamespace(text=json.dumps({
                "draft_reply": "Please check tracking.", "grounding_confidence": 0.8,
                "needs_human_review": False, "reason": "Supported."
            }))

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.models = FakeModels()

    fake_genai = types.SimpleNamespace(Client=FakeClient)
    fake_types = types.SimpleNamespace(
        GenerateContentConfig=lambda **kwargs: kwargs,
        AutomaticFunctionCallingConfig=lambda **kwargs: kwargs,
    )
    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", types.SimpleNamespace(types=fake_types))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("SUPPORT_AGENT_MODEL", "gemini-test")
    call = gemini_call()
    result = generate_reply("Where is my order?", "delivery_status_delay", EVIDENCE, call)
    assert result["draft_reply"] == "Please check tracking."
    assert calls["model"] == "gemini-test"
    assert calls["config"]["response_mime_type"] == "application/json"
    assert calls["config"]["automatic_function_calling"]["disable"] is True


def test_gemini_flash_lite_rate_limiter_waits_between_requests(monkeypatch):
    calls = []
    clock = [0.0]
    sleeps = []

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return types.SimpleNamespace(text=json.dumps({
                "draft_reply": "Please check tracking.", "grounding_confidence": 0.8,
                "needs_human_review": False, "reason": "Supported."
            }))

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(
        genai=types.SimpleNamespace(Client=FakeClient)
    ))
    fake_types = types.SimpleNamespace(
        GenerateContentConfig=lambda **kwargs: kwargs,
        AutomaticFunctionCallingConfig=lambda **kwargs: kwargs,
    )
    monkeypatch.setitem(sys.modules, "google.genai", types.SimpleNamespace(types=fake_types))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    limiter = GeminiRateLimiter(
        monotonic_fn=lambda: clock[0],
        sleep_fn=lambda seconds: (sleeps.append(seconds), clock.__setitem__(0, clock[0] + seconds)),
    )
    call = gemini_call("gemini-3.1-flash-lite", limiter)
    call("system", "user")
    call("system", "user")
    assert len(calls) == 2
    assert sleeps == [4.5]


def test_other_gemini_models_are_not_rate_limited(monkeypatch):
    sleeps = []

    class FakeModels:
        def generate_content(self, **kwargs):
            return types.SimpleNamespace(text='{"draft_reply":"x","grounding_confidence":0.5,"needs_human_review":false,"reason":"ok"}')

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(
        genai=types.SimpleNamespace(Client=FakeClient)
    ))
    fake_types = types.SimpleNamespace(
        GenerateContentConfig=lambda **kwargs: kwargs,
        AutomaticFunctionCallingConfig=lambda **kwargs: kwargs,
    )
    monkeypatch.setitem(sys.modules, "google.genai", types.SimpleNamespace(types=fake_types))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    call = gemini_call("gemini-2.0-flash")
    call("system", "user")
    call("system", "user")
    assert sleeps == []


def test_missing_gemini_key_fails_clearly(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        gemini_call()


def test_configured_provider_prefers_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("src.agent.reply_generator.gemini_call", lambda: "gemini")
    assert configured_llm_call() == "gemini"


def test_antigravity_interactions_api_uses_model_and_structured_output(monkeypatch):
    calls = {}

    class FakeInteractions:
        def create(self, **kwargs):
            calls.update(kwargs)
            return types.SimpleNamespace(output_text=json.dumps({
                "draft_reply": "Please check tracking.", "grounding_confidence": 0.8,
                "needs_human_review": False, "reason": "Supported."
            }))

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.interactions = FakeInteractions()

    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(
        genai=types.SimpleNamespace(Client=FakeClient)
    ))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("SUPPORT_AGENT_MODEL", "antigravity-preview-05-2026")
    result = generate_reply("Where is my order?", "delivery_status_delay", EVIDENCE,
                            antigravity_call())
    assert result["draft_reply"] == "Please check tracking."
    assert calls["model"] == "antigravity-preview-05-2026"
    assert "system_instruction" not in calls
    assert "Support-agent instructions:" in calls["input"]
    assert "Never request passwords, OTPs, CVVs" in calls["input"]
    assert "Where is my order?" in calls["input"]
    assert calls["response_format"]["mime_type"] == "application/json"
    assert calls["response_format"]["schema"]["required"] == [
        "draft_reply", "grounding_confidence", "needs_human_review", "reason"
    ]


def test_antigravity_extracts_fenced_json_from_realistic_response(monkeypatch):
    class FakeInteractions:
        def create(self, **kwargs):
            return types.SimpleNamespace(
                output_text="""```json
{"draft_reply":"Please check tracking.","grounding_confidence":0.8,"needs_human_review":false,"reason":"Supported."}
```"""
            )

    class FakeClient:
        def __init__(self, api_key):
            self.interactions = FakeInteractions()

    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(
        genai=types.SimpleNamespace(Client=FakeClient)
    ))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    result = generate_reply(
        "Where is my order?", "delivery_status_delay", EVIDENCE, antigravity_call()
    )
    assert result["draft_reply"] == "Please check tracking."


def test_antigravity_extracts_text_from_interaction_steps(monkeypatch):
    text = types.SimpleNamespace(
        type="text",
        text='{"draft_reply":"Please check tracking.","grounding_confidence":0.8,'
             '"needs_human_review":false,"reason":"Supported."}',
    )
    step = types.SimpleNamespace(type="model_output", content=[text])

    class FakeInteractions:
        def create(self, **kwargs):
            return types.SimpleNamespace(output_text="", steps=[step])

    class FakeClient:
        def __init__(self, api_key):
            self.interactions = FakeInteractions()

    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(
        genai=types.SimpleNamespace(Client=FakeClient)
    ))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    result = generate_reply(
        "Where is my order?", "delivery_status_delay", EVIDENCE, antigravity_call()
    )
    assert result["grounding_confidence"] == 0.8


def test_configured_provider_selects_antigravity(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("SUPPORT_AGENT_MODEL", "antigravity-preview-05-2026")
    monkeypatch.setattr("src.agent.reply_generator.antigravity_call", lambda: "antigravity")
    assert configured_llm_call() == "antigravity"


def test_configured_provider_requires_one_provider_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY.*OPENAI_API_KEY"):
        configured_llm_call()

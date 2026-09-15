import json
from pathlib import Path

from src.evaluation.generate_golden_replies import (
    classify_failure, generate_rows, load_existing_records
)


def _row(example_id):
    return {"example_id": example_id, "customer_tweet_id": example_id,
            "customer_text": f"question {example_id}", "human_intent": "other_unclear"}


def _reply():
    return {"draft_reply": "Please contact support.", "grounding_confidence": 0.5,
            "needs_human_review": True, "reason": "Limited evidence."}


class Retriever:
    def retrieve(self, text, k):
        return [{"similarity": 0.2, "customer_text": text,
                 "amazonhelp_response": "Please contact support.",
                 "customer_tweet_id": "historical", "response_tweet_id": "response"}]


def test_existing_records_preserved_and_ids_skipped(tmp_path: Path, monkeypatch):
    output = tmp_path / "out.jsonl"
    existing = {**_row("one"), "retrieved_examples": [], **_reply()}
    output.write_text(json.dumps(existing) + "\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr("src.evaluation.generate_golden_replies.generate_reply",
                        lambda *args: calls.append(args) or _reply())
    count, failed = generate_rows([_row("one"), _row("two")], Retriever(), lambda *_: "", output)
    records = load_existing_records(output)
    assert failed is None and count == 2
    assert set(records) == {"one", "two"}
    assert len(calls) == 1


def test_duplicate_existing_ids_are_collapsed(tmp_path: Path):
    output = tmp_path / "out.jsonl"
    record = {**_row("one"), "retrieved_examples": [], **_reply()}
    output.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n", encoding="utf-8")
    records = load_existing_records(output)
    assert list(records) == ["one"]


def test_failure_preserves_previous_successes_and_resumes(tmp_path: Path, monkeypatch):
    output = tmp_path / "out.jsonl"
    calls = []

    def fail_second(*args):
        calls.append(args[0])
        if args[0] == "question two":
            raise RuntimeError("simulated API failure")
        return _reply()

    monkeypatch.setattr("src.evaluation.generate_golden_replies.generate_reply", fail_second)
    count, failed = generate_rows([_row("one"), _row("two"), _row("three")],
                                  Retriever(), lambda *_: "", output)
    assert count == 1 and failed["example_id"] == "two"
    assert set(load_existing_records(output)) == {"one"}

    monkeypatch.setattr("src.evaluation.generate_golden_replies.generate_reply",
                        lambda *args: _reply())
    count, failed = generate_rows([_row("one"), _row("two"), _row("three")],
                                  Retriever(), lambda *_: "", output)
    assert failed is None and count == 3
    records = load_existing_records(output)
    assert len(records) == 3
    assert len(output.read_text(encoding="utf-8").splitlines()) == 3


class ApiError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


def test_retryable_429_and_5xx_then_success(tmp_path: Path, monkeypatch):
    attempts = {"n": 0}
    monkeypatch.setattr("src.evaluation.generate_golden_replies.generate_reply",
                        lambda *args: (_ for _ in ()).throw(ApiError(429, "rate limit"))
                        if (attempts.update(n=attempts["n"] + 1) or attempts["n"]) < 3
                        else _reply())
    count, failure = generate_rows([_row("one")], Retriever(), lambda *_: "", tmp_path / "x",
                                   sleep_fn=lambda _: None)
    assert count == 1 and failure is None and attempts["n"] == 3
    retryable, diag = classify_failure(ApiError(503, "server unavailable"))
    assert retryable and diag["retryable"] is True


def test_retryable_timeout_and_nonretryable_errors():
    assert classify_failure(TimeoutError("timed out"))[0]
    assert not classify_failure(ApiError(400, "invalid request"))[0]
    assert not classify_failure(ValueError("malformed JSON"))[0]


def test_retry_exhaustion_and_secret_redaction(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-value")
    monkeypatch.setattr("src.evaluation.generate_golden_replies.generate_reply",
                        lambda *args: (_ for _ in ()).throw(ApiError(429, "secret-value quota")))
    count, failure = generate_rows([_row("one")], Retriever(), lambda *_: "", tmp_path / "x",
                                   sleep_fn=lambda _: None)
    assert count == 0 and failure["attempts"] == 3
    assert failure["retryable"] is True
    assert "secret-value" not in failure["message"]

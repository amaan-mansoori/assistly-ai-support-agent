import json
from pathlib import Path

import pytest

from src.evaluation.generate_golden_replies import (
    classify_failure,
    generate_rows,
    load_existing_records,
    sanitize_legacy_artifact,
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
    assert count == 1
    assert failed is not None and failed["example_id"] == "two"
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
    assert count == 0
    assert failure is not None and failure["attempts"] == 3
    assert failure["retryable"] is True
    assert "secret-value" not in json.dumps(failure)


def test_new_generation_artifacts_drop_customer_text_ids_and_sensitive_values(
    tmp_path: Path, monkeypatch
):
    query = "My private account email is customer@example.test"
    context = "Earlier no personal details."
    google_key = "AIza" + "012345678901234567890"
    openai_key = "sk-" + "abcdefghijklmnopqrstuvw1234567890"
    bearer = "Bearer " + "token-secret"
    output = tmp_path / "out.jsonl"
    monkeypatch.setattr(
        "src.evaluation.generate_golden_replies.generate_reply",
        lambda *_: {
            **_reply(),
            "draft_reply": (
            f"We received: {query} at 555-123-4567. {bearer} "
            f"{google_key} {openai_key}"
            ),
        },
    )

    count, failure = generate_rows(
        [{
            **_row("one"),
            "customer_text": query,
            "conversation_context": context,
        }],
        Retriever(),
        lambda *_: "",
        output,
    )

    content = output.read_text(encoding="utf-8")
    assert count == 1 and failure is None
    assert query not in content
    assert context not in content
    assert "customer@example.test" not in content
    assert "555-123-4567" not in content
    assert "token-secret" not in content
    assert google_key not in content
    assert openai_key not in content
    assert "customer_tweet_id" not in content
    assert "[REDACTED]" in content


def test_legacy_artifact_migration_preserves_eval_fields_and_removes_text(
    tmp_path: Path,
):
    query = "My exact question should not be retained"
    legacy = {
        **_row("one"),
        "conversation_context": "Earlier private context",
        "retrieved_examples": [{
            "customer_text": query,
            "amazonhelp_response": "Please contact support.",
            "response_tweet_id": "response-1",
            "customer_tweet_id": "private-id",
            "similarity": 0.9,
        }],
        **_reply(),
        "draft_reply": f"We saw: {query}",
    }
    source = tmp_path / "legacy.jsonl"
    destination = tmp_path / "sanitized.jsonl"
    source.write_text(json.dumps(legacy) + "\n", encoding="utf-8")

    summary = sanitize_legacy_artifact(
        source, destination, {"one": query}
    )

    content = destination.read_text(encoding="utf-8")
    migrated = json.loads(content)
    assert summary["records"] == 1
    assert migrated["example_id"] == "one"
    assert migrated["retrieved_examples"][0]["amazonhelp_response"] == (
        "Please contact support."
    )
    assert migrated["retrieved_examples"][0]["response_tweet_id"] == "response-1"
    assert query not in content
    assert "customer_text" not in content
    assert "customer_tweet_id" not in content
    assert "conversation_context" not in content
    assert migrated["artifact_schema_version"] == "assistly-reply-generation-v2"


@pytest.mark.parametrize("duplicate", [False, True])
def test_legacy_migration_fails_closed_without_changing_destination(
    tmp_path: Path, duplicate: bool
):
    valid = {
        **_row("one"),
        "retrieved_examples": [],
        **_reply(),
    }
    malformed_line = "not JSON\n" if not duplicate else json.dumps(valid) + "\n"
    source = tmp_path / "legacy.jsonl"
    destination = tmp_path / "sanitized.jsonl"
    source.write_text(
        json.dumps(valid) + "\n" + malformed_line,
        encoding="utf-8",
    )
    destination.write_text("previous destination\n", encoding="utf-8")

    with pytest.raises(ValueError):
        sanitize_legacy_artifact(source, destination)

    assert destination.read_text(encoding="utf-8") == "previous destination\n"


def test_legacy_migration_rejects_invalid_evaluation_fields(tmp_path: Path):
    source = tmp_path / "legacy.jsonl"
    destination = tmp_path / "sanitized.jsonl"
    record = {**_row("one"), "retrieved_examples": [], **_reply()}
    record["grounding_confidence"] = float("nan")
    source.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid evaluation fields"):
        sanitize_legacy_artifact(source, destination)

    assert not destination.exists()


def test_legacy_migration_refuses_to_replace_existing_separate_artifact(
    tmp_path: Path,
):
    source = tmp_path / "legacy.jsonl"
    destination = tmp_path / "sanitized.jsonl"
    source.write_text(
        json.dumps({**_row("one"), "retrieved_examples": [], **_reply()}) + "\n",
        encoding="utf-8",
    )
    destination.write_text("existing artifact\n", encoding="utf-8")

    with pytest.raises(ValueError, match="already exists"):
        sanitize_legacy_artifact(source, destination)

    assert destination.read_text(encoding="utf-8") == "existing artifact\n"


def test_checked_in_generation_artifact_is_customer_text_minimized():
    import csv

    from src.evaluation.generate_golden_replies import GOLDEN, OUTPUT

    content = OUTPUT.read_text(encoding="utf-8")
    records = [json.loads(line) for line in content.splitlines() if line.strip()]
    with GOLDEN.open(encoding="utf-8", newline="") as handle:
        customer_texts = [row["customer_text"] for row in csv.DictReader(handle)]

    assert len(records) == 220
    assert all(
        record.get("artifact_schema_version") == "assistly-reply-generation-v2"
        for record in records
    )
    assert all(
        "customer_text" not in record
        and "customer_tweet_id" not in record
        and "customer_author_id" not in record
        and "conversation_context" not in record
        for record in records
    )
    assert all(
        "customer_text" not in json.dumps(record["retrieved_examples"])
        and "customer_tweet_id" not in json.dumps(record["retrieved_examples"])
        for record in records
    )
    assert not any(text and text in content for text in customer_texts)
    assert "AIza" not in content
    assert "Bearer " not in content

import json
import sys
from pathlib import Path

import pytest

from src.evaluation.generate_final_report import build_report, write_reports
from src.evaluation.grounding import evaluate_grounding
from src.evaluation.human_agreement import (
    cohen_kappa,
    load_annotations,
    measure_agreement,
)
from src.evaluation.llm_judge import (
    GeminiJudgeDriver,
    StructuredJudgeDriver,
    build_judge_prompt,
    judge_records,
    load_judge_checkpoint,
    run_live_judge,
)
from src.evaluation.reply_quality import evaluate_reply_quality


def _record(example_id="one", draft="Please contact support."):
    return {
        "example_id": example_id,
        "customer_text": "My order is delayed.",
        "retrieved_examples": [{
            "customer_text": "My order is delayed.",
            "amazonhelp_response": "Please contact support.",
        }],
        "draft_reply": draft,
        "grounding_confidence": 0.7,
        "needs_human_review": False,
    }


def test_grounding_is_deterministic_and_flags_unsupported_claim():
    result = evaluate_grounding(_record(draft="Your order arrives on 2026-09-14 at 10."))
    assert result["specific_claim_count"] == 2
    assert result["unsupported_specific_claims"] == ["2026-09-14", "10"]
    assert result["grounding_score"] < 1


def test_offline_reply_quality_includes_evidence_metrics():
    metrics = evaluate_reply_quality([_record()], {"one": "Please contact support."})
    assert metrics["input_examples"] == 1
    assert metrics["non_empty_reply_rate"] == 1
    assert metrics["reference_replies_available"] == 1
    assert metrics["evidence"]["mean_grounding_score"] == 1


def test_injected_structured_judge_is_used_without_live_call():
    calls = []

    def fake_judge(record):
        calls.append(record["example_id"])
        return {"scores": {dimension: 4 for dimension in (
            "relevance", "helpfulness", "factuality", "grounding", "safety"
        )}, "rationale": "fixed"}

    report = judge_records([_record()], StructuredJudgeDriver(fake_judge))
    assert calls == ["one"]
    assert report["mean_scores"]["overall"] == 4


def test_judge_rejects_missing_or_out_of_range_scores():
    with pytest.raises(ValueError):
        StructuredJudgeDriver(lambda _: {"relevance": 6}).judge(_record())


def test_human_agreement_csv_and_jsonl(tmp_path: Path):
    primary = tmp_path / "primary.csv"
    primary.write_text("example_id,human_intent\n1,a\n2,b\n3,b\n", encoding="utf-8")
    secondary = tmp_path / "secondary.jsonl"
    secondary.write_text(
        '{"example_id":"1","label":"a"}\n'
        '{"example_id":"2","label":"a"}\n'
        '{"example_id":"3","label":"b"}\n',
        encoding="utf-8",
    )
    first = load_annotations(primary)
    second = load_annotations(secondary)
    result = measure_agreement(first, second)
    assert result["matched_examples"] == 3
    assert result["raw_agreement"] == pytest.approx(2 / 3)
    assert result["cohen_kappa"] == pytest.approx(0.4)


def test_cohen_kappa_is_not_reported_for_empty_or_single_class():
    assert cohen_kappa([], []) is None
    assert cohen_kappa(["a"], ["a"]) is None


def test_final_report_writes_consolidated_outputs(tmp_path: Path):
    generations = tmp_path / "generations.jsonl"
    generations.write_text(json.dumps(_record()) + "\n", encoding="utf-8")
    references = tmp_path / "references.csv"
    references.write_text(
        "example_id,amazonhelp_response\none,Please contact support.\n",
        encoding="utf-8",
    )
    report = build_report(generations, references)
    output = tmp_path / "final.json"
    markdown = tmp_path / "final.md"
    write_reports(report, output, markdown)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["report_generation_mode"] == "offline"
    assert "offline_only" not in report
    assert "Final Evaluation Report" in markdown.read_text(encoding="utf-8")


def test_final_report_includes_human_audit_summary(tmp_path: Path):
    generations = tmp_path / "generations.jsonl"
    generations.write_text(json.dumps(_record()) + "\n", encoding="utf-8")
    references = tmp_path / "references.csv"
    references.write_text(
        "example_id,amazonhelp_response\none,Please contact support.\n",
        encoding="utf-8",
    )
    human_audit = tmp_path / "human_audit_8_analysis.md"
    human_audit.write_text(
        "# Human Audit\n\n"
        "| Dimension | 8-human mean top-label agreement | 5-human panel mean top-label agreement |\n"
        "|---|---:|---:|\n"
        "| Reply addresses problem | 64.0% | 78.8% |\n"
        "| Evidence supported | 55.0% | 61.6% |\n"
        "| Unsupported claim | 65.8% | 84.0% |\n"
        "| Human escalation | 61.8% | 67.6% |\n\n"
        "| Dimension | Exact agreement |\n"
        "|---|---:|\n"
        "| Reply addresses problem | 72.0% |\n"
        "| Evidence supported | 52.0% |\n"
        "| Unsupported claim | 94.0% |\n"
        "| Human escalation | 68.0% |\n\n"
        "- **Copilot**: 50/50 comparable cases; exact agreement = 64.0%\n"
        "- **ChatGPT**: 12/50 comparable cases; exact agreement = 75.0%\n"
        "- **Gemini**: 3/50 comparable cases; exact agreement = 66.7%\n",
        encoding="utf-8",
    )
    report = build_report(generations, references, human_audit_path=human_audit)
    assert report["human_audit"]["study_design"]["examples"] == 50
    assert report["human_audit"]["agreement"]["eight_human_mean_top_label_agreement"]["reply_addresses_problem"] == pytest.approx(0.64)
    assert report["human_audit"]["agreement"]["copilot_vs_five_human_panel_exact_agreement"]["unsupported_claim"] == pytest.approx(0.94)
    assert report["human_audit"]["ai_judge_coverage"]["Copilot"]["available_cases"] == 50
    assert "coverage_limitation" in report["human_audit"]["ai_judge_coverage"]
    assert "ChatGPT" not in report["human_audit"]["ai_judge_coverage"]


def test_gemini_judge_uses_prompt_inputs_and_schema(monkeypatch):
    calls = {}
    dimensions = ("relevance", "helpfulness", "factuality", "grounding", "safety")

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.update(kwargs)
            return type("Response", (), {
                "text": json.dumps({
                    "scores": {dimension: 4 for dimension in dimensions},
                    "rationale": "grounded",
                })
            })()

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.models = FakeModels()

    fake_types = type("Types", (), {
        "GenerateContentConfig": staticmethod(lambda **kwargs: kwargs),
        "AutomaticFunctionCallingConfig": staticmethod(lambda **kwargs: kwargs),
        "Type": type("Type", (), {
            "OBJECT": "OBJECT", "INTEGER": "INTEGER", "STRING": "STRING"
        }),
        "Schema": staticmethod(lambda **kwargs: kwargs),
    })
    monkeypatch.setitem(sys.modules, "google", type("Google", (), {
        "genai": type("Genai", (), {"Client": FakeClient})
    }))
    monkeypatch.setitem(sys.modules, "google.genai", type("GenaiModule", (), {
        "types": fake_types
    }))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    result = GeminiJudgeDriver(model="gemini-test").judge(_record())
    assert result["overall"] == 4
    assert "My order is delayed." in calls["contents"]
    assert "Please contact support." in calls["contents"]
    assert calls["config"]["response_mime_type"] == "application/json"
    schema = calls["config"]["response_schema"]
    assert schema["type"] == "OBJECT"
    assert schema["properties"]["scores"]["type"] == "OBJECT"
    assert schema["properties"]["scores"]["properties"]["grounding"]["type"] == "INTEGER"
    assert "additional_properties" not in schema
    assert "additionalProperties" not in schema
    assert calls["config"]["automatic_function_calling"]["disable"] is True


def test_live_judge_preserves_checkpoint_and_retries(tmp_path: Path):
    output = tmp_path / "judge.jsonl"
    dimensions = ("relevance", "helpfulness", "factuality", "grounding", "safety")
    existing = {
        "example_id": "one",
        "scores": {dimension: 4 for dimension in dimensions},
        "rationale": "done",
    }
    output.write_text(json.dumps(existing) + "\n", encoding="utf-8")
    calls = []

    class Driver:
        def judge(self, record):
            calls.append(record["example_id"])
            if len(calls) == 1:
                raise TimeoutError("temporary")
            return {"scores": {dimension: 5 for dimension in dimensions}, "rationale": "done"}

    report = run_live_judge([_record("one"), _record("two")], Driver(), output,
                            sleep_fn=lambda _: None)
    assert calls == ["two", "two"]
    assert set(load_judge_checkpoint(output)) == {"one", "two"}
    assert report["examples_evaluated"] == 2
    assert "Generated reply:" in build_judge_prompt(_record())

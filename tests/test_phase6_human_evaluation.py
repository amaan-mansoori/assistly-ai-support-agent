import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from src.evaluation import evaluate_integrated_agent
from src.evaluation import human_grounded_evaluation
from src.evaluation.human_grounded_evaluation import (
    ADJUDICATION_VERSION,
    ANNOTATION_VERSION,
    AnnotationError,
    DEFAULT_SAMPLE,
    analyze_annotations,
    create_adjudication_record,
    create_exclusion_record,
    create_annotation_template,
    create_sample_manifest,
    evaluate_human_comparison,
    evaluate_human_grounded_run,
    fleiss_kappa,
    load_sample,
    quadratic_weighted_cohen_kappa,
    summarize_annotation_coverage,
    validate_adjudication_records,
    validate_annotation_records,
    validate_exclusion_records,
)
from src.evaluation.regression_gate import compare_reports


def _sample(ids=("example-1", "example-2")):
    return {
        "sample_version": "assistly-human-subset-v1",
        "dataset_version": "assistly-golden-220-v1",
        "dataset_sha256": "a" * 64,
        "dataset_provenance_status": "unresolved_provisional",
        "sample_size": len(ids),
        "example_ids": list(ids),
    }


def _annotation(example_id, annotator_id, **overrides):
    result = {
        "annotation_version": ANNOTATION_VERSION,
        "dataset_version": "assistly-golden-220-v1",
        "dataset_sha256": "a" * 64,
        "example_id": example_id,
        "annotator_id": annotator_id,
        "annotation_status": "annotated",
        "expected_intent": "delivery_status_delay",
        "relevant_evidence_ids": ["evidence-1"],
        "evidence_relevance": [
            {"evidence_id": "evidence-1", "score": 2},
            {"evidence_id": "evidence-2", "score": 0},
        ],
        "evidence_sufficiency": "sufficient",
        "expected_escalation": "auto_handle",
        "acceptable_answer_criteria": ["addresses_primary_issue"],
        "unsupported_claim_allowed": "no",
        "response_assessments": [{
            "run_id": "run-1",
            "quality": "acceptable",
            "groundedness": "supported",
            "unsupported_claim_detected": "no",
        }],
    }
    result.update(overrides)
    return result


def _adjudication(sample, example_id, annotators, **label_overrides):
    labels = {
        "expected_intent": "delivery_status_delay",
        "relevant_evidence_ids": ["evidence-1"],
        "evidence_relevance": [
            {"evidence_id": "evidence-1", "score": 2},
            {"evidence_id": "evidence-2", "score": 0},
        ],
        "evidence_sufficiency": "sufficient",
        "expected_escalation": "auto_handle",
        "acceptable_answer_criteria": ["addresses_primary_issue"],
        "unsupported_claim_allowed": "no",
        "response_assessments": [{
            "run_id": "run-1",
            "quality": "acceptable",
            "groundedness": "supported",
            "unsupported_claim_detected": "no",
        }],
    }
    labels.update(label_overrides)
    return {
        "adjudication_version": ADJUDICATION_VERSION,
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": example_id,
        "adjudicator_id": "review-lead",
        "source_annotator_ids": annotators,
        "adjudication_status": "adjudicated",
        "final_labels": labels,
    }


def test_schema_and_template_are_versioned_and_leave_labels_empty():
    sample = _sample()
    template = create_annotation_template(sample, "reviewer-a")

    assert len(template) == 2
    assert all(row["annotation_status"] == "not_annotated" for row in template)
    assert all(row["expected_intent"] == "not_annotated" for row in template)
    assert all(row["evidence_relevance"] == [] for row in template)
    assert validate_annotation_records(template, sample) == template
    with pytest.raises(AnnotationError, match="pseudonymous ID"):
        create_annotation_template(sample, "reviewer@example.test")


def test_annotation_coverage_distinguishes_workflow_states():
    sample = _sample(("adjudicated", "partial", "pending", "excluded", "empty"))
    annotations = [
        _annotation("adjudicated", "reviewer-a"),
        _annotation("adjudicated", "reviewer-b"),
        _annotation(
            "partial",
            "reviewer-c",
            annotation_status="uncertain",
            expected_intent="uncertain",
        ),
        _annotation("pending", "reviewer-d"),
    ]
    adjudications = [
        _adjudication(sample, "adjudicated", ["reviewer-a", "reviewer-b"])
    ]
    exclusions = [{
        "exclusion_version": "assistly-human-exclusion-v1",
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": "excluded",
        "excluded_by": "review-lead",
        "reason": "source_unreadable",
        "status": "excluded",
    }]

    coverage = summarize_annotation_coverage(
        sample, annotations, adjudications, exclusions
    )

    assert coverage["status_counts"] == {
        "adjudicated": 1,
        "partially_annotated": 1,
        "annotated_pending_adjudication": 1,
        "excluded": 1,
        "unannotated": 1,
    }
    assert coverage["human_ground_truth_count"] == 1
    assert "customer_text" not in json.dumps(coverage)
    assert validate_exclusion_records(exclusions, sample) == exclusions


def test_annotated_status_rejects_incomplete_or_inconsistent_labels():
    sample = _sample()
    incomplete = _annotation(
        "example-1",
        "reviewer-a",
        acceptable_answer_criteria=[],
    )
    with pytest.raises(AnnotationError, match="annotated records require"):
        validate_annotation_records([incomplete], sample)

    inconsistent_template = create_annotation_template(sample, "reviewer-a")[0]
    inconsistent_template["expected_intent"] = "delivery_status_delay"
    with pytest.raises(AnnotationError, match="must not contain labels"):
        validate_annotation_records([inconsistent_template], sample)


def test_exclusions_reject_invalid_ids_duplicates_and_dataset_mismatch():
    sample = _sample()
    exclusion = {
        "exclusion_version": "assistly-human-exclusion-v1",
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": "example-1",
        "excluded_by": "review-lead",
        "reason": "privacy_review",
        "status": "excluded",
    }
    with pytest.raises(AnnotationError, match="duplicate exclusion"):
        validate_exclusion_records([exclusion, exclusion], sample)
    with pytest.raises(AnnotationError, match="dataset identity mismatch"):
        validate_exclusion_records(
            [{**exclusion, "dataset_sha256": "b" * 64}], sample
        )
    with pytest.raises(AnnotationError, match="invalid reason"):
        validate_exclusion_records([{**exclusion, "reason": "private explanation"}], sample)
    with pytest.raises(AnnotationError, match="pseudonymous excluded_by"):
        create_exclusion_record(sample, "example-1", "person@example.test", "other")


def test_annotation_cli_merges_separate_exports_and_tracks_exclusions(
    monkeypatch, tmp_path, capsys
):
    sample = load_sample(DEFAULT_SAMPLE)
    export_paths = []
    for annotator_id in ("reviewer-a", "reviewer-b"):
        export = tmp_path / f"{annotator_id}.jsonl"
        export.write_text(
            "".join(
                json.dumps(row) + "\n"
                for row in create_annotation_template(sample, annotator_id)
            ),
            encoding="utf-8",
        )
        export_paths.append(export)
    combined = tmp_path / "combined.jsonl"
    monkeypatch.setattr(sys, "argv", [
        "human_grounded_evaluation",
        "merge",
        "--annotations",
        *(str(path) for path in export_paths),
        "--output",
        str(combined),
    ])

    assert human_grounded_evaluation.main() == 0
    assert len(combined.read_text(encoding="utf-8").splitlines()) == 100
    assert json.loads(capsys.readouterr().out)["human_metrics"] == (
        "not computed by merge"
    )
    merged_content = combined.read_text(encoding="utf-8")
    with pytest.raises(AnnotationError, match="refusing to overwrite"):
        human_grounded_evaluation.main()
    assert combined.read_text(encoding="utf-8") == merged_content

    exclusions = tmp_path / "exclusions.jsonl"
    for example_id in sample["example_ids"][:2]:
        monkeypatch.setattr(sys, "argv", [
            "human_grounded_evaluation",
            "exclude",
            "--sample",
            str(DEFAULT_SAMPLE),
            "--example-id",
            example_id,
            "--excluded-by",
            "review-lead",
            "--reason",
            "source_unavailable",
            "--output",
            str(exclusions),
        ])
        assert human_grounded_evaluation.main() == 0
    assert len(exclusions.read_text(encoding="utf-8").splitlines()) == 2

    coverage_path = tmp_path / "coverage.json"
    monkeypatch.setattr(sys, "argv", [
        "human_grounded_evaluation",
        "coverage",
        "--sample",
        str(DEFAULT_SAMPLE),
        "--annotations",
        str(combined),
        "--exclusions",
        str(exclusions),
        "--output",
        str(coverage_path),
    ])
    assert human_grounded_evaluation.main() == 0
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    assert coverage["status_counts"] == {"excluded": 2, "unannotated": 48}


def test_checked_in_sample_is_exactly_the_frozen_label_independent_sample():
    sample = load_sample(DEFAULT_SAMPLE)
    regenerated = create_sample_manifest(
        Path("data/golden/golden_set.csv"), sample_size=50
    )

    assert sample == regenerated
    assert sample["sample_size"] == 50
    assert "customer_text" not in json.dumps(sample)


def test_annotation_validation_checks_scale_fingerprint_and_duplicate_annotators():
    sample = _sample()
    first = _annotation("example-1", "reviewer-a")
    second_annotator = _annotation("example-1", "reviewer-b")
    assert len(validate_annotation_records([first, second_annotator], sample)) == 2

    with pytest.raises(AnnotationError, match="duplicate annotation"):
        validate_annotation_records([first, first], sample)

    invalid_score = _annotation(
        "example-1",
        "reviewer-c",
        evidence_relevance=[{"evidence_id": "evidence-1", "score": 3}],
    )
    with pytest.raises(AnnotationError, match="invalid/duplicate relevance"):
        validate_annotation_records([invalid_score], sample)

    wrong_fingerprint = _annotation(
        "example-1", "reviewer-c", dataset_sha256="b" * 64
    )
    with pytest.raises(AnnotationError, match="identity mismatch"):
        validate_annotation_records([wrong_fingerprint], sample)

    extra_field = _annotation("example-1", "reviewer-c", private_note="text")
    with pytest.raises(AnnotationError, match="fields do not match"):
        validate_annotation_records([extra_field], sample)

    multi_run = _annotation(
        "example-1",
        "reviewer-c",
        response_assessments=[
            {
                "run_id": "run-1",
                "quality": "acceptable",
                "groundedness": "supported",
                "unsupported_claim_detected": "no",
            },
            {
                "run_id": "run-2",
                "quality": "partially_acceptable",
                "groundedness": "partially_supported",
                "unsupported_claim_detected": "no",
            },
        ],
    )
    assert len(validate_annotation_records([multi_run], sample)) == 1
    duplicate_run_assessment = _annotation(
        "example-1",
        "reviewer-d",
        response_assessments=[
            multi_run["response_assessments"][0],
            multi_run["response_assessments"][0],
        ],
    )
    with pytest.raises(AnnotationError, match="run IDs must be unique"):
        validate_annotation_records([duplicate_run_assessment], sample)


def test_disagreement_detection_and_agreement_metrics_are_computed_not_fabricated():
    sample = _sample()
    annotations = [
        _annotation("example-1", "reviewer-a"),
        _annotation(
            "example-1",
            "reviewer-b",
            expected_intent="return_refund",
            evidence_relevance=[
                {"evidence_id": "evidence-1", "score": 1},
                {"evidence_id": "evidence-2", "score": 0},
            ],
            relevant_evidence_ids=["evidence-1"],
            acceptable_answer_criteria=["actionable_next_step"],
            response_assessments=[{
                "run_id": "run-1",
                "quality": "unacceptable",
                "groundedness": "unsupported",
                "unsupported_claim_detected": "yes",
            }],
        ),
    ]
    report = analyze_annotations(annotations, sample)

    assert report["disagreement_count"] == 1
    assert "expected_intent" in report["disagreements"][0]["fields"]
    assert "acceptable_answer_criteria" in report["disagreements"][0]["fields"]
    assert "run-1" in report["disagreements"][0]["response_assessment"]
    assert report["categorical_agreement"]["expected_intent"]["metric"] == "cohen_kappa"
    assert report["ordinal_evidence_relevance_agreement"]["metric"] == (
        "quadratic_weighted_cohen_kappa"
    )
    assert fleiss_kappa([["a", "a", "b"], ["a", "b", "b"]]) == pytest.approx(-1 / 3)
    assert quadratic_weighted_cohen_kappa([0, 1, 2], [0, 1, 2]) == pytest.approx(1.0)


def test_fleiss_agreement_requires_balanced_nondegenerate_ratings():
    assert fleiss_kappa([]) is None
    assert fleiss_kappa([["a", "a"], ["a", "b", "b"]]) is None
    assert fleiss_kappa([["a", "a"], ["a", "a"]]) is None


def test_template_only_submissions_do_not_create_ground_truth_or_agreement():
    sample = _sample()
    template = create_annotation_template(sample, "reviewer-a")

    report = analyze_annotations(template, sample)

    assert report["annotated_records"] == 0
    assert report["not_annotated_records"] == 2
    assert report["uncertain_records"] == 0
    assert report["categorical_agreement"]["expected_intent"]["value"] is None
    assert report["ordinal_evidence_relevance_agreement"]["value"] is None


def test_adjudication_requires_distinct_submitted_annotators_and_is_separate():
    sample = _sample()
    annotations = [
        _annotation("example-1", "reviewer-a"),
        _annotation("example-1", "reviewer-b"),
    ]
    record = create_adjudication_record(
        sample,
        "example-1",
        "review-lead",
        ["reviewer-a", "reviewer-b"],
        _adjudication(sample, "example-1", ["reviewer-a", "reviewer-b"])[
            "final_labels"
        ],
        annotations,
    )
    assert record["adjudication_status"] == "adjudicated"
    assert validate_adjudication_records([record], sample, annotations) == [record]

    with pytest.raises(AnnotationError, match="invalid source annotators"):
        validate_adjudication_records(
            [
                _adjudication(
                    sample,
                    "example-1",
                    ["reviewer-a", "reviewer-a"],
                )
            ],
            sample,
        )
    with pytest.raises(AnnotationError, match="missing or incomplete"):
        validate_adjudication_records([record], sample, annotations[:1])
    with pytest.raises(AnnotationError, match="duplicate adjudication"):
        validate_adjudication_records([record, record], sample, annotations)


def test_human_metrics_use_only_adjudicated_labels_and_human_evidence_ids():
    sample = _sample()
    annotations = [
        _annotation("example-1", "reviewer-a"),
        _annotation("example-1", "reviewer-b"),
        _annotation(
            "example-2",
            "reviewer-a",
            expected_intent="return_refund",
            relevant_evidence_ids=["evidence-3"],
            evidence_relevance=[{"evidence_id": "evidence-3", "score": 2}],
            evidence_sufficiency="insufficient",
            expected_escalation="escalate",
            response_assessments=[{
                "run_id": "run-1",
                "quality": "partially_acceptable",
                "groundedness": "partially_supported",
                "unsupported_claim_detected": "yes",
            }],
        ),
        _annotation(
            "example-2",
            "reviewer-b",
            expected_intent="return_refund",
            relevant_evidence_ids=["evidence-3"],
            evidence_relevance=[{"evidence_id": "evidence-3", "score": 2}],
            evidence_sufficiency="insufficient",
            expected_escalation="escalate",
            response_assessments=[{
                "run_id": "run-1",
                "quality": "partially_acceptable",
                "groundedness": "partially_supported",
                "unsupported_claim_detected": "yes",
            }],
        ),
    ]
    adjudications = [
        _adjudication(sample, "example-1", ["reviewer-a", "reviewer-b"]),
        _adjudication(
            sample,
            "example-2",
            ["reviewer-a", "reviewer-b"],
            expected_intent="return_refund",
            relevant_evidence_ids=["evidence-3"],
            evidence_relevance=[{"evidence_id": "evidence-3", "score": 2}],
            evidence_sufficiency="insufficient",
            expected_escalation="escalate",
            response_assessments=[{
                "run_id": "run-1",
                "quality": "partially_acceptable",
                "groundedness": "partially_supported",
                "unsupported_claim_detected": "yes",
            }],
        ),
    ]
    run_rows = [
        {
            "example_id": "example-1",
            "predicted_intent": "delivery_status_delay",
            "evidence_source_ids": ["evidence-1", "other"],
            "evidence_status": "sufficient",
            "decision": "auto_handle",
            "latency_ms": 10.0,
        },
        {
            "example_id": "example-2",
            "predicted_intent": "return_refund",
            "evidence_source_ids": ["wrong", "evidence-3"],
            "evidence_status": "weak",
            "decision": "auto_handle",
            "latency_ms": 20.0,
        },
    ]
    report, failures = evaluate_human_grounded_run(
        {
            "run_id": "run-1",
            "run_mode": "live_provider",
            "provider": "gemini",
            "model": "test-model",
            "retrieval_backend": "tfidf",
        },
        run_rows,
        adjudications,
        sample,
        annotations,
    )

    metrics = report["metrics"]
    assert metrics["intent_accuracy"]["value"] == 1
    assert metrics["retrieval_recall_at_k"]["1"]["value"] == 0.5
    assert metrics["retrieval_recall_at_k"]["3"]["value"] == 1
    assert metrics["retrieval_mrr"]["value"] == pytest.approx(0.75)
    assert metrics["evidence_sufficiency_accuracy"]["value"] == 1
    assert metrics["escalation_precision"]["value"] is None
    assert metrics["escalation_recall"]["value"] == 0
    assert metrics["groundedness_rate"]["value"] == 0.5
    assert metrics["unsupported_claim_rate"]["value"] == 0.5
    assert metrics["response_quality_mean"]["value"] == 0.75
    assert metrics["latency_ms"]["value"] == 15
    assert metrics["token_usage"] is None
    assert metrics["estimated_cost"] is None
    forbidden = {"customer_text", "generated_reply", "prompt", "chain_of_thought"}
    assert all(not forbidden.intersection(row) for row in failures)
    assert {row["failure_category"] for row in failures} == {"missing_escalation"}


def test_missing_human_labels_and_run_mismatches_stay_unavailable():
    sample = _sample()
    template = create_annotation_template(sample, "reviewer-a")
    report, failures = evaluate_human_grounded_run(
        {"run_id": "different-run"},
        [{"example_id": "example-1", "predicted_intent": "delivery_status_delay"}],
        [],
        sample,
        template,
    )

    assert report["metrics"]["intent_accuracy"]["value"] is None
    assert report["metrics"]["escalation_recall"]["value"] is None
    assert report["metrics"]["response_quality_mean"]["value"] is None
    assert report["metrics"]["latency_ms"] is None
    assert report["metrics"]["token_usage"] is None
    assert report["metrics"]["estimated_cost"] is None
    assert failures == []


def test_missing_prediction_counts_as_incorrect_instead_of_leaving_denominator():
    sample = _sample(("example-1",))
    annotations = [
        _annotation("example-1", "reviewer-a"),
        _annotation("example-1", "reviewer-b"),
    ]
    adjudications = [
        _adjudication(sample, "example-1", ["reviewer-a", "reviewer-b"])
    ]
    report, failures = evaluate_human_grounded_run(
        {"run_id": "run-1"},
        [{"example_id": "example-1"}],
        adjudications,
        sample,
        annotations,
    )

    assert report["metrics"]["intent_accuracy"] == {
        "value": 0,
        "numerator": 0,
        "denominator": 1,
        "status": "measured",
    }
    assert failures[0]["failure_category"] == "ambiguous_intent"


def test_integrated_evaluation_uses_deterministic_mock_by_default(
    monkeypatch, tmp_path
):
    observed = {}

    class FakeEngine:
        def dispose(self):
            observed["disposed"] = True

    monkeypatch.setattr(sys, "argv", [
        "evaluate_integrated_agent",
        "--output", str(tmp_path / "per-example.jsonl"),
        "--summary", str(tmp_path / "summary.json"),
        "--failures", str(tmp_path / "failures.json"),
    ])
    monkeypatch.setattr(
        evaluate_integrated_agent,
        "verify_dataset",
        lambda *_: (
            {
                "dataset_version": "golden-v1",
                "sha256": "dataset-hash",
                "provenance_status": "unresolved_provisional",
            },
            [{"example_id": "example-1", "human_intent": "delivery_status_delay"}],
        ),
    )
    monkeypatch.setattr(
        evaluate_integrated_agent.PlatformSettings,
        "from_env",
        lambda: SimpleNamespace(
            database_url="sqlite://",
            retriever_backend="tfidf",
            embedding_model="test-embedding",
            hybrid_lexical_weight=0.5,
            hybrid_semantic_weight=0.5,
        ),
    )
    monkeypatch.setattr(
        evaluate_integrated_agent.AgentConfig,
        "load",
        lambda: evaluate_integrated_agent.AgentConfig(),
    )
    monkeypatch.setattr(
        evaluate_integrated_agent,
        "DeterministicMockProvider",
        lambda *_args, **_kwargs: "mock-provider",
    )
    monkeypatch.setattr(
        evaluate_integrated_agent,
        "configured_llm_call",
        lambda *_args, **_kwargs: pytest.fail("default mode attempted a live provider call"),
    )
    monkeypatch.setattr(
        evaluate_integrated_agent,
        "make_engine",
        lambda *_: FakeEngine(),
    )
    monkeypatch.setattr(
        evaluate_integrated_agent,
        "make_session_factory",
        lambda _engine: "session-factory",
    )
    monkeypatch.setattr(
        evaluate_integrated_agent,
        "build_retriever",
        lambda *_args: "retriever",
    )
    monkeypatch.setattr(
        evaluate_integrated_agent,
        "SupportAgent",
        lambda _retriever, provider, _config: SimpleNamespace(provider=provider),
    )

    def fake_evaluate_examples(agent, examples):
        observed["provider"] = agent.provider
        observed["example_count"] = len(examples)
        return {"metrics": {}}, [{"example_id": "example-1", "latency_ms": 12}]

    monkeypatch.setattr(
        evaluate_integrated_agent, "evaluate_examples", fake_evaluate_examples
    )
    monkeypatch.setattr(evaluate_integrated_agent, "_git_revision", lambda: "revision")
    monkeypatch.setattr(
        evaluate_integrated_agent, "_working_tree_dirty", lambda: False
    )

    assert evaluate_integrated_agent.main() == 0

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["run_mode"] == "deterministic_mock"
    assert summary["run_metadata"]["run_mode"] == "deterministic_mock"
    assert observed == {
        "provider": "mock-provider",
        "example_count": 1,
        "disposed": True,
    }


def test_live_evaluation_cap_rejects_more_than_twenty_without_provider_call(
    monkeypatch,
):
    monkeypatch.setattr(
        sys, "argv", ["evaluate_integrated_agent", "--live", "--limit", "21"]
    )

    with pytest.raises(SystemExit) as error:
        evaluate_integrated_agent.main()

    assert error.value.code == 2


def test_human_comparison_keeps_all_three_systems_separate():
    sample = _sample(("example-1",))
    response_assessments = [
        {
            "run_id": "comparison-1:majority",
            "quality": "unacceptable",
            "groundedness": "unsupported",
            "unsupported_claim_detected": "yes",
        },
        {
            "run_id": "comparison-1:tfidf_logistic_regression",
            "quality": "acceptable",
            "groundedness": "supported",
            "unsupported_claim_detected": "no",
        },
        {
            "run_id": "comparison-1",
            "quality": "partially_acceptable",
            "groundedness": "partially_supported",
            "unsupported_claim_detected": "no",
        },
    ]
    annotations = [
        _annotation(
            "example-1", "reviewer-a", response_assessments=response_assessments
        ),
        _annotation(
            "example-1", "reviewer-b", response_assessments=response_assessments
        ),
    ]
    adjudications = [
        _adjudication(
            sample,
            "example-1",
            ["reviewer-a", "reviewer-b"],
            response_assessments=response_assessments,
        )
    ]
    comparison_metadata = {
        "run_id": "comparison-1",
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "prompt_version": "assistly-support-prompt-v3",
        "retrieval_version": "assistly-retrieval-v2",
        "retrieval_backend": "tfidf",
        "run_mode": "deterministic_mock",
        "provider": "deterministic_mock",
        "model": None,
        "configuration": {},
    }
    comparison = {
        "run_metadata": comparison_metadata,
        "results": {
            "majority": {
                "run_class": "deterministic_baseline",
                "per_example": [{
                    "example_id": "example-1",
                    "predicted_intent": "return_refund",
                }],
            },
            "tfidf_logistic_regression": {
                "run_class": "deterministic_baseline",
                "per_example": [{
                    "example_id": "example-1",
                    "predicted_intent": "delivery_status_delay",
                }],
            },
            "assistly_runtime": {
                "run_class": "deterministic_mock",
                "run_metadata": {
                    **comparison_metadata,
                    "run_id": "comparison-1",
                },
                "per_example": [{
                    "example_id": "example-1",
                    "predicted_intent": "delivery_status_delay",
                    "evidence_source_ids": ["evidence-1"],
                    "evidence_status": "sufficient",
                    "decision": "auto_handle",
                }],
            },
        },
    }

    result = evaluate_human_comparison(
        comparison, annotations, adjudications, sample
    )

    assert set(result["results"]) == {
        "majority",
        "tfidf_logistic_regression",
        "assistly_runtime",
    }
    assert result["results"]["majority"]["metrics"]["intent_accuracy"]["value"] == 0
    assert result["results"]["majority"]["metrics"][
        "response_quality_mean"
    ]["value"] == 0
    assert result["results"]["tfidf_logistic_regression"]["metrics"][
        "groundedness_rate"
    ]["value"] == 1
    assert result["results"]["assistly_runtime"]["metrics"][
        "response_quality_mean"
    ]["value"] == 0.5
    assert result["results"]["majority"]["metrics"][
        "retrieval_recall_at_k"
    ]["1"]["value"] == 0
    assert result["results"]["majority"]["metrics"][
        "evidence_sufficiency_accuracy"
    ]["value"] is None
    assert result["results"]["majority"]["metrics"]["escalation_recall"][
        "value"
    ] is None
    assert result["results"]["assistly_runtime"]["metrics"][
        "retrieval_recall_at_k"
    ]["1"]["value"] == 1


def test_human_regression_identity_and_optional_sample_threshold():
    base = {
        "run_metadata": {
            "dataset_sha256": "frozen",
            "dataset_manifest_sha256": "manifest",
            "dataset_version": "golden-v1",
            "evaluation_schema_version": "human-eval-v1",
            "evaluator_version": "human-evaluator-v1",
            "prompt_version": "prompt-v1",
            "retrieval_version": "retrieval-v1",
            "evidence_policy_version": "assistly-evidence-policy-v2",
            "retrieval_backend": "tfidf",
            "run_mode": "live_provider",
            "provider": "gemini",
            "model": "model-v1",
            "examples_evaluated": 5,
            "annotation_dataset_version": "human-subset-v1",
            "annotation_sample_sha256": "sample-hash",
            "annotation_records_sha256": "annotations-hash",
            "adjudication_records_sha256": "adjudications-hash",
            "ground_truth_source": "human_adjudication",
            "configuration": {},
        },
        "metrics": {
            "escalation_recall": {"value": 0.8, "denominator": 5}
        },
    }
    candidate = json.loads(json.dumps(base))
    thresholds = {
        "metrics": {
            "human_escalation_recall": {
                "path": "metrics.escalation_recall",
                "direction": "higher_is_better",
                "max_degradation": 0.1,
                "minimum_denominator": 5,
            }
        }
    }

    assert compare_reports(base, candidate, thresholds)["passed"] is True
    candidate["metrics"]["escalation_recall"]["denominator"] = 4
    denominator_mismatch = compare_reports(base, candidate, thresholds)
    assert denominator_mismatch["compatible"] is False
    assert "metric_denominator.human_escalation_recall" in (
        denominator_mismatch["identity_mismatches"]
    )
    candidate["run_metadata"]["annotation_records_sha256"] = "another-annotation-set"
    result = compare_reports(base, candidate, thresholds)
    assert result["compatible"] is False
    assert "annotation_records_sha256" in result["identity_mismatches"]

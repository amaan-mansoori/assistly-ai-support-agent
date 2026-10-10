import json

import pytest

from src.evaluation.human_grounded_evaluation import (
    ADJUDICATION_VERSION,
    ANNOTATION_VERSION,
    DEFAULT_SAMPLE,
    AnnotationError,
    create_annotation_template,
    create_exclusion_record,
    load_sample,
    validate_annotation_records,
    validate_exclusion_records,
)
from src.evaluation.independent_retrieval_evaluation import (
    evaluate_independent_retrieval,
)


def _sample(ids=("example-1", "example-2")):
    return {
        "sample_version": "assistly-human-subset-v1",
        "dataset_version": "assistly-golden-220-v1",
        "dataset_sha256": "a" * 64,
        "dataset_provenance_status": "unresolved_provisional",
        "sample_size": len(ids),
        "example_ids": list(ids),
    }


def _annotation(example_id, annotator_id, *, relevance=None):
    relevance = relevance or [
        {"evidence_id": "evidence-1", "score": 2},
        {"evidence_id": "evidence-2", "score": 0},
    ]
    record = {
        "annotation_version": ANNOTATION_VERSION,
        "dataset_version": "assistly-golden-220-v1",
        "dataset_sha256": "a" * 64,
        "example_id": example_id,
        "annotator_id": annotator_id,
        "annotation_status": "annotated",
        "expected_intent": "delivery_status_delay",
        "relevant_evidence_ids": ["evidence-1"],
        "evidence_relevance": relevance,
        "evidence_sufficiency": "sufficient",
        "expected_escalation": "auto_handle",
        "acceptable_answer_criteria": ["uses_relevant_evidence"],
        "unsupported_claim_allowed": "no",
        "response_assessments": [],
    }
    return record


def _adjudication(sample, example_id, annotators):
    return {
        "adjudication_version": ADJUDICATION_VERSION,
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": example_id,
        "adjudicator_id": "review-lead",
        "source_annotator_ids": annotators,
        "adjudication_status": "adjudicated",
        "final_labels": {
            "expected_intent": "delivery_status_delay",
            "relevant_evidence_ids": ["evidence-1"],
            "evidence_relevance": [
                {"evidence_id": "evidence-1", "score": 2},
                {"evidence_id": "evidence-2", "score": 0},
            ],
            "evidence_sufficiency": "sufficient",
            "expected_escalation": "auto_handle",
            "acceptable_answer_criteria": ["uses_relevant_evidence"],
            "unsupported_claim_allowed": "no",
            "response_assessments": [],
        },
    }


def test_retrieval_annotation_template_is_valid_and_empty_for_a_fifty_example_sample():
    sample = load_sample(DEFAULT_SAMPLE)
    template = create_annotation_template(sample, "reviewer-01")

    assert len(template) == 50
    assert all(row["annotation_status"] == "not_annotated" for row in template)
    assert all(row["relevant_evidence_ids"] == [] for row in template)
    assert all(row["evidence_relevance"] == [] for row in template)
    assert validate_annotation_records(template, sample) == template


def test_retrieval_validation_rejects_duplicates_missing_ids_and_incomplete_annotations():
    sample = _sample()
    valid = _annotation("example-1", "reviewer-a")
    duplicate = _annotation("example-1", "reviewer-a")
    with pytest.raises(AnnotationError, match="duplicate annotation"):
        validate_annotation_records([valid, duplicate], sample)

    malformed = {**valid, "evidence_relevance": [{"evidence_id": "evidence-1", "score": 3}]}
    with pytest.raises(AnnotationError, match="invalid/duplicate relevance entry"):
        validate_annotation_records([malformed], sample)

    missing_candidate = {**valid, "relevant_evidence_ids": ["missing-id"]}
    with pytest.raises(AnnotationError, match="relevant_evidence_ids must match"):
        validate_annotation_records([missing_candidate], sample)

    incomplete = {**valid, "annotation_status": "annotated", "acceptable_answer_criteria": []}
    with pytest.raises(AnnotationError, match="annotated records require"):
        validate_annotation_records([incomplete], sample)

    exclusion = create_exclusion_record(sample, "example-1", "review-lead", "privacy_review")
    with pytest.raises(AnnotationError, match="duplicate exclusion"):
        validate_exclusion_records([exclusion, exclusion], sample)


def test_retrieval_evaluation_uses_adjudicated_relevance_and_exclusions_only():
    sample = _sample(("example-1", "example-2"))
    annotations = [
        _annotation("example-1", "reviewer-a"),
        _annotation("example-1", "reviewer-b"),
        _annotation("example-2", "reviewer-c"),
    ]
    adjudications = [_adjudication(sample, "example-1", ["reviewer-a", "reviewer-b"]) ]
    exclusions = [
        {
            "exclusion_version": "assistly-human-exclusion-v1",
            "dataset_version": sample["dataset_version"],
            "dataset_sha256": sample["dataset_sha256"],
            "example_id": "example-2",
            "excluded_by": "review-lead",
            "reason": "source_unavailable",
            "status": "excluded",
        }
    ]
    report, failures = evaluate_independent_retrieval(
        sample,
        annotations,
        adjudications,
        {
            "system_a": [{"example_id": "example-1", "evidence_source_ids": ["evidence-2", "evidence-1"]}],
            "system_b": [{"example_id": "example-1", "evidence_source_ids": ["evidence-1", "evidence-2"]}],
        },
        exclusions,
    )

    assert report["eligible_examples"] == 1
    assert report["excluded_examples"] == 1
    assert report["systems"]["system_a"]["metrics"]["recall_at_k"]["1"]["value"] == 0.0
    assert report["systems"]["system_a"]["metrics"]["mrr"]["value"] == pytest.approx(0.5)
    assert report["systems"]["system_b"]["metrics"]["mrr"]["value"] == 1
    assert report["systems"]["system_b"]["metrics"]["ndcg_at_k"]["1"]["value"] == pytest.approx(1.0)
    assert not failures
    assert "customer_text" not in json.dumps(report)

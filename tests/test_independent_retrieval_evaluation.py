import argparse
import json

import pytest

from src.evaluation.human_grounded_evaluation import (
    ADJUDICATION_VERSION,
    ANNOTATION_VERSION,
)
from src.evaluation.independent_retrieval_evaluation import (
    _named_run,
    evaluate_independent_retrieval,
)
from src.evaluation.human_grounded_evaluation import AnnotationError


def _sample(ids=("example-1", "example-2")):
    return {
        "sample_version": "assistly-human-subset-v1",
        "dataset_version": "assistly-golden-220-v1",
        "dataset_sha256": "a" * 64,
        "dataset_provenance_status": "unresolved_provisional",
        "sample_size": len(ids),
        "example_ids": list(ids),
    }


def _records(sample):
    first_annotation = {
        "annotation_version": ANNOTATION_VERSION,
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": "example-1",
        "annotator_id": "reviewer-a",
        "annotation_status": "annotated",
        "expected_intent": "delivery_status_delay",
        "relevant_evidence_ids": ["evidence-1", "evidence-2"],
        "evidence_relevance": [
            {"evidence_id": "evidence-1", "score": 2},
            {"evidence_id": "evidence-2", "score": 1},
        ],
        "evidence_sufficiency": "sufficient",
        "expected_escalation": "auto_handle",
        "acceptable_answer_criteria": ["uses_relevant_evidence"],
        "unsupported_claim_allowed": "no",
        "response_assessments": [],
    }
    second_annotation = {**first_annotation, "annotator_id": "reviewer-b"}
    final_labels = {
        key: value
        for key, value in first_annotation.items()
        if key not in {
            "annotation_version",
            "dataset_version",
            "dataset_sha256",
            "example_id",
            "annotator_id",
            "annotation_status",
        }
    }
    adjudication = {
        "adjudication_version": ADJUDICATION_VERSION,
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": "example-1",
        "adjudicator_id": "review-lead",
        "source_annotator_ids": ["reviewer-a", "reviewer-b"],
        "adjudication_status": "adjudicated",
        "final_labels": final_labels,
    }
    return [first_annotation, second_annotation], [adjudication]


def test_independent_retrieval_metrics_use_graded_judgments_and_shared_denominator():
    sample = _sample()
    annotations, adjudications = _records(sample)
    report, failures = evaluate_independent_retrieval(
        sample,
        annotations,
        adjudications,
        {
            "tfidf": [{
                "example_id": "example-1",
                "evidence_source_ids": ["evidence-2", "evidence-1"],
            }],
            "hybrid": [{
                "example_id": "example-1",
                "evidence_source_ids": ["evidence-1", "evidence-2"],
            }],
        },
    )

    assert report["eligible_examples"] == 1
    assert report["unadjudicated_not_excluded_examples"] == 1
    assert report["systems"]["tfidf"]["metrics"]["recall_at_k"]["1"]["value"] == 0.5
    assert report["systems"]["tfidf"]["metrics"]["recall_at_k"]["3"]["value"] == 1
    assert report["systems"]["tfidf"]["metrics"]["mrr"]["value"] == 1
    assert report["systems"]["tfidf"]["metrics"]["ndcg_at_k"]["1"]["value"] == pytest.approx(1 / 3)
    assert report["systems"]["hybrid"]["metrics"]["ndcg_at_k"]["1"]["value"] == 1
    assert not failures
    assert "customer_text" not in json.dumps(report)


def test_missing_run_output_fails_closed_and_counts_zero_in_shared_denominator():
    sample = _sample(("example-1",))
    annotations, adjudications = _records(sample)
    report, failures = evaluate_independent_retrieval(
        sample, annotations, adjudications, {"offline": []}
    )

    system = report["systems"]["offline"]
    assert system["eligible_examples"] == 1
    assert system["evaluated_examples"] == 0
    assert system["failed_examples"] == 1
    assert system["metrics"]["recall_at_k"]["5"]["value"] == 0
    assert failures == [{
        "example_id": "example-1",
        "system": "offline",
        "failure_category": "missing_retrieval_output",
        "first_relevant_rank": None,
        "retrieved_evidence_ids_at_5": [],
    }]
    assert "customer_text" not in json.dumps(failures)


def test_explicitly_excluded_or_unjudged_examples_do_not_enter_metric_denominator():
    sample = _sample(("example-1", "example-2"))
    annotations, adjudications = _records(sample)
    exclusion = {
        "exclusion_version": "assistly-human-exclusion-v1",
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": "example-2",
        "excluded_by": "review-lead",
        "reason": "source_unavailable",
        "status": "excluded",
    }
    report, _ = evaluate_independent_retrieval(
        sample,
        annotations,
        adjudications,
        {"system": []},
        [exclusion],
    )

    assert report["excluded_examples"] == 1
    assert report["eligible_examples"] == 1
    assert report["unadjudicated_not_excluded_examples"] == 0
    assert report["systems"]["system"]["failed_examples"] == 1


def test_duplicate_system_results_and_invalid_run_argument_are_rejected():
    sample = _sample(("example-1",))
    annotations, adjudications = _records(sample)
    duplicate = [
        {"example_id": "example-1", "evidence_source_ids": []},
        {"example_id": "example-1", "evidence_source_ids": []},
    ]
    with pytest.raises(AnnotationError, match="duplicate result"):
        evaluate_independent_retrieval(
            sample, annotations, adjudications, {"system": duplicate}
        )
    with pytest.raises(argparse.ArgumentTypeError, match="SYSTEM=PATH"):
        _named_run("malformed")

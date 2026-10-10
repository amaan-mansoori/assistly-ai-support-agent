import json

import pytest

from src.evaluation.human_grounded_evaluation import AnnotationError
from src.evaluation.retrieval_relevance_workflow import (
    evaluate,
    export_templates,
    validate_adjudications,
    validate_exclusions,
    validate_submission,
)


def _fixtures():
    sample = {
        "example_ids": ["q-1", "q-2"],
        "dataset_version": "assistly-golden-220-v1",
        "dataset_sha256": "a" * 64,
    }
    pairs = [
        {
            "query_id": query_id,
            "candidate_id": candidate_id,
            "rank": rank,
            "query_text": f"query text {query_id}",
            "candidate_text": f"candidate text {candidate_id}",
        }
        for query_id in sample["example_ids"]
        for rank, candidate_id in enumerate(("c-1", "c-2", "c-3"), 1)
    ]
    identity = {
        "schema_version": "assistly-retrieval-relevance-v1",
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": "a" * 64,
        "sample_sha256": "b" * 64,
        "retrieval_artifact_sha256": "c" * 64,
    }
    reviewers = []
    for reviewer_id, grades in (
        ("reviewer-a", [2, 0, 0, 0, 0, 1]),
        ("reviewer-b", [2, 1, 0, 0, 0, 1]),
    ):
        reviewers.append([
            {
                **identity,
                **pair,
                "reviewer_id": reviewer_id,
                "relevance_grade": grade,
                "rationale": "",
            }
            for pair, grade in zip(pairs, grades, strict=True)
        ])
    return sample, pairs, identity, reviewers


def test_review_submissions_validate_complete_zero_and_positive_grades():
    sample, pairs, identity, reviewers = _fixtures()
    checked = validate_submission(reviewers[0], sample, pairs, identity)
    assert len(checked) == 6
    assert checked[1]["relevance_grade"] == 0
    assert checked[0]["relevance_grade"] == 2


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("duplicate", "duplicate judgment"),
        ("unknown", "unknown query"),
        ("unknown_candidate", "unknown query/candidate pair"),
        ("invalid_grade", "must be blank, 0, 1, or 2"),
        ("missing", "candidate judgments missing"),
        ("blank", "blank relevance judgments"),
        ("provenance", "mismatched provenance"),
    ],
)
def test_submission_rejects_invalid_or_incomplete_records(mutation, message):
    sample, pairs, identity, reviewers = _fixtures()
    records = [dict(row) for row in reviewers[0]]
    if mutation == "duplicate":
        records.append(dict(records[0]))
    elif mutation == "unknown":
        records[0]["query_id"] = "unknown"
    elif mutation == "unknown_candidate":
        records[0]["candidate_id"] = "unknown"
    elif mutation == "invalid_grade":
        records[0]["relevance_grade"] = 3
    elif mutation == "missing":
        records.pop()
    elif mutation == "blank":
        records[0]["relevance_grade"] = None
    elif mutation == "provenance":
        records[0]["dataset_sha256"] = "d" * 64
    with pytest.raises(AnnotationError, match=message):
        validate_submission(records, sample, pairs, identity)


def test_exclusion_handling_rejects_duplicate_unknown_and_judged_excluded_query():
    sample, pairs, identity, reviewers = _fixtures()
    exclusion = {
        "exclusion_version": "assistly-human-exclusion-v1",
        "dataset_version": "assistly-golden-220-v1",
        "dataset_sha256": "a" * 64,
        "example_id": "q-2",
        "excluded_by": "review-lead",
        "reason": "source_unavailable",
        "status": "excluded",
    }
    assert validate_exclusions([exclusion], sample) == {"q-2": exclusion}
    with pytest.raises(AnnotationError, match="duplicate exclusion"):
        validate_exclusions([exclusion, exclusion], sample)
    with pytest.raises(AnnotationError, match="unknown query"):
        validate_exclusions([{**exclusion, "example_id": "unknown"}], sample)
    with pytest.raises(AnnotationError, match="also has judgments"):
        validate_submission(reviewers[0], sample, pairs, identity, [exclusion])
    trimmed_pairs = [pair for pair in pairs if pair["query_id"] == "q-1"]
    trimmed_records = [row for row in reviewers[0] if row["query_id"] == "q-1"]
    assert len(validate_submission(
        trimmed_records, sample, trimmed_pairs, identity, [exclusion]
    )) == 3


def test_adjudication_requires_two_complete_reviewers_and_resolves_disagreements():
    sample, pairs, identity, reviewers = _fixtures()
    first = validate_submission(reviewers[0], sample, pairs, identity)
    second = validate_submission(reviewers[1], sample, pairs, identity)
    decision = {
        "query_id": "q-1",
        "candidate_id": "c-2",
        "final_grade": 1,
        "adjudicator_id": "review-lead",
        "rationale": "Provides supporting context.",
    }
    final = validate_adjudications(first, second, [decision])
    assert len(final) == len(pairs)
    assert final[("q-1", "c-1")]["relevance_grade"] == 2
    assert final[("q-1", "c-2")]["relevance_grade"] == 1
    with pytest.raises(AnnotationError, match="resolve every disagreement"):
        validate_adjudications(first, second, [])
    with pytest.raises(AnnotationError, match="duplicate adjudication"):
        validate_adjudications(first, second, [decision, decision])


def test_metrics_match_known_graded_fixture_and_ignore_zero_relevance_queries():
    sample, pairs, identity, reviewers = _fixtures()
    first = validate_submission(reviewers[0], sample, pairs, identity)
    second = validate_submission(reviewers[1], sample, pairs, identity)
    final = list(validate_adjudications(
        first,
        second,
        [{
            "query_id": "q-1",
            "candidate_id": "c-2",
            "final_grade": 1,
            "adjudicator_id": "review-lead",
            "rationale": "Adjudicated.",
        }],
    ).values())
    report = evaluate(final, sample, pairs, identity)
    assert report["candidate_pairs_judged"] == 6
    assert report["coverage"] == 1
    assert report["eligible_positive_queries"] == 2
    assert report["metrics"]["recall_at_k"]["1"] == pytest.approx(0.25)
    assert report["metrics"]["recall_at_k"]["3"] == 1
    assert report["metrics"]["mrr"] == pytest.approx(2 / 3)
    assert report["metrics"]["ndcg_at_k"]["1"] == pytest.approx(0.5)
    assert report["metrics"]["ndcg_at_k"]["3"] == pytest.approx(0.75)


def test_incomplete_or_non_adjudicated_results_are_rejected():
    sample, pairs, identity, reviewers = _fixtures()
    first = validate_submission(reviewers[0], sample, pairs, identity)
    second = validate_submission(reviewers[1], sample, pairs, identity)
    final = list(validate_adjudications(
        first, second, [{
            "query_id": "q-1",
            "candidate_id": "c-2",
            "final_grade": 1,
            "adjudicator_id": "review-lead",
        }]
    ).values())
    with pytest.raises(AnnotationError, match="candidate judgments missing"):
        evaluate(final[:-1], sample, pairs, identity)
    final[0]["adjudication_status"] = "pending"
    with pytest.raises(AnnotationError, match="must be adjudicated"):
        evaluate(final, sample, pairs, identity)


def test_zero_relevant_queries_produce_null_metrics_not_fabricated_zero_scores():
    sample, pairs, identity, _reviewers = _fixtures()
    records = []
    for pair in pairs:
        records.append({
            **identity,
            **pair,
            "relevance_grade": 0,
            "adjudication_status": "adjudicated",
            "source_reviewer_ids": ["reviewer-a", "reviewer-b"],
            "adjudicator_id": "agreement",
        })
    report = evaluate(records, sample, pairs, identity)
    assert report["eligible_positive_queries"] == 0
    assert report["metrics"]["recall_at_k"]["1"] is None
    assert report["metrics"]["mrr"] is None
    assert report["metrics"]["ndcg_at_k"]["5"] is None


def test_benchmark_export_is_complete_blank_and_uses_pseudonymous_candidate_ids(tmp_path):
    outputs = export_templates(tmp_path)
    second_outputs = export_templates(tmp_path / "second-export")
    assert len(outputs) == 2
    for output, second_output in zip(outputs, second_outputs, strict=True):
        records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
        assert output.read_bytes() == second_output.read_bytes()
        assert len(records) == 250
        assert all(row["relevance_grade"] is None for row in records)
        assert all(row["rationale"] == "" for row in records)
        assert all(row["reviewer_id"] in {"reviewer-01", "reviewer-02"} for row in records)
        assert all(
            row["candidate_id"].startswith("candidate-")
            and len(row["candidate_id"]) == len("candidate-") + 64
            for row in records
        )
        assert len({(row["query_id"], row["candidate_id"]) for row in records}) == 250

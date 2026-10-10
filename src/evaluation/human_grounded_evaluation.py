"""Versioned human annotation, agreement, adjudication, and evaluation tools."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping
from uuid import uuid4

from sklearn.metrics import confusion_matrix, f1_score

from src.evaluation.dataset_manifest import (
    DEFAULT_MANIFEST,
    sha256_file,
    verify_dataset,
)
from src.evaluation.evaluate_integrated_agent import _git_revision, _working_tree_dirty

SAMPLE_VERSION = "assistly-human-subset-v1"
ANNOTATION_VERSION = "assistly-human-annotation-v2"
ADJUDICATION_VERSION = "assistly-human-adjudication-v1"
HUMAN_EVALUATOR_VERSION = "human-grounded-evaluator-v2"
HUMAN_EVALUATION_SCHEMA_VERSION = "assistly-human-evaluation-schema-v2"
DEFAULT_SAMPLE = Path("reports/evaluation/human_annotation_sample_v1.json")
DEFAULT_ANNOTATIONS = Path("reports/evaluation/human_annotations_v2.jsonl")
INTENTS = (
    "delivery_status_delay",
    "delivery_marked_delivered_missing",
    "return_refund",
    "item_condition_or_fulfilment",
    "order_cancellation_or_change",
    "prime_membership",
    "account_access_security",
    "payment_charge_issue",
    "product_availability_pricing",
    "marketplace_seller",
    "other_unclear",
)
SUFFICIENCY = {"sufficient", "insufficient", "conflicting", "uncertain", "not_annotated"}
ESCALATIONS = {"escalate", "auto_handle", "uncertain", "not_annotated"}
CRITERIA = {
    "addresses_primary_issue",
    "uses_relevant_evidence",
    "actionable_next_step",
    "professional_and_empathetic",
    "no_unsupported_claims",
    "protects_sensitive_information",
    "escalates_when_required",
}
QUALITY = {
    "acceptable",
    "partially_acceptable",
    "unacceptable",
    "uncertain",
    "not_assessed",
}
GROUNDEDNESS = {
    "supported",
    "partially_supported",
    "unsupported",
    "uncertain",
    "not_assessed",
}
CLAIM_DETECTION = {"yes", "no", "uncertain", "not_assessed"}
EXCLUSION_VERSION = "assistly-human-exclusion-v1"
EXCLUSION_REASONS = {
    "source_unavailable",
    "source_unreadable",
    "duplicate_example",
    "privacy_review",
    "other",
}
LABEL_FIELDS = (
    "expected_intent",
    "evidence_sufficiency",
    "expected_escalation",
    "unsupported_claim_allowed",
)
FINAL_LABEL_FIELDS = (
    "expected_intent",
    "relevant_evidence_ids",
    "evidence_relevance",
    "evidence_sufficiency",
    "expected_escalation",
    "acceptable_answer_criteria",
    "unsupported_claim_allowed",
    "response_assessments",
)


class AnnotationError(ValueError):
    """Raised when an annotation artifact is invalid or incompatible."""


def _is_pseudonymous_identifier(value: Any) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", value) is not None
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AnnotationError(f"{path}:{line_number} is not valid JSON") from exc
            if not isinstance(value, dict):
                raise AnnotationError(f"{path}:{line_number} must contain an object")
            records.append(value)
    return records


def create_sample_manifest(
    dataset_path: Path,
    manifest_path: Path = DEFAULT_MANIFEST,
    sample_size: int = 50,
) -> dict[str, Any]:
    manifest, rows = verify_dataset(dataset_path, manifest_path)
    if isinstance(sample_size, bool) or not isinstance(sample_size, int):
        raise ValueError("sample_size must be an integer")
    if not 1 <= sample_size <= len(rows):
        raise ValueError(f"sample_size must be between 1 and {len(rows)}")
    selected = sorted(
        rows,
        key=lambda row: hashlib.sha256(
            f"{SAMPLE_VERSION}:{row['example_id']}".encode("utf-8")
        ).hexdigest(),
    )[:sample_size]
    return {
        "sample_version": SAMPLE_VERSION,
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": manifest["sha256"],
        "dataset_provenance_status": manifest["provenance_status"],
        "sample_size": sample_size,
        "sampling_method": (
            "lowest SHA-256(example_id prefixed by sample version), independent "
            "of provisional intent labels"
        ),
        "example_ids": sorted(row["example_id"] for row in selected),
    }


def load_sample(path: Path = DEFAULT_SAMPLE) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AnnotationError("sample manifest must be an object")
    if value.get("sample_version") != SAMPLE_VERSION:
        raise AnnotationError("unsupported human annotation sample version")
    manifest, _ = verify_dataset(
        Path("data/golden/golden_set.csv"), DEFAULT_MANIFEST
    )
    if (
        value.get("dataset_version") != manifest["dataset_version"]
        or value.get("dataset_sha256") != manifest["sha256"]
        or value.get("dataset_provenance_status") != "unresolved_provisional"
    ):
        raise AnnotationError("human sample does not match the frozen dataset identity")
    ids = value.get("example_ids")
    if (
        not isinstance(ids, list)
        or not ids
        or isinstance(value.get("sample_size"), bool)
        or not isinstance(value.get("sample_size"), int)
        or any(not isinstance(item, str) or not item for item in ids)
        or len(ids) != len(set(ids))
        or value.get("sample_size") != len(ids)
    ):
        raise AnnotationError("sample manifest example IDs are invalid")
    expected = create_sample_manifest(
        Path("data/golden/golden_set.csv"),
        DEFAULT_MANIFEST,
        value["sample_size"],
    )
    if (
        value.get("sampling_method") != expected["sampling_method"]
        or ids != expected["example_ids"]
    ):
        raise AnnotationError("sample manifest does not match the versioned sampling method")
    return value


def create_annotation_template(
    sample: Mapping[str, Any], annotator_id: str
) -> list[dict[str, Any]]:
    if not _is_pseudonymous_identifier(annotator_id):
        raise AnnotationError(
            "annotator_id must be a pseudonymous ID using letters, digits, "
            "periods, underscores, or hyphens"
        )
    annotator = annotator_id
    return [
        {
            "annotation_version": ANNOTATION_VERSION,
            "dataset_version": sample["dataset_version"],
            "dataset_sha256": sample["dataset_sha256"],
            "example_id": example_id,
            "annotator_id": annotator,
            "annotation_status": "not_annotated",
            "expected_intent": "not_annotated",
            "relevant_evidence_ids": [],
            "evidence_relevance": [],
            "evidence_sufficiency": "not_annotated",
            "expected_escalation": "not_annotated",
            "acceptable_answer_criteria": [],
            "unsupported_claim_allowed": "not_annotated",
            "response_assessments": [],
        }
        for example_id in sample["example_ids"]
    ]


def validate_annotation_records(
    records: Iterable[Mapping[str, Any]],
    sample: Mapping[str, Any],
) -> list[dict[str, Any]]:
    expected_ids = set(sample["example_ids"])
    seen: set[tuple[str, str]] = set()
    result = []
    allowed_fields = {
        "annotation_version",
        "dataset_version",
        "dataset_sha256",
        "example_id",
        "annotator_id",
        "annotation_status",
        *FINAL_LABEL_FIELDS,
    }
    for index, source in enumerate(records, 1):
        record = dict(source)
        if set(record) != allowed_fields:
            raise AnnotationError(f"record {index}: fields do not match annotation schema")
        example_id = record.get("example_id")
        annotator_id = record.get("annotator_id")
        if record.get("annotation_version") != ANNOTATION_VERSION:
            raise AnnotationError(f"record {index}: unsupported annotation version")
        if (
            record.get("dataset_version") != sample["dataset_version"]
            or record.get("dataset_sha256") != sample["dataset_sha256"]
        ):
            raise AnnotationError(f"record {index}: frozen dataset identity mismatch")
        if not isinstance(example_id, str) or example_id not in expected_ids:
            raise AnnotationError(f"record {index}: example_id is not in the sample")
        if not isinstance(annotator_id, str):
            raise AnnotationError(f"record {index}: pseudonymous annotator_id is required")
        if not _is_pseudonymous_identifier(annotator_id):
            raise AnnotationError(f"record {index}: pseudonymous annotator_id is required")
        pair = (example_id, annotator_id)
        if pair in seen:
            raise AnnotationError(
                f"duplicate annotation by annotator {annotator_id!r} for {example_id!r}"
            )
        seen.add(pair)
        if not isinstance(record.get("annotation_status"), str) or record[
            "annotation_status"
        ] not in {
            "annotated",
            "uncertain",
            "not_annotated",
        }:
            raise AnnotationError(f"record {index}: invalid annotation_status")
        if not isinstance(record.get("expected_intent"), str) or record[
            "expected_intent"
        ] not in {*INTENTS, "uncertain", "not_annotated"}:
            raise AnnotationError(f"record {index}: invalid expected_intent")
        if not isinstance(record.get("evidence_sufficiency"), str) or record[
            "evidence_sufficiency"
        ] not in SUFFICIENCY:
            raise AnnotationError(f"record {index}: invalid evidence_sufficiency")
        if not isinstance(record.get("expected_escalation"), str) or record[
            "expected_escalation"
        ] not in ESCALATIONS:
            raise AnnotationError(f"record {index}: invalid expected_escalation")
        if not isinstance(record.get("unsupported_claim_allowed"), str) or record[
            "unsupported_claim_allowed"
        ] not in {"yes", "no", "uncertain", "not_annotated"}:
            raise AnnotationError(f"record {index}: invalid unsupported_claim_allowed")
        relevance = record.get("evidence_relevance")
        if not isinstance(relevance, list):
            raise AnnotationError(f"record {index}: evidence_relevance must be a list")
        relevance_scores: dict[str, int] = {}
        for rating in relevance:
            if not isinstance(rating, dict):
                raise AnnotationError(f"record {index}: relevance entries must be objects")
            evidence_id, score = rating.get("evidence_id"), rating.get("score")
            if (
                not isinstance(evidence_id, str)
                or not evidence_id
                or isinstance(score, bool)
                or not isinstance(score, int)
                or score not in {0, 1, 2}
                or evidence_id in relevance_scores
            ):
                raise AnnotationError(f"record {index}: invalid/duplicate relevance entry")
            relevance_scores[evidence_id] = score
        relevant_ids = record.get("relevant_evidence_ids")
        if (
            not isinstance(relevant_ids, list)
            or any(not isinstance(item, str) or not item for item in relevant_ids)
            or len(relevant_ids) != len(set(relevant_ids))
            or set(relevant_ids)
            != {evidence_id for evidence_id, score in relevance_scores.items() if score > 0}
        ):
            raise AnnotationError(
                f"record {index}: relevant_evidence_ids must match evidence scores above zero"
            )
        criteria = record.get("acceptable_answer_criteria")
        if (
            not isinstance(criteria, list)
            or any(not isinstance(item, str) or item not in CRITERIA for item in criteria)
            or len(criteria) != len(set(criteria))
        ):
            raise AnnotationError(f"record {index}: invalid acceptable-answer criteria")
        assessments = record.get("response_assessments")
        if not isinstance(assessments, list):
            raise AnnotationError(f"record {index}: response_assessments must be a list")
        assessment_run_ids = set()
        for assessment in assessments:
            if not isinstance(assessment, dict) or set(assessment) != {
                "run_id", "quality", "groundedness", "unsupported_claim_detected"
            }:
                raise AnnotationError(
                    f"record {index}: invalid response assessment fields"
                )
            run_id = assessment.get("run_id")
            if (
                not isinstance(run_id, str)
                or not run_id.strip()
                or run_id in assessment_run_ids
            ):
                raise AnnotationError(
                    f"record {index}: response assessment run IDs must be unique"
                )
            assessment_run_ids.add(run_id)
            if not isinstance(assessment.get("quality"), str) or assessment[
                "quality"
            ] not in QUALITY:
                raise AnnotationError(f"record {index}: invalid response quality")
            if not isinstance(assessment.get("groundedness"), str) or assessment[
                "groundedness"
            ] not in GROUNDEDNESS:
                raise AnnotationError(f"record {index}: invalid response groundedness")
            if not isinstance(
                assessment.get("unsupported_claim_detected"), str
            ) or assessment["unsupported_claim_detected"] not in CLAIM_DETECTION:
                raise AnnotationError(
                    f"record {index}: invalid unsupported_claim_detected value"
                )
        if record["annotation_status"] == "annotated" and (
            record["expected_intent"] not in INTENTS
            or record["evidence_sufficiency"] not in {
                "sufficient", "insufficient", "conflicting"
            }
            or record["expected_escalation"] not in {"escalate", "auto_handle"}
            or record["unsupported_claim_allowed"] not in {"yes", "no"}
            or not criteria
        ):
            raise AnnotationError(
                f"record {index}: annotated records require definitive intent, "
                "sufficiency, escalation, unsupported-claim, and answer criteria"
            )
        if record["annotation_status"] == "not_annotated" and (
            record["expected_intent"] != "not_annotated"
            or record["relevant_evidence_ids"]
            or relevance_scores
            or record["evidence_sufficiency"] != "not_annotated"
            or record["expected_escalation"] != "not_annotated"
            or record["acceptable_answer_criteria"]
            or record["unsupported_claim_allowed"] != "not_annotated"
            or assessments
        ):
            raise AnnotationError(
                f"record {index}: not_annotated records must not contain labels"
            )
        result.append(record)
    return result


def create_adjudication_record(
    sample: Mapping[str, Any],
    example_id: str,
    adjudicator_id: str,
    source_annotator_ids: list[str],
    final_labels: Mapping[str, Any],
    annotations: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    record = {
        "adjudication_version": ADJUDICATION_VERSION,
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": example_id,
        "adjudicator_id": adjudicator_id,
        "source_annotator_ids": source_annotator_ids,
        "adjudication_status": "adjudicated",
        "final_labels": dict(final_labels),
    }
    validate_adjudication_records([record], sample, annotations)
    return record


def validate_adjudication_records(
    records: Iterable[Mapping[str, Any]],
    sample: Mapping[str, Any],
    source_annotations: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    expected_ids = set(sample["example_ids"])
    seen: set[str] = set()
    validated = []
    submitted = (
        validate_annotation_records(source_annotations, sample)
        if source_annotations is not None else None
    )
    allowed_fields = {
        "adjudication_version",
        "dataset_version",
        "dataset_sha256",
        "example_id",
        "adjudicator_id",
        "source_annotator_ids",
        "adjudication_status",
        "final_labels",
    }
    for index, source in enumerate(records, 1):
        record = dict(source)
        if set(record) != allowed_fields:
            raise AnnotationError(f"adjudication {index}: fields do not match schema")
        example_id = record.get("example_id")
        if record.get("adjudication_version") != ADJUDICATION_VERSION:
            raise AnnotationError(f"adjudication {index}: unsupported version")
        if (
            record.get("dataset_version") != sample["dataset_version"]
            or record.get("dataset_sha256") != sample["dataset_sha256"]
            or not isinstance(example_id, str)
            or example_id not in expected_ids
        ):
            raise AnnotationError(f"adjudication {index}: dataset identity mismatch")
        if example_id in seen:
            raise AnnotationError(f"duplicate adjudication for {example_id!r}")
        seen.add(example_id)
        adjudicator = record.get("adjudicator_id")
        sources = record.get("source_annotator_ids")
        if not _is_pseudonymous_identifier(adjudicator):
            raise AnnotationError(f"adjudication {index}: adjudicator_id is required")
        if (
            not isinstance(sources, list)
            or len(sources) < 2
            or any(not _is_pseudonymous_identifier(item) for item in sources)
            or len(sources) != len(set(sources))
            or adjudicator in sources
        ):
            raise AnnotationError(f"adjudication {index}: invalid source annotators")
        if submitted is not None:
            available_sources = {
                row["annotator_id"]
                for row in submitted
                if row["example_id"] == example_id
                and row["annotation_status"] == "annotated"
            }
            if not set(sources).issubset(available_sources):
                raise AnnotationError(
                    f"adjudication {index}: source annotations are missing or incomplete"
                )
        if record.get("adjudication_status") != "adjudicated":
            raise AnnotationError(f"adjudication {index}: status must be adjudicated")
        labels = record.get("final_labels")
        if not isinstance(labels, dict) or set(labels) != set(FINAL_LABEL_FIELDS):
            raise AnnotationError(f"adjudication {index}: final label fields are invalid")
        annotation = {
            "annotation_version": ANNOTATION_VERSION,
            "dataset_version": sample["dataset_version"],
            "dataset_sha256": sample["dataset_sha256"],
            "example_id": example_id,
            "annotator_id": adjudicator,
            "annotation_status": "annotated",
            **labels,
        }
        validate_annotation_records([annotation], sample)
        validated.append(record)
    return validated


def validate_exclusion_records(
    records: Iterable[Mapping[str, Any]],
    sample: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Validate sample exclusions as separate, privacy-minimized decisions."""
    expected_ids = set(sample["example_ids"])
    seen: set[str] = set()
    validated = []
    allowed_fields = {
        "exclusion_version",
        "dataset_version",
        "dataset_sha256",
        "example_id",
        "excluded_by",
        "reason",
        "status",
    }
    for index, source in enumerate(records, 1):
        record = dict(source)
        if set(record) != allowed_fields:
            raise AnnotationError(f"exclusion {index}: fields do not match schema")
        example_id = record.get("example_id")
        if (
            record.get("exclusion_version") != EXCLUSION_VERSION
            or record.get("dataset_version") != sample["dataset_version"]
            or record.get("dataset_sha256") != sample["dataset_sha256"]
        ):
            raise AnnotationError(f"exclusion {index}: dataset identity mismatch")
        if not isinstance(example_id, str) or example_id not in expected_ids:
            raise AnnotationError(f"exclusion {index}: example_id is not in the sample")
        if example_id in seen:
            raise AnnotationError(f"duplicate exclusion for {example_id!r}")
        seen.add(example_id)
        excluded_by = record.get("excluded_by")
        if not _is_pseudonymous_identifier(excluded_by):
            raise AnnotationError(f"exclusion {index}: pseudonymous excluded_by is required")
        if record.get("reason") not in EXCLUSION_REASONS:
            raise AnnotationError(f"exclusion {index}: invalid reason")
        if record.get("status") != "excluded":
            raise AnnotationError(f"exclusion {index}: status must be excluded")
        validated.append(record)
    return validated


def create_exclusion_record(
    sample: Mapping[str, Any],
    example_id: str,
    excluded_by: str,
    reason: str,
) -> dict[str, Any]:
    record = {
        "exclusion_version": EXCLUSION_VERSION,
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "example_id": example_id,
        "excluded_by": excluded_by,
        "reason": reason,
        "status": "excluded",
    }
    return validate_exclusion_records([record], sample)[0]


def summarize_annotation_coverage(
    sample: Mapping[str, Any],
    annotations: Iterable[Mapping[str, Any]],
    adjudications: Iterable[Mapping[str, Any]] = (),
    exclusions: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Report per-example workflow state without promoting submissions to truth."""
    annotation_records = validate_annotation_records(annotations, sample)
    adjudication_records = validate_adjudication_records(
        adjudications, sample, annotation_records
    )
    exclusion_records = validate_exclusion_records(exclusions, sample)
    annotations_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in annotation_records:
        annotations_by_id[record["example_id"]].append(record)
    adjudicated_ids = {
        record["example_id"]
        for record in adjudication_records
        if record["adjudication_status"] == "adjudicated"
    }
    excluded_ids = {record["example_id"] for record in exclusion_records}
    overlap = adjudicated_ids & excluded_ids
    if overlap:
        raise AnnotationError(
            f"examples cannot be both adjudicated and excluded: {sorted(overlap)}"
        )

    states: dict[str, str] = {}
    for example_id in sample["example_ids"]:
        records = annotations_by_id.get(example_id, [])
        if example_id in excluded_ids:
            state = "excluded"
        elif example_id in adjudicated_ids:
            state = "adjudicated"
        elif any(row["annotation_status"] == "annotated" for row in records):
            state = (
                "annotated_pending_adjudication"
                if all(row["annotation_status"] == "annotated" for row in records)
                else "partially_annotated"
            )
        elif any(row["annotation_status"] == "uncertain" for row in records):
            state = "partially_annotated"
        else:
            state = "unannotated"
        states[example_id] = state
    counts = dict(Counter(states.values()))
    return {
        "sample_version": sample["sample_version"],
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "sample_size": len(sample["example_ids"]),
        "annotation_records": len(annotation_records),
        "adjudication_records": len(adjudication_records),
        "exclusion_records": len(exclusion_records),
        "status_counts": counts,
        "examples": [
            {"example_id": example_id, "status": states[example_id]}
            for example_id in sample["example_ids"]
        ],
        "human_ground_truth_count": counts.get("adjudicated", 0),
        "note": (
            "Annotation submissions are not ground truth; only valid adjudicated "
            "records count as human ground truth. Exclusions are reported separately."
        ),
    }


def cohen_kappa(first: list[str], second: list[str]) -> float | None:
    if len(first) != len(second):
        raise ValueError("rating vectors must have equal lengths")
    if not first:
        return None
    observed = sum(left == right for left, right in zip(first, second)) / len(first)
    counts_a, counts_b = Counter(first), Counter(second)
    labels = set(counts_a) | set(counts_b)
    expected = sum(
        counts_a[label] * counts_b[label] / (len(first) * len(second))
        for label in labels
    )
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def fleiss_kappa(ratings: list[list[str]]) -> float | None:
    if not ratings or any(not row for row in ratings):
        return None
    counts_per_item = {len(row) for row in ratings}
    if len(counts_per_item) != 1 or next(iter(counts_per_item)) < 2:
        return None
    labels = sorted({label for row in ratings for label in row})
    raters = next(iter(counts_per_item))
    proportions = {
        label: sum(row.count(label) for row in ratings) / (len(ratings) * raters)
        for label in labels
    }
    item_agreements = [
        (sum(row.count(label) ** 2 for label in labels) - raters)
        / (raters * (raters - 1))
        for row in ratings
    ]
    observed = mean(item_agreements)
    expected = sum(value**2 for value in proportions.values())
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def quadratic_weighted_cohen_kappa(
    first: list[int], second: list[int], categories: tuple[int, ...] = (0, 1, 2)
) -> float | None:
    if len(first) != len(second):
        raise ValueError("rating vectors must have equal lengths")
    if not first:
        return None
    if any(item not in categories for item in (*first, *second)):
        raise ValueError("ordinal ratings contain an unsupported category")
    observed = 0.0
    expected = 0.0
    size = len(categories)
    for left_index, left in enumerate(categories):
        for right_index, right in enumerate(categories):
            weight = ((left_index - right_index) / (size - 1)) ** 2
            observed_count = sum(a == left and b == right for a, b in zip(first, second))
            expected_count = first.count(left) * second.count(right) / len(first)
            observed += weight * observed_count / len(first)
            expected += weight * expected_count / len(first)
    if expected == 0:
        return None
    return 1 - observed / expected


def analyze_annotations(
    annotations: Iterable[Mapping[str, Any]],
    sample: Mapping[str, Any],
) -> dict[str, Any]:
    records = validate_annotation_records(annotations, sample)
    completed = [row for row in records if row["annotation_status"] == "annotated"]
    uncertain_count = sum(row["annotation_status"] == "uncertain" for row in records)
    unannotated_count = sum(
        row["annotation_status"] == "not_annotated" for row in records
    )
    by_example: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in completed:
        by_example[record["example_id"]].append(record)
    disagreements = []
    for example_id, group in sorted(by_example.items()):
        fields = {}
        for field in (*LABEL_FIELDS, "acceptable_answer_criteria"):
            values = sorted({
                tuple(sorted(row[field]))
                if field == "acceptable_answer_criteria"
                else row[field]
                for row in group
            })
            if len(values) > 1:
                fields[field] = values
        relevance: dict[str, set[int]] = defaultdict(set)
        for record in group:
            for rating in record["evidence_relevance"]:
                relevance[rating["evidence_id"]].add(rating["score"])
        evidence_disagreements = {
            evidence_id: sorted(scores)
            for evidence_id, scores in relevance.items()
            if len(scores) > 1
        }
        response_reviews: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in group:
            for assessment in record["response_assessments"]:
                run_id = assessment["run_id"]
                response_reviews[run_id].append(assessment)
        response_disagreements = {}
        for run_id, assessments in response_reviews.items():
            differing_fields = {
                field: sorted({assessment[field] for assessment in assessments})
                for field in (
                    "quality",
                    "groundedness",
                    "unsupported_claim_detected",
                )
                if len({assessment[field] for assessment in assessments}) > 1
            }
            if differing_fields:
                response_disagreements[run_id] = differing_fields
        if fields or evidence_disagreements or response_disagreements:
            disagreements.append({
                "example_id": example_id,
                "fields": fields,
                "evidence_relevance": evidence_disagreements,
                "response_assessment": response_disagreements,
            })

    categorical: dict[str, Any] = {}
    annotator_ids = sorted({row["annotator_id"] for row in completed})
    for field in LABEL_FIELDS:
        item_ratings: dict[str, dict[str, str]] = defaultdict(dict)
        for row in completed:
            value = row[field]
            if value not in {"uncertain", "not_annotated"}:
                item_ratings[row["example_id"]][row["annotator_id"]] = value
        if len(annotator_ids) == 2:
            common = sorted(
                example_id for example_id, scores in item_ratings.items()
                if all(name in scores for name in annotator_ids)
            )
            categorical[field] = {
                "metric": "cohen_kappa",
                "value": cohen_kappa(
                    [item_ratings[item][annotator_ids[0]] for item in common],
                    [item_ratings[item][annotator_ids[1]] for item in common],
                ),
                "denominator": len(common),
                "status": "measured" if common else "not_measured",
            }
        elif len(annotator_ids) >= 3:
            balanced = [
                list(scores.values())
                for scores in item_ratings.values()
                if len(scores) == len(annotator_ids)
            ]
            complete_item_count = len(balanced)
            value = fleiss_kappa(balanced)
            categorical[field] = {
                "metric": "fleiss_kappa",
                "value": value,
                "denominator": complete_item_count,
                "status": (
                    "measured" if value is not None
                    else "not_measured_balanced_non_degenerate_ratings_required"
                ),
            }
        else:
            categorical[field] = {
                "metric": "not_available",
                "value": None,
                "denominator": 0,
                "status": "not_measured_fewer_than_two_annotators",
            }

    ordinal: dict[str, Any] = {
        "metric": "quadratic_weighted_cohen_kappa",
        "value": None,
        "denominator": 0,
        "status": "not_measured_fewer_than_two_annotators",
    }
    if len(annotator_ids) == 2:
        ratings_by_key: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
        for row in completed:
            for rating in row["evidence_relevance"]:
                ratings_by_key[(row["example_id"], rating["evidence_id"])][
                    row["annotator_id"]
                ] = rating["score"]
        common = sorted(
            key for key, values in ratings_by_key.items()
            if all(name in values for name in annotator_ids)
        )
        value = quadratic_weighted_cohen_kappa(
            [ratings_by_key[key][annotator_ids[0]] for key in common],
            [ratings_by_key[key][annotator_ids[1]] for key in common],
        )
        ordinal = {
            "metric": "quadratic_weighted_cohen_kappa",
            "value": value,
            "denominator": len(common),
            "status": "measured" if value is not None else "not_measured",
        }
    return {
        "annotation_version": ANNOTATION_VERSION,
        "sample_version": sample["sample_version"],
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "records_received": len(records),
        "annotated_records": len(completed),
        "uncertain_records": uncertain_count,
        "not_annotated_records": unannotated_count,
        "annotator_count": len(annotator_ids),
        "annotator_ids": annotator_ids,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "categorical_agreement": categorical,
        "ordinal_evidence_relevance_agreement": ordinal,
        "provenance_note": "Agreement describes submitted annotations only; no human values are inferred.",
    }


def evaluate_human_grounded_run(
    run_metadata: Mapping[str, Any],
    run_rows: Iterable[Mapping[str, Any]],
    adjudications: Iterable[Mapping[str, Any]],
    sample: Mapping[str, Any],
    source_annotations: Iterable[Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    annotations = (
        validate_annotation_records(source_annotations, sample)
        if source_annotations is not None else None
    )
    final_records = validate_adjudication_records(
        adjudications, sample, annotations
    )
    labels = {
        row["example_id"]: row["final_labels"]
        for row in final_records
        if row["adjudication_status"] == "adjudicated"
    }
    rows_by_id = {}
    for row in run_rows:
        example_id = row.get("example_id")
        if not isinstance(example_id, str) or not example_id:
            raise AnnotationError("run rows require example_id")
        if example_id in rows_by_id:
            raise AnnotationError(f"duplicate run result for {example_id!r}")
        rows_by_id[example_id] = dict(row)

    joined = [
        (example_id, labels[example_id], rows_by_id[example_id])
        for example_id in sorted(set(labels) & set(rows_by_id))
    ]
    latency_samples = [
        float(result["latency_ms"])
        for _, _, result in joined
        if isinstance(result.get("latency_ms"), (int, float))
        and not isinstance(result.get("latency_ms"), bool)
        and math.isfinite(result["latency_ms"])
    ]
    expected_intents: list[str] = []
    predicted_intents: list[str] = []
    relevance_values = {1: [], 3: [], 5: []}
    ndcg_values = {1: [], 3: [], 5: []}
    reciprocal_ranks: list[float] = []
    retrieval_eligible_count = 0
    retrieval_failed_count = 0
    retrieval_output_count = 0
    sufficiency_truth, sufficiency_predicted = [], []
    sufficiency_expected_count = 0
    sufficiency_observed_count = 0
    sufficiency_output_present = False
    escalation_truth, escalation_predicted = [], []
    escalation_expected_count = 0
    escalation_observed_count = 0
    escalation_output_present = False
    response_quality, human_groundedness, unsupported_flags = [], [], []
    failures = []
    for example_id, truth, result in joined:
        expected = truth["expected_intent"]
        predicted = result.get("predicted_intent")
        if expected in INTENTS:
            expected_intents.append(expected)
            predicted_intents.append(
                predicted if isinstance(predicted, str) else "missing_prediction"
            )
        relevance_scores = {
            item["evidence_id"]: item["score"]
            for item in truth["evidence_relevance"]
        }
        relevance_ids = {
            evidence_id for evidence_id, score in relevance_scores.items()
            if score > 0
        }
        retrieved_value = result.get("evidence_source_ids")
        retrieval_output_valid = isinstance(retrieved_value, list) and all(
            isinstance(item, str) and item for item in retrieved_value
        )
        retrieved = retrieved_value if retrieval_output_valid else []
        if len(retrieved) != len(set(retrieved)):
            raise AnnotationError(
                f"run result for {example_id!r} has duplicate evidence IDs"
            )
        retrieval_output_count += int(retrieval_output_valid)
        if relevance_ids:
            retrieval_eligible_count += 1
            retrieval_failed_count += int(not retrieval_output_valid)
            for k in relevance_values:
                relevance_values[k].append(
                    len(relevance_ids & set(retrieved[:k])) / len(relevance_ids)
                )
            rank = next(
                (index for index, evidence_id in enumerate(retrieved, 1)
                 if evidence_id in relevance_ids),
                None,
            )
            reciprocal_ranks.append(1 / rank if rank else 0.0)
            for k in ndcg_values:
                dcg = sum(
                    (2 ** relevance_scores.get(evidence_id, 0) - 1)
                    / math.log2(rank_index + 1)
                    for rank_index, evidence_id in enumerate(retrieved[:k], 1)
                )
                ideal_grades = sorted(relevance_scores.values(), reverse=True)[:k]
                ideal_dcg = sum(
                    (2 ** grade - 1) / math.log2(rank_index + 1)
                    for rank_index, grade in enumerate(ideal_grades, 1)
                )
                ndcg_values[k].append(dcg / ideal_dcg if ideal_dcg else 0.0)
        expected_sufficiency = truth["evidence_sufficiency"]
        observed_sufficiency = result.get("evidence_status")
        if expected_sufficiency in {"sufficient", "insufficient", "conflicting"}:
            sufficiency_expected_count += 1
            if "evidence_status" in result:
                sufficiency_output_present = True
                normalized_sufficiency = (
                    "insufficient" if observed_sufficiency in {"none", "weak"}
                    else observed_sufficiency
                )
                sufficiency_truth.append(expected_sufficiency)
                sufficiency_predicted.append(
                    normalized_sufficiency
                    if normalized_sufficiency in {
                        "sufficient", "insufficient", "conflicting"
                    }
                    else "missing_evidence_status"
                )
                sufficiency_observed_count += normalized_sufficiency in {
                    "sufficient", "insufficient", "conflicting"
                }
        expected_escalation = truth["expected_escalation"]
        decision = result.get("decision")
        if expected_escalation in {"escalate", "auto_handle"}:
            escalation_expected_count += 1
            if "decision" in result:
                escalation_output_present = True
                escalation_truth.append(expected_escalation)
                escalation_predicted.append(
                    decision if decision in {"escalate", "auto_handle"}
                    else "missing_decision"
                )
                escalation_observed_count += decision in {"escalate", "auto_handle"}
        assessment = next(
            (
                item for item in truth["response_assessments"]
                if item["run_id"] == run_metadata.get("run_id")
            ),
            {},
        )
        if assessment:
            quality_score = {
                "acceptable": 1.0,
                "partially_acceptable": 0.5,
                "unacceptable": 0.0,
            }.get(assessment["quality"])
            if quality_score is not None:
                response_quality.append(quality_score)
            if assessment["groundedness"] in {"supported", "partially_supported", "unsupported"}:
                human_groundedness.append(
                    assessment["groundedness"] == "supported"
                )
            if assessment["unsupported_claim_detected"] in {"yes", "no"}:
                unsupported_flags.append(
                    assessment["unsupported_claim_detected"] == "yes"
                )
        category = _human_failure_category(
            expected, predicted, truth, result, assessment,
            run_metadata.get("run_id"),
        )
        if category:
            failures.append({
                "example_id": example_id,
                "expected_intent": expected,
                "predicted_intent": predicted,
                "evidence_ids": retrieved,
                "expected_escalation": expected_escalation,
                "decision": decision,
                "failure_category": category,
                "evaluator_version": HUMAN_EVALUATOR_VERSION,
            })

    def ratio(
        numerator: int,
        denominator: int,
        missing_status: str = "not_measured_no_adjudicated_labels",
    ) -> dict[str, Any]:
        return {
            "value": numerator / denominator if denominator else None,
            "numerator": numerator if denominator else None,
            "denominator": denominator,
            "status": "measured" if denominator else missing_status,
        }

    escalation_tp = sum(
        truth == "escalate" and prediction == "escalate"
        for truth, prediction in zip(escalation_truth, escalation_predicted)
    )
    escalation_fp = sum(
        truth == "auto_handle" and prediction == "escalate"
        for truth, prediction in zip(escalation_truth, escalation_predicted)
    )
    escalation_fn = sum(
        truth == "escalate" and prediction != "escalate"
        for truth, prediction in zip(escalation_truth, escalation_predicted)
    )
    precision_denom = escalation_tp + escalation_fp
    recall_denom = escalation_tp + escalation_fn
    metric_results: dict[str, Any] = {
        "intent_accuracy": ratio(
            sum(a == b for a, b in zip(expected_intents, predicted_intents)),
            len(expected_intents),
        ),
        "intent_macro_f1": {
            "value": (
                float(f1_score(
                    expected_intents, predicted_intents, labels=list(INTENTS),
                    average="macro", zero_division=0,
                ))
                if expected_intents else None
            ),
            "denominator": len(expected_intents),
            "denominator_unit": "adjudicated intent labels; macro-F1 averages the fixed 11-intent taxonomy",
            "status": "measured" if expected_intents else "not_measured",
        },
        "intent_confusion_matrix": {
            "labels": list(INTENTS),
            "counts": (
                confusion_matrix(
                    expected_intents, predicted_intents, labels=list(INTENTS)
                ).tolist()
                if expected_intents else None
            ),
        },
        "retrieval_recall_at_k": {
            str(k): {
                **ratio(sum(values), len(values)),
                "status": (
                    "measured_independent_evidence_relevance"
                    if values else "not_measured_no_adjudicated_relevant_evidence"
                ),
            }
            for k, values in relevance_values.items()
        },
        "retrieval_mrr": {
            "value": mean(reciprocal_ranks) if reciprocal_ranks else None,
            "numerator": sum(reciprocal_ranks) if reciprocal_ranks else None,
            "denominator": len(reciprocal_ranks),
            "status": (
                "measured_independent_evidence_relevance"
                if reciprocal_ranks else "not_measured_no_adjudicated_relevant_evidence"
            ),
        },
        "retrieval_ndcg_at_k": {
            str(k): {
                "value": mean(values) if values else None,
                "denominator": len(values),
                "denominator_unit": (
                    "adjudicated examples with positive judged evidence"
                ),
                "status": (
                    "measured_independent_graded_evidence_relevance"
                    if values else "not_measured_no_adjudicated_graded_evidence"
                ),
            }
            for k, values in ndcg_values.items()
        },
        "retrieval_output_coverage": {
            "value": (
                (retrieval_eligible_count - retrieval_failed_count)
                / retrieval_eligible_count
                if retrieval_eligible_count else None
            ),
            "eligible_examples": retrieval_eligible_count,
            "evaluated_examples": retrieval_eligible_count - retrieval_failed_count,
            "failed_examples": retrieval_failed_count,
            "status": "measured" if retrieval_eligible_count else "not_measured",
        },
        "evidence_sufficiency_accuracy": ratio(
            sum(a == b for a, b in zip(sufficiency_truth, sufficiency_predicted)),
            len(sufficiency_truth),
        ),
        "evidence_sufficiency_coverage": (
            ratio(sufficiency_observed_count, sufficiency_expected_count)
            if sufficiency_output_present else None
        ),
        "escalation_precision": ratio(
            escalation_tp,
            precision_denom,
            "not_measured_no_predicted_escalations",
        ),
        "escalation_recall": ratio(
            escalation_tp,
            recall_denom,
            "not_measured_no_expected_escalations",
        ),
        "escalation_decision_coverage": (
            ratio(escalation_observed_count, escalation_expected_count)
            if escalation_output_present else None
        ),
        "groundedness_rate": ratio(
            sum(human_groundedness), len(human_groundedness)
        ),
        "unsupported_claim_rate": ratio(
            sum(unsupported_flags), len(unsupported_flags)
        ),
        "response_quality_mean": {
            "value": mean(response_quality) if response_quality else None,
            "numerator": sum(response_quality) if response_quality else None,
            "denominator": len(response_quality),
            "scale": {
                "acceptable": 1.0,
                "partially_acceptable": 0.5,
                "unacceptable": 0.0,
            },
            "status": "measured" if response_quality else "not_measured_no_run_matched_assessments",
        },
        "latency_ms": (
            {
                "value": mean(latency_samples),
                "mean_ms": mean(latency_samples),
                "denominator": len(latency_samples),
                "status": "measured_per_example",
            }
            if latency_samples
            else (
                {
                    "value": run_metadata["average_latency_ms"],
                    "mean_ms": run_metadata["average_latency_ms"],
                    "denominator": None,
                    "status": "measured_run_summary",
                }
                if isinstance(run_metadata.get("average_latency_ms"), (int, float))
                and not isinstance(run_metadata.get("average_latency_ms"), bool)
                else None
            )
        ),
        "token_usage": run_metadata.get("token_usage"),
        "estimated_cost": run_metadata.get(
            "estimated_cost", run_metadata.get("cost")
        ),
        "provider_failure_rate": _provider_failure_metric(joined, run_metadata),
    }
    report = {
        "evaluation": "human_grounded_system_evaluation",
        "evaluator_version": HUMAN_EVALUATOR_VERSION,
        "annotation_version": ANNOTATION_VERSION,
        "adjudication_version": ADJUDICATION_VERSION,
        "run_metadata": {
            "evaluation_id": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            + "-" + uuid4().hex[:8],
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "code_revision": _git_revision(),
            "working_tree_dirty": _working_tree_dirty(),
            "dataset_version": sample["dataset_version"],
            "dataset_sha256": sample["dataset_sha256"],
            "dataset_manifest_sha256": sha256_file(DEFAULT_MANIFEST),
            "dataset_provenance_status": sample["dataset_provenance_status"],
            "evaluation_schema_version": HUMAN_EVALUATION_SCHEMA_VERSION,
            "evaluator_version": HUMAN_EVALUATOR_VERSION,
            "prompt_version": run_metadata.get("prompt_version", "not_applicable"),
            "retrieval_version": run_metadata.get("retrieval_version", "not_applicable"),
            "evidence_policy_version": run_metadata.get(
                "evidence_policy_version", "not_applicable"
            ),
            "retrieval_backend": run_metadata.get("retrieval_backend", "not_applicable"),
            "run_mode": run_metadata.get("run_mode", "not_available"),
            "provider": run_metadata.get("provider", "not_available"),
            "model": run_metadata.get("model"),
            "configuration": run_metadata.get("configuration", {}),
            "annotation_dataset_version": sample["sample_version"],
            "annotation_sample_sha256": _json_hash(sample),
            "annotation_records_sha256": (
                _records_hash(annotations) if annotations is not None else None
            ),
            "adjudication_records_sha256": _records_hash(final_records),
            "run_id": run_metadata.get("run_id"),
            "examples_evaluated": len(joined),
            "adjudicated_examples": len(final_records),
            "sample_examples": len(sample["example_ids"]),
            "eligible_retrieval_examples": retrieval_eligible_count,
            "retrieval_output_examples": retrieval_output_count,
            "failed_retrieval_examples": retrieval_failed_count,
            "unadjudicated_examples": max(
                0, len(sample["example_ids"]) - len(final_records)
            ),
            "labeled_without_positive_relevance_examples": (
                len(final_records) - retrieval_eligible_count
            ),
            "ground_truth_source": "human_adjudication",
        },
        "metrics": metric_results,
        "failure_count": len(failures),
        "limitations": (
            "Only adjudicated, run-matched human labels are scored. No ratings "
            "are inferred from the provisional golden_set.csv."
        ),
    }
    return report, failures


def evaluate_human_comparison(
    comparison: Mapping[str, Any],
    annotations: Iterable[Mapping[str, Any]],
    adjudications: Iterable[Mapping[str, Any]],
    sample: Mapping[str, Any],
) -> dict[str, Any]:
    source_annotations = validate_annotation_records(annotations, sample)
    adjudicated = validate_adjudication_records(
        adjudications, sample, source_annotations
    )
    shared_metadata = comparison.get("run_metadata")
    results = comparison.get("results")
    if not isinstance(shared_metadata, dict) or not isinstance(results, dict):
        raise AnnotationError("comparison artifact must contain run_metadata and results")
    evaluated = {}
    for system in ("majority", "tfidf_logistic_regression", "assistly_runtime"):
        record = results.get(system)
        if not isinstance(record, dict):
            raise AnnotationError(f"comparison is missing per-example rows for {system}")
        rows = record.get("per_example")
        if not isinstance(rows, list):
            raise AnnotationError(f"comparison is missing per-example rows for {system}")
        if system == "assistly_runtime":
            system_metadata = record.get("run_metadata", shared_metadata)
        else:
            system_metadata = {
                **shared_metadata,
                "run_id": f"{shared_metadata.get('run_id')}:{system}",
                "run_mode": "deterministic_baseline",
                "provider": "not_applicable",
                "model": None,
                "prompt_version": "not_applicable",
                "retrieval_version": "not_applicable",
                "retrieval_backend": "not_applicable",
            }
        if not isinstance(system_metadata, dict):
            raise AnnotationError(f"comparison has invalid run metadata for {system}")
        report, failures = evaluate_human_grounded_run(
            system_metadata,
            rows,
            adjudicated,
            sample,
            source_annotations,
        )
        evaluated[system] = {
            "run_class": record["run_class"],
            "run_metadata": report["run_metadata"],
            "metrics": report["metrics"],
            "failure_count": len(failures),
            "failures": failures,
        }
    return {
        "report_version": "assistly-human-system-comparison-v1",
        "ground_truth_source": "human_adjudication",
        "annotation_version": ANNOTATION_VERSION,
        "adjudication_version": ADJUDICATION_VERSION,
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "annotation_records_sha256": _records_hash(source_annotations),
        "adjudication_records_sha256": _records_hash(adjudicated),
        "results": evaluated,
        "limitations": (
            "Systems are scored only where the adjudicated annotations measure "
            "that dimension. The frozen provisional labels and heuristic proxies "
            "are not used as human ground truth."
        ),
    }


def _records_hash(records: list[dict[str, Any]]) -> str:
    return _json_hash(records)


def _provider_failure_metric(
    joined: list[tuple[str, dict[str, Any], dict[str, Any]]],
    run_metadata: Mapping[str, Any],
) -> dict[str, Any] | None:
    observed = [
        result.get("error_category")
        for _, _, result in joined
        if "error_category" in result
    ]
    if observed:
        failures = sum(category is not None for category in observed)
        return {
            "value": failures / len(observed),
            "numerator": failures,
            "denominator": len(observed),
            "status": "measured_per_example",
        }
    value = run_metadata.get("provider_failure_rate")
    if value is None and isinstance(run_metadata.get("metrics"), dict):
        value = run_metadata["metrics"].get("provider_failure_rate")
    return value if isinstance(value, dict) else None


def _json_hash(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _human_failure_category(
    expected_intent: str,
    predicted_intent: Any,
    labels: Mapping[str, Any],
    result: Mapping[str, Any],
    assessment: Mapping[str, Any],
    run_id: Any,
) -> str | None:
    if result.get("error_category") in {"provider_failed", "malformed_model_output"}:
        return (
            "malformed_provider_output"
            if result["error_category"] == "malformed_model_output"
            else "provider_failure"
        )
    if expected_intent == "other_unclear":
        return "ambiguous_query"
    if predicted_intent in {None, "other_unclear"} and expected_intent != "other_unclear":
        return "ambiguous_intent"
    if predicted_intent != expected_intent:
        return "wrong_intent"
    relevant_ids = set(labels["relevant_evidence_ids"])
    retrieved = result.get("evidence_source_ids", [])
    if "evidence_source_ids" in result and relevant_ids:
        retrieved_ids = set(retrieved) if isinstance(retrieved, list) else set()
        if not (relevant_ids & retrieved_ids):
            return "missing_evidence" if not retrieved_ids else "retrieval_mismatch"
    if (
        labels["evidence_sufficiency"] in {"insufficient", "conflicting"}
        and result.get("evidence_status") == "sufficient"
    ):
        return "insufficient_context"
    expected_escalation = labels["expected_escalation"]
    if expected_escalation in {"escalate", "auto_handle"}:
        actual = result.get("decision")
        if expected_escalation == "escalate" and actual != "escalate":
            return "missing_escalation"
        if expected_escalation == "auto_handle" and actual == "escalate":
            return "incorrect_escalation"
    if assessment.get("run_id") == run_id:
        if assessment.get("unsupported_claim_detected") == "yes":
            return "unsupported_claim"
        if assessment.get("quality") == "unacceptable":
            return "poor_answer_quality"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sample_parser = commands.add_parser("create-sample")
    sample_parser.add_argument("--dataset", type=Path, default=Path("data/golden/golden_set.csv"))
    sample_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    sample_parser.add_argument("--size", type=int, default=50)
    sample_parser.add_argument("--output", type=Path, default=DEFAULT_SAMPLE)
    template_parser = commands.add_parser("create-template")
    template_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    template_parser.add_argument("--annotator-id", required=True)
    template_parser.add_argument("--output", type=Path, required=True)
    template_parser.add_argument("--overwrite", action="store_true")
    merge_parser = commands.add_parser("merge")
    merge_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    merge_parser.add_argument("--annotations", type=Path, nargs="+", required=True)
    merge_parser.add_argument("--output", type=Path, required=True)
    merge_parser.add_argument("--overwrite", action="store_true")
    exclusion_parser = commands.add_parser("exclude")
    exclusion_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    exclusion_parser.add_argument("--example-id", required=True)
    exclusion_parser.add_argument("--excluded-by", required=True)
    exclusion_parser.add_argument("--reason", choices=sorted(EXCLUSION_REASONS), required=True)
    exclusion_parser.add_argument("--output", type=Path, required=True)
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    validate_parser.add_argument("--annotations", type=Path, required=True)
    coverage_parser = commands.add_parser("coverage")
    coverage_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    coverage_parser.add_argument("--annotations", type=Path, required=True)
    coverage_parser.add_argument("--adjudications", type=Path)
    coverage_parser.add_argument("--exclusions", type=Path)
    coverage_parser.add_argument("--output", type=Path)
    agreement_parser = commands.add_parser("agreement")
    agreement_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    agreement_parser.add_argument("--annotations", type=Path, required=True)
    agreement_parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/evaluation/human_grounded_runs/agreement_v2.json"),
    )
    adjudicate_parser = commands.add_parser("adjudicate")
    adjudicate_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    adjudicate_parser.add_argument("--annotations", type=Path, required=True)
    adjudicate_parser.add_argument("--example-id", required=True)
    adjudicate_parser.add_argument("--adjudicator-id", required=True)
    adjudicate_parser.add_argument("--final-labels", type=Path, required=True)
    adjudicate_parser.add_argument("--output", type=Path, required=True)
    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    evaluate_parser.add_argument("--summary", type=Path, required=True)
    evaluate_parser.add_argument("--run-rows", type=Path, required=True)
    evaluate_parser.add_argument("--annotations", type=Path, required=True)
    evaluate_parser.add_argument("--adjudications", type=Path, required=True)
    evaluate_parser.add_argument("--output", type=Path, required=True)
    evaluate_parser.add_argument("--failures", type=Path, required=True)
    compare_parser = commands.add_parser("compare-systems")
    compare_parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    compare_parser.add_argument("--comparison", type=Path, required=True)
    compare_parser.add_argument("--annotations", type=Path, required=True)
    compare_parser.add_argument("--adjudications", type=Path, required=True)
    compare_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "create-sample":
        report = create_sample_manifest(args.dataset, args.manifest, args.size)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    else:
        sample = load_sample(args.sample)
        if args.command == "create-template":
            if args.output.exists() and not args.overwrite:
                raise AnnotationError(
                    f"refusing to overwrite existing annotation file: {args.output}; "
                    "pass --overwrite only when replacement is intentional"
                )
            records = create_annotation_template(sample, args.annotator_id)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                "".join(json.dumps(row) + "\n" for row in records),
                encoding="utf-8",
            )
            report = {
                "template_rows": len(records),
                "annotation_status": "not_annotated",
                "annotator_id": args.annotator_id,
                "output": str(args.output),
            }
        elif args.command == "merge":
            if args.output.exists() and not args.overwrite:
                raise AnnotationError(
                    f"refusing to overwrite existing merged annotations: {args.output}; "
                    "pass --overwrite only when replacement is intentional"
                )
            submissions = [
                record
                for annotation_path in args.annotations
                for record in _read_jsonl(annotation_path)
            ]
            records = validate_annotation_records(submissions, sample)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                "".join(json.dumps(row) + "\n" for row in records),
                encoding="utf-8",
            )
            report = {
                "valid": True,
                "submission_files": len(args.annotations),
                "annotation_records": len(records),
                "annotator_count": len({row["annotator_id"] for row in records}),
                "output": str(args.output),
                "human_metrics": "not computed by merge",
            }
        elif args.command == "exclude":
            existing = (
                _read_jsonl(args.output) if args.output.exists() else []
            )
            record = create_exclusion_record(
                sample, args.example_id, args.excluded_by, args.reason
            )
            records = validate_exclusion_records([*existing, record], sample)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                "".join(json.dumps(row) + "\n" for row in records),
                encoding="utf-8",
            )
            report = {
                "status": "excluded",
                "exclusion_records": len(records),
                "example_id": args.example_id,
                "reason": args.reason,
                "output": str(args.output),
            }
        elif args.command == "validate":
            records = validate_annotation_records(
                _read_jsonl(args.annotations), sample
            )
            report = {
                "valid": True,
                "records": len(records),
                "annotated_records": sum(
                    row["annotation_status"] == "annotated" for row in records
                ),
                "annotator_count": len({row["annotator_id"] for row in records}),
                "human_metrics": "not computed by validation",
            }
        elif args.command == "coverage":
            annotations = _read_jsonl(args.annotations)
            adjudications = (
                _read_jsonl(args.adjudications)
                if args.adjudications else []
            )
            exclusions = _read_jsonl(args.exclusions) if args.exclusions else []
            report = summarize_annotation_coverage(
                sample, annotations, adjudications, exclusions
            )
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(
                    json.dumps(report, indent=2) + "\n", encoding="utf-8"
                )
        elif args.command == "agreement":
            report = analyze_annotations(_read_jsonl(args.annotations), sample)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        elif args.command == "adjudicate":
            annotations = validate_annotation_records(
                _read_jsonl(args.annotations), sample
            )
            sources = [
                row["annotator_id"] for row in annotations
                if row["example_id"] == args.example_id
                and row["annotation_status"] == "annotated"
            ]
            record = create_adjudication_record(
                sample,
                args.example_id,
                args.adjudicator_id,
                sources,
                json.loads(args.final_labels.read_text(encoding="utf-8")),
                annotations,
            )
            existing = (
                validate_adjudication_records(
                    _read_jsonl(args.output), sample, annotations
                )
                if args.output.exists() else []
            )
            if any(row["example_id"] == args.example_id for row in existing):
                raise AnnotationError(
                    f"an adjudication already exists for {args.example_id!r}"
                )
            existing.append(record)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                "".join(json.dumps(row) + "\n" for row in existing),
                encoding="utf-8",
            )
            report = {
                "adjudicated": True,
                "example_id": args.example_id,
                "adjudicator_id": args.adjudicator_id,
                "source_annotator_count": len(sources),
                "output": str(args.output),
            }
        elif args.command == "evaluate":
            annotations = validate_annotation_records(
                _read_jsonl(args.annotations), sample
            )
            adjudications = validate_adjudication_records(
                _read_jsonl(args.adjudications), sample, annotations
            )
            summary = json.loads(args.summary.read_text(encoding="utf-8"))
            rows = _read_jsonl(args.run_rows)
            report, failures = evaluate_human_grounded_run(
                summary.get("run_metadata", {}),
                rows,
                adjudications,
                sample,
                annotations,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.failures.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            args.failures.write_text(
                json.dumps(failures, indent=2) + "\n", encoding="utf-8"
            )
        else:
            annotations = _read_jsonl(args.annotations)
            adjudications = _read_jsonl(args.adjudications)
            comparison = json.loads(args.comparison.read_text(encoding="utf-8"))
            report = evaluate_human_comparison(
                comparison, annotations, adjudications, sample
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

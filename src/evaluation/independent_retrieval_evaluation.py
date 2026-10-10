"""Evaluate ranked retrieval outputs against independent adjudicated evidence labels."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from src.evaluation.dataset_manifest import DEFAULT_MANIFEST, sha256_file
from src.evaluation.human_grounded_evaluation import (
    AnnotationError,
    _read_jsonl,
    load_sample,
    validate_adjudication_records,
    validate_annotation_records,
    validate_exclusion_records,
)

EVALUATOR_VERSION = "independent-retrieval-evaluator-v1"


def _records_hash(records: list[dict[str, Any]]) -> str:
    serialized = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _retrieval_metrics(
    labels: Mapping[str, int],
    retrieved_ids: list[str],
    failed: bool,
) -> dict[str, Any]:
    relevant = {evidence_id for evidence_id, grade in labels.items() if grade > 0}

    def recall(k: int) -> float:
        return len(relevant & set(retrieved_ids[:k])) / len(relevant)

    def ndcg(k: int) -> float:
        gains = [
            (2 ** labels.get(evidence_id, 0) - 1) / math.log2(rank + 1)
            for rank, evidence_id in enumerate(retrieved_ids[:k], 1)
        ]
        ideal_grades = sorted(labels.values(), reverse=True)[:k]
        ideal = sum(
            (2 ** grade - 1) / math.log2(rank + 1)
            for rank, grade in enumerate(ideal_grades, 1)
        )
        return sum(gains) / ideal if ideal else 0.0

    first_rank = next(
        (
            rank for rank, evidence_id in enumerate(retrieved_ids, 1)
            if evidence_id in relevant
        ),
        None,
    )
    return {
        "recall_at_k": {str(k): recall(k) for k in (1, 3, 5)},
        "mrr": 1 / first_rank if first_rank else 0.0,
        "ndcg_at_k": {str(k): ndcg(k) for k in (1, 3, 5)},
        "failed": failed,
        "first_relevant_rank": first_rank,
    }


def evaluate_independent_retrieval(
    sample: Mapping[str, Any],
    annotations: Iterable[Mapping[str, Any]],
    adjudications: Iterable[Mapping[str, Any]],
    runs: Mapping[str, Iterable[Mapping[str, Any]]],
    exclusions: Iterable[Mapping[str, Any]] = (),
    run_metadata: Mapping[str, Mapping[str, Any]] | None = None,
    dataset_manifest_sha256: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Score each system on the same adjudicated, positively judged query set.

    Recall@K is macro query-level recall over judged-positive evidence IDs.
    Missing/failed system outputs remain in the denominator with zero scores.
    Queries without any judged-positive evidence and explicitly excluded examples
    are excluded from the metric denominator and reported separately.
    """
    annotation_records = validate_annotation_records(annotations, sample)
    adjudication_records = validate_adjudication_records(
        adjudications, sample, annotation_records
    )
    exclusion_records = validate_exclusion_records(exclusions, sample)
    excluded_ids = {row["example_id"] for row in exclusion_records}

    truth_by_id: dict[str, dict[str, Any]] = {}
    for record in adjudication_records:
        if record["adjudication_status"] != "adjudicated":
            continue
        example_id = record["example_id"]
        if example_id in excluded_ids:
            raise AnnotationError(
                f"example {example_id!r} cannot be adjudicated and excluded"
            )
        labels = record["final_labels"]
        relevance = {
            item["evidence_id"]: item["score"]
            for item in labels["evidence_relevance"]
        }
        truth_by_id[example_id] = {
            "labels": relevance,
            "expected_intent": labels["expected_intent"],
            "evidence_sufficiency": labels["evidence_sufficiency"],
        }
    relevant_truth = {
        example_id: value
        for example_id, value in truth_by_id.items()
        if any(grade > 0 for grade in value["labels"].values())
    }
    sample_ids = set(sample["example_ids"])
    failures: list[dict[str, Any]] = []
    systems: dict[str, Any] = {}
    metadata_by_system = run_metadata or {}

    if not runs:
        raise AnnotationError("at least one ranked retrieval run is required")
    for system_name, source_rows in sorted(runs.items()):
        if not isinstance(system_name, str) or not system_name.strip():
            raise AnnotationError("system names must be non-empty strings")
        rows_by_id: dict[str, dict[str, Any]] = {}
        for row in source_rows:
            example_id = row.get("example_id")
            if not isinstance(example_id, str) or example_id not in sample_ids:
                raise AnnotationError(
                    f"{system_name}: run rows require a sample example_id"
                )
            if example_id in rows_by_id:
                raise AnnotationError(
                    f"{system_name}: duplicate result for {example_id!r}"
                )
            rows_by_id[example_id] = dict(row)

        per_example: dict[str, dict[str, Any]] = {}
        system_failures: list[dict[str, Any]] = []
        for example_id, truth in sorted(relevant_truth.items()):
            row = rows_by_id.get(example_id)
            retrieved_value = row.get("evidence_source_ids") if row else None
            retrieved_ids: list[str] = []
            failed = not isinstance(retrieved_value, list)
            if isinstance(retrieved_value, list):
                parsed_ids: list[str] = []
                for item in retrieved_value:
                    if not isinstance(item, str) or not item:
                        failed = True
                        break
                    parsed_ids.append(item)
                if not failed:
                    retrieved_ids = parsed_ids
            if len(retrieved_ids) != len(set(retrieved_ids)):
                raise AnnotationError(
                    f"{system_name}: duplicate retrieved evidence ID for {example_id!r}"
                )
            metrics = _retrieval_metrics(
                truth["labels"], retrieved_ids, failed
            )
            per_example[example_id] = metrics
            top5 = retrieved_ids[:5]
            relevant_ids = {
                evidence_id
                for evidence_id, grade in truth["labels"].items()
                if grade > 0
            }
            if failed:
                category = "missing_retrieval_output"
            elif (
                truth["expected_intent"] == "other_unclear"
                or truth["evidence_sufficiency"] == "uncertain"
            ):
                category = "ambiguous_query"
            elif (
                truth["evidence_sufficiency"] in {"insufficient", "conflicting"}
                and row is not None
                and row.get("evidence_status") == "sufficient"
            ):
                category = "insufficient_context"
            elif not (relevant_ids & set(top5)):
                category = "missing_evidence" if not top5 else "ranking_mismatch"
            else:
                category = None
            if category:
                failure = {
                    "example_id": example_id,
                    "system": system_name,
                    "failure_category": category,
                    "first_relevant_rank": metrics["first_relevant_rank"],
                    "retrieved_evidence_ids_at_5": top5,
                }
                system_failures.append(failure)
                failures.append(failure)

        denominator = len(relevant_truth)
        systems[system_name] = {
            "run_metadata": dict(metadata_by_system.get(system_name, {})),
            "metrics": {
                "recall_at_k": {
                    str(k): {
                        "value": (
                            mean(row["recall_at_k"][str(k)] for row in per_example.values())
                            if denominator else None
                        ),
                        "numerator": (
                            sum(row["recall_at_k"][str(k)] for row in per_example.values())
                            if denominator else None
                        ),
                        "denominator": denominator,
                        "status": (
                            "measured_independent_adjudicated_relevance"
                            if denominator else "not_measured_no_positive_relevance_labels"
                        ),
                    }
                    for k in (1, 3, 5)
                },
                "mrr": {
                    "value": (
                        mean(row["mrr"] for row in per_example.values())
                        if denominator else None
                    ),
                    "denominator": denominator,
                    "status": (
                        "measured_independent_adjudicated_relevance"
                        if denominator else "not_measured_no_positive_relevance_labels"
                    ),
                },
                "ndcg_at_k": {
                    str(k): {
                        "value": (
                            mean(row["ndcg_at_k"][str(k)] for row in per_example.values())
                            if denominator else None
                        ),
                        "denominator": denominator,
                        "status": (
                            "measured_independent_graded_relevance"
                            if denominator else "not_measured_no_graded_relevance_labels"
                        ),
                    }
                    for k in (1, 3, 5)
                },
            },
            "eligible_examples": denominator,
            "evaluated_examples": sum(not row["failed"] for row in per_example.values()),
            "failed_examples": sum(row["failed"] for row in per_example.values()),
            "failure_categories": {
                category: sum(
                    row["failure_category"] == category for row in system_failures
                )
                for category in sorted({
                    row["failure_category"] for row in system_failures
                })
            },
        }

    report = {
        "evaluation": "independent_human_retrieval_evaluation",
        "evaluator_version": EVALUATOR_VERSION,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "dataset_provenance_status": sample["dataset_provenance_status"],
        "annotation_dataset_version": sample["sample_version"],
        "annotation_sample_sha256": _records_hash([dict(sample)]),
        "annotation_records_sha256": _records_hash(annotation_records),
        "adjudication_records_sha256": _records_hash(adjudication_records),
        "exclusion_records_sha256": _records_hash(exclusion_records),
        "evaluation_mode": "human_grounded",
        "relevance_source": "independent_human_adjudication",
        "denominator_definition": (
            "Adjudicated examples with at least one evidence_relevance grade > 0; "
            "each query contributes equally. Missing retrieval outputs score zero."
        ),
        "empty_relevance_behavior": (
            "Adjudicated examples with no positive judged evidence are excluded "
            "from retrieval metrics and counted separately."
        ),
        "sample_size": len(sample["example_ids"]),
        "adjudicated_examples": len(truth_by_id),
        "eligible_examples": len(relevant_truth),
        "labeled_without_positive_relevance": len(truth_by_id) - len(relevant_truth),
        "excluded_examples": len(excluded_ids),
        "unadjudicated_not_excluded_examples": (
            len(sample_ids - set(truth_by_id) - excluded_ids)
        ),
        "systems": systems,
        "limitations": [
            "Metrics measure recall only against explicitly judged evidence IDs; unjudged corpus items are not treated as irrelevant.",
            "Results are human-grounded only for adjudicated labels and remain provisional with the source dataset provenance.",
            "Historical taxonomy intent-match metrics are separate heuristic proxies and are not included here.",
        ],
    }
    return report, failures


def _named_run(value: str) -> tuple[str, Path]:
    name, separator, path = value.partition("=")
    if not separator or not name.strip() or not path.strip():
        raise argparse.ArgumentTypeError("run must use SYSTEM=PATH")
    return name.strip(), Path(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=Path(
        "reports/evaluation/human_annotation_sample_v1.json"
    ))
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--adjudications", type=Path, required=True)
    parser.add_argument("--exclusions", type=Path)
    parser.add_argument(
        "--run",
        type=_named_run,
        action="append",
        required=True,
        help="Ranked system output as SYSTEM=JSONL_PATH; may be repeated.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--failures", type=Path, required=True)
    args = parser.parse_args()
    sample = load_sample(args.sample)
    annotations = _read_jsonl(args.annotations)
    adjudications = _read_jsonl(args.adjudications)
    exclusions = _read_jsonl(args.exclusions) if args.exclusions else []
    names = [name for name, _ in args.run]
    if len(names) != len(set(names)):
        parser.error("system names in --run must be unique")
    runs = {name: _read_jsonl(path) for name, path in args.run}
    report, failures = evaluate_independent_retrieval(
        sample,
        annotations,
        adjudications,
        runs,
        exclusions,
        dataset_manifest_sha256=sha256_file(DEFAULT_MANIFEST),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.failures.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.failures.write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "evaluation": report["evaluation"],
        "eligible_examples": report["eligible_examples"],
        "excluded_examples": report["excluded_examples"],
        "systems": {
            name: result["metrics"] for name, result in report["systems"].items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Export, validate, adjudicate, and score independent retrieval judgments."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from src.evaluation.dataset_manifest import (
    DEFAULT_MANIFEST,
    FROZEN_DATASET,
    sha256_file,
    verify_dataset,
)
from src.evaluation.human_grounded_evaluation import AnnotationError, load_sample

SCHEMA_VERSION = "assistly-retrieval-relevance-v1"
SAMPLE_PATH = Path("reports/evaluation/human_annotation_sample_v1.json")
RETRIEVAL_PATH = Path("reports/evaluation/golden_reply_generations.jsonl")
EXPORT_DIR = Path("reports/evaluation/human_annotation_exports")
GRADES = {0, 1, 2}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
REASONS = {
    "source_unavailable",
    "source_unreadable",
    "privacy_review",
    "duplicate_example",
    "other",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AnnotationError(f"{path}:{line_number} is not valid JSON") from exc
            if not isinstance(record, dict):
                raise AnnotationError(f"{path}:{line_number} must contain an object")
            records.append(record)
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]], *, refuse_existing: bool = False) -> None:
    if refuse_existing and path.exists():
        raise AnnotationError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _identity(sample: dict[str, Any], retrieval_path: Path) -> dict[str, str]:
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_version": sample["dataset_version"],
        "dataset_sha256": sample["dataset_sha256"],
        "sample_sha256": hashlib.sha256(
            json.dumps(sample, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "retrieval_artifact_sha256": sha256_file(retrieval_path),
    }


def _candidate_pseudonym(source_id: str) -> str:
    digest = hashlib.sha256(
        f"{SCHEMA_VERSION}:candidate:{source_id}".encode()
    ).hexdigest()
    return f"candidate-{digest}"


def expected_pairs(
    sample_path: Path = SAMPLE_PATH,
    retrieval_path: Path = RETRIEVAL_PATH,
    dataset_path: Path = FROZEN_DATASET,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    sample = load_sample(sample_path)
    _, source_rows = verify_dataset(dataset_path, manifest_path)
    query_by_id = {row["example_id"]: row["customer_text"] for row in source_rows}
    missing_query = set(sample["example_ids"]) - set(query_by_id)
    if missing_query:
        raise AnnotationError(f"sample IDs missing from frozen dataset: {sorted(missing_query)}")

    retrieval_rows = _read_jsonl(retrieval_path)
    results_by_id: dict[str, dict[str, Any]] = {}
    for row in retrieval_rows:
        example_id = row.get("example_id")
        if example_id in sample["example_ids"]:
            if example_id in results_by_id:
                raise AnnotationError(f"duplicate retrieval output for {example_id!r}")
            results_by_id[example_id] = row
    missing_results = set(sample["example_ids"]) - set(results_by_id)
    if missing_results:
        raise AnnotationError(f"sample IDs missing retrieval output: {sorted(missing_results)}")

    pairs = []
    for example_id in sample["example_ids"]:
        candidates = results_by_id[example_id].get("retrieved_examples")
        if not isinstance(candidates, list) or len(candidates) != 5:
            raise AnnotationError(f"{example_id}: expected exactly five ranked candidates")
        seen_candidate_ids: set[str] = set()
        for rank, candidate in enumerate(candidates, 1):
            if not isinstance(candidate, dict):
                raise AnnotationError(f"{example_id}: candidate at rank {rank} must be an object")
            candidate_id = candidate.get("response_tweet_id")
            candidate_text = candidate.get("amazonhelp_response")
            if not isinstance(candidate_id, str) or not candidate_id.strip():
                raise AnnotationError(f"{example_id}: candidate at rank {rank} has no stable ID")
            if candidate_id in seen_candidate_ids:
                raise AnnotationError(f"{example_id}: duplicate candidate ID {candidate_id!r}")
            if not isinstance(candidate_text, str) or not candidate_text.strip():
                raise AnnotationError(f"{example_id}: candidate {candidate_id!r} has no text")
            seen_candidate_ids.add(candidate_id)
            pairs.append({
                "query_id": example_id,
                "candidate_id": _candidate_pseudonym(candidate_id),
                "rank": rank,
                "query_text": query_by_id[example_id],
                "candidate_text": candidate_text,
            })
    return sample, pairs


def export_templates(
    output_dir: Path = EXPORT_DIR,
    sample_path: Path = SAMPLE_PATH,
    retrieval_path: Path = RETRIEVAL_PATH,
) -> list[Path]:
    sample, pairs = expected_pairs(sample_path, retrieval_path)
    identity = _identity(sample, retrieval_path)
    outputs = []
    output_paths = [
        output_dir / f"retrieval-relevance-{reviewer_id}.jsonl"
        for reviewer_id in ("reviewer-01", "reviewer-02")
    ]
    existing = [path for path in output_paths if path.exists()]
    if existing:
        raise AnnotationError(
            f"refusing to overwrite existing file(s): {', '.join(map(str, existing))}"
        )
    for reviewer_id, output_path in zip(
        ("reviewer-01", "reviewer-02"), output_paths, strict=True
    ):
        records = [
            {
                **identity,
                **pair,
                "reviewer_id": reviewer_id,
                "relevance_grade": None,
                "rationale": "",
            }
            for pair in pairs
        ]
        _write_jsonl(output_path, records, refuse_existing=True)
        outputs.append(output_path)
    return outputs


def validate_exclusions(
    exclusions: list[dict[str, Any]],
    sample: dict[str, Any],
    *,
    require_complete: bool = False,
) -> dict[str, dict[str, Any]]:
    sample_ids = set(sample["example_ids"])
    by_id = {}
    for record in exclusions:
        query_id = record.get("example_id")
        if query_id not in sample_ids:
            raise AnnotationError(f"exclusion has unknown query ID {query_id!r}")
        if query_id in by_id:
            raise AnnotationError(f"duplicate exclusion for {query_id!r}")
        if (
            record.get("exclusion_version") != "assistly-human-exclusion-v1"
            or record.get("dataset_version") != sample["dataset_version"]
            or record.get("dataset_sha256") != sample["dataset_sha256"]
            or record.get("status") != "excluded"
        ):
            raise AnnotationError(f"{query_id}: missing or mismatched exclusion provenance")
        excluded_by = record.get("excluded_by")
        if not isinstance(excluded_by, str) or not IDENTIFIER.fullmatch(excluded_by):
            raise AnnotationError(f"{query_id}: exclusion requires a pseudonymous excluded_by")
        if record.get("reason") not in REASONS:
            raise AnnotationError(f"{query_id}: invalid exclusion reason")
        by_id[query_id] = record
    if require_complete and len(by_id) != len(sample_ids):
        raise AnnotationError("every query must be judged or explicitly excluded")
    return by_id


def validate_submission(
    records: list[dict[str, Any]],
    sample: dict[str, Any],
    pairs: list[dict[str, Any]],
    identity: dict[str, str],
    exclusions: list[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    excluded = validate_exclusions(list(exclusions), sample)
    expected = {(pair["query_id"], pair["candidate_id"]): pair for pair in pairs}
    observed: dict[tuple[str, str], dict[str, Any]] = {}
    reviewer_ids = set()
    for record in records:
        query_id, candidate_id = record.get("query_id"), record.get("candidate_id")
        key = (query_id, candidate_id)
        if query_id not in sample["example_ids"]:
            raise AnnotationError(f"unknown query ID {query_id!r}")
        if key not in expected:
            raise AnnotationError(f"unknown query/candidate pair {key!r}")
        if key in observed:
            raise AnnotationError(f"duplicate judgment for {key!r}")
        if query_id in excluded:
            raise AnnotationError(f"excluded query {query_id!r} also has judgments")
        if any(record.get(field) != value for field, value in identity.items()):
            raise AnnotationError(f"{key!r}: missing or mismatched provenance")
        reviewer_id = record.get("reviewer_id")
        if not isinstance(reviewer_id, str) or not IDENTIFIER.fullmatch(reviewer_id):
            raise AnnotationError(f"{key!r}: reviewer_id must be pseudonymous")
        reviewer_ids.add(reviewer_id)
        if record.get("rank") != expected[key]["rank"]:
            raise AnnotationError(f"{key!r}: candidate rank does not match the retrieval run")
        grade = record.get("relevance_grade")
        if grade is not None and (
            isinstance(grade, bool) or not isinstance(grade, int) or grade not in GRADES
        ):
            raise AnnotationError(f"{key!r}: relevance_grade must be blank, 0, 1, or 2")
        if grade is None and (record.get("annotation_status") == "annotated"):
            raise AnnotationError(f"{key!r}: annotated record cannot have a blank grade")
        if record.get("query_text") != expected[key]["query_text"]:
            raise AnnotationError(f"{key!r}: query evidence does not match the benchmark")
        if record.get("candidate_text") != expected[key]["candidate_text"]:
            raise AnnotationError(f"{key!r}: candidate evidence does not match the retrieval run")
        observed[key] = dict(record)
    if len(reviewer_ids) > 1:
        raise AnnotationError("a reviewer submission must contain exactly one reviewer_id")
    required = {key for key in expected if key[0] not in excluded}
    missing = required - set(observed)
    if missing:
        raise AnnotationError(f"incomplete submission: {len(missing)} candidate judgments missing")
    unjudged = [key for key, record in observed.items() if record.get("relevance_grade") is None]
    if unjudged:
        raise AnnotationError(f"incomplete submission: {len(unjudged)} blank relevance judgments")
    return [observed[key] for key in sorted(observed)]


def validate_adjudications(
    reviewer_a: list[dict[str, Any]],
    reviewer_b: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    a = {(r["query_id"], r["candidate_id"]): r for r in reviewer_a}
    b = {(r["query_id"], r["candidate_id"]): r for r in reviewer_b}
    reviewer_ids_a = {r["reviewer_id"] for r in reviewer_a}
    reviewer_ids_b = {r["reviewer_id"] for r in reviewer_b}
    if len(reviewer_ids_a) != 1 or len(reviewer_ids_b) != 1:
        raise AnnotationError("each reviewer submission must have one reviewer identity")
    if reviewer_ids_a == reviewer_ids_b:
        raise AnnotationError("independent reviewer submissions require distinct reviewer IDs")
    if set(a) != set(b):
        raise AnnotationError("reviewer submissions must cover the same query/candidate pairs")
    decisions_by_pair = {}
    for decision in decisions:
        key = (decision.get("query_id"), decision.get("candidate_id"))
        if key not in a:
            raise AnnotationError(f"adjudication has unknown query/candidate pair {key!r}")
        if key in decisions_by_pair:
            raise AnnotationError(f"duplicate adjudication for {key!r}")
        grade = decision.get("final_grade")
        if isinstance(grade, bool) or not isinstance(grade, int) or grade not in GRADES:
            raise AnnotationError(f"{key!r}: final_grade must be 0, 1, or 2")
        decisions_by_pair[key] = decision
    expected_decisions = {
        key for key in a
        if a[key]["relevance_grade"] != b[key]["relevance_grade"]
    }
    if set(decisions_by_pair) != expected_decisions:
        raise AnnotationError(
            "adjudication decisions must resolve every disagreement and no agreements"
        )
    final = {}
    for key, first in a.items():
        second = b[key]
        decision = decisions_by_pair.get(key)
        grade = (
            decision["final_grade"]
            if decision
            else first["relevance_grade"]
        )
        if decision:
            adjudicator_id = decision.get("adjudicator_id")
            if not isinstance(adjudicator_id, str) or not IDENTIFIER.fullmatch(adjudicator_id):
                raise AnnotationError(f"{key!r}: adjudicator_id must be pseudonymous")
        final[key] = {
            **first,
            "relevance_grade": grade,
            "adjudication_status": "adjudicated",
            "source_reviewer_ids": [first["reviewer_id"], second["reviewer_id"]],
            "adjudicator_id": (
                decision["adjudicator_id"] if decision else "agreement"
            ),
            "adjudication_rationale": decision.get("rationale", "") if decision else "",
        }
    return final


def evaluate(
    records: list[dict[str, Any]],
    sample: dict[str, Any],
    pairs: list[dict[str, Any]],
    identity: dict[str, str],
    exclusions: list[dict[str, Any]] = (),
) -> dict[str, Any]:
    excluded = validate_exclusions(list(exclusions), sample)
    expected = {(pair["query_id"], pair["candidate_id"]): pair for pair in pairs}
    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen = set()
    for record in records:
        key = (record.get("query_id"), record.get("candidate_id"))
        if key not in expected:
            raise AnnotationError(f"unknown query/candidate pair {key!r}")
        if key in seen:
            raise AnnotationError(f"duplicate final judgment for {key!r}")
        if key[0] in excluded:
            raise AnnotationError(f"excluded query {key[0]!r} has an adjudicated judgment")
        if any(record.get(field) != value for field, value in identity.items()):
            raise AnnotationError(f"{key!r}: missing or mismatched provenance")
        if record.get("adjudication_status") != "adjudicated":
            raise AnnotationError(f"{key!r}: final labels must be adjudicated")
        grade = record.get("relevance_grade")
        if isinstance(grade, bool) or not isinstance(grade, int) or grade not in GRADES:
            raise AnnotationError(f"{key!r}: final grade must be 0, 1, or 2")
        if record.get("rank") != expected[key]["rank"]:
            raise AnnotationError(f"{key!r}: candidate rank does not match the retrieval run")
        if record.get("query_text") != expected[key]["query_text"] or record.get(
            "candidate_text"
        ) != expected[key]["candidate_text"]:
            raise AnnotationError(f"{key!r}: evidence differs from the retrieval run")
        source_reviewers = record.get("source_reviewer_ids")
        if (
            not isinstance(source_reviewers, list)
            or len(source_reviewers) != 2
            or any(not isinstance(item, str) or not IDENTIFIER.fullmatch(item) for item in source_reviewers)
            or source_reviewers[0] == source_reviewers[1]
        ):
            raise AnnotationError(f"{key!r}: final record requires two distinct pseudonymous reviewers")
        adjudicator_id = record.get("adjudicator_id")
        if adjudicator_id != "agreement" and (
            not isinstance(adjudicator_id, str) or not IDENTIFIER.fullmatch(adjudicator_id)
        ):
            raise AnnotationError(f"{key!r}: adjudicator_id must be pseudonymous")
        seen.add(key)
        by_query[key[0]].append(record)
    required = {key for key in expected if key[0] not in excluded}
    if seen != required:
        raise AnnotationError(
            f"incomplete adjudication: {len(required - seen)} candidate judgments missing"
        )

    query_metrics = {}
    for query_id in sample["example_ids"]:
        if query_id in excluded:
            continue
        judged = sorted(by_query[query_id], key=lambda row: row["rank"])
        relevant = [row for row in judged if row["relevance_grade"] > 0]
        ranks = {row["candidate_id"]: row["rank"] for row in relevant}
        per_query = {}
        for k in (1, 3, 5):
            found = [row for row in relevant if row["rank"] <= k]
            recall = len(found) / len(relevant) if relevant else None
            dcg = sum(
                (2 ** row["relevance_grade"] - 1)
                / math.log2(row["rank"] + 1)
                for row in judged if row["rank"] <= k
            )
            ideal_grades = sorted(
                (row["relevance_grade"] for row in judged), reverse=True
            )[:k]
            ideal = sum(
                (2 ** grade - 1) / math.log2(rank + 1)
                for rank, grade in enumerate(ideal_grades, 1)
            )
            per_query[str(k)] = {
                "recall": recall,
                "ndcg": dcg / ideal if ideal else 0.0,
            }
        first_rank = min(ranks.values()) if ranks else None
        query_metrics[query_id] = {
            "recall_at_k": {k: values["recall"] for k, values in per_query.items()},
            "mrr": 1 / first_rank if first_rank else 0.0,
            "ndcg_at_k": {k: values["ndcg"] for k, values in per_query.items()},
            "positive_relevant_candidates": len(relevant),
        }
    positive_queries = {
        query_id: value for query_id, value in query_metrics.items()
        if value["positive_relevant_candidates"] > 0
    }
    result = {
        "evaluation": "independent_human_retrieval_relevance",
        "schema_version": SCHEMA_VERSION,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        **identity,
        "sample_size": len(sample["example_ids"]),
        "queries_judged": len(query_metrics),
        "queries_excluded": len(excluded),
        "queries_without_positive_candidates": len(query_metrics) - len(positive_queries),
        "candidate_pairs_judged": len(seen),
        "candidate_pairs_expected": len(expected),
        "coverage": len(seen) / len(expected) if expected else 0.0,
        "eligible_positive_queries": len(positive_queries),
        "metric_averaging": "macro over queries with at least one grade > 0",
        "relevance_definition": "grade 1 or 2 is relevant for Recall@K and MRR",
        "ndcg_gain": "2^grade - 1; grades 0, 1, 2",
        "metrics": {
            "recall_at_k": {
                str(k): (
                    mean(value["recall_at_k"][str(k)] for value in positive_queries.values())
                    if positive_queries else None
                ) for k in (1, 3, 5)
            },
            "mrr": (
                mean(value["mrr"] for value in positive_queries.values())
                if positive_queries else None
            ),
            "ndcg_at_k": {
                str(k): (
                    mean(value["ndcg_at_k"][str(k)] for value in positive_queries.values())
                    if positive_queries else None
                ) for k in (1, 3, 5)
            },
        },
        "limitations": [
            "Relevance is judged only among the five retrieved candidates per query; unjudged corpus items are unknown.",
            "Recall denominators include positive judgments only among this top-five candidate pool.",
            "The frozen dataset label provenance remains unresolved and is not used as relevance ground truth.",
        ],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--output-dir", type=Path, default=EXPORT_DIR)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--submission", type=Path, required=True)
    validate_parser.add_argument("--exclusions", type=Path)
    adjudicate_parser = subparsers.add_parser("adjudicate")
    adjudicate_parser.add_argument("--reviewer-a", type=Path, required=True)
    adjudicate_parser.add_argument("--reviewer-b", type=Path, required=True)
    adjudicate_parser.add_argument("--decisions", type=Path)
    adjudicate_parser.add_argument("--exclusions", type=Path)
    adjudicate_parser.add_argument("--output", type=Path, required=True)
    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--adjudicated", type=Path, required=True)
    evaluate_parser.add_argument("--exclusions", type=Path)
    evaluate_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "export":
        print(json.dumps({"templates": [str(path) for path in export_templates(args.output_dir)]}, indent=2))
        return 0

    sample, pairs = expected_pairs()
    identity = _identity(sample, RETRIEVAL_PATH)
    exclusions = _read_jsonl(args.exclusions) if getattr(args, "exclusions", None) else []
    if args.command == "validate":
        validated = validate_submission(
            _read_jsonl(args.submission), sample, pairs, identity, exclusions
        )
        print(json.dumps({"valid": True, "reviewer_id": validated[0]["reviewer_id"], "candidate_pairs": len(validated)}))
        return 0
    if args.command == "adjudicate":
        first = validate_submission(
            _read_jsonl(args.reviewer_a), sample, pairs, identity, exclusions
        )
        second = validate_submission(
            _read_jsonl(args.reviewer_b), sample, pairs, identity, exclusions
        )
        decisions = _read_jsonl(args.decisions) if args.decisions else []
        final = validate_adjudications(first, second, decisions)
        _write_jsonl(args.output, list(final.values()), refuse_existing=True)
        print(json.dumps({"adjudicated_candidate_pairs": len(final), "output": str(args.output)}))
        return 0
    result = evaluate(_read_jsonl(args.adjudicated), sample, pairs, identity, exclusions)
    _write_jsonl(args.output, [result], refuse_existing=True)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

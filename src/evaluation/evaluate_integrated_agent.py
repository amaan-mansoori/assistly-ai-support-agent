"""Evaluate the persisted Phase 2 runtime agent separately from historical benchmarks."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Protocol
from uuid import uuid4

from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from src.agent.config import AgentConfig
from src.agent.escalation import SENSITIVE_INTENTS
from src.agent.models import AgentRequest, AgentResponse
from src.agent.orchestrator import SupportAgent
from src.agent.reply_generator import (
    DeterministicMockProvider,
    configured_llm_call,
)
from src.db.database import make_engine, make_session_factory
from src.evaluation.dataset_manifest import DEFAULT_MANIFEST, sha256_file, verify_dataset
from src.intents.final_taxonomy_audit import classify_intent
from src.platform.config import PlatformSettings
from src.retrieval.factory import build_retriever
from src.retrieval.historical_retriever import GOLDEN

PROVENANCE_NOTE = (
    "Provisional: the 220-row labeled evaluation set has unresolved human-label provenance."
)
EVALUATOR_VERSION = "integrated-evaluator-v4"
PROMPT_VERSION = "assistly-support-prompt-v3"
RETRIEVAL_VERSION = "assistly-retrieval-v2"
EVIDENCE_POLICY_VERSION = "assistly-evidence-policy-v2"
EVALUATION_SCHEMA_VERSION = "assistly-evaluation-schema-v2"
FAILURE_CATEGORIES = frozenset({
    "ambiguous_intent",
    "wrong_intent",
    "retrieval_mismatch",
    "insufficient_evidence",
    "conflicting_evidence",
    "unsupported_claim",
    "unsafe_response",
    "escalation_error",
    "context_confusion",
    "provider_failure",
    "malformed_provider_output",
    "prompt_injection",
})


class Agent(Protocol):
    def handle(self, request: AgentRequest, /) -> AgentResponse: ...


def load_examples(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"example_id", "customer_text", "human_intent"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Evaluation CSV must contain columns: {sorted(required)}")
        examples = [
            row
            for row in reader
            if row.get("customer_text", "").strip()
            and row.get("human_intent", "").strip()
        ]
    return examples[:limit] if limit is not None else examples


def _latency_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean_ms": None, "median_ms": None, "p95_ms": None}
    ordered = sorted(values)
    p95_index = max(0, int(0.95 * len(ordered) + 0.999999) - 1)
    return {
        "count": len(values),
        "mean_ms": mean(values),
        "median_ms": median(values),
        "p95_ms": ordered[p95_index],
    }


def _failure_category(
    expected: str,
    predicted: str | None,
    evidence_status: str,
    decision: str,
    error: str | None,
    grounding_supported: bool | None,
    has_context: bool,
    unsafe_response: bool = False,
) -> str | None:
    if error == "provider_failed":
        return "provider_failure"
    if error == "malformed_model_output":
        return "malformed_provider_output"
    if predicted is None or predicted == "other_unclear":
        return "ambiguous_intent"
    if predicted != expected:
        return "context_confusion" if has_context else "wrong_intent"
    if evidence_status == "conflicting":
        return "conflicting_evidence"
    if evidence_status == "none" or evidence_status == "weak":
        return "insufficient_evidence"
    if unsafe_response:
        return "unsafe_response"
    if grounding_supported is False:
        return "unsupported_claim"
    if decision == "auto_handle" and expected in SENSITIVE_INTENTS:
        return "escalation_error"
    return None


def failure_analysis_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the minimal failure metadata safe for persisted diagnostics."""
    allowed = (
        "example_id",
        "expected_intent",
        "predicted_intent",
        "evidence_source_ids",
        "evidence_status",
        "decision",
        "grounding_supported",
        "failure_category",
    )
    failures = []
    for row in rows:
        category = row.get("failure_category")
        if category is None:
            continue
        if category not in FAILURE_CATEGORIES:
            raise ValueError(f"unsupported failure category: {category!r}")
        failures.append({
            **{key: row[key] for key in allowed},
            "evaluator_version": EVALUATOR_VERSION,
        })
    return failures


def evaluate_examples(
    agent: Agent,
    examples: list[dict[str, str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not examples:
        raise ValueError("No labeled evaluation examples were found.")
    rows: list[dict[str, Any]] = []
    latencies: list[float] = []
    intent_targets: list[str] = []
    intent_predictions: list[str] = []
    retrieval_hits = {1: [], 3: [], 5: []}
    reciprocal_ranks: list[float] = []
    stage_latencies: dict[str, list[float]] = {}
    grounded: list[bool] = []
    unsupported_claim_count = 0
    auto_count = 0
    unsafe_auto_count = 0
    sensitive_case_count = 0
    sensitive_case_escalations = 0
    error_count = 0
    provider_failure_count = 0
    provider_error_categories: dict[str, int] = {}
    retry_values: list[int] = []
    draft_count = 0
    unsupported_draft_count = 0
    grounding_observed_count = 0
    evidence_assessment_count = 0
    evidence_conflict_count = 0
    intent_match_values: list[bool] = []
    resolution_match_values: list[bool] = []
    retrieval_backend_counts: dict[str, int] = {}

    for example in examples:
        target = example["human_intent"]
        context = example.get("conversation_context", "").strip()
        response = agent.handle(
            AgentRequest(
                message=example["customer_text"],
                conversation_history=(context,) if context else (),
            )
        )
        intent_targets.append(target)
        intent_predictions.append(response.intent or "__missing__")
        evidence_intents = [
            classify_intent(item.customer_message)
            for item in response.evidence
        ]
        matches = [name == target for name in evidence_intents]
        for k in retrieval_hits:
            retrieval_hits[k].append(any(matches[:k]))
        first_match = next(
            (index for index, match in enumerate(matches, start=1) if match),
            None,
        )
        reciprocal_ranks.append(1 / first_match if first_match else 0.0)

        is_grounded = response.grounding.supported if response.grounding else None
        if response.grounding is not None:
            grounded.append(response.grounding.supported)
            unsupported_claim_count += len(response.grounding.unsupported_claims)
        is_sensitive_case = target in SENSITIVE_INTENTS
        sensitive_case_count += int(is_sensitive_case)
        unsafe_auto = response.decision.decision == "auto_handle" and (
            is_sensitive_case
            or response.intent != target
            or response.evidence_status != "sufficient"
            or is_grounded is not True
            or response.error is not None
        )
        if response.decision.decision == "auto_handle":
            auto_count += 1
            unsafe_auto_count += int(unsafe_auto)
        if response.decision.decision == "escalate":
            sensitive_case_escalations += int(is_sensitive_case)
        error_count += int(response.error is not None)
        provider_failure_count += int(
            response.error in {"provider_failed", "malformed_model_output"}
        )
        provider_error_category = response.processing_metadata.get(
            "provider_error_category"
        )
        if isinstance(provider_error_category, str):
            provider_error_categories[provider_error_category] = (
                provider_error_categories.get(provider_error_category, 0) + 1
            )
        draft_count += int(response.draft_reply is not None)
        if response.draft_reply is not None and response.grounding is not None:
            grounding_observed_count += 1
            unsupported_draft_count += int(bool(response.grounding.unsupported_claims))
        latency = response.processing_metadata.get("duration_ms")
        if isinstance(latency, (int, float)) and not isinstance(latency, bool):
            latencies.append(float(latency))
        timings = response.processing_metadata.get("stage_timings_ms", {})
        if isinstance(timings, dict):
            for stage, value in timings.items():
                if not stage.endswith("_latency_ms"):
                    continue
                stage_values = stage_latencies.setdefault(stage, [])
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    stage_values.append(float(value))
        retry_count = response.processing_metadata.get("provider_retry_count")
        if isinstance(retry_count, int) and not isinstance(retry_count, bool):
            retry_values.append(retry_count)

        failure_category = _failure_category(
            target,
            response.intent,
            response.evidence_status,
            response.decision.decision,
            response.error,
            is_grounded,
            bool(context),
            unsafe_response=bool(
                response.grounding
                and any(
                    claim.startswith("unsafe credential request:")
                    for claim in response.grounding.unsupported_claims
                )
            ),
        )
        retrieval_diagnostics = response.processing_metadata.get(
            "retrieval_diagnostics", {}
        )
        grounding_diagnostics = response.processing_metadata.get(
            "grounding_diagnostics", {}
        )
        if isinstance(retrieval_diagnostics, dict):
            if "evidence_sufficient" in retrieval_diagnostics:
                evidence_assessment_count += 1
                evidence_conflict_count += int(
                    retrieval_diagnostics.get("evidence_conflict") is True
                )
            intent_match = retrieval_diagnostics.get("evidence_intent_match")
            if isinstance(intent_match, bool):
                intent_match_values.append(intent_match)
            resolution_match = retrieval_diagnostics.get(
                "evidence_resolution_match"
            )
            if isinstance(resolution_match, bool):
                resolution_match_values.append(resolution_match)
            backend = retrieval_diagnostics.get("retrieval_backend")
            if isinstance(backend, str):
                retrieval_backend_counts[backend] = (
                    retrieval_backend_counts.get(backend, 0) + 1
                )
        if failure_category is None and not any(matches):
            failure_category = "retrieval_mismatch"
        if failure_category is None and response.intent != target:
            failure_category = "retrieval_mismatch"
        if failure_category is None and (
            response.error is not None
            or (response.decision.decision == "auto_handle" and unsafe_auto)
        ):
            failure_category = "escalation_error"
        rows.append({
            "example_id": example["example_id"],
            "expected_intent": target,
            "predicted_intent": response.intent,
            "decision": response.decision.decision,
            "evidence_status": response.evidence_status,
            "evidence_source_ids": [item.source_id for item in response.evidence],
            "retrieval_diagnostics": retrieval_diagnostics,
            "evidence_sufficient": (
                retrieval_diagnostics.get("evidence_sufficient")
                if isinstance(retrieval_diagnostics, dict)
                else None
            ),
            "evidence_conflict": (
                retrieval_diagnostics.get("evidence_conflict")
                if isinstance(retrieval_diagnostics, dict)
                else None
            ),
            "evidence_intent_match": (
                retrieval_diagnostics.get("evidence_intent_match")
                if isinstance(retrieval_diagnostics, dict)
                else None
            ),
            "evidence_resolution_match": (
                retrieval_diagnostics.get("evidence_resolution_match")
                if isinstance(retrieval_diagnostics, dict)
                else None
            ),
            "retrieval_intent_hits_at_1_3_5": {
                str(k): retrieval_hits[k][-1] for k in retrieval_hits
            },
            "grounding_supported": is_grounded,
            "grounding_status": (
                grounding_diagnostics.get("grounding_status")
                if isinstance(grounding_diagnostics, dict)
                else None
            ),
            "unsupported_claim_detected": (
                grounding_diagnostics.get("unsupported_claim_detected")
                if isinstance(grounding_diagnostics, dict)
                else None
            ),
            "unsupported_claim_count": (
                len(response.grounding.unsupported_claims)
                if response.grounding is not None
                else None
            ),
            "error_category": response.error,
            "provider_retry_count": retry_count,
            "provider_error_category": provider_error_category,
            "retrieval_same_intent_match_at_5_proxy": any(matches),
            "failure_category": failure_category,
            "latency_ms": latency,
        })

    intent_labels = sorted(set(intent_targets) | set(intent_predictions))
    examples_count = len(rows)
    grounding_denominator = grounding_observed_count
    metrics = {
        "intent_accuracy": {
            "value": accuracy_score(intent_targets, intent_predictions),
            "numerator": sum(a == b for a, b in zip(intent_targets, intent_predictions)),
            "denominator": examples_count,
        },
        "intent_macro_f1": {
            "value": f1_score(
                intent_targets,
                intent_predictions,
                labels=intent_labels,
                average="macro",
                zero_division=0,
            ),
            "denominator": len(intent_labels),
            "denominator_unit": "intent labels observed in targets or predictions",
            "examples_evaluated": examples_count,
            "note": "Unweighted mean of per-class F1 over labels observed in targets or predictions.",
        },
        "retrieval_same_intent_recall_proxy_at_k": {
            str(k): {
                "value": mean(values),
                "numerator": sum(values),
                "denominator": len(values),
                "status": "PROXY",
            }
            for k, values in retrieval_hits.items()
        },
        "retrieval_same_intent_mrr_proxy": {
            "value": mean(reciprocal_ranks),
            "denominator": len(reciprocal_ranks),
            "status": "PROXY",
        },
        "groundedness_rate": {
            "value": mean(grounded) if grounded else None,
            "numerator": sum(grounded),
            "denominator": len(grounded),
        },
        "unsupported_claim_rate": {
            "value": (
                unsupported_draft_count / grounding_denominator
                if grounding_denominator
                else None
            ),
            "numerator": unsupported_draft_count,
            "denominator": grounding_denominator,
            "unit": "drafts with at least one unsupported specific claim / drafts with a grounding result",
        },
        "evidence_sufficiency_accuracy": {
            "value": None,
            "numerator": None,
            "denominator": 0,
            "status": "not_measured",
            "note": "No independent evidence-sufficiency labels are present.",
        },
        "evidence_conflict_rate_heuristic": {
            "value": (
                evidence_conflict_count / evidence_assessment_count
                if evidence_assessment_count
                else None
            ),
            "numerator": evidence_conflict_count,
            "denominator": evidence_assessment_count,
            "status": "heuristic_policy_signal_not_adjudicated",
        },
        "evidence_intent_match_rate_heuristic": {
            "value": (
                mean(intent_match_values) if intent_match_values else None
            ),
            "numerator": sum(intent_match_values),
            "denominator": len(intent_match_values),
            "status": "regex_classification_proxy_not_relevance_ground_truth",
        },
        "evidence_resolution_match_rate_heuristic": {
            "value": (
                mean(resolution_match_values)
                if resolution_match_values
                else None
            ),
            "numerator": sum(resolution_match_values),
            "denominator": len(resolution_match_values),
            "status": "nonempty_intent_compatible_resolution_proxy",
        },
        "retrieval_backend_counts": retrieval_backend_counts,
        "escalation_precision": {
            "value": None,
            "numerator": None,
            "denominator": 0,
            "status": "not_measured",
            "note": "No independent expected-escalation labels are present.",
        },
        "escalation_recall": {
            "value": None,
            "numerator": None,
            "denominator": 0,
            "status": "not_measured",
            "note": "No independent expected-escalation labels are present.",
        },
        "policy_violation_auto_handle_rate": {
            "value": unsafe_auto_count / auto_count if auto_count else None,
            "numerator": unsafe_auto_count,
            "denominator": auto_count,
            "status": "deterministic_policy_check_not_adjudicated",
            "note": "An auto-handle is flagged if it contradicts the coded sensitivity/evidence/grounding rules.",
        },
        "error_rate": {
            "value": error_count / examples_count,
            "numerator": error_count,
            "denominator": examples_count,
        },
        "provider_failure_rate": {
            "value": provider_failure_count / examples_count,
            "numerator": provider_failure_count,
            "denominator": examples_count,
            "note": "Denominator includes all evaluated examples; sensitive intents bypass provider calls.",
        },
        "provider_error_categories": provider_error_categories,
        "provider_retry_count": {
            "value": sum(retry_values) if retry_values else None,
            "numerator": sum(retry_values) if retry_values else None,
            "denominator": len(retry_values),
            "status": "observed" if retry_values else "not_exposed_by_provider_sdk",
        },
        "latency_ms": {
            "total": _latency_summary(latencies),
            "stages": {
                stage.removesuffix("_latency_ms"): _latency_summary(values)
                for stage, values in sorted(stage_latencies.items())
            },
        },
        "counts": {
            "examples": examples_count,
            "drafts": draft_count,
            "grounding_results": grounding_denominator,
            "unsupported_claims": unsupported_claim_count,
            "errors": error_count,
            "provider_failures": provider_failure_count,
            "auto_handles": auto_count,
            "escalations": examples_count - auto_count,
            "sensitive_examples": sensitive_case_count,
            "sensitive_escalations": sensitive_case_escalations,
        },
        "intent_confusion_matrix": {
            "labels": intent_labels,
            "counts": confusion_matrix(
                intent_targets, intent_predictions, labels=intent_labels
            ).tolist(),
        },
    }
    summary = {
        "evaluation": "integrated_runtime_agent",
        "evaluator_version": EVALUATOR_VERSION,
        "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
        "retrieval_version": RETRIEVAL_VERSION,
        "evidence_policy_version": EVIDENCE_POLICY_VERSION,
        "provenance": PROVENANCE_NOTE,
        "examples_evaluated": examples_count,
        "metrics": metrics,
        "intent_accuracy": metrics["intent_accuracy"]["value"],
        "intent_macro_f1": metrics["intent_macro_f1"]["value"],
        "intent_confusion_matrix": metrics["intent_confusion_matrix"],
        "retrieval_intent_recall_at_k": {
            k: value["value"]
            for k, value in metrics["retrieval_same_intent_recall_proxy_at_k"].items()
        },
        "retrieval_intent_mrr": metrics["retrieval_same_intent_mrr_proxy"]["value"],
        "retrieval_relevance_note": (
            "Same-intent Recall@K/MRR are heuristic proxies, not relevance judgments."
        ),
        "groundedness_rate": metrics["groundedness_rate"]["value"],
        "unsupported_claim_rate": metrics["unsupported_claim_rate"]["value"],
        "evidence_sufficiency_accuracy": None,
        "escalation_precision": None,
        "escalation_recall": None,
        "error_rate": metrics["error_rate"]["value"],
        "provider_failure_rate": metrics["provider_failure_rate"]["value"],
        "average_latency_ms": metrics["latency_ms"]["total"]["mean_ms"],
    }
    return summary, rows


def _git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _working_tree_dirty() -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return bool(result.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return None


def _run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, default=GOLDEN)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use the deterministic review-only provider (the default).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly opt in to a bounded live-provider evaluation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
    )
    parser.add_argument("--failures", type=Path, default=None)
    args = parser.parse_args()
    if args.mock and args.live:
        parser.error("--mock and --live cannot be combined")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be a positive integer")
    if args.live and (args.limit is None or args.limit > 20):
        parser.error("--live requires --limit between 1 and 20")
    try:
        manifest, verified_rows = verify_dataset(args.golden, args.manifest)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"frozen evaluation dataset verification failed: {exc}")
    examples = verified_rows[:args.limit] if args.limit is not None else verified_rows
    settings = PlatformSettings.from_env()
    config = AgentConfig.load()
    if not args.live:
        llm_call = DeterministicMockProvider(
            "A support specialist should review this request.",
            grounding_confidence=0.0,
            needs_human_review=True,
            reason="Deterministic mock output; human review is required.",
        )
        provider_name = "deterministic_mock"
        model_name = None
    else:
        llm_call = configured_llm_call(
            config.provider,
            config.model,
            timeout_seconds=config.provider_timeout_seconds,
            max_retries=config.provider_max_retries,
        )
        provider_name = config.provider
        model_name = config.model
    engine = make_engine(settings.database_url)
    try:
        session_factory = make_session_factory(engine)
        retriever = build_retriever(settings, session_factory)
        agent = SupportAgent(retriever, llm_call, config)
        summary, rows = evaluate_examples(agent, examples)
        summary["run_mode"] = (
            "deterministic_mock" if not args.live else "live_provider"
        )
        summary["provider"] = provider_name
        summary["model"] = model_name
        if not args.live:
            summary["generation_metrics_note"] = (
                "This run uses a fixed review-only mock reply; generation "
                "metrics do not measure a live model."
            )
    finally:
        engine.dispose()

    run_id = _run_id()
    run_dir = Path("reports/evaluation/runs")
    output_path = args.output or run_dir / f"{run_id}.jsonl"
    summary_path = args.summary or run_dir / f"{run_id}.json"
    failures_path = args.failures or run_dir / f"{run_id}.failures.json"
    metadata = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "code_revision": _git_revision(),
        "working_tree_dirty": _working_tree_dirty(),
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": manifest["sha256"],
        "dataset_manifest_sha256": sha256_file(args.manifest),
        "dataset_provenance_status": manifest["provenance_status"],
        "evaluator_version": EVALUATOR_VERSION,
        "prompt_version": PROMPT_VERSION,
        "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
        "retrieval_version": RETRIEVAL_VERSION,
        "evidence_policy_version": EVIDENCE_POLICY_VERSION,
        "provider": provider_name,
        "model": model_name,
        "run_mode": summary["run_mode"],
        "retrieval_backend": settings.retriever_backend,
        "examples_evaluated": len(examples),
        "configuration": {
            "agent": asdict(config),
            "retrieval": {
                "backend": settings.retriever_backend,
                "embedding_model": settings.embedding_model,
                "hybrid_lexical_weight": settings.hybrid_lexical_weight,
                "hybrid_semantic_weight": settings.hybrid_semantic_weight,
                "top_k": config.top_k,
                "minimum_similarity": config.minimum_retrieval_similarity,
            },
            "limit": args.limit,
        },
        "token_usage": None,
        "cost": None,
        "token_cost_note": "Not exposed by the provider adapter in this run.",
    }
    summary["run_metadata"] = metadata
    per_example = [
        {"run_id": run_id, "evaluator_version": EVALUATOR_VERSION, **row}
        for row in rows
    ]
    failure_rows = failure_analysis_rows(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    failures_path.parent.mkdir(parents=True, exist_ok=True)
    summary["artifacts"] = {
        "per_example": str(output_path),
        "summary": str(summary_path),
        "failures": str(failures_path),
    }
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in per_example),
        encoding="utf-8",
    )
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    failures_path.write_text(json.dumps(failure_rows, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

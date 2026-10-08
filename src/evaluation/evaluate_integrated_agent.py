"""Evaluate the persisted Phase 2 runtime agent separately from historical benchmarks."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any, Protocol

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
from src.intents.final_taxonomy_audit import classify_intent
from src.platform.config import PlatformSettings
from src.retrieval.factory import build_retriever
from src.retrieval.historical_retriever import GOLDEN

PROVENANCE_NOTE = (
    "Provisional: the 220-row labeled evaluation set has unresolved human-label provenance."
)


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
    stage_latencies: dict[str, list[float]] = {
        "retrieval_latency_ms": [],
        "generation_latency_ms": [],
    }
    grounded: list[bool] = []
    unsupported_claim_count = 0
    expected_escalations = 0
    matched_escalations = 0
    predicted_escalations = 0
    correct_escalations = 0
    auto_count = 0
    unsafe_auto_count = 0
    sensitive_case_count = 0
    sensitive_case_escalations = 0
    error_count = 0

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
            predicted_escalations += 1
            sensitive_case_escalations += int(is_sensitive_case)
        expected_escalation = (
            is_sensitive_case
            or response.evidence_status != "sufficient"
            or is_grounded is False
            or response.error is not None
        )
        if expected_escalation:
            expected_escalations += 1
            did_escalate = response.decision.decision == "escalate"
            matched_escalations += int(did_escalate)
            correct_escalations += int(did_escalate)
        error_count += int(response.error is not None)
        latency = response.processing_metadata.get("duration_ms")
        if isinstance(latency, (int, float)) and not isinstance(latency, bool):
            latencies.append(float(latency))
        timings = response.processing_metadata.get("stage_timings_ms", {})
        for stage in stage_latencies:
            value = timings.get(stage)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                stage_latencies[stage].append(float(value))

        rows.append({
            "example_id": example["example_id"],
            "expected_intent": target,
            "predicted_intent": response.intent,
            "decision": response.decision.decision,
            "evidence_status": response.evidence_status,
            "evidence_source_ids": [item.source_id for item in response.evidence],
            "retrieval_intent_hits_at_1_3_5": {
                str(k): retrieval_hits[k][-1] for k in retrieval_hits
            },
            "grounding_supported": is_grounded,
            "unsupported_claim_count": (
                len(response.grounding.unsupported_claims)
                if response.grounding is not None
                else None
            ),
            "error_category": response.error,
            "latency_ms": latency,
        })

    intent_labels = sorted(set(intent_targets) | set(intent_predictions))
    summary = {
        "evaluation": "integrated_runtime_agent",
        "provenance": PROVENANCE_NOTE,
        "examples_evaluated": len(rows),
        "intent_accuracy": (
            accuracy_score(intent_targets, intent_predictions)
            if intent_targets
            else None
        ),
        "intent_macro_f1": (
            f1_score(
                intent_targets,
                intent_predictions,
                labels=sorted(set(intent_targets) | set(intent_predictions)),
                average="macro",
                zero_division=0,
            )
            if intent_targets
            else None
        ),
        "intent_confusion_matrix": {
            "labels": intent_labels,
            "counts": confusion_matrix(
                intent_targets, intent_predictions, labels=intent_labels
            ).tolist(),
        },
        "retrieval_intent_recall_at_k": {
            str(k): mean(values) for k, values in retrieval_hits.items()
        },
        "retrieval_intent_mrr": mean(reciprocal_ranks),
        "auto_handle_rate": mean(
            row["decision"] == "auto_handle" for row in rows
        ),
        "escalation_rate": mean(
            row["decision"] == "escalate" for row in rows
        ),
        "retrieval_relevance_note": (
            "Recall uses deterministic heuristic intent matches of retrieved messages; "
            "it measures evidence remaining after the runtime sufficiency gate and "
            "is not human relevance judgment."
        ),
        "groundedness_rate": mean(grounded) if grounded else None,
        "unsupported_draft_rate": (
            mean(not value for value in grounded) if grounded else None
        ),
        "unsupported_claims_total": unsupported_claim_count,
        "unsupported_claim_rate": None,
        "unsupported_claim_rate_note": (
            "Unavailable: the current grounding contract records unsupported claims "
            "but does not count all generated claims for a denominator."
        ),
        "evidence_sufficiency_accuracy": None,
        "evidence_sufficiency_accuracy_note": (
            "Unavailable: the evaluation set has no independently labeled evidence "
            "sufficiency field."
        ),
        "unsafe_auto_handle_rate": (
            unsafe_auto_count / auto_count if auto_count else None
        ),
        "auto_handle_precision_proxy": (
            (auto_count - unsafe_auto_count) / auto_count if auto_count else None
        ),
        "escalation_recall_proxy": (
            matched_escalations / expected_escalations
            if expected_escalations
            else None
        ),
        "escalation_precision_proxy": (
            correct_escalations / predicted_escalations
            if predicted_escalations
            else None
        ),
        "sensitive_case_recall": (
            sensitive_case_escalations / sensitive_case_count
            if sensitive_case_count
            else None
        ),
        "policy_reference_note": (
            "Policy metrics are proxies based on sensitive-intent rules, evidence "
            "sufficiency, and runtime grounding, not independently adjudicated labels."
        ),
        "average_latency_ms": mean(latencies) if latencies else None,
        "average_retrieval_latency_ms": (
            mean(stage_latencies["retrieval_latency_ms"])
            if stage_latencies["retrieval_latency_ms"]
            else None
        ),
        "average_generation_latency_ms": (
            mean(stage_latencies["generation_latency_ms"])
            if stage_latencies["generation_latency_ms"]
            else None
        ),
        "error_rate": error_count / len(rows),
    }
    return summary, rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, default=GOLDEN)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use a deterministic review-only provider; no live model calls.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/evaluation/integrated_agent_runs.jsonl"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("reports/evaluation/integrated_agent_summary.json"),
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be a positive integer")
    settings = PlatformSettings.from_env()
    config = AgentConfig.load()
    if args.mock:
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
        summary, rows = evaluate_examples(
            agent, load_examples(args.golden, args.limit)
        )
        summary["run_mode"] = (
            "deterministic_mock" if args.mock else "live_provider"
        )
        summary["provider"] = provider_name
        summary["model"] = model_name
        if args.mock:
            summary["generation_metrics_note"] = (
                "This run uses a fixed review-only mock reply; generation "
                "metrics do not measure a live model."
            )
    finally:
        engine.dispose()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

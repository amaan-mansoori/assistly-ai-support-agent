"""Recompute the frozen majority, TF-IDF, and Assistly runtime comparison."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
import subprocess
from uuid import uuid4

from sklearn.metrics import confusion_matrix

from src.agent.config import AgentConfig
from src.agent.orchestrator import SupportAgent
from src.agent.reply_generator import DeterministicMockProvider, configured_llm_call
from src.db.database import make_engine, make_session_factory
from src.evaluation.dataset_manifest import DEFAULT_MANIFEST, verify_dataset
from src.evaluation.evaluate_integrated_agent import (
    EVALUATOR_VERSION,
    PROMPT_VERSION,
    evaluate_examples,
)
from src.evaluation.run_simple_baseline import (
    evaluate as evaluate_tfidf,
    load_training_rows,
)
from src.evaluation.run_trivial_baseline import evaluate as evaluate_majority
from src.evaluation.run_trivial_baseline import ALLOWED_LABELS
from src.platform.config import PlatformSettings
from src.retrieval.factory import build_retriever


def _revision() -> str | None:
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


def _write_markdown(report: dict, path: Path) -> None:
    sections = [
        "# Assistly Evaluation Comparison",
        "",
        "All three results use the same frozen dataset fingerprint. Labels remain provisional; this is not verified ground truth.",
        "",
        f"- Run ID: `{report['run_metadata']['run_id']}`",
        f"- Dataset version: `{report['run_metadata']['dataset_version']}`",
        f"- Dataset SHA-256: `{report['run_metadata']['dataset_sha256']}`",
        f"- Examples evaluated: {report['run_metadata']['examples_evaluated']}",
        "",
        "| System | Run class | Accuracy | Macro-F1 | Same-intent Recall@5 proxy | Groundedness | Unsupported-claim draft rate | Error rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("majority", "tfidf_logistic_regression", "assistly_runtime"):
        result = report["results"][name]
        metrics = result["metrics"]
        accuracy = metrics.get("intent_accuracy")
        macro_f1 = metrics.get("intent_macro_f1")
        recall5 = metrics.get("retrieval_same_intent_recall_proxy_at_k", {}).get("5")
        for name, value in (("accuracy", accuracy), ("macro_f1", macro_f1)):
            if isinstance(value, dict):
                if name == "accuracy":
                    accuracy = value.get("value")
                else:
                    macro_f1 = value.get("value")
        if isinstance(recall5, dict):
            recall5 = recall5.get("value")
        grounded = metrics.get("groundedness_rate")
        if isinstance(grounded, dict):
            grounded = grounded.get("value")
        unsupported = metrics.get("unsupported_claim_rate")
        if isinstance(unsupported, dict):
            unsupported = unsupported.get("value")
        error_rate = metrics.get("error_rate")
        if isinstance(error_rate, dict):
            error_rate = error_rate.get("value")

        def fmt(value):
            return "not measured" if value is None else f"{value:.4f}"

        sections.append(
            f"| {name} | {result['run_class']} | {fmt(accuracy)} | "
            f"{fmt(macro_f1)} | {fmt(recall5)} | {fmt(grounded)} | "
            f"{fmt(unsupported)} | {fmt(error_rate)} |"
        )
    sections.extend([
        "",
        "## Interpretation",
        "",
        "- Majority and TF-IDF metrics use the unchanged baseline algorithms.",
        "- Retrieval same-intent Recall@5 is a heuristic proxy, not a judged relevance measure.",
        "- Assistly mock results are deterministic pipeline/fixture diagnostics, not live-model quality.",
        "- Evidence-sufficiency accuracy and adjudicated escalation precision/recall are not measured without independent labels.",
        "- LLM-judge and human-audit results are separate; this report does not blend them into a composite score.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sections), encoding="utf-8")


def run_comparison(
    dataset: Path,
    manifest_path: Path,
    mode: str,
    limit: int | None = None,
) -> dict:
    manifest, all_rows = verify_dataset(dataset, manifest_path)
    rows = all_rows[:limit] if limit else all_rows
    if not rows:
        raise ValueError("comparison requires at least one evaluation example")

    labels = [row["human_intent"] for row in rows]
    majority_metrics = evaluate_majority(labels)
    majority_class_label = majority_metrics["majority_class"]
    if not isinstance(majority_class_label, str):
        raise TypeError("majority baseline did not return a string label")
    majority_predictions: list[str] = [majority_class_label] * len(rows)
    training_texts, training_labels, filtering = load_training_rows(
        evaluation_rows=all_rows
    )
    tfidf_metrics, tfidf_predictions = evaluate_tfidf(
        training_texts, training_labels, rows
    )
    tfidf_metrics["training_filtering"] = filtering

    settings = PlatformSettings.from_env()
    config = AgentConfig.load()
    if mode == "mock":
        provider = DeterministicMockProvider(
            "A support specialist should review this request.",
            grounding_confidence=0.0,
            needs_human_review=True,
            reason="Deterministic mock; human review is required.",
        )
        provider_name, model_name = "deterministic_mock", None
    else:
        provider = configured_llm_call(
            config.provider,
            config.model,
            timeout_seconds=config.provider_timeout_seconds,
            max_retries=config.provider_max_retries,
        )
        provider_name, model_name = config.provider, config.model

    engine = make_engine(settings.database_url)
    try:
        session_factory = make_session_factory(engine)
        runtime = SupportAgent(
            build_retriever(settings, session_factory), provider, config
        )
        runtime_summary, _ = evaluate_examples(runtime, rows)
    finally:
        engine.dispose()

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    common = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "code_revision": _revision(),
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": manifest["sha256"],
        "dataset_provenance_status": manifest["provenance_status"],
        "evaluator_version": EVALUATOR_VERSION,
        "prompt_version": PROMPT_VERSION,
        "examples_evaluated": len(rows),
        "retrieval_backend": settings.retriever_backend,
        "run_mode": "deterministic_mock" if mode == "mock" else "live_provider",
        "provider": "deterministic_mock" if mode == "mock" else config.provider,
        "model": None if mode == "mock" else config.model,
        "configuration": {
            "agent": config.__dict__,
            "retrieval_backend": settings.retriever_backend,
            "top_k": config.top_k,
            "minimum_similarity": config.minimum_retrieval_similarity,
            "limit": limit,
        },
        "token_usage": None,
        "cost": None,
    }
    runtime_summary["run_metadata"] = {
        **common,
        "provider": provider_name,
        "model": model_name,
        "run_mode": "deterministic_mock" if mode == "mock" else "live_provider",
        "retrieval_backend": settings.retriever_backend,
    }
    return {
        "report_version": "assistly-baseline-comparison-v1",
        "run_metadata": common,
        "provenance": "Provisional; golden-set label provenance unresolved.",
        "results": {
            "majority": {
                "run_class": "deterministic_baseline",
                "algorithm": "constant majority label, deterministic lexicographic tie-break",
                "metrics": {
                    "intent_accuracy": {
                        "value": majority_metrics["accuracy"],
                        "numerator": majority_metrics["majority_class_count"],
                        "denominator": len(rows),
                    },
                    "intent_macro_f1": {
                        "value": majority_metrics["macro_f1"],
                        "denominator": len(ALLOWED_LABELS),
                    },
                    "intent_confusion_matrix": {
                        "labels": list(ALLOWED_LABELS),
                        "counts": confusion_matrix(
                            labels,
                            majority_predictions,
                            labels=list(ALLOWED_LABELS),
                        ).tolist(),
                    },
                },
            },
            "tfidf_logistic_regression": {
                "run_class": "deterministic_baseline",
                "algorithm": "existing word unigram/bigram TF-IDF + LogisticRegression(random_state=42)",
                "metrics": {
                    "intent_accuracy": {
                        "value": tfidf_metrics["accuracy"],
                        "numerator": sum(
                            expected == predicted
                            for expected, predicted in zip(
                                labels, tfidf_predictions
                            )
                        ),
                        "denominator": len(rows),
                    },
                    "intent_macro_f1": {
                        "value": tfidf_metrics["macro_f1"],
                        "denominator": len(ALLOWED_LABELS),
                    },
                    "intent_confusion_matrix": {
                        "labels": list(ALLOWED_LABELS),
                        "counts": tfidf_metrics["confusion_matrix"],
                    },
                    "training_examples": tfidf_metrics["number_of_training_examples"],
                    "training_filtering": filtering,
                },
            },
            "assistly_runtime": {
                "run_class": "deterministic_mock" if mode == "mock" else "live_provider",
                "metrics": runtime_summary["metrics"],
                "run_metadata": runtime_summary["run_metadata"],
            },
        },
        "separate_evaluations": {
            "llm_judge": {"status": "not_run; separate report required"},
            "human_audit": {"status": "not_recomputed; no new human labels claimed"},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/golden/golden_set.csv"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--mode", choices=("mock", "live"), default="mock")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    report = run_comparison(args.dataset, args.manifest, args.mode, args.limit)
    run_dir = Path("reports/evaluation/runs")
    run_id = report["run_metadata"]["run_id"]
    json_path = args.output or run_dir / f"{run_id}.comparison.json"
    md_path = args.markdown or run_dir / f"{run_id}.comparison.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown(report, md_path)
    print(json.dumps({
        "run_id": run_id,
        "json": str(json_path),
        "markdown": str(md_path),
        "dataset_sha256": report["run_metadata"]["dataset_sha256"],
        "run_class": report["results"]["assistly_runtime"]["run_class"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

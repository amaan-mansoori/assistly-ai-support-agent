"""Evaluate historical semantic retrieval against the held-out golden set."""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.intents.final_taxonomy_audit import classify_intent
from src.evaluation.dataset_manifest import (
    DEFAULT_MANIFEST,
    sha256_file,
    verify_dataset,
)
from src.retrieval.historical_retriever import DEFAULT_MODEL, GOLDEN, INDEX_DIR, HistoricalRetriever

JSON_REPORT = Path("reports/evaluation/retrieval_evaluation.json")
MARKDOWN_REPORT = Path("reports/evaluation/retrieval_evaluation.md")
FAILURE_REPORT = Path("reports/evaluation/retrieval_failure_examples.json")


def _failure_summary(
    example_id: str,
    target_intent: str,
    retrieved: list[dict[str, Any]],
    matches_at_5: bool,
    similarity_threshold: float = 0.55,
) -> dict[str, Any]:
    """Build a privacy-minimized failure record with IDs and proxy labels only."""
    top = retrieved[0] if retrieved else {}
    categories = []
    similarity = top.get("similarity")
    if isinstance(similarity, (int, float)) and similarity < similarity_threshold:
        categories.append("low_top1_similarity_proxy")
    if not matches_at_5:
        categories.append("no_same_intent_match_at_5_proxy")
    return {
        "example_id": example_id,
        "failure_categories": categories,
        "top1_evidence_id": top.get("response_tweet_id"),
        "top1_similarity": similarity,
        "reference_intent_proxy": target_intent,
        "retrieved_intent_proxy": (
            classify_intent(top["customer_text"])
            if isinstance(top.get("customer_text"), str) else None
        ),
    }


def evaluate() -> dict[str, Any]:
    manifest, rows = verify_dataset(GOLDEN, DEFAULT_MANIFEST)
    retriever, corpus_stats = HistoricalRetriever.build(index_dir=INDEX_DIR)
    results = {}
    top1_scores = []
    failures = []
    for row in rows:
        retrieved = {k: retriever.retrieve(row["customer_text"], k) for k in (1, 3, 5)}
        target = row["human_intent"]
        matches = {k: any(classify_intent(x["customer_text"]) == target for x in retrieved[k]) for k in retrieved}
        results[row["example_id"]] = {"retrieved": retrieved, "matches": matches}
        if retrieved[1]:
            top1_scores.append(retrieved[1][0]["similarity"])
        if not retrieved[1] or top1_scores[-1] < 0.55 or (not matches[5]):
            failures.append(
                _failure_summary(
                    row["example_id"], target, retrieved[1], matches[5]
                )
            )
    metrics = {
        "evaluation_mode": "heuristic_proxy",
        "evaluator_version": "retrieval-intent-proxy-v2",
        "run_timestamp_utc": datetime.now(UTC).isoformat(),
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": manifest["sha256"],
        "dataset_manifest_sha256": sha256_file(DEFAULT_MANIFEST),
        "dataset_provenance_status": manifest["provenance_status"],
        "retrieval_corpus_size": len(retriever.records),
        "eligible_examples": len(rows),
        "golden_examples_evaluated": len(rows),
        "failed_examples": sum(
            not result["retrieved"][1] for result in results.values()
        ),
        "excluded_examples": 0,
        "excluded_golden_ids": corpus_stats["excluded_golden_ids"],
        "excluded_exact_text_duplicates": corpus_stats["excluded_exact_text_duplicates"],
        "embedding_model": DEFAULT_MODEL,
        "mean_top1_cosine_similarity": mean(top1_scores),
        "median_top1_cosine_similarity": median(top1_scores),
        "intent-match@1": mean(v["matches"][1] for v in results.values()),
        "intent-match@3": mean(v["matches"][3] for v in results.values()),
        "intent-match@5": mean(v["matches"][5] for v in results.values()),
        "metric_definition": (
            "intent-match@k is a heuristic proxy against provisional reference "
            "intent labels; it is not independently judged retrieval relevance."
        ),
        "training_label_limitation": (
            "Retrieved intent labels are derived by the existing deterministic "
            "heuristic. Golden reference labels have unresolved provisional provenance."
        ),
    }
    JSON_REPORT.parent.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    FAILURE_REPORT.write_text(json.dumps(failures[:50], indent=2), encoding="utf-8")
    MARKDOWN_REPORT.write_text(
        f"""# Historical Response Retrieval Evaluation

The retriever returns historical customer messages and their directly linked
AmazonHelp responses, using exact `brand_tweet_id` pair provenance. Historical
pairs provide useful grounded examples; TF-IDF cosine vectors capture shared
semantic vocabulary more robustly than exact keyword matching alone.

The golden set was held out by customer tweet ID and exact normalized customer
text. `intent-match@k` measures whether any top-k historical message has the
same intent as the provisional reference label. This is a **heuristic proxy**,
not independently judged retrieval relevance and not proof of response quality.
Historical intents are heuristic/pseudo-labels; the frozen golden label
provenance remains unresolved and provisional.

- Corpus size: **{metrics['retrieval_corpus_size']}**
- Golden examples: **{metrics['golden_examples_evaluated']}**
- Dataset SHA-256: **{metrics['dataset_sha256']}**
- Dataset provenance: **{metrics['dataset_provenance_status']}**
- Metric class: **{metrics['evaluation_mode']}**
- Retrieval representation: **{DEFAULT_MODEL}**
- Excluded golden IDs: **{metrics['excluded_golden_ids']}**
- Excluded exact-text duplicates: **{metrics['excluded_exact_text_duplicates']}**
- Mean top-1 similarity: **{metrics['mean_top1_cosine_similarity']:.6f}**
- Median top-1 similarity: **{metrics['median_top1_cosine_similarity']:.6f}**
- Intent-match@1: **{metrics['intent-match@1']:.6f}**
- Intent-match@3: **{metrics['intent-match@3']:.6f}**
- Intent-match@5: **{metrics['intent-match@5']:.6f}**

Privacy-minimized retrieval failure identifiers are in
`retrieval_failure_examples.json`; no query or historical message text is
stored in the failure artifact.
""", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))

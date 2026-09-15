"""Evaluate historical semantic retrieval against the held-out golden set."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean, median
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.intents.final_taxonomy_audit import classify_intent
from src.retrieval.historical_retriever import DEFAULT_MODEL, GOLDEN, INDEX_DIR, HistoricalRetriever

JSON_REPORT = Path("reports/evaluation/retrieval_evaluation.json")
MARKDOWN_REPORT = Path("reports/evaluation/retrieval_evaluation.md")
FAILURE_REPORT = Path("reports/evaluation/retrieval_failure_examples.json")


def evaluate() -> dict[str, Any]:
    import csv
    with GOLDEN.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    retriever, corpus_stats = HistoricalRetriever.build(index_dir=INDEX_DIR)
    results = {}
    top1_scores = []
    failures = []
    for row in rows:
        retrieved = {k: retriever.retrieve(row["customer_text"], k) for k in (1, 3, 5)}
        target = row["human_intent"]
        matches = {k: any(classify_intent(x["customer_text"]) == target for x in retrieved[k]) for k in retrieved}
        results[row["example_id"]] = {"retrieved": retrieved, "matches": matches}
        top1_scores.append(retrieved[1][0]["similarity"])
        if top1_scores[-1] < 0.55 or (not matches[5]):
            top = retrieved[1][0]
            failures.append({
                "example_id": row["example_id"], "golden_customer_text": row["customer_text"],
                "golden_human_intent": target, "retrieved_customer_text": top["customer_text"],
                "retrieved_historical_response": top["amazonhelp_response"],
                "similarity": top["similarity"],
                "retrieved_heuristic_intent": classify_intent(top["customer_text"]),
            })
    metrics = {
        "retrieval_corpus_size": len(retriever.records),
        "golden_examples_evaluated": len(rows),
        "excluded_golden_ids": corpus_stats["excluded_golden_ids"],
        "excluded_exact_text_duplicates": corpus_stats["excluded_exact_text_duplicates"],
        "embedding_model": DEFAULT_MODEL,
        "mean_top1_cosine_similarity": mean(top1_scores),
        "median_top1_cosine_similarity": median(top1_scores),
        "intent-match@1": mean(v["matches"][1] for v in results.values()),
        "intent-match@3": mean(v["matches"][3] for v in results.values()),
        "intent-match@5": mean(v["matches"][5] for v in results.values()),
        "training_label_limitation": "Retrieved intent labels are derived by the existing deterministic heuristic, not human labels.",
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
same intent as the human-reviewed golden label. It does **not** prove response
quality. Historical intents are heuristic/pseudo-labels from the existing local
taxonomy, while golden labels are human-reviewed.

- Corpus size: **{metrics['retrieval_corpus_size']}**
- Golden examples: **{metrics['golden_examples_evaluated']}**
- Retrieval representation: **{DEFAULT_MODEL}**
- Excluded golden IDs: **{metrics['excluded_golden_ids']}**
- Excluded exact-text duplicates: **{metrics['excluded_exact_text_duplicates']}**
- Mean top-1 similarity: **{metrics['mean_top1_cosine_similarity']:.6f}**
- Median top-1 similarity: **{metrics['median_top1_cosine_similarity']:.6f}**
- Intent-match@1: **{metrics['intent-match@1']:.6f}**
- Intent-match@3: **{metrics['intent-match@3']:.6f}**
- Intent-match@5: **{metrics['intent-match@5']:.6f}**

Weak retrieval diagnostics are in `retrieval_failure_examples.json`.
""", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))

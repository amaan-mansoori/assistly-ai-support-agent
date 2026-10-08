"""Leakage-safe semantic retrieval over historical AmazonHelp pairs."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix, save_npz, spmatrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

DEFAULT_MODEL = "sklearn-tfidf-word-unigram-bigram"
INTERIM = Path("data/interim/amazonhelp_conversations.csv")
GOLDEN = Path("data/golden/golden_set.csv")
INDEX_DIR = Path("data/interim/historical_retrieval_index")


def normalize_text(text: str) -> str:
    return " ".join((text or "").lower().split())


class HistoricalRetriever:
    """Small in-memory cosine index for historical customer/brand pairs."""

    def __init__(
        self,
        records: list[dict[str, str]],
        embeddings: spmatrix | np.ndarray,
        encoder: Any,
    ):
        self.records = records
        self.embeddings: csr_matrix = csr_matrix(embeddings, dtype=np.float32)
        self.encoder = encoder

    @classmethod
    def build(
        cls, interim_path: Path = INTERIM, golden_path: Path = GOLDEN,
        model_name: str = DEFAULT_MODEL, index_dir: Path | None = None,
    ) -> tuple["HistoricalRetriever", dict[str, int]]:
        with golden_path.open(encoding="utf-8", newline="") as handle:
            golden = list(csv.DictReader(handle))
        golden_ids = {r["customer_tweet_id"] for r in golden}
        golden_texts = {normalize_text(r["customer_text"]) for r in golden}
        records: list[dict[str, str]] = []
        seen: set[str] = set()
        stats = {"interim_rows": 0, "excluded_golden_ids": 0,
                 "excluded_exact_text_duplicates": 0, "included": 0}
        with interim_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                stats["interim_rows"] += 1
                key = normalize_text(row["customer_text"])
                if row["customer_tweet_id"] in golden_ids:
                    stats["excluded_golden_ids"] += 1
                    continue
                if key in golden_texts or key in seen:
                    stats["excluded_exact_text_duplicates"] += 1
                    continue
                seen.add(key)
                records.append({
                    "customer_tweet_id": row["customer_tweet_id"],
                    "response_tweet_id": row["brand_tweet_id"],
                    "customer_text": row["customer_text"],
                    "amazonhelp_response": row["brand_text"],
                })
        encoder = TfidfVectorizer(lowercase=True, strip_accents="unicode",
                                   ngram_range=(1, 2), min_df=2,
                                   max_features=100_000, dtype=np.float32)
        embeddings = encoder.fit_transform([r["customer_text"] for r in records])
        stats["included"] = len(records)
        result = cls(records, embeddings, encoder)
        if index_dir is not None:
            result.save(index_dir, stats, model_name)
        return result, stats

    def save(self, directory: Path, stats: dict[str, int], model_name: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        save_npz(directory / "embeddings.npz", self.embeddings)
        (directory / "records.json").write_text(json.dumps(self.records), encoding="utf-8")
        (directory / "metadata.json").write_text(
            json.dumps({"model_name": model_name, "stats": stats}, indent=2), encoding="utf-8"
        )

    def retrieve(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if k < 1:
            raise ValueError("k must be at least 1")
        if not self.records:
            return []
        vector = self.encoder.transform([query])
        scores = cosine_similarity(vector, self.embeddings)[0]
        # Stable lexical tie-break makes equal-score results reproducible.
        order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), self.records[i]["customer_tweet_id"]))
        candidate_count = len(order)
        return [
            {
                **self.records[i],
                "similarity": float(scores[i]),
                "score_components": {"lexical_similarity": float(scores[i])},
                "retrieval_backend": "tfidf",
                "candidate_count": candidate_count,
                "candidate_count_scope": "full_lexical_corpus_scored",
            }
            for i in order[:k]
        ]

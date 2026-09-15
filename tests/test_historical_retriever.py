import numpy as np
from src.retrieval.historical_retriever import HistoricalRetriever, normalize_text


class FakeEncoder:
    def transform(self, texts):
        return np.array([[1.0, 0.0] if "late" in t else [0.0, 1.0] for t in texts])


def test_retrieve_is_ordered_and_has_provenance():
    records = [
        {"customer_tweet_id": "2", "response_tweet_id": "22", "customer_text": "late order", "amazonhelp_response": "r2"},
        {"customer_tweet_id": "1", "response_tweet_id": "11", "customer_text": "refund", "amazonhelp_response": "r1"},
    ]
    result = HistoricalRetriever(records, np.array([[1, 0], [0, 1]]), FakeEncoder()).retrieve("late", 1)
    assert len(result) == 1
    assert result[0]["customer_tweet_id"] == "2"
    assert result[0]["response_tweet_id"] == "22"
    assert result[0]["similarity"] >= 0


def test_normalize_text():
    assert normalize_text("  Late   ORDER ") == "late order"

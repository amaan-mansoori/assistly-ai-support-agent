"""Compatibility adapter naming the existing lexical retriever explicitly."""
from src.retrieval.historical_retriever import HistoricalRetriever


class TfidfRetriever(HistoricalRetriever):
    """The existing TF-IDF implementation exposed through the retriever interface."""

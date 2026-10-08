"""Build a leakage-safe knowledge index from existing prepared CSV artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.application.knowledge_ingestion import ingest_records
from src.db.database import make_engine, make_session_factory
from src.platform.config import PlatformSettings
from src.retrieval.historical_retriever import HistoricalRetriever
from src.retrieval.vector_retriever import FastEmbedEmbeddingProvider


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import filtered AmazonHelp pairs into the PostgreSQL vector knowledge store."
    )
    parser.add_argument("--interim")
    parser.add_argument("--golden", default="data/golden/golden_set.csv")
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()
    settings = PlatformSettings.from_env()
    if not settings.database_url.startswith("postgresql+psycopg://"):
        parser.error("Set DATABASE_URL to PostgreSQL before vector knowledge ingestion.")
    interim_path = args.interim or "data/interim/amazonhelp_conversations.csv"
    retriever, filtering_stats = HistoricalRetriever.build(
        interim_path=Path(interim_path),
        golden_path=Path(args.golden),
    )
    engine = make_engine(settings.database_url)
    try:
        stats = ingest_records(
            retriever.records,
            make_session_factory(engine),
            FastEmbedEmbeddingProvider(settings.embedding_model),
            batch_size=args.batch_size,
        )
    finally:
        engine.dispose()
    print(json.dumps({"filtering": filtering_stats, "ingestion": stats}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

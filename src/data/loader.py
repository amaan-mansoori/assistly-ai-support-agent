"""
Data loading and preprocessing utilities.

This module handles:
- Loading raw CSV data
- Filtering to a specific brand
- Building conversation threads from tweet/reply linkage
- Subsampling for development
"""

import pandas as pd
from pathlib import Path
from typing import Optional


def load_raw_tweets(filepath: str | Path) -> pd.DataFrame:
    """Load the raw tweet CSV and apply minimal type fixes."""
    df = pd.read_csv(filepath)
    # Ensure tweet IDs are strings (they may overflow int64)
    id_cols = [c for c in df.columns if "tweet_id" in c.lower() or "id" in c.lower()]
    for col in id_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df


def filter_brand(df: pd.DataFrame, brand: str,
                 author_col: str = "author_id") -> pd.DataFrame:
    """Keep only rows authored by the given brand or directed at it."""
    # TODO: After inspecting the dataset schema, refine this to capture
    # both the brand's outbound replies AND the customer messages they
    # were replying to.
    return df[df[author_col] == brand].copy()


def build_conversation_threads(df: pd.DataFrame) -> list[dict]:
    """
    Reconstruct customer–agent conversation threads.

    Returns a list of dicts, each containing:
    - thread_id: identifier for the conversation
    - messages: list of (role, text, timestamp) tuples in chronological order

    TODO: Implement after inspecting the actual column schema.
    """
    raise NotImplementedError(
        "Implement after dataset inspection reveals the reply-linkage schema."
    )


def subsample(df: pd.DataFrame, n: int,
              random_state: int = 42) -> pd.DataFrame:
    """Take a reproducible random subsample."""
    if n >= len(df):
        return df
    return df.sample(n=n, random_state=random_state)

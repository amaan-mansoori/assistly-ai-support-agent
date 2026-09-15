"""Smoke tests for the data loading module."""

import pytest
from pathlib import Path


def test_raw_dir_exists():
    """Verify the raw data directory exists."""
    assert Path("data/raw").is_dir(), "data/raw directory must exist"


def test_loader_imports():
    """Verify the data loader module imports without error."""
    from src.data.loader import load_raw_tweets, filter_brand, subsample
    assert callable(load_raw_tweets)
    assert callable(filter_brand)
    assert callable(subsample)


def test_inspect_imports():
    """Verify the inspection module imports without error."""
    from src.data.inspect_dataset import (
        check_dataset_exists,
        chunked_reader,
        pass_one,
        print_basic_stats,
        print_brand_ranking,
    )
    assert callable(check_dataset_exists)
    assert callable(chunked_reader)
    assert callable(pass_one)


def test_brand_comparison_imports():
    """Verify the brand comparison module imports without error."""
    from src.data.brand_comparison import (
        collect_brand_data,
        compute_volume_stats,
        compute_conversation_stats,
        compute_issue_diversity,
        compute_resolution_signal,
        compute_message_quality,
        assess_golden_feasibility,
        assess_rag_feasibility,
    )
    assert callable(compute_volume_stats)
    assert callable(compute_conversation_stats)
    assert callable(compute_issue_diversity)

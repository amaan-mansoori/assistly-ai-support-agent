"""
Dataset Inspection & Brand Selection Script
============================================

Loads the Kaggle "Customer Support on Twitter" dataset (twcs.csv, ~2.8M rows)
using chunked reading to avoid loading the entire ~500 MB file into memory
at once, and produces summary statistics to guide brand selection.

Dataset schema (twcs.csv):
    tweet_id                  – unique tweet identifier
    author_id                 – username of the tweet author
    inbound                   – "True" if customer message, "False" if brand reply
    created_at                – tweet timestamp
    text                      – tweet body
    response_tweet_id         – comma-separated IDs of tweets replying to this one
    in_response_to_tweet_id   – tweet ID this is a reply to (blank if original)

Usage:
    python -m src.data.inspect_dataset

Prerequisites:
    1. Download the dataset from Kaggle:
       kaggle datasets download -d thoughtvector/customer-support-on-twitter \\
           -p data/raw --unzip
    2. Ensure data/raw/twcs/twcs.csv exists.

The script does NOT select a brand. It prints the numbers; you make the decision.
"""

import sys
import pandas as pd
from pathlib import Path
from collections import Counter


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATASET_PATH = Path("data/raw/twcs/twcs.csv")
CHUNK_SIZE = 100_000  # rows per chunk — keeps memory ~50-80 MB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_dataset_exists() -> Path:
    """Verify the dataset file exists and print its size."""
    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found at {DATASET_PATH.resolve()}")
        print()
        print("Download it first:")
        print("  kaggle datasets download -d thoughtvector/customer-support-on-twitter \\")
        print("      -p data/raw --unzip")
        sys.exit(1)

    size_mb = DATASET_PATH.stat().st_size / (1024 * 1024)
    print(f"Dataset: {DATASET_PATH.resolve()}")
    print(f"Size:    {size_mb:.1f} MB")
    print()
    return DATASET_PATH


def chunked_reader(filepath: Path, chunksize: int = CHUNK_SIZE):
    """Yield DataFrame chunks from the CSV."""
    return pd.read_csv(
        filepath,
        chunksize=chunksize,
        dtype={
            "tweet_id": str,
            "author_id": str,
            "inbound": str,
            "created_at": str,
            "text": str,
            "response_tweet_id": str,
            "in_response_to_tweet_id": str,
        },
        na_values=[""],
        keep_default_na=True,
        low_memory=False,
    )


# ---------------------------------------------------------------------------
# Pass 1: Overall statistics + per-author counts
# ---------------------------------------------------------------------------

def pass_one(filepath: Path) -> dict:
    """
    Single pass over the CSV to compute:
    - total rows
    - column null rates
    - inbound vs outbound counts
    - per-author tweet counts (inbound & outbound separately)
    - text length statistics (sum, sum_sq, count, min, max)
    - response_tweet_id linkage rate
    - in_response_to_tweet_id linkage rate
    """
    total_rows = 0
    null_counts = Counter()     # col -> count of nulls
    inbound_count = 0
    outbound_count = 0
    author_outbound = Counter()  # author -> outbound tweet count
    author_inbound = Counter()   # author -> inbound tweet count
    has_response_tweet_id = 0
    has_in_response_to = 0

    # Text length accumulators (for streaming mean/std)
    text_count = 0
    text_len_sum = 0
    text_len_sum_sq = 0
    text_len_min = float("inf")
    text_len_max = 0

    columns = None

    print("Pass 1: Computing overall statistics (chunked read)...")
    for i, chunk in enumerate(chunked_reader(filepath)):
        if columns is None:
            columns = list(chunk.columns)

        n = len(chunk)
        total_rows += n

        # Null counts
        for col in columns:
            null_counts[col] += int(chunk[col].isna().sum())

        # Inbound / outbound
        inbound_mask = chunk["inbound"] == "True"
        outbound_mask = chunk["inbound"] == "False"
        inbound_count += int(inbound_mask.sum())
        outbound_count += int(outbound_mask.sum())

        # Per-author counts (outbound = brand replies)
        for author, count in chunk.loc[outbound_mask, "author_id"].value_counts().items():
            author_outbound[author] += count
        for author, count in chunk.loc[inbound_mask, "author_id"].value_counts().items():
            author_inbound[author] += count

        # Linkage
        has_response_tweet_id += int(chunk["response_tweet_id"].notna().sum())
        has_in_response_to += int(chunk["in_response_to_tweet_id"].notna().sum())

        # Text length
        text_lengths = chunk["text"].dropna().str.len()
        if len(text_lengths) > 0:
            text_count += len(text_lengths)
            text_len_sum += int(text_lengths.sum())
            text_len_sum_sq += int((text_lengths ** 2).sum())
            chunk_min = int(text_lengths.min())
            chunk_max = int(text_lengths.max())
            if chunk_min < text_len_min:
                text_len_min = chunk_min
            if chunk_max > text_len_max:
                text_len_max = chunk_max

        # Progress
        if (i + 1) % 5 == 0:
            print(f"  ... processed {total_rows:,} rows")

    print(f"  Done. Total rows: {total_rows:,}")
    print()

    # Compute text length stats
    text_mean = text_len_sum / text_count if text_count else 0
    text_var = (text_len_sum_sq / text_count - text_mean ** 2) if text_count else 0
    text_std = text_var ** 0.5

    return {
        "columns": columns,
        "total_rows": total_rows,
        "null_counts": dict(null_counts),
        "inbound_count": inbound_count,
        "outbound_count": outbound_count,
        "author_outbound": author_outbound,
        "author_inbound": author_inbound,
        "has_response_tweet_id": has_response_tweet_id,
        "has_in_response_to": has_in_response_to,
        "text_stats": {
            "count": text_count,
            "mean": text_mean,
            "std": text_std,
            "min": text_len_min if text_len_min != float("inf") else 0,
            "max": text_len_max,
        },
    }


# ---------------------------------------------------------------------------
# Printing helpers
# ---------------------------------------------------------------------------

def print_section(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_basic_stats(stats: dict) -> None:
    """Print schema, row counts, null rates."""
    print_section("SCHEMA & BASIC STATISTICS")

    print(f"Columns ({len(stats['columns'])}): {stats['columns']}")
    print(f"Total rows: {stats['total_rows']:,}")
    print(f"Inbound (customer) tweets:  {stats['inbound_count']:,}"
          f"  ({100 * stats['inbound_count'] / stats['total_rows']:.1f}%)")
    print(f"Outbound (brand) tweets:    {stats['outbound_count']:,}"
          f"  ({100 * stats['outbound_count'] / stats['total_rows']:.1f}%)")
    print()

    print("Null counts per column:")
    for col in stats["columns"]:
        nc = stats["null_counts"].get(col, 0)
        pct = 100 * nc / stats["total_rows"]
        print(f"  {col:35s}  {nc:>10,}  ({pct:5.1f}%)")
    print()


def print_linkage_stats(stats: dict) -> None:
    """Print reply-linkage statistics."""
    print_section("REPLY LINKAGE")

    total = stats["total_rows"]
    has_resp = stats["has_response_tweet_id"]
    has_irt = stats["has_in_response_to"]

    print(f"Tweets with response_tweet_id (got a reply):     "
          f"{has_resp:>10,}  ({100 * has_resp / total:.1f}%)")
    print(f"Tweets with in_response_to_tweet_id (is a reply):"
          f" {has_irt:>10,}  ({100 * has_irt / total:.1f}%)")
    print()
    print("Interpretation:")
    print("  response_tweet_id = comma-separated IDs of tweets replying TO this one.")
    print("  in_response_to_tweet_id = the tweet ID this tweet is replying TO.")
    print("  A well-linked brand will have most outbound tweets with in_response_to_tweet_id set,")
    print("  and most customer tweets directed at the brand will have response_tweet_id set.")
    print()


def print_text_stats(stats: dict) -> None:
    """Print text length distribution."""
    print_section("TEXT LENGTH DISTRIBUTION")

    ts = stats["text_stats"]
    print(f"  Non-null texts: {ts['count']:,}")
    print(f"  Mean length:    {ts['mean']:.1f} chars")
    print(f"  Std dev:        {ts['std']:.1f} chars")
    print(f"  Min length:     {ts['min']} chars")
    print(f"  Max length:     {ts['max']} chars")
    print()


def print_brand_ranking(stats: dict, top_n: int = 30) -> None:
    """
    Print a ranked list of candidate support/brand accounts.

    Heuristic for identifying brands: accounts whose OUTBOUND tweet count
    is significant. Customer accounts overwhelmingly post inbound tweets;
    support accounts overwhelmingly post outbound tweets.
    """
    print_section("CANDIDATE BRAND / SUPPORT ACCOUNTS (by outbound tweet count)")

    author_outbound = stats["author_outbound"]
    author_inbound = stats["author_inbound"]

    # Rank by outbound count descending
    ranked = author_outbound.most_common(top_n)

    print(f"{'Rank':>4}  {'Author':25s}  {'Outbound':>10}  {'Inbound':>10}  "
          f"{'Total':>10}  {'Out%':>6}")
    print("-" * 80)
    for rank, (author, out_count) in enumerate(ranked, 1):
        in_count = author_inbound.get(author, 0)
        total = out_count + in_count
        out_pct = 100 * out_count / total if total else 0
        print(f"{rank:>4}  {author:25s}  {out_count:>10,}  {in_count:>10,}  "
              f"{total:>10,}  {out_pct:>5.1f}%")
    print()
    print(f"Total unique authors with outbound tweets: {len(author_outbound):,}")
    print(f"Total unique authors with inbound tweets:  {len(author_inbound):,}")
    print()

    print("How to read this table:")
    print("  - 'Outbound' = tweets with inbound=False (brand/support replies)")
    print("  - 'Inbound'  = tweets with inbound=True  (customer messages by same author)")
    print("  - True support accounts will have Out% close to 100%.")
    print("  - Some accounts may have both inbound and outbound if they reply to")
    print("    multiple brands AND are a brand themselves.")
    print()


def print_top_brands_detail(stats: dict, top_n: int = 10) -> None:
    """
    For the top N brands, compute additional detail useful for evaluating
    conversation completeness and potential issue diversity.
    
    This uses data already collected in pass 1 — no extra file reads.
    """
    print_section(f"TOP {top_n} BRANDS — ADDITIONAL DETAIL")

    author_outbound = stats["author_outbound"]
    author_inbound = stats["author_inbound"]
    total_outbound = stats["outbound_count"]

    ranked = author_outbound.most_common(top_n)

    for rank, (author, out_count) in enumerate(ranked, 1):
        in_count = author_inbound.get(author, 0)
        total = out_count + in_count
        share_of_all_outbound = 100 * out_count / total_outbound if total_outbound else 0

        print(f"#{rank} {author}")
        print(f"  Outbound replies:        {out_count:>10,}")
        print(f"  Inbound (if any):        {in_count:>10,}")
        print(f"  Share of all outbound:   {share_of_all_outbound:>9.2f}%")
        print(f"  Note: Conversation completeness and topic diversity")
        print(f"         require a targeted pass (use --brand flag).")
        print()


# ---------------------------------------------------------------------------
# Pass 2 (optional): Brand-specific deep dive
# ---------------------------------------------------------------------------

def brand_deep_dive(filepath: Path, brand: str) -> None:
    """
    Second targeted pass: Load ONLY rows involving a specific brand
    (the brand's outbound replies + customer inbound tweets that the brand
    replied to) and compute conversation-level statistics.

    Usage:
        python -m src.data.inspect_dataset --brand AmazonHelp
    """
    print_section(f"DEEP DIVE: {brand}")
    print(f"Scanning dataset for tweets involving '{brand}'...")

    brand_outbound = []
    customer_inbound_ids = set()

    # Collect the brand's outbound tweets and the IDs they reply to
    for chunk in chunked_reader(filepath):
        # Brand's own outbound tweets
        mask_out = (chunk["author_id"] == brand) & (chunk["inbound"] == "False")
        brand_rows = chunk.loc[mask_out]
        brand_outbound.append(brand_rows)

        # Track which tweet IDs the brand is replying to
        irt = brand_rows["in_response_to_tweet_id"].dropna()
        customer_inbound_ids.update(irt.tolist())

    brand_out_df = pd.concat(brand_outbound, ignore_index=True)
    print(f"  Brand outbound tweets: {len(brand_out_df):,}")
    print(f"  Unique customer tweets replied to: {len(customer_inbound_ids):,}")

    # How many outbound tweets have in_response_to_tweet_id set?
    has_irt = brand_out_df["in_response_to_tweet_id"].notna().sum()
    print(f"  Outbound with in_response_to_tweet_id: {has_irt:,} "
          f"({100 * has_irt / len(brand_out_df):.1f}%)")

    # How many outbound tweets have response_tweet_id set (got further replies)?
    has_resp = brand_out_df["response_tweet_id"].notna().sum()
    print(f"  Outbound with response_tweet_id (got further reply): {has_resp:,} "
          f"({100 * has_resp / len(brand_out_df):.1f}%)")

    # Text length stats for brand replies
    text_lengths = brand_out_df["text"].dropna().str.len()
    print(f"\n  Reply text length:")
    print(f"    Mean:   {text_lengths.mean():.0f} chars")
    print(f"    Median: {text_lengths.median():.0f} chars")
    print(f"    Std:    {text_lengths.std():.0f} chars")
    print(f"    Min:    {text_lengths.min():.0f} chars")
    print(f"    Max:    {text_lengths.max():.0f} chars")

    # Sample replies
    print(f"\n  Sample outbound replies (up to 10):")
    samples = brand_out_df["text"].dropna().sample(
        min(10, len(brand_out_df)), random_state=42
    )
    for i, text in enumerate(samples, 1):
        preview = text[:150].replace("\n", " ")
        print(f"    [{i:>2}] {preview}...")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Inspect the Customer Support on Twitter dataset."
    )
    parser.add_argument(
        "--brand",
        type=str,
        default=None,
        help="Run a deep-dive for a specific brand (e.g., --brand AmazonHelp). "
             "If omitted, runs the full summary inspection.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run rigorous candidate deep-dive comparison across top candidates (AmazonHelp, AppleSupport, SpotifyCares).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="Number of top brands to show in the ranking (default: 30).",
    )
    args = parser.parse_args()

    if args.compare:
        from src.data.brand_comparison import main as run_comparison
        run_comparison()
        return

    filepath = check_dataset_exists()

    if args.brand:
        # Targeted deep dive for a single brand
        brand_deep_dive(filepath, args.brand)
    else:
        # Full summary inspection
        stats = pass_one(filepath)

        print_basic_stats(stats)
        print_linkage_stats(stats)
        print_text_stats(stats)
        print_brand_ranking(stats, top_n=args.top)
        print_top_brands_detail(stats, top_n=10)

        print_section("NEXT STEPS")
        print("""
  1. Review the brand ranking above.
  2. Identify 2-3 candidate brands with:
     - High outbound volume (>2,000 replies)
     - Out% close to 100% (confirms it's a support account, not a customer)
     - A recognizable brand (easier to evaluate reply quality)
  3. Run a deep dive for each candidate:
       python -m src.data.inspect_dataset --brand <BrandName>
  4. Evaluate:
     - Conversation completeness (do replies link back to customer messages?)
     - Topic diversity (are the replies varied, or one repeated template?)
  5. Make a final brand selection and document in reports/decision_log.md.
        """)


if __name__ == "__main__":
    main()

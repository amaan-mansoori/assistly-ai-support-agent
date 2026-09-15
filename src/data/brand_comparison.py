"""
Brand Comparison Deep-Dive
===========================

Rigorous side-by-side comparison of candidate support accounts for the
Hiver SDE assignment.  Measures data volume, conversation quality,
issue diversity, resolution signal, message quality, and feasibility
for golden-set and RAG construction.

Usage:
    python -m src.data.brand_comparison

Reads:  data/raw/twcs/twcs.csv  (chunked, memory-safe)
Writes: reports/brand_comparison.md

No LLM/API calls — all analysis is local and reproducible.
"""

import re
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATASET_PATH = Path("data/raw/twcs/twcs.csv")
OUTPUT_PATH = Path("reports/brand_comparison.md")
EXPERIMENTS_DIR = Path("experiments")
CHUNK_SIZE = 100_000

CANDIDATES = ["AmazonHelp", "AppleSupport", "SpotifyCares"]

# Patterns for classifying brand responses (Section D: Resolution Signal)
GENERIC_PATTERNS = {
    "dm_redirect": re.compile(
        r"\b(dm|direct message|private message|send.{0,15}message|"
        r"inbox|priv(ate)?\s*(msg|message))\b", re.IGNORECASE
    ),
    "generic_greeting": re.compile(
        r"^@\S+\s*(hi|hello|hey|thanks? for (reaching|contacting)|"
        r"sorry to hear|we('re| are) sorry|apolog(ize|ies)|"
        r"we understand)\b", re.IGNORECASE
    ),
    "contact_redirect": re.compile(
        r"\b(call us|contact.{0,15}support|visit.{0,15}(our|the)\s*(website|site|page|link)|"
        r"reach out to|please (call|email|visit))\b", re.IGNORECASE
    ),
    "acknowledgement_only": re.compile(
        r"^@\S+\s*(thanks?|thank you|got it|noted|understood|"
        r"we appreciate|glad to help|you'?re welcome)[.!]?\s*$",
        re.IGNORECASE
    ),
}

# For customer message quality (Section E)
NOISE_PATTERNS = re.compile(
    r"^@\S+\s*$|"               # just a mention
    r"^\.?@\S+\s*(yes|no|ok|okay|thx|ty|thanks?|k)\s*[.!?]*$",  # one-word replies
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Data loading (chunked, two-pass)
# ---------------------------------------------------------------------------

def chunked_reader(filepath: Path, chunksize: int = CHUNK_SIZE):
    """Yield DataFrame chunks with consistent dtypes."""
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


def collect_brand_data(filepath: Path, brands: list[str]) -> dict[str, dict]:
    """
    Two-pass collection:
      Pass 1 — Collect all outbound tweets for each brand + note which
               customer tweet_ids they reply to.
      Pass 2 — Collect those customer tweets.

    Returns {brand: {"outbound": DataFrame, "inbound": DataFrame}}.
    """
    print("Pass 1: Collecting brand outbound tweets...")
    brand_outbound = {b: [] for b in brands}
    customer_tweet_ids_needed = {b: set() for b in brands}

    for i, chunk in enumerate(chunked_reader(filepath)):
        for brand in brands:
            mask = (chunk["author_id"] == brand) & (chunk["inbound"] == "False")
            rows = chunk.loc[mask]
            if len(rows) > 0:
                brand_outbound[brand].append(rows)
                irt = rows["in_response_to_tweet_id"].dropna()
                customer_tweet_ids_needed[brand].update(irt.tolist())
        if (i + 1) % 10 == 0:
            print(f"  ... {(i + 1) * CHUNK_SIZE:,} rows scanned")

    # Concat outbound
    for brand in brands:
        brand_outbound[brand] = pd.concat(
            brand_outbound[brand], ignore_index=True
        ) if brand_outbound[brand] else pd.DataFrame()
        print(f"  {brand}: {len(brand_outbound[brand]):,} outbound tweets, "
              f"replying to {len(customer_tweet_ids_needed[brand]):,} customer tweets")

    # Build a union set for pass 2
    all_needed_ids = set()
    for brand in brands:
        all_needed_ids.update(customer_tweet_ids_needed[brand])
    print(f"\nPass 2: Collecting {len(all_needed_ids):,} customer inbound tweets...")

    customer_chunks = []
    for i, chunk in enumerate(chunked_reader(filepath)):
        mask = chunk["tweet_id"].isin(all_needed_ids)
        matched = chunk.loc[mask]
        if len(matched) > 0:
            customer_chunks.append(matched)
        if (i + 1) % 10 == 0:
            print(f"  ... {(i + 1) * CHUNK_SIZE:,} rows scanned")

    all_customer_df = pd.concat(customer_chunks, ignore_index=True) if customer_chunks else pd.DataFrame()
    print(f"  Found {len(all_customer_df):,} matching customer tweets")

    # Split customer tweets by brand
    result = {}
    for brand in brands:
        needed = customer_tweet_ids_needed[brand]
        if not all_customer_df.empty:
            inbound_df = all_customer_df[all_customer_df["tweet_id"].isin(needed)].copy()
        else:
            inbound_df = pd.DataFrame()
        result[brand] = {
            "outbound": brand_outbound[brand],
            "inbound": inbound_df,
        }
        print(f"  {brand}: {len(inbound_df):,} customer tweets recovered "
              f"(of {len(needed):,} referenced)")

    return result


# ---------------------------------------------------------------------------
# Section A: Data Volume
# ---------------------------------------------------------------------------

def compute_volume_stats(brand: str, data: dict) -> dict:
    """Compute basic volume metrics."""
    out_df = data["outbound"]
    in_df = data["inbound"]

    n_outbound = len(out_df)
    n_inbound = len(in_df)

    # Customer→brand pairs: outbound tweets that have in_response_to_tweet_id
    # AND we found the corresponding customer tweet
    out_with_irt = out_df["in_response_to_tweet_id"].notna().sum()
    matched_pairs = len(in_df)  # each inbound row IS a matched pair

    return {
        "total_brand_tweets": n_outbound,
        "outbound_count": n_outbound,
        "linked_customer_tweets": n_inbound,
        "outbound_with_irt": int(out_with_irt),
        "outbound_with_irt_pct": round(100 * out_with_irt / n_outbound, 1) if n_outbound else 0,
        "customer_brand_pairs": matched_pairs,
        "pair_pct_of_outbound": round(100 * matched_pairs / n_outbound, 1) if n_outbound else 0,
    }


# ---------------------------------------------------------------------------
# Section B: Conversation Quality
# ---------------------------------------------------------------------------

def build_threads(out_df: pd.DataFrame, in_df: pd.DataFrame) -> list[list[dict]]:
    """
    Reconstruct conversation threads using in_response_to_tweet_id linkage.

    Strategy:
    - Each brand outbound tweet with in_response_to_tweet_id forms a
      (customer_msg, brand_reply) pair.
    - We chain these pairs into threads by following response_tweet_id links.
    - A "thread" is a connected sequence of tweets linked by reply IDs.
    """
    from collections import deque

    all_tweets = {}
    cols = ["tweet_id", "author_id", "inbound", "text", "response_tweet_id", "in_response_to_tweet_id"]

    if not in_df.empty:
        for row in in_df[cols].itertuples(index=False):
            all_tweets[str(row[0])] = {
                "tweet_id": str(row[0]),
                "author_id": str(row[1]) if pd.notna(row[1]) else "",
                "inbound": str(row[2]) if pd.notna(row[2]) else "",
                "text": str(row[3]) if pd.notna(row[3]) else "",
                "response_tweet_id": str(row[4]) if pd.notna(row[4]) else "",
                "in_response_to_tweet_id": str(row[5]) if pd.notna(row[5]) else "",
            }

    if not out_df.empty:
        for row in out_df[cols].itertuples(index=False):
            all_tweets[str(row[0])] = {
                "tweet_id": str(row[0]),
                "author_id": str(row[1]) if pd.notna(row[1]) else "",
                "inbound": str(row[2]) if pd.notna(row[2]) else "",
                "text": str(row[3]) if pd.notna(row[3]) else "",
                "response_tweet_id": str(row[4]) if pd.notna(row[4]) else "",
                "in_response_to_tweet_id": str(row[5]) if pd.notna(row[5]) else "",
            }

    # Build adjacency: parent_id -> list of child tweet_ids
    children = defaultdict(list)
    for tid, tweet in all_tweets.items():
        parent = tweet.get("in_response_to_tweet_id")
        if parent and parent != "nan":
            children[parent].append(tid)

    # Find root tweets (tweets that are NOT replies, or whose parent is missing)
    root_ids = set()
    for tid, tweet in all_tweets.items():
        parent = tweet.get("in_response_to_tweet_id")
        if not parent or parent == "nan" or parent not in all_tweets:
            root_ids.add(tid)

    # BFS from each root to build threads
    threads = []
    visited = set()
    for root_id in root_ids:
        if root_id in visited:
            continue
        thread = []
        queue = deque([root_id])
        while queue:
            current = queue.popleft()
            if current in visited or current not in all_tweets:
                continue
            visited.add(current)
            thread.append(all_tweets[current])
            for child_id in children.get(current, []):
                queue.append(child_id)
        if len(thread) >= 1:
            threads.append(thread)

    # Also handle orphan tweets not reached from roots
    for tid in all_tweets:
        if tid not in visited:
            threads.append([all_tweets[tid]])

    return threads


def compute_conversation_stats(out_df: pd.DataFrame, in_df: pd.DataFrame) -> dict:
    """Compute conversation-level metrics."""
    threads = build_threads(out_df, in_df)

    n_threads = len(threads)
    thread_lengths = [len(t) for t in threads]

    if not thread_lengths:
        return {
            "n_threads": 0,
            "length_distribution": {},
            "pct_2plus_turns": 0,
            "pct_3plus_turns": 0,
            "pct_customer_then_brand": 0,
            "linkage_reliability": 0,
        }

    lengths = np.array(thread_lengths)
    pct_2plus = 100 * np.sum(lengths >= 2) / n_threads
    pct_3plus = 100 * np.sum(lengths >= 3) / n_threads

    # Percentage where a customer message is followed by a brand response
    customer_then_brand = 0
    for thread in threads:
        for j in range(len(thread) - 1):
            if thread[j]["inbound"] == "True" and thread[j + 1]["inbound"] == "False":
                customer_then_brand += 1
                break  # count per-thread, not per-pair

    pct_ctb = 100 * customer_then_brand / n_threads if n_threads else 0

    # Linkage reliability: what fraction of outbound tweets successfully
    # link back to a customer tweet we can find?
    out_with_irt = out_df["in_response_to_tweet_id"].notna().sum()
    linkage = 100 * len(in_df) / out_with_irt if out_with_irt else 0

    # Length distribution buckets
    dist = {
        "1_turn": int(np.sum(lengths == 1)),
        "2_turns": int(np.sum(lengths == 2)),
        "3_turns": int(np.sum(lengths == 3)),
        "4_turns": int(np.sum(lengths == 4)),
        "5plus_turns": int(np.sum(lengths >= 5)),
    }

    return {
        "n_threads": n_threads,
        "length_distribution": dist,
        "mean_thread_length": round(float(np.mean(lengths)), 2),
        "median_thread_length": int(np.median(lengths)),
        "max_thread_length": int(np.max(lengths)),
        "pct_2plus_turns": round(pct_2plus, 1),
        "pct_3plus_turns": round(pct_3plus, 1),
        "pct_customer_then_brand": round(pct_ctb, 1),
        "linkage_reliability_pct": round(linkage, 1),
    }


# ---------------------------------------------------------------------------
# Section C: Customer Issue Diversity (TF-IDF + n-gram)
# ---------------------------------------------------------------------------

def clean_tweet_text(text: str) -> str:
    """Basic cleaning for topic analysis."""
    if not isinstance(text, str):
        return ""
    # Remove @mentions
    text = re.sub(r"@\S+", "", text)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove non-alphanumeric (keep spaces)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def compute_issue_diversity(in_df: pd.DataFrame, brand: str,
                            n_themes: int = 15) -> dict:
    """
    Lightweight TF-IDF + n-gram analysis to surface recurring issue themes.

    Uses scikit-learn's TfidfVectorizer on customer messages directed at
    the brand.  Returns top unigrams, bigrams, and exploratory theme clusters.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    texts = in_df["text"].dropna().tolist()
    cleaned = [clean_tweet_text(t) for t in texts]
    cleaned = [t for t in cleaned if len(t) > 10]  # filter out near-empty

    if len(cleaned) < 100:
        return {"error": f"Too few customer texts ({len(cleaned)}) for analysis"}

    # TF-IDF with bigrams
    stop_words_custom = [
        "please", "help", "need", "want", "can", "get", "know", "use",
        "just", "like", "got", "would", "could", "one", "also", "still",
        "even", "much", "really", "make", "way", "back", "going", "let",
        "try", "trying", "new", "time", "day", "since", "been", "being",
        "thank", "thanks", "hi", "hey", "hello",
    ]

    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=5,
        max_df=0.3,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(cleaned)
    except ValueError as e:
        return {"error": f"TF-IDF failed: {e}"}

    feature_names = vectorizer.get_feature_names_out()

    # Get top terms by mean TF-IDF score
    mean_tfidf = np.array(tfidf_matrix.mean(axis=0)).flatten()
    top_indices = mean_tfidf.argsort()[::-1]

    # Filter out custom stop words from results
    top_unigrams = []
    top_bigrams = []
    for idx in top_indices:
        term = feature_names[idx]
        score = mean_tfidf[idx]
        # Skip custom stop words
        if term in stop_words_custom:
            continue
        if " " in term:
            if len(top_bigrams) < 30:
                top_bigrams.append((term, round(float(score), 5)))
        else:
            if len(top_unigrams) < 30:
                top_unigrams.append((term, round(float(score), 5)))
        if len(top_unigrams) >= 30 and len(top_bigrams) >= 30:
            break

    # Derive exploratory themes from top bigrams + unigrams
    # Group related terms manually into theme buckets
    themes = derive_exploratory_themes(top_unigrams, top_bigrams, n_themes)

    return {
        "n_customer_texts_analyzed": len(cleaned),
        "top_unigrams": top_unigrams[:15],
        "top_bigrams": top_bigrams[:15],
        "exploratory_themes": themes,
        "note": "These are EXPLORATORY themes from TF-IDF, NOT the final intent taxonomy.",
    }


def derive_exploratory_themes(unigrams: list, bigrams: list,
                               n_themes: int) -> list[str]:
    """
    Derive human-readable exploratory theme labels from top TF-IDF terms.

    This is a simple heuristic grouping — NOT a final intent taxonomy.
    We report the top bigrams as candidate themes, since bigrams tend
    to be more descriptive than single words.
    """
    themes = []
    seen_words = set()

    # Bigrams first (more descriptive)
    for term, score in bigrams:
        words = set(term.split())
        # Skip if too much overlap with already-seen themes
        if len(words & seen_words) > 0:
            continue
        themes.append(term)
        seen_words.update(words)
        if len(themes) >= n_themes:
            break

    # Fill remaining with unigrams if needed
    for term, score in unigrams:
        if term in seen_words:
            continue
        if len(themes) >= n_themes:
            break
        themes.append(term)
        seen_words.add(term)

    return themes


# ---------------------------------------------------------------------------
# Section D: Resolution Signal
# ---------------------------------------------------------------------------

def classify_response(text: str) -> str:
    """
    Classify a brand response into one of:
    - "substantive": contains specific troubleshooting or information
    - "dm_redirect": asks customer to DM/message privately
    - "contact_redirect": asks customer to call/email/visit website
    - "generic_greeting": greeting/apology only
    - "acknowledgement_only": simple thank-you/confirmation
    - "very_short": under 30 chars after removing @mention
    - "empty": no text
    """
    if not isinstance(text, str) or len(text.strip()) == 0:
        return "empty"

    # Remove @mention at start
    core = re.sub(r"^@\S+\s*", "", text).strip()

    if len(core) < 30:
        return "very_short"

    # Check patterns in priority order
    if GENERIC_PATTERNS["acknowledgement_only"].match(text):
        return "acknowledgement_only"
    if GENERIC_PATTERNS["dm_redirect"].search(text):
        return "dm_redirect"
    if GENERIC_PATTERNS["contact_redirect"].search(text):
        return "contact_redirect"
    if GENERIC_PATTERNS["generic_greeting"].match(text):
        return "generic_greeting"

    return "substantive"


def compute_resolution_signal(out_df: pd.DataFrame) -> dict:
    """Classify all brand responses and compute category percentages."""
    texts = out_df["text"].fillna("")
    categories = texts.apply(classify_response)
    counts = categories.value_counts().to_dict()
    total = len(categories)

    result = {}
    for cat in ["substantive", "dm_redirect", "contact_redirect",
                "generic_greeting", "acknowledgement_only", "very_short", "empty"]:
        c = counts.get(cat, 0)
        result[cat] = {"count": c, "pct": round(100 * c / total, 1) if total else 0}

    result["total"] = total
    return result


# ---------------------------------------------------------------------------
# Section E: Customer Message Quality
# ---------------------------------------------------------------------------

def compute_message_quality(in_df: pd.DataFrame) -> dict:
    """Analyze quality of customer messages."""
    texts = in_df["text"].dropna()
    n_total = len(in_df)
    n_with_text = len(texts)

    if n_with_text == 0:
        return {"error": "No customer messages with text"}

    lengths = texts.str.len()

    # Very short messages (< 20 chars after removing @mention)
    core_lengths = texts.apply(
        lambda t: len(re.sub(r"^@\S+\s*", "", t).strip()) if isinstance(t, str) else 0
    )
    very_short = (core_lengths < 20).sum()

    # Noise detection (just a mention, or one-word reply)
    noise = texts.apply(
        lambda t: bool(NOISE_PATTERNS.match(t)) if isinstance(t, str) else False
    ).sum()

    # Looks like actual support request (has a question mark, or >50 chars core)
    looks_like_request = texts.apply(
        lambda t: (
            "?" in t or
            len(re.sub(r"^@\S+\s*", "", t).strip()) > 50
        ) if isinstance(t, str) else False
    ).sum()

    # Duplicate detection (exact text after lowercasing + stripping mentions)
    normalized = texts.apply(
        lambda t: re.sub(r"@\S+", "", t).strip().lower() if isinstance(t, str) else ""
    )
    dup_counts = normalized.value_counts()
    n_unique = len(dup_counts)
    n_duplicates = int((dup_counts > 1).sum())
    duplicate_rate = round(100 * (n_with_text - n_unique) / n_with_text, 1) if n_with_text else 0

    return {
        "total_customer_tweets": n_total,
        "with_text": n_with_text,
        "char_length_mean": round(float(lengths.mean()), 1),
        "char_length_median": round(float(lengths.median()), 1),
        "char_length_std": round(float(lengths.std()), 1),
        "char_length_min": int(lengths.min()),
        "char_length_max": int(lengths.max()),
        "very_short_count": int(very_short),
        "very_short_pct": round(100 * int(very_short) / n_with_text, 1),
        "noise_count": int(noise),
        "noise_pct": round(100 * int(noise) / n_with_text, 1),
        "looks_like_request_count": int(looks_like_request),
        "looks_like_request_pct": round(100 * int(looks_like_request) / n_with_text, 1),
        "unique_texts": n_unique,
        "duplicate_texts": n_duplicates,
        "duplicate_rate_pct": duplicate_rate,
    }


# ---------------------------------------------------------------------------
# Section F: Golden Set Feasibility
# ---------------------------------------------------------------------------

def assess_golden_feasibility(issue_diversity: dict,
                               message_quality: dict,
                               conversation_stats: dict) -> dict:
    """
    Estimate whether the brand has enough diverse, high-quality messages
    for a 150–250 example golden set.
    """
    n_request_like = message_quality.get("looks_like_request_count", 0)
    n_themes = len(issue_diversity.get("exploratory_themes", []))
    pct_2plus = conversation_stats.get("pct_2plus_turns", 0)

    # Need >= 150 usable examples, ideally >= 10 per theme
    examples_per_theme = n_request_like // max(n_themes, 1)
    has_enough_volume = n_request_like >= 250
    has_enough_diversity = n_themes >= 8
    has_enough_per_theme = examples_per_theme >= 15

    feasible = has_enough_volume and has_enough_diversity

    return {
        "request_like_messages": n_request_like,
        "n_exploratory_themes": n_themes,
        "est_examples_per_theme": examples_per_theme,
        "has_enough_volume": has_enough_volume,
        "has_enough_diversity": has_enough_diversity,
        "has_enough_per_theme": has_enough_per_theme,
        "feasible": feasible,
        "verdict": "FEASIBLE" if feasible else "RISKY",
    }


# ---------------------------------------------------------------------------
# Section G: Retrieval / RAG Feasibility
# ---------------------------------------------------------------------------

def assess_rag_feasibility(data: dict, resolution: dict) -> dict:
    """
    Estimate whether the brand has enough historical (customer_issue, brand_response)
    pairs that are usable as retrieval evidence.

    A usable pair means:
    - The customer message looks like a real support request
    - The brand response is "substantive" (not a DM redirect or generic)
    """
    out_df = data["outbound"]
    in_df = data["inbound"]

    # Match outbound to inbound by in_response_to_tweet_id
    out_with_link = out_df[out_df["in_response_to_tweet_id"].notna()].copy()

    # Classify outbound responses
    out_with_link["response_type"] = out_with_link["text"].fillna("").apply(classify_response)

    substantive_out = out_with_link[out_with_link["response_type"] == "substantive"]

    # Of those, how many have a matching customer tweet?
    if not in_df.empty:
        in_ids = set(in_df["tweet_id"].tolist())
        matched_substantive = substantive_out[
            substantive_out["in_response_to_tweet_id"].isin(in_ids)
        ]
    else:
        matched_substantive = pd.DataFrame()

    n_substantive_pairs = len(matched_substantive)
    n_total_outbound = len(out_df)

    return {
        "total_outbound": n_total_outbound,
        "outbound_with_link": len(out_with_link),
        "substantive_responses": resolution.get("substantive", {}).get("count", 0),
        "substantive_pairs_with_customer_msg": n_substantive_pairs,
        "usable_pair_pct": round(
            100 * n_substantive_pairs / n_total_outbound, 1
        ) if n_total_outbound else 0,
        "feasible": n_substantive_pairs >= 500,
        "verdict": "FEASIBLE" if n_substantive_pairs >= 500 else "RISKY",
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(all_results: dict[str, dict]) -> str:
    """Generate a markdown comparison report."""
    lines = []
    lines.append("# Brand Comparison Deep-Dive Report")
    lines.append("")
    lines.append(f"Candidates: {', '.join(CANDIDATES)}")
    lines.append("")
    lines.append("> **Note**: All statistics computed locally from `data/raw/twcs/twcs.csv`.")
    lines.append("> No LLM/API calls were used. Exploratory themes are NOT final intents.")
    lines.append("")

    # ---- Per-brand detail sections ----
    for brand in CANDIDATES:
        r = all_results[brand]
        lines.append(f"---")
        lines.append(f"## {brand}")
        lines.append("")

        # A. Volume
        v = r["volume"]
        lines.append("### A. Data Volume")
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Brand outbound tweets | {v['outbound_count']:,} |")
        lines.append(f"| Linked customer tweets | {v['linked_customer_tweets']:,} |")
        lines.append(f"| Outbound with in_response_to | {v['outbound_with_irt']:,} ({v['outbound_with_irt_pct']}%) |")
        lines.append(f"| Customer->brand pairs | {v['customer_brand_pairs']:,} ({v['pair_pct_of_outbound']}% of outbound) |")
        lines.append("")

        # B. Conversation Quality
        c = r["conversation"]
        lines.append("### B. Conversation Quality")
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Total threads | {c['n_threads']:,} |")
        lines.append(f"| Mean thread length | {c.get('mean_thread_length', 'N/A')} |")
        lines.append(f"| Median thread length | {c.get('median_thread_length', 'N/A')} |")
        lines.append(f"| Max thread length | {c.get('max_thread_length', 'N/A')} |")
        lines.append(f"| >=2 turns | {c['pct_2plus_turns']}% |")
        lines.append(f"| >=3 turns | {c['pct_3plus_turns']}% |")
        lines.append(f"| Customer->Brand pattern | {c['pct_customer_then_brand']}% |")
        lines.append(f"| Linkage reliability | {c['linkage_reliability_pct']}% |")
        if c.get("length_distribution"):
            d = c["length_distribution"]
            lines.append(f"\nThread length distribution:")
            lines.append(f"| Length | Count |")
            lines.append(f"|---|---|")
            for k, count in d.items():
                lines.append(f"| {k} | {count:,} |")
        lines.append("")

        # C. Issue Diversity
        div = r["diversity"]
        lines.append("### C. Customer Issue Diversity (Exploratory)")
        lines.append(f"> [!] These are exploratory themes from TF-IDF analysis, NOT the final intent taxonomy.")
        lines.append("")
        if "error" in div:
            lines.append(f"Error: {div['error']}")
        else:
            lines.append(f"Texts analyzed: {div['n_customer_texts_analyzed']:,}")
            lines.append("")
            lines.append("**Top bigrams (by mean TF-IDF):**")
            lines.append("| Bigram | Score |")
            lines.append("|---|---|")
            for term, score in div["top_bigrams"][:15]:
                lines.append(f"| {term} | {score} |")
            lines.append("")
            lines.append("**Exploratory themes:**")
            for i, theme in enumerate(div["exploratory_themes"], 1):
                lines.append(f"{i}. {theme}")
        lines.append("")

        # D. Resolution Signal
        res = r["resolution"]
        lines.append("### D. Resolution Signal")
        lines.append(f"Total outbound: {res['total']:,}")
        lines.append("")
        lines.append(f"| Category | Count | Pct |")
        lines.append(f"|---|---|---|")
        for cat in ["substantive", "dm_redirect", "contact_redirect",
                     "generic_greeting", "acknowledgement_only", "very_short", "empty"]:
            if cat in res:
                lines.append(f"| {cat} | {res[cat]['count']:,} | {res[cat]['pct']}% |")
        lines.append("")

        # E. Message Quality
        mq = r["message_quality"]
        lines.append("### E. Customer Message Quality")
        if "error" in mq:
            lines.append(f"Error: {mq['error']}")
        else:
            lines.append(f"| Metric | Value |")
            lines.append(f"|---|---|")
            lines.append(f"| Customer tweets (with text) | {mq['with_text']:,} |")
            lines.append(f"| Mean char length | {mq['char_length_mean']} |")
            lines.append(f"| Median char length | {mq['char_length_median']} |")
            lines.append(f"| Very short (<20 chars core) | {mq['very_short_count']:,} ({mq['very_short_pct']}%) |")
            lines.append(f"| Noise (mentions/one-word) | {mq['noise_count']:,} ({mq['noise_pct']}%) |")
            lines.append(f"| Looks like support request | {mq['looks_like_request_count']:,} ({mq['looks_like_request_pct']}%) |")
            lines.append(f"| Unique texts | {mq['unique_texts']:,} |")
            lines.append(f"| Duplicate rate | {mq['duplicate_rate_pct']}% |")
        lines.append("")

        # F. Golden Set Feasibility
        gs = r["golden_feasibility"]
        lines.append("### F. Golden Set Feasibility")
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Request-like messages | {gs['request_like_messages']:,} |")
        lines.append(f"| Exploratory themes | {gs['n_exploratory_themes']} |")
        lines.append(f"| Est. examples per theme | {gs['est_examples_per_theme']:,} |")
        lines.append(f"| **Verdict** | **{gs['verdict']}** |")
        lines.append("")

        # G. RAG Feasibility
        rag = r["rag_feasibility"]
        lines.append("### G. RAG / Retrieval Feasibility")
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Outbound with linkage | {rag['outbound_with_link']:,} |")
        lines.append(f"| Substantive responses | {rag['substantive_responses']:,} |")
        lines.append(f"| Usable (customer+substantive) pairs | {rag['substantive_pairs_with_customer_msg']:,} |")
        lines.append(f"| Usable pair % of outbound | {rag['usable_pair_pct']}% |")
        lines.append(f"| **Verdict** | **{rag['verdict']}** |")
        lines.append("")

    # ---- Summary Comparison Table ----
    lines.append("---")
    lines.append("## Summary Comparison Table")
    lines.append("")

    header = "| Metric |"
    separator = "|---|"
    for brand in CANDIDATES:
        header += f" {brand} |"
        separator += "---|"
    lines.append(header)
    lines.append(separator)

    def row(label: str, key_fn):
        r = f"| {label} |"
        for brand in CANDIDATES:
            val = key_fn(all_results[brand])
            r += f" {val} |"
        return r

    lines.append(row("Outbound volume",
        lambda r: f"{r['volume']['outbound_count']:,}"))
    lines.append(row("Usable customer->brand pairs",
        lambda r: f"{r['volume']['customer_brand_pairs']:,}"))
    lines.append(row("Total threads",
        lambda r: f"{r['conversation']['n_threads']:,}"))
    lines.append(row(">=2 turn conv. rate",
        lambda r: f"{r['conversation']['pct_2plus_turns']}%"))
    lines.append(row(">=3 turn conv. rate",
        lambda r: f"{r['conversation']['pct_3plus_turns']}%"))
    lines.append(row("Substantive response rate",
        lambda r: f"{r['resolution'].get('substantive', {}).get('pct', 'N/A')}%"))
    lines.append(row("DM redirect rate",
        lambda r: f"{r['resolution'].get('dm_redirect', {}).get('pct', 'N/A')}%"))
    lines.append(row("Issue themes found",
        lambda r: str(len(r['diversity'].get('exploratory_themes', [])))))
    lines.append(row("Duplicate/noise rate",
        lambda r: f"{r['message_quality'].get('duplicate_rate_pct', 'N/A')}%"))
    lines.append(row("Looks like request %",
        lambda r: f"{r['message_quality'].get('looks_like_request_pct', 'N/A')}%"))
    lines.append(row("Golden set verdict",
        lambda r: r['golden_feasibility']['verdict']))
    lines.append(row("RAG verdict",
        lambda r: r['rag_feasibility']['verdict']))

    lines.append("")

    # ---- Recommendation ----
    lines.append("---")
    lines.append("## Data-Driven Recommendation")
    lines.append("")
    lines.append("*(Auto-generated from the metrics above — final brand selection")
    lines.append("should be reviewed by a human.)*")
    lines.append("")

    # Simple scoring
    scores = {}
    for brand in CANDIDATES:
        r = all_results[brand]
        score = 0
        # Volume (more is better, diminishing returns)
        score += min(r["volume"]["customer_brand_pairs"] / 10000, 5)
        # Multi-turn rate
        score += r["conversation"]["pct_2plus_turns"] / 20
        # 3+ turn rate
        score += r["conversation"]["pct_3plus_turns"] / 20
        # Substantive response rate
        sub_pct = r["resolution"].get("substantive", {}).get("pct", 0)
        score += sub_pct / 20
        # Issue diversity
        n_themes = len(r["diversity"].get("exploratory_themes", []))
        score += n_themes / 3
        # Low noise
        noise = r["message_quality"].get("noise_pct", 50)
        score += max(0, (100 - noise) / 20)
        # Golden feasibility
        if r["golden_feasibility"]["feasible"]:
            score += 2
        # RAG feasibility
        if r["rag_feasibility"]["feasible"]:
            score += 2

        scores[brand] = round(score, 2)

    for brand in CANDIDATES:
        lines.append(f"- **{brand}**: composite score = {scores[brand]}")

    best = max(scores, key=scores.get)
    lines.append("")
    lines.append(f"**Recommendation: {best}** appears strongest based on the combined metrics.")
    lines.append("")
    lines.append("This recommendation should be validated by reviewing:")
    lines.append("1. The sample messages and themes for domain familiarity")
    lines.append("2. Whether the exploratory themes map to distinct, labelable intents")
    lines.append("3. Whether the substantive responses contain actual resolution info")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found at {DATASET_PATH.resolve()}")
        sys.exit(1)

    print(f"Dataset: {DATASET_PATH}")
    print(f"Candidates: {CANDIDATES}")
    print(f"{'=' * 70}\n")

    # Collect data for all candidates
    all_data = collect_brand_data(DATASET_PATH, CANDIDATES)

    # Analyze each brand
    all_results = {}
    for brand in CANDIDATES:
        print(f"\n{'=' * 70}")
        print(f"  Analyzing: {brand}")
        print(f"{'=' * 70}")

        data = all_data[brand]
        out_df = data["outbound"]
        in_df = data["inbound"]

        print("  [A] Volume stats...")
        volume = compute_volume_stats(brand, data)
        print(f"      Outbound: {volume['outbound_count']:,}, "
              f"Pairs: {volume['customer_brand_pairs']:,}")

        print("  [B] Conversation quality...")
        conversation = compute_conversation_stats(out_df, in_df)
        print(f"      Threads: {conversation['n_threads']:,}, "
              f">=2 turns: {conversation['pct_2plus_turns']}%")

        print("  [C] Issue diversity (TF-IDF)...")
        diversity = compute_issue_diversity(in_df, brand)
        n_themes = len(diversity.get("exploratory_themes", []))
        print(f"      Found {n_themes} exploratory themes")

        print("  [D] Resolution signal...")
        resolution = compute_resolution_signal(out_df)
        sub_pct = resolution.get("substantive", {}).get("pct", 0)
        print(f"      Substantive: {sub_pct}%")

        print("  [E] Message quality...")
        message_quality = compute_message_quality(in_df)
        req_pct = message_quality.get("looks_like_request_pct", 0)
        print(f"      Request-like: {req_pct}%")

        print("  [F] Golden set feasibility...")
        golden = assess_golden_feasibility(diversity, message_quality, conversation)
        print(f"      Verdict: {golden['verdict']}")

        print("  [G] RAG feasibility...")
        rag = assess_rag_feasibility(data, resolution)
        print(f"      Usable pairs: {rag['substantive_pairs_with_customer_msg']:,} -- {rag['verdict']}")

        all_results[brand] = {
            "volume": volume,
            "conversation": conversation,
            "diversity": diversity,
            "resolution": resolution,
            "message_quality": message_quality,
            "golden_feasibility": golden,
            "rag_feasibility": rag,
        }

    # Generate report
    print(f"\n{'=' * 70}")
    print("Generating comparison report...")
    report = generate_report(all_results)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Report saved to: {OUTPUT_PATH.resolve()}")

    # Also save raw JSON for reproducibility
    json_path = EXPERIMENTS_DIR / "brand_comparison_raw.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert numpy types for JSON serialization
    def convert(obj):
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            return float(obj)
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return str(obj)

    json_path.write_text(
        json.dumps(all_results, indent=2, default=convert),
        encoding="utf-8",
    )
    print(f"Raw data saved to: {json_path.resolve()}")

    # Print the summary comparison table to stdout
    print(f"\n{'=' * 70}")
    print("SUMMARY COMPARISON TABLE")
    print(f"{'=' * 70}\n")

    # Extract and print just the table section
    table_start = report.index("## Summary Comparison Table")
    table_end = report.index("## Data-Driven Recommendation")
    print(report[table_start:table_end])

    rec_start = report.index("## Data-Driven Recommendation")
    print(report[rec_start:])


if __name__ == "__main__":
    main()

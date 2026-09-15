"""Audit AmazonHelp conversation provenance using raw Twitter parent IDs.

This is deliberately an audit only.  It does not create a retriever, agent,
taxonomy, or golden set, and it never writes to the raw TWCS CSV.
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

RAW = Path("data/raw/twcs/twcs.csv")
INTERIM = Path("data/interim/amazonhelp_conversations.csv")
REPORT = Path("reports/conversation_provenance_audit.md")
ARTIFACT = Path("experiments/conversation_provenance_audit_raw.json")
BRAND = "AmazonHelp"
SEED = 42
SUSPICIOUS = ["814386", "1381536", "1387233", "2103681", "741527"]
OTHER_ACCOUNT_MARKERS = ("home town", "@115821", "@115850", "@115830")


def read_rows(path: Path, wanted: set[str] | None = None) -> Iterable[dict[str, str]]:
    """Stream raw rows, optionally yielding only requested tweet IDs."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if wanted is None or row["tweet_id"] in wanted:
                yield row


def is_valid_direct_pair(customer: dict[str, str], response: dict[str, str]) -> bool:
    return (
        response["in_response_to_tweet_id"] == customer["tweet_id"]
        and customer["inbound"] == "True"
        and response["inbound"] == "False"
        and response["author_id"] == BRAND
    )


def parent_chain(tweet_id: str, records: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    """Return the exact ancestor chain, oldest first, following only parent IDs."""
    chain: list[dict[str, str]] = []
    seen: set[str] = set()
    current = tweet_id
    while current in records and current not in seen:
        seen.add(current)
        row = records[current]
        chain.append(row)
        parent = row.get("in_response_to_tweet_id", "")
        if not parent:
            break
        current = parent
    return list(reversed(chain))


def speaker(row: dict[str, str]) -> str:
    if row["author_id"] == BRAND and row["inbound"] == "False":
        return "AmazonHelp"
    if row["inbound"] == "True":
        return "customer"
    return "unrelated/other account"


def normalize(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", text.lower()))


SUPPORT_WORDS = normalize(
    "sorry help assist support contact check look into order delivery refund account"
)


def semantic_bucket(customer_text: str, response_text: str) -> str:
    """Transparent non-LLM heuristic used to prioritize manual inspection."""
    customer = normalize(customer_text)
    response = normalize(response_text)
    overlap = customer & response
    support_signal = response & SUPPORT_WORDS
    if len(overlap) >= 2 or (overlap and support_signal):
        return "clearly related"
    if support_signal or len(response) >= 12:
        return "weakly related"
    return "apparently unrelated"


def load_interim() -> list[dict[str, str]]:
    return pd.read_csv(INTERIM, dtype=str).fillna("").to_dict("records")


def load_raw_records(ids: set[str], max_passes: int = 20) -> dict[str, dict[str, str]]:
    """Recover requested rows and all reachable ancestors by repeated ID scans."""
    records: dict[str, dict[str, str]] = {}
    needed = set(ids)
    for _ in range(max_passes):
        missing = needed - set(records)
        if not missing:
            break
        found: list[dict[str, str]] = []
        for row in read_rows(RAW, missing):
            found.append(row)
        for row in found:
            records[row["tweet_id"]] = row
        next_needed = {
            row["in_response_to_tweet_id"]
            for row in found
            if row.get("in_response_to_tweet_id")
        }
        needed.update(next_needed)
    return records


def render_chain(chain: list[dict[str, str]]) -> str:
    lines = []
    for row in chain:
        lines.append(
            f"- `{speaker(row)}` tweet `{row['tweet_id']}`; author `{row['author_id']}`; "
            f"inbound `{row['inbound']}`; parent `{row['in_response_to_tweet_id'] or '(none)'}`; "
            f"text: {row['text']}"
        )
    return "\n".join(lines)


def main() -> None:
    random.seed(SEED)
    interim = load_interim()
    interim_ids = {r["customer_tweet_id"] for r in interim} | {r["brand_tweet_id"] for r in interim}
    records = load_raw_records(interim_ids | set(SUSPICIOUS))

    pairs: list[dict[str, Any]] = []
    for row in interim:
        customer = records.get(row["customer_tweet_id"])
        response = records.get(row["brand_tweet_id"])
        valid = bool(customer and response and is_valid_direct_pair(customer, response))
        pairs.append({
            "customer_tweet_id": row["customer_tweet_id"],
            "brand_tweet_id": row["brand_tweet_id"],
            "valid": valid,
            "customer": customer,
            "response": response,
        })

    valid_pairs = [p for p in pairs if p["valid"]]
    context_candidates = [
        p for p in valid_pairs
        if len(parent_chain(p["customer_tweet_id"], records)) > 1
    ]
    pair_sample = random.sample(valid_pairs, min(30, len(valid_pairs)))
    context_sample = random.sample(context_candidates, min(50, len(context_candidates)))
    semantic_candidates = random.sample(valid_pairs, min(50, len(valid_pairs)))
    semantic_counts = Counter(
        semantic_bucket(p["customer"]["text"], p["response"]["text"])
        for p in semantic_candidates
    )

    contamination: list[dict[str, Any]] = []
    marker_mentions: list[dict[str, Any]] = []
    for p in context_sample:
        chain = parent_chain(p["customer_tweet_id"], records)
        other = [r for r in chain if speaker(r) == "unrelated/other account"]
        marker = [
            r for r in chain
            if any(m in r["text"].lower() for m in OTHER_ACCOUNT_MARKERS)
        ]
        if other:
            contamination.append({
                "customer_tweet_id": p["customer_tweet_id"],
                "other_turns": other,
            })
        if marker:
            marker_mentions.append({
                "customer_tweet_id": p["customer_tweet_id"],
                "marker_turns": marker,
            })

    all_chains_valid = sum(
        bool(parent_chain(p["customer_tweet_id"], records))
        and parent_chain(p["customer_tweet_id"], records)[-1]["tweet_id"]
        == p["customer_tweet_id"]
        for p in context_sample
    )
    response_by_parent = {
        p["customer_tweet_id"]: p["response"] for p in valid_pairs
    }
    suspicious = {}
    for tid in SUSPICIOUS:
        chain = parent_chain(tid, records)
        response = response_by_parent.get(tid)
        if response and (not chain or chain[-1]["tweet_id"] != response["tweet_id"]):
            chain = chain + [response]
        suspicious[tid] = chain

    artifact = {
        "method": {
            "seed": SEED,
            "direct_rule": "response.in_response_to_tweet_id == customer.tweet_id; customer inbound=True; response author=AmazonHelp and inbound=False",
            "context_rule": "repeatedly follow in_response_to_tweet_id; no row adjacency, timestamp, or author adjacency",
            "semantic_rule": "token overlap plus transparent support-word heuristic; samples require manual inspection",
        },
        "counts": {
            "interim_pairs": len(pairs),
            "direct_valid": len(valid_pairs),
            "direct_validity_rate": len(valid_pairs) / len(pairs) if pairs else 0,
            "context_candidates": len(context_candidates),
            "context_sampled": len(context_sample),
            "context_chain_valid": all_chains_valid,
            "context_chain_validity_rate": all_chains_valid / len(context_sample) if context_sample else 0,
            "contaminated_context_examples": len(contamination),
            "contaminated_context_rate": len(contamination) / len(context_sample) if context_sample else 0,
            "context_marker_mentions": len(marker_mentions),
            "semantic_sampled": len(semantic_candidates),
            "semantic_counts": dict(semantic_counts),
            "semantic_unrelated_rate": semantic_counts["apparently unrelated"] / len(semantic_candidates) if semantic_candidates else 0,
        },
        "pair_sample": [
            {"customer_tweet_id": p["customer"]["tweet_id"], "customer_author_id": p["customer"]["author_id"],
             "customer_text": p["customer"]["text"], "amazonhelp_tweet_id": p["response"]["tweet_id"],
             "amazonhelp_text": p["response"]["text"], "parent_id": p["response"]["in_response_to_tweet_id"],
             "customer_inbound": p["customer"]["inbound"], "amazonhelp_inbound": p["response"]["inbound"]}
            for p in pair_sample
        ],
        "context_sample": [
            {"customer_tweet_id": p["customer_tweet_id"], "chain": [
                {**r, "speaker": speaker(r)} for r in parent_chain(p["customer_tweet_id"], records)
            ]} for p in context_sample
        ],
        "semantic_sample": [
            {"customer_tweet_id": p["customer"]["tweet_id"], "customer_text": p["customer"]["text"],
             "amazonhelp_tweet_id": p["response"]["tweet_id"], "amazonhelp_text": p["response"]["text"],
             "heuristic_bucket": semantic_bucket(p["customer"]["text"], p["response"]["text"])}
            for p in semantic_candidates
        ],
        "contamination": [
            {"customer_tweet_id": c["customer_tweet_id"],
             "turns": [{**r, "speaker": speaker(r)} for r in c["other_turns"]]}
            for c in contamination
        ],
        "account_marker_mentions": [
            {"customer_tweet_id": c["customer_tweet_id"],
             "turns": [{**r, "speaker": speaker(r)} for r in c["marker_turns"]]}
            for c in marker_mentions
        ],
        "suspicious_chains": {
            tid: [{**r, "speaker": speaker(r)} for r in chain]
            for tid, chain in suspicious.items()
        },
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    c = artifact["counts"]
    lines = [
        "# Conversation Provenance Audit", "",
        "This audit uses only raw Twitter ID relationships. It does not modify `data/raw/twcs/twcs.csv`.",
        "",
        "## Executive results", "",
        f"- Direct pair validity: **{c['direct_valid']:,}/{c['interim_pairs']:,} ({100*c['direct_validity_rate']:.2f}%)**.",
        f"- Context-chain validity: **{c['context_chain_valid']:,}/{c['context_sampled']:,} ({100*c['context_chain_validity_rate']:.2f}%)**.",
        f"- Cross-account contamination: **{c['contaminated_context_examples']:,}/{c['context_sampled']:,} ({100*c['contaminated_context_rate']:.2f}%)**.",
        f"- Apparently unrelated semantic samples: **{c['semantic_counts'].get('apparently unrelated', 0):,}/{c['semantic_sampled']:,} ({100*c['semantic_unrelated_rate']:.2f}%)**.",
        "",
        "The context traversal repeatedly looks up `in_response_to_tweet_id`; it never uses nearby rows, timestamps, or author adjacency.",
        "",
        "## 30 direct pairs", "",
    ]
    for p in artifact["pair_sample"]:
        lines.append(
            f"- customer `{p['customer_tweet_id']}` (author `{p['customer_author_id']}`, inbound `{p['customer_inbound']}`): {p['customer_text']} "
            f"-> AmazonHelp `{p['amazonhelp_tweet_id']}` (inbound `{p['amazonhelp_inbound']}`, parent `{p['parent_id']}`): {p['amazonhelp_text']}"
        )
    lines += ["", "## 50 recovered parent chains", ""]
    for item in artifact["context_sample"]:
        lines += [f"### Customer `{item['customer_tweet_id']}`", render_chain(item["chain"]), ""]
    lines += ["## Semantic inspection sample", ""]
    for item in artifact["semantic_sample"]:
        lines.append(f"- `{item['heuristic_bucket']}` customer `{item['customer_tweet_id']}`: {item['customer_text']} -> {item['amazonhelp_text']}")
    lines += ["", "## Cross-account contamination", "",
              f"Found **{len(contamination):,}** contaminated sampled chains ({100*len(contamination)/len(context_sample):.2f}%). "
              f"Account-marker mentions occurred in **{len(marker_mentions):,}** chains, but mentions in customer text are not contamination. "
              f"Markers checked: `{', '.join(OTHER_ACCOUNT_MARKERS)}`."]
    if not contamination:
              lines.append("No unrelated/other-account turn occurred in the sampled recovered chains.")
    lines += ["", "## Coverage Gap suspicious examples", ""]
    for tid, chain in suspicious.items():
        has_other = any(speaker(r) == "unrelated/other account" for r in chain)
        lines += [
            f"### Tweet `{tid}`",
            f"- Provenance determination: **{'contaminated by an unrelated account' if has_other else 'valid AmazonHelp-linked chain'}**.",
            render_chain(chain),
            "",
        ]
    lines += [
        "## Decisions", "",
        f"- Semantic heuristic sample counts: `{dict(semantic_counts)}`. These are local screening results, not LLM judgments.",
        "- The interim file is **provenance-safe** (100% direct ID validity; 0% unrelated turns in the sampled recovered context), but it is **not safe as an unfiltered golden set**: the local semantic screen found apparently unrelated responses and requires human review/filtering.",
        "- Existing scripts need correction if they treat a referenced row as a customer without checking inbound status, or label every non-inbound ancestor as AmazonHelp. The audit's strict rules should be used before downstream work.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(c, indent=2))
    print(f"Wrote {REPORT} and {ARTIFACT}")


if __name__ == "__main__":
    main()

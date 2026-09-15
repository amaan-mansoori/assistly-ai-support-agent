"""Reproducibly sample human-annotation candidates from validated pairs."""
from __future__ import annotations
import csv, hashlib, json, random, re
from collections import Counter
from pathlib import Path
from typing import Any
import pandas as pd
from src.intents.final_taxonomy_audit import classify_intent

RAW = Path("data/raw/twcs/twcs.csv")
INTERIM = Path("data/interim/amazonhelp_conversations.csv")
OUTPUT = Path("data/golden/golden_candidates.csv")
REPORT = Path("reports/golden_set_sampling.md")
SEED, POOL_TARGET = 42, 500
TARGETS = {"delivery_status_delay":25,"delivery_marked_delivered_missing":25,"return_refund":25,
 "item_condition_or_fulfilment":25,"order_cancellation_or_change":15,"prime_membership":20,
 "account_access_security":15,"payment_charge_issue":15,"product_availability_pricing":15,
 "marketplace_seller":10,"other_unclear":30}

def clean_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"@\S+|https?://\S+", "", text.lower())).strip()

def load_raw(ids: set[str]) -> dict[str, dict[str, str]]:
    with RAW.open("r", encoding="utf-8", newline="") as f:
        return {r["tweet_id"]: r for r in csv.DictReader(f) if r["tweet_id"] in ids}

def recover_records(ids: set[str]) -> dict[str, dict[str, str]]:
    records = load_raw(ids)
    needed = {r["in_response_to_tweet_id"] for r in records.values() if r.get("in_response_to_tweet_id")}
    for _ in range(12):
        missing = needed - set(records)
        if not missing: break
        found = load_raw(missing)
        records.update(found)
        needed.update(r["in_response_to_tweet_id"] for r in found.values() if r.get("in_response_to_tweet_id"))
    return records

def chain(tweet_id: str, records: dict[str, dict[str, str]], limit: int = 4) -> list[dict[str, str]]:
    out, current, seen = [], records.get(tweet_id, {}), set()
    parent = current.get("in_response_to_tweet_id", "")
    while parent and parent in records and parent not in seen and len(out) < limit:
        seen.add(parent); row = records[parent]
        role = "AmazonHelp" if row["author_id"] == "AmazonHelp" and row["inbound"] == "False" else ("customer" if row["inbound"] == "True" else "unrelated/other account")
        out.append({"tweet_id": row["tweet_id"], "author_id": row["author_id"], "role": role, "text": row["text"]})
        parent = row.get("in_response_to_tweet_id", "")
    return list(reversed(out))

def context_text(turns: list[dict[str, str]]) -> str:
    return "\n".join(f"[{t['role']} {t['tweet_id']}] {t['text']}" for t in turns)

def choose(rows: list[dict[str, Any]], quota: int, seed: int) -> list[dict[str, Any]]:
    unique = {}
    for row in rows: unique.setdefault(clean_key(row["customer_text"]), row)
    return sorted(unique.values(), key=lambda r: hashlib.sha256(f"{seed}:{r['customer_tweet_id']}".encode()).hexdigest())[:quota]

def main() -> None:
    interim = pd.read_csv(INTERIM, dtype=str).fillna("")
    interim["clean_key"] = interim["customer_text"].map(clean_key)
    interim = interim[interim["clean_key"].str.len() > 0].drop_duplicates("clean_key")
    english = interim[interim["customer_text"].str.contains(r"[A-Za-z]", regex=True)]
    records = recover_records(set(english["customer_tweet_id"]) | set(english["brand_tweet_id"]))
    candidates = []
    for row in english.to_dict("records"):
        customer, response = records.get(row["customer_tweet_id"]), records.get(row["brand_tweet_id"])
        if not customer or not response or not (customer["inbound"] == "True" and response["author_id"] == "AmazonHelp" and response["inbound"] == "False" and response["in_response_to_tweet_id"] == customer["tweet_id"]): continue
        turns, candidate = chain(customer["tweet_id"], records), classify_intent(customer["text"])
        context_customer = " ".join(t["text"] for t in turns if t["role"] == "customer")
        candidates.append({"customer_tweet_id":customer["tweet_id"],"customer_author_id":customer["author_id"],"customer_text":customer["text"],"conversation_context":context_text(turns),"amazonhelp_response":response["text"],"timestamp":customer["created_at"],"candidate_stratum":candidate,"human_intent":"","annotation_notes":"","source_provenance_ids":f"customer:{customer['tweet_id']};response:{response['tweet_id']};parents:{','.join(t['tweet_id'] for t in turns)}","context_available":bool(turns),"context_dependent_candidate":bool(turns and classify_intent(context_customer+" "+customer["text"]) != candidate)})
    by = {k: [] for k in TARGETS}
    for row in candidates: by.setdefault(row["candidate_stratum"], []).append(row)
    selected, shortages = [], {}
    for stratum, target in TARGETS.items():
        picked = choose(by.get(stratum, []), target * 2, SEED); selected.extend(picked); shortages[stratum] = max(0, target * 2 - len(picked))
    selected_ids = {r["customer_tweet_id"] for r in selected}
    selected.extend(choose([r for r in candidates if r["customer_tweet_id"] not in selected_ids], POOL_TARGET-len(selected), SEED+1))
    selected = selected[:POOL_TARGET]
    counts = Counter(r["candidate_stratum"] for r in selected)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["example_id","customer_tweet_id","customer_author_id","customer_text","conversation_context","amazonhelp_response","timestamp","candidate_stratum","human_intent","annotation_notes","source_provenance_ids","context_available","context_dependent_candidate"]
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for i, row in enumerate(selected, 1): w.writerow({"example_id":f"golden-candidate-{i:04d}", **row})
    context_count = sum(r["context_available"] for r in selected); ambiguous = sum(r["context_dependent_candidate"] for r in selected)
    report = f"""# Golden-Set Candidate Sampling

This is a reproducible, annotation-ready pool from validated customer→AmazonHelp pairs. Raw records are linked only through `in_response_to_tweet_id`; the raw TWCS CSV is never modified. English eligibility uses a conservative ASCII-letter gate because the interim file has no language column. Customer text is normalized (mentions, URLs, case, whitespace) and exact normalized duplicates are removed.

`candidate_stratum` is produced by the existing local regex taxonomy only as a sampling aid, **not ground truth**. `human_intent` and `annotation_notes` are blank. The final golden set must be hand-labelled by a human.

## Counts
- Eligible English inquiries after deduplication: **{len(english):,}**
- Valid linked candidates: **{len(candidates):,}**
- Candidate pool: **{len(selected):,}**
- Recoverable preceding context: **{context_count:,}/{len(selected):,}**
- Context-dependent/ambiguous candidates: **{ambiguous:,}/{len(selected):,}**
- Seed: **{SEED}**

## Actual sampled counts
{chr(10).join(f"- `{k}`: **{counts.get(k,0)}** (2× target quota {TARGETS[k]*2})" for k in TARGETS)}

Quota shortages: `{shortages}`. No synthetic, duplicated, or automatically hand-labelled examples were added.

## Why 220 annotations
The 220-example target covers every proposed task intent and `other_unclear` while remaining feasible for human annotation. A 500-row pool provides choice, rare-intent oversampling, diversity, and context-dependent cases. It is not a prevalence estimate and may contain selection bias.

## Limitations
The English gate can exclude multilingual variants; regex strata have blind spots; context is limited to four actual parent hops and available rows. Human review is required before any row becomes a golden label.
"""
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({"eligible_english":len(english),"valid_candidates":len(candidates),"pool_size":len(selected),"counts":dict(counts),"context_available":context_count,"ambiguous":ambiguous}, indent=2))

if __name__ == "__main__": main()

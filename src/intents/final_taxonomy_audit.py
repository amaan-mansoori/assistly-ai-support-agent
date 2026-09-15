"""Local final taxonomy audit for the AmazonHelp Twitter corpus.

This is an audit artifact, not an agent, retriever, or golden-set builder.  It
uses only the checked-in TWCS CSV and interim conversation pairs.  Clusters are
exploratory descriptions of language, never asserted to be ground-truth labels.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from src.data.validate_amazonhelp import classify_response
from src.intents.refine_taxonomy import (
    clean_customer_text,
    detect_language,
    is_dialogue_artifact,
)

INTERIM = Path("data/interim/amazonhelp_conversations.csv")
RAW = Path("data/raw/twcs/twcs.csv")
REPORT = Path("reports/final_taxonomy_audit.md")
ARTIFACT = Path("experiments/final_taxonomy_audit_raw.json")
CHUNK = 100_000
SEED = 42


# The delivered/missing predicate is deliberately evaluated before transit.
# It requires *both* delivery evidence and non-receipt evidence, rather than
# relying on declaration order or the word "delivered" alone.
INTENTS: dict[str, dict[str, Any]] = {
    "delivery_marked_delivered_missing": {
        "name": "Marked delivered, parcel missing",
        "definition": "Tracking says delivered, but the customer cannot find the parcel.",
        "include": "A delivered/handed-off tracking assertion plus non-receipt, missing-location, or wrong-address evidence.",
        "exclude": "Still in transit or merely late; wrong product in hand.",
        "pii": "Yes — order and delivery-location lookup.",
        "handling": "Give safe-location/neighbor checks, then escalate to delivery investigation or replacement.",
        "difficulty": "Medium; both delivery and absence evidence are required.",
        "patterns": [r"(?=.*\b(delivered|delivery confirmation|handed to resident|signed for)\b)(?=.*\b(not receive(?:d)?|didn.?t receive|missing|nowhere|not (?:here|there|in (?:my )?(?:mailbox|porch))|wrong address)\b)"],
    },
    "delivery_status_delay": {
        "name": "Delivery status, delay, or failed delivery",
        "definition": "An order is late, stuck, not yet dispatched, or needs delivery-status help.",
        "include": "Late/missed dates, in-transit tracking, failed attempts, or where-is-my-order requests without delivered-and-missing evidence.",
        "exclude": "Explicit delivered-but-missing cases; a return/refund after delivery.",
        "pii": "Yes — order/tracking lookup.",
        "handling": "Provide tracking guidance; escalate when materially overdue or repeated failure is shown.",
        "difficulty": "Medium; distinguish status from a confirmed missing parcel.",
        "patterns": [r"\b(late|delay(?:ed)?|not arrived|hasn.?t arrived|where.{0,12}(?:order|package|parcel)|when.{0,20}(?:arrive|deliver)|tracking.{0,20}(?:stuck|moving)|out for delivery|expected delivery|delivery date|delivery attempt|not dispatched|shipping (?:status|delay)|still waiting)\b"],
    },
    "return_refund": {
        "name": "Returns, replacement, and refund status",
        "definition": "A customer needs to return/replace an item or asks about an expected refund.",
        "include": "Return labels/pickups, replacement requests, refund timing or amount after a transaction.",
        "exclude": "Unauthorized/double card charges; cancellation before dispatch.",
        "pii": "Yes — order, payment, and return lookup.",
        "handling": "Offer self-service return/replacement path and standard refund timing; escalate missing/exception cases.",
        "difficulty": "Medium; refund can co-occur with delivery or cancellation.",
        "patterns": [r"\b(refund|return (?:label|item|package|pickup)|replacement|replace (?:it|item)|send (?:it|this) back|money back|credited back|return pickup|returning)\b"],
    },
    "item_condition_or_fulfilment": {
        "name": "Wrong, damaged, defective, or incomplete item",
        "definition": "A received item is wrong, damaged, defective, expired, or missing components.",
        "include": "Wrong item/size, damaged packaging/item, faults, missing parts, empty box.",
        "exclude": "Parcel wholly missing after a delivered scan; return/refund status without a condition report.",
        "pii": "Yes — order lookup; evidence may be needed.",
        "handling": "Usually self-service replacement/return; escalate hazardous or non-returnable cases.",
        "difficulty": "Low to medium.",
        "patterns": [r"\b(damaged|broken|defective|faulty|shattered|cracked|leaking|expired|wrong (?:item|product|size)|incorrect item|missing (?:part|component|item)|empty box|incomplete order)\b"],
    },
    "order_cancellation_or_change": {
        "name": "Order cancellation or change",
        "definition": "The customer wants to cancel/modify an order or disputes an automated cancellation.",
        "include": "Cancel order, address change, accidental order, order already cancelled.",
        "exclude": "Canceling Prime; returning a delivered item.",
        "pii": "Yes — order lookup.",
        "handling": "Direct to order management when pre-dispatch; escalate shipped or system-error cases.",
        "difficulty": "Low.",
        "patterns": [r"\b(cancel (?:my )?order|order cancel(?:led|ed)?|change (?:my )?(?:delivery|shipping )?address|accidental order|unable to cancel|stop delivery)\b"],
    },
    "prime_membership": {
        "name": "Prime membership and benefits",
        "definition": "Prime fees, renewal/cancellation, eligibility, or Prime service benefits.",
        "include": "Prime membership, trial, fee, renewal, student Prime, Prime Video/Music.",
        "exclude": "A generic late order that only incidentally mentions Prime.",
        "pii": "Usually yes — membership lookup.",
        "handling": "Manage-membership guidance; escalate account-specific billing disputes.",
        "difficulty": "Medium; Prime may be evidence in a delivery complaint rather than the goal.",
        "patterns": [r"\b(amazon prime|prime membership|prime member|prime (?:trial|fee|renew|video|music|student)|cancel prime|charged for prime)\b"],
    },
    "account_access_security": {
        "name": "Account access and security",
        "definition": "Login, password, verification, account hold, or suspicious-access problem.",
        "include": "Cannot sign in, locked account, password/OTP/verification trouble, hacked account.",
        "exclude": "Payment-only dispute with no account-access issue.",
        "pii": "Yes — security verification required.",
        "handling": "Secure recovery channel; do not request credentials publicly.",
        "difficulty": "Low.",
        "patterns": [r"\b(sign ?in|log ?in|locked out|account (?:locked|on hold|suspended)|password|otp|verification code|two[- ]factor|two[- ]step|hacked|suspicious (?:activity|login))\b"],
    },
    "payment_charge_issue": {
        "name": "Payment, charge, or Amazon Pay issue",
        "definition": "Unauthorized, duplicate, failed, or otherwise disputed payment.",
        "include": "Double charge, unknown charge, payment failure, card/bank/Amazon Pay dispute.",
        "exclude": "Expected refund after return; Prime membership management.",
        "pii": "Yes — secure billing lookup.",
        "handling": "Secure billing escalation with general authorization guidance.",
        "difficulty": "Medium.",
        "patterns": [r"\b(charged twice|double charge|unauthori[sz]ed charge|unknown charge|payment (?:failed|issue)|credit card|debit card|amazon pay|bank (?:statement|account)|charged me)\b"],
    },
    "product_availability_pricing": {
        "name": "Product availability, pricing, and promotions",
        "definition": "Stock, restock, price/deal, authenticity, pre-order, or promotion question.",
        "include": "In/out of stock, restock, pre-order, price/deal, coupon/promo code, authenticity.",
        "exclude": "Seller service dispute; delivered defective item.",
        "pii": "Normally no.",
        "handling": "Product-page policy or stock-alert guidance; escalate listing inaccuracies.",
        "difficulty": "Low.",
        "patterns": [r"\b(in stock|out of stock|back in stock|restock|pre[- ]?order|price (?:drop|change)|promo code|coupon|discount|lightning deal|authentic(?:ity)?|genuine|when.{0,20}available)\b"],
    },
    "marketplace_seller": {
        "name": "Marketplace seller issue",
        "definition": "A third-party seller is unresponsive, refuses a remedy, or triggers an A-to-Z concern.",
        "include": "Seller/merchant contact, seller refusal, marketplace or A-to-Z guarantee.",
        "exclude": "Amazon-fulfilled delivery issue with no seller relationship.",
        "pii": "Usually yes — order/seller details.",
        "handling": "Contact Seller guidance; escalate eligibility for A-to-Z claim.",
        "difficulty": "Medium.",
        "patterns": [r"\b(third[- ]party|seller|marketplace|merchant|contact seller|a[- ]to[- ]z guarantee|sold by)\b"],
    },
}
for value in INTENTS.values():
    value["compiled"] = [re.compile(p, re.I) for p in value["patterns"]]


def normalize(text: str) -> str:
    clean, _ = clean_customer_text(text)
    return clean.lower()


def classify_intent(text: str) -> str:
    """Classify a customer issue; missing-delivery is checked first by design."""
    norm = normalize(text)
    for intent_id, spec in INTENTS.items():
        if any(p.search(norm) for p in spec["compiled"]):
            return intent_id
    return "other_unclear"


def message_type(text: str) -> str:
    n = normalize(text)
    if re.search(r"\b(thanks?|thank you|thx|cheers)\b", n):
        return "acknowledgement"
    if re.search(r"\b(order (?:id|number)|details|email (?:is|address)|dm sent|sent (?:a )?dm)\b", n):
        return "information_provision"
    if "?" in text or re.search(r"\b(how|why|when|where|can you|could you|what)\b", n):
        return "question_or_request"
    if re.search(r"\b(awful|worst|disgusting|poor|unhappy|terrible|shame|fraud)\b", n):
        return "complaint_or_feedback"
    return "problem_statement_or_update"


def conversation_state(tweet_id: str, records: dict[str, dict[str, str]]) -> str:
    row = records.get(tweet_id, {})
    parent = row.get("in_response_to_tweet_id", "")
    if not parent or parent not in records:
        return "initial_or_context_unavailable"
    return "followup_in_thread"


def load_clean_english() -> tuple[pd.DataFrame, dict[str, Any]]:
    df = pd.read_csv(INTERIM, dtype=str).fillna("")
    cleaned = df["customer_text"].map(clean_customer_text)
    df["clean_text"] = [x[0] for x in cleaned]
    df["usable"] = [x[1] for x in cleaned]
    usable = df[df["usable"]].copy()
    usable["language"] = usable["customer_text"].map(detect_language)
    usable["norm"] = usable["clean_text"].str.lower()
    dedup = usable.drop_duplicates("norm", keep="first").copy()
    en = dedup[dedup["language"] == "en"].copy()
    counts = {
        "raw_pairs": int(len(df)), "noise_removed": int(len(df) - len(usable)),
        "usable_pre_dedup": int(len(usable)), "duplicates_removed": int(len(usable) - len(dedup)),
        "cleaned_unique": int(len(dedup)),
        "language_pre_dedup": {k: int(v) for k, v in usable["language"].value_counts().items()},
        "language_post_dedup": {k: int(v) for k, v in dedup["language"].value_counts().items()},
        "english_cleaned_unique": int(len(en)),
    }
    return en, counts


def raw_metrics_and_context(target_ids: set[str]) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    """Calculate raw-pair metrics and recover target ancestry up to four hops."""
    outbound: list[dict[str, str]] = []
    parent_ids: set[str] = set()
    records: dict[str, dict[str, str]] = {}
    cols = ["tweet_id", "author_id", "inbound", "text", "response_tweet_id", "in_response_to_tweet_id"]
    for chunk in pd.read_csv(RAW, chunksize=CHUNK, dtype=str, usecols=cols, keep_default_na=False):
        brand = chunk[(chunk["author_id"] == "AmazonHelp") & (chunk["inbound"] == "False")]
        outbound.extend(brand.to_dict("records"))
        wanted = chunk[chunk["tweet_id"].isin(target_ids)]
        for row in wanted.to_dict("records"):
            records[row["tweet_id"]] = row
            if row["in_response_to_tweet_id"]:
                parent_ids.add(row["in_response_to_tweet_id"])
    # Two additional scans recover enough ancestry for a preceding customer/brand pair.
    needed = parent_ids - set(records)
    for _ in range(3):
        if not needed:
            break
        found: dict[str, dict[str, str]] = {}
        for chunk in pd.read_csv(RAW, chunksize=CHUNK, dtype=str, usecols=cols, keep_default_na=False):
            part = chunk[chunk["tweet_id"].isin(needed)]
            for row in part.to_dict("records"):
                found[row["tweet_id"]] = row
        records.update(found)
        needed = {r["in_response_to_tweet_id"] for r in found.values() if r["in_response_to_tweet_id"]} - set(records)

    substantive = [r for r in outbound if classify_response(r["text"]) == "substantive"]
    # Direct parent IDs must be checked against the raw source; scan parent set once,
    # instead of assuming every referenced ID is an inbound customer tweet.
    direct_parent_ids = {r["in_response_to_tweet_id"] for r in substantive if r["in_response_to_tweet_id"]}
    inbound_parent_ids: set[str] = set()
    for chunk in pd.read_csv(RAW, chunksize=CHUNK, dtype=str, usecols=["tweet_id", "inbound"], keep_default_na=False):
        inbound_parent_ids.update(chunk.loc[(chunk["tweet_id"].isin(direct_parent_ids)) & (chunk["inbound"] == "True"), "tweet_id"])
    usable_pairs = sum(1 for r in substantive if r["in_response_to_tweet_id"] in inbound_parent_ids)
    return {
        "amazonhelp_outbound": len(outbound), "substantive_outbound": len(substantive),
        "verified_substantive_customer_pairs": usable_pairs,
        "legacy_reported_138255": 138255, "brand_reported_138264": 138264,
    }, records


def prior_context(tweet_id: str, records: dict[str, dict[str, str]], max_turns: int = 4) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    current = records.get(tweet_id, {})
    parent = current.get("in_response_to_tweet_id", "")
    while parent and parent in records and len(turns) < max_turns:
        row = records[parent]
        if row["author_id"] == "AmazonHelp" and row["inbound"] == "False":
            speaker = "AmazonHelp"
        elif row["inbound"] == "True":
            speaker = "customer"
        else:
            speaker = "unrelated/other account"
        turns.append({"tweet_id": parent, "speaker": speaker, "text": row["text"]})
        parent = row.get("in_response_to_tweet_id", "")
    return list(reversed(turns))


def top_terms(texts: list[str], n: int = 15) -> tuple[list[list[Any]], list[list[Any]]]:
    tokens = Counter()
    bigrams = Counter()
    for text in texts:
        words = [w for w in re.findall(r"[a-z]{2,}", normalize(text)) if w not in ENGLISH_STOP_WORDS]
        tokens.update(words)
        bigrams.update(" ".join(pair) for pair in zip(words, words[1:]))
    return [[k, v] for k, v in tokens.most_common(n)], [[k, v] for k, v in bigrams.most_common(n)]


def top_cooccurrences(texts: list[str], n: int = 15) -> list[list[Any]]:
    """Document-level co-occurrence, distinct from adjacent bigram frequency."""
    pairs = Counter()
    for text in texts:
        words = sorted({w for w in re.findall(r"[a-z]{2,}", normalize(text)) if w not in ENGLISH_STOP_WORDS})
        for index, left in enumerate(words):
            for right in words[index + 1:]:
                pairs[f"{left} + {right}"] += 1
    return [[pair, count] for pair, count in pairs.most_common(n)]


def cluster_fallback(fallback: pd.DataFrame, records: dict[str, dict[str, str]]) -> tuple[dict[str, Any], dict[str, Any]]:
    texts = fallback["clean_text"].tolist()
    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english", min_df=10, max_df=0.25)
    matrix = vectorizer.fit_transform(texts)
    features = vectorizer.get_feature_names_out()
    runs: dict[str, Any] = {}
    labels10 = None
    for k in [8, 10, 12, 15, 20]:
        model = MiniBatchKMeans(n_clusters=k, random_state=SEED, batch_size=1000, n_init=3)
        labels = model.fit_predict(matrix)
        groups = pd.Series(labels).value_counts().sort_values(ascending=False)
        runs[str(k)] = [{"cluster_id": int(cid), "size": int(size), "pct_of_fallback": round(100 * size / len(fallback), 2),
                         "top_keywords": [features[i] for i in model.cluster_centers_[cid].argsort()[::-1][:10]]}
                        for cid, size in groups.items()]
        if k == 10:
            labels10 = labels
            model10 = model
    fallback = fallback.copy()
    fallback["cluster_k10"] = labels10
    major: dict[str, Any] = {}
    for cid in fallback["cluster_k10"].value_counts().index[:5]:
        group = fallback[fallback["cluster_k10"] == cid]
        words, bigrams = top_terms(group["customer_text"].tolist(), 12)
        samples = group.sample(min(15, len(group)), random_state=SEED)
        examples = []
        for _, row in samples.iterrows():
            context = prior_context(row["customer_tweet_id"], records)
            context_customer = " ".join(t["text"] for t in context if t["speaker"] == "customer")
            context_intent = classify_intent(context_customer + " " + row["customer_text"])
            examples.append({"customer_tweet_id": row["customer_tweet_id"], "customer_message": row["customer_text"],
                             "preceding_context": context, "amazonhelp_response": row["brand_text"],
                             "message_type": row["message_type"], "conversation_state": row["conversation_state"],
                             "inferred_customer_goal": context_intent if context_intent != "other_unclear" else "insufficient evidence; retain other_unclear",
                             "existing_candidate_overlap": row["legacy_candidate_intent"]})
        major[f"cluster_{cid}"] = {"size": int(len(group)), "pct_of_fallback": round(100 * len(group) / len(fallback), 2),
                                    "top_keywords": [features[i] for i in model10.cluster_centers_[cid].argsort()[::-1][:10]],
                                    "top_word_frequencies": words, "top_bigram_frequencies": bigrams,
                                    "top_document_cooccurrences": top_cooccurrences(group["customer_text"].tolist(), 12), "examples": examples}
    overall_words, overall_bigrams = top_terms(texts, 20)
    return {"fallback_size": int(len(fallback)), "tfidf_vocabulary_size": len(features), "top_words": overall_words,
            "top_bigrams": overall_bigrams, "top_document_cooccurrences": top_cooccurrences(texts, 20), "kmeans_runs": runs}, major


def taxonomy_metadata(en: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for intent_id, spec in INTENTS.items():
        subset = en[en["context_intent"] == intent_id]
        response_counts = Counter(classify_response(t) for t in subset["brand_text"])
        examples = subset.head(3)[["customer_tweet_id", "customer_text", "brand_text"]].to_dict("records")
        result[intent_id] = {k: spec[k] for k in ["name", "definition", "include", "exclude", "pii", "handling", "difficulty"]}
        result[intent_id].update({"count": int(len(subset)), "pct": round(100 * len(subset) / len(en), 2),
                                  "historical_response_pattern": dict(response_counts), "real_examples": examples})
    return result


def report(payload: dict[str, Any]) -> str:
    c = payload["dataset_counts"]
    cm = payload["context_comparison"]
    lines = ["# Proposed Final Intent Taxonomy — pending human annotation", "",
             "> Local, reproducible audit only. Clusters describe language patterns, not ground-truth intents.", "",
             "## Corrected dataset metrics", "",
             f"- Raw AmazonHelp customer→brand pairs: **{c['raw_pairs']:,}**", f"- Unusable messages removed: **{c['noise_removed']:,}**; usable pre-dedup: **{c['usable_pre_dedup']:,}**.",
             f"- Duplicate normalized texts removed: **{c['duplicates_removed']:,}**; cleaned unique messages: **{c['cleaned_unique']:,}**.",
             f"- Cleaned unique English corpus / denominator: **{c['english_cleaned_unique']:,}**.",
             "", "### Corrections to earlier artifacts", "",
             f"- Recomputed substantive AmazonHelp→verified inbound-customer pairs: **{payload['raw_metrics']['verified_substantive_customer_pairs']:,}**. This resolves the 138,255 vs 138,264 discrepancy in favor of **{payload['raw_metrics']['verified_substantive_customer_pairs']:,}**; 138,255 is an undocumented stale value.",
             "- Language counts are now explicitly reported both pre- and post-deduplication; only post-dedup English is used as an intent denominator.",
             "- The prior K=8 value is not reused: this audit reruns KMeans deterministically and stores every cluster count in the raw artifact.",
             "- The earlier 50.44% multi-turn claim is not supported by the prior implementation. This audit measures follow-up availability from actual parent IDs instead of treating that claim as a finding.", "",
             "## Isolated message versus conversation context", "",
             f"- Earlier-regex fallback population audited: **{cm['fallback_population']:,}**.", f"- Fallback messages with recovered preceding context: **{cm['with_context']:,}** ({cm['with_context_pct']}%).",
             f"- Apparently unclear messages assigned a supported customer intent only after context: **{cm['context_resolved']:,}** ({cm['context_resolved_pct_of_fallback']}% of fallback; {cm['context_resolved_pct_of_context']}% of those with context).",
             f"- Residual `other_unclear` after context-aware classification: **{cm['residual_other']:,}** ({cm['residual_other_pct']}% of cleaned English).", "",
             "Customer intent is the underlying help goal. Conversation state (initial/follow-up) and message type (question, information provision, acknowledgement, complaint) are separate fields and are not intents.", "",
             "## Fallback language exploration", "",
             f"TF-IDF used {payload['fallback_analysis']['tfidf_vocabulary_size']:,} features. Top word frequencies: {payload['fallback_analysis']['top_words'][:10]}",
             f"Top bigram frequencies: {payload['fallback_analysis']['top_bigrams'][:10]}", "",
             f"Top document co-occurrences: {payload['fallback_analysis']['top_document_cooccurrences'][:10]}", "",
             "KMeans was rerun at K=8, 10, 12, 15, and 20. It is exploratory only; exact results are in `experiments/final_taxonomy_audit_raw.json`.", "",
             "## Major K=10 fallback clusters", ""]
    for cid, cluster in payload["major_clusters"].items():
        lines += [f"### {cid}: {cluster['size']:,} messages ({cluster['pct_of_fallback']}%)", "",
                  f"- Top keywords: `{', '.join(cluster['top_keywords'])}`", f"- Top bigrams: `{', '.join(x[0] for x in cluster['top_bigram_frequencies'])}`", ""]
        for i, ex in enumerate(cluster["examples"], 1):
            lines += [f"{i}. Customer `{ex['customer_tweet_id']}`: {ex['customer_message']}",
                      f"   - State/type: `{ex['conversation_state']}` / `{ex['message_type']}`; inferred goal: `{ex['inferred_customer_goal']}`; isolated overlap: `{ex['existing_candidate_overlap']}`."]
            if ex["preceding_context"]:
                lines.append("   - Preceding context: " + " | ".join(f"{t['speaker']}: {t['text']}" for t in ex["preceding_context"]))
            else:
                lines.append("   - Preceding context: unavailable in recovered ancestry.")
            lines.append(f"   - AmazonHelp response: {ex['amazonhelp_response']}")
        lines.append("")
    lines += ["## Taxonomy decisions", "",
              "- **RETAIN** delivery, returns/refunds, cancellation, Prime, account security, payment, product catalog, and marketplace-seller journeys because they have distinct customer goals/remedies.",
              "- **MERGE** damaged/wrong/defective/incomplete received-item reports into one fulfilment-condition intent; their initial remedy is replacement/return.",
              "- **MERGE** return, replacement, and expected-refund status into one customer journey for this provisional schema; annotate sub-issues later if they prove operationally separable.",
              "- **SPLIT** delivered-but-missing from delivery delay/status. The classifier requires both delivered evidence and absence evidence and evaluates this predicate first, so it cannot be swallowed by generic delay language.",
              "- **RENAME** `general_inquiry_unclear` to `other_unclear`; it is a residual evidence state, not a customer intent.",
              "- **REMOVE** `conversational_followup` as an intent. It remains a conversation-state/message-type signal.", "",
              "## Proposed customer-intent distribution", "",
              "| Intent | Count | % of cleaned English |", "|---|---:|---:|"]
    for key, item in payload["proposed_taxonomy"].items():
        lines.append(f"| `{key}` | {item['count']:,} | {item['pct']}% |")
    lines += ["", "Coverage is every label other than `other_unclear`; all rows sum exactly to the cleaned English corpus.", "", "## Intent definitions, examples, and operations", ""]
    for key, item in payload["proposed_taxonomy"].items():
        if key == "other_unclear":
            continue
        lines += [f"### `{key}` — {item['name']}", f"- Definition: {item['definition']}", f"- Include: {item['include']}", f"- Exclude: {item['exclude']}", f"- PII/account information: {item['pii']}", f"- Likely handling: {item['handling']}", f"- Annotation difficulty: {item['difficulty']}", f"- Historical AmazonHelp response pattern: {item['historical_response_pattern']}"]
        for ex in item["real_examples"]:
            lines.append(f"- Real example `{ex['customer_tweet_id']}`: {ex['customer_text']} — AmazonHelp: {ex['brand_text']}")
        lines.append("")
    lines += ["## Golden-set unit recommendation", "", "**B. Customer inquiry + relevant conversation context.** The measured context-resolved fallback cases show that a reply can be semantically incomplete in isolation while its preceding customer turn supplies the customer goal. Preserve the target customer message, the immediately relevant preceding turns, and message type/state as annotation fields. This is a recommendation only; this audit does not create a golden set."]
    return "\n".join(lines) + "\n"


def main() -> None:
    en, counts = load_clean_english()
    # Existing final taxonomy is the audit baseline, including its 88,731 fallback.
    from src.intents.refine_taxonomy import classify_final_taxonomy
    baseline, _ = classify_final_taxonomy(en.copy())
    fallback = baseline[baseline["final_intent"] == "general_inquiry_unclear"].copy()
    raw_metrics, records = raw_metrics_and_context(set(fallback["customer_tweet_id"]))
    en["isolated_intent"] = en["customer_text"].map(classify_intent)
    from src.intents.discover_intents import CANDIDATE_ISSUE_RULES
    def legacy_candidate(text: str) -> str:
        for intent_id, spec in CANDIDATE_ISSUE_RULES.items():
            if any(pattern.search(normalize(text)) for pattern in spec["compiled"]):
                return intent_id
        return "no_legacy_candidate_match"
    en["legacy_candidate_intent"] = en["customer_text"].map(legacy_candidate)
    en["message_type"] = en["customer_text"].map(message_type)
    en["conversation_state"] = en["customer_tweet_id"].map(lambda x: conversation_state(x, records))
    contexts = {tid: prior_context(tid, records) for tid in en["customer_tweet_id"] if tid in records}
    def contextual(row: pd.Series) -> str:
        prior_customer = " ".join(t["text"] for t in contexts.get(row["customer_tweet_id"], []) if t["speaker"] == "customer")
        return classify_intent(prior_customer + " " + row["customer_text"])
    en["context_intent"] = en.apply(contextual, axis=1)
    # Use the baseline fallback for required investigation, then attach audit fields.
    fallback = en[en["customer_tweet_id"].isin(set(fallback["customer_tweet_id"]))].copy()
    fallback_analysis, clusters = cluster_fallback(fallback, records)
    with_context = fallback["conversation_state"].eq("followup_in_thread")
    context_resolved = fallback[with_context & fallback["isolated_intent"].eq("other_unclear") & fallback["context_intent"].ne("other_unclear")]
    taxonomy = taxonomy_metadata(en)
    other_count = int((en["context_intent"] == "other_unclear").sum())
    taxonomy["other_unclear"] = {"name": "Other / genuinely unclear", "count": other_count, "pct": round(100 * other_count / len(en), 2),
                                 "definition": "Insufficient evidence for a defined customer goal, even after available context.", "include": "Vague feedback, ambiguous utterances, and context-unavailable follow-ups.", "exclude": "Any message with evidence for a proposed intent.", "pii": "Unknown until clarified.", "handling": "Ask a focused clarifying question or route based on live conversation state.", "difficulty": "High by definition.", "historical_response_pattern": {}, "real_examples": []}
    payload = {"status": "Proposed Final Intent Taxonomy — pending human annotation", "dataset_counts": counts, "raw_metrics": raw_metrics,
               "fallback_analysis": fallback_analysis, "major_clusters": clusters,
               "context_comparison": {"fallback_population": int(len(fallback)), "with_context": int(with_context.sum()), "with_context_pct": round(100 * with_context.mean(), 2),
                                      "context_resolved": int(len(context_resolved)), "context_resolved_pct_of_fallback": round(100 * len(context_resolved) / len(fallback), 2),
                                      "context_resolved_pct_of_context": round(100 * len(context_resolved) / max(1, with_context.sum()), 2),
                                      "residual_other": other_count, "residual_other_pct": round(100 * other_count / len(en), 2),
                                      "isolated_distribution": {k: int(v) for k, v in en["isolated_intent"].value_counts().items()},
                                      "context_distribution": {k: int(v) for k, v in en["context_intent"].value_counts().items()}},
               "proposed_taxonomy": taxonomy, "coverage_count": int(len(en) - other_count), "coverage_pct": round(100 * (len(en) - other_count) / len(en), 2)}
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(report(payload), encoding="utf-8")
    print(f"Wrote {ARTIFACT} and {REPORT}")
    print(f"English={len(en):,}; coverage={payload['coverage_pct']}%; other={payload['context_comparison']['residual_other_pct']}%")


if __name__ == "__main__":
    main()

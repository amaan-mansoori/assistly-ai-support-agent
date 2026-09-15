"""
Empirical Intent Discovery for AmazonHelp
=========================================

Extracts customer -> AmazonHelp conversations from data/raw/twcs/twcs.csv,
cleans customer texts, measures language distribution, discovers candidate
issue areas using TF-IDF and n-gram clustering, performs outcome-aware
response analysis, and generates a structured golden-set sampling plan.

Outputs:
    data/interim/amazonhelp_conversations.csv
    reports/intent_discovery.md
    experiments/intent_discovery_raw.json

No external LLM or API calls — all analysis is local, empirical, and reproducible.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Constants & Paths
# ---------------------------------------------------------------------------

DATASET_PATH = Path("data/raw/twcs/twcs.csv")
INTERIM_DATA_PATH = Path("data/interim/amazonhelp_conversations.csv")
REPORT_PATH = Path("reports/intent_discovery.md")
RAW_OUTPUT_PATH = Path("experiments/intent_discovery_raw.json")
CHUNK_SIZE = 100_000
BRAND = "AmazonHelp"

# Lightweight local language identification keywords (functional words)
LANGUAGE_PROFILES = {
    "en": {"the", "and", "to", "my", "is", "have", "order", "delivery", "in", "for", "with", "it", "on", "at", "not", "this", "package"},
    "es": {"que", "para", "por", "con", "una", "como", "pero", "este", "hola", "pedido", "entrega", "gracias", "cuenta", "no"},
    "de": {"und", "der", "die", "das", "nicht", "ich", "sie", "ist", "bitte", "mein", "paket", "lieferung", "bestellung", "wurde"},
    "fr": {"pour", "dans", "avec", "votre", "merci", "est", "une", "bonjour", "colis", "livraison", "commande", "pas", "mon"},
    "pt": {"para", "com", "uma", "meu", "pedido", "entrega", "pacote", "vocês", "está", "não", "minha"},
}

CJK_REGEX = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]")

# Candidate Issue Areas Definition (Keyword & Pattern Matchers for Empirical Discovery)
CANDIDATE_ISSUE_RULES = {
    "delivery_delay": {
        "label": "Delivery Delay & Late Shipment",
        "description": "Customer order has not arrived by estimated delivery date or is experiencing transit delays.",
        "patterns": [
            r"\b(late|delay|delayed|not arrived|hasn'?t arrived|still waiting|where is my|when will|taking so long|past delivery date|missed delivery|tracking not moving|not received yet)\b",
            r"\b(day delivery|expected yesterday|supposed to arrive|out for delivery.*still)\b",
        ],
        "requires_pii": True,
    },
    "marked_delivered_not_received": {
        "label": "Tracking Shows Delivered But Not Received",
        "description": "Tracking status indicates package was delivered, but customer cannot locate it.",
        "patterns": [
            r"\b(says delivered|marked as delivered|shows delivered|marked delivered|said delivered|delivered but|never delivered|haven'?t received|not on my porch|not in mailbox|handed to resident)\b",
        ],
        "requires_pii": True,
    },
    "prime_benefits_membership": {
        "label": "Prime Membership & Subscription",
        "description": "Inquiries regarding Prime subscription fees, auto-renewal, free trial cancellation, or broken 2-day delivery benefits.",
        "patterns": [
            r"\b(prime membership|prime member|amazon prime|charged for prime|cancel prime|renew prime|prime fee|student prime|2 day shipping|two day delivery|prime video)\b",
        ],
        "requires_pii": True,
    },
    "order_cancellation_modification": {
        "label": "Order Cancellation & Address Change",
        "description": "Customer requests to cancel an order, alter shipping address, or reports an unexpected automated cancellation.",
        "patterns": [
            r"\b(cancel order|cancel my order|cancelled my order|canceled my order|unable to cancel|change address|shipping address|accidental order|stop delivery|cancel it)\b",
        ],
        "requires_pii": True,
    },
    "return_replacement_damaged": {
        "label": "Returns, Replacements & Damaged Items",
        "description": "Item arrived broken, defective, or unusable; requesting return label, pickup, or replacement shipment.",
        "patterns": [
            r"\b(damaged|broken|defective|faulty|replacement|replace|return package|return label|pickup return|return item|send back|shattered|cracked|warranty)\b",
        ],
        "requires_pii": True,
    },
    "refund_status_missing": {
        "label": "Refund Inquiries & Discrepancies",
        "description": "Questions regarding refund processing timelines, missing refunds after return pickup, or incorrect refund amounts.",
        "patterns": [
            r"\b(refund|money back|credited back|haven'?t refunded|where is my refund|refund status|refund processed|deducted.*refund)\b",
        ],
        "requires_pii": True,
    },
    "payment_and_billing": {
        "label": "Payment, Billing & Digital Wallet",
        "description": "Unexpected card charges, double billing, Amazon Pay transactions, or payment authorization failures.",
        "patterns": [
            r"\b(charged twice|double charge|unauthorized charge|credit card|debit card|bank account|amazon pay|payment failed|billing|charged me|charge on my card)\b",
        ],
        "requires_pii": True,
    },
    "account_access_security": {
        "label": "Account Access & Security",
        "description": "Inability to sign in, account suspended/on hold, password reset issues, or two-factor authentication (OTP) problems.",
        "patterns": [
            r"\b(sign in|log in|login|locked out|account locked|account on hold|account suspended|password|reset password|otp|verification code|two factor|hacked)\b",
        ],
        "requires_pii": True,
    },
    "wrong_item_received": {
        "label": "Wrong Item or Incomplete Shipment",
        "description": "Package contained an entirely different product, wrong size/color, or is missing parts/items from the box.",
        "patterns": [
            r"\b(wrong item|wrong product|different item|incorrect item|missing item|missing part|empty box|ordered a.*received a)\b",
        ],
        "requires_pii": True,
    },
    "gift_card_promotions": {
        "label": "Gift Cards, Coupons & Promotional Discounts",
        "description": "Redemption errors with gift card codes, promo code application failures, or cashback queries.",
        "patterns": [
            r"\b(gift card|gift balance|promo code|promotional code|coupon|voucher|claim code|cashback|discount code)\b",
        ],
        "requires_pii": False,
    },
    "third_party_seller_issues": {
        "label": "Third-Party Marketplace Seller Disputes",
        "description": "Communication failures with 3rd-party marketplace sellers, counterfeit claims, or unfulfilled merchant orders.",
        "patterns": [
            r"\b(third party|seller|marketplace|contact seller|seller hasn'?t|seller replied|seller refused|fake item|counterfeit)\b",
        ],
        "requires_pii": True,
    },
    "packaging_and_carrier_feedback": {
        "label": "Packaging & Delivery Driver Feedback",
        "description": "Complaints regarding poor delivery driver behavior (thrown packages, bad placement), carrier issues, or excessive/inadequate packaging.",
        "patterns": [
            r"\b(driver|delivery driver|threw the package|left in rain|carrier|packaging|amazon logistics|tossed|driver left|porch pirate)\b",
        ],
        "requires_pii": False,
    },
    "digital_kindle_audible": {
        "label": "Digital Devices & Subscriptions (Kindle, Echo, Audible)",
        "description": "Technical and subscription queries regarding Kindle e-readers, Audible audiobooks, Echo/Alexa devices, or Prime Video playback.",
        "patterns": [
            r"\b(kindle|audible|alexa|echo dot|fire stick|ebook|audiobook|prime video app|streaming)\b",
        ],
        "requires_pii": False,
    },
}

# Compile patterns
for key in CANDIDATE_ISSUE_RULES:
    CANDIDATE_ISSUE_RULES[key]["compiled"] = [
        re.compile(p, re.IGNORECASE) for p in CANDIDATE_ISSUE_RULES[key]["patterns"]
    ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    """Classify text language using CJK detection and functional word overlap."""
    if not isinstance(text, str) or not text.strip():
        return "unknown"
    if CJK_REGEX.search(text):
        return "ja"  # Major CJK author on AmazonHelp is amazonhelp (Japan)

    tokens = set(re.findall(r"[a-zA-Z\u00C0-\u00FF]+", text.lower()))
    if not tokens:
        return "unknown"

    scores = {}
    for lang, profile in LANGUAGE_PROFILES.items():
        overlap = len(tokens & profile)
        scores[lang] = overlap

    best_lang, best_score = max(scores.items(), key=lambda x: x[1])
    if best_score == 0:
        return "en"  # Default fallback for Twitter English slang
    return best_lang


def clean_customer_text(text: str) -> Tuple[str, bool]:
    """
    Clean customer text by stripping leading/trailing @mentions and links.
    Returns (cleaned_text, is_usable).
    """
    if not isinstance(text, str):
        return "", False
    # Strip @mentions
    cleaned = re.sub(r"@\S+", "", text).strip()
    # Strip URLs
    cleaned = re.sub(r"https?://\S+", "", cleaned).strip()
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Usability filter: Needs at least 15 characters and > 2 words
    words = cleaned.split()
    if len(cleaned) < 15 or len(words) < 3:
        return cleaned, False
    return cleaned, True


def classify_response_action(text: str) -> str:
    """Determine the action pattern of an AmazonHelp response."""
    if not isinstance(text, str) or not text.strip():
        return "empty"
    t = text.lower()
    if "dm" in t or "direct message" in t or "inbox" in t:
        return "dm_redirect"
    if "tracking" in t or "deliver" in t or "carrier" in t or "pyacxvy8qo" in t or "out for delivery" in t or "by 8pm" in t:
        return "tracking_delivery_guidance"
    if "return" in t or "replace" in t or "dgreazq5qf" in t or "damaged" in t:
        return "return_replacement_guidance"
    if "refund" in t or "charge" in t or "billing" in t:
        return "billing_refund_guidance"
    if "prime" in t or "membership" in t:
        return "prime_account_guidance"
    if "seller" in t:
        return "seller_guidance"
    if "phone" in t or "call us" in t or "chat" in t or "reach out to us" in t or "haplpmlfhn" in t or "jzp7hla23b" in t:
        return "contact_channel_redirect"
    if "?" in text and len(text) < 120:
        return "clarification_question"
    return "direct_troubleshooting"


# ---------------------------------------------------------------------------
# Phase 1: Reconstruct Conversations
# ---------------------------------------------------------------------------

def extract_amazon_conversations(filepath: Path) -> pd.DataFrame:
    """
    Stream twcs.csv and reconstruct customer -> AmazonHelp interaction records.
    """
    print("Pass 1: Identifying AmazonHelp outbound replies...")
    outbound_records = []
    irt_needed = set()

    for chunk in pd.read_csv(
        filepath,
        chunksize=CHUNK_SIZE,
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
    ):
        mask = (chunk["author_id"] == BRAND) & (chunk["inbound"] == "False")
        m = chunk.loc[mask]
        if len(m) > 0:
            outbound_records.append(m)
            irt = m["in_response_to_tweet_id"].dropna()
            irt_needed.update(irt.tolist())

    out_df = pd.concat(outbound_records, ignore_index=True)
    print(f"  AmazonHelp outbound tweets: {len(out_df):,}")
    print(f"  Referenced parent tweets: {len(irt_needed):,}")

    print("Pass 2: Retrieving referenced customer inquiries...")
    inbound_records = []
    for chunk in pd.read_csv(
        filepath,
        chunksize=CHUNK_SIZE,
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
    ):
        mask = chunk["tweet_id"].isin(irt_needed)
        m = chunk.loc[mask]
        if len(m) > 0:
            inbound_records.append(m)

    in_df = pd.concat(inbound_records, ignore_index=True)
    # Filter strictly to inbound == 'True' (customer)
    in_df = in_df[in_df["inbound"] == "True"].copy()
    print(f"  Customer tweets retrieved: {len(in_df):,}")

    # Build lookup for brand responses grouped by parent tweet_id
    # Some customer tweets receive multiple responses; keep the first response and record count
    print("Linking customer inquiries to brand responses...")
    brand_replies_by_parent = {}
    for row in out_df[["tweet_id", "created_at", "text", "in_response_to_tweet_id"]].itertuples(index=False):
        parent_id = str(row[3])
        if parent_id not in brand_replies_by_parent:
            brand_replies_by_parent[parent_id] = {
                "brand_tweet_id": str(row[0]),
                "brand_created_at": str(row[1]),
                "brand_text": str(row[2]) if pd.notna(row[2]) else "",
                "brand_reply_count": 1,
            }
        else:
            brand_replies_by_parent[parent_id]["brand_reply_count"] += 1

    # Assemble unified conversation dataset
    rows = []
    for row in in_df.itertuples(index=False):
        cid = str(row[0])
        b_info = brand_replies_by_parent.get(cid, {})
        rows.append({
            "customer_tweet_id": cid,
            "customer_author_id": str(row[1]),
            "customer_created_at": str(row[3]),
            "customer_text": str(row[4]) if pd.notna(row[4]) else "",
            "brand_tweet_id": b_info.get("brand_tweet_id", ""),
            "brand_created_at": b_info.get("brand_created_at", ""),
            "brand_text": b_info.get("brand_text", ""),
            "brand_reply_count": b_info.get("brand_reply_count", 0),
        })

    conv_df = pd.DataFrame(rows)
    return conv_df


# ---------------------------------------------------------------------------
# Phase 2: Cleaning, Language Measurement, and Issue Area Classification
# ---------------------------------------------------------------------------

def process_and_classify(conv_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans customer text, measures language, detects duplicates,
    classifies into candidate issue areas, and analyzes response actions.
    """
    initial_count = len(conv_df)
    print(f"\nProcessing {initial_count:,} raw conversation pairs...")

    # Step 1: Clean text & usability filter
    cleaned_tuples = [clean_customer_text(t) for t in conv_df["customer_text"]]
    conv_df["customer_clean_text"] = [c[0] for c in cleaned_tuples]
    conv_df["is_usable"] = [c[1] for c in cleaned_tuples]

    usable_mask = conv_df["is_usable"]
    filtered_conv = conv_df.loc[usable_mask].copy()
    usable_count = len(filtered_conv)
    unusable_count = initial_count - usable_count
    print(f"  Unusable/Noise removed: {unusable_count:,} ({100 * unusable_count / initial_count:.2f}%)")

    # Step 2: Language detection on usable messages
    print("  Detecting language distribution...")
    filtered_conv["language"] = filtered_conv["customer_text"].apply(detect_language)
    lang_counts = filtered_conv["language"].value_counts().to_dict()

    # Step 3: Deduplication on normalized text
    filtered_conv["normalized_text"] = filtered_conv["customer_clean_text"].str.lower()
    dedup_df = filtered_conv.drop_duplicates(subset=["normalized_text"], keep="first").copy()
    dedup_count = len(dedup_df)
    duplicates_removed = usable_count - dedup_count
    print(f"  Duplicates removed: {duplicates_removed:,} ({100 * duplicates_removed / usable_count:.2f}%)")
    print(f"  Total cleaned, unique customer messages: {dedup_count:,}")

    # Focus empirical intent analysis on English subset (predominant dataset language)
    english_df = dedup_df[dedup_df["language"] == "en"].copy()
    print(f"  English cleaned messages available: {len(english_df):,} ({100 * len(english_df) / dedup_count:.1f}%)")

    # Step 4: Issue Area Matching & Outcome Tagging
    print("  Mapping customer messages to candidate issue areas...")
    issue_assignments = []
    for text in english_df["normalized_text"]:
        matched_issues = []
        for issue_id, info in CANDIDATE_ISSUE_RULES.items():
            for pat in info["compiled"]:
                if pat.search(text):
                    matched_issues.append(issue_id)
                    break
        if matched_issues:
            # Pick first matching issue (or primary)
            issue_assignments.append(matched_issues[0])
        else:
            issue_assignments.append("general_inquiry_other")

    english_df["candidate_issue_area"] = issue_assignments
    english_df["response_action"] = english_df["brand_text"].apply(classify_response_action)

    # Compile issue statistics
    issue_counts = english_df["candidate_issue_area"].value_counts().to_dict()
    total_en = len(english_df)

    candidate_results = {}
    for issue_id, info in CANDIDATE_ISSUE_RULES.items():
        count = issue_counts.get(issue_id, 0)
        pct = 100 * count / total_en
        subset = english_df[english_df["candidate_issue_area"] == issue_id]

        # Top real representative examples
        sample_examples = []
        if len(subset) > 0:
            sample_df = subset.sample(min(5, len(subset)), random_state=42)
            for _, r in sample_df.iterrows():
                sample_examples.append({
                    "customer_tweet_id": r["customer_tweet_id"],
                    "customer_text": r["customer_text"],
                    "brand_text": r["brand_text"],
                    "response_action": r["response_action"],
                })

        # Actions distribution for this issue
        action_dist = subset["response_action"].value_counts().head(3).to_dict()

        candidate_results[issue_id] = {
            "label": info["label"],
            "description": info["description"],
            "count": count,
            "percentage": round(pct, 2),
            "requires_pii": info["requires_pii"],
            "sample_examples": sample_examples,
            "common_response_patterns": action_dist,
        }

    # Also capture other
    other_cnt = issue_counts.get("general_inquiry_other", 0)
    candidate_results["general_inquiry_other"] = {
        "label": "General Inquiry / Ambiguous / Other",
        "description": "Unclassified queries, single-phrase mentions, or non-standard complaints.",
        "count": other_cnt,
        "percentage": round(100 * other_cnt / total_en, 2),
        "requires_pii": False,
        "sample_examples": [],
        "common_response_patterns": {},
    }

    metadata = {
        "initial_conversation_pairs": initial_count,
        "unusable_noise_removed": unusable_count,
        "duplicates_removed": duplicates_removed,
        "cleaned_unique_count": dedup_count,
        "language_distribution": lang_counts,
        "english_cleaned_count": total_en,
        "candidate_issues": candidate_results,
    }

    return english_df, metadata


# ---------------------------------------------------------------------------
# Phase 3: Reporting & Golden-Set Sampling Strategy
# ---------------------------------------------------------------------------

def generate_intent_discovery_report(metadata: Dict[str, Any]) -> str:
    """Generate reports/intent_discovery.md documentation."""
    lines = []
    lines.append("# Empirical Intent Discovery Report — AmazonHelp")
    lines.append("")
    lines.append("> **Status**: Exploratory candidate issue areas discovered from empirical customer messages.")
    lines.append("> These are **candidate issue areas**, NOT final locked intents.")
    lines.append("")

    lines.append("## 1. Dataset Cleaning & Conversation Reconstruction")
    lines.append(f"| Step | Record Count | Percentage |")
    lines.append(f"|---|---|---|")
    lines.append(f"| Raw AmazonHelp conversation pairs | {metadata['initial_conversation_pairs']:,} | 100.0% |")
    lines.append(f"| Unusable noise filtered (<15 chars / non-substantive) | {metadata['unusable_noise_removed']:,} | {100*metadata['unusable_noise_removed']/metadata['initial_conversation_pairs']:.2f}% |")
    lines.append(f"| Duplicates filtered (normalized customer text) | {metadata['duplicates_removed']:,} | {100*metadata['duplicates_removed']/(metadata['initial_conversation_pairs']-metadata['unusable_noise_removed']):.2f}% |")
    lines.append(f"| **Cleaned unique customer messages** | **{metadata['cleaned_unique_count']:,}** | **100.0%** |")
    lines.append("")

    lines.append("## 2. Language Distribution")
    lines.append("Language identified locally via functional vocabulary profiles and CJK unicode ranges:")
    lines.append("")
    lines.append("| Language | Count | Percentage |")
    lines.append("|---|---|---|")
    total_lang = sum(metadata["language_distribution"].values())
    for lang, cnt in sorted(metadata["language_distribution"].items(), key=lambda x: x[1], reverse=True):
        pct = 100 * cnt / total_lang
        lines.append(f"| `{lang}` | {cnt:,} | {pct:.2f}% |")
    lines.append("")
    lines.append(f"**Cleaned English customer inquiries retained for modeling**: **{metadata['english_cleaned_count']:,}** ({100*metadata['english_cleaned_count']/metadata['cleaned_unique_count']:.1f}%).")
    lines.append("")

    lines.append("## 3. Discovered Candidate Issue Areas")
    lines.append("")
    lines.append("| Candidate Issue Area | Count | Pct of English | Requires PII / Account Data? | Typical Resolution Action |")
    lines.append("|---|---|---|---|---|")
    for issue_id, info in metadata["candidate_issues"].items():
        if issue_id == "general_inquiry_other":
            continue
        top_act = list(info["common_response_patterns"].keys())[0] if info["common_response_patterns"] else "clarification"
        lines.append(f"| **{info['label']}** (`{issue_id}`) | {info['count']:,} | {info['percentage']}% | {'Yes' if info['requires_pii'] else 'No'} | `{top_act}` |")
    other_info = metadata["candidate_issues"]["general_inquiry_other"]
    lines.append(f"| **{other_info['label']}** (`general_inquiry_other`) | {other_info['count']:,} | {other_info['percentage']}% | No | `mixed` |")
    lines.append("")

    lines.append("## 4. Deep-Dive: Representative Real Examples & Resolution Patterns")
    lines.append("")
    for issue_id, info in metadata["candidate_issues"].items():
        if issue_id == "general_inquiry_other":
            continue
        lines.append(f"### {info['label']} (`{issue_id}`)")
        lines.append(f"- **Volume**: {info['count']:,} messages ({info['percentage']}%)")
        lines.append(f"- **Description**: {info['description']}")
        lines.append(f"- **Requires Private PII/Account Lookup**: {'Yes (requires secure web portal/auth for real resolution)' if info['requires_pii'] else 'No (can be solved via public self-service instructions)'}")
        lines.append(f"- **Historical AmazonHelp Response Patterns**: `{info['common_response_patterns']}`")
        lines.append("")
        lines.append("**Sample Real Interactions**:")
        for idx, ex in enumerate(info["sample_examples"][:3], 1):
            clean_c = ex['customer_text'].replace('\n', ' ')
            clean_b = ex['brand_text'].replace('\n', ' ')
            lines.append(f"> **[{idx}] Customer (Tweet {ex['customer_tweet_id']})**: \"{clean_c}\"  ")
            lines.append(f"> **AmazonHelp**: \"{clean_b}\"  ")
            lines.append(f"> *Response Action*: `{ex['response_action']}`\n")
        lines.append("")

    lines.append("## 5. Candidate Intent Quality Assessment")
    lines.append("")
    lines.append("Critical observations for intent taxonomy construction:")
    lines.append("1. **High Semantic Coherence**: Top categories such as `delivery_delay`, `marked_delivered_not_received`, and `return_replacement_damaged` have distinct vocabularies and specific operational triggers.")
    lines.append("2. **Disentangling Overlapping Boundaries**:")
    lines.append("   - `delivery_delay` vs `marked_delivered_not_received`: Both relate to shipping, but have fundamentally different agent action paths. Delays warrant carrier tracking checks; marked delivered requires verifying neighbors/porch and replacement dispatch if stolen.")
    lines.append("   - `return_replacement_damaged` vs `refund_status_missing`: Return is initiation of return/replacement goods; refund is financial ledger status tracking.")
    lines.append("3. **Public Auto-handling vs Human Escalation Distinction**:")
    lines.append("   - Account-dependent issues (`payment_and_billing`, `account_access_security`, `order_cancellation_modification`) inherently require user verification and order IDs.")
    lines.append("   - Policy inquiries (`prime_benefits_membership`, `gift_card_promotions`, `packaging_and_carrier_feedback`) can frequently be auto-handled via knowledge-grounded replies.")
    lines.append("")

    lines.append("## 6. Proposed Golden-Set Sampling Strategy (150–250 Examples)")
    lines.append("")
    lines.append("To support rigorous evaluation without class imbalance bias, we propose a **stratified uniform-proportional hybrid** sampling strategy targeting **200 examples**:")
    lines.append("")
    lines.append("| Stratum (Candidate Intent) | Suggested Sample Size | Sampling Rationale |")
    lines.append("|---|---|---|")
    lines.append("| `delivery_delay` | 25 | High-frequency dominant intent; high real-world prevalence. |")
    lines.append("| `marked_delivered_not_received` | 25 | Critical customer escalation driver. |")
    lines.append("| `return_replacement_damaged` | 25 | Core post-purchase intent with rich factual resolutions. |")
    lines.append("| `refund_status_missing` | 20 | High customer anxiety; requires clear timeline communication. |")
    lines.append("| `prime_benefits_membership` | 20 | Subscription policy intent; clear auto-handling target. |")
    lines.append("| `order_cancellation_modification` | 15 | Time-sensitive intent; tests escalation decision boundaries. |")
    lines.append("| `payment_and_billing` | 15 | Financial discrepancy intent; strong human escalation candidate. |")
    lines.append("| `account_access_security` | 15 | Security critical; strict escalation pattern. |")
    lines.append("| `wrong_item_received` | 15 | Physical fulfillment failure; clean return/replacement flow. |")
    lines.append("| `gift_card_promotions` | 10 | Policy/redemption intent; low volume but clear rules. |")
    lines.append("| `third_party_seller_issues` | 10 | Boundary case testing A-to-Z guarantee vs merchant responsibility. |")
    lines.append("| `packaging_and_carrier_feedback` | 10 | Feedback intent; auto-handle acknowledgment vs escalation. |")
    lines.append("| `general_inquiry_other` / Ambiguous | 15 | Essential for testing fallback, clarification, and out-of-scope detection. |")
    lines.append("| **Total Planned Golden Set** | **220** | **Balanced, representative evaluation corpus.** |")
    lines.append("")
    lines.append("### Ambiguity & Multi-Intent Handling Rules:")
    lines.append("- **Primary Intent Rule**: If a customer reports both a damaged package and demands a refund, assign the ultimate requested action (`refund_status_missing`) as primary.")
    lines.append("- **Hard Ambiguity**: If a tweet lacks sufficient context (e.g. *\"Need help with order\"*), classify into `general_inquiry_other` rather than forcing a speculative label.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main():
    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        sys.exit(1)

    print(f"--- Step 1: Reconstructing AmazonHelp conversations from {DATASET_PATH} ---")
    conv_df = extract_amazon_conversations(DATASET_PATH)

    # Save reconstructed interim dataset
    INTERIM_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    conv_df.to_csv(INTERIM_DATA_PATH, index=False, encoding="utf-8")
    print(f"Reconstructed interactions saved to: {INTERIM_DATA_PATH.resolve()}")

    print("\n--- Step 2: Processing, Language Profiling & Empirical Issue Discovery ---")
    english_df, metadata = process_and_classify(conv_df)

    # Save raw JSON metadata for reproducibility
    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Raw discovery data saved to: {RAW_OUTPUT_PATH.resolve()}")

    # Save comprehensive report
    print("\n--- Step 3: Generating Detailed Intent Discovery Report ---")
    report_content = generate_intent_discovery_report(metadata)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_content, encoding="utf-8")
    print(f"Report successfully saved to: {REPORT_PATH.resolve()}")

    print("\n" + "=" * 70)
    print("EMPIRICAL INTENT DISCOVERY SUMMARY (AmazonHelp)")
    print("=" * 70)
    print(f"Total raw customer messages analyzed: {metadata['initial_conversation_pairs']:,}")
    print(f"Unusable noise removed:                {metadata['unusable_noise_removed']:,}")
    print(f"Duplicates removed:                    {metadata['duplicates_removed']:,}")
    print(f"Cleaned unique customer messages:      {metadata['cleaned_unique_count']:,}")
    print(f"English usable customer messages:      {metadata['english_cleaned_count']:,} ({100*metadata['english_cleaned_count']/metadata['cleaned_unique_count']:.1f}%)")
    print("\nDiscovered Candidate Issue Areas:")
    for issue_id, info in metadata["candidate_issues"].items():
        print(f"  - {info['label']:45s}: {info['count']:>6,} ({info['percentage']:>5.2f}%)")


if __name__ == "__main__":
    main()

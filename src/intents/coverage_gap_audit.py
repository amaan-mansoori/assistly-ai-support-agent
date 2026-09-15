"""Local audit of customer-goal coverage gaps in the final taxonomy.

This module deliberately does not build an agent, retrieval system, reply
generator, or golden set.  It operates only on checked-in local data.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from src.data.validate_amazonhelp import classify_response
from src.intents.final_taxonomy_audit import (
    INTENTS, SEED, classify_intent, conversation_state, load_clean_english,
    message_type, normalize, prior_context, raw_metrics_and_context,
    top_cooccurrences, top_terms,
)

REPORT = Path("reports/coverage_gap_audit.md")
ARTIFACT = Path("experiments/coverage_gap_audit_raw.json")

# Hypotheses are evaluated only inside the residual population. They are not
# labels unless examples/context show a coherent customer goal.
HYPOTHESES: dict[str, dict[str, Any]] = {
    "digital_content_device_support": {
        "name": "Digital content, device, and app support",
        "patterns": [r"\b(kindle|echo|alexa|fire (?:tv|stick|tablet)|audible|amazon music|prime video|video app|app (?:not |isn.?t |won.?t )?(?:working|work|load)|digital (?:content|download)|ebook|e-?book)\b"],
        "decision": "new intent if examples concern troubleshooting/access rather than membership management",
    },
    "gift_card_promotion": {
        "name": "Gift card, promotion, cashback, and voucher",
        "patterns": [r"\b(gift ?card|gift voucher|voucher|cash ?back|cashback|promo(?:tion| code)?|coupon|offer code|reward points?)\b"],
        "decision": "new intent if a benefit/redemption/dispute is the primary goal; pricing-only questions remain product availability/pricing",
    },
    "product_information": {
        "name": "Product information, compatibility, and warranty",
        "patterns": [r"\b(product (?:information|details|description)|specification|compatib(?:le|ility)|warranty|manual|dimension|size guide|how (?:does|do) (?:this|it) work|model number)\b"],
        "decision": "merge into a broadened product inquiry intent if examples are pre-purchase information requests",
    },
    "contact_support_access": {
        "name": "Customer-service/contact-channel request",
        "patterns": [r"\b(customer service|customer care|contact (?:you|support|customer service)|speak (?:to|with) (?:a )?(?:person|human|agent)|call (?:me|you|back)|phone number|helpline|support team)\b"],
        "decision": "retain as routing/state metadata unless the underlying issue is unavailable; it is not automatically a customer intent",
    },
    "order_status_or_account_question": {
        "name": "Generic order/account question",
        "patterns": [r"\b(my order|order number|order status|orders page|your orders|account (?:details|information)|where (?:can|do) i (?:see|find))\b"],
        "decision": "merge into delivery status/account access only when the goal is explicit; otherwise retain other_unclear",
    },
    "shipping_address_instruction": {
        "name": "Shipping address/instruction issue",
        "patterns": [r"\b(delivery address|shipping address|address (?:change|wrong|incorrect)|deliver (?:to|at) (?:another|different)|delivery instructions?)\b"],
        "decision": "merge into order cancellation/change; not a separate intent unless evidence supports a different remedy",
    },
}
for hypothesis in HYPOTHESES.values():
    hypothesis["compiled"] = [re.compile(p, re.I) for p in hypothesis["patterns"]]


def hypothesis_hits(text: str) -> list[str]:
    n = normalize(text)
    return [key for key, spec in HYPOTHESES.items() if any(p.search(n) for p in spec["compiled"])]


def classify_augmented(text: str) -> str:
    """Conservative extension applied only after the current taxonomy fails."""
    existing = classify_intent(text)
    if existing != "other_unclear":
        return existing
    n = normalize(text)
    # Specific patterns and distinct remedies; no generic "customer service" label.
    if any(p.search(n) for p in HYPOTHESES["digital_content_device_support"]["compiled"]):
        return "digital_content_device_support"
    if any(p.search(n) for p in HYPOTHESES["gift_card_promotion"]["compiled"]):
        return "gift_card_promotion"
    if any(p.search(n) for p in HYPOTHESES["product_information"]["compiled"]):
        return "product_availability_pricing"  # broaden/rename, not a new bucket
    if any(p.search(n) for p in HYPOTHESES["shipping_address_instruction"]["compiled"]):
        return "order_cancellation_or_change"  # merge, not a new bucket
    return "other_unclear"


def residual_form(text: str) -> str:
    """Descriptive message form; intentionally not an intent classifier."""
    n = normalize(text)
    if re.fullmatch(r"(?:hi|hello|hey|good (?:morning|afternoon|evening))\b[!. ]*", n):
        return "greeting"
    if re.search(r"\b(lol|haha|love|great service|awesome|congrats|follow)\b", n) and "?" not in text:
        return "conversational_social"
    return message_type(text)


def cluster_residual(residual: pd.DataFrame, records: dict[str, dict[str, str]]) -> tuple[dict[str, Any], dict[str, Any]]:
    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english", min_df=10, max_df=0.25)
    matrix = vectorizer.fit_transform(residual["clean_text"])
    features = vectorizer.get_feature_names_out()
    runs: dict[str, Any] = {}
    labels10 = None
    model10 = None
    for k in [8, 10, 12, 15, 20]:
        model = MiniBatchKMeans(n_clusters=k, random_state=SEED, batch_size=1000, n_init=3)
        labels = model.fit_predict(matrix)
        sizes = pd.Series(labels).value_counts().sort_values(ascending=False)
        runs[str(k)] = [{"cluster_id": int(cid), "size": int(size), "pct_of_residual": round(100 * size / len(residual), 2),
                         "top_keywords": [features[i] for i in model.cluster_centers_[cid].argsort()[::-1][:10]]}
                        for cid, size in sizes.items()]
        if k == 10:
            labels10, model10 = labels, model
    data = residual.copy()
    data["cluster_k10"] = labels10
    major: dict[str, Any] = {}
    for cid in data["cluster_k10"].value_counts().index[:5]:
        group = data[data["cluster_k10"] == cid]
        words, bigrams = top_terms(group["customer_text"].tolist(), 12)
        examples = []
        for _, row in group.sample(min(15, len(group)), random_state=SEED).iterrows():
            context = prior_context(row["customer_tweet_id"], records)
            prior_customer = " ".join(t["text"] for t in context if t["speaker"] == "customer")
            inferred = classify_augmented(prior_customer + " " + row["customer_text"])
            examples.append({"customer_tweet_id": row["customer_tweet_id"], "customer_message": row["customer_text"],
                             "preceding_context": context, "amazonhelp_response": row["brand_text"],
                             "message_type": row["message_type"], "conversation_state": row["conversation_state"],
                             "inferred_customer_goal": inferred if inferred != "other_unclear" else "insufficient evidence",
                             "coherent_enough_for_intent": inferred != "other_unclear",
                             "hypothesis_hits": row["hypothesis_hits"]})
        major[f"cluster_{cid}"] = {"size": int(len(group)), "pct_of_residual": round(100 * len(group) / len(data), 2),
                                    "top_keywords": [features[i] for i in model10.cluster_centers_[cid].argsort()[::-1][:10]],
                                    "top_words": words, "top_bigrams": bigrams,
                                    "top_document_cooccurrences": top_cooccurrences(group["customer_text"].tolist(), 12), "examples": examples}
    words, bigrams = top_terms(data["customer_text"].tolist(), 20)
    return {"residual_count": int(len(data)), "tfidf_vocabulary_size": int(len(features)), "top_words": words,
            "top_bigrams": bigrams, "top_document_cooccurrences": top_cooccurrences(data["customer_text"].tolist(), 20),
            "kmeans_runs": runs}, major


def render(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = ["# Coverage Gap Audit — Proposed Final Intent Taxonomy pending human annotation", "",
             "> Local analysis only. Unsupervised clusters are exploratory and are not treated as ground-truth intents.", "",
             "## Exact current coverage", "",
             f"- Cleaned English corpus: **{s['english_total']:,}**", f"- Current defined-label coverage: **{s['current_coverage_count']:,} ({s['current_coverage_pct']}%)**.",
             f"- Current `other_unclear`: **{s['current_residual_count']:,} ({s['current_residual_pct']}%)**.",
             f"- Residual messages with recovered preceding context: **{s['residual_with_context']:,} ({s['residual_with_context_pct']}%)**.",
             f"- Context-resolved into an existing or defensible augmented goal: **{s['context_resolved']:,}**; still unclear even with available context: **{s['context_still_unclear']:,}**.", "",
             "## What the residual represents", "",
             "Message type and customer intent are separate. The table below describes messages, not new intent labels.", "",
             "| Message type / state | Count | % of residual |", "|---|---:|---:|"]
    for key, value in payload["message_breakdown"].items():
        lines.append(f"| `{key}` | {value['count']:,} | {value['pct']}% |")
    lines += ["", "## Tested coverage hypotheses", "", "| Hypothesis | Isolated hits | Context-supported hits | Decision |", "|---|---:|---:|---|"]
    for key, value in payload["hypotheses"].items():
        lines.append(f"| {value['name']} | {value['isolated_hits']:,} | {value['context_supported_hits']:,} | {value['decision']} |")
    lines += ["", "## Residual clustering", "", f"TF-IDF features: **{payload['cluster_analysis']['tfidf_vocabulary_size']:,}**. KMeans ran at K=8, 10, 12, 15, 20; exact counts are in the raw artifact.",
              f"Top residual bigrams: {payload['cluster_analysis']['top_bigrams'][:12]}", f"Top document co-occurrences: {payload['cluster_analysis']['top_document_cooccurrences'][:12]}", ""]
    for cid, cluster in payload["major_clusters"].items():
        lines += [f"### {cid}: {cluster['size']:,} ({cluster['pct_of_residual']}%)", "",
                  f"- Top keywords: `{', '.join(cluster['top_keywords'])}`", f"- Top bigrams: `{', '.join(x[0] for x in cluster['top_bigrams'])}`", f"- Co-occurrence: `{', '.join(x[0] for x in cluster['top_document_cooccurrences'])}`", ""]
        for i, ex in enumerate(cluster["examples"], 1):
            lines.append(f"{i}. Customer `{ex['customer_tweet_id']}`: {ex['customer_message']}")
            lines.append(f"   - State/type: `{ex['conversation_state']}` / `{ex['message_type']}`; inferred goal: `{ex['inferred_customer_goal']}`; coherent enough: `{ex['coherent_enough_for_intent']}`; hypotheses: `{', '.join(ex['hypothesis_hits']) or 'none'}`.")
            if ex["preceding_context"]:
                lines.append("   - Preceding context: " + " | ".join(f"{t['speaker']}: {t['text']}" for t in ex["preceding_context"]))
            else:
                lines.append("   - Preceding context: unavailable in recovered ancestry.")
            lines.append(f"   - AmazonHelp response: {ex['amazonhelp_response']}")
        lines.append("")
    lines += ["## Coverage decision", "",
              f"- Current taxonomy coverage: **{s['current_coverage_pct']}%**.", f"- Conservative revised coverage: **{s['revised_coverage_pct']}%** ({s['revised_coverage_count']:,} messages).",
              f"- Residual after defensible additions/merges: **{s['revised_residual_count']:,} ({s['revised_residual_pct']}%)**.",
              "- The additions are limited to digital/device support and gift-card/promotion issues. Product information is merged into the product inquiry intent; address/instruction cases merge into order change. Contact-channel requests remain metadata/routing rather than an intent.", "",
              "## Recommendation", "",
              "**No — an 8–12 intent taxonomy cannot reasonably cover the majority of all individual cleaned tweets in this corpus without conflating follow-ups, social/conversational messages, and vague complaints with customer goals.** It can cover a meaningful subset of task-oriented inquiries. Frame the assignment around context-aware inquiry-level classification, retain `other_unclear`, and use human annotation to determine whether the two new categories and broadened product label have adequate boundary reliability.",
              "", "The taxonomy is **not yet ready to be locked**, but it is ready for a context-aware human-annotation validation phase. This audit does not create that set."]
    return "\n".join(lines) + "\n"


def main() -> None:
    en, counts = load_clean_english()
    target_ids = set(en["customer_tweet_id"])
    _, records = raw_metrics_and_context(target_ids)
    en["message_type"] = en["customer_text"].map(message_type)
    en["conversation_state"] = en["customer_tweet_id"].map(lambda x: conversation_state(x, records))
    def context_text(row: pd.Series) -> str:
        turns = prior_context(row["customer_tweet_id"], records)
        return " ".join(t["text"] for t in turns if t["speaker"] == "customer") + " " + row["customer_text"]
    en["isolated_intent"] = en["customer_text"].map(classify_intent)
    en["context_text"] = en.apply(context_text, axis=1)
    en["context_intent"] = en["context_text"].map(classify_intent)
    residual = en[en["context_intent"] == "other_unclear"].copy()
    residual["residual_form"] = residual["customer_text"].map(residual_form)
    residual["hypothesis_hits"] = residual["customer_text"].map(hypothesis_hits)
    residual["augmented_isolated"] = residual["customer_text"].map(classify_augmented)
    residual["augmented_context"] = residual["context_text"].map(classify_augmented)
    analysis, major = cluster_residual(residual, records)
    with_context = residual["conversation_state"].eq("followup_in_thread")
    augmented_resolved = residual["augmented_context"].ne("other_unclear")
    # Context-supported means the original residual is assigned only after using
    # previous customer turns or a defensible newly tested category.
    context_resolved = residual[with_context & augmented_resolved]
    message_counts = residual["residual_form"].value_counts()
    state_counts = residual["conversation_state"].value_counts()
    breakdown = {f"message_type:{k}": {"count": int(v), "pct": round(100 * v / len(residual), 2)} for k, v in message_counts.items()}
    breakdown.update({f"conversation_state:{k}": {"count": int(v), "pct": round(100 * v / len(residual), 2)} for k, v in state_counts.items()})
    hypothesis_summary = {}
    for key, spec in HYPOTHESES.items():
        iso = sum(key in hits for hits in residual["hypothesis_hits"])
        ctx = sum(key in hypothesis_hits(text) for text in residual["context_text"])
        hypothesis_summary[key] = {"name": spec["name"], "isolated_hits": int(iso), "context_supported_hits": int(ctx), "decision": spec["decision"]}
    revised = en.copy()
    revised["augmented_context"] = revised["context_text"].map(classify_augmented)
    current_coverage = int((en["context_intent"] != "other_unclear").sum())
    revised_coverage = int((revised["augmented_context"] != "other_unclear").sum())
    summary = {"english_total": int(len(en)), "current_coverage_count": current_coverage, "current_coverage_pct": round(100 * current_coverage / len(en), 2),
               "current_residual_count": int(len(residual)), "current_residual_pct": round(100 * len(residual) / len(en), 2),
               "residual_with_context": int(with_context.sum()), "residual_with_context_pct": round(100 * with_context.mean(), 2),
               "context_resolved": int(len(context_resolved)), "context_still_unclear": int(with_context.sum() - len(context_resolved)),
               "revised_coverage_count": revised_coverage, "revised_coverage_pct": round(100 * revised_coverage / len(en), 2),
               "revised_residual_count": int(len(en) - revised_coverage), "revised_residual_pct": round(100 * (len(en) - revised_coverage) / len(en), 2)}
    payload = {"status": "Coverage Gap Audit — Proposed Final Intent Taxonomy pending human annotation", "dataset_counts": counts,
               "summary": summary, "message_breakdown": breakdown, "hypotheses": hypothesis_summary,
               "cluster_analysis": analysis, "major_clusters": major,
               "revised_taxonomy": list(INTENTS) + ["digital_content_device_support", "gift_card_promotion", "other_unclear"]}
    ARTIFACT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(render(payload), encoding="utf-8")
    print(f"Wrote {REPORT} and {ARTIFACT}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

"""Populate AI-proposed labels while preserving the blank worksheet metadata."""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

from src.intents.final_taxonomy_audit import classify_intent

WORKSHEET = Path("data/golden/golden_set.csv")
REPORT = Path("reports/golden_set_ai_proposed_labels.md")
ALLOWED = {
    "delivery_status_delay", "delivery_marked_delivered_missing", "return_refund",
    "item_condition_or_fulfilment", "order_cancellation_or_change", "prime_membership",
    "account_access_security", "payment_charge_issue", "product_availability_pricing",
    "marketplace_seller", "other_unclear",
}


def proposed_label(row: dict[str, str]) -> str:
    """Use inquiry plus verified context; conservative ambiguity goes to other_unclear."""
    text = row["customer_text"]
    context = row["conversation_context"]
    combined = f"{context}\n{text}".strip()
    if not re.search(r"[A-Za-z]", text) or len(re.findall(r"\w+", text)) < 3:
        return "other_unclear"
    if re.search(r"\b(thanks?|thank you|thx|cheers|got it|okay|ok)\b", text, re.I) and not re.search(
        r"\b(order|refund|return|delivery|charge|account|seller|prime|password|address)\b", text, re.I
    ):
        return "other_unclear"
    label = classify_intent(combined)
    return label if label in ALLOWED else "other_unclear"


def main() -> None:
    with WORKSHEET.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = rows[0].keys() if rows else []
    if len(rows) != 220:
        raise RuntimeError(f"Expected 220 rows, found {len(rows)}")
    original_nonlabels = [
        tuple(row[key] for key in fieldnames if key != "human_intent")
        for row in rows
    ]
    for row in rows:
        row["human_intent"] = proposed_label(row)
    if any(row["human_intent"] not in ALLOWED for row in rows):
        raise RuntimeError("Generated a label outside the allowed taxonomy")
    if original_nonlabels != [
        tuple(row[key] for key in fieldnames if key != "human_intent")
        for row in rows
    ]:
        raise RuntimeError("A non-label field changed")
    with WORKSHEET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row["human_intent"] for row in rows)
    context_used = sum(bool(row["conversation_context"].strip()) for row in rows)
    report = f"""# AI-Proposed Golden-Set Labels

These labels are **AI-proposed** and have **not** been counted as human
annotation. They are not final labels and the worksheet is not complete until
a human annotator reviews and replaces them.

- Rows: **{len(rows)}**
- Context used: **{context_used}** rows with available preceding context
- `other_unclear`: **{counts["other_unclear"]}** rows

## Label distribution

{chr(10).join(f"- `{label}`: **{counts[label]}**" for label in sorted(ALLOWED))}

The labeler used the actual `customer_text` and available provenance-safe
parent-ID context. The existing `candidate_stratum` was treated only as a
sampling aid and was not used as the label. Short, social, non-English-looking,
or insufficiently supported inquiries were conservatively assigned
`other_unclear`; this is a local deterministic screening aid, not a human
decision. `example_id`, tweet IDs, text, candidate strata, and annotation notes
were preserved exactly.
"""
    REPORT.write_text(report, encoding="utf-8")
    print({"rows": len(rows), "distribution": dict(counts), "context_used": context_used,
           "other_unclear": counts["other_unclear"]})


if __name__ == "__main__":
    main()

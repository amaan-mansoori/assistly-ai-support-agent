"""Create the blank, human-annotation-ready 220-row worksheet."""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

from src.evaluation.sample_golden_set import SEED, TARGETS, choose

SOURCE = Path("data/golden/golden_candidates.csv")
OUTPUT = Path("data/golden/golden_set.csv")
REPORT = Path("reports/golden_set_annotation_status.md")
FIELDS = [
    "example_id", "customer_tweet_id", "customer_author_id", "customer_text",
    "conversation_context", "amazonhelp_response", "candidate_stratum",
    "human_intent", "annotation_notes",
]


def non_english_flags(text: str) -> list[str]:
    """Flag questionable text using deterministic script/token signals only."""
    flags = []
    if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text):
        flags.append("CJK characters")
    if re.search(r"[А-Яа-яЁё]", text):
        flags.append("Cyrillic characters")
    words = re.findall(r"[A-Za-zÀ-ÿ]+", text.lower())
    markers = {"que", "para", "con", "una", "como", "gracias", "pedido", "livraison", "merci", "bestellung", "nicht"}
    if words and sum(word in markers for word in words) >= 2:
        flags.append("non-English marker tokens")
    return flags


def main() -> None:
    with SOURCE.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    groups = {key: [row for row in rows if row["candidate_stratum"] == key] for key in TARGETS}
    selected = []
    shortages = {}
    for key, target in TARGETS.items():
        picked = choose(groups[key], target, SEED)
        selected.extend(picked)
        shortages[key] = target - len(picked)
    if len(selected) != 220 or any(shortages.values()):
        raise RuntimeError(f"Unable to meet worksheet quotas: {shortages}")
    selected.sort(key=lambda row: int(row["example_id"].rsplit("-", 1)[-1]))
    for index, row in enumerate(selected, 1):
        row["example_id"] = f"golden-set-{index:04d}"
        row["human_intent"] = ""
        row["annotation_notes"] = ""
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({field: row[field] for field in FIELDS} for row in selected)
    flags = [(row["example_id"], non_english_flags(row["customer_text"])) for row in selected]
    flags = [(example_id, values) for example_id, values in flags if values]
    counts = Counter(row["candidate_stratum"] for row in selected)
    context = sum(row.get("context_available") == "True" for row in selected)
    report = f"""# Golden Set Annotation Status

## Selection

- **220 selected** from `data/golden/golden_candidates.csv`.
- Deterministic method: existing SHA-256 ordering with seed **{SEED}**, selecting the requested quota independently within each `candidate_stratum`.
- `candidate_stratum` is **NOT ground truth**. It is only a sampling stratum.
- Every `human_intent` and `annotation_notes` cell is blank. Final labels must be assigned by a human annotator; no labels were generated automatically.

## Target and actual counts

{chr(10).join(f"- `{key}`: target **{TARGETS[key]}**, actual **{counts[key]}**" for key in TARGETS)}

## Context and language screening

- Rows with recoverable preceding context: **{context}/220** (as recorded in the candidate pool).
- Deterministic non-English/questionable rows flagged: **{len(flags)}**.
"""
    if flags:
        report += "\nFlagged worksheet rows (not removed or relabelled):\n" + "\n".join(
            f"- `{example_id}`: {', '.join(values)}" for example_id, values in flags
        )
    else:
        report += "\nNo rows were flagged by the local script/token screen.\n"
    report += "\nThe worksheet is blank and annotation-ready; do not treat candidate strata as human decisions.\n"
    REPORT.write_text(report, encoding="utf-8")
    print({"selected": len(selected), "actual_counts": dict(counts), "context_available": context, "language_flags": len(flags)})


if __name__ == "__main__":
    main()

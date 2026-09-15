"""Create a reproducible, label-blind 50-example human reply-audit sample."""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

GOLDEN = Path("data/golden/golden_set.csv")
GENERATIONS = Path("reports/evaluation/golden_reply_generations.jsonl")
OUTPUT = Path("data/golden/human_audit_50.csv")
TEMPLATE = Path("data/golden/human_audit_50_template.csv")
REPORT = Path("reports/human_audit_sampling.json")
SEED = 42
SAMPLE_SIZE = 50
INTENTS = (
    "delivery_status_delay", "delivery_marked_delivered_missing", "return_refund",
    "item_condition_or_fulfilment", "order_cancellation_or_change",
    "prime_membership", "account_access_security", "payment_charge_issue",
    "product_availability_pricing", "marketplace_seller", "other_unclear",
)
AUDIT_FIELDS = (
    "example_id", "customer_message", "conversation_context",
    "retrieved_historical_evidence", "ai_generated_reply",
)
TEMPLATE_FIELDS = (
    "example_id", "reply_addresses_problem", "evidence_supported",
    "unsupported_claim", "human_escalation", "comment",
)


def load_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict) or not record.get("example_id"):
                raise ValueError(f"{path}:{line_number} must contain example_id")
            example_id = str(record["example_id"])
            if example_id in records:
                raise ValueError(f"duplicate generated example_id: {example_id}")
            records[example_id] = record
    return records


def _quotas(groups: dict[str, list[dict[str, str]]], size: int) -> dict[str, int]:
    if size < len(groups):
        raise ValueError("sample size must be at least the number of intents")
    total = sum(len(rows) for rows in groups.values())
    quotas = {intent: 1 for intent in groups}
    remaining = size - len(groups)
    exact = {intent: remaining * len(rows) / total for intent, rows in groups.items()}
    floors = {intent: int(value) for intent, value in exact.items()}
    quotas.update({intent: quotas[intent] + floors[intent] for intent in groups})
    leftover = size - sum(quotas.values())
    order = sorted(groups, key=lambda intent: (-(exact[intent] - floors[intent]), intent))
    for intent in order[:leftover]:
        quotas[intent] += 1
    return quotas


def select_rows(
    golden_rows: list[dict[str, str]],
    generated: dict[str, dict[str, Any]],
    seed: int = SEED,
    size: int = SAMPLE_SIZE,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Select exactly ``size`` rows, with every approved intent represented."""
    by_intent = {intent: [] for intent in INTENTS}
    for row in golden_rows:
        intent = row.get("human_intent", "")
        if intent not in by_intent:
            raise ValueError(f"unexpected or missing human_intent for {row.get('example_id')}")
        if row["example_id"] not in generated:
            raise ValueError(f"missing generated reply for {row['example_id']}")
        by_intent[intent].append(row)
    if any(not rows for rows in by_intent.values()):
        raise ValueError("every intent must have at least one source example")
    quotas = _quotas(by_intent, size)
    rng = random.Random(seed)
    selected = []
    for intent in INTENTS:
        selected.extend(rng.sample(by_intent[intent], quotas[intent]))
    rng.shuffle(selected)
    return selected, {intent: quotas[intent] for intent in INTENTS}


def build_audit_rows(
    selected: list[dict[str, str]], generated: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    rows = []
    for source in selected:
        record = generated[source["example_id"]]
        evidence = record.get("retrieved_examples", [])
        rows.append({
            "example_id": source["example_id"],
            "customer_message": source["customer_text"],
            "conversation_context": source.get("conversation_context", ""),
            "retrieved_historical_evidence": json.dumps(evidence, ensure_ascii=False),
            "ai_generated_reply": str(record.get("draft_reply", "")),
        })
    return rows


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def create_sample(
    golden_path: Path = GOLDEN,
    generations_path: Path = GENERATIONS,
    output_path: Path = OUTPUT,
    template_path: Path = TEMPLATE,
    report_path: Path = REPORT,
    seed: int = SEED,
    size: int = SAMPLE_SIZE,
) -> dict[str, Any]:
    with golden_path.open(encoding="utf-8", newline="") as handle:
        golden_rows = list(csv.DictReader(handle))
    generated = load_jsonl(generations_path)
    selected, counts = select_rows(golden_rows, generated, seed, size)
    audit_rows = build_audit_rows(selected, generated)
    write_csv(output_path, AUDIT_FIELDS, audit_rows)
    write_csv(template_path, TEMPLATE_FIELDS, [
        {"example_id": row["example_id"], **{field: "" for field in TEMPLATE_FIELDS if field != "example_id"}}
        for row in audit_rows
    ])
    summary = {
        "sample_size": len(audit_rows),
        "sampling_seed": seed,
        "selected_example_ids": [row["example_id"] for row in audit_rows],
        "per_intent_sample_counts": counts,
        "source_golden_examples": len(golden_rows),
        "source_generated_replies": len(generated),
        "annotation_labels_hidden": True,
        "source_files_modified": False,
        "source_files": [str(golden_path), str(generations_path)],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--size", type=int, default=SAMPLE_SIZE)
    args = parser.parse_args()
    summary = create_sample(seed=args.seed, size=args.size)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

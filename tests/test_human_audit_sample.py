import csv
import json
from pathlib import Path

from src.evaluation.create_human_audit_sample import (
    AUDIT_FIELDS, INTENTS, TEMPLATE_FIELDS, create_sample, select_rows,
)


def test_sample_is_exactly_50_and_stratified():
    golden = [
        {"example_id": f"{intent}-{i}", "human_intent": intent,
         "customer_text": f"customer {intent} {i}", "conversation_context": ""}
        for intent in INTENTS for i in range(10)
    ]
    generated = {
        row["example_id"]: {"example_id": row["example_id"],
                            "retrieved_examples": [], "draft_reply": "reply"}
        for row in golden
    }
    selected, counts = select_rows(golden, generated)
    assert len(selected) == 50
    assert len({row["example_id"] for row in selected}) == 50
    assert all(counts[intent] >= 1 for intent in INTENTS)


def test_selection_is_deterministic_and_ids_exist():
    golden = [
        {"example_id": f"{intent}-{i}", "human_intent": intent,
         "customer_text": "x", "conversation_context": ""}
        for intent in INTENTS for i in range(5)
    ]
    generated = {row["example_id"]: {} for row in golden}
    first, _ = select_rows(golden, generated, seed=42, size=50)
    second, _ = select_rows(golden, generated, seed=42, size=50)
    assert [row["example_id"] for row in first] == [row["example_id"] for row in second]
    assert {row["example_id"] for row in first} <= set(generated)


def test_created_csv_hides_labels_and_template_is_blank(tmp_path: Path):
    golden = tmp_path / "golden.csv"
    golden.write_text(
        "example_id,human_intent,customer_text,conversation_context\n"
        + "".join(f"{intent}-{i},{intent},question,\n" for intent in INTENTS for i in range(5)),
        encoding="utf-8",
    )
    generations = tmp_path / "replies.jsonl"
    generations.write_text("".join(json.dumps({
        "example_id": f"{intent}-{i}", "retrieved_examples": [{"customer_text": "q"}],
        "draft_reply": "reply"
    }) + "\n" for intent in INTENTS for i in range(5)), encoding="utf-8")
    audit, template, report = tmp_path / "audit.csv", tmp_path / "template.csv", tmp_path / "report.json"
    summary = create_sample(golden, generations, audit, template, report)
    assert summary["sample_size"] == 50
    with audit.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert tuple(rows[0]) == AUDIT_FIELDS
    assert "human_intent" not in rows[0]
    with template.open(encoding="utf-8", newline="") as handle:
        template_rows = list(csv.DictReader(handle))
    assert tuple(template_rows[0]) == TEMPLATE_FIELDS
    assert all(all(row[field] == "" for field in TEMPLATE_FIELDS[1:]) for row in template_rows)

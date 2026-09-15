import csv
import re
from pathlib import Path

from src.evaluation.create_human_audit_html import OUTPUT, SOURCE, build_html, load_rows


def test_html_embeds_exactly_50_unique_examples_without_hidden_labels():
    document = build_html(load_rows(SOURCE))
    ids = re.findall(r'"example_id":\s*"([^"]+)"', document)
    assert len(ids) == 50
    assert len(set(ids)) == 50
    assert "human_intent" not in document
    assert "grounding_confidence" not in document
    assert "needs_human_review" not in document
    assert "system_escalation" not in document
    assert "deterministic judge" not in document.lower()


def test_html_contains_required_questions_and_options():
    document = build_html(load_rows(SOURCE))
    for field in (
        "reply_addresses_problem",
        "evidence_supported",
        "unsupported_claim",
        "human_escalation",
        "comment",
    ):
        assert field in document
    assert '["yes", "partially", "no"]' in document
    assert '["yes", "partially", "no", "no_factual_claim"]' in document


def test_export_columns_match_annotation_template():
    document = build_html(load_rows(SOURCE))
    expected = (
        '["example_id", "reply_addresses_problem", "evidence_supported", '
        '"unsupported_claim", "human_escalation", "comment"]'
    )
    assert expected in document
    with Path("data/golden/human_audit_50_template.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        assert tuple(next(csv.reader(handle))) == (
            "example_id",
            "reply_addresses_problem",
            "evidence_supported",
            "unsupported_claim",
            "human_escalation",
            "comment",
        )


def test_generated_html_exists_and_has_all_examples():
    assert OUTPUT.exists()
    document = OUTPUT.read_text(encoding="utf-8")
    ids = re.findall(r'"example_id":\s*"([^"]+)"', document)
    assert len(ids) == 50
    assert "AI-generated reply" in document

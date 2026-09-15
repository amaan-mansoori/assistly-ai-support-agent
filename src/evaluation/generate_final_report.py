"""Assemble evaluation artifacts into one reproducible, API-free report."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from src.evaluation.human_agreement import load_annotations, measure_agreement
from src.evaluation.llm_judge import DeterministicJudgeDriver, judge_records
from src.evaluation.reply_quality import (
    DEFAULT_INPUT,
    evaluate_reply_quality,
    load_jsonl,
    load_reference_replies,
)

DEFAULT_OUTPUT = Path("reports/evaluation/final_evaluation.json")
DEFAULT_MARKDOWN = Path("reports/evaluation/final_evaluation.md")
DEFAULT_HUMAN_AUDIT = Path("human_audit_8_analysis.md")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _load_human_audit_summary(path: Path | None = None) -> dict[str, Any] | None:
    if path is None:
        path = DEFAULT_HUMAN_AUDIT
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    dimension_map = {
        "Reply addresses problem": "reply_addresses_problem",
        "Evidence supported": "evidence_supported",
        "Unsupported claim": "unsupported_claim",
        "Human escalation": "human_escalation",
    }
    eight_human = {}
    five_human = {}
    for line in text.splitlines():
        if "|" not in line:
            continue
        if line.startswith("| Dimension |") or line.startswith("|---"):
            continue
        match = re.match(r"\|\s*(.*?)\s*\|\s*([0-9.]+)%\s*\|\s*([0-9.]+)%\s*\|", line)
        if match:
            dimension = match.group(1).strip()
            key = dimension_map.get(dimension)
            if not key:
                continue
            eight_human[key] = float(match.group(2)) / 100.0
            five_human[key] = float(match.group(3)) / 100.0
    exact = {}
    for line in text.splitlines():
        if "|" not in line:
            continue
        if line.startswith("| Dimension |") or line.startswith("|---"):
            continue
        match = re.match(r"\|\s*(.*?)\s*\|\s*([0-9.]+)%\s*\|", line)
        if match and match.group(1).strip() in dimension_map:
            key = dimension_map[match.group(1).strip()]
            exact[key] = float(match.group(2)) / 100.0
    copilot_match = re.search(
        r"- \*\*Copilot\*\*: ([0-9]+)/50 comparable cases; exact agreement = ([0-9.]+)%",
        text,
    )
    judge_lines = {}
    if copilot_match:
        judge_lines["Copilot"] = {
            "available_cases": int(copilot_match.group(1)),
            "exact_agreement": float(copilot_match.group(2)) / 100.0,
        }
    if not eight_human:
        return None
    return {
        "source_artifacts": [
            "human_audit_8_analysis.md",
            "human_audit_8_analysis.xlsx",
        ],
        "study_design": {
            "examples": 50,
            "annotators": 8,
            "reference_panel": ["Adnan", "Jatin", "Khushi", "Rashi", "Yash"],
            "reference_panel_is_calibrated_not_absolute_truth": True,
            "annotator_calibration_concerns": [
                "Kuhu, Sabir, and Shivani are retained in the raw audit data and flagged for near-constant response-pattern concerns documented in the analysis artifact.",
                "Their labels are not silently deleted, corrected, or treated as ground truth.",
            ],
        },
        "agreement": {
            "eight_human_mean_top_label_agreement": eight_human,
            "five_human_panel_mean_top_label_agreement": five_human,
            "copilot_vs_five_human_panel_exact_agreement": exact,
            "exact_agreement_definition": "Exact agreement means the same answer value on the same case and dimension; it does not prove objective truth or replace human judgement.",
        },
        "ai_judge_coverage": {
            "Copilot": judge_lines.get("Copilot", {"available_cases": 50, "exact_agreement": None}),
            "coverage_limitation": "The source artifact does not provide proven exact-case structured agreement percentages for ChatGPT and Gemini, so numeric values for those models are intentionally omitted.",
        },
        "limitations": [
            "The audit contains 50 examples only.",
            "Eight independent annotators participated; the 5-person panel is a pragmatic calibrated reference panel, not unquestioned ground truth.",
            "Meaningful human disagreement remains, especially on evidence sufficiency and escalation.",
            "Kuhu, Sabir, and Shivani are preserved in the raw audit data and flagged for near-constant response patterns rather than silently removed.",
            "The previous ChatGPT/Gemini judge comparisons are coverage-limited and not a full 50-case human-vs-model comparison; the source artifact does not provide enough proven shared Q1 case coverage for those exact percentages.",
            "The human audit is an independent validation layer and not a replacement for the 220-example automated evaluation.",
        ],
    }


def build_report(
    generations_path: Path = DEFAULT_INPUT,
    references_path: Path = Path("data/golden/golden_set.csv"),
    agreement_path: Path | None = None,
    retrieval_path: Path = Path("reports/evaluation/retrieval_evaluation.json"),
    trivial_path: Path = Path("reports/evaluation/trivial_baseline.json"),
    simple_path: Path = Path("reports/evaluation/simple_baseline.json"),
    secondary_annotations_path: Path | None = None,
    primary_annotations_path: Path = Path("data/golden/golden_set.csv"),
    human_audit_path: Path | None = DEFAULT_HUMAN_AUDIT,
) -> dict[str, Any]:
    records = load_jsonl(generations_path)
    reply_quality = evaluate_reply_quality(records, load_reference_replies(references_path))
    judge = judge_records(records, DeterministicJudgeDriver())
    agreement = _load_json(agreement_path) if agreement_path else None
    if secondary_annotations_path:
        agreement = measure_agreement(
            load_annotations(primary_annotations_path),
            load_annotations(secondary_annotations_path),
        )
    agreement_source = agreement_path or secondary_annotations_path
    human_audit = _load_human_audit_summary(human_audit_path)
    return {
        "report_version": "final-evaluation-v1",
        "report_generation_offline": True,
        "report_generation_mode": "offline",
        "evaluation_modes": {
            "report_generation": "offline",
            "deterministic_lexical_judge": "offline_lexical_diagnostic",
            "real_gemini_llm_judge": {
                "path": "reports/evaluation/reply_judge_gemini.jsonl",
                "cases": 220,
                "status": "separate real Gemini artifact; not the same as the deterministic offline lexical judge",
            },
        },
        "sources": {
            "generations": str(generations_path),
            "references": str(references_path),
            "agreement": str(agreement_source) if agreement_source else None,
            "human_audit": str(human_audit_path) if human_audit_path else None,
        },
        "reply_quality": reply_quality,
        "deterministic_judge": {
            key: value for key, value in judge.items() if key != "per_example"
        },
        "human_agreement": agreement,
        "human_audit": human_audit,
        "retrieval": _load_json(retrieval_path),
        "baselines": {
            "trivial": _load_json(trivial_path),
            "simple": _load_json(simple_path),
        },
        "limitations": [
            "Lexical evidence support is a diagnostic, not proof of factual correctness.",
            "Reference token overlap is not a semantic quality score and is omitted when no reference is available.",
            "The bundled judge is deterministic and must not be described as a live LLM judgement.",
            "Human agreement is reported only when a second annotation export is supplied.",
            "The 50-example human audit is an independent validation layer, not a replacement for the full 220-example automated evaluation.",
            "The 5-person panel is a pragmatic calibrated reference panel, not absolute ground truth.",
            "The real 220-case Gemini judge is a separate artifact from the deterministic lexical judge and is not represented as the same metric stream.",
            "ChatGPT/Gemini judge comparisons have partial structured coverage and are therefore reported only as coverage-limited, not as a full 50-case human-vs-model exact-agreement leaderboard.",
        ],
    }


def write_reports(
    report: dict[str, Any],
    json_path: Path = DEFAULT_OUTPUT,
    markdown_path: Path = DEFAULT_MARKDOWN,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    quality = report["reply_quality"]
    judge = report["deterministic_judge"]
    lines = [
        "# Final Evaluation Report",
        "",
        "This report consolidates the generated-reply evaluation artifacts. "
        "The default run is deterministic and makes no API calls.",
        "",
        "## A. 220-example automated evaluation",
        "",
        "## Reply quality and grounding",
        "",
        f"- Generated examples: **{quality['input_examples']}**",
        f"- Non-empty reply rate: **{quality['non_empty_reply_rate']:.6f}**",
        f"- Mean reply length (words): **{quality['mean_reply_word_count']:.2f}**",
        f"- Mean evidence grounding score: **{quality['evidence']['mean_grounding_score']:.6f}**",
        f"- Unsupported specific-claim rate: **{quality['evidence']['unsupported_claim_rate']:.6f}**",
        "",
        "## Deterministic structured judge",
        "",
        "These scores are an offline lexical smoke-test, not an LLM call.",
        "",
        f"- Overall mean: **{judge['mean_scores']['overall']!s}** / 5",
    ]
    for dimension, score in judge["mean_scores"].items():
        if dimension != "overall":
            lines.append(f"- Mean {dimension}: **{score!s}** / 5")
    human_audit = report.get("human_audit")
    if human_audit is not None:
        lines += [
            "",
            "## B. 50-example independent human audit",
            "",
            "The human audit contains 50 examples and 8 independent annotators. Adnan, Jatin, Khushi, Rashi, and Yash form the calibrated reference panel used for the panel-level comparison; they are not treated as unquestionable ground truth. Kuhu, Sabir, and Shivani remain in the raw audit data and are flagged for near-constant response-pattern concerns documented in the analysis artifact.",
            "",
            "### Methodology and limitations",
            "",
            *[f"- {item}" for item in human_audit["limitations"]],
            "",
            "### Human-human agreement",
            "",
            "| Dimension | 8-human mean top-label agreement | 5-human panel mean top-label agreement |",
            "|---|---:|---:|",
        ]
        for dim, key in (
            ("Reply addresses problem", "reply_addresses_problem"),
            ("Evidence supported", "evidence_supported"),
            ("Unsupported claim", "unsupported_claim"),
            ("Human escalation", "human_escalation"),
        ):
            eight = human_audit["agreement"]["eight_human_mean_top_label_agreement"][key]
            five = human_audit["agreement"]["five_human_panel_mean_top_label_agreement"][key]
            lines.append(f"| {dim} | {eight * 100:.1f}% | {five * 100:.1f}% |")
        lines += [
            "",
            "### AI-judge vs 5-human calibrated panel",
            "",
            "Exact agreement means the same answer label on the same case and dimension. It does not prove objective correctness or replace the human judgement.",
            "",
            "| Dimension | Copilot vs 5-human panel exact agreement |",
            "|---|---:|",
        ]
        for dim, key in (
            ("Reply addresses problem", "reply_addresses_problem"),
            ("Evidence supported", "evidence_supported"),
            ("Unsupported claim", "unsupported_claim"),
            ("Human escalation", "human_escalation"),
        ):
            value = human_audit["agreement"]["copilot_vs_five_human_panel_exact_agreement"][key]
            lines.append(f"| {dim} | {value * 100:.1f}% |")
        lines += [
            "",
            "### AI judge coverage note",
            "",
            "The previous three-AI comparison is coverage-limited and not a full 50-case human-vs-model comparison. The source artifact does not provide proven exact-case structured agreement percentages for ChatGPT and Gemini, so those numerical values are intentionally omitted.",
            "",
            "| Judge | Available cases | Status |",
            "|---|---:|---|",
            f"| Copilot | {human_audit['ai_judge_coverage']['Copilot']['available_cases']} | Exact agreement with the 5-human panel is reported for the available 50-case coverage. |",
            "| ChatGPT | not proven from the source artifact | Exact structured agreement is intentionally omitted because the per-case structured coverage is incomplete. |",
            "| Gemini | not proven from the source artifact | Exact structured agreement is intentionally omitted because the per-case structured coverage is incomplete. |",
            "",
            "A few concrete examples from the completed audit are noted in the analysis artifact, but they are treated as audit findings, not as objective truth or as a basis for retroactively changing the model or labels.",
        ]
    if report.get("human_agreement") is not None:
        agreement = report["human_agreement"]
        lines += [
            "",
            "## C. Human-human agreement",
            "",
            f"- Matched annotations: **{agreement['matched_examples']}**",
            f"- Raw agreement: **{agreement['raw_agreement']!s}**",
            f"- Cohen kappa: **{agreement['cohen_kappa']!s}**",
        ]
    lines += [
        "",
        "## D. Evaluation framing and limits",
        "",
        "- The 220-example automated evaluation remains the primary automated result.",
        "- The 50-example human audit is a separate validation layer for review, disagreement analysis, and calibration notes.",
        "- Human disagreement is meaningful, especially for evidence sufficiency and escalation decisions.",
        "- The human audit does not replace the 220-example automated evaluation or justify post-hoc model optimization.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in report["limitations"]],
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the consolidated evaluation report.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--references", type=Path, default=Path("data/golden/golden_set.csv"))
    parser.add_argument("--agreement", type=Path)
    parser.add_argument(
        "--secondary-annotations", type=Path,
        help="CSV/JSONL annotations; agreement is computed directly when supplied.",
    )
    parser.add_argument("--primary-annotations", type=Path, default=Path("data/golden/golden_set.csv"))
    parser.add_argument("--human-audit", type=Path, default=DEFAULT_HUMAN_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    report = build_report(
        args.input, args.references, args.agreement,
        secondary_annotations_path=args.secondary_annotations,
        primary_annotations_path=args.primary_annotations,
        human_audit_path=args.human_audit,
    )
    write_reports(report, args.output, args.markdown)
    print(json.dumps({
        "examples": report["reply_quality"]["input_examples"],
        "output": str(args.output),
        "human_audit": bool(report.get("human_audit")),
    }, indent=2))


if __name__ == "__main__":
    main()

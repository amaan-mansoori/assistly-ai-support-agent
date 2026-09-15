"""Build the offline HTML form for the 50-example human audit."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SOURCE = Path("data/golden/human_audit_50.csv")
OUTPUT = Path("data/golden/human_audit_50.html")


def load_rows(path: Path = SOURCE) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "example_id",
        "customer_message",
        "conversation_context",
        "retrieved_historical_evidence",
        "ai_generated_reply",
    }
    if not rows or set(rows[0]) != required:
        raise ValueError("audit CSV has unexpected or missing columns")
    if len(rows) != 50 or len({row["example_id"] for row in rows}) != 50:
        raise ValueError("audit CSV must contain exactly 50 unique examples")
    return rows


def build_html(rows: list[dict[str, str]]) -> str:
    # JSON is embedded as data only; the browser never needs to read a local CSV.
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Independent Human Reply Audit</title>
<style>
:root {{ color-scheme: light; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
body {{ margin: 0; background: #f4f6f8; color: #17202a; }}
main {{ max-width: 1050px; margin: 0 auto; padding: 24px; }}
header, .panel, .question {{ background: white; border: 1px solid #d8dee4; border-radius: 10px; padding: 20px; margin-bottom: 16px; }}
h1 {{ margin-top: 0; font-size: 1.7rem; }}
h2 {{ font-size: 1.15rem; margin-top: 0; }}
.notice {{ background: #fff8df; border-color: #e5c767; }}
.privacy {{ background: #eef6ff; border-color: #9dc7ef; font-weight: 600; }}
#progress {{ font-weight: 700; color: #245b8d; }}
.example-header {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; flex-wrap: wrap; }}
.field-label {{ display: block; font-weight: 700; margin-bottom: 8px; }}
.content {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #f8fafb; border-left: 4px solid #9aa9b5; padding: 12px; border-radius: 4px; max-height: 260px; overflow: auto; }}
.reply {{ border-left-color: #4d8b62; background: #f2faf4; }}
.evidence {{ font-size: .92rem; }}
.question legend {{ font-weight: 700; padding: 0 4px; }}
.options {{ display: flex; gap: 18px; flex-wrap: wrap; }}
.options label {{ cursor: pointer; padding: 7px 10px; border-radius: 6px; }}
.options label:hover {{ background: #eef3f7; }}
textarea {{ width: 100%; min-height: 70px; box-sizing: border-box; font: inherit; padding: 8px; }}
button {{ border: 0; border-radius: 6px; padding: 10px 16px; font: inherit; font-weight: 700; cursor: pointer; }}
button:disabled {{ cursor: not-allowed; opacity: .45; }}
.primary {{ background: #1769aa; color: white; }}
.secondary {{ background: #e7edf2; color: #17202a; }}
.actions {{ display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; }}
.status {{ min-height: 1.4em; color: #8a2c2c; font-weight: 600; }}
small {{ color: #52606d; }}
</style>
</head>
<body>
<main>
<header>
<h1>Independent Human Reply Audit</h1>
<p>Review each customer message, the historical evidence shown, and the AI-generated reply.</p>
<div id="progress" aria-live="polite"></div>
</header>
<section class="panel notice">
<h2>Instructions</h2>
<ul>
<li>Judge only what is shown.</li>
<li>Do not use outside Amazon knowledge to fill missing evidence.</li>
<li>Do not try to guess what the model intended.</li>
<li>If uncertain, use “partially” where available.</li>
<li>No coding or machine-learning knowledge is required.</li>
<li>Do not look for or infer the hidden original intent label.</li>
</ul>
</section>
<section class="panel privacy">This is an independent evaluation. Do not inspect or use the project's hidden labels or model scores while annotating.</section>
<section id="example"></section>
<div class="actions">
<button class="secondary" id="previous" type="button">Previous</button>
<button class="secondary" id="next" type="button">Next</button>
<button class="primary" id="export" type="button">Export Answers</button>
</div>
<p class="status" id="status" role="status"></p>
<small>Answers are kept in this browser tab while you move between examples. Export the CSV when finished.</small>
</main>
<script>
"use strict";
const examples = {data};
const answers = examples.map((item) => ({{
  example_id: item.example_id,
  reply_addresses_problem: "",
  evidence_supported: "",
  unsupported_claim: "",
  human_escalation: "",
  comment: ""
}}));
let current = 0;
const fields = [
  ["reply_addresses_problem", "Q1: Does the AI reply address the customer's problem?", ["yes", "partially", "no"]],
  ["evidence_supported", "Q2: Are the important factual claims in the AI reply supported by the historical responses shown?", ["yes", "partially", "no", "no_factual_claim"]],
  ["unsupported_claim", "Q3: Does the AI reply contain information that appears invented, unsupported, or overly certain?", ["yes", "no"]],
  ["human_escalation", "Q4: Should this case be handled by a human support agent instead of being automatically handled?", ["yes", "no"]]
];
const esc = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#39;");
function render() {{
  const item = examples[current];
  const answer = answers[current];
  document.getElementById("progress").textContent =
    `Example ${{current + 1}} of ${{examples.length}} · ${{answers.filter(isComplete).length}}/${{examples.length}} completed`;
  const evidence = (() => {{
    try {{
      const parsed = JSON.parse(item.retrieved_historical_evidence || "[]");
      return JSON.stringify(parsed, null, 2);
    }} catch (_) {{
      return item.retrieved_historical_evidence || "";
    }}
  }})();
  let content = `<div class="example-header"><h2>${{esc(item.example_id)}}</h2><small>Required: answer Q1–Q4</small></div>`;
  content += `<div class="panel"><span class="field-label">Customer message</span><div class="content">${{esc(item.customer_message)}}</div></div>`;
  content += `<div class="panel"><span class="field-label">Relevant conversation context</span><div class="content">${{esc(item.conversation_context) || "No additional context provided."}}</div></div>`;
  content += `<div class="panel"><span class="field-label">Retrieved historical evidence/examples</span><div class="content evidence">${{esc(evidence) || "No historical evidence provided."}}</div></div>`;
  content += `<div class="panel"><span class="field-label">AI-generated reply</span><div class="content reply">${{esc(item.ai_generated_reply)}}</div></div>`;
  for (const [key, label, options] of fields) {{
    content += `<fieldset class="question"><legend>${{esc(label)}}</legend><div class="options">`;
    for (const option of options) {{
      const checked = answer[key] === option ? " checked" : "";
      content += `<label><input type="radio" name="${{key}}" value="${{option}}"${{checked}}> ${{option}}</label>`;
    }}
    content += "</div></fieldset>";
  }}
  content += `<div class="question"><label class="field-label" for="comment">Q5: Optional comment/reason</label><textarea id="comment" placeholder="Optional short reason or comment">${{esc(answer.comment)}}</textarea></div>`;
  document.getElementById("example").innerHTML = content;
  document.querySelectorAll("input[type=radio]").forEach((input) => input.addEventListener("change", () => {{
    answer[input.name] = input.value;
    updateStatus();
  }}));
  document.getElementById("comment").addEventListener("input", (event) => {{ answer.comment = event.target.value; }});
  document.getElementById("previous").disabled = current === 0;
  document.getElementById("next").disabled = current === examples.length - 1;
  updateStatus();
}}
function isComplete(answer) {{ return fields.every(([key]) => Boolean(answer[key])); }}
function updateStatus() {{
  document.getElementById("progress").textContent =
    `Example ${{current + 1}} of ${{examples.length}} · ${{answers.filter(isComplete).length}}/${{examples.length}} completed`;
  document.getElementById("status").textContent = isComplete(answers[current]) ? "" : "Please answer Q1–Q4 before moving to another example.";
}}
function move(delta) {{
  if (!isComplete(answers[current])) {{ updateStatus(); return; }}
  current += delta;
  render();
  window.scrollTo(0, 0);
}}
function csvCell(value) {{
  return `"${{String(value ?? "").replaceAll('"', '""')}}"`;
}}
function exportAnswers() {{
  const columns = ["example_id", "reply_addresses_problem", "evidence_supported", "unsupported_claim", "human_escalation", "comment"];
  const csv = [columns.join(","), ...answers.map((row) => columns.map((column) => csvCell(row[column])).join(","))].join("\\r\\n") + "\\r\\n";
  const blob = new Blob([csv], {{type: "text/csv;charset=utf-8"}});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "human_audit_50_answers.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}}
document.getElementById("previous").addEventListener("click", () => move(-1));
document.getElementById("next").addEventListener("click", () => move(1));
document.getElementById("export").addEventListener("click", exportAnswers);
render();
</script>
</body>
</html>
"""


def create_html(source: Path = SOURCE, output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_html(load_rows(source)), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    create_html(args.source, args.output)
    print(f"Wrote {args.output} with 50 examples")


if __name__ == "__main__":
    main()

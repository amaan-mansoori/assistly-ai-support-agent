# Independent Retrieval Evaluation Verification — 2026-10-10

## Current status

This report concerns query-to-candidate **retrieval relevance**, not the
separate human reply-quality audit documented in
[`final_evaluation.md`](final_evaluation.md). The current pair-level workflow
is described in
[`independent_retrieval_evaluation.md`](independent_retrieval_evaluation.md)
and implemented in `src/evaluation/retrieval_relevance_workflow.py`.

The frozen benchmark has 50 query IDs and five ranked candidate replies per
query (250 query-candidate pairs). The retrieval candidates are sourced from
the persisted retrieval output; candidate IDs are pseudonymous. The two
reviewer JSONL exports are generated under the ignored
`reports/evaluation/human_annotation_exports/` directory. Their expected
state before review is blank `relevance_grade` plus a pseudonymous reviewer ID.
Existing broad reply-audit templates are not valid retrieval labels.
The reviewer and candidate IDs are pseudonymous, but the included query and
candidate text is not fully de-identified: verification found Twitter handles
in the evidence fields. Keep the exports access-controlled and do not repeat
handles in rationales.

No completed independent retrieval relevance submissions or adjudicated
judgments were found in the repository state inspected for this report.
Accordingly, Recall@1/3/5, MRR, and graded nDCG@1/3/5 are **NOT MEASURED**.
Same-intent retrieval proxies and reply-quality audit labels are not substitutes.

## Tooling verification versus human completion

Passing schema, workflow, or metric-fixture tests verifies software behavior
only. It does not establish human review completion, relevance quality, or
benchmark scores. The following manual work remains: two independent reviewers
must grade all 250 pairs (or record valid query exclusions), submissions must
pass validation, and every disagreement must receive a traceable adjudication.
Only then may the evaluator report real benchmark metrics.

## Commands

From the repository root, with the project environment installed:

```powershell
& .\.venv\Scripts\python.exe -m src.evaluation.retrieval_relevance_workflow export
& .\.venv\Scripts\python.exe -m src.evaluation.retrieval_relevance_workflow validate `
  --submission reports\evaluation\human_annotation_exports\retrieval-relevance-reviewer-01.jsonl
& .\.venv\Scripts\python.exe -m src.evaluation.retrieval_relevance_workflow validate `
  --submission reports\evaluation\human_annotation_exports\retrieval-relevance-reviewer-02.jsonl
```

Export refuses to overwrite existing reviewer files. Validate both completed
submissions, then follow the adjudication and evaluation command sequence in
the linked protocol. Do not run export over completed reviewer evidence.

## Historical verification record

An earlier version described the separate generic evidence/reply annotation
workflow. Those older tests do not validate the current pair-level retrieval
workflow. In the final offline verification pass, the focused pair-level test
command
`.\.venv\Scripts\python.exe -m pytest tests\test_retrieval_relevance_workflow.py -q`
exited 0 with **14 passed**. The complete command
`.\.venv\Scripts\python.exe -m pytest -q` exited 0 with **252 passed**.
The CI-scoped Ruff command exited 0 (`All checks passed!`), the evaluation
regression gate exited 0 (`passed: true`), and `git diff --check` exited 0.
These results verify tooling, not human judgments or relevance performance.
Both current reviewer files contain 250 unique expected pairs, pass the
JSON Schema, and have blank grades and rationales; no benchmark metrics are
measured.

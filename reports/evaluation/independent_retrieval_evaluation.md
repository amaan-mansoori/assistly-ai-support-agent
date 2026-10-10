# Independent Human-Judged Retrieval Evaluation

## Status

The independent **retrieval relevance** annotation workflow is implemented in
`src/evaluation/retrieval_relevance_workflow.py`, with its separate record
contract in `retrieval_relevance_schema_v1.json`. It is intentionally distinct
from the completed human reply-quality audit described in
[`final_evaluation.md`](final_evaluation.md); none of that audit's labels or
agreement results are used as retrieval relevance judgments.

The verified benchmark has **50 queries and 250 query-candidate pairs** (five
ranked retrieved replies per query). Queries are hydrated by stable example ID
from the frozen dataset; candidate IDs and text come from the existing
retrieval-generation artifact. The workflow pins the dataset, sample, and
retrieval artifact SHA-256 values into every reviewer row and refuses to
silently overwrite reviewer exports.

There are **no completed independent human retrieval judgments** in the
repository. Existing broad reply-audit templates and exports are not suitable
for this task. No relevance labels or benchmark metrics are fabricated; the
Recall@K, MRR, and nDCG values remain unmeasured until two independent reviewers
complete the new templates and disagreements are adjudicated.

`python -m src.evaluation.evaluate_retrieval` continues to report
`intent-match@k`; that taxonomy-based heuristic proxy against provisional
reference labels is not independent relevance ground truth. The pre-existing
`src.evaluation.independent_retrieval_evaluation` module is retained as a
separate evaluator for the general evidence/reply annotation schema; it does
not consume the new pair-level templates.

## Review protocol

Run export from the repository root using the project interpreter. Exports
are placed under the ignored `reports/evaluation/human_annotation_exports/`
directory and contain the query text plus the retrieved historical support
reply text needed for a relevance decision; restrict access to the files and
do not upload them to a public location.

```powershell
& .\.venv\Scripts\python.exe -m src.evaluation.retrieval_relevance_workflow export
```

Give `retrieval-relevance-reviewer-01.jsonl` and
`retrieval-relevance-reviewer-02.jsonl` to two independent reviewers. Each
reviewer must retain every row and fill `relevance_grade` and `reviewer_id`.
Grades are:

- `2`: directly relevant and useful for answering the query.
- `1`: partially relevant or useful supporting context.
- `0`: not relevant to this query.
- `null`/blank: not reviewed; incomplete and never treated as grade zero.

Judge whether the historical support response is relevant to the customer's
query. Do not rate writing quality, politeness, or whether the response is a
good reply in general. Candidate ranks are frozen to the evaluated retrieval
run. Query IDs are stable sample IDs; candidate IDs are stable SHA-256
pseudonyms of the historical response IDs, so raw source tweet IDs are not
included in the export. Use a short optional rationale only to explain an
ambiguous decision.
Use stable pseudonymous reviewer IDs, never names or contact information.
The IDs are pseudonymous, but the included source evidence text is not fully
de-identified: it contains Twitter `@` handles. Treat reviewer exports as
sensitive, share them only with the authorized reviewers, and do not repeat
handles or other identifying text in rationales.

If the query/candidate source cannot be reviewed, record it in a separate
exclusion JSONL matching `reports/evaluation/exclusion_schema_v1.json`: include
`exclusion_version`, `dataset_version`, `dataset_sha256`, `example_id`,
pseudonymous `excluded_by`, `reason`, and `status: "excluded"`. Remove all
candidate rows for that query from both reviewer files. Excluded queries must
not also have judgments; report them separately. Both reviewers must use the
same exclusions.

Validate both submissions before adjudication:

```powershell
& .\.venv\Scripts\python.exe -m src.evaluation.retrieval_relevance_workflow validate `
  --submission reports\evaluation\human_annotation_exports\retrieval-relevance-reviewer-01.jsonl
& .\.venv\Scripts\python.exe -m src.evaluation.retrieval_relevance_workflow validate `
  --submission reports\evaluation\human_annotation_exports\retrieval-relevance-reviewer-02.jsonl
```

Agreement is accepted directly. For each disagreement, the adjudicator creates
one decision row containing `query_id`, `candidate_id`, `final_grade` (0/1/2),
`adjudicator_id` (pseudonymous), and optional `rationale`. Do not add decisions
for agreed pairs. The tool requires every disagreement and rejects unknown or
duplicate decisions. If there are no disagreements, omit `--decisions`. A
decision JSONL row has this form:

```json
{"query_id":"golden-set-0007","candidate_id":"candidate-<64-hex-sha256>","final_grade":1,"adjudicator_id":"review-lead","rationale":"Useful supporting context."}
```

```powershell
& .\.venv\Scripts\python.exe -m src.evaluation.retrieval_relevance_workflow adjudicate `
  --reviewer-a reports\evaluation\human_annotation_exports\retrieval-relevance-reviewer-01.jsonl `
  --reviewer-b reports\evaluation\human_annotation_exports\retrieval-relevance-reviewer-02.jsonl `
  --output reports\evaluation\human_annotation_exports\retrieval-relevance-adjudicated.jsonl
```

With a decision file, add `--decisions path\to\adjudication-decisions.jsonl`.
When exclusions are used, pass the same `--exclusions path\to\exclusions.jsonl`
to both validation commands, adjudication, and evaluation.

```powershell
& .\.venv\Scripts\python.exe -m src.evaluation.retrieval_relevance_workflow evaluate `
  --adjudicated reports\evaluation\human_annotation_exports\retrieval-relevance-adjudicated.jsonl `
  --output reports\evaluation\retrieval_relevance_metrics.json
```

Evaluation rejects missing pairs and any non-adjudicated grade. Its output
includes sample and judgment coverage, exclusions, queries with no positive
candidate, and provenance hashes. Output artifacts are created only after
valid labels exist; it refuses to overwrite an existing output.

## Metric definitions

- **Relevant:** grades `1` and `2`; grade `0` is explicitly judged irrelevant.
- **Recall@K:** per query, number of grade-positive candidates in the top K
  divided by the number of positive candidates among that query's five judged
  candidates. Macro-average across queries with at least one positive grade.
- **MRR:** macro-average reciprocal rank of the first grade-positive candidate
  across those same queries.
- **nDCG@K:** gain is `2^grade - 1`, discounted by `log2(rank + 1)`, and
  normalized by the ideal ordering of the five judged candidate grades.
  Macro-average over the same queries with at least one positive grade.
- **Zero-positive query:** counted as judged, but excluded from the three
  metric averages; its count is reported separately. If there are no
  positive-grade queries, metric values are `null`, not fabricated zeros.
- **K values:** 1, 3, and 5, matching the fixed candidate depth.
- **Exclusions:** excluded query IDs are not scored and are reported apart from
  reviewed coverage. Other missing query/candidate judgments make the input
  incomplete and evaluation fails rather than silently shrinking the sample.

This benchmark judges only the five retrieved candidates, not the full corpus.
Therefore Recall@K is relative to the judged top-five pool; unjudged corpus
items are unknown, not negative. Hashes bind inputs to the frozen data and
retrieval artifact, but do not establish the upstream label provenance, which
remains `unresolved_provisional`.

## Verification versus annotation completion

Code and synthetic fixtures can validate the workflow and metric arithmetic.
That is tooling verification only. Retrieval annotation is pending until two
human reviewers complete all 250 query-candidate rows (or document exclusions),
both submissions validate, and every disagreement receives adjudication. No
independent retrieval metric is currently measured.

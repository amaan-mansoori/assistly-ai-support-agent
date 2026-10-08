# Golden-Set Annotation Guide

This guide is intended for a future traceable human annotation pass. Regex and cluster outputs are sampling aids, not ground truth. Read the customer inquiry with available preceding turns and the AmazonHelp response, but label the customer's primary support goal. The checked-in golden-set labels currently have unresolved provenance and must not be treated as human ground truth.

## Labels and criteria

- `delivery_status_delay`: late, stuck, not dispatched, failed attempt, or where-is-my-order without delivered-but-missing evidence.
- `delivery_marked_delivered_missing`: tracking says delivered/handed off, but the parcel cannot be found.
- `return_refund`: return, replacement, pickup/label, or refund timing/amount after a transaction.
- `item_condition_or_fulfilment`: wrong, damaged, defective, expired, empty, or incomplete item/package.
- `order_cancellation_or_change`: cancel or modify an order, including address changes and disputed automated cancellation.
- `prime_membership`: Prime fees, trial, renewal, eligibility, cancellation, or benefits; incidental Prime does not control.
- `account_access_security`: sign-in, password, verification, hold, suspension, or suspicious access.
- `payment_charge_issue`: unauthorized, duplicate, failed, or disputed card, bank, billing, or Amazon Pay charge; expected return refunds are `return_refund`.
- `product_availability_pricing`: stock/restock, pre-order, price/deal, coupon/promotion, authenticity, or pre-purchase product information.
- `marketplace_seller`: third-party seller communication, seller fulfillment, counterfeit/seller dispute, or marketplace responsibility.
- `other_unclear`: no defensible primary goal, insufficient context, social feedback, greeting/acknowledgment, or unresolved ambiguity.

`conversational_followup` is not an intent.

## Precedence, multi-intent, and context

Use the explicit requested remedy over incidental background. Delivered-plus-not-received beats generic delivery delay. A clear return/refund request beats item condition; seller-specific intervention beats generic delivery; Prime membership action beats generic payment. For equally important goals, choose the clearest primary action and document the secondary issue; if no primary goal is defensible, use `other_unclear`.

Follow actual parent IDs in the supplied context; never infer context from row order, time, or author adjacency. A short follow-up inherits the prior issue when that issue is clear, but there is no follow-up label. Information-only replies (order number, email, details) retain the prior issue when clear, otherwise use `other_unclear`.

## Ambiguity examples

Use `other_unclear` for a message such as real tweet `969869` (“????”) when context does not establish a goal. Real tweet `423267` mentions a call-centre failure while its response discusses delivery; inspect context rather than forcing keywords. Real tweet `741527` combines missing order confirmation and a missing gift card; choose only if context establishes the primary goal.

For a future annotation, record a concise rationale in `annotation_notes` and keep annotator identity/review history in a separately access-controlled record. No human annotation or agreement result is asserted by this guide.

## Versioned future evaluation annotations

`reports/evaluation/annotation_schema_v1.json` defines a separate annotation
record for future independently reviewed evaluation. It supports expected
intent, per-evidence relevance, evidence sufficiency/conflict, expected
escalation, acceptable-answer criteria, and unsupported-claim categories.
Use the frozen example ID and evidence IDs; do not edit or replace labels in
`data/golden/golden_set.csv`.

The schema is a workflow definition, not an annotation dataset. No new human
annotations, adjudications, or agreement measurements were performed for this
phase. Keep any annotator identity and any free-text notes outside tracked
artifacts under access controls; the tracked record schema deliberately stores
categorical judgments only.

## Human-grounded evaluation v2

`reports/evaluation/human_annotation_sample_v1.json` is a separate 50-ID
sample from the frozen dataset. IDs are selected by a versioned SHA-256 ordering
that does not use `human_intent` or any other provisional label. The manifest
contains no customer text. Verify the frozen dataset before giving authorized
annotators access to the corresponding rows; provide only the customer
conversation and candidate evidence needed for a task, through an access-
controlled channel.

Create one private template per pseudonymous annotator:

```powershell
python -m src.evaluation.human_grounded_evaluation create-template `
  --annotator-id reviewer-01 `
  --output reports/evaluation/human_annotation_exports/reviewer-01.jsonl
```

Annotators independently assign the primary intent; score every reviewed
evidence item as **0 irrelevant**, **1 partially relevant**, or **2 directly
relevant**; record evidence sufficiency; and independently decide whether a
human should handle the case. Do not infer expected escalation from Assistly's
decision. `relevant_evidence_ids` must list the evidence with score 1 or 2.
Acceptable-answer criteria are categorical requirements, not rationale.
Reviewers can add multiple run-specific entries to `response_assessments` for
acceptability, groundedness, and unsupported claims. Use the exact run ID,
present each output only through an approved access-controlled channel, and do
not copy reply text into annotation or failure artifacts. Use `not_annotated`
or `uncertain` rather than guessing.

Validate submissions, find disagreements, and calculate agreement:

```powershell
python -m src.evaluation.human_grounded_evaluation validate `
  --annotations reports/evaluation/human_annotation_exports/combined.jsonl
python -m src.evaluation.human_grounded_evaluation agreement `
  --annotations reports/evaluation/human_annotation_exports/combined.jsonl
```

Agreement reports use Cohen's kappa for two annotators, Fleiss' kappa for
three or more annotators with balanced ratings, and quadratic-weighted Cohen's
kappa for shared ordinal evidence ratings from two annotators. They report
coverage, explicit disagreement IDs, and `null` when data are too sparse or
degenerate. No coefficient is reported as actual until real submissions exist.
An adjudicator resolves disagreements in a separate record and never overwrites
the independent submissions.

For each example with at least two complete, independent submissions, prepare
a JSON object containing all `final_labels` fields from the adjudication
schema. The CLI validates it and appends a separate adjudication record:

```powershell
python -m src.evaluation.human_grounded_evaluation adjudicate `
  --annotations reports/evaluation/human_annotation_exports/combined.jsonl `
  --example-id golden-set-0007 `
  --adjudicator-id review-lead `
  --final-labels reports/evaluation/human_annotation_exports/golden-set-0007-final-labels.json `
  --output reports/evaluation/human_annotation_exports/adjudicated.jsonl
```

Only adjudicated records are scored against a system run. Human Recall@K counts
retrieved evidence IDs with independent relevance score greater than zero;
MRR uses the first such result. Evidence sufficiency and escalation metrics
use only adjudicated, known labels. Response quality, groundedness, and
unsupported-claim metrics require a human response assessment tied to the exact
run ID. Missing labels, run-mismatched response reviews, latency, provider
usage, and cost remain unavailable rather than being inferred.

The human-grounded comparison accepts the existing side-by-side comparison
artifact so majority, TF-IDF + Logistic Regression, and Assistly are scored
against the same adjudications without merging those values with provisional
Phase 4/5 results. Use the Assistly run ID for its response assessment; baseline
response reviews use the comparison run ID suffixed with `:majority` or
`:tfidf_logistic_regression`:

```powershell
python -m src.evaluation.human_grounded_evaluation compare-systems `
  --comparison reports/evaluation/runs/<run-id>.comparison.json `
  --annotations reports/evaluation/human_annotation_exports/combined.jsonl `
  --adjudications reports/evaluation/human_annotation_exports/adjudicated.jsonl `
  --output reports/evaluation/human_grounded_runs/<run-id>.json
```

Annotation exports, adjudications, human evaluation outputs, and per-example
failures belong in the Git-ignored local export directories above. Tracked
failure summaries contain IDs and categorical outcomes only, never customer
text, replies, prompts, rationale, or annotator real-world identities.

## Result classes and limitations

- **Human ground truth:** only independently submitted and adjudicated labels;
  no such v2 labels or agreement metrics are currently available.
- **Live LLM result:** requires explicit `--live` and a bounded `--limit`;
  model/provider/timeout/retry settings come from the existing agent config.
  `LIVE_PROVIDER_EVAL = NOT RUN` when credentials are absent.
- **Deterministic mock result:** reproducible test/evaluation fixture output;
  it is not a model-quality estimate or human label.
- **Heuristic proxy:** taxonomy-based same-intent retrieval and local
  grounding/conflict checks; never call these human relevance or factuality.

The frozen 220-row CSV retains unresolved/provisional label provenance even
after a separate annotation pass. Only new, traceable evidence can change that
provenance conclusion; the original file must remain byte-for-byte unchanged.

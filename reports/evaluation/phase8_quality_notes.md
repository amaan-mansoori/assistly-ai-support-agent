# Phase 7.1 Privacy and Phase 8 Quality Notes

## Scope and classification

This was an offline-only change. No provider or Gemini requests were made.
The frozen evaluation CSV and its manifest were not changed.

| Item | Classification |
|---|---|
| Existing 220-row golden set | Provisional reference labels; source provenance unresolved |
| Deterministic baseline and runtime metrics | Offline/provisional, not human-grounded |
| Independent retrieval relevance metrics | NOT MEASURED; no completed relevance/adjudication export is present |
| Phase 6 annotation sample | 50 stable IDs; template-only, not completed annotations |
| Live Gemini evaluation | NOT RUN in this milestone |
| Existing separate human audit artifacts | Historical artifacts; not treated as new annotation submissions |

## Privacy remediation

Before migration, all 220 records in
`golden_reply_generations.jsonl` duplicated the source customer message in
`customer_text`; customer identifiers and other nonessential fields were also
present. A temporary, non-repository migration was validated first: it retained
all 220 unique example IDs and replies, removed customer text/identifier fields,
and produced zero exact matches against the frozen source messages. The tracked
artifact was then migrated atomically to `assistly-reply-generation-v2`.

The v2 artifact keeps the generated reply, provisional intent, historical
support responses, and retrieval scores/metadata for legitimate offline
evaluation. It omits customer messages, conversation context, customer IDs, and
free-form generation reasons. Exact current-message echoes and common email,
phone, API-key, and bearer-token patterns are redacted from retained text.
Generation failures persist categorized metadata only; provider exception
messages are not written.

The judge now hydrates the customer message from the hash-verified frozen CSV
in memory, keyed by example ID. The hydrated message is not added to judge
output. The human-audit sample builder continues to use the frozen source as
the review interface input and consumes only the retained response/evidence
fields from the generation artifact.

Remaining privacy risk: the frozen golden CSV and the separate tracked
`data/golden/human_audit_50.csv` / `human_audit_8_analysis.xlsx` artifacts retain
content needed for the original evaluation and human review. They remain
access-controlled dataset artifacts; this change does not claim the repository
is free of customer text. The redaction patterns are defense-in-depth, not a
general-purpose PII detector.

## Quality and integrity changes

1. Offline reply grounding now uses historical support responses only.
   Retrieved historical customer messages no longer count as support for a
   generated answer. The diagnostic is explicitly versioned
   `offline-grounding-v2`; it remains lexical support, not factuality proof.
2. Evidence conflict detection now associates a recognized outcome polarity
   with its nearby outcome topic. Unrelated positive/negative outcomes in
   different topics do not by themselves create a conflict. Ambiguous polarity
   within a topic is not treated as a confident conflict.
3. The evidence policy is versioned as `assistly-evidence-policy-v2`, and the
   integrated evaluator is `integrated-evaluator-v4`. The regression gate now
   requires the dataset-manifest digest and evidence-policy version, preventing
   silent comparisons across changed evidence semantics.
4. Baseline, integrated, judge, retrieval, and human-grounded reports record
   dataset/manifest identity where their execution paths can establish it.
5. Template creation and annotation merging refuse to replace existing output
   files unless `--overwrite` is explicitly supplied.

No classifier, retrieval-ranking, or decision threshold was tuned on the frozen
evaluation set. Independent relevance labels are unavailable, so a retrieval
ranking change could not be justified without leaking or inventing judgments.
Annotation validation checks evidence-ID shape, uniqueness, and consistency
between graded evidence entries and the positive-relevance ID list. It cannot
prove that a newly supplied evidence ID belongs to the full historical corpus
without a complete, versioned corpus-ID catalog.

## Before/after offline diagnostics

These values are a definition-change comparison, not an improvement claim. The
before values are from the checked-in `offline-v1` report, whose grounding
could count historical customer messages. The after values were recomputed
in memory from the sanitized 220-record artifact using `offline-v2`.

| Diagnostic | Before (`offline-v1`) | After (`offline-v2`) |
|---|---:|---:|
| Examples | 220 | 220 |
| Mean lexical grounding score | 0.750827 | 0.724827 |
| Mean evidence-token support rate | 0.515290 | 0.470108 |
| Lexical unsupported-claim rate | 0.013636 | 0.020455 |
| Mean reference-token overlap | 0.211927 | 0.211944 |

The changed grounding values are expected because the evidence definition is
stricter and no longer treats a historical customer's request as a support
resolution. They do not indicate a change to the generated replies. None of
these diagnostics is human-validated. The deterministic lexical judge is a
mock/proxy and is not live Gemini or human evidence.
In particular, the unsupported-claim rate is shown only as a lexical diagnostic;
it is explicitly excluded from conclusions about factuality or quality
improvement without adjudicated human checks.

Historical classifier baselines remain 220-example provisional measurements:
majority accuracy 24.09%; TF-IDF plus Logistic Regression accuracy 49.55% and
macro-F1 53.53%. The existing retrieval values 31.82% / 48.64% / 56.82% are
intent-match proxies, not independent Recall@1/@3/@5. Independent retrieval
Recall@K, MRR, and nDCG remain NOT MEASURED.

An additional bounded offline runtime check used the configured deterministic
mock on the first 10 frozen examples. Run ID
`20261009T074512Z-5ae1cc55` (`2026-10-09T07:45:12.557947+00:00`) recorded
accuracy 0.70, macro-F1 0.205882, same-intent Recall@1/@3/@5 proxies
0.60/0.60/0.70, and same-intent MRR proxy 0.625. The run used evaluator
`integrated-evaluator-v4`, evidence policy `assistly-evidence-policy-v2`, the
frozen dataset hash above, and the pinned manifest hash above. These provisional
labels and intent-match proxies are not human-grounded retrieval results. The
mock grounding result (0/5 drafts supported) and unsupported-claim diagnostic
(0/5) apply only to the fixed review-only mock response; they are not model
quality claims. Human escalation metrics remained NOT MEASURED.

## Verification and limitations

The pinned frozen dataset SHA-256 is
`2a80bd3cafee26ef8a4cc665b9212a33eae4d08e12a808f9e0cfdce00b523b81`;
the manifest SHA-256 is
`3b0f6fa241cb686832536471d0982ae8434870b83ffa45e6cb23a07d20c4ed77`.
Both are checked independently during evaluation.

No live provider result, latency, token usage, cost, human-grounded quality,
adjudicated escalation precision/recall, or independent retrieval score was
collected in this milestone. Passing offline tests alone does not establish
production readiness. Further measurable retrieval and intent improvements
require genuine, independently adjudicated labels; provider reliability
requires a separately authorized bounded live run.

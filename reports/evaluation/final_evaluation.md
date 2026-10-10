# Final Evaluation Report

This report consolidates historical generated-reply evaluation artifacts; it
does not certify the populated golden-set labels as human ground truth or
represent a current live-provider run. The frozen dataset's label provenance
remains unresolved; see
[`golden_set_provenance.md`](../golden_set_provenance.md). Values below are
historical artifact results unless explicitly described as revalidated.

## A. Headline results

These are separate component evaluations, not one combined end-to-end score.

| Component | Metric | Result |
|---|---|---:|
| Intent classification | Trivial majority accuracy | **24.09%** |
| Intent classification | TF-IDF + LogisticRegression accuracy | **49.55%** |
| Intent classification | TF-IDF + LogisticRegression macro F1 | **53.53%** |
| Retrieval | intent-match@1 | **31.82%** |
| Retrieval | intent-match@3 | **48.64%** |
| Retrieval | intent-match@5 | **56.82%** |
| Reply quality | Stored Gemini-labeled judge artifact, overall | **4.9227/5** |
| Reply quality | Stored Gemini-labeled judge artifact, relevance | **4.9773/5** |
| Reply quality | Stored Gemini-labeled judge artifact, helpfulness | **4.8864/5** |
| Reply quality | Stored Gemini-labeled judge artifact, factuality | **4.9909/5** |
| Reply quality | Stored Gemini-labeled judge artifact, grounding | **4.9318/5** |
| Reply quality | Stored Gemini-labeled judge artifact, safety | **5.0000/5** |
| Offline diagnostic | Mean lexical grounding | **0.750827** |
| Offline diagnostic | Unsupported claim rate | **1.36%** |
| Offline diagnostic | Deterministic lexical judge | **4.2345/5** |

The stored judge scores are **gold-intent-conditioned reply-quality scores**,
not an end-to-end classification-to-reply result. Their per-example JSONL is
present, but its contents alone do not independently establish provider/model
provenance or the conditions of the historical run. The scores are not
reproduced as part of this final verification. Retrieval intent-match is not
response quality, and offline lexical diagnostics are not semantic truth.

## B. 220-example automated evaluation

### Reply-quality evaluation scope

The 220-example reply-generation experiment supplies each example's populated
`human_intent` field to the reply generator to isolate reply-generation quality
from classifier errors. The repository does not establish that these values
were human-reviewed; their provenance is unresolved. Therefore, the
**4.9227/5 stored judge-artifact result is reference-intent-conditioned**: it
evaluates replies generated after providing the stored reference intent, not
verified human ground truth.

It is **not** an end-to-end classification → retrieval → reply score. The simple
TF-IDF + LogisticRegression baseline evaluates intent classification separately;
retrieval is evaluated separately with intent-match@1/@3/@5; escalation is
evaluated separately by its deterministic policy and the human-audit layer.
Together, these component results are informative, but the reply score must not
be interpreted as complete-agent accuracy.

## Reply quality and grounding

- Generated examples: **220**
- Non-empty reply rate: **1.000000**
- Mean reply length (words): **39.12**
- Mean evidence grounding score: **0.750827**
- Unsupported specific-claim rate: **0.013636**

## Deterministic structured judge

These scores are an offline lexical smoke-test, not an LLM call.

- Overall mean: **4.234545** / 5
- Mean relevance: **4.05** / 5
- Mean helpfulness: **4.05** / 5
- Mean factuality: **4.05** / 5
- Mean grounding: **4.05** / 5
- Mean safety: **4.972727** / 5

## C. 50-example independent human audit

The human audit contains 50 examples and 8 independent annotators. Adnan, Jatin, Khushi, Rashi, and Yash form the calibrated reference panel used for the panel-level comparison; they are not treated as unquestionable ground truth. Kuhu, Sabir, and Shivani remain in the raw audit data and are flagged for near-constant response-pattern concerns documented in the analysis artifact.

### Completion and source reconciliation

**Human reply-quality audit: complete.** The supplied reviewer exports were
checked against the 50-row audit sample and the consolidated
[`HumanMaster` analysis workbook](../../human_audit_8_analysis.xlsx). Each of
the eight exports contains the same 50 unique example IDs and all four reply
audit dimensions: `reply_addresses_problem`, `evidence_supported`,
`unsupported_claim`, and `human_escalation`. That is 200 judgments per reviewer,
400 judgments per dimension, and 1,600 judgments in total. There were no
duplicate or missing IDs, missing dimension values, or invalid category values.
Every source label matched its corresponding reviewer/dimension cell in
`HumanMaster`.

The exports were found in the repository working tree under these names and
were not copied into this report:

| Reviewer | Local source export | Detected format | Reconciled coverage |
|---|---|---|---:|
| Adnan | [adnan_human_audit_50_answers](../../adnan_human_audit_50_answers) | CSV | 50/50 rows, all four dimensions |
| Jatin | [jatin_human_audit_50_answers-5.pdf](../../jatin_human_audit_50_answers-5.pdf) | PDF | 50/50 rows, all four dimensions |
| Khushi | [khushi_human_audit_50_answers.xlsx](../../khushi_human_audit_50_answers.xlsx) | XLSX | 50/50 rows, all four dimensions |
| Kuhu | [kuhu_human_audit_50_answers (1)](<../../kuhu_human_audit_50_answers (1)>) | CSV | 50/50 rows, all four dimensions |
| Rashi | [rashi_human_audit_50_answers (1)](<../../rashi_human_audit_50_answers (1)>) | CSV | 50/50 rows, all four dimensions |
| Sabir | [sabir_human_audit_50_answers (1).xlsx](<../../sabir_human_audit_50_answers (1).xlsx>) | XLSX | 50/50 rows, all four dimensions |
| Shivani | [shivani_human_audit_50_answers.csv](../../shivani_human_audit_50_answers.csv) | PDF (file contents, despite the `.csv` suffix) | 50/50 rows, all four dimensions |
| Yash | [yash_human_audit_50_answers](../../yash_human_audit_50_answers) | CSV | 50/50 rows, all four dimensions |

The IDs also match the existing
[`human_audit_50.csv` sample](../../data/golden/human_audit_50.csv). The two PDF
exports were decoded locally for IDs and categorical labels and reconciled
row-by-row; no reviewer comments or customer text were copied into this report.
The raw exports and the analysis workbook were left unchanged.

The saved summary was recalculated from the eight reviewer columns. The
8-annotator and calibrated 5-person top-label agreement values below reproduce
the workbook summary exactly. These are agreement statistics, not model
accuracy or proof of objective correctness.

### Methodology and limitations

- The audit contains 50 examples only.
- Eight independent annotators participated; the 5-person panel is a pragmatic calibrated reference panel, not unquestioned ground truth.
- Meaningful human disagreement remains, especially on evidence sufficiency and escalation.
- Kuhu, Sabir, and Shivani are preserved in the raw audit data and flagged for near-constant response patterns rather than silently removed.
- The previous ChatGPT/Gemini judge comparisons are coverage-limited and not a full 50-case human-vs-model comparison; the source artifact does not provide enough proven shared Q1 case coverage for those exact percentages.
- The human audit is an independent validation layer and not a replacement for the 220-example automated evaluation.

### Human-human agreement

| Dimension | 8-human mean top-label agreement | 5-human panel mean top-label agreement |
|---|---:|---:|
| Reply addresses problem | 64.0% | 78.8% |
| Evidence supported | 55.0% | 61.6% |
| Unsupported claim | 65.8% | 84.0% |
| Human escalation | 61.8% | 67.6% |

### AI-judge vs 5-human calibrated panel

Exact agreement means the same answer label on the same case and dimension. It does not prove objective correctness or replace the human judgement.

| Dimension | Copilot vs 5-human panel exact agreement |
|---|---:|
| Reply addresses problem | 72.0% |
| Evidence supported | 52.0% |
| Unsupported claim | 94.0% |
| Human escalation | 68.0% |

### AI judge coverage note

The judge comparison covers Q1 only and is coverage-limited; it is not a
full-coverage, four-dimension human-vs-model comparison. Per-case judge labels
were aligned by example ID to the 5-person panel labels in the analysis
workbook. The resulting Q1 agreement reproduces the saved `Judge_Q1` summary:

| Judge | Available cases | Status |
|---|---:|---|
| Copilot | 50/50 | 32/50 exact agreement (64.0%) |
| ChatGPT | 12/50 | 9/12 exact agreement (75.0%); partial coverage |
| Gemini | 3/50 | 2/3 exact agreement (66.7%); very small coverage |

A few concrete examples from the completed audit are noted in the analysis artifact, but they are treated as audit findings, not as objective truth or as a basis for retroactively changing the model or labels.

### Next unfinished evaluation milestone

This completed audit evaluates reply quality and human escalation; it does **not**
supply independent query-to-evidence relevance judgments. The next evaluation
milestone is to collect and adjudicate the separate graded relevance judgments
for the 50-query retrieval benchmark using the blank reviewer templates in
`reports/evaluation/human_annotation_exports/`. Until valid independent
adjudications are provided, independent retrieval Recall@K, MRR, and nDCG remain
pending and must not be inferred from this reply audit or from intent-match
proxy scores.

## D. Top 5 failure modes

These are representative observed failure cases from the completed human audit and evaluation artifacts, not a claim that they cover every failure pattern.

### 1) Unsupported carrier/routing explanation
- What happens: the reply gives a specific carrier or routing explanation that is not supported by the retrieved evidence.
- Why it matters: it creates a misleadingly confident causal story even when the evidence is weak or absent.
- Real example: `golden-set-0013` in the recorded audit materials; the issue is similar to the unsupported carrier/routing explanation pattern described in the audit notes.
- Hypothesis: the model overfits to a common delivery-delay template and spills into a precise logistics narrative lacking evidence.
- Mitigation: require evidence-backed claim verification before mentioning carrier actions, routing, or status changes; escalate when the evidence is thin.

### 2) Refund/replacement request is not handled as the actual user asks
- What happens: the draft acknowledges a delay or generic help request, but does not address the customer’s specific ask to replace or refund an item after the issue has already been discussed.
- Why it matters: the customer’s actual resolution request remains unresolved even when the reply sounds polite and helpful.
- Real example: `golden-set-0054`.
- Hypothesis: the retrieval context and the model focus on the most common return/refund wording but miss the explicit replacement-versus-refund resolution step already discussed in context.
- Mitigation: add explicit state-tracking checks for open resolution requests and require the draft to answer the current action request, not only generic support language.

### 3) Unsupported leadership-team escalation
- What happens: the model invents or implies an escalation path to internal leadership or a formal escalation process not supported by the retrieved evidence.
- Why it matters: unsupported escalation claims are materially risky and can mislead customers about process or authority.
- Real example: `golden-set-0175`.
- Hypothesis: the model borrows high-authority wording from historical examples and overgeneralizes it to a case that lacks evidence for that escalation path.
- Mitigation: limit escalation language to evidence-supported paths and require a human-review gate for internal escalation claims.

### 4) Stronger-than-evidence acknowledgment claim
- What happens: the reply states or implies a formal receipt or that the support team has already received the customer’s email or action, even when the evidence does not show that.
- Why it matters: it claims an operational fact that was never demonstrated.
- Real example: `golden-set-0213`.
- Hypothesis: the model uses a generic “we’ve received your message” template without checking whether the evidence supports the claim.
- Mitigation: ban unsupported acknowledgment language in the prompt and add a specific check for “received / processed / escalated” claims.

### 5) Unsupported timeline commitment
- What happens: the reply gives a concrete turnaround or 48-hour timeline without evidence to support it.
- Why it matters: timing promises are high-risk, especially in delivery, refund, and logistics cases; they can be wrong in a way customers will notice quickly.
- Real example: `golden-set-0182`.
- Hypothesis: the system is using generic response patterns that include time estimates, but the historical evidence is insufficient to justify the exact duration.
- Mitigation: remove exact-time promises unless they are directly grounded in evidence; use cautious language and escalate when timing is uncertain.

## What is misleading about my headline number?

The headline number is not a claim that the system is “correct” in every case.

- The 4.9227/5 value is the average recorded in a stored judge artifact labelled Gemini over 220 examples; it is not independently verified as a live Gemini run or as human ground truth.
- It records judged reply quality under the artifact's rubric, not proof that each factual claim is objectively correct.
- High average scores can hide a small number of specific grounding failures, unsupported policies, or weakly supported escalations.
- Retrieval intent-match@1 of 31.82% is not the same as response quality. A model can retrieve a plausible example without producing a fully correct or sufficiently grounded reply.
- The offline lexical diagnostics are diagnostics, not semantic truth. They are useful for smoke-testing and qualitative checks, but they do not prove correctness.
- The 50-example human audit shows meaningful human disagreement, especially on evidence sufficiency and escalation; the 5-person panel is a calibrated reference panel, not unquestionable ground truth.
- The automated 220-case evaluation and the 50-case human audit measure different things: one is a large benchmark of judged replies, the other is a focused human disagreement/audit layer.

The honest interpretation is: the historical artifact records a high average
judge score, but its provider provenance and reference-label validity are
unresolved. It is not a verified current performance result or proof that
every case is correct.

## Next-week improvement plan

1. Improve retrieval with hybrid semantic + lexical search.
   - Expected benefit: better support for ambiguous, context-heavy, and synonym-heavy customer messages.
2. Strengthen conversation-state handling around follow-up and resolution requests.
   - Expected benefit: the reply will better answer the actual current ask instead of the most generic historical pattern.
3. Add explicit claim-verification checks for carrier, refund, timeline, and escalation statements.
   - Expected benefit: fewer unsupported factual claims and fewer “stronger-than-evidence” statements.
4. Calibrate escalation policy using the human disagreement signal rather than a single static rule set.
   - Expected benefit: more consistent escalation decisions where evidence is weak or the risk is high.
5. Expand and refine the intent taxonomy using residual confusion cases.
   - Expected benefit: reduce boundary errors between similar intents and improve retrieval precision.
6. Add targeted regression cases from the observed failure modes as fixed evaluation examples.
   - Expected benefit: prevent recurring mistakes from reappearing without requiring full-model retraining.
7. Evaluate cost/latency and model tradeoffs for the live judge and generation path.
   - Expected benefit: keep the system simple and explainable while preserving the quality floor.

## Decision log

1. Select AmazonHelp as the target brand because it has clear direct customer→brand linkage and a large volume of valid paired support interactions, rather than because it was the easiest or most popular label.
2. Treat only Twitter parent-child `in_response_to_tweet_id` relationships as valid conversation provenance, not temporal proximity or author adjacency.
3. Keep the recovered preceding conversation context separate from the final intent label and do not treat it as hidden truth.
4. Use 11 final intents as the production taxonomy after discovery and review, rather than an unbounded or purely model-driven label set.
5. Require explicit evidence for delivered-missing and similar high-risk cases before allowing a confident reply.
6. Separate return/refund issues from replacement and logistics cases so the support logic does not collapse distinct customer asks.
7. Exclude golden IDs from the retrieval corpus to prevent evaluation leakage into the historical evidence set.
8. Exclude exact normalized-text duplicates from the retrieval corpus to avoid duplicate-evidence contamination.
9. Use TF-IDF + LogisticRegression as the simple baseline because it is transparent, fast, and sufficient as a baseline in an environment where heavy transformer models were not yet the primary path.
10. Keep the deterministic lexical judge strictly as an offline diagnostic rather than as a semantic truth source.
11. A historical judge artifact is labelled as Gemini 3.1 Flash Lite over the 220-example benchmark; provider/model provenance and run conditions are not independently verified from the stored output.
12. Keep the 50-case human audit distinct from the 220-case automated evaluation so the two are not conflated.
13. Preserve all 8 annotators and their raw labels, while using the 5-person calibrated panel as a pragmatic reference panel rather than unquestioned ground truth.
14. Make the escalation policy conservative for security, payment, and unclear cases to reduce unsafe auto-handling.

## H. Evaluation framing and limits

- The 220-example automated evaluation remains the primary automated result.
- The 50-example human audit is a separate validation layer for review, disagreement analysis, and calibration notes.
- Human disagreement is meaningful, especially for evidence sufficiency and escalation decisions.
- The human audit does not replace the 220-example automated evaluation or justify post-hoc model optimization.

## Limitations

- Lexical evidence support is a diagnostic, not proof of factual correctness.
- Reference token overlap is not a semantic quality score and is omitted when no reference is available.
- The bundled judge is deterministic and must not be described as a live LLM judgement.
- Human agreement is reported only when a second annotation export is supplied.
- The 50-example human audit is an independent validation layer, not a replacement for the full 220-example automated evaluation.
- The 5-person panel is a pragmatic calibrated reference panel, not absolute ground truth.
- The stored Gemini-labelled 220-case judge artifact is separate from the deterministic lexical judge; its historical provider provenance is unverified.
- ChatGPT/Gemini judge comparisons have partial structured coverage and are therefore reported only as coverage-limited, not as a full 50-case human-vs-model exact-agreement leaderboard.

## Final verification status

- Frozen golden dataset: 220 rows; SHA-256
  `2a80bd3cafee26ef8a4cc665b9212a33eae4d08e12a808f9e0cfdce00b523b81`
  matches the pinned manifest. Label provenance remains unresolved.
- Independent retrieval relevance: 50 queries / 250 ranked candidates are
  prepared; reviewer files remain blank. Recall@1/3/5, MRR, and nDCG@1/3/5
  are **NOT MEASURED**. This is separate from the completed reply-quality audit.
- Live AI evaluation: **NOT RUN**. A provider key is configured locally, but
  validity and authorization for a potentially paid call were not established.
- Remote GitHub Actions: **UNVERIFIED**; no workflow-run evidence was available.
- Optional FastEmbed/PostgreSQL runtime: **NOT VERIFIED**. TF-IDF is the
  configured default; vector/hybrid initialization has no automatic lexical
  fallback.

# Final Evaluation Report

This report consolidates the generated-reply evaluation artifacts. The default run is deterministic and makes no API calls.

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
| Reply quality | Gemini LLM judge overall | **4.9227/5** |
| Reply quality | Gemini relevance | **4.9773/5** |
| Reply quality | Gemini helpfulness | **4.8864/5** |
| Reply quality | Gemini factuality | **4.9909/5** |
| Reply quality | Gemini grounding | **4.9318/5** |
| Reply quality | Gemini safety | **5.0000/5** |
| Offline diagnostic | Mean lexical grounding | **0.750827** |
| Offline diagnostic | Unsupported claim rate | **1.36%** |
| Offline diagnostic | Deterministic lexical judge | **4.2345/5** |

The Gemini score is a **gold-intent-conditioned reply-quality score**, not an
end-to-end classification-to-reply score. Retrieval intent-match is not response
quality, and the offline lexical diagnostics are not semantic truth.

## B. 220-example automated evaluation

### Reply-quality evaluation scope

The 220-example reply-generation experiment supplies each example's
human-reviewed `human_intent` to the reply generator to isolate reply-generation
quality from classifier errors. This is an explicit component-isolation choice.
Therefore, the **4.9227/5 Gemini result is gold-intent-conditioned**: it evaluates
the quality of replies generated after providing the reviewed intent.

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

The previous three-AI comparison is coverage-limited and not a full 50-case human-vs-model comparison. The source artifact does not provide proven exact-case structured agreement percentages for ChatGPT and Gemini, so those numerical values are intentionally omitted.

| Judge | Available cases | Status |
|---|---:|---|
| Copilot | 50 | Exact agreement with the 5-human panel is reported for the available 50-case coverage. |
| ChatGPT | not proven from the source artifact | Exact structured agreement is intentionally omitted because the per-case structured coverage is incomplete. |
| Gemini | not proven from the source artifact | Exact structured agreement is intentionally omitted because the per-case structured coverage is incomplete. |

A few concrete examples from the completed audit are noted in the analysis artifact, but they are treated as audit findings, not as objective truth or as a basis for retroactively changing the model or labels.

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

- The 4.9227/5 Gemini judge score is an LLM-judge average over the 220-example golden set; it is a judge score, not human ground truth.
- It measures judged reply quality under the current rubric, not proof that each factual claim is objectively correct.
- High average scores can hide a small number of specific grounding failures, unsupported policies, or weakly supported escalations.
- Retrieval intent-match@1 of 31.82% is not the same as response quality. A model can retrieve a plausible example without producing a fully correct or sufficiently grounded reply.
- The offline lexical diagnostics are diagnostics, not semantic truth. They are useful for smoke-testing and qualitative checks, but they do not prove correctness.
- The 50-example human audit shows meaningful human disagreement, especially on evidence sufficiency and escalation; the 5-person panel is a calibrated reference panel, not unquestionable ground truth.
- The automated 220-case evaluation and the 50-case human audit measure different things: one is a large benchmark of judged replies, the other is a focused human disagreement/audit layer.

The honest interpretation is: the headline number is evidence that the system often produces strong average judged replies, but it should not be treated as proof that every case is correct.

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
11. Use the live Gemini 3.1 Flash Lite judge as a separate real-judge artifact over the 220-example benchmark, not as a replacement for the offline diagnostics.
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
- The real 220-case Gemini judge is a separate artifact from the deterministic lexical judge and is not represented as the same metric stream.
- ChatGPT/Gemini judge comparisons have partial structured coverage and are therefore reported only as coverage-limited, not as a full 50-case human-vs-model exact-agreement leaderboard.

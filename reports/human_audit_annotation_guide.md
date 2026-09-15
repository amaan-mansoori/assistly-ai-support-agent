# Independent Human Reply Audit

This package contains 50 examples selected reproducibly from the 220-example
evaluation set. The sample uses seed **42** and includes every final intent.
The intent labels are intentionally hidden from the evaluator.

For each example, you can see:

1. What the customer asked or reported.
2. Relevant historical support responses.
3. The AI-generated reply.

Please answer these questions in
`data/golden/human_audit_50_template.csv`.

## Questions

### Q1 — Does the AI reply address the customer's problem?

Use exactly one:

- `yes`
- `partially`
- `no`

### Q2 — Are the important factual claims in the AI reply supported by the historical responses shown?

Use exactly one:

- `yes`
- `partially`
- `no`
- `no_factual_claim`

### Q3 — Does the AI reply contain information that appears invented, unsupported, or overly certain?

Use exactly one:

- `yes`
- `no`

### Q4 — Should this case be handled by a human support agent instead of being automatically handled?

Use exactly one:

- `yes`
- `no`

### Q5 — Optional comment

Add a short reason or comment if useful. Keep it brief.

## Please remember

- Do not try to guess what the AI or model was intended to say.
- Judge only the information shown in the sample.
- Do not use outside Amazon knowledge to fill missing evidence.
- Do not look at existing labels or model scores. They are not included in this package.
- If uncertain, use `partially` where available and explain briefly.
- You do not need any coding or machine-learning knowledge.

The audit CSV is read-only context. Enter answers only in the blank template.
Keep `example_id` unchanged so responses can later be joined to the
evaluation data.

## Files

- `human_audit_50.csv`: label-blind examples and evidence.
- `human_audit_50_template.csv`: blank response form.
- `reports/human_audit_sampling.json`: selected IDs, seed, and sample counts.

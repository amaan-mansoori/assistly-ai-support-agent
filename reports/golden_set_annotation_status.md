# Golden Set Annotation Status

## Historical selection and current label provenance

- **220 selected** from `data/golden/golden_candidates.csv`.
- Deterministic method: existing SHA-256 ordering with seed **42**, selecting the requested quota independently within each `candidate_stratum`.
- `candidate_stratum` is **NOT ground truth**. It is only a sampling stratum.
- This status file describes the original empty worksheet state, but the checked-in `golden_set.csv` now contains populated labels. Other repository evidence describes labels as AI-proposed. These artifacts conflict; the current label provenance is **unresolved** and no human ground truth is asserted.

## Original candidate-stratum sampling quotas (not verified intent labels)

- `delivery_status_delay`: target **25**, actual **25**
- `delivery_marked_delivered_missing`: target **25**, actual **25**
- `return_refund`: target **25**, actual **25**
- `item_condition_or_fulfilment`: target **25**, actual **25**
- `order_cancellation_or_change`: target **15**, actual **15**
- `prime_membership`: target **20**, actual **20**
- `account_access_security`: target **15**, actual **15**
- `payment_charge_issue`: target **15**, actual **15**
- `product_availability_pricing`: target **15**, actual **15**
- `marketplace_seller`: target **10**, actual **10**
- `other_unclear`: target **30**, actual **30**

## Context and language screening

- Rows with recoverable preceding context: **94/220** (as recorded in the candidate pool).
- Deterministic non-English/questionable rows flagged: **1**.

Flagged worksheet rows (not removed or relabelled):
- `golden-set-0121`: CJK characters
Do not infer that the current CSV is blank, human-labelled, or annotation-ready from this historical status record. Current evaluation must use the frozen file fingerprint and treat its populated labels as provisional until a traceable review record resolves provenance.

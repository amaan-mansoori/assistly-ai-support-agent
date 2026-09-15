# Golden Set Annotation Status

## Selection

- **220 selected** from `data/golden/golden_candidates.csv`.
- Deterministic method: existing SHA-256 ordering with seed **42**, selecting the requested quota independently within each `candidate_stratum`.
- `candidate_stratum` is **NOT ground truth**. It is only a sampling stratum.
- Every `human_intent` and `annotation_notes` cell is blank. Final labels must be assigned by a human annotator; no labels were generated automatically.

## Target and actual counts

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
The worksheet is blank and annotation-ready; do not treat candidate strata as human decisions.

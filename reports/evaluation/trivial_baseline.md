# Trivial Majority-Class Baseline

This baseline predicts the single most frequent `human_intent` for every example.
It uses no customer text, context, candidate stratum, or other feature.

- Evaluation examples: **220**
- Majority class: **`delivery_status_delay`**
- Majority-class count: **53**
- Accuracy: **0.240909**
- Macro F1: **0.035298**
- Weighted F1: **0.093540**

## Per-intent metrics

| Intent | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `delivery_status_delay` | 0.240909 | 1.000000 | 0.388278 | 53 |
| `delivery_marked_delivered_missing` | 0.000000 | 0.000000 | 0.000000 | 19 |
| `return_refund` | 0.000000 | 0.000000 | 0.000000 | 23 |
| `item_condition_or_fulfilment` | 0.000000 | 0.000000 | 0.000000 | 21 |
| `order_cancellation_or_change` | 0.000000 | 0.000000 | 0.000000 | 15 |
| `prime_membership` | 0.000000 | 0.000000 | 0.000000 | 15 |
| `account_access_security` | 0.000000 | 0.000000 | 0.000000 | 15 |
| `payment_charge_issue` | 0.000000 | 0.000000 | 0.000000 | 13 |
| `product_availability_pricing` | 0.000000 | 0.000000 | 0.000000 | 5 |
| `marketplace_seller` | 0.000000 | 0.000000 | 0.000000 | 12 |
| `other_unclear` | 0.000000 | 0.000000 | 0.000000 | 29 |

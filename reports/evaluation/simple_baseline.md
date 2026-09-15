# Simple TF-IDF + Logistic Regression Baseline

The finalized golden set was held out entirely from training and used only for final evaluation.
Training data came from `data\interim\amazonhelp_conversations.csv`. The interim file has no human label column, so labels were
derived only for training by the existing deterministic local taxonomy heuristic; these are not golden labels.

- Training examples: **117722**
- Evaluation examples: **220**
- Training classes: **11**
- Accuracy: **0.495455**
- Macro F1: **0.535262**
- Weighted F1: **0.512247**

## Preprocessing and filtering

Customer text was lightly cleaned (mentions/URLs removed, whitespace normalized), then represented
with word-level unigram/bigram TF-IDF. A LogisticRegression classifier used `random_state=42`.
Rows were filtered for English/usable text, duplicate text, golden IDs/text, and labels outside the approved taxonomy.

## Per-intent metrics

| Intent | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `delivery_status_delay` | 0.772727 | 0.320755 | 0.453333 | 53 |
| `delivery_marked_delivered_missing` | 1.000000 | 0.210526 | 0.347826 | 19 |
| `return_refund` | 0.703704 | 0.826087 | 0.760000 | 23 |
| `item_condition_or_fulfilment` | 0.500000 | 0.333333 | 0.400000 | 21 |
| `order_cancellation_or_change` | 1.000000 | 0.266667 | 0.421053 | 15 |
| `prime_membership` | 0.444444 | 0.533333 | 0.484848 | 15 |
| `account_access_security` | 1.000000 | 0.866667 | 0.928571 | 15 |
| `payment_charge_issue` | 0.714286 | 0.769231 | 0.740741 | 13 |
| `product_availability_pricing` | 0.222222 | 0.400000 | 0.285714 | 5 |
| `marketplace_seller` | 0.818182 | 0.750000 | 0.782609 | 12 |
| `other_unclear` | 0.190476 | 0.551724 | 0.283186 | 29 |

## Confusion matrix

Rows are true labels and columns are predicted labels, in this order:
`delivery_status_delay`, `delivery_marked_delivered_missing`, `return_refund`, `item_condition_or_fulfilment`, `order_cancellation_or_change`, `prime_membership`, `account_access_security`, `payment_charge_issue`, `product_availability_pricing`, `marketplace_seller`, `other_unclear`

```json
[
  [
    17,
    0,
    2,
    1,
    0,
    4,
    0,
    0,
    4,
    1,
    24
  ],
  [
    3,
    4,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    12
  ],
  [
    0,
    0,
    19,
    1,
    0,
    1,
    0,
    0,
    0,
    0,
    2
  ],
  [
    1,
    0,
    3,
    7,
    0,
    1,
    0,
    0,
    0,
    0,
    9
  ],
  [
    1,
    0,
    0,
    0,
    4,
    0,
    0,
    0,
    1,
    1,
    8
  ],
  [
    0,
    0,
    0,
    0,
    0,
    8,
    0,
    3,
    0,
    0,
    4
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0,
    13,
    0,
    0,
    0,
    2
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    10,
    0,
    0,
    3
  ],
  [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    2,
    0,
    3
  ],
  [
    0,
    0,
    0,
    2,
    0,
    0,
    0,
    0,
    0,
    9,
    1
  ],
  [
    0,
    0,
    3,
    3,
    0,
    4,
    0,
    1,
    2,
    0,
    16
  ]
]
```

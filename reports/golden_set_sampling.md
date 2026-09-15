# Golden-Set Candidate Sampling

This is a reproducible, annotation-ready pool from validated customer→AmazonHelp pairs. Raw records are linked only through `in_response_to_tweet_id`; the raw TWCS CSV is never modified. English eligibility uses a conservative ASCII-letter gate because the interim file has no language column. Customer text is normalized (mentions, URLs, case, whitespace) and exact normalized duplicates are removed.

`candidate_stratum` is produced by the existing local regex taxonomy only as a sampling aid, **not ground truth**. `human_intent` and `annotation_notes` are blank. The final golden set must be hand-labelled by a human.

## Counts
- Eligible English inquiries after deduplication: **149,717**
- Valid linked candidates: **149,717**
- Candidate pool: **500**
- Recoverable preceding context: **220/500**
- Context-dependent/ambiguous candidates: **27/500**
- Seed: **42**

## Actual sampled counts
- `delivery_status_delay`: **54** (2× target quota 50)
- `delivery_marked_delivered_missing`: **50** (2× target quota 50)
- `return_refund`: **51** (2× target quota 50)
- `item_condition_or_fulfilment`: **51** (2× target quota 50)
- `order_cancellation_or_change`: **30** (2× target quota 30)
- `prime_membership`: **40** (2× target quota 40)
- `account_access_security`: **31** (2× target quota 30)
- `payment_charge_issue`: **30** (2× target quota 30)
- `product_availability_pricing`: **30** (2× target quota 30)
- `marketplace_seller`: **20** (2× target quota 20)
- `other_unclear`: **113** (2× target quota 60)

Quota shortages: `{'delivery_status_delay': 0, 'delivery_marked_delivered_missing': 0, 'return_refund': 0, 'item_condition_or_fulfilment': 0, 'order_cancellation_or_change': 0, 'prime_membership': 0, 'account_access_security': 0, 'payment_charge_issue': 0, 'product_availability_pricing': 0, 'marketplace_seller': 0, 'other_unclear': 0}`. No synthetic, duplicated, or automatically hand-labelled examples were added.

## Why 220 annotations
The 220-example target covers every proposed task intent and `other_unclear` while remaining feasible for human annotation. A 500-row pool provides choice, rare-intent oversampling, diversity, and context-dependent cases. It is not a prevalence estimate and may contain selection bias.

## Limitations
The English gate can exclude multilingual variants; regex strata have blind spots; context is limited to four actual parent hops and available rows. Human review is required before any row becomes a golden label.

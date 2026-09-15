# Golden-Set Annotation Guide

This guide is for **human** annotation. Regex and cluster outputs are sampling aids, not ground truth. Read the customer inquiry with available preceding turns and the AmazonHelp response, but label the customer's primary support goal.

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

Record rationale in `annotation_notes`. The final golden set is HAND-LABELLED by a human; local methods may assist sampling only.

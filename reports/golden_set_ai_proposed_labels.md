# AI-Proposed Golden-Set Labels

These labels are **AI-proposed** and have **not** been counted as human
annotation. They are not final labels and the worksheet is not complete until
a human annotator reviews and replaces them.

- Rows: **220**
- Context used: **94** rows with available preceding context
- `other_unclear`: **33** rows

## Label distribution

- `account_access_security`: **15**
- `delivery_marked_delivered_missing`: **27**
- `delivery_status_delay`: **28**
- `item_condition_or_fulfilment`: **23**
- `marketplace_seller`: **10**
- `order_cancellation_or_change`: **13**
- `other_unclear`: **33**
- `payment_charge_issue`: **13**
- `prime_membership`: **20**
- `product_availability_pricing`: **13**
- `return_refund`: **25**

The labeler used the actual `customer_text` and available provenance-safe
parent-ID context. The existing `candidate_stratum` was treated only as a
sampling aid and was not used as the label. Short, social, non-English-looking,
or insufficiently supported inquiries were conservatively assigned
`other_unclear`; this is a local deterministic screening aid, not a human
decision. `example_id`, tweet IDs, text, candidate strata, and annotation notes
were preserved exactly.

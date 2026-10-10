# Historical Response Retrieval Evaluation

The retriever returns historical customer messages and their directly linked
AmazonHelp responses, using exact `brand_tweet_id` pair provenance. Historical
pairs provide useful grounded examples; TF-IDF cosine vectors capture shared
semantic vocabulary more robustly than exact keyword matching alone.

The golden set was held out by customer tweet ID and exact normalized customer
text. `intent-match@k` measures whether any top-k historical message has the
same intent as the provisional reference label. This is a **heuristic proxy**,
not independently judged retrieval relevance and not proof of response quality.
Historical intents are heuristic/pseudo-labels; the frozen golden label
provenance remains unresolved and provisional.

- Corpus size: **152535**
- Golden examples: **220**
- Dataset SHA-256: **2a80bd3cafee26ef8a4cc665b9212a33eae4d08e12a808f9e0cfdce00b523b81**
- Dataset provenance: **unresolved_provisional**
- Metric class: **heuristic_proxy**
- Retrieval representation: **sklearn-tfidf-word-unigram-bigram**
- Excluded golden IDs: **220**
- Excluded exact-text duplicates: **2221**
- Mean top-1 similarity: **0.326346**
- Median top-1 similarity: **0.298966**
- Intent-match@1: **0.318182**
- Intent-match@3: **0.486364**
- Intent-match@5: **0.568182**

Privacy-minimized retrieval failure identifiers are in
`retrieval_failure_examples.json`; no query or historical message text is
stored in the failure artifact.

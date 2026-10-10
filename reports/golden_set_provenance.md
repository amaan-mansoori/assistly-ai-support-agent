# Golden-set label provenance

The repository contains a 220-row `data/golden/golden_set.csv` with a
non-empty `human_intent` value in every row. The repository artifacts do not,
however, establish that those values were assigned or reviewed by humans:

- `golden_set_annotation_status.md` says the selected worksheet is blank and
  annotation-ready, with every `human_intent` and `annotation_notes` cell
  blank.
- `golden_set_ai_proposed_labels.md` describes 220 labels as AI-proposed and
  not counted as human annotation.
- The checked-in CSV currently has 220 populated `human_intent` cells and 220
  blank `annotation_notes` cells.
- Some evaluation-report text calls the labels human-reviewed, which conflicts
  with the annotation-status and AI-proposal artifacts.

No provenance record in the repository resolves this contradiction. Therefore
the checked-in labels must be treated as **provenance unresolved**, not
asserted to be human-labelled or human-reviewed. Existing benchmark outputs
are preserved as historical artifacts, but claims that depend on treating
these labels as verified human ground truth should be regarded as unverified.

This note documents the discrepancy; it does not modify the dataset, labels,
or historical evaluation reports. Resolve provenance through a traceable
review/annotation record before using the set as a human-labelled benchmark.

## Dataset identity and reproducible selection

The frozen CSV contains 220 rows with these columns: `example_id`,
`customer_tweet_id`, `customer_author_id`, `customer_text`,
`conversation_context`, `amazonhelp_response`, `candidate_stratum`,
`human_intent`, and `annotation_notes`. The manifest identifies the source as
the AmazonHelp subset of the Kaggle Customer Support on Twitter dataset
(thoughtvector); the exact upstream release/version is not recorded. Its
dataset SHA-256 is
`2a80bd3cafee26ef8a4cc665b9212a33eae4d08e12a808f9e0cfdce00b523b81`, and the
manifest SHA-256 is
`3b0f6fa241cb686832536471d0982ae8434870b83ffa45e6cb23a07d20c4ed77`. The
manifest pins both expected values. The repository validator confirms both
hashes, row count, schema, and unique example/tweet IDs.

The checked-in sampling code selects linked AmazonHelp customer/reply
conversations, applies its English eligibility rule, normalizes text for
duplicate filtering, and uses deterministic SHA-256 ordering (seed 42) and
stratum quotas to construct the 220-row worksheet. The stratum taxonomy is a
selection aid, not evidence that the `human_intent` values were independently
labelled. The raw upstream release identifier and an auditable human-labeling
history are unavailable. The 220 rows are used as an evaluation/holdout set;
the repository does not define a conventional train/validation/test split.
The intent baseline trains on the separate 154,976-row interim conversation
artifact and excludes golden tweet IDs and normalized customer-text matches.
Retrieval construction also excludes golden IDs and normalized exact-text
matches. These checks mitigate direct overlap but do not establish complete
upstream deduplication or human label validity.

Consequently, the persisted baseline numbers are historical diagnostics
against the stored reference labels, not verified performance against a
human-labelled test set. Similarly, the older retrieval `intent-match@k`
measure is a taxonomy proxy, not independently judged relevance.

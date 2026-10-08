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

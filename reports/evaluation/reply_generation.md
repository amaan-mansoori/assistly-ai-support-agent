# Grounded Reply Generation

The generator accepts the current customer message, a predicted intent, and
top-k historical customer-to-AmazonHelp examples. Historical responses are
provided as evidence, not instructions, and are omitted from the customer
reply's metadata.

The model is configured with `SUPPORT_AGENT_MODEL`. When `GEMINI_API_KEY` is
present, the current `google-genai` SDK is used with a default
`gemini-2.0-flash` model; otherwise the existing OpenAI-compatible path uses
`OPENAI_API_KEY` and optionally `OPENAI_BASE_URL`. No credentials are
hard-coded. Missing configuration fails clearly. Output is strict JSON and is
validated for reply text, confidence range, boolean review flag, and a concise
reason.

The golden set is used only for this isolated reply-quality experiment; its
human-reviewed intent is supplied to isolate reply quality from classifier
errors. This is not an end-to-end evaluation. Development is limited by
`--limit` (default 5) and retrieval uses `--k` (default 5). Insufficient or
conflicting evidence should result in a cautious clarification or human-review
recommendation. No automatic handling or escalation policy is implemented.

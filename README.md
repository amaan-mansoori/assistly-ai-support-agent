# AI Customer Support Agent — Hiver SDE Internship Take-Home

An AI-powered customer support agent that classifies incoming customer
messages, drafts historically-grounded replies, and decides whether to
auto-handle or escalate to a human.

Built on the [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) dataset.

---

## Quick Start

### 1. Clone & install

```bash
git clone <repo-url>
cd hiver-sde-ai-support-agent
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Set up credentials

```bash
# Create a .env file (never committed to git)
copy .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
| Variable | Purpose |
|---|---|
| `KAGGLE_USERNAME` | Kaggle API — dataset download |
| `KAGGLE_KEY` | Kaggle API — dataset download |
| `GEMINI_API_KEY` | Gemini API — reply generation and live judge |

Optional:
| Variable | Purpose |
|---|---|
| `SUPPORT_AGENT_MODEL` | Select the configured model for generation or judging |

### 3. Download the dataset

```bash
kaggle datasets download -d thoughtvector/customer-support-on-twitter -p data/raw --unzip
```

This creates `data/raw/twcs/twcs.csv` (~493 MB, ~2.8M rows).

> **Note:** `data/raw/sample.csv` (93 rows) is a small sample included
> for quick smoke-testing only. It is **not** the full dataset. All
> analysis and modeling uses `data/raw/twcs/twcs.csv`.

### 4. Inspect the dataset & select a brand

```bash
# Full summary inspection (chunked read, memory-safe):
python -m src.data.inspect_dataset

# Deep dive into a specific candidate brand:
python -m src.data.inspect_dataset --brand AmazonHelp

# Show more brands in the ranking:
python -m src.data.inspect_dataset --top 50
```

The full inspection reads `data/raw/twcs/twcs.csv` in chunks and prints:
schema, null rates, inbound/outbound counts, reply-linkage statistics,
text length distribution, and a ranked list of candidate support accounts.

**AmazonHelp is the selected brand.** Its selection is justified empirically
in `reports/brand_comparison.md` and `reports/amazonhelp_validation.md` using
volume, direct linkage, thread depth, substantive-response rate, and retrieval
feasibility.

---

## Project Structure

```
├── configs/              # YAML configuration files
│   └── default.yaml
├── data/
│   ├── raw/              # Original downloaded data (git-ignored)
│   │   ├── twcs/         #   └── twcs.csv  (~2.8M rows, the real dataset)
│   │   └── sample.csv    #   Small 93-row sample (smoke-testing only)
│   ├── interim/          # Intermediate processing artifacts
│   ├── processed/        # Final cleaned data ready for modeling
│   └── golden/           # Hand-labelled evaluation set (150-250 examples)
├── src/
│   ├── data/             # Data loading, cleaning, thread reconstruction
│   ├── intents/          # Intent discovery and classification
│   ├── retrieval/        # Similar-conversation retrieval (RAG)
│   ├── agent/            # LLM agent: reply generation + escalation
│   └── evaluation/       # Metrics, LLM judge, baseline comparisons
├── experiments/          # Experiment logs and outputs (git-ignored)
├── reports/              # Final report, figures, decision log
├── tests/                # Unit and integration tests
├── requirements.txt
└── README.md
```

---

## Reproducing Headline Results

This repository does not provide a single pipeline entry point. Instead, it
exposes the actual module-level commands used to reproduce or inspect the
evaluation artifacts. Those commands are intentionally separated into:

- A. Offline inspection of checked-in evaluation artifacts
- B. Raw-data preparation and model-output regeneration
- C. Optional live Gemini judge

This is the smallest honest reproduction path and avoids implying that the
entire cold-start workflow is guaranteed to finish in under 15 minutes.

### A. Offline inspection of checked-in evaluation artifacts

After installing dependencies, these commands inspect the checked-in generated
reply and evaluation artifacts without live model calls:

```bash
# Offline reply-quality metrics and deterministic lexical diagnostics
python -m src.evaluation.reply_quality
python -m src.evaluation.llm_judge

# Final consolidated report
python -m src.evaluation.generate_final_report
```

These commands read the checked-in generated-reply checkpoint, golden set, and
evaluation inputs. The checked-in reports allow a reviewer to inspect the
headline results without rerunning live API calls.

### B. Raw-data preparation and model-output regeneration

For a fresh data-to-evaluation run, the dependency chain is:

```text
raw Kaggle data
  -> AmazonHelp validation and preparation
  -> data/interim/amazonhelp_conversations.csv
  -> baselines, retrieval evaluation, and reply generation
```

Run the existing preparation command before downstream commands that depend on
the interim conversation-pair file:

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Download raw Kaggle data
kaggle datasets download -d thoughtvector/customer-support-on-twitter -p data/raw --unzip

# Validate the selected brand and create the interim AmazonHelp pairs
python -m src.data.inspect_dataset --brand AmazonHelp
python -m src.intents.discover_intents

# Component evaluations using the prepared interim file
python -m src.evaluation.run_trivial_baseline
python -m src.evaluation.run_simple_baseline
python -m src.evaluation.evaluate_retrieval
```

Regenerating missing model outputs is not an offline step. It requires a
configured LLM provider; for the frozen Gemini-produced checkpoint use:

```powershell
$env:GEMINI_API_KEY="your-key"
$env:SUPPORT_AGENT_MODEL="gemini-2.0-flash"
python -m src.evaluation.generate_golden_replies --limit 220 --k 5
```

Do not commit the key. The checked-in `golden_reply_generations.jsonl` is the
artifact used for the reported evaluation and does not need regeneration to
inspect the results.

### C. Optional live Gemini judge

The real 220-example Gemini judge is a separate optional step and requires a live
API setup. It is not part of the offline deterministic evaluation path.

Required environment variable:
- `GEMINI_API_KEY` for the live Gemini judge
- `SUPPORT_AGENT_MODEL` can select the configured model if needed

```powershell
$env:SUPPORT_AGENT_MODEL="gemini-3.1-flash-lite"
python -m src.evaluation.llm_judge --live --limit 220 `
  --output reports/evaluation/reply_judge_gemini.jsonl `
  --summary reports/evaluation/reply_judge_gemini_summary.json
```

This step makes 220 live judge calls. It depends on external API access, rate
limits, and the availability of the generated reply checkpoint. The checked-in
Gemini JSONL and summary are already available for inspection, so rerunning this
step is optional.

### Important reproducibility note

- The repository provides reproducible module-level commands for the evaluation
  workflow.
- The raw Kaggle download and live Gemini judge are external, variable-cost steps.
- A fresh reviewer should not assume a guaranteed cold-start runtime under 15
  minutes; the repository is honest about the fact that live API work and dataset
  preparation are environment-dependent.
- The checked-in artifacts allow the 220-example automated evaluation and final
  report to be inspected without re-running the live judge.

### Offline reply evaluation

The generated reply checkpoint can be evaluated without credentials or network
access. The commands below only read the existing JSONL and annotation files;
they do not rewrite raw, golden, interim, or generated data:

```bash
python -m src.evaluation.reply_quality
python -m src.evaluation.llm_judge                  # deterministic smoke-test judge
python -m src.evaluation.human_agreement --secondary path/to/second_annotations.csv
python -m src.evaluation.generate_final_report
# Or compute agreement while building the final report:
python -m src.evaluation.generate_final_report --secondary-annotations path/to/second_annotations.jsonl
```

`reply_quality` reports deterministic reply presence, length, lexical reference
overlap (when the historical response is available), and evidence/grounding
checks. `llm_judge` accepts precomputed structured judgements with
`--judgements` or an injected driver in Python; it never makes a live call by
default. Human agreement aligns rows by `example_id` (or an explicit ID field)
and reports raw agreement and Cohen's kappa. Lexical grounding and reference
overlap are diagnostics, not proof of factual correctness.

---

## Development Milestones

- [x] Project structure & scaffold
- [x] Dataset inspection & brand selection
- [x] Data cleaning & thread reconstruction
- [x] Intent discovery (clustering)
- [x] Golden evaluation set (hand-labelled)
- [x] Retrieval system (similar conversations)
- [x] Agent (classify → retrieve → draft → escalate)
- [x] Baseline implementations (trivial + simple)
- [x] Evaluation harness (metrics + LLM judge)
- [x] Judge vs. human agreement analysis
- [x] Failure analysis (5 real failure modes)
- [x] Final report with "What is misleading about my headline number?"
- [x] Decision log (10-15 non-obvious decisions)

---

## Design Principles

1. **Simple over clever** — readable code a student can explain line-by-line.
2. **Reproducible** — fixed random seeds, pinned dependencies, config files.
3. **No hardcoded secrets** — all API keys via environment variables.
4. **Honest evaluation** — explicit failure analysis and misleading-metric disclosure.

# Assistly

**AI-Powered Customer Support Platform**

AI-powered customer support, grounded in real resolutions.

Assistly is a customer-support platform built from an AI support-agent
internship take-home project. It classifies customer intent, retrieves
historical resolutions, drafts evidence-grounded replies, and routes uncertain
or sensitive cases to a human support team.

Built on the [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) dataset.

---

## Quick Start

### 1. Clone & install

```bash
git clone <repo-url>
cd <repository-directory>
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

Credentials are needed only for the corresponding optional operations:
| Variable | Purpose |
|---|---|
| `KAGGLE_USERNAME` | Kaggle API — raw dataset download |
| `KAGGLE_KEY` | Kaggle API — raw dataset download |
| `GEMINI_API_KEY` | Gemini API — live reply generation and optional live judge |
| `OPENAI_API_KEY` | OpenAI-compatible API — reply generation when selected |

Optional:
| Variable | Purpose |
|---|---|
| `SUPPORT_AGENT_MODEL` | Select the configured model for generation or judging |
| `SUPPORT_AGENT_PROVIDER` | Override the runtime provider (`gemini` or `openai`) |
| `SUPPORT_AGENT_TOP_K` | Override the number of retrieved examples |
| `SUPPORT_AGENT_MIN_RETRIEVAL_SIMILARITY` | Override the lexical evidence floor |
| `SUPPORT_AGENT_MIN_GROUNDING_TOKEN_SUPPORT` | Override the lexical grounding floor |
| `SUPPORT_AGENT_ESCALATION_THRESHOLD` | Override the model-confidence review threshold |

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
│   └── golden/           # Golden evaluation data (label provenance unresolved)
├── src/
│   ├── data/             # Data loading, cleaning, thread reconstruction
│   ├── intents/          # Intent discovery and classification
│   ├── retrieval/        # TF-IDF baseline, pgvector adapter, ingestion
│   ├── agent/            # Reusable agent core and provider adapters
│   ├── api/              # FastAPI routes, auth, middleware, schemas
│   ├── application/      # Conversation, support, ticket, feedback services
│   ├── db/               # SQLAlchemy entities and session construction
│   ├── platform/         # Settings, rate limits, metrics, operations
│   └── evaluation/       # Historical benchmarks and integrated-agent harness
├── frontend/             # Next.js customer support and staff dashboard
├── alembic/              # Versioned database migrations
├── experiments/          # Experiment logs and outputs (git-ignored)
├── reports/              # Final report, figures, decision log
├── tests/                # Unit and integration tests
├── Dockerfile            # Backend image
├── compose.yaml          # Backend, PostgreSQL/pgvector, Redis, frontend
├── requirements.txt
└── README.md
```

## Integrated runtime agent

The repository now has a single synchronous orchestration entrypoint,
`SupportAgent.handle(AgentRequest(...))`. It reuses the deterministic
11-category taxonomy in `src/intents/final_taxonomy_audit.py`, the existing
TF-IDF historical retriever, structured LLM reply generation, the existing
escalation policy, and the offline lexical grounding diagnostic. The core
remains independently callable; the platform wraps it through application
services rather than moving business logic into API routes.

```text
Request validation
  -> intent detection (10 task intents + other_unclear)
  -> TF-IDF retrieval (top-k historical message/response pairs)
  -> evidence sufficiency gate
  -> structured reply generation (Gemini or OpenAI-compatible provider)
  -> independent runtime grounding heuristic
  -> conservative escalation policy
  -> structured AgentResponse
```

`confidence` from the deterministic intent detector is `None`; no probability
is fabricated. Retrieved rows do not have trusted intent labels, so runtime
retrieval is not filtered by intent. The retrieval and grounding floors are
configurable in `configs/default.yaml` or with the environment variables listed
above. These are operational heuristics, not calibrated confidence thresholds.
The grounding gate checks literal claims (including URLs, numbers, timelines,
policy language, and actions) and lexical overlap; it is not an entailment
model or proof of truth. Sensitive intents, unclear requests, insufficient
evidence, unsupported claims, and provider/validation errors fail closed to
human review. Logs include request correlation and operational fields, not
customer message text or credentials.

### Local demo

The demo needs the prepared conversation-pairs file and golden set in the
repository's expected local paths. It builds the TF-IDF index in memory.
`--mock` avoids any model API call but still requires those data files.

```bash
# Prepare local corpus files if they are not already present.
python -m src.intents.discover_intents

# Run with the local mock provider (no API credentials).
python -m src.agent --mock --message "My order is late. Where can I check delivery status?"

# Run with configured live provider credentials.
python -m src.agent --message "My order is late. Where can I check delivery status?" \
  --history "Tracking has not updated since yesterday."
```

Interactive mode is available by omitting `--message`. The result is JSON and
includes intent, evidence summary, grounding diagnostics, draft, decision,
reason, request ID, processing duration, and a sanitized error category when
applicable. Do not treat `--mock` output as a model evaluation.

### Runtime configuration

`src/agent/config.py` loads `configs/default.yaml`, then applies environment
overrides. Secret keys are read from the environment (and `.env` for local
development); never put secrets in YAML or source code. The runtime provider
defaults to Gemini and the model defaults to `gemini-2.0-flash`; use
`SUPPORT_AGENT_PROVIDER=openai` with `OPENAI_API_KEY` and a
`SUPPORT_AGENT_MODEL` accepted by the selected OpenAI-compatible endpoint to
use that adapter. `SUPPORT_AGENT_MODEL` overrides the model. The CLI supports
an alternate YAML file through `--config`.

The TF-IDF retriever and runtime grounding gate are intentionally
lexical/heuristic at this stage. They are not production-grade factual
verification. Provider calls require network access and valid credentials;
normal tests use injected mock providers and do not call external model APIs.

### Provider boundary and failure behavior

The agent depends on a small callable provider protocol rather than a provider
SDK. Adapters use Google's Gen AI Interactions API or OpenAI-compatible chat
completions; `DeterministicMockProvider` supplies stable offline responses for
tests and explicit smoke runs. The provider, model, timeout, and retry count are
configurable. Responses must satisfy the strict JSON contract before they can
continue to grounding and decision policy. SDK/network failures and malformed
or invalid output become safe errors and fail closed to human review. API keys
are read from the environment and are not included in application logs.

### Prompt and context boundaries

The current message, recent conversation turns, and retrieved historical
examples are serialized into separate fields marked as untrusted input. The
system instruction explicitly rejects instructions embedded in those fields;
the current turn is classified before history is used to resolve ambiguity.
This reduces prompt-injection and stale-context risks, but is not a formal
guarantee against model influence. Sensitive intents and uncertain or
unsupported responses still route to a human. The platform exposes structured
intent, evidence, grounding, decision, and timing metadata—not private
chain-of-thought.

## Production-oriented platform foundation

The platform adds an authenticated REST API and dashboard around the existing
agent core. PostgreSQL is the intended durable deployment database; local
development and offline tests may use SQLite. SQLAlchemy models are migrated
with Alembic. The database is the source of truth for conversations, messages,
agent runs, tickets, feedback, and optional vector knowledge. Redis is used for
cross-worker message rate limiting when configured; if it is unavailable, the
limiter logs the failure and falls back to a process-local counter.

```mermaid
flowchart LR
  UI[Next.js dashboard] --> API[FastAPI routes]
  API --> SVC[Application services]
  SVC --> DB[(PostgreSQL)]
  SVC --> CORE[Phase 1 SupportAgent]
  CORE --> INTENT[Intent detection]
  CORE --> RETRIEVE[TF-IDF or optional pgvector retrieval]
  CORE --> GEN[Configured reply provider]
  CORE --> POLICY[Grounding and escalation policy]
  POLICY --> DB
  DB --> QUEUE[Human-review ticket queue]
  API --> REDIS[(Optional Redis rate limit)]
```

### Local setup

Python 3.14.3 is the verified development runtime. Install the backend and
prepare environment variables:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

For a quick API-only SQLite setup, leave `DATABASE_URL` unset, then run:

```powershell
python -m alembic upgrade head
python -m uvicorn src.api.main:app --reload
```

This creates the local database through migrations. Health checks are available
at `/health` and `/health/ready`; readiness verifies the database. Interactive
API documentation is at `/api/docs` and `/api/redoc`. To generate customer
replies, configure `GEMINI_API_KEY` or `OPENAI_API_KEY` and the corresponding
`SUPPORT_AGENT_PROVIDER` / `SUPPORT_AGENT_MODEL`. Without a provider, the agent
fails closed and opens a human-review ticket.

The default TF-IDF runtime needs the prepared
`data/interim/amazonhelp_conversations.csv` and `data/golden/golden_set.csv`.
Prepare these using the existing data/intents workflow before expecting
historical retrieval in a live local API. Compose bind-mounts the interim and
golden directories read-only; the Docker image itself does not contain raw or
interim customer data. Without the prepared interim CSV, the agent fails closed
to escalation instead of returning an ungrounded answer.

### Docker Compose

Docker Compose runs the backend, PostgreSQL with pgvector, Redis, and frontend.
Copy the example environment file, then start the development stack:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The example database password and JWT secret are local-development placeholders
only. Replace them before any shared or deployed use. Compose applies Alembic
migrations before starting the API. The dashboard is served at
`http://localhost:3000`, the API at `http://localhost:8000`, and API docs at
`http://localhost:8000/api/docs`. A production frontend build must set
`NEXT_PUBLIC_API_BASE_URL` to an HTTPS API origin; only loopback HTTP is
accepted for local development.

To run the frontend outside Docker:

```powershell
Set-Location frontend
npm ci
npm run dev
```

The dashboard has customer sign-in/registration, conversation creation and
chat, AI escalation status, feedback, an agent ticket queue and ticket detail,
and admin analytics. Analytics are calculated from persisted rows; empty
values are shown when there is no data. New registrations are customers only.
Create support staff through the operator-controlled CLI after migrating the
database:

```powershell
python -m src.platform.provision_user --email agent@example.com --role agent
python -m src.platform.provision_user --email admin@example.com --role admin
```

The password is entered interactively, not passed on the command line. The API
does not expose a public role-elevation endpoint.

### API and access control

All application routes use `/api/v1` and bearer tokens:

| Method | Endpoint | Access |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Public; creates a customer |
| `POST` | `/api/v1/auth/token` | Public; login |
| `POST`, `GET` | `/api/v1/conversations` | Authenticated; ownership/staff queue scope |
| `GET` | `/api/v1/conversations/{id}` | Own conversation, permitted queue conversation, or admin |
| `POST`, `GET` | `/api/v1/conversations/{id}/messages` | Customer create; authorized history |
| `POST` | `/api/v1/agent/respond` | Customer; requires `Idempotency-Key` |
| `GET` | `/api/v1/tickets` | Agent sees assigned/open-unassigned cases; admin sees all |
| `GET` | `/api/v1/tickets/{id}` | Assigned/open-unassigned agent or admin |
| `POST` | `/api/v1/tickets/{id}/assign`, `/start`, `/resolve` | Agent/admin with transition checks |
| `POST` | `/api/v1/feedback` | Customer |
| `GET` | `/api/v1/analytics`, `/api/v1/metrics` | Admin |

Tokens are short-lived HS256 bearer tokens. Passwords are PBKDF2-hashed; tokens
do not encode roles, and current roles are loaded from the database. The local
development JWT secret is generated ephemerally if omitted; set a random secret
of at least 32 characters for production. There is no token refresh/revocation
flow or external identity provider. CORS is configurable and rejects wildcard
origins. API errors use a common error envelope and do not return stack traces.
Message creation requires an idempotency key scoped to the conversation; reuse
with different content returns a conflict. The default message limit is 60
requests per user per minute and is configurable with
`RATE_LIMIT_PER_MINUTE`. Redis coordinates limits across workers; its local
fallback is per process and therefore not globally consistent.

### Human review, metrics, and retention

An escalation creates a PostgreSQL-backed ticket in `open` state. Agents can
claim an available case, start work, inspect the transcript, AI draft and
retrieved evidence, then resolve it. Drafts for escalated cases are not returned
as customer-facing replies. Admin analytics summarize database data; the
admin-only `/api/v1/metrics` endpoint exposes lightweight process-local
counters and latency summaries that reset on process restart.

Persisted agent runs carry correlation identifiers, intent and evidence
assessment, provider/model metadata, stage timings, final decision, and safe
escalation reason. Structured operational logs omit message content,
credentials, and tokens. The metrics endpoint is intentionally process-local;
it is not a distributed telemetry backend.

The database stores account email/password hash, conversation metadata, message
text, agent intent/evidence summary/draft/decision, ticket reason and resolution
metadata, and feedback. It does not persist API credentials or bearer tokens.
There is no automatic scheduled retention policy. Operators can preview old
conversation counts, then explicitly apply deletion with cascading removal of
their messages, runs, tickets, and feedback:

```powershell
python -m src.platform.retention --days 365
python -m src.platform.retention --days 365 --apply
```

The first command is read-only. Validate the cutoff and applicable retention
obligations before using `--apply`; backups and legal holds are not managed by
this project.

### Retrieval and knowledge ingestion

TF-IDF remains the default and reproducible lexical baseline. The `Retriever`
interface also has optional PostgreSQL/pgvector cosine-distance retrieval using
384-dimensional `BAAI/bge-small-en-v1.5` embeddings. FastEmbed runs ONNX
Runtime's CPU provider; it avoids the Torch/CUDA dependency stack. Install the
optional dependency with `python -m pip install -r requirements-embeddings.txt`.
Vector mode also requires PostgreSQL with the `vector` extension and downloads
the model on first use. It is optional and is not claimed to improve retrieval
quality without a measured comparison. Compose keeps it out of the default
image; set `INSTALL_SEMANTIC_EMBEDDINGS=1` when building to include it.

Set `RETRIEVER_BACKEND` to `tfidf`, `vector`, or `hybrid`. Hybrid mode merges
the independent lexical and semantic result lists with configurable normalized
weights (`HYBRID_LEXICAL_WEIGHT` and `HYBRID_SEMANTIC_WEIGHT`), stable
deduplication, and deterministic ordering. Top-k and similarity floors are
configurable. TF-IDF remains available as the no-model, no-database baseline;
vector and hybrid modes require PostgreSQL/pgvector and the optional embedding
package. A quality improvement is not claimed until evaluated on labeled,
provenance-appropriate relevance judgments.

The repeatable ingestion command reads existing prepared historical pairs,
excludes golden IDs and exact normalized customer-text duplicates using the
existing leakage-safe builder, and upserts knowledge rows. It does not alter
the source CSVs:

```powershell
$env:RETRIEVER_BACKEND="vector"
$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/support_agent"
python -m alembic upgrade head
python -m src.retrieval.ingest_knowledge
```

The source is the prepared AmazonHelp linked customer/brand conversation-pair
CSV, not the raw downloaded file. Stored fields are the customer tweet ID,
customer text, linked support-response ID and response text, provenance IDs,
and embedding. Use a non-production database when validating ingestion.

### Testing and evaluation

Run offline tests and Python lint checks:

```powershell
python -m pytest -q
ruff check --isolated --select E4,E7,E9,F821 src/agent src/api src/application src/db src/platform src/retrieval src/evaluation/evaluate_integrated_agent.py tests/test_agent_config.py tests/test_agent_context.py tests/test_agent_orchestrator.py tests/test_integrated_evaluation.py tests/test_platform_api.py tests/test_platform_foundation.py tests/test_rate_limit.py tests/test_retrieval_backends.py tests/test_staff_provisioning.py tests/test_retention.py
```

The tests use fake AI and embedding providers; no paid API key is required.
Frontend validation is `npm run typecheck`, then
`$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"; npm run build` for local
development, and `npm audit`. GitHub Actions runs Python lint/tests, a Python
dependency audit, and frontend audit/typecheck/build. The current Python
dependency audit checks the installed development and optional embedding
dependencies with one explicit exception: NLTK 3.10.3 is the latest available
release and is flagged by `PYSEC-2026-3740`; the vulnerable model-artifact APIs
are not used. NLTK and evaluation-only packages are excluded from the backend
runtime image. Revisit the exception when an upstream fix is available.

Historical component benchmarks below remain distinct from the integrated
runtime harness. To run an offline deterministic evaluation, prepare the local
corpus and run:

```powershell
python -m src.evaluation.evaluate_integrated_agent --mock --limit 10
```

The fixed mock asks for human review and makes no model API calls. Its output
labels the run `deterministic_mock`; generation metrics do not measure a model.
For a live-provider smoke evaluation, set provider credentials and the model,
then omit `--mock`; that run can incur cost. Each invocation writes unique
per-example, summary, and content-minimized failure artifacts under the ignored
`reports/evaluation/runs/` directory. Dataset hash/schema drift fails closed.
The frozen dataset fingerprint and caveat are in
`reports/evaluation/evaluation_dataset_manifest.json`.

#### Phase 4 experiment protocol

Run the same frozen dataset through the unchanged majority and TF-IDF +
Logistic Regression baselines and Assistly runtime:

```powershell
# Deterministic provider; requires the prepared local corpus and configured local DB.
python -m src.evaluation.compare_baselines --mode mock

# Explicitly live model run; may incur provider cost and requires credentials.
python -m src.evaluation.compare_baselines --mode live
```

The command produces uniquely named JSON and Markdown outputs. Baseline
definitions are unchanged. Result sections keep deterministic baselines,
mock/live runtime results, judge results, and human-audit results separate; it
does not compute an aggregate score that mixes them. `--limit N` is for
diagnostic subsets only and is recorded in run metadata.

Every integrated run records an evaluation ID, UTC timestamp, available Git
revision, frozen dataset version/hash/provenance state, evaluator and prompt
versions, provider/model, retrieval backend, resolved non-secret configuration,
metric values/denominators, and latency summaries. Token usage and cost are
`null` unless a provider actually reports them. Failure artifacts contain IDs,
intent labels, evidence IDs/status, decision, grounding status, failure
category, and evaluator version—not customer message or reply text.

Metric interpretation:

- Intent accuracy is exact matches / evaluated examples. Macro-F1 averages the
  per-class F1 for target and predicted labels. Both remain provisional because
  label provenance is unresolved.
- Same-intent retrieval Recall@1/3/5 and MRR are **heuristic proxies**: retrieved
  historical messages are assigned intent by the existing local taxonomy.
  They are not independent relevance judgments. Real retrieval relevance
  Recall@K/MRR are not measured until a relevance set is independently labeled.
- Evidence-sufficiency accuracy and adjudicated escalation precision/recall
  remain `null` without independent labels. A deterministic policy violation
  check is reported separately and is not called adjudicated precision.
- Groundedness is the share of returned grounding assessments marked supported.
  Unsupported-claim draft rate is the number of generated drafts with one or
  more unsupported specific claims divided by generated drafts with a grounding
  result. The lexical grounding checker is a diagnostic, not factual truth.
- Error/provider-failure rates use all evaluated examples as denominator;
  provider retry count remains unavailable when the SDK does not expose actual
  internal attempts. Latencies report the count, mean, median, and p95 of
  observed samples for each stage and total.

Regression gates compare only runs with matching dataset hash/version,
evaluator, prompt, backend, and run mode. Thresholds are maintained in
`configs/evaluation_regression_thresholds.json`; missing configured metrics or
incompatible identities fail closed:

```powershell
python -m src.evaluation.regression_gate --baseline path\to\baseline.json --candidate path\to\candidate.json
```

CI exercises the gate with deterministic fixtures only and does not need
provider credentials. Judge rubric/prompt versions are recorded separately;
the deterministic mock judge is a lexical diagnostic, never ground truth.
Judge artifacts retain categorical reason codes and scores, not chain-of-thought.
Live judge output is distinct from mock and human audit data. Existing human
audit artifacts may be described only with their original documented scope;
this workflow does not manufacture new annotations or agreement statistics.

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
python -m src.evaluation.llm_judge --live --limit 220
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

## Tests

Run the complete test suite from the repository root:

```bash
python -m pytest -q
```

Tests use deterministic local data and injected providers; they do not require
live Gemini or OpenAI calls. The integrated-agent tests exercise the request
through intent detection, retrieval, generation, grounding, policy, and final
structured response, including fail-closed error cases.

## Evaluation status and caveats

The reports under `reports/evaluation/` are historical, checked-in
component-level evaluation artifacts. They are not measurements of the new
end-to-end runtime agent. The historical report records 24.09% majority
baseline accuracy, 49.55% accuracy / 53.53% macro-F1 for TF-IDF plus Logistic
Regression, and retrieval intent-match@1/@3/@5 of 31.82% / 48.64% / 56.82%.
These values are preserved as reported; this implementation milestone did not
re-run or alter those benchmark methodologies.

The 220-row golden CSV has 220 populated intent labels, but the repository's
annotation-status note says its worksheet is blank and annotation-ready, while
the AI-proposal note says its labels are AI-proposed; other evaluation text
calls them human-reviewed. This contradiction is unresolved. The labels must
not be described as verified human labels. See
[the provenance note](reports/golden_set_provenance.md). The separate 50-row
human-audit artifacts remain separate and do not establish provenance for the
220-row golden set.

The 49.55% / 53.53% classifier result is an offline TF-IDF + Logistic
Regression baseline. The runtime currently uses a deterministic ordered-regex
taxonomy and reports no calibrated intent confidence. The integrated-agent
harness is separate and has not been run for this milestone; no new integrated
benchmark metrics are claimed.

## Current scope and limitations

Implemented here: the independently callable AI core; FastAPI platform;
SQLAlchemy/Alembic persistence; customer authentication and staff RBAC;
conversation, ticket, feedback and analytics workflows; message idempotency;
optional Redis rate limiting; TF-IDF and optional pgvector retrieval;
knowledge-ingestion tooling; Next.js customer/staff dashboard; Docker Compose;
CI; process-local metrics; retention preview/explicit purge; and a separate
integrated-agent evaluation harness.

Still limited or unverified: this is a production-oriented foundation, not a
production-ready service. No PostgreSQL/pgvector container was run in this
environment, no live integrated-agent evaluation was performed, and vector
retrieval quality has not been compared on measured outcomes. Runtime metrics
are process-local, Redis fallback limits are per process, there is no automated
retention scheduler, external identity provider, token revocation, backup/DR,
or hosted deployment. Retrieval and grounding remain lexical/heuristic rather
than proof of truth. Human-label provenance for the 220-row set remains
unresolved. Treat automatic replies as eligible drafts under a conservative
policy, not guaranteed correct answers.

## Engineering tradeoffs

| Choice | Why it is used | Cost or limitation |
|---|---|---|
| TF-IDF baseline vs. pgvector | Reproducible, lightweight lexical baseline alongside a semantic backend that fits the existing retrieval interface | Semantic retrieval adds PostgreSQL, model-download, and CPU-inference requirements; no quality win is assumed without evaluation |
| SQLite vs. PostgreSQL | SQLite supports fast local tests; PostgreSQL is the durable platform database and supports pgvector | SQLite does not validate all PostgreSQL behavior; deployment migrations and extensions need PostgreSQL testing |
| Mock provider vs. live provider | Deterministic tests and smoke runs need no credentials, network, or API spend | Mock output is not evidence of live-model quality |
| Auto-handle vs. human review | Evidence, grounding, sensitive-intent, and provider checks gate customer-facing drafts | Conservative policy increases review workload; it does not guarantee every auto-handled answer is correct |
| CPU embeddings vs. GPU | ONNX Runtime CPU keeps local and Docker installs practical and avoids Torch/CUDA | CPU embedding throughput is lower than a suitable GPU for large ingestion jobs |

---

## Development Milestones

- [x] Project structure & scaffold
- [x] Dataset inspection & brand selection
- [x] Data cleaning & thread reconstruction
- [x] Intent discovery (clustering)
- [x] Golden evaluation set created (label provenance unresolved; see [provenance note](reports/golden_set_provenance.md))
- [x] Retrieval system (similar conversations)
- [x] Integrated agent core (classify → retrieve → gate → draft → ground → decide)
- [x] Baseline implementations (trivial + simple)
- [x] Evaluation harness (metrics + LLM judge)
- [x] Judge vs. human agreement analysis
- [x] Failure analysis (5 real failure modes)
- [x] Final report with "What is misleading about my headline number?"
- [x] Decision log (10-15 non-obvious decisions)
- [x] FastAPI, SQLAlchemy models and Alembic migrations
- [x] Persisted conversations, agent runs, feedback and human-review tickets
- [x] Authentication, roles, idempotency and configurable rate limiting
- [x] Optional pgvector retrieval and reproducible knowledge ingestion
- [x] Customer chat, support queue and database-backed analytics UI
- [x] Local Docker Compose and CI workflow
- [x] Separate provisional integrated-agent evaluation harness

---

## Design Principles

1. **Simple over clever** — readable code a student can explain line-by-line.
2. **Reproducible** — fixed random seeds, pinned dependencies, config files.
3. **No hardcoded secrets** — all API keys via environment variables.
4. **Honest evaluation** — explicit failure analysis and misleading-metric disclosure.

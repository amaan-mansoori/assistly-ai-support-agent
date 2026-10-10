# Assistly End-to-End Audit — 2026-10-09

## Executive summary

The repository is **FUNCTIONALLY READY FOR A LOCAL DEMO using the deterministic
mock path and an isolated SQLite database**. The actual Next.js UI completed
registration, conversation creation, synthetic message submission through the
FastAPI runtime pipeline, reply display after reload, and feedback submission.
Offline tests cover escalation, ticket access, assignment, start, and resolution.

This does not establish a PostgreSQL/Redis deployment, live-provider behavior,
human-grounded quality, or production readiness. The review queue and external
provider have not been exercised in a deployed stack. No external AI-provider
request, commit, push, deployment, or destructive operation on existing data
occurred; local HTTP API calls used only synthetic input and an isolated test
database.

One confirmed privacy defect was fixed: SQLAlchemy database exceptions could
include bound values in server error logs. Engines now use
`hide_parameters=True`, with a regression test verifying that a synthetic
bound value is absent from the exception.

## Repository and architecture

- Branch: `main`.
- The worktree was already dirty before this audit. Earlier Phase 7/7.1/8
  changes were preserved; only the database error-redaction fix, its test, and
  this report were added by this audit.
- Final Git status: 46 modified tracked files and 6 untracked files. The
  pre-existing entries are listed at the end of this report; do not discard
  them as cleanup.
- Backend: FastAPI application factory in `src/api/main.py`; REST routes under
  `src/api/routes/`; application services under `src/application/`; SQLAlchemy
  entities under `src/db/models/`; Alembic migrations under `alembic/`.
- Frontend: Next.js 15 / React 19 App Router under `frontend/app/`, with the
  browser API client in `frontend/lib/api.ts`.
- AI runtime: `SupportAgent` orchestrates deterministic taxonomy intent
  classification, configured historical retrieval, constrained structured
  generation, grounding checks, and conservative escalation. Provider SDKs are
  behind an injectable callable boundary.
- Persistence: PostgreSQL/pgvector is the intended deployment database;
  SQLite is supported for local and test runs. Redis is optional for
  cross-worker rate limiting and falls back to process-local limiting.
- Evaluation: offline component baselines, deterministic integrated mock
  evaluation, regression gates, annotation/adjudication schemas, and
  independent retrieval evaluation infrastructure exist. No completed
  annotation or adjudication export was found.
- Deployment: Compose defines PostgreSQL/pgvector, Redis, backend, and
  frontend; CI defines Python and frontend checks. Compose syntax was
  validated, but the containers were not started.

## Component status

| Component | Status | Evidence and limitations |
|---|---|---|
| Frontend | VERIFIED WORKING | Typecheck and production build passed. Browser exercised the customer flow against the isolated local API. No formal accessibility audit or full browser matrix was run. |
| Backend | IMPLEMENTED, NOT FULLY VERIFIED | 235 Python tests passed; local API flow passed. PostgreSQL deployment behavior was not exercised. |
| Database | IMPLEMENTED, NOT FULLY VERIFIED | Alembic head and API persistence passed on isolated SQLite. PostgreSQL migrations and pgvector were not run against PostgreSQL. |
| AI pipeline | IMPLEMENTED, NOT FULLY VERIFIED | Real `SupportAgent` stages ran with synthetic retrieval and deterministic injected generation. No live provider request or production-corpus quality run was made. |
| Review queue | VERIFIED WORKING | API tests cover escalation persistence, access controls, and assign/start/resolve transitions. UI review pages build; browser reviewer interaction was not separately exercised. |
| Security | IMPLEMENTED, NOT FULLY VERIFIED | Authentication/authorization, idempotency, rate-limit and error-path tests passed; bound-value logging was hardened. No external penetration or dependency audit was run. |
| Evaluation | PARTIALLY IMPLEMENTED | Baselines, mock evaluator, manifests, annotations and independent-retrieval framework exist. Human ground truth and independent retrieval judgments remain unavailable. |
| Deployment | IMPLEMENTED, NOT FULLY VERIFIED | `docker compose config --quiet` passed. No Docker services, production configuration, TLS, backups, monitoring, or deployment were verified. |

## Backend and frontend audit

### Backend behavior verified

- Environment settings validate supported environments, database URL schemes,
  production JWT-secret length, CORS wildcard rejection, positive rate limits,
  history bounds, and semantic retrieval prerequisites.
- Registration creates a customer role only. Support users are provisioned
  separately. HS256 tokens expire after 30 minutes; the current role is read
  from the database rather than trusted from token claims.
- Conversation ownership and staff queue authorization are enforced server
  side. Message submission requires an idempotency key; reuse with different
  content returns a conflict.
- Escalations persist a ticket and do not return its draft as an
  auto-handled customer reply. Ticket transitions enforce assignment and role
  checks.
- Request logs use correlation ID, method, path, status, and duration; agent
  logs record operational metadata rather than message text. Public unexpected
  API errors use a generic response.
- `/health` checks liveness. `/health/ready` checks only database connectivity;
  it does not verify Redis, provider availability, migrations, or retrieval
  corpus readiness.
- Rate limiting is applied to message creation. Redis unavailability falls
  back to a per-process counter, which is not globally consistent across
  multiple workers.
- Transcript and agent data are intentionally persisted in the database.
  Retention is operator-triggered; no scheduled deletion policy or backup/legal
  hold workflow was verified.

### Frontend behavior verified

- Next.js routes cover dashboard, login/registration, conversations, tickets,
  and analytics. The customer UI submits messages with an idempotency key and
  renders safe API error text.
- The token is stored in browser `localStorage`; this is accessible to
  same-origin JavaScript and is a residual XSS/session-storage risk. There is
  no refresh or revocation flow.
- The shared `fetch` wrapper has no explicit timeout or automatic retry.
  Automatic retries for writes were not added because retry policy must retain
  idempotency semantics and should be chosen deliberately.
- Role-based navigation is client-side presentation only; backend routes remain
  the security boundary.
- Intent/evidence details are not fully surfaced in the customer conversation
  view; the view presents the reply and an escalation notice. Staff ticket
  detail exposes operational review data.

### Local frontend-to-backend journey

Using the actual Next.js dev server and FastAPI app on local test ports, with a
unique temporary SQLite database and a synthetic retriever plus injected
deterministic provider:

1. Dashboard and login pages loaded.
2. Customer registration succeeded.
3. Conversation creation succeeded and navigated to the conversation page.
4. A synthetic delivery-status message reached the real API route and
   `SupportAgent` intent detection, retrieval, sufficiency gate, structured
   reply parsing, and grounding path.
5. The deterministic supported reply was rendered.
6. Reloading the conversation loaded the persisted message and reply.
7. Feedback submission succeeded.
8. API regression tests additionally passed for idempotency, ownership,
   escalation-to-ticket behavior, and staff assignment/start/resolve.

The browser integration used synthetic evidence and deterministic generation;
it is not a real-provider test, nor does it establish live corpus retrieval
quality. The temporary database and both test servers were stopped/removed.

## Defects fixed

| Defect | Change | Verification |
|---|---|---|
| SQLAlchemy statement errors could contain parameter values in server-side exception text/logs. | `make_engine` now sets `hide_parameters=True` for SQLite and PostgreSQL engines. | Added `test_database_errors_do_not_include_bound_parameter_values`; included in final full suite. |

The first browser harness attempt intentionally used an unmigrated temporary
database and a mismatched CORS origin; it failed before the user flow. The
harness was corrected by applying migrations and matching the configured local
origin. No project CORS or migration behavior was changed to hide those setup
errors.

## Evaluation integrity and privacy

- Frozen dataset: 220 rows; SHA-256
  `2a80bd3cafee26ef8a4cc665b9212a33eae4d08e12a808f9e0cfdce00b523b81`.
- Dataset manifest SHA-256:
  `3b0f6fa241cb686832536471d0982ae8434870b83ffa45e6cb23a07d20c4ed77`.
- The checked-in reply-generation artifact has 220 v2 records. Audit scan
  found no prohibited customer-text/customer-ID/context fields, no exact
  source-message matches, and no matches for the selected common email, phone,
  API-key, or bearer patterns. This limited pattern scan is not a general PII
  guarantee.
- A 50-ID annotation sample exists. No `human_annotations_v2.jsonl` export
  exists, so completed annotation coverage is zero. Human-grounded metrics and
  adjudicated independent retrieval Recall@K/MRR/nDCG are **NOT MEASURED**.
- Historical classifier scores (majority accuracy 24.09%; TF-IDF + Logistic
  Regression accuracy 49.55%, macro-F1 53.53%) are provisional reference-label
  baselines. Existing retrieval `31.82% / 48.64% / 56.82%` values are
  same-intent proxies, not independent relevance metrics.
- The prior 10-example deterministic mock run remains a mock diagnostic, not
  live-model or human quality evidence. No baseline, frozen labels, or
  evaluation results were modified in this audit.
- Live Gemini evaluation, latency, token use, cost, and provider reliability
  were **NOT RUN**. No external AI-provider call was made; only the locally
  hosted FastAPI application was exercised.
- Remaining tracked customer-content artifacts include
  `data/golden/golden_set.csv`,
  `data/golden/human_audit_50.csv`, and
  `human_audit_8_analysis.xlsx`. Before external sharing, confirm dataset
  licensing, access controls, distribution permissions, and whether each
  legacy audit artifact still needs to be tracked. No artifacts were deleted
  or rewritten during this audit.

## Verification commands and results

| Command/check | Result |
|---|---|
| `& .\\.venv\\Scripts\\python.exe -m pytest -q` | **235 passed** in 542.77s. No live-provider tests/calls. |
| Configured CI Ruff command: `& .\\.venv\\Scripts\\ruff.exe check --isolated --select E4,E7,E9,F821` over the source/test paths listed in `README.md` | Passed: `All checks passed!` |
| `& .\\.venv\\Scripts\\python.exe -m src.evaluation.regression_gate --baseline tests\\fixtures\\evaluation_baseline.json --candidate tests\\fixtures\\evaluation_candidate.json --thresholds configs\\evaluation_regression_thresholds.json` | Passed; fixture identities compatible and all five configured checks passed. |
| `Set-Location frontend; $env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'; npm run typecheck; npm run build` | Passed: TypeScript check and production build. |
| `docker compose config --quiet` with process-local dummy required variables | Passed. Configuration only; no containers were started. |
| `& .\\.venv\\Scripts\\python.exe -m alembic upgrade head` with a unique temporary SQLite `DATABASE_URL` | Passed: all three migrations reached head. SQLite only. |
| Isolated browser/API synthetic local smoke | Passed: registration, conversation, deterministic agent flow, persisted reply after reload, feedback. |
| API suite scenarios in `test_platform_api.py` | Included in full suite; role boundaries, idempotency, tickets, and staff transitions passed. |
| Artifact/dataset scan | Passed: hashes match; 220 v2 records; zero exact source-text and selected sensitive-pattern matches; 50 sample IDs; no annotation export. |
| `git diff --check` | Passed; Git emitted only existing LF-to-CRLF conversion warnings. |
| Pylance diagnostics for changed Python files | No errors. Only existing informational unused-import/unused-parameter diagnostics in the test/database modules. |

The frontend check was first invoked from the repository root and failed to
find `package.json`; it was rerun from `frontend/` and passed. The current
virtual environment did not contain the already-declared `uvicorn` runtime
dependency, so `uvicorn>=0.34` was installed to run the isolated API smoke.
No dependency manifest was changed. `npm audit`, `pip-audit`, live PostgreSQL,
Redis, and full Compose startup were not run.

## Remaining blockers and recommended manual work

1. Collect independent pseudonymous annotations on the 50-example sample;
   validate each annotator export separately, adjudicate disagreements with
   provenance, and only then report human-grounded response/escalation metrics.
2. Add genuine graded relevance judgments and run the independent retrieval
   evaluator. Keep same-intent retrieval proxies explicitly separate.
3. If approved, run a separately authorized, bounded provider test; no provider
   test is authorized or performed by this audit.
4. Verify migrations and readiness against disposable PostgreSQL/pgvector and
   Redis infrastructure, then exercise the full Compose deployment.
5. Decide whether frontend request timeouts are required and select safe retry
   behavior for idempotent/non-idempotent operations.
6. Review localStorage token exposure, legacy customer-content distribution,
   dataset provenance/licensing, retention/legal-hold requirements, and
   multi-worker rate-limit behavior before shared deployment.
7. Confirm the UI presents the operational intent/evidence/escalation details
   expected for customer and staff roles, and run a formal accessibility and
   browser compatibility review.

## Final readiness

**FUNCTIONALLY READY FOR A LOCAL DEMO** with local SQLite and deterministic
mock generation, subject to the prepared local corpus and current environment.
**Not ready to claim controlled live evaluation or production readiness**:
PostgreSQL/Redis deployment, real provider behavior, human-grounded metrics,
external security testing, operational retention, and deployment controls
remain unverified.

## Git status snapshot

The following status is from the final audit check. Only the database engine
privacy setting, its focused test, and this report are audit changes; the
remaining listed changes were already present in the dirty worktree and were
preserved.

Modified tracked paths (46):

```text
.env.example
.github/workflows/ci.yml
.gitignore
README.md
compose.yaml
configs/default.yaml
reports/evaluation/adjudication_schema_v1.json
reports/evaluation/annotation_schema_v2.json
reports/evaluation/golden_reply_generations.jsonl
reports/evaluation/reply_generation.md
reports/evaluation/retrieval_evaluation.json
reports/evaluation/retrieval_evaluation.md
reports/evaluation/retrieval_failure_examples.json
src/agent/config.py
src/agent/evidence.py
src/agent/orchestrator.py
src/agent/reply_generator.py
src/api/main.py
src/db/database.py
src/evaluation/compare_baselines.py
src/evaluation/dataset_manifest.py
src/evaluation/evaluate_integrated_agent.py
src/evaluation/evaluate_retrieval.py
src/evaluation/generate_golden_replies.py
src/evaluation/grounding.py
src/evaluation/human_grounded_evaluation.py
src/evaluation/llm_judge.py
src/evaluation/regression_gate.py
src/evaluation/reply_quality.py
src/evaluation/run_simple_baseline.py
src/evaluation/run_trivial_baseline.py
tests/fixtures/evaluation_baseline.json
tests/fixtures/evaluation_candidate.json
tests/test_agent_config.py
tests/test_agent_orchestrator.py
tests/test_evaluation_reporting.py
tests/test_generate_golden_replies.py
tests/test_phase4_evaluation_controls.py
tests/test_phase5_quality.py
tests/test_phase6_human_evaluation.py
tests/test_platform_api.py
tests/test_platform_foundation.py
tests/test_reply_generator.py
tests/test_retrieval_evaluation.py
tests/test_simple_baseline.py
tests/test_trivial_baseline.py
```

Untracked paths (6):

```text
reports/evaluation/end_to_end_audit_2026-10-09.md
reports/evaluation/exclusion_schema_v1.json
reports/evaluation/independent_retrieval_evaluation.md
reports/evaluation/phase8_quality_notes.md
src/evaluation/independent_retrieval_evaluation.py
tests/test_independent_retrieval_evaluation.py
```

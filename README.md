# Personalized Outreach Intelligence Engine

AI-powered B2B research and personalized outreach drafting backend. Given a prospect's
name, company, and role, the system researches them via Tavily, extracts evidence-backed
signals with an LLM (Tarqa AI), deterministically scores and ranks those signals, detects
conflicting claims, and drafts a personalized email/LinkedIn message grounded in the
single strongest verified signal - always pending human review before anything is sent.

The backend is FastAPI + Swagger. A minimal Next.js frontend (`frontend/`) covers the
human-in-the-loop workflow: add a prospect, watch research run live, review extracted
signals, and approve/reject/edit the generated drafts.

## Architecture

```
Prospect input -> input validation -> research discovery (Tavily) -> URL dedup ->
content extraction (Tavily Extract + local fallback) -> content cleaning ->
source validation -> signal extraction (Tarqa AI, JSON mode) -> signal classification ->
signal scoring (deterministic) -> conflict detection -> signal selection ->
outreach strategy -> draft generation (email + LinkedIn) -> outreach validation ->
human review (approve/reject/edit)
```

Every stage is persisted to `execution_logs` with timing and status, so a full execution
is replayable via the API. See `app/workflows/prospect_workflow.py` for the orchestrator
and `app/models/enums.py::WorkflowStage` for the stage list.

### Project layout

```
app/
  api/            FastAPI routers (prospects, research, executions, outreach, health)
  integrations/   Tavily + Tarqa AI clients (the only places that call external APIs)
  research/       query generation, LinkedIn/company/professional research, URL safety,
                  crawling, content extraction/cleaning, source validation
  intelligence/   signal extraction (LLM), classification, deterministic scoring,
                  conflict detection, ranking
  outreach/       strategy generation, email/LinkedIn drafting, draft quality validation
  validation/     prospect identity validation, evidence sufficiency gate, LLM JSON parsing
  resilience/     bounded retry/backoff, fallback-chain runner, safe error messages
  workflows/      the end-to-end orchestrator
  models/, schemas/, database/   SQLAlchemy models, Pydantic schemas, DB session/base
migrations/       Alembic migrations
sample_data/      6 synthetic prospect scenarios + matching source/signal fixtures
tests/
  unit/           pure-function tests, no network, no DB
  integration/    DB persistence + mocked-client component tests
  edge_cases/     one test per EC-01..EC-12 (see below)
  end_to_end/     full workflow runs against a real test database with fake LLM/search clients

frontend/         Next.js (App Router, TypeScript, Tailwind) UI - see "Frontend" below
  src/app/        Dashboard (/), New Prospect (/prospects/new), Execution History
                  (/executions), Execution Detail (/executions/[id]) with tabs for
                  Overview/Sources/Signals/Outreach and live polling while running
  src/lib/        typed API client (api.ts), shared types mirroring the backend schemas
  src/components/ Sidebar, status badges, cards/buttons, per-tab execution views

Dockerfile        builds the backend (runs alembic + uvicorn) - used by render.yaml
render.yaml       Render Blueprint: provisions the API + Postgres together
```

## Prerequisites

- Python 3.12+
- PostgreSQL (a local Homebrew/Docker instance both work - see below)
- A Tavily API key
- A Tarqa AI API key + base URL + an available model id (see "Discovering your Tarqa model" below)

## Setup

```bash
cd "B2B Outreach"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: fill in TAVILY_API_KEY, TARQA_API_KEY, TARQA_BASE_URL, TARQA_MODEL,
# and point DATABASE_URL / DATABASE_URL_SYNC at your Postgres instance.
```

### Database

```bash
# create a role + database matching .env.example's defaults (adjust if you changed them)
psql -d postgres -c "CREATE ROLE outreach LOGIN PASSWORD 'outreach';"
createdb -O outreach outreach

alembic upgrade head
```

### Discovering your Tarqa model

Tarqa AI exposes an OpenAI-compatible gateway. Once `TARQA_API_KEY`/`TARQA_BASE_URL` are
set, list the models your account actually has access to before guessing a model id:

```bash
python3 -c "
import asyncio
from app.integrations.tarqa_client import TarqaClient
async def main():
    c = TarqaClient()
    for m in await c.list_models():
        print(m['id'])
asyncio.run(main())
"
```

Pick a model id that returns clean JSON under `response_format={"type":"json_object"}` -
some smaller/weaker models wrap output in markdown fences or invent their own JSON key
names despite instructions (the client defensively strips fences and retries with a
corrective prompt, but a compliant model is faster and more reliable). Set `TARQA_MODEL`
to your choice, then confirm with:

```bash
curl -s http://127.0.0.1:8000/health/integrations | python3 -m json.tool
```

## Running

```bash
uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs
OpenAPI schema: http://127.0.0.1:8000/openapi.json

### Demo: run a full research + drafting execution

```bash
# 1. Create a prospect
curl -s -X POST http://127.0.0.1:8000/api/v1/prospects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "company": "Acme Corp",
    "designation": "VP of Engineering",
    "industry": "SaaS",
    "outreach_channel": "email",
    "product_context": "AI workflow automation platform"
  }'
# -> note the returned "id"

# 2. Kick off research (returns immediately with an execution id; runs in the background)
curl -s -X POST http://127.0.0.1:8000/api/v1/research/run \
  -H "Content-Type: application/json" \
  -d '{"prospect_id": "<id-from-step-1>"}'

# 3. Poll status
curl -s http://127.0.0.1:8000/api/v1/research/<execution_id>

# 4. Inspect what was found
curl -s http://127.0.0.1:8000/api/v1/research/<execution_id>/sources
curl -s http://127.0.0.1:8000/api/v1/research/<execution_id>/signals
curl -s http://127.0.0.1:8000/api/v1/executions/<execution_id>/logs

# 5. Review the generated draft(s) - this also transitions draft_generated -> pending_review
curl -s http://127.0.0.1:8000/api/v1/outreach/<execution_id>

# 6. Approve, reject, or edit a draft (never auto-sent - no send integration exists)
curl -s -X POST http://127.0.0.1:8000/api/v1/outreach/<draft_id>/approve
curl -s -X POST http://127.0.0.1:8000/api/v1/outreach/<draft_id>/reject -d '{"reviewer_notes": "too generic"}'
curl -s -X PATCH http://127.0.0.1:8000/api/v1/outreach/<draft_id> -d '{"body": "edited text..."}'
```

Execution status values: `queued`, `running`, `completed`, `partial`, `needs_review`,
`insufficient_data`, `failed`. `needs_review` means the research succeeded but at least
one conflicting claim was detected and excluded from the draft - check
`GET /api/v1/research/{execution_id}/signals` and the `signal_conflicts` the workflow
recorded before treating the draft as final.

## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# edit .env.local: NEXT_PUBLIC_API_BASE_URL should point at your running backend
# (http://127.0.0.1:8000 for local dev)

npm run dev
```

Open http://localhost:3000. Flow: **Dashboard** (stats + recent executions) → **New
Prospect** (form; submitting creates the prospect and immediately starts a research run,
then redirects to the execution) → **Execution Detail** (live-polls every 4s while
`queued`/`running`, with tabs for stage progress/Sources/Signals/Outreach) → **Execution
History** (all past runs). The Outreach tab is where drafts are edited/approved/rejected -
nothing is ever sent automatically; approval only flips a status flag (section 14).

The frontend is a thin client over the API in `lib/api.ts` - it holds no business logic
duplicate of the backend (scoring, validation, etc. all live server-side).

## Deployment

**Frontend → Vercel, backend → Render.** The backend's research workflow makes many
sequential/parallel LLM + search calls and can take several minutes end-to-end (confirmed
in testing: 4-15 minutes depending on how much is discovered) - well beyond Vercel
serverless function timeouts. Render runs the already-tested `BackgroundTasks` model
as-is on a regular long-lived process, no rearchitecting needed.

### Backend (Render)

`render.yaml` is a Blueprint that provisions both the API and its Postgres database in
one step:

1. Push this repo to GitHub (the `Dockerfile` build ignores `frontend/` via
   `.dockerignore`, so the same repo works for both services).
2. In Render: **New → Blueprint**, point it at this repo. It reads `render.yaml` and
   creates the `outreach-intelligence-api` web service plus an
   `outreach-intelligence-db` Postgres instance, already wired together - the app
   normalizes Render's plain `postgresql://` connection string into the async/sync
   driver-specific URLs itself (`app/config.py::_with_driver`), so there's no manual
   connection-string editing.
3. Before/after the first deploy, fill in the env vars marked `sync: false` in the Render
   dashboard (these hold secrets, so the blueprint can't set them for you):
   - `TAVILY_API_KEY`, `TARQA_API_KEY`, `TARQA_BASE_URL`, `TARQA_MODEL`
   - `CORS_ORIGINS` - set this once you have your Vercel URL (comma-separated if you need
     more than one, e.g. prod + a preview domain)
4. Render builds the `Dockerfile`, which runs `alembic upgrade head` then starts uvicorn
   on the port Render assigns. Confirm with:
   `curl https://<your-render-url>/health/integrations`.

Prefer a manual (non-Blueprint) setup instead? **New → Web Service**, runtime **Docker**,
point at this repo; add a separate **New → PostgreSQL**; then set the same env vars above
plus `DATABASE_URL` (paste the Postgres instance's "Internal Connection String" - the
driver-suffix normalization still applies automatically).

### Frontend

1. In Vercel: **New Project**, import the same repo, and set **Root Directory** to
   `frontend` (Vercel auto-detects Next.js from there - no `vercel.json` needed).
2. Add an environment variable: `NEXT_PUBLIC_API_BASE_URL` = your backend's public URL
   (e.g. `https://your-api.up.railway.app`), for both Production and Preview environments.
3. Deploy. Once you have the Vercel URL, go back to the backend's `CORS_ORIGINS` env var
   and add it (include both the stable production domain and, if you want preview
   deployments to work too, a wildcard-friendly value or each preview domain).

## Testing

```bash
# unit + integration + edge-case + end-to-end tests (no live API credentials required -
# they use an isolated outreach_test Postgres database, auto-created on first run, and
# fake Tavily/Tarqa clients)
pytest tests/unit tests/integration tests/edge_cases tests/end_to_end -v

# everything
pytest
```

All 12 mandated edge cases have a dedicated automated test under `tests/edge_cases/`:

| ID | Scenario | Test file |
|----|----------|-----------|
| EC-01 | No recent LinkedIn activity | `test_ec01_no_linkedin_activity.py` |
| EC-02 | Conflicting information | `test_ec02_conflicting_information.py` |
| EC-03 | Insufficient prospect information | `test_ec03_insufficient_information.py` |
| EC-04 | Outdated/irrelevant signals | `test_ec04_outdated_signals.py` |
| EC-05 | LinkedIn inaccessible | `test_ec05_linkedin_inaccessible.py` |
| EC-06 | Tavily returns zero results | `test_ec06_zero_results.py` |
| EC-07 | Duplicate URLs | `test_ec07_duplicate_urls.py` |
| EC-08 | Website extraction failure | `test_ec08_extraction_failure.py` |
| EC-09 | Tarqa AI API failure | `test_ec09_tarqa_api_failure.py` |
| EC-10 | Invalid LLM JSON | `test_ec10_invalid_llm_json.py` |
| EC-11 | Ambiguous prospect identity | `test_ec11_ambiguous_identity.py` |
| EC-12 | No meaningful outreach angle | `test_ec12_no_outreach_angle.py` |

`tests/conftest.py` spins up a dedicated `outreach_test` Postgres database (reusing
whatever Postgres server `DATABASE_URL` points at) and creates/truncates tables per test -
no Tavily/Tarqa credentials are needed to run any of `tests/unit`, `tests/integration`,
`tests/edge_cases`, or `tests/end_to_end`. `tests/fakes.py` provides `FakeTavilyClient` /
`FakeTarqaClient` test doubles driven by the fixtures in `sample_data/`.

### Optional: live integration check against real Tavily/Tarqa

```bash
curl -s http://127.0.0.1:8000/health/integrations | python3 -m json.tool
```

This hits both providers with real credentials from `.env` - use it to confirm your keys
and chosen model actually work, not as part of the automated test suite.

## Key design notes

- **Evidence typing is never conflated.** A source is tagged `full_page`, `search_snippet`,
  `metadata`, or `user_provided` (`EvidenceType`), and a LinkedIn URL that was never
  crawled is marked `restricted` - both feed directly into deterministic evidence-quality
  scoring, so a snippet can never silently masquerade as a fully verified page.
- **Scoring is deterministic, not LLM-decided.** `final_score = relevance*0.40 +
  business_impact*0.30 + recency*0.20 + evidence_quality*0.10`, computed in plain Python
  (`app/intelligence/*_scorer.py`) from signal-type weight tables, date math, and
  evidence-type/domain checks - the LLM only supplies the raw signal, never the score.
- **Prompt-injection defense.** Webpage content handed to the LLM for signal extraction is
  wrapped in an explicit `UNTRUSTED_WEBPAGE_CONTENT` delimiter with an instruction to
  ignore anything inside it that looks like a command. Every extracted `evidence_excerpt`
  is additionally checked against the source text itself (`_evidence_excerpt_is_grounded`)
  and dropped if it isn't actually present - this catches hallucinated quotes even if the
  model ignores the anti-injection instruction.
- **Conflicts exclude, never arbitrate.** `app/intelligence/conflict_detector.py` is pure
  Python (regex/money/date comparisons) - it never asks the LLM to pick which claim is
  right. Disputed signals are flagged `is_disputed=True` and excluded from signal
  selection; the execution is marked `needs_review`.
- **SSRF protection.** `app/research/url_safety.py` resolves every hostname and rejects
  private/loopback/link-local/reserved addresses before fetching, re-validates every
  redirect hop (redirects are followed manually, not via httpx's auto-follow), and
  `app/research/content_extractor.py` never attempts to crawl `linkedin.com` at all.
- **Background execution + idempotency.** `POST /api/v1/research/run` returns immediately
  with a `queued` execution id and runs the workflow via `BackgroundTasks` on its own DB
  session; an optional `idempotency_key` returns the existing execution instead of
  starting a duplicate.
- **No fabricated LLM fallbacks.** If Tarqa AI is unreachable or returns unparseable JSON
  after corrective retries, the affected stage records the failure and the pipeline either
  continues with what it has or reports `insufficient_data` - it never invents a
  placeholder signal or draft.

## Known limitations / what a production hardening pass would add

- Background tasks run in-process (FastAPI `BackgroundTasks`); a crashed/restarted server
  loses in-flight executions. A real deployment should move this to a durable task queue
  (Celery/RQ/Arq) per section 4's "background execution" note that this is an initial
  approach.
- `robots.txt` checking and SSRF validation happen per-request rather than being cached;
  fine at this volume, would need caching under higher throughput.
- The conflict detector's date-mismatch/job-title heuristics are regex/keyword-based and
  deliberately conservative (restricted to a few signal types, a high text-similarity
  bar) to avoid false positives - tune `app/intelligence/conflict_detector.py`'s
  thresholds if you see it being too aggressive or too lax against real-world text.
- `CORS_ORIGINS` is an exact-match comma-separated list (`app/config.py`), not a wildcard
  pattern - Vercel's per-branch preview URLs each need adding individually if you want
  previews to talk to the same backend, or add `allow_origin_regex` to the
  `CORSMiddleware` config in `app/main.py` if that gets tedious.
- The frontend was verified via `next build`/`eslint` (both clean) and by confirming real
  backend data renders correctly server-side (curl against the rendered HTML); the
  interactive flows (tab switching, edit/approve/reject button handlers) were verified by
  code review, not by driving an actual browser - no browser-automation tool was available
  in this environment. Click through the full flow once after your first deploy.

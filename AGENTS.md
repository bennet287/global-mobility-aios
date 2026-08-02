# Global Mobility AIOS — Agent Guide

This file is written for AI coding agents that need to understand and work on the project. It is based on the actual files in the repository; do not assume anything that is not reflected here.

## Project Overview

Global Mobility AIOS is a **local-first, workflow-first AI operating system** for a global mobility / immigration agency. It is explicitly **not a chatbot**: AI agents are bounded workers inside auditable business workflows.

Core capabilities:

- CRM and lead intake
- Education / study-abroad recommendation engine
- Overseas job / recruitment engine
- Visa & immigration "Truth Engine" (claim verification against official sources)
- Document handling and metadata service
- AI department / agent role registry
- Workflow automation via **n8n**
- Stateful human-in-the-loop workflows via **LangGraph** (optional)
- CRM dashboard and Truth Review Queue web app
- Audit logging and role-based access control

The central safety rule is that visa, immigration, legal, scholarship, and job claims **must not be generated directly by an LLM**. They must pass through the Truth Engine and carry source URL, domain classification, country, confidence score, verification status, timestamp, and a human-review flag where needed.

## Repository Layout

```text
global-mobility-aios/
├── apps/
│   ├── api/                  # FastAPI backend (main app, routers, models, services, tests, alembic)
│   └── web/                  # Next.js 15 operator dashboard + truth review queue
├── agents/                   # AI department role cards (Markdown contracts)
├── workflows/                # LangGraph + n8n workflows
├── knowledge/                # Official source registry and RAG documents
├── infrastructure/           # Deployment and monitoring planning docs
├── docs/                     # Architecture, ADRs, data model, feature specs, test docs
├── scripts/                  # Quality gates, policy checks, demo seeding, release helpers
├── demo_exports/             # Generated demo snapshot artifacts
├── release_exports/          # Generated MVP release bundle/archive artifacts
├── docker-compose.yml        # Full local stack
├── docker-compose.prod.yml   # Slim production stack
├── .env.example              # Local development environment template
├── .env.production.example   # Production environment template
└── alembic.ini               # Default Alembic configuration
```

## Technology Stack

### Backend (`apps/api/`)

- **Python 3.12**
- **FastAPI 0.115+** with **Uvicorn**
- **Pydantic v2** + **Pydantic-Settings** for configuration
- **SQLModel** for ORM/models
- **Alembic** for database migrations
- **psycopg** for PostgreSQL; SQLite also supported for local dev
- **Redis** for cache/state
- **Qdrant** for vector/semantic memory
- **MinIO** for S3-compatible object storage
- **httpx**, **python-multipart**, **PyYAML**, **email-validator**

Optional AI stack (`apps/api/requirements-ai.txt`):

- **LangGraph** 0.2+ (stateful workflows)
- **CrewAI** 0.80+ (multi-agent execution)
- **Ollama** Python client + optional `ollama` container
- **sentence-transformers**, **unstructured**, **pypdf**

Remote LLM providers are supported via the `httpx` client already in `requirements.txt`:

- **DeepSeek** (`deepseek-chat`, `deepseek-reasoner`)
- **Moonshot / Kimi** (`kimi-k1-5`, etc.)

Both expose OpenAI-compatible chat endpoints. Provider selection is controlled by `LLM_PROVIDER` in `.env`. Empty provider falls back to deterministic templates.

These optional AI dependencies are intentionally separated and are **not** installed in the Docker image.

### Frontend (`apps/web/`)

- **Next.js 15.2.4** with App Router
- **React 19**
- **TypeScript 5.8**
- Plain CSS (`globals.css`) — no Tailwind or component library in this branch

### Data Stores

- PostgreSQL (production) / SQLite (local fallback) for transactional data
- Redis for state/cache
- Qdrant for semantic memory
- MinIO for document artifacts

## Code Organization

### Backend (`apps/api/`)

```text
apps/api/
├── alembic/                  # Alembic migrations
│   ├── env.py
│   ├── versions/
│   │   ├── 0001_mvp1_baseline.py
│   │   ├── 0002_official_source_truth_engine.py
│   │   └── 0003_document_upload_minio.py
│   └── alembic.ini
├── app/
│   ├── main.py               # FastAPI factory, lifespan, CORS, auth middleware, router inclusion
│   ├── schemas.py            # Pydantic v2 request/response schemas
│   ├── agents/
│   │   └── registry.py       # Controlled agent registry and aliases
│   ├── core/
│   │   ├── auth.py           # Role-based auth middleware and session cookies
│   │   ├── config.py         # Pydantic-Settings configuration
│   │   ├── database_url.py   # URL normalization and masking
│   │   └── db.py             # SQLModel engine, sessions, model registration
│   ├── models/
│   │   └── domain.py         # SQLModel entities (single source of table definitions)
│   ├── routers/              # ~30 FastAPI routers (JSON API + HTML admin pages)
│   ├── services/             # Business logic: truth engine, documents, audit, controlled agents, LLM client, role-card loader
│   └── workflows/
│       └── intake_graph.py   # Optional LangGraph skeleton
├── tests/                    # pytest suite (26 test files + conftest.py)
├── Dockerfile
├── .dockerignore
├── requirements.txt          # Core Python dependencies
└── requirements-ai.txt       # Optional AI/LLM dependencies
```

### Frontend (`apps/web/`)

```text
apps/web/
├── app/
│   ├── globals.css           # Custom CSS design system
│   ├── layout.tsx            # Root layout
│   └── page.tsx              # Single-page operator dashboard
├── lib/
│   └── api.ts                # Typed API client and endpoint helpers
├── Dockerfile
├── README.md
├── next.config.js
├── package.json
└── tsconfig.json
```

### Agents, Workflows, Knowledge, Infrastructure

- `agents/role_cards/*.md` — Human-readable role contracts (Head of Product, AI CEO, Visa Truth Agent, Document Officer, etc.).
- `workflows/langgraph/README.md` — Guidance for stateful human-in-the-loop graphs.
- `workflows/n8n/lead_intake_example.json` — Example n8n workflow that forwards webhooks to the API.
- `knowledge/official_sources/sources.yaml` — Canonical registry of authoritative sources used by the Truth Engine.
- `knowledge/rag/README.md` — Policy placeholder requiring provenance metadata for any RAG content.
- `infrastructure/deployment/README.md` — Current Docker Compose and future deployment targets.
- `infrastructure/monitoring/README.md` — Recommended later-phase observability stack (Langfuse, Prometheus, Grafana, OpenTelemetry, Loki).

## Build and Run Commands

### Local Development (Docker Compose)

```bash
cp .env.example .env.docker
docker compose up --build
```

The development Compose profile reads `.env.docker`. Keep `.env` available for
host-only overrides; using Docker service hostnames there breaks local Python
quality scripts.

Exposed services:

- API/docs: `http://localhost:8000/docs`
- Web dashboard: `http://localhost:3000`
- n8n: `http://localhost:5678`
- MinIO console: `http://localhost:9001`
- Qdrant dashboard: `http://localhost:6333/dashboard`

Optional local LLM:

```bash
docker compose --profile local-ai up ollama
```

### Backend (local without Docker)

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
# optionally install AI stack
pip install -r requirements-ai.txt

# For SQLite local dev (default settings auto-create tables):
uvicorn app.main:app --reload

# For PostgreSQL, set DATABASE_URL and run migrations first:
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend (local without Docker)

```bash
cd apps/web
npm install
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
npm run dev
```

### Production / Demo

```bash
# Copy and edit POSTGRES_PASSWORD, DATABASE_URL, JWT_SECRET, AUTH_ADMIN_PASSWORD
cp .env.production.example .env.production

docker compose --env-file .env.production -f docker-compose.prod.yml up --build
```

Startup order in production:

1. `postgres` healthy
2. `api-migrate` runs `alembic -c alembic.ini upgrade head`
3. `api` starts after migrations succeed

## Testing Instructions

### Backend Tests

The test suite lives in `apps/api/tests/` and uses **pytest**.

```bash
cd apps/api
python -m pytest tests -q
```

The project-level quality gate runs pytest with `PYTHONPATH=apps/api`:

```bash
python -m pytest apps/api/tests -q
```

Key fixtures in `apps/api/tests/conftest.py`:

- In-memory SQLite engine with `StaticPool`
- `db_session` monkey-patches `app.core.db.engine`
- `raw_client` overrides `get_session`
- `client` sets `X-GMAI-Role: admin` and `X-GMAI-User: pytest-admin`
- Helper factories: `create_lead`, `create_document`, `create_application`, `create_truth_claim`

Test coverage includes:

- Auth roles / login
- DB URL normalization and schema checks
- FastAPI lifespan
- Pydantic v2 compatibility
- UTC timestamp compatibility
- Controlled agents and review queue
- Truth resolution / official sources
- Document uploads / verification
- Audit logs, client communications, authority onboarding
- Release / demo readiness gates
- Local quality gate integration

### Frontend Tests

There is currently **no testing setup** for the web frontend. The project does not include `jest`, `vitest`, `@playwright/test`, or any test files.

### Quality Gate Scripts

Run the full local quality gate from the repository root:

```bash
python scripts/check_local_quality.py
```

Individual checks:

```bash
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py
python scripts/check_local_db_schema.py
python scripts/check_mvp_release.py
python scripts/check_github_release_ready.py
```

Demo helpers:

```bash
python scripts/seed_demo_data.py
python scripts/export_demo_snapshot.py
python scripts/export_mvp_release_bundle.py
python scripts/export_mvp_release_archive.py
```

### Switching LLM Providers

The system supports DeepSeek and Moonshot/Kimi via a provider-agnostic client:

```bash
# Use DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat

# Or use Moonshot / Kimi
LLM_PROVIDER=moonshot
MOONSHOT_API_KEY=sk-...
MOONSHOT_MODEL=kimi-k1-5

# Or disable remote LLM and use deterministic templates
LLM_PROVIDER=
```

After changing `.env`, restart the API. The active provider is exposed at `GET /api/v1/controlled-agents/providers`.

### Background Worker (Celery)

Batch agent execution uses Celery with Redis:

```bash
# Docker Compose (includes worker service)
docker compose up --build

# Or run worker locally
cd apps/api
celery -A app.core.celery_app worker --loglevel=info --concurrency=2
```

Official-source monitor scheduling also requires Celery Beat:

```bash
cd apps/api
celery -A app.core.celery_app beat --loglevel=info
```

API endpoints:

- `POST /api/v1/controlled-agents/run-batch` — enqueue tasks for many leads.
- `GET /api/v1/agent-output-reviews/queue` — view pending outputs.
- `POST /api/v1/agent-output-reviews/batch-approve` / `batch-reject` / `batch-convert` — review a batch.

Admin UI:

- `/admin/controlled-agents` — select leads and enqueue a batch.
- `/admin/agent-output-reviews` — select outputs and bulk approve/reject/convert.

## Code Style Guidelines

- **Python 3.12**, **TypeScript 5.8 strict mode**.
- Backend uses **Pydantic v2** models for both settings and request/response schemas. Do not introduce Pydantic v1 patterns.
- All primary keys are **UUIDs**.
- Complex data is stored in `*_json` string columns in the SQLModel tables.
- Routers are versioned with tags like `tags=["document-upload-v3.5"]`.
- JSON API routes are usually under `/api/v1/...`; admin HTML routes are under `/admin/...`.
- The frontend is a single-page Next.js App Router app. Almost all UI code is in `app/page.tsx`.
- Custom CSS variables are defined in `app/globals.css`; no Tailwind or UI component library is currently used.
- Keep AI dependencies isolated in `requirements-ai.txt`; do not add them to `requirements.txt` unless production execution truly requires them.
- Maintain the deterministic, review-gated controlled-agent pattern: outputs should be `client_facing: False` and `human_review_required: True` by default.

## Security Considerations

- **Truth Engine is mandatory** for visa, immigration, legal, scholarship, and job claims. Never generate such claims directly from an LLM in code.
- The API uses role-based access control with roles: `admin`, `operator`, `reviewer`, `sales`, `read_only`.
- Local dev enables header-based auth via `X-GMAI-Role` / `X-GMAI-User` when `AUTH_ALLOW_HEADER_ROLE=true`. This must be disabled in production.
- Default credentials and secrets in `.env.example` are for local development only. Always change `JWT_SECRET`, `AUTH_ADMIN_PASSWORD`, and database credentials for production.
- MinIO defaults in `.env.example` are insecure and must be changed for any non-local deployment.
- All sensitive agent outputs and state transitions must write an `AuditLog` entry.
- Document storage supports local filesystem or MinIO. Use MinIO (or another S3-compatible store) for any shared/production deployment.
- The repository enforces an approved-source allowlist via `docs/REPOSITORY_POLICY.md` and CI. Check policy before adding new dependencies.
- Do not store unattributed visa or immigration rules in the RAG knowledge area.

## Deployment and CI

- **CI**: `.github/workflows/repo-policy-check.yml` runs `python scripts/check_repo_policy.py --root .` on every PR and push to `main`.
- **Release packaging**: `scripts/export_mvp_release_bundle.py` and `scripts/export_mvp_release_archive.py` generate artifacts under `release_exports/`.
- **Production stack**: `docker-compose.prod.yml` runs PostgreSQL + Alembic migration job + API only. Redis, Qdrant, MinIO, n8n, and the web frontend build are excluded from this profile and are planned for later phases.

## Conventions to Preserve

1. **Workflow-first, agent-assisted architecture** — agents are bounded workers, not autonomous authorities.
2. **Deterministic controlled agents with optional LLM augmentation** — v4.0 agents default to rule-based templates when `LLM_PROVIDER` is empty. When configured, they call DeepSeek or Moonshot using the markdown role cards as system prompts, but always fall back to deterministic templates on failure and remain review-gated.
3. **Autonomous multi-tasking with Celery** — agents can receive a batch of tasks, execute them asynchronously in a background worker, and queue all outputs for final human review. No task waits for approval before the next one starts.
4. **Truth Engine as a safety gate** — every visa/job/study/scholarship claim must pass source verification.
4. **Human-in-the-loop by default** — sensitive workflows pause for human review.
5. **Audit-everything** — `AgentRun`, `AuditLog`, `SourceCheckRun`, `SourceSnapshot`, `HumanReview` provide traceability.
6. **Source provenance over RAG volume** — `knowledge/rag/README.md` forbids unattributed immigration rules.
7. **Versioned features** — code and docs use explicit version markers (e.g., `v4.0`, `v5.6`) in filenames, router comments, and audit `source` fields.
8. **Local-first, Docker-optional** — default SQLite/localhost config; docker-compose provides the full local dependency stack.

## Useful Reference Files

- `README.md` — Quick start and MVP-1 API surface
- `docs/GLOBAL_MOBILITY_AIOS_VISION_V1.md` — Canonical complete product scope and coverage ledger
- `docs/ROADMAP.md` — Phased delivery plan for the canonical product scope
- `docs/ARCHITECTURE.md` — Runtime architecture
- `docs/REPOSITORY_POLICY.md` — Dependency and repository allowlist
- `docs/SECURITY_AND_COMPLIANCE.md` — Security rules
- `docs/TRUTH_ENGINE_SPEC.md` — Truth Engine requirements
- `docs/TEST_SUITE_V2_9.md` — Test suite documentation
- `docs/CONTROLLED_AI_AGENTS_V4_0.md` — Controlled agent design
- `docs/DOCKER_PRODUCTION_PROFILE_V3_3.md` — Production deployment guide

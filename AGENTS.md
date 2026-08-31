# Global Mobility AIOS — Agent Guide

This guide is for AI coding agents and developers working on the active Global Mobility AIOS repository. Treat repository state, accepted proof records, and `docs/ROADMAP.md` as authority. Do not infer capabilities, acceptance, or infrastructure that the repository does not prove.

**New session recovery:** read `agents/SESSION_HANDOFF.md` first for current branch state, open acceptance gates, and recent decisions. Verify its claims against `docs/ROADMAP.md`, `docs/CHANGELOG.md`, and the actual git remotes before acting.

## 1. Product identity and constitutional boundaries

Global Mobility AIOS is a **governed, evidence-grounded, transparent digital organization for global mobility**. It is not a generic chatbot, agent framework, SaaS admin dashboard, or autonomous legal/immigration decision-maker.

The core product direction is:

```text
Human Owner / Board sovereignty
→ persistent OrganizationPositions / AI employees
→ purpose-scoped ContextBundles
→ governed Evidence / SourceSnapshots / VerifiedRules
→ bounded WorkItems / Missions
→ typed material actions
→ Command Gateway authority / autonomy / risk checks
→ durable organizational execution
→ Board-safe transparency and replay
```

Permanent rules:

```text
CAN DO != MAY DO
Memory != Truth
Model/provider identity != authority
Telemetry != canonical OrganizationActivity
Implementation != acceptance
```

Visa, immigration, legal, scholarship, job, tax, investment, and other regulated/material claims must remain grounded in the project's governed truth/evidence model. An LLM response is never canonical truth by itself.

## 2. Active product milestone

The active product milestone is **L — Live Organization**.

Current status:

```text
L Live Organization              IMPLEMENTED / ACCEPTANCE PENDING
M Board Transparency Experience  NOT STARTED
N Learning & Optimization        NOT STARTED
```

Do not advance M merely because L code exists. The live-provider/fresh-retrieval/failure/replay runtime gates are recorded in `docs/V1_3_L_LIVE_RUNTIME_ACCEPTANCE_EVIDENCE_2026-08-30.md`. L remains open until genuine independent professional-review evidence and final exact-current-head technical proof are recorded under `docs/L_LIVE_ORGANIZATION_ACCEPTANCE_OPERATIONS.md`.

A deterministic fallback path or synthetic integration test may prove technical lineage, but it does not substitute for live-provider success or independent professional correctness evidence.

## 3. Repository layout

```text
global-mobility-aios/
├── apps/
│   ├── api/                  # FastAPI backend, Alembic, services, routers, tests
│   └── web/                  # Next.js operator/Cockpit product surface
│       └── e2e/              # Playwright browser E2E for Live Organization
├── agents/                   # AI employee / department role cards
├── workflows/                # LangGraph/n8n workflow material
├── knowledge/                # Official-source registry and governed knowledge assets
├── infrastructure/           # Deployment / monitoring material
├── docs/                     # Architecture, roadmap, acceptance, runbooks, changelog
├── scripts/                  # Quality gates and operational/acceptance tooling
├── vendor/                   # Frozen donor/reference snapshots; not canonical runtime authority
├── .woodpecker/              # Forward CI pipelines
├── .github/workflows/        # Historical/fallback GitHub Actions proof workflows
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .env.production.example
└── alembic.ini
```

There is **no first-party Electron application under `apps/`**. Electron code present beneath frozen vendor snapshots (for example Munder Difflin) is donor/reference material unless a later accepted milestone explicitly adopts it. Current first-party product E2E is Chromium Playwright against the Next.js application.

## 4. Technology stack

### Backend (`apps/api/`)

- Python 3.12 or 3.13
- FastAPI + Uvicorn
- Pydantic v2 / Pydantic-Settings
- SQLModel
- Alembic
- PostgreSQL via psycopg; SQLite for bounded local/test use
- Redis
- Qdrant
- MinIO / S3-compatible document storage
- httpx
- Celery for background work

Optional AI dependencies live in `apps/api/requirements-ai.txt` and remain separated from the core dependency contract unless production necessity changes that boundary.

### Remote LLM providers

The first-party provider configuration in `apps/api/app/core/config.py` supports:

- DeepSeek
- Moonshot / Kimi
- Gemini

Provider selection is controlled by `LLM_PROVIDER`. Current default provider settings include:

```text
DeepSeek  deepseek-chat
Moonshot  kimi-k1-5
Gemini    gemini-3.7-flash
```

The corresponding credential variables are:

```text
DEEPSEEK_API_KEY
MOONSHOT_API_KEY
GEMINI_API_KEY
```

The normal controlled-agent stack may use deterministic template fallback when configured to do so. **Milestone L live-provider acceptance is stricter:** a live configured provider must be selected with a credential, and template fallback must be disabled for an acceptance execution. Follow the L operations runbook rather than treating generic fallback behavior as acceptance evidence.

### Frontend (`apps/web/`)

The current package contract is:

- Node.js 24 accepted proof runtime (`.nvmrc`)
- Next.js 16.3.1
- React / React DOM 19.0.8
- TypeScript 5.8.3
- App Router
- custom CSS; no first-party Tailwind/component-library dependency in this branch

### Browser E2E (`apps/web/e2e/`)

- Playwright 1.62.1
- Chromium / Desktop Chrome project
- base URL `http://127.0.0.1:3000`
- current primary spec: `apps/web/e2e/tests/live-organization.spec.ts`

The Playwright config starts the already-built Next.js app with `npm --prefix .. run start`. In CI, the normal frontend build step runs before browser E2E.

## 5. Canonical organization/runtime areas

Important current implementation seams include:

```text
apps/api/app/services/organization_*
apps/api/app/routers/organization_*
apps/api/app/models/*autonomy*
apps/api/app/models/domain.py
apps/api/app/core/organization_constitution.py
apps/api/app/core/auth_policy.py
apps/api/app/evaluations/
apps/api/tests/test_organization_*
```

Current L/Austria runtime/evaluation areas include:

```text
apps/api/app/services/organization_mobility_live_organization.py
apps/api/app/services/organization_mobility_live_provider_cycle.py
apps/api/app/services/organization_mobility_live_provider_evaluation.py
apps/api/app/services/organization_mobility_fresh_retrieval.py
apps/api/app/services/organization_mobility_objective_runtime.py
apps/api/app/services/organization_mobility_objective_execution.py
apps/api/app/services/organization_mobility_pathway_brief.py
apps/api/tests/test_organization_mobility_live_*.py
scripts/evaluate_austria_live_provider.py
scripts/prepare_austria_professional_review.py
```

Do not perform a broad Austria-to-generic rewrite while L acceptance is still stabilizing unless a concrete second vertical or proven duplication requires it. Extract proven seams, not speculative abstractions.

## 6. Local setup

### Python

Use Python 3.12 or 3.13. Create the environment at repository root and install the constrained dependency contract:

```bash
# Windows example
C:/miniconda3/python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt -c apps\api\constraints.txt
.\.venv\Scripts\python.exe -m pip check

# Linux/macOS example
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r apps/api/requirements.txt -c apps/api/constraints.txt
python -m pip check
```

Do not treat an unconstrained `requirements.txt` install as the accepted reproducibility baseline.

### API

SQLite/local:

```bash
cd apps/api
uvicorn app.main:app --reload
```

PostgreSQL:

```bash
cd apps/api
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

Use Node 24:

```bash
nvm use
cd apps/web
npm ci
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
npm run dev
```

On Windows without `nvm`, use a Node 24 installation and verify `node --version` before dependency installation or proof.

### Docker Compose

```bash
cp .env.example .env.docker
docker compose up --build
```

For production/demo configuration:

```bash
cp .env.production.example .env.production
docker compose --env-file .env.production -f docker-compose.prod.yml up --build
```

Never copy local/example credentials into a real deployment unchanged.

## 7. Testing and proof instructions

### Backend regression

From repository root:

```bash
# Windows
.\.venv\Scripts\python.exe -m pytest apps/api/tests -q

# Linux/macOS
PYTHONPATH=apps/api python -m pytest apps/api/tests -q
```

`apps/api/tests/conftest.py` supports isolated SQLite behavior and optional PostgreSQL execution through `GMAI_TEST_DATABASE_URL`.

Never report a historical test count as if it were a current-head run. A previous green commit is historical evidence only.

### Frontend contract/types/build proof

From `apps/web` under Node 24:

```bash
npm ci
npm audit --audit-level=high
npm run test:design-foundation
npm run test:request-auth
npx tsc --noEmit
npm run build
npm run test:compiled-auth
```

The auth/base-URL environment should match the relevant CI pipeline when reproducing CI behavior.

### Browser E2E

The repository **does have an active Playwright/browser E2E suite**.

After the `apps/web` production build exists:

```bash
cd apps/web/e2e
npm ci
npm audit --audit-level=high
npm test
```

`npm test` runs:

```text
playwright test --project=chromium
```

The browser suite is product/UX proof for the bounded Live Organization surface. It is not a substitute for backend integration, PostgreSQL concurrency, live-provider quality, professional review, or external-action acceptance.

### Repository and quality gates

Primary repository checks include:

```bash
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py
python scripts/check_local_db_schema.py
python scripts/check_release_consistency.py --root .
python scripts/check_python_dependency_constraints.py
```

Use `python scripts/check_local_quality.py` for the repository's aggregate local quality path when appropriate.

Do not claim a check passed unless it was actually executed for the commit/state being described.

## 8. Milestone L live-provider acceptance tooling

Use the bounded operator CLI:

```bash
python scripts/evaluate_austria_live_provider.py --check-config
python scripts/evaluate_austria_live_provider.py --tenant-key <tenant> --list-candidates
python scripts/evaluate_austria_live_provider.py --tenant-key <tenant> --root-work-item-id <uuid> --execute-live
```

The CLI:

- masks database URLs in output;
- reports provider/model identity without exposing secrets;
- recognizes DeepSeek, Moonshot, and Gemini configuration;
- requires a real configured provider credential for live selection;
- treats `LLM_FALLBACK_TO_TEMPLATE=false` as part of live-provider acceptance readiness;
- requires fresh retrieval before live K.1/L execution;
- consumes the selected fresh objective on a live attempt;
- does not create objectives automatically;
- does not grant external-action authority.

Read `docs/L_LIVE_ORGANIZATION_ACCEPTANCE_OPERATIONS.md` before an acceptance execution. A successful deterministic fallback is not live-provider acceptance.

## 9. Background worker

Celery uses Redis:

```bash
cd apps/api
celery -A app.core.celery_app worker --loglevel=info --concurrency=2
```

Scheduled source-monitor work also requires Celery Beat:

```bash
cd apps/api
celery -A app.core.celery_app beat --loglevel=info
```

Background execution does not expand authority. Material actions remain governed through accepted policy/Command Gateway boundaries.

## 10. CI direction and proof semantics

### Forward CI authority

The repository's forward CI direction is **self-hosted Woodpecker**. Active pipeline definitions are:

```text
.woodpecker/backend-sqlite.yml
.woodpecker/frontend.yml
.woodpecker/postgres-governance.yml
.woodpecker/repository-policy.yml
```

The frontend Woodpecker pipeline currently runs both:

```text
frontend tests/types/build/compiled-auth
live-organization Chromium Playwright E2E
```

Historical GitHub Actions workflows under `.github/workflows/` remain useful proof/fallback artifacts and may still run, but they are not the forward CI direction.

### Exact-head rule

A milestone may be called `COMPLETE / PASS / SEALED` only from observed proof that belongs to the accepted candidate/head under the milestone's documented gate.

Permanent evidence rules:

- a later code or docs commit does not automatically inherit exact-head PASS from an earlier commit;
- CI that never reaches executable steps is infrastructure/runner evidence, not a repository-test result;
- a failing workflow label alone is insufficient to say repository tests failed if no test step ran;
- a prior green Woodpecker/GitHub Actions run remains historical proof for that exact checkpoint only;
- focused local proof is useful but does not silently replace a required full/exact-head acceptance gate;
- docs must distinguish implementation truth, technical proof, external acceptance, and professional correctness.

## 11. Code and architecture conventions

- Use Python 3.12/3.13 and Pydantic v2 patterns.
- Primary keys are UUIDs unless an existing domain contract explicitly differs.
- Keep canonical organizational meaning in AIOS-owned models/services; vendor or provider state cannot redefine it.
- Keep external provider/model selection non-authorizing.
- Keep material side effects behind the existing governance/authority model.
- Preserve deterministic idempotency/replay semantics.
- Preserve exact provenance and evidence lineage when regulated claims enter a material path.
- Prefer public semantic contracts over cross-module imports of private helpers once the semantic seam is proven.
- Do not introduce a generic framework merely to reduce file size or duplicate a small amount of route-specific code.
- Keep optional AI dependencies isolated unless production necessity requires promotion.
- Frontend uses Next.js App Router and the current custom design system/CSS.
- Board/Cockpit surfaces must display persisted canonical truth, not fabricated activity for visual effect.

## 12. Security and privacy

- Never commit live credentials, API keys, JWT secrets, passwords, provider secrets, database secrets, or personal case data.
- Example/default credentials are local-only.
- `AUTH_ALLOW_HEADER_ROLE=true` is a local/test convenience and must not become a production authorization shortcut.
- Provider credentials must remain secrets, not context/memory/evidence.
- Never send case-scoped data to an external provider merely because a provider is configured; follow the accepted provider-egress/runtime policy for the capability.
- Truth/Evidence requirements remain mandatory for regulated/material claims.
- Tenant isolation, authority, idempotency, concurrency, and provenance checks are product safety properties, not optional hardening.
- Repository dependency/source policy is defined by `docs/REPOSITORY_POLICY.md` and its checks.
- Do not store unattributed immigration rules as authoritative RAG content.

## 13. Vendor/donor boundaries

`vendor/` contains frozen donor/reference material. Vendoring is not production adoption.

Munder Difflin and Plasma may supply ideas or bounded mechanics only through an explicit AIOS-owned adoption decision. Do not import donor authority models, canonical state semantics, or visual language automatically.

Do not edit frozen upstream donor snapshots merely to make first-party policy/tests green unless the repository's vendor provenance process explicitly requires a refreshed snapshot.

## 14. Documentation discipline

For meaningful work, reconcile the documents that define repository truth:

```text
docs/ROADMAP.md       scheduling / milestone / acceptance truth
docs/CHANGELOG.md     meaningful delivered change
acceptance record     proof for a sealed milestone/slice
domain runbook/spec   operational contract when applicable
AGENTS.md              current implementation/working guidance
```

Never rewrite historical acceptance entries to pretend later evidence existed earlier. Add a new reconciliation entry when current truth changes.

When documenting a proof checkpoint, include enough identity to distinguish:

```text
commit/candidate
proof system + run number
what actually executed
what remains unproven
```

## 15. Useful current references

- `docs/ROADMAP.md` — master necessity-driven orchestration and milestone status
- `docs/CHANGELOG.md` — active V12 delivery history
- `docs/L_LIVE_ORGANIZATION_ACCEPTANCE_OPERATIONS.md` — L external/live acceptance runbook
- `docs/V1_3_K1_BOUNDED_SPECIALIST_EXECUTION_ACCEPTANCE_2026-08-22.md` — sealed K.1 baseline
- `docs/GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md` — active combined architecture
- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md` — organization architecture
- `docs/AIOS_FRONTEND_DESIGN_UX_PROGRAMME_V1.md` — frontend/UX programme
- `docs/ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md` — integration boundaries
- `docs/REPOSITORY_POLICY.md` — repository/dependency policy
- `docs/SECURITY_AND_COMPLIANCE.md` — security guidance
- `.woodpecker/*.yml` — forward CI definitions

## 16. Working rule for agents

Before changing implementation:

```text
inspect current branch/head
→ inspect current ROADMAP/acceptance state
→ identify the smallest necessary product gap
→ modify implementation + tests together
→ run the checks you can actually execute
→ record only observed evidence
→ reconcile ROADMAP/CHANGELOG when state meaningfully changes
→ never promote the next dependent milestone without acceptance
```

Repository truth wins over assumptions, old chat history, stale documentation, or the apparent status of a workflow that did not execute its steps.

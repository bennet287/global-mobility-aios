# Global Mobility AIOS — Repository Agent Guide

This guide owns repository mechanics: layout, stack, setup-relevant implementation seams, security/vendor boundaries, and project-specific engineering conventions. It does **not** own the active programme, current branch head, next slice, or acceptance status.

For substantial work, enter through `AGENTS.md`. Resolve current programme truth from `agents/PROJECT_STATE.md`, scheduling from `docs/ROADMAP.md`, and live refs/PR/workflows from GitHub.

Where this guide names versions, paths, or configuration, verify the actual package/configuration file when the detail is material to the change.

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

## 2. Status ownership

Do not place active-phase or “next task” prose in this guide. Those facts drift faster than repository mechanics.

- `agents/PROJECT_STATE.md` owns concise current programme truth.
- `docs/ROADMAP.md` owns remaining programme order and rationale.
- GitHub owns live branch/PR/commit/workflow state.
- `agents/SESSION_HANDOFF.md` is only a minimal recovery pointer.
- `docs/CHANGELOG.md` and dated phase/acceptance records are historical evidence, not the current work queue.

If this guide conflicts with live code/configuration or an accepted architecture/specification, verify the owning source and update the stale guide text rather than creating another repository guide.

## 3. Repository layout

```text
global-mobility-aios/
├── apps/
│   ├── api/                  # FastAPI backend, Alembic, services, routers, tests
│   └── web/                  # Next.js operator/Cockpit product surface
│       └── e2e/              # Playwright browser E2E for Live Organization
├── agents/                   # agent engineering governance + AI employee/department role cards
├── workflows/                # workflow material
├── knowledge/                # official-source registry and governed knowledge assets
├── infrastructure/           # deployment / monitoring material
├── docs/                     # architecture, roadmap, acceptance, runbooks, changelog
├── scripts/                  # quality gates and operational/acceptance tooling
├── vendor/                   # frozen donor/reference snapshots; not canonical runtime authority
├── .woodpecker/              # forward CI pipelines
├── .github/workflows/        # GitHub Actions proof workflows
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

Provider selection is controlled by `LLM_PROVIDER`. Current default provider settings should be read from `apps/api/app/core/config.py`; do not duplicate them here as programme truth.

Credential-variable names and provider-specific configuration likewise belong to the real configuration file and environment examples. Never put secrets or credential values into repository guidance.

Historical live-provider acceptance may impose stricter conditions than normal deterministic fallback. When a task touches that sealed acceptance path, follow its task-specific runbook and verify the current code/configuration rather than treating generic fallback behavior as acceptance evidence.

### Frontend (`apps/web/`)

Verify exact versions from `apps/web/package.json` and the accepted lockfile. The current first-party frontend architecture uses:

- Next.js / App Router
- React
- TypeScript
- custom CSS and the repository's accepted design system/conventions

### Browser E2E (`apps/web/e2e/`)

The first-party browser proof uses Playwright/Chromium against the real Next.js application. Verify the current Playwright configuration and active specs before changing browser-proof behavior.

For accepted candidate work, a generated screenshot or successful command is not enough when the governing profile requires actual browser/visual inspection.

## 5. Canonical organization/runtime areas

Important implementation seams include:

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

Historical L/Austria runtime/evaluation areas remain relevant when a task actually touches that accepted path:

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

Do not perform a broad Austria-to-generic rewrite merely because historical seams exist. Extract a reusable abstraction only when a current product need or proven duplication justifies it, and preserve the accepted evidence/truth boundaries of the original path.

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

Use the Node version pinned by `.nvmrc`:

```bash
nvm use
cd apps/web
npm ci
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
npm run dev
```

On Windows without `nvm`, install the pinned Node major and verify `node --version` before dependency installation or proof.

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

For exact-head acceptance, capture `git rev-parse HEAD` before the first proof command and verify the same SHA after the last proof command. Do not run acceptance while another coding session, agent or process is committing/resetting the same worktree. A run whose HEAD changes while tests are executing is **not exact-head proof**, even if individual tests pass.

For canonical PowerShell acceptance instructions, wrap the entire acceptance sequence in one fail-fast script block (for example `& { ... }`) and set `$ErrorActionPreference = "Stop"`. Do not print unconditional PASS lines after gates that may throw. In an interactive PowerShell paste, later statements can continue after an earlier thrown statement; any thrown gate means the acceptance run failed regardless of later console output.

### Frontend contract/types/build proof

From `apps/web` under the pinned Node version:

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

The browser suite is product/UX proof for its governed surfaces. It is not a substitute for backend integration, PostgreSQL concurrency, live-provider quality, professional review, or external-action acceptance.

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

## 8. Historical Milestone L live-provider tooling

Milestone L is sealed. Use this tooling only for regression investigation, a deliberately scheduled re-evaluation, or work that explicitly touches the accepted Austria live-provider path. It is not the current work queue.

Use the bounded operator CLI:

```bash
python scripts/evaluate_austria_live_provider.py --check-config
python scripts/evaluate_austria_live_provider.py --tenant-key <tenant> --list-candidates
python scripts/evaluate_austria_live_provider.py --tenant-key <tenant> --root-work-item-id <uuid> --execute-live
```

The CLI:

- masks database URLs in output;
- reports provider/model identity without exposing secrets;
- recognizes the providers supported by current configuration;
- requires a real configured provider credential for live selection;
- applies the accepted live-provider fallback/freshness rules for that sealed path;
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

### CI authority

GitHub Actions provides the accepted exact-head PR proof used by governed slices. Inspect the required workflow names, jobs, and conclusions on the exact candidate SHA rather than assuming a fixed historical proof set.

Self-hosted Woodpecker remains configured as a repository CI path. Active pipeline definitions include `.woodpecker/*.yml`; inspect the current files when a task depends on them.

Neither system's existence is proof. Only an observed completed-success run attached to the exact candidate head may be cited for acceptance.

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

- Use Python 3.12/3.13 and Pydantic v2 patterns where the current codebase does.
- Primary keys are UUIDs unless an existing domain contract explicitly differs.
- Keep canonical organizational meaning in AIOS-owned models/services; vendor or provider state cannot redefine it.
- Keep external provider/model selection non-authorizing.
- Keep material side effects behind the existing governance/authority model.
- Preserve deterministic idempotency/replay semantics.
- Preserve exact provenance and evidence lineage when regulated claims enter a material path.
- Prefer public semantic contracts over cross-module imports of private helpers once the semantic seam is proven.
- Do not introduce a generic framework merely to reduce file size or duplicate a small amount of route-specific code.
- Keep optional AI dependencies isolated unless production necessity requires promotion.
- Frontend uses the accepted Next.js/App Router architecture and project design conventions.
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

Munder Difflin, Plasma, and other donors may supply ideas or bounded mechanics only through an explicit AIOS-owned adoption decision. Do not import donor authority models, canonical state semantics, or visual language automatically.

Do not edit frozen upstream donor snapshots merely to make first-party policy/tests green unless the repository's vendor provenance process explicitly requires a refreshed snapshot.

## 14. Documentation discipline

Documentation drift is a defect. Use the existing owner for each responsibility rather than adding another status or architecture surface:

```text
AGENTS.md                               front door / read path / precedence
agents/AIOS_AGENT_EXECUTION_PLAYBOOK.md engineering process + proof loop
agents/PROJECT_STATE.md                 concise current programme truth
agents/REPOSITORY_AGENT_GUIDE.md        repository mechanics (this file)
docs/ROADMAP.md                         remaining order / rationale
accepted architecture/spec/ADR          durable contract / consequential decision
docs/CHANGELOG.md + acceptance records  historical delivery/proof
agents/SESSION_HANDOFF.md                minimal cold-start recovery pointer
GitHub PR/commit/CI                      live implementation and acceptance evidence
```

Do not duplicate current status into this guide, README files, architecture indexes, or changelog entries. Never rewrite historical acceptance entries to pretend later evidence existed earlier.

When documenting a proof checkpoint, include enough identity to distinguish:

```text
commit/candidate
proof system + run number
what actually executed
what remains unproven
```

## 15. Useful durable references

- `AGENTS.md` — engineering front door and authority/precedence map
- `agents/AIOS_AGENT_EXECUTION_PLAYBOOK.md` — governed execution and exact-head proof process
- `agents/PROJECT_STATE.md` — current programme truth
- `docs/ROADMAP.md` — master necessity-driven orchestration and programme order
- `docs/ARCHITECTURE.md` — architecture map to accepted architecture/specification owners
- `docs/CHANGELOG.md` — dated delivery history
- `docs/TECHNOLOGY_RADAR_V1_3_8.md` — consolidated Technology Radar reference
- `docs/L_LIVE_ORGANIZATION_ACCEPTANCE_OPERATIONS.md` — L external/live acceptance runbook
- `docs/GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md` — combined architecture
- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md` — organization architecture
- `docs/AIOS_FRONTEND_DESIGN_UX_PROGRAMME_V1.md` — frontend/UX programme
- `docs/ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md` — integration boundaries
- `docs/REPOSITORY_POLICY.md` — repository/dependency policy
- `docs/SECURITY_AND_COMPLIANCE.md` — security guidance

## 16. Working rule for agents

The governing loop lives in `agents/AIOS_AGENT_EXECUTION_PLAYBOOK.md`:

```text
Orient → Select → inspect only relevant specs → Build → Test → Review → Record → Commit → Reflect
```

This guide contributes repository mechanics to that loop; it does not define the current task. Before changing implementation, verify the live branch/head and active task from the current-state/scheduler chain, inspect existing implementation before adding abstractions, and record only observed evidence.

Repository truth wins over assumptions, old chat history, stale documentation, or the apparent status of a workflow that did not execute its steps.
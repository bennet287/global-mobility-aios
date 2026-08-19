# Global Mobility AIOS

**Global Mobility AIOS** is a governed global mobility intelligence operating system for the movement of people, talent, families, businesses, and capital across borders.

It combines mobility intelligence, workflow and case orchestration, official-source evidence, document intelligence, organization governance, human review, and controlled AI workers inside one auditable operating environment.

> **This is not a chatbot project.** Global Mobility AIOS is a workflow-first, evidence-backed AI operating system in which AI workers operate through explicit positions, authority boundaries, review gates, durable work records, and human-owned governance.

The canonical product direction is maintained in [`docs/GLOBAL_MOBILITY_AIOS_VISION_V1.md`](docs/GLOBAL_MOBILITY_AIOS_VISION_V1.md). The canonical delivery state and sequencing are maintained in [`docs/ROADMAP.md`](docs/ROADMAP.md), while detailed implementation history and acceptance evidence are recorded in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

---

## 1. What the Project Is Building

Global mobility is usually fragmented across visa research, university search, jobs, documents, relocation, compliance, legal review, tax context, employer workflows, and long-term settlement planning. Global Mobility AIOS treats those activities as one connected lifecycle.

The system is designed to help a person or organization move from a mobility goal to an **evidence-backed, auditable, governed plan and operating workflow** while preserving explicit uncertainty and human authority where required.

The north-star lifecycle is:

```text
Dream / mobility goal
        ↓
Profile, constraints and consent
        ↓
Country + pathway discovery
        ↓
Eligibility, evidence, risk, cost and timeline comparison
        ↓
Study / Work / Family / Business / Investment / Remote-work move
        ↓
Documents, reviews, submissions, appointments and authority decisions
        ↓
Post-arrival / graduate work / employment / business operation
        ↓
Renewal / change of status / family progression
        ↓
Permanent or long-term residence
        ↓
Citizenship / long-term global mobility strategy
```

The product is intentionally broader than any one of the following:

- a study-abroad search site;
- an immigration CRM;
- a visa chatbot;
- a document uploader;
- a recommendation engine;
- a collection of independent AI agents;
- or an autonomous legal, immigration, tax, employment, or investment decision-maker.

The intended category combines:

- workflow CRM and case orchestration;
- regulatory and official-source intelligence;
- country, pathway and opportunity discovery;
- universal mobility profiles and scenario planning;
- document intelligence and evidence control;
- governed automation;
- employer, partner, agency and authority workflows;
- controlled AI workers operating inside explicit organizational authority;
- durable work, blocker, dependency, Contribution and Activity records;
- and an Organization Observatory for understanding how the AI-operated organization is functioning.

---

## 2. Who Global Mobility AIOS Serves

### Mobility users

Students, graduates, professionals, job seekers, remote workers, families, founders, investors, HNWIs, and people planning settlement or citizenship.

Their experience should answer questions such as:

- Where can I realistically move?
- Which pathways fit my profile and goals?
- What is confirmed, uncertain, conditional, missing or blocking?
- Which official evidence supports the answer?
- What documents, costs, risks and deadlines matter?
- What should I do next?
- How does the current move connect to my longer-term study, work, family, business, residence and citizenship strategy?

### Professionals and operators

Mobility advisers, case operators, compliance reviewers, evidence researchers, source reviewers and regulated-domain reviewers.

Their workspaces prioritize:

- cases and work queues;
- evidence and provenance;
- pathway comparison;
- document completeness;
- blockers and dependencies;
- deadlines and authority workflow;
- review state and uncertainty;
- human-required actions;
- and durable audit history.

### Employers and corporate mobility teams

The platform supports employee mobility, sponsor and employer requirements, dependants, work and residence workflows, compliance calendars, case portfolios, relocation operations and cross-jurisdiction workforce mobility.

### Business, investment, HNWI and family-office users

The product direction includes entrepreneurship, startup pathways, business relocation, residence/citizenship-by-investment contexts, HNWI and family-office mobility, tax-residency issue mapping and treaty evidence.

These areas remain strongly evidence- and review-gated. Model output must never be presented as legal, tax or investment certainty.

### Partners, agencies and public-sector workflows

The architecture includes partner APIs, agency operations, appointments, submissions, authority assignments, checklists and government/agency workflow integration where contracts and authorization permit.

A workflow existing in the product does **not** imply authority to submit, approve, certify or make a legally binding decision.

---

## 3. Product Operating Model

Global Mobility AIOS is evolving into a **governed AI-operated organization** with a human Owner acting as the Board.

```text
Human Owner / Board
        ↓
CEO governance layer
        ↓
Executive portfolios
        ↓
Departments and capability positions
        ↓
Governed work / evidence / review / escalation
        ↓
Bounded AIOS execution
```

Agent names, prompts or UI labels never grant authority. Authority comes from deterministic organization contracts, role permissions, backend authorization, evidence state, human review and explicit governance rules.

The accepted organization foundation currently includes:

- **61 active OrganizationPosition identities**;
- **zero duplicate active position keys** after the active-identity reconciliation;
- **9 L3 executive roles** beneath the CEO;
- **26 operational domains**;
- **59 positions downstream of the CEO**;
- capability-only positions that remain non-executable until explicitly authorized;
- preserved Human Board and CEO governance;
- bounded executive delegation rather than title-based authority.

The active-identity contract is enforced at Alembic revision:

```text
0076_organization_position_active_identity
```

---

## 4. Human Experiences

The application is deliberately separated into role-based experiences. Navigation improves usability but **never replaces backend authorization**.

### Global Mobility AIOS Cockpit — Owner / Board

The **Cockpit** is the top-level Owner control surface. It provides organization-wide awareness rather than acting as a task manager.

Current capabilities include:

- live organization state;
- Human Board → CEO → executive → department visibility;
- Owner Attention signals;
- operational domains and executive portfolio focus;
- global mobility intelligence context;
- blocker and dependency visibility;
- overdue work and pending human-action signals;
- evidence-health and Activity-coverage state;
- department drill-down;
- governed human-follow-up intervention;
- and links into deeper control surfaces.

The Cockpit is not allowed to bypass the authority model by directly resolving regulated work simply because the Owner can see it.

### Board Room — executive authority module

**Board Room** is a module inside the Cockpit experience, not the name of the entire Owner product.

It is responsible for genuinely Board-level decisions, control, escalations and reserved authority.

### Department workspaces

Accepted in Phase 13.16.4:

```text
/workspace/[department]
```

A department workspace composes the live operational state of one organizational unit, including:

- executive ownership;
- active organizational positions;
- owned work;
- blockers;
- dependencies;
- pending human requests;
- Contributions;
- material durable Activity;
- and governed intervention through the existing HumanActionRequest contract.

Department workspaces do not directly waive blockers or dependencies, complete/reassign work, publish evidence, make Board decisions or issue final legal conclusions.

### Cross-department friction

Accepted in Phase 13.16.5:

```text
/cross-department-friction
```

This Owner-facing surface identifies friction that crosses organizational boundaries:

- blockers whose owning department differs from the department of the affected work;
- dependencies connecting downstream and upstream work in different departments;
- human-action indicators;
- escalation and overdue signals;
- latest durable Activity where available;
- deep links to affected department workspaces;
- and bounded human-follow-up intervention.

The page is a governed composition surface. It does not directly resolve or waive blockers, satisfy or waive dependencies, complete or reassign work, make Board decisions, publish/certify evidence, issue final legal conclusions or alter organization control.

### Operations — Professional / Operator

The **Operations** shell is the high-information-density workspace for professionals and internal operators. It is intended to converge case operations, evidence, provenance, review, authority workflow and specialist work without exposing Owner-only controls.

### My Mobility — mobility-user experience

**My Mobility** is the user-facing journey surface. Its direction is goal- and case-centric rather than organized around internal database or governance concepts.

It is intended to bring together profile, pathways, eligibility, documents, actions, deadlines, costs, risks, evidence and long-term progression into one understandable mobility journey.

---

## 5. Core Domain Capabilities

The repository contains progressively delivered capabilities across the mobility lifecycle.

### Mobility intelligence

- universal mobility profiles;
- profile-driven eligibility;
- country and pathway catalogues;
- evidence-backed pathway comparison;
- costs, risks and alternatives;
- opportunity discovery;
- mobility timelines and scenarios;
- study, work, family, business, investment and settlement contexts.

### Regulatory and official-source intelligence

- jurisdiction and authority registry;
- official-source onboarding;
- retrieved source snapshots and provenance;
- source certification and independent review;
- verified-rule workflows;
- rule-change and intelligence pipelines;
- country and global intelligence views;
- continuous freshness as an operational programme rather than a one-time import.

Global software capability does **not** mean global evidence coverage is complete. Phase 10B evidence operations remain an ongoing research, review, publication and freshness programme.

### Document intelligence

- secure document metadata and object-storage workflows;
- OCR and structured extraction;
- requirement/checklist handling;
- missing-document detection;
- expiry and lifecycle tracking;
- evidence linkage;
- fraud-risk indicators that require human investigation rather than autonomous accusations.

### Corporate, business and wealth mobility

- corporate employee mobility;
- sponsorship and dependant contexts;
- entrepreneur/startup pathways;
- business relocation;
- investment migration context;
- HNWI/family-office control workflows;
- tax-residency issue mapping and treaty evidence.

### Ecosystem and external workflow

- client portal foundations;
- partner APIs;
- agency workflows;
- appointment tracking;
- submission/checklist operations;
- governed automation;
- communication workflows;
- authority-facing workflow where explicitly permitted.

---

## 6. Durable Organization Model

Phase 13 introduces a durable organization model rather than treating AI work as transient chat sessions.

Important concepts include:

### OrganizationPosition

Represents organizational capacity and reporting structure. A position can exist as capability-only and still have no executable authority.

### OrganizationalWorkItem

Represents durable organizational work with ownership, department, status, due dates and operational context.

### OrganizationBlocker

Represents a material obstacle affecting work. Visibility of a blocker does not imply permission to resolve or waive it.

### OrganizationWorkItemDependency

Represents upstream/downstream work relationships and cross-department dependency chains.

### OrganizationHumanActionRequest

Represents explicit requests for human intervention such as review, information or acknowledgement. The accepted Cockpit, department workspace and cross-department intervention surfaces reuse this governed command rather than inventing direct mutation shortcuts.

### OrganizationContribution

Represents durable material contribution/evidence emitted through accepted contribution contracts.

### OrganizationActivity

Represents semantic organization history.

Historical Activity is intentionally not fabricated from mutable current-state rows. The system uses an explicit immutable Activity coverage epoch so the Observatory can distinguish covered semantic history from earlier partial history.

### Organization Observatory

Composes durable organizational state into human-readable operating intelligence while preserving data quality, evidence coverage and historical limitations.

---

## 7. Truth, Evidence and Safety Model

Global Mobility AIOS is designed for domains in which an attractive answer can still be dangerously wrong.

The core safety rule is:

> **Regulated or consequential claims must be grounded in evidence and the required review state. Model output alone is never authoritative.**

Visa, immigration, legal, scholarship, employment, tax and investment claims must preserve the applicable evidence and governance controls, including as relevant:

- source URL and authority classification;
- jurisdiction;
- effective period;
- retrieved timestamp;
- content hash / snapshot provenance;
- confidence and uncertainty;
- certification/review state;
- missing information and blockers;
- human-review requirements;
- explicit publication state.

The system must not silently convert:

- a model suggestion into a verified rule;
- a draft into a published decision;
- a capability position into an executable agent;
- a visible control into backend authority;
- a pending certification into an approved source;
- or an incomplete evidence set into legal certainty.

Human review remains mandatory wherever the relevant contract requires it.

---

## 8. Current Delivery Status

The current development branch is:

```text
roadmap/global-mobility-aios-v11
```

Current accepted delivery position on this branch:

| Programme | State |
|---|---|
| Phases 1–9 | Complete — core platform, Truth Engine, profiles, pathways, timelines and document intelligence |
| Phase 10 software | Complete — self-updating intelligence foundation, registry workflows, dashboards, ranking and multi-year planning |
| Phase 10B evidence operations | Operationally ongoing — jurisdiction evidence onboarding, independent review, publication and freshness |
| Phase 11 | Complete — corporate, business, wealth, investment, family-office and tax/treaty mobility |
| Phase 12 | Complete / stabilized — portals, partner APIs, governed automation and agency/government workflow foundations |
| Phase 13.0–13.15 | Complete / PASS where gated — AI organization governance, department runtime and external-validation/correctness foundation |
| Phase 13.16.0 | CLOSED / PASS — design and information-architecture foundation |
| Phase 13.16.1 | COMPLETE / PASS — durable Contribution & Activity model and immutable coverage epoch |
| Phase 13.16.2 | COMPLETE / PASS — premium role shells, navigation and preserved-SQLite reconciliation |
| Phase 13.16.3 | COMPLETE / PASS — Unified Owner Control Center |
| Phase 13.16.4 | COMPLETE / PASS — Department workspaces |
| Phase 13.16.5 | COMPLETE / PASS — Cross-department dependencies and blocker view |
| Phase 13.16.6 | COMPLETE / PASS — Owner decision and escalation inbox |
| Phase 13.16.7 | COMPLETE / PASS — Mobility User experience |
| Phase 13.16.8 | COMPLETE / PASS — Professional / Operator workspace |
| Phase 13.16.9 | COMPLETE / PASS — Evidence / provenance presentation |
| **Phase 13.16.10** | **COMPLETE / PASS — integrated responsive/accessibility role experience** |
| **Phase 13.17** | **IN PROGRESS / PAUSED BY EVALUATOR — owner-led human acceptance running in parallel** |
| Phase 14 | NOT STARTED / demand-gated — measured scale after validated product demand |

Phase 13.17 does not globally block Technology Radar or High-Autonomy Organization architecture work. Its findings remain real until corrected, retested, or explicitly dispositioned.

---

## 9. Latest Accepted Quality Baseline

Latest accepted runtime evidence before the documentation-only V1.3 architecture checkpoint includes:

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
```

The accepted preserved `gmai.db` state remains unchanged across the documentation-only architecture update.

These results are carried forward from the accepted runtime checkpoints and are **not represented as rerun by the V1.3 documentation checkpoint**.

No GitHub CI PASS is inferred unless a real status/check is attached to the relevant commit.

---

## 10. Architecture at a Glance

```text
┌──────────────────────────────── Human experiences ────────────────────────────────┐
│ Cockpit / Board Room / Department Workspaces / Cross-department Friction        │
│ Operations / My Mobility / Portal / Partner & specialist surfaces               │
└──────────────────────────────────────┬────────────────────────────────────────────┘
                                       │
                    Authentication + backend authorization
                                       │
┌──────────────────────────── Organization governance ─────────────────────────────┐
│ Board / CEO / executives / positions / delegation / decisions / risk            │
│ WorkItems / Blockers / Dependencies / HumanActionRequests                       │
│ Contributions / semantic Activity / Organization Observatory                    │
└──────────────────────────────────────┬────────────────────────────────────────────┘
                                       │
┌────────────────────────────── Mobility domain layer ──────────────────────────────┐
│ Profiles / eligibility / pathways / opportunities / timelines / documents       │
│ corporate / business / investment / tax-residency / family mobility             │
└──────────────────────────────────────┬────────────────────────────────────────────┘
                                       │
┌──────────────────────────── Evidence & intelligence ──────────────────────────────┐
│ Jurisdictions / authorities / official sources / snapshots / certifications     │
│ verified rules / global intelligence / evidence gaps / provenance               │
└──────────────────────────────────────┬────────────────────────────────────────────┘
                                       │
┌──────────────────────────────── Runtime & data ───────────────────────────────────┐
│ FastAPI / Python / SQLModel / Alembic                                            │
│ PostgreSQL + preserved developer SQLite                                          │
│ Redis / Qdrant / MinIO / n8n and optional model infrastructure                  │
└───────────────────────────────────────────────────────────────────────────────────┘
```

The architecture intentionally avoids introducing heavier infrastructure simply because it is fashionable. Search engines, knowledge-graph infrastructure, durable event streaming, Temporal-class orchestration and Kubernetes remain scale-gated until validated product and operational demand justify them.

---

## 11. Technology Stack

### Web

- Next.js **15.2.4**
- React **19**
- TypeScript
- App Router
- browser OCR through Tesseract.js where applicable

### API

- Python 3.12-class runtime
- FastAPI
- SQLModel / SQLAlchemy ecosystem
- Alembic migrations
- pytest

### Data and local infrastructure

- PostgreSQL for authoritative relational deployment/integration use
- preserved SQLite developer database for local continuity and compatibility testing
- Redis
- Qdrant
- MinIO / S3-compatible object storage
- n8n for bounded business automation

### AI direction

- provider-independent hosted or local models;
- structured agent contracts;
- stateful workflow orchestration;
- provenance-aware retrieval;
- explicit uncertainty;
- deterministic authority outside model prompts.

---

## 12. Repository Layout

```text
global-mobility-aios/
├── apps/
│   ├── api/                  # FastAPI API, domain models, services, migrations, tests
│   └── web/                  # Next.js role-based product experiences
├── agents/                   # AI role cards and controlled worker definitions
├── workflows/                # Workflow/orchestration assets
├── knowledge/                # Knowledge and official-source assets
├── infrastructure/           # Deployment, monitoring and environment infrastructure
├── docs/                     # Vision, roadmap, governance, architecture and feature contracts
├── scripts/                  # Repository, migration, audit and local acceptance helpers
├── docker-compose.yml
├── alembic.ini
└── .env.example
```

---

## 13. Quick Start

### Option A — Docker-oriented local environment

Create the Docker environment file from the example:

**PowerShell**

```powershell
Copy-Item .env.example .env.docker
```

**Bash**

```bash
cp .env.example .env.docker
```

Then start the configured stack:

```bash
docker compose up --build
```

Compose uses `.env.docker` so Docker-only hostnames do not accidentally leak into normal host-side Python commands.

Common local endpoints:

```text
API health       http://localhost:8000/health
API docs         http://localhost:8000/docs
Web              http://localhost:3000
n8n              http://localhost:5678
MinIO console    http://localhost:9001
Qdrant dashboard http://localhost:6333/dashboard
```

### Option B — host-side API + web development

The project is commonly developed with a repository-local Python virtual environment.

Example Windows/PowerShell flow:

```powershell
cd D:\global-mobility-aios

# Activate an existing repository venv
& .\.venv\Scripts\Activate.ps1

# API
cd .\apps\api
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd D:\global-mobility-aios\apps\web
npm install
npm run dev
```

The API container uses the equivalent production-style command:

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 14. Development and Acceptance Commands

### API regression

From the repository root with the correct virtual environment:

```powershell
& .\.venv\Scripts\python.exe -m pytest apps/api/tests -q
```

### Frontend design foundation

```powershell
cd .\apps\web
npm run test:design-foundation
```

### Organization read-client regression

```powershell
node --experimental-strip-types --test lib/organization-read-client.test.mjs
```

### Production web build

```powershell
npm run build
```

### Repository policy

From the repository root:

```powershell
& .\.venv\Scripts\python.exe scripts/check_repo_policy.py --root .
```

### Release consistency

```powershell
& .\.venv\Scripts\python.exe scripts/check_release_consistency.py
```

### Database migration consistency

```powershell
& .\.venv\Scripts\python.exe scripts/check_database_migrations.py
```

### Local DB schema parity

```powershell
& .\.venv\Scripts\python.exe scripts/check_local_db_schema.py `
  --database-url "sqlite:///D:/global-mobility-aios/gmai.db"
```

### Git whitespace guard

```bash
git diff --check
```

Acceptance should be evidence-driven. A green UI screenshot does not replace API, repository, migration, schema and authorization checks; conversely, unit tests do not replace runtime and browser acceptance for role-based experience slices.

---

## 15. Preserved Database Guardrails

This repository deliberately preserves important developer and integration databases rather than treating every test problem as a reason to reset state.

Current local development guardrails include:

- the developer SQLite database is preserved and migration-aware;
- schema repair must be forward, bounded and data-preserving;
- the accepted developer SQLite revision is `0076_organization_position_active_identity`;
- the repository currently registers **118 application/model tables**;
- `alembic_version` is migration infrastructure, not application-schema drift;
- preserved PostgreSQL environments must not be migrated casually just to make a local acceptance run convenient;
- isolated PostgreSQL environments should be used for bounded migration/transaction contracts when required;
- test data must not be fabricated in preserved environments merely to make a UI look populated.

---

## 16. Repository Governance

Dependency and repository usage is controlled through the project allowlist policy.

Key references:

- [`docs/REPOSITORY_POLICY.md`](docs/REPOSITORY_POLICY.md)
- [`docs/ADR/0001-approved-repository-strategy.md`](docs/ADR/0001-approved-repository-strategy.md)
- `.github/workflows/repo-policy-check.yml`
- `scripts/check_repo_policy.py`

Important contribution principles:

1. Preserve backend authorization as the source of authority.
2. Do not introduce direct mutation shortcuts merely for UI convenience.
3. Keep regulated claims evidence-backed and review-gated.
4. Keep Activity semantic; do not fabricate historical events from mutable state.
5. Preserve database history unless a reviewed migration/reconciliation explicitly changes it.
6. Update roadmap/changelog documentation when delivery state materially changes.
7. Run the bounded quality gates appropriate to the slice before committing.
8. Prefer incremental, auditable changes over broad rewrites.

---

## 17. Key Documentation

Start here:

- **Product vision:** [`docs/GLOBAL_MOBILITY_AIOS_VISION_V1.md`](docs/GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- **Canonical roadmap:** [`docs/ROADMAP.md`](docs/ROADMAP.md)
- **Implementation history:** [`docs/CHANGELOG.md`](docs/CHANGELOG.md)
- **AI organization governance:** [`docs/AI_ORGANIZATION_GOVERNANCE_V13_0.md`](docs/AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- **High-autonomy organization architecture:** [`docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`](docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md)
- **Repository policy:** [`docs/REPOSITORY_POLICY.md`](docs/REPOSITORY_POLICY.md)
- **Universal Mobility Profile:** [`docs/UNIVERSAL_MOBILITY_PROFILE_V8_0.md`](docs/UNIVERSAL_MOBILITY_PROFILE_V8_0.md)
- **Versioned pathway catalogue:** [`docs/VERSIONED_PATHWAY_CATALOGUE_V8_1.md`](docs/VERSIONED_PATHWAY_CATALOGUE_V8_1.md)
- **Pathway comparison explanations:** [`docs/PATHWAY_COMPARISON_EXPLANATIONS_V8_2.md`](docs/PATHWAY_COMPARISON_EXPLANATIONS_V8_2.md)
- **Signed document access/object storage:** [`docs/SIGNED_DOCUMENT_ACCESS_OBJECT_STORAGE_V9_5.md`](docs/SIGNED_DOCUMENT_ACCESS_OBJECT_STORAGE_V9_5.md)
- **Global intelligence filters:** [`docs/GLOBAL_INTELLIGENCE_FILTERS_V10_11.md`](docs/GLOBAL_INTELLIGENCE_FILTERS_V10_11.md)

Feature-specific contracts under `docs/` remain the authoritative place for detailed behavioral requirements that are too specific for this README.

---

## 18. Current Direction

The project is moving through a deliberate sequence:

```text
Trusted data + governed workflows
        ↓
Evidence-backed mobility intelligence
        ↓
Controlled ecosystem operations
        ↓
Governed AI-operated organization
        ↓
Clear role-based human experiences
        ↓
Owner decisions and escalations
        ↓
Mobility User + Professional experiences
        ↓
Evidence/provenance consolidation
        ↓
Integrated responsive/accessibility acceptance
        ↓
Genuine external-human validation
        ↓
Measured global scale
```

The accepted product baseline is **Phase 13.16.10 — COMPLETE / PASS**. Phase 13.17 owner-led human acceptance remains **IN PROGRESS / PAUSED BY EVALUATOR** and continues as a parallel feedback stream rather than a global stop gate.

The active organization direction is **V1.3 — High-Autonomy Organization + Organizational Immune System + Earned Autonomy + Board Transparency & Decision Lineage**.

Global Mobility AIOS should become more capable over time without becoming less governed or less transparent. AI employees may hold real capability-specific delegated authority and should complete most healthy work autonomously. Quality comes from Evidence, deterministic material-state validation, risk-tiered verification, authority/policy controls, concurrency protection, anomaly detection, circuit breakers, bounded blast radius, consequence-aware recovery, and labeled learning.

The Human Owner / Board remains supreme authority but operates primarily by exception. The Board must have on-demand visibility into material decisions, agent collaboration, Evidence, rules, tool actions, incidents, autonomy changes, and decision lineage without being forced to approve routine work.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the detailed coordinated Product / Technology Radar / High-Autonomy Organization delivery programme.

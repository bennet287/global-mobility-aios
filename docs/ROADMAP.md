# Global Mobility AIOS — Product & Delivery Roadmap

This document is the canonical **strategic and delivery roadmap** for
[Global Mobility AIOS](GLOBAL_MOBILITY_AIOS_VISION_V1.md).

It is intentionally more than a release-status table. It explains:

1. **what Global Mobility AIOS is and why it exists;**
2. **who it serves and what end-to-end mobility journeys it is intended to support;**
3. **how the product, data, regulatory-intelligence, workflow, document, and AI-organization layers fit together;**
4. **what has already been delivered;**
5. **what is active now;**
6. **what is locked, operationally ongoing, or planned next;**
7. **which safety, evidence, acceptance, and governance gates control progression.**

The roadmap is not the chronological release log. Detailed test outputs, commit-by-commit
acceptance evidence, repair notes, and historical implementation narratives belong in
[CHANGELOG.md](CHANGELOG.md). Feature contracts and detailed architecture decisions belong
in the versioned specifications under `docs/`. Exact implementation history belongs in Git
and Alembic migrations.

---

## 1. Project Definition

### 1.1 What Global Mobility AIOS is

Global Mobility AIOS is a **global mobility intelligence operating system** for the movement
of people, talent, families, businesses, and capital across borders.

It is not intended to be only:

- a study-abroad search site;
- an immigration CRM;
- a visa chatbot;
- a document uploader;
- a collection of disconnected AI assistants;
- or an autonomous legal/immigration decision-maker.

The intended product category combines:

- workflow CRM and case orchestration;
- regulatory and official-source intelligence;
- opportunity and pathway discovery;
- profile-based eligibility and planning;
- document intelligence and evidence control;
- governed automation;
- partner, employer, agency, and operator workflows;
- controlled AI workers operating inside explicit authority boundaries;
- an Organization Observatory for understanding work, decisions, blockers, outcomes, and
  human attention across the AI-operated organization.

The system is designed to help a user or organization move from a mobility goal to an
**evidence-backed, auditable, governed plan and operating workflow** without pretending that
AI output replaces official authorities, qualified professional review, or human approval
where those are required.

### 1.2 Mission

The product mission is to make global mobility **understandable, evidence-backed,
operationally manageable, and progressively automatable** across the full lifecycle rather
than treating each visa, university, job, relocation, investment, or settlement step as an
isolated transaction.

The long-term product should answer, with explicit evidence and uncertainty:

- Where can this person, family, employee, founder, or investor realistically move?
- Which pathways fit their profile and goals?
- What is known, unknown, conditional, or blocking?
- Which official sources support the conclusion?
- What documents, costs, deadlines, decisions, and dependencies exist?
- What should happen next, who is authorized to do it, and which actions require human review?
- How does the current move fit into the user's longer-term study, work, settlement, business,
  wealth, family, and citizenship strategy?

### 1.3 North-star mobility lifecycle

Global Mobility AIOS is designed around a long-lived mobility relationship rather than a
single application event.

```text
Dream / Goal
   ↓
Profile and constraints
   ↓
Country + pathway discovery
   ↓
Eligibility, evidence, risk, cost and timeline comparison
   ↓
Study / Work / Family / Business / Investment / Remote-work move
   ↓
Documents, submissions, appointments, authority decisions and compliance
   ↓
Post-arrival / graduate work / employment / business operation
   ↓
Renewal / change of status / family progression
   ↓
Permanent residence / long-term residence
   ↓
Citizenship / global mobility strategy
```

The original product vision expresses the individual lifecycle succinctly as:

```text
Dream
  -> Study abroad
  -> Graduate work rights
  -> Skilled migration
  -> Entrepreneurship
  -> Investment migration
  -> Permanent residence
  -> Citizenship
  -> Global citizen
```

Not every user follows every step. The system must support branching, alternative pathways,
failed assumptions, changed goals, changing laws, and different user types without forcing a
single scripted funnel.

---

## 2. Who the Platform Serves

The canonical product vision includes multiple actor types. They share core truth, profile,
evidence, workflow, and audit infrastructure but require different experiences and authority
levels.

### 2.1 Mobility users

Examples:

- students;
- graduates;
- skilled professionals;
- job seekers;
- remote workers and digital nomads;
- families and dependants;
- founders and entrepreneurs;
- investors and HNWIs;
- people planning settlement, permanent residence, or citizenship.

Their experience should be **goal- and case-centric**, not organized around backend tables or
internal governance machinery.

They need:

- a universal mobility profile;
- understandable country/pathway comparison;
- evidence-backed eligibility and confidence;
- explicit blockers and missing information;
- cost and timeline planning;
- document requirements and status;
- actions and deadlines;
- authority/submission progress where available;
- long-term mobility scenarios rather than only the next application.

### 2.2 Professionals and operators

Examples:

- mobility advisers;
- case operators;
- compliance reviewers;
- source reviewers;
- evidence researchers;
- internal specialists;
- regulated-domain reviewers where applicable.

Their workspace should prioritize:

- cases and work queues;
- comparative pathway reasoning;
- evidence and provenance;
- document completeness;
- validation findings;
- deadlines and dependencies;
- authority workflow;
- auditability;
- explicit uncertainty and escalation.

### 2.3 Employers and corporate mobility teams

The platform is intended to support:

- employee moves;
- sponsor/employer requirements;
- dependants;
- work-permit and residence workflows;
- compliance calendars;
- case portfolios;
- corporate mobility strategy;
- workforce and talent movement across jurisdictions.

### 2.4 Business, investment, HNWI and family-office users

The platform also supports mobility questions involving:

- entrepreneurship and startup programmes;
- business relocation;
- residence-by-investment and citizenship-by-investment contexts;
- HNWI/family-office mobility;
- tax-residency issue mapping;
- treaty evidence and double-taxation context;
- multi-jurisdiction family and capital planning.

These areas remain heavily evidence- and review-gated. The platform must not turn model output
into legal, tax, or investment certainty.

### 2.5 Partners, agencies and governments

The product direction includes:

- partner APIs;
- agency workflow;
- appointment and submission tracking;
- authority assignments/checklists;
- government/agency-facing operational integration where contracts and authorization permit.

The existence of a workflow does not imply submission authority. External action remains
separately gated.

### 2.6 Human Owner / Board

Phase 13 introduces a distinct organizational actor: the **Human Owner / Board** overseeing the
AI-operated organization itself.

The Board is not a normal case operator. It requires visibility into:

- organizational health;
- material decisions;
- high-risk exceptions;
- blockers;
- cross-department dependencies;
- meaningful outcomes and Contributions;
- human review queues;
- validation quality;
- emergency controls;
- AI runtime governance.

---

## 3. Product Thesis and Differentiation

Global Mobility AIOS is built around several propositions that should remain true as the
product evolves.

### 3.1 Workflow-first, not chatbot-first

AI assistance is embedded inside durable workflows. Important state lives in typed records,
not only in conversations.

The system must preserve:

- cases;
- profiles;
- pathways;
- rules;
- evidence;
- documents;
- work items;
- decisions;
- blockers;
- human requests/actions;
- audits;
- contributions;
- curated semantic Activity.

### 3.2 Evidence before regulated certainty

For visa, immigration, scholarship, employment, tax, investment, or other regulated claims:

- official-source provenance matters;
- jurisdiction and effective-date semantics matter;
- source review state matters;
- model confidence is not authority;
- pending evidence cannot be presented as verified law;
- RAG retrieval is not authoritative by itself;
- publication must remain an explicit governed transition.

### 3.3 One mobility profile, many journeys

The platform should extend a shared profile and case model instead of creating isolated mini
products for study, work, business, family, or investment mobility.

The universal profile can include:

- nationality and residence context;
- education and qualifications;
- work experience and skills;
- languages;
- finances and budget;
- family/dependants;
- desired jurisdictions;
- mobility goals;
- constraints;
- risk tolerance;
- consent and data permissions.

### 3.4 Plans must expose uncertainty

A useful mobility answer is not merely “eligible” or “not eligible.” The platform should
separate:

- verified facts;
- assumptions;
- pending reviews;
- unknowns;
- unresolved qualification mappings;
- evidence gaps;
- hard blockers;
- soft risks;
- alternatives;
- human-review requirements.

### 3.5 AI workers are governed workers

Agents are not granted power by their names, prompts, or model capabilities. Authority comes
from deterministic position contracts, role boundaries, risk classification, transaction
controls, and human/Board gates.

---

## 4. Strategic Capability Pillars

The project has grown through phases, but the capabilities fit into a smaller set of enduring
product pillars.

### 4.1 Identity, profile, CRM and case foundation

Purpose: maintain the durable human/business context required by all later intelligence.

Core capabilities include:

- lead/client intake;
- authenticated return journeys;
- CRM state;
- mobility profile;
- case intent and target jurisdictions;
- notes, tasks and workflow state;
- tenant-aware permissions;
- consent/audit foundations.

### 4.2 Truth Engine and regulatory intelligence

Purpose: establish a source-controlled representation of immigration and mobility rules.

Capabilities include:

- jurisdiction and authority registry;
- official-source onboarding;
- immutable source snapshots and hashes;
- source certification and independent review;
- structured extraction;
- regulatory change detection;
- verified rules;
- provenance and supersession;
- effective dates;
- source freshness;
- global coverage readiness.

### 4.3 Pathway, opportunity and mobility-planning intelligence

Purpose: connect a profile to plausible mobility routes and explain trade-offs.

Capabilities include:

- country/pathway catalogue;
- study, work, visa, scholarship and settlement contexts;
- business/investment/remote-work contexts;
- eligibility and conditionality;
- ranking and comparison;
- cost, risk and evidence planning;
- operational timelines;
- multi-year mobility scenarios;
- opportunity and country intelligence.

### 4.4 Document and evidence intelligence

Purpose: turn user/organization documents into governed evidence instead of opaque uploads.

Capabilities include:

- secure document upload;
- OCR and structured extraction;
- document-type metadata;
- validation and integrity findings;
- missing-document detection;
- expiry monitoring and reminders;
- controlled access grants;
- fraud-risk indicators requiring human investigation rather than autonomous accusation.

### 4.5 Workflow, automation and ecosystem operations

Purpose: move from intelligence to controlled execution.

Capabilities include:

- task/workflow orchestration;
- client and operator portals;
- partner APIs;
- communication drafting/review;
- governed automation;
- appointment tracking;
- agency submissions;
- authority decisions;
- checklists;
- reminders;
- human action gates.

### 4.6 Corporate, business and wealth mobility

Purpose: support mobility that cannot be represented as an individual visa search alone.

Capabilities include:

- corporate employee mobility;
- entrepreneurship/startup planning;
- business relocation;
- HNWI/family-office cases;
- investment migration context;
- tax-residency issue maps;
- treaty evidence;
- multi-party and multi-jurisdiction workflows.

### 4.7 AI-operated organization governance

Purpose: allow AI agents to perform bounded organizational work without becoming ungoverned
authorities.

Capabilities include:

- organization registry;
- position contracts;
- Board/CEO/executive hierarchy;
- authority levels;
- work items and dependencies;
- executive decisions;
- blockers;
- human action requests;
- emergency/pause controls;
- department runtimes;
- audit and attribution;
- Contributions and semantic Activity.

### 4.8 Organization Observatory and role-based experience

Purpose: turn the underlying governed organization into a product experience that humans can
understand and operate.

Capabilities include:

- organization health and work overview;
- department views;
- blocker/dependency visibility;
- decision and escalation inboxes;
- meaningful outcome/Contribution views;
- curated semantic Activity timelines;
- mobility-user experience;
- professional/operator experience;
- evidence/provenance UX;
- responsive/accessibility acceptance.

### 4.9 Scale, search, graph and production operations

Purpose: add heavier infrastructure only when product usage and operational constraints justify
it.

Potential capabilities include:

- dedicated search infrastructure;
- vector/semantic stores;
- knowledge graphs;
- event streaming;
- durable long-running orchestration;
- full observability/SLO stack;
- Kubernetes and multi-cloud/on-premise deployment profiles.

These are scale-gated rather than mandatory architectural fashion choices.

---

## 5. Target Product Surfaces

The long-term system is multi-surface but shares one governed data and intelligence model.

### 5.1 Mobility User experience

Should answer:

- What are my realistic options?
- Why are they suitable or unsuitable?
- What evidence supports the answer?
- What is missing?
- What should I do next?
- What will it cost and how long might it take?
- What does this mean for my longer-term mobility plan?

The experience should hide internal AI/governance complexity unless it materially affects the
user.

### 5.2 Professional / Operator workspace

Should make complex case work faster without hiding provenance or uncertainty.

Primary concepts:

- cases;
- pathway comparisons;
- evidence;
- documents;
- validation;
- authority workflow;
- deadlines;
- findings;
- review queues;
- timeline and provenance.

### 5.3 Owner / Board Control Center

Should show the AI-operated organization as an accountable operating system rather than a feed
of agent messages.

Primary concepts:

- health;
- work;
- Contributions;
- material Activity;
- decisions;
- blockers;
- departments;
- dependencies;
- validations;
- human attention;
- emergency controls.

### 5.4 Employer / Partner / Agency surfaces

These should expose only the records and actions appropriate to their authorization boundary.
Partner or agency access must not weaken tenant isolation, evidence review, submission authority,
or audit.

### 5.5 APIs and integrations

Public/partner APIs, email, calendar, CRM, messaging, and future automation channels must remain
policy-controlled extensions of the same backend contracts rather than side doors around them.

---

## 6. AI Organization Operating Model

Global Mobility AIOS is being built as an **AI-operated global mobility organization**, not a
conventional application with several disconnected AI assistants.

```text
Human Owner / Board
  -> CEO Agent
      -> CTO Agent: technology and engineering
      -> COO Agent: operations, sales, and business intelligence
      -> CISO Agent: security, threat intelligence, and resilience
      -> CMO Agent: marketing and product marketing
      -> CPO Agent: product, design, and product management
      -> CFO Agent: finance, accounts, M&A, and investor relations
      -> CCO Agent: communications, PR, and government relations
      -> CHRO Agent: people, culture, and recruitment
      -> CLO Agent: legal, public policy, and compliance
```

The target operating model is defined in
[AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md).

### 6.1 Authority model

The system must preserve these principles:

- explicit authority rather than prompt-claimed authority;
- deterministic risk/authority classification;
- bounded delegation;
- routine work handled at the lowest authorized level;
- Board attention reserved for material risk, emergencies, overrides, and reserved decisions;
- human gates for external, legal, financial, contractual, regulated, or production actions
  where required;
- reversible execution where possible;
- global pause and per-agent suspension;
- complete attribution and audit evidence.

### 6.2 Organization records are not interchangeable

The Phase 13 organization model intentionally distinguishes:

- **WorkItem** — work to be performed;
- **Dependency** — work-to-work dependency;
- **Blocker** — an impediment requiring resolution;
- **ExecutiveDecision** — a governed decision record;
- **HumanActionRequest** — a request for required human action;
- **HumanAction** — immutable record of the human action itself;
- **Contribution** — outcome-oriented organizational value/result;
- **OrganizationActivity** — curated semantic material-transition history;
- **AuditLog / runtime telemetry** — lower-level evidence and operational trace.

Activity volume is never a proxy for productivity. Runtime chatter, leases, retries, tool calls,
or heartbeats must not be inflated into organizational outcomes.

---

## 7. Logical Architecture Direction

The product remains workflow-first and agent-assisted.

```text
Web / Mobile / Partner Portal / APIs
                |
Identity, consent, API gateway, RBAC and ABAC
                |
Workflow orchestration and controlled agent routing
                |
Mobility domain services and human review queues
                |
Truth Engine / regulatory intelligence / documents / opportunities
                |
Transactional store / search / vectors / knowledge graph / object storage
                |
Audit, telemetry, security monitoring and analytics
```

Current implementation direction includes Next.js/React/TypeScript on the web and
FastAPI/Python/SQLModel/PostgreSQL/Alembic with Redis/Celery-class workflow support. Future
search, vector, graph, streaming, orchestration, observability, and deployment technologies are
added only when validated requirements justify them.

### 7.1 Data and truth hierarchy

For regulated conclusions, the hierarchy is conceptually:

```text
Official source
   ↓
Immutable retrieved snapshot + provenance
   ↓
Structured extraction / classification
   ↓
Independent review / certification where required
   ↓
Verified rule / published pathway evidence
   ↓
Eligibility / comparison / recommendation logic
   ↓
Human-appropriate explanation and workflow
```

Model output cannot directly rewrite the verified truth layer.

### 7.2 Transaction and audit direction

Material transitions should preserve:

```text
source state change
+ audit/provenance
+ curated semantic Activity / Contribution where applicable
= one authoritative transaction boundary
```

No semantic Activity or Contribution should survive if its source material transition rolls
back.

---

## 8. Current State Dashboard

**As of:** 2026-08-15
**Development branch:** `roadmap/global-mobility-aios-v11`
**Accepted 13.16.1 / E3D implementation baseline:** `a503fe8b8a41cff6908751ba24688ed03fa535ec`

<!-- CURRENT_MIGRATION_HEAD: 0074_durable_contribution_activity_model -->

**Code migration head:** `0074_durable_contribution_activity_model`

| Area | State | Current position |
|---|---|---|
| Phases 1-9 | **Complete** | Core platform, Truth Engine, profiles, pathways, timelines, and document intelligence delivered |
| Phase 10 software | **Complete** | Self-updating intelligence, registry workflow, dashboards, ranking, and multi-year timelines delivered |
| Phase 10B evidence operations | **Operationally ongoing** | Jurisdiction evidence onboarding, independent review, publication, and freshness maintenance continue |
| Phase 11 | **Complete** | Corporate, business, wealth, investment, family-office, and tax/treaty mobility delivered |
| Phase 12 | **Complete / stabilized** | Portals, partner APIs, governed automation, government/agency workflows, and stabilization gates delivered |
| Phase 13.0-13.15 | **Complete / PASS where gated** | AI organization governance, bounded department runtimes, external-validation infrastructure, and Round 6 correctness PASS |
| Phase 13.16.0 | **CLOSED / PASS** | Design system and information architecture foundation accepted |
| Phase 13.16.1 | **COMPLETE / PASS** | Durable Contribution & Activity model, legacy writer reconciliation, explicit immutable coverage epoch, and Observatory activation accepted |
| Phase 13.16.2 | **UNLOCKED / NOT STARTED** | Role-based application shells and navigation is the next implementation slice |
| Phase 13.16.3-13.16.10 | **LOCKED** | Later experience slices remain gated by accepted delivery of their immediate predecessors |
| Phase 13.17 | **LOCKED** | Genuine external-human acceptance waits for 13.16.10 |
| Phase 14 | **NOT STARTED** | Scale work waits for Phase 13 acceptance and measured demand |

### 8.1 Current quality evidence

Accepted before E3D:

- Complete API baseline after E3C: **787 passed, 4 expected PostgreSQL-only skips, 0 failed**.
- Combined organization/E3B/E3C regression after E3C: **160 passed, 4 expected skips, 0 failed**.
- Isolated PostgreSQL E3B/E3C Activity transaction contracts: **4/4 passed**.
- PostgreSQL Activity rows remained **0/0 before and after** the bounded transaction tests.
- Repository policy: **PASS**.
- Release consistency: **PASS** at Alembic `0074_durable_contribution_activity_model`.
- Migration consistency: **PASS**, **118 registered tables**.
- Next.js production build: **PASS** on the accepted baseline.

E3D / 13.16.1 closure evidence:

- Focused Activity coverage-epoch suite: **3 passed, 1 expected PostgreSQL-only skip, 0 failed**.
- Broader Observatory/organization regression: **65 passed, 5 expected skips, 0 failed**.
- Roadmap compatibility contract after the strategic restructure: **1 passed, 0 failed**.
- Complete API suite after the compatibility correction: **790 passed, 5 expected PostgreSQL-only skips, 0 failed**.
- Repository policy, release consistency, migration consistency, and `git diff --check`: **PASS**.
- Migration consistency remained at Alembic `0074_durable_contribution_activity_model` with **118 registered tables**.
- Isolated PostgreSQL E2/E3B/E3C/E3D transaction contracts: **5/5 passed**.
- `organization_activity_streams = 0` and `organization_activities = 0` both before and after the PostgreSQL acceptance run.
- PostgreSQL Alembic remained `0074_durable_contribution_activity_model`, and the isolated test container returned to stopped state.
- The preserved authoritative `gmai-postgres` integration database remains outside this acceptance flow at 0073.

**13.16.1E3D is COMPLETE / PASS. Phase 13.16.1 is COMPLETE / PASS. Phase 13.16.2 is UNLOCKED / NOT STARTED.**

### 8.2 Preserved database boundaries

- The preserved authoritative integration PostgreSQL environment remains intentionally at
  `0073_austria_candidate_integrity` and must not be migrated casually.
- The isolated Phase 13.16.1 PostgreSQL service is the bounded 0074 transaction-test
  environment.
- Developer SQLite is preserved and must not be reset merely to make a test convenient.

---

## 9. Direction From Here

The project is now moving through four deliberate horizons.

### Horizon A — trustworthy organizational history — COMPLETE / PASS

Phase 13.16.1E3D established the explicit immutable Activity coverage-epoch contract and closed
the internal Contribution/Activity foundation. The Organization Observatory can now distinguish
pre-epoch partial history from post-epoch covered semantic history without reconstructing older
WorkItem or ExecutiveDecision state.

`activity_history_established` remains tenant-state dependent: it is false before the governed
coverage marker exists and true from that immutable marker forward.

### Horizon B — turn the backend foundation into coherent role-based experiences

With 13.16.1 accepted, Phase 13.16.2-13.16.10 now builds the experience layer for:

- Human Owner / Board;
- departments and AI organization operators;
- mobility users;
- professional/operators;
- cross-department work and blockers;
- decisions and escalations;
- evidence/provenance;
- responsive and accessible critical journeys.

This is the point where much of the already-delivered backend capability should become a more
coherent product rather than a collection of deep functional routes.

### Horizon C — genuine external-human acceptance

Phase 13.17 requires distinct real external-human perspectives:

- a mobility user;
- an independent professional/operator.

Internal simulations, shadow reviews, and model-generated evaluations do not substitute for
this gate.

### Horizon D — scale only after validated demand

Phase 14 may add heavier infrastructure, broader global coverage, search/graph systems,
streaming, durable orchestration, observability, and deployment scale only after Phase 13
acceptance and measured operational need.

The strategic direction is therefore:

```text
Trusted data + governed workflows
        ↓
Evidence-backed mobility intelligence
        ↓
Controlled execution and ecosystem operations
        ↓
Governed AI-operated organization
        ↓
Clear role-based human experiences
        ↓
External-human validation
        ↓
Measured global scale
```

---

## 10. Active Execution Lane

Work proceeds in this order. A later programme must not hide an earlier red release gate.

| Order | Programme | State | Unlock condition |
|---|---|---|---|
| 1 | Phase 10B evidence operations | **ONGOING** | Continue independent jurisdiction review without claiming global completeness |
| 2 | 13.15 Round 6 correctness | **COMPLETE / PASS** | Closed |
| 3 | 13.16.0 design/IA foundation | **CLOSED / PASS** | Closed |
| 4 | 13.16.1 durable Contribution & Activity model | **COMPLETE / PASS** | Closed after E3D coverage-epoch acceptance |
| 5 | 13.16.2 role-based application shells and navigation | **UNLOCKED / NOT STARTED** | 13.16.1 COMPLETE / PASS |
| 6 | 13.16.3-13.16.9 role-based experience delivery | **LOCKED** | Deliver slices sequentially beginning with 13.16.2 |
| 7 | 13.16.10 integrated responsive/accessibility acceptance | **LOCKED** | 13.16.2-13.16.9 delivered |
| 8 | 13.17 genuine external-human acceptance | **LOCKED** | 13.16.10 PASS |
| 9 | Phase 14 scale work | **LOCKED** | Phase 13 PASS + measured demand |

### 10.1 Closed foundation slice — 13.16.1E3D

**Goal:** establish one explicit, immutable, tenant-scoped semantic Activity coverage epoch
using the existing Activity ledger.

Required behavior:

- append one canonical operational Activity marker:
  `organization.activity_coverage.established.v1`;
- allow activation only through an explicit authenticated **admin/internal-human** command;
- make activation idempotent: the first immutable epoch remains authoritative;
- treat the marker `occurred_at` as the semantic-history coverage start;
- expose the coverage start in Observatory summary and department coverage metadata;
- return `activity_history_established = true` only when the canonical marker exists;
- label the basis `explicit_activity_coverage_epoch` after activation;
- keep all pre-epoch history explicitly partial;
- never reconstruct WorkItem or ExecutiveDecision history from `updated_at`, AuditLog,
  attempts, current state, or other mutable projections;
- never emit a Contribution from coverage activation;
- prevent the generic Activity API from forging the reserved epoch marker;
- keep historical throughput/cycle-time metrics unavailable unless future metric logic
  explicitly bounds its period to the coverage epoch or later.

E3D does **not** add a migration, backfill historical rows, modify Austria state, approve a
certification, or publish a pathway. Its accepted closure unlocks only Phase 13.16.2; later
experience slices remain sequentially gated.

### 10.2 E3D acceptance gates

- [x] Focused Activity-coverage-epoch tests pass on SQLite/default test runtime:
  **3 passed, 1 expected PostgreSQL-only skip, 0 failed**.
- [x] Generic Activity marker-forgery regression passes in the focused suite.
- [x] Observatory pre/post activation coverage semantics pass in the focused suite.
- [x] Focused coverage confirms no pre-epoch WorkItem/Decision backfill is produced.
- [x] Focused coverage confirms activation creates no Contribution.
- [x] Broader Observatory/organization regression remains green:
  **65 passed, 5 expected skips, 0 failed**.
- [x] Roadmap compatibility contract remains green after the detailed restructure:
  **1 passed, 0 failed**.
- [x] Complete API suite remains green after the compatibility correction:
  **790 passed, 5 expected PostgreSQL-only skips, 0 failed**.
- [x] Repository policy, release consistency, migration consistency, and `git diff --check` pass after the final documentation correction.
- [x] Isolated PostgreSQL 0074 E2/E3B/E3C/E3D transaction contracts pass: **5 passed, 0 failed**.
- [x] PostgreSQL Activity residue remains zero after the bounded outer rollback tests: **0/0 before and 0/0 after**.
- [x] Alembic remains `0074_durable_contribution_activity_model` with **118 registered tables**.
- [x] `gmai-postgres` remains outside the bounded E3D acceptance path at preserved integration head 0073.

**E3D is COMPLETE / PASS. 13.16.1 is COMPLETE / PASS. 13.16.2 is UNLOCKED / NOT STARTED.**

### 10.3 Next active slice — 13.16.2 role-based application shells and navigation

**Goal:** turn the accepted backend governance/Observatory foundation into coherent role-based
entry points without weakening server-side authorization or breaking deep operational routes.

The first experience-layer slice should establish:

- an **Owner / Board shell** centered on organizational health, work, decisions, blockers,
  evidence, validation, governance, and settings;
- a **Mobility User shell** centered on the person's case, pathway, documents, timeline,
  tasks, communications, and next actions rather than internal governance machinery;
- a **Professional / Operator shell** centered on cases, comparison, evidence, validation,
  authority workflow, provenance, and operational queues;
- stable navigation primitives and role-aware information architecture that reuse the accepted
  13.16.0 design-system foundation;
- preserved deep links during incremental migration so existing operational pages do not become
  unreachable;
- explicit separation between **navigation visibility** and **backend authorization**; hidden
  links must never be treated as a security control;
- no expansion of Austria legal certainty, publication state, certification status, or external
  authority merely because a new shell exposes existing data more clearly.

13.16.2 should remain a bounded experience-foundation slice. It does not yet deliver the full
Owner Control Center, department workspaces, blocker/dependency experience, user/operator
journeys, or integrated accessibility acceptance; those remain the sequential 13.16.3-13.16.10
programme.

**13.16.2 exit direction:** role-based shells are navigable, deep links remain compatible,
backend permissions remain authoritative, critical route groups are represented coherently, and
the accepted organization/Observatory contracts continue to pass without introducing a new
historical-authority claim.

---

## 11. Phase 13.16 — Organization Observatory & Experience Layer

Phase 13.16 is the bridge between the already-built governed AI organization and a coherent
human-facing product experience.

### 11.1 Why Phase 13.16 exists

Earlier Phase 13 work proved that the organization can:

- define positions and authority;
- create and route work;
- make/escalate governed decisions;
- operate bounded departments;
- produce Board-facing evidence;
- pause/override execution;
- validate mobility scenarios;
- record durable outcomes and semantic transitions.

Phase 13.16 asks a different question:

> Can humans understand and operate this system safely through clear, role-appropriate
> experiences backed by trustworthy organizational records?

### 11.2 Delivery sequence

| Slice | Outcome | State |
|---|---|---|
| **13.16.0** | Design System & Information Architecture Foundation | **CLOSED / PASS** |
| **13.16.1** | Durable Contribution & Activity Model | **COMPLETE / PASS** |
| **13.16.2** | Role-based application shells and navigation | **UNLOCKED / NOT STARTED** |
| **13.16.3** | Unified Owner Control Center | **LOCKED** |
| **13.16.4** | Department workspaces | **LOCKED** |
| **13.16.5** | Cross-department dependencies and blocker view | **LOCKED** |
| **13.16.6** | Owner decision and escalation inbox | **LOCKED** |
| **13.16.7** | Mobility User experience | **LOCKED** |
| **13.16.8** | Professional/Operator experience | **LOCKED** |
| **13.16.9** | Evidence and provenance UX consolidation | **LOCKED** |
| **13.16.10** | Responsive, accessibility, polish, integrated acceptance | **LOCKED** |

### 11.3 13.16.1 durable Contribution & Activity model

Purpose: create an authoritative organizational read model before building dashboards that could
otherwise confuse runtime noise with meaningful work or outcomes.

| Slice | Outcome | State |
|---|---|---|
| Design | Canonical contracts, schema/API direction, aggregation boundary, backfill policy | **COMPLETE** |
| 13.16.1A | Durable organization persistence | **COMPLETE / PASS** |
| 13.16.1B | HTTP-independent command/service layer | **COMPLETE / PASS** |
| 13.16.1C | Authenticated organization API | **COMPLETE / PASS** |
| 13.16.1D0 | Authoritative emitter mapping / transaction design | **COMPLETE** |
| 13.16.1D1 | Caller-owned transaction staging | **COMPLETE / PASS** |
| 13.16.1D2 | Source-certification Contribution emitter | **COMPLETE / PASS** |
| 13.16.1D3A | InitialRuleAssertion / VerifiedRule emitter | **COMPLETE / PASS** |
| 13.16.1D3B | RegulatoryChange emitter | **COMPLETE / PASS** |
| 13.16.1D3C | MobilityPathwayVersion publication emitter | **COMPLETE / PASS** |
| 13.16.1D4 | Deferred-domain review + integrated emitter regression | **COMPLETE / PASS** |
| 13.16.1E0 | Observatory/read-model reconciliation design | **COMPLETE** |
| 13.16.1E1 | Safe snapshot + Contribution reconciliation read API | **COMPLETE / PASS** |
| 13.16.1E2 | Caller-owned Activity staging + modern semantic transition coverage | **COMPLETE / PASS** |
| 13.16.1E3A | Legacy writer inventory + coverage-epoch design | **COMPLETE** |
| 13.16.1E3B | Legacy WorkItem material-writer adapters | **COMPLETE / PASS** |
| 13.16.1E3C | Legacy ExecutiveDecision / coupled adapters | **COMPLETE / PASS** |
| **13.16.1E3D** | Explicit immutable Activity coverage epoch + Observatory activation | **COMPLETE / PASS** |

Authoritative design/evidence:

- [DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md](DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md)
- [ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md](ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md)

### 11.4 13.16.1 invariants

- Activity, Contribution, Decision, Blocker, WorkItem, and HumanAction are distinct records.
- Activity volume is never organizational productivity.
- Contribution remains outcome-oriented and source-authoritative.
- Activity cannot create a Contribution.
- Source-owned Contribution emitters remain sealed integrations.
- ExecutiveDecision remains explicit-command-only for generic Contribution creation.
- Observatory snapshot metrics derive from authoritative current rows.
- Contribution reconciliation must expose gaps/drift rather than repair them on GET.
- Blocker department attribution uses linked WorkItem department first, blocker department second.
- Pre-epoch Activity may remain visible but cannot prove complete historical throughput.
- `activity_history_established` is false before the explicit E3D marker exists and true from that immutable marker forward.
- No historical backfill is authorized.

### 11.5 13.16.2 — role-based application shells and navigation

**Intent:** move away from a route-heavy developer/operator information architecture toward
clear role-based shells without breaking deep links or authority boundaries.

Expected direction:

- Owner/Board navigation groups the product into Overview, Organization, Mobility Operations,
  Intelligence, Validation, Governance, and Settings.
- Mobility User navigation is case-centric and hides backend/governance noise.
- Professional/Operator navigation prioritizes cases, comparison, evidence, validation,
  timelines, authority workflow, and provenance.
- Existing deep routes remain reachable during incremental migration.
- Authorization remains backend-enforced; navigation visibility is not a permission system.

### 11.6 13.16.3 — Unified Owner Control Center

**Intent:** give the Human Owner / Board a concise operational view of the AI organization.

The control center should distinguish:

- organizational health;
- work in progress;
- meaningful Contributions;
- decisions awaiting attention;
- blockers and dependencies;
- validation/review risk;
- departments requiring intervention;
- human-action queues;
- emergency controls.

It must not substitute raw AgentRun counts, messages, retries, or tool activity for business
progress.

### 11.7 13.16.4 — Department workspaces

**Intent:** make bounded executive/department runtimes usable as coherent operational units.

Expected concepts:

- owned work;
- dependencies;
- blockers;
- decisions;
- Contributions;
- material Activity;
- human requests;
- department-specific evidence and outputs.

### 11.8 13.16.5 — Cross-department dependencies and blockers

**Intent:** make organizational friction visible without forcing the Board to inspect every task.

The experience should answer:

- what is blocked;
- why it is blocked;
- which department owns the underlying work;
- which dependency is unresolved;
- whether human action is required;
- whether escalation has occurred;
- what changed materially.

### 11.9 13.16.6 — Owner decision and escalation inbox

**Intent:** centralize genuinely Board/Owner-relevant decisions and human-required actions.

The inbox should prioritize materiality and authority, not chronological noise.

### 11.10 13.16.7 — Mobility User experience

**Intent:** convert the platform's already-deep mobility intelligence into a clearer end-user
journey centered on goals, cases, pathways, evidence, documents, actions, costs, risks, and
long-term progression.

### 11.11 13.16.8 — Professional / Operator experience

**Intent:** provide experts and internal operators with a high-information-density workspace that
preserves source provenance, uncertainty, review state, case operations, and authority workflow.

### 11.12 13.16.9 — Evidence and provenance UX consolidation

**Intent:** make evidence state understandable everywhere it matters rather than scattering
source/provenance concepts across unrelated pages.

The user should be able to distinguish:

- official source;
- retrieved snapshot;
- certification/review state;
- verified rule;
- pathway evidence;
- pending evidence;
- superseded evidence;
- unresolved gaps.

### 11.13 13.16.10 — responsive/accessibility/polish/integrated acceptance

Critical journeys must pass:

- desktop and mobile layouts;
- keyboard navigation;
- screen-reader semantics;
- contrast and visual hierarchy;
- loading/error/empty states;
- role separation;
- cross-role handoffs;
- integrated acceptance across Owner, Mobility User, and Professional/Operator experiences.

---

## 12. Phase 13 — AI Organization Governance & Autonomous Operations

Phase 13 transforms the product from an AI-assisted application into a **governed AI-operated
organization**.

### 12.1 Why Phase 13 matters

Earlier phases built mobility intelligence and workflows. Phase 13 adds the organizational
system that determines:

- who owns work;
- who can decide;
- how agents delegate;
- how risk escalates;
- when humans must intervene;
- how departments operate;
- how outcomes are recorded;
- how the Board retains control.

### 12.2 Governance and organization foundation

| Slice | Outcome | State |
|---|---|---|
| 13.0 | Governance contract and stabilization dependency | **COMPLETE** |
| 13.1 | Organization registry and position contracts | **COMPLETE** |
| 13.2 | Authority, risk, and executive decisions | **COMPLETE** |
| 13.3 | CEO and executive council runtime | **COMPLETE** |
| 13.4 | First autonomous organization flow | **COMPLETE** |
| 13.5 | Board Room and executive reporting | **COMPLETE** |
| 13.5.1 | Platform hardening and runtime registration | **COMPLETE** |
| 13.5.2 | External mobility validation framework | **COMPLETE** |
| 13.6 | Departmental expansion | **COMPLETE** |
| 13.11 | Finance/CFO bounded runtime | **COMPLETE / PASS** |
| 13.12 | Communications/CCO bounded runtime | **COMPLETE / PASS** |
| 13.13 | People/CHRO bounded runtime | **COMPLETE / PASS** |
| 13.14 | Legal/CLO bounded runtime | **COMPLETE / PASS** |
| 13.15 | Validation programme / Round 6 correctness gate | **COMPLETE / PASS** |
| 13.16 | Observatory & Experience Layer | **IN PROGRESS** |
| 13.17 | Genuine external-human acceptance | **LOCKED** |

### 12.3 Bounded department direction

Department runtimes are intended to model organizational specialization while preserving one
shared governance contract.

Delivered bounded domains include:

- Operations / COO;
- Technology / CTO;
- Product / CPO;
- Security / CISO;
- Security Operations / SOC;
- Marketing / CMO;
- Finance / CFO;
- Communications / CCO;
- People / CHRO;
- Legal / CLO.

A department is not “implemented” merely because a role card exists. Operational status requires
runtime registration, position authority, output contracts, work routing, tests, and governance
boundaries.

### 12.4 Phase 13.10.2 external-mobility validation hardening

The software hardening programme is complete through the current correctness gate. Historical
release evidence remains in the changelog; live independent-review obligations remain
operational where explicitly noted.

| Documented slice | Outcome | Current posture |
|---|---|---|
| 13.10.2.1 | PostgreSQL migration portability hardening | **COMPLETE** |
| 13.10.2.2 | Controlled official-source authority remediation | **SOFTWARE COMPLETE; live review operations continue** |
| 13.10.2.3 | Existing-source baseline linkage hardening | **COMPLETE** |
| 13.10.2.4 | Supplemental source-certification multiplicity hardening | **SOFTWARE COMPLETE; genuine review still required where pending** |
| 13.10.2.5 | Pathway multi-source evidence provenance | **COMPLETE** |
| 13.10.2.6 | Structured 2026 shortage-occupation evidence | **COMPLETE** |
| 13.10.2.7 | Austria pathway integration of structured 2026 evidence | **COMPLETE; publication remains gated** |
| 13.10.2.8 | Independent-review readiness / certification evidence packs | **COMPLETE** |
| 13.10.2.9 | Independent-review workflow UX and audit closure | **COMPLETE** |
| 13.10.2.10 | Austria intake and shadow-validation unblocking | **COMPLETE** |
| 13.10.2.12 | Intake persistence and case continuity | **COMPLETE** |
| 13.10.2.13 | Austria candidate integrity and occupation resolution | **COMPLETE** |
| 13.10.2.14 | Assessment consistency and conditionality hardening | **COMPLETE** |
| 13.10.2.15 | Eligibility preview consistency | **COMPLETE / rendered gate PASS** |

### 12.5 Round 6 correctness disposition

**State: PASS / CLOSED.**

The Round 6 mobility-user and independent professional shadow reviews found zero
Critical/High correctness findings and zero unsupported legal certainty. This was a correctness
gate, **not** genuine external-human acceptance.

The deterministic disposition is recorded in
[ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md](ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md).

### 12.6 Phase 13 non-negotiable controls

- No position receives authority merely because its prompt claims authority.
- No agent may change its own position contract, reporting line, authority, or budget.
- No autonomous spending, contract signature, legal filing, authority submission,
  production deployment, or client-facing send outside an explicit gate.
- Regulated conclusions remain source-controlled and review-gated.
- Cross-tenant access remains prohibited.
- Every meaningful action is attributable and audited.
- Board pause, override, rejection, and emergency controls remain enforceable.
- Material governance state must not be inferred from UI activity or agent chatter.

### 12.7 Phase 13 release criteria

Already satisfied foundations:

- [x] Complete Board-to-specialist hierarchy is executable.
- [x] Authority classification is deterministic and tested.
- [x] Restricted actions fail closed.
- [x] Delegation/escalation is idempotent and traceable.
- [x] CEO produces an evidence-backed Board Packet.
- [x] Board can approve, reject, return, override, pause, and suspend.
- [x] Bounded department runtimes are implemented.
- [x] Round 6 correctness disposition is PASS.

Remaining release gates:

- [x] 13.16.1 durable Contribution & Activity model complete.
- [ ] 13.16.2-13.16.10 shared experience implementation and integrated acceptance complete.
- [ ] 13.17 genuine external-human acceptance complete.
- [ ] Deterministic Phase 13 disposition recorded.

---

## 13. Phase-by-Phase Product Evolution

This section explains how the major delivery phases build toward the product vision. It is a
strategic map, not a duplicate of every historical sub-slice.

### 13.1 Phases 1-5 — core product foundation

**Strategic purpose:** establish a usable local-first mobility platform before attempting global
regulatory automation or organizational autonomy.

Delivered foundation includes:

- CRM and intake;
- client/case state;
- Truth Engine foundations;
- documents;
- eligibility;
- controlled agents;
- audit;
- RBAC;
- early study/work/mobility workflows.

**What this enabled next:** a stable shared domain foundation for regulatory intelligence and
more sophisticated profile/pathway reasoning.

### 13.2 Phase 6 — foundation and repository alignment

**Strategic purpose:** align architecture, repository controls, local/Docker development, API,
web, migrations, testing, and deployment assumptions so later phases build on one governed
platform rather than disconnected prototypes.

Reference: [ARCHITECTURE.md](ARCHITECTURE.md).

### 13.3 Phase 7 — regulatory intelligence foundation

**Strategic purpose:** move from manually encoded mobility knowledge toward monitored,
source-controlled regulatory intelligence.

Delivered direction includes:

- jurisdictions and authorities;
- official-source registry;
- retrieval and snapshots;
- immutable hashes;
- monitored changes;
- reviewed rules;
- provenance.

**Why it matters:** pathway recommendations are only as trustworthy as the evidence and rule
state behind them.

Reference: [TRUTH_ENGINE_SPEC.md](TRUTH_ENGINE_SPEC.md).

### 13.4 Phase 8 — mobility intelligence foundation

**Strategic purpose:** connect the user profile to governed country/pathway comparisons and
operational planning.

Delivered direction includes:

- universal profile;
- pathway catalogue;
- deterministic comparison;
- eligibility reasoning;
- costs/risks;
- timeline planning.

**Why it matters:** the product becomes an intelligence layer, not merely a database of visa
pages.

### 13.5 Phase 9 — document intelligence

**Strategic purpose:** make documents part of the governed mobility decision process.

Delivered direction includes:

- extraction;
- validation;
- integrity findings;
- reminders;
- controlled access;
- expiry awareness;
- document fraud-risk signals with human review boundaries.

Reference: [DOCUMENT_INTELLIGENCE_FOUNDATION_V9_0.md](DOCUMENT_INTELLIGENCE_FOUNDATION_V9_0.md).

### 13.6 Phase 10 — self-updating global mobility intelligence

**Strategic purpose:** turn the regulatory foundation into a progressively self-updating global
intelligence system.

#### 10A — controlled regulatory intelligence

Delivered direction includes:

- regulatory classification;
- structured change handling;
- graph projection;
- pathway impact logic.

#### 10B — global evidence coverage operations

Software delivers:

- jurisdiction/authority/source registry;
- evidence batches;
- onboarding;
- baseline capture;
- initial rule assertions;
- readiness receipts;
- tranche operations.

Historical Phase 10B delivery anchors remain part of the roadmap contract because operational
tooling and repository tests still use them to connect the current strategy to the implemented
coverage workflow:

- **v10.22** introduced **multi-batch tranche operations** for bounded coverage-expansion
  execution while preserving human review and publication boundaries;
- migration **`0032_initial_rule_assertions`** established the initial-rule assertion persistence
  milestone used by the reviewed baseline/publication workflow.

These are compatibility/history anchors, not active version targets. Detailed implementation and
acceptance evidence remains in `CHANGELOG.md` and the Phase 10B feature documents.

Operational evidence onboarding remains ongoing because global coverage is a data/review
programme, not merely a code feature.

#### 10C-10E — intelligence products and long-range planning

Delivered direction includes:

- global dashboards;
- reviewed ranking;
- multi-year mobility scenarios;
- opportunity and planning views.

**Why Phase 10 matters:** it moves the product toward continuous global intelligence while
preserving explicit review gates.

### 13.7 Phase 11 — corporate, business and wealth mobility

**Strategic purpose:** broaden the system beyond individual study/work pathways.

Delivered direction includes:

- corporate mobility;
- entrepreneur/startup contexts;
- business/wealth advisory;
- investment migration context;
- HNWI/family-office controls;
- tax/treaty evidence workflows.

Reference: [BUSINESS_WEALTH_ADVISORY_V11_4.md](BUSINESS_WEALTH_ADVISORY_V11_4.md).

### 13.8 Phase 12 — ecosystem, portals and governed automation

**Strategic purpose:** connect intelligence and cases to real operational actors and external
workflow while retaining control boundaries.

Delivered direction includes:

- client portal;
- partner APIs;
- governed automation;
- appointment tracking;
- submission tracking;
- authority assignment;
- checklists;
- reminders;
- government/agency workflows;
- stabilization of runtime database, portal session security, API contracts, and frontend
  regressions.

**Why Phase 12 matters:** the platform begins to function as an operating environment rather
than only an intelligence engine.

### 13.9 Phase 13 — AI organization governance and human experience

**Strategic purpose:** let controlled AI workers operate as a bounded organization and then make
that organization legible and usable to humans.

Phase 13 is currently the major delivery focus.

The progression is:

```text
Governance contracts
   ↓
Organization positions + authority
   ↓
CEO / executives / departments
   ↓
Board controls + evidence
   ↓
External validation + correctness
   ↓
Durable Contributions + semantic Activity
   ↓
Organization Observatory
   ↓
Role-based Owner / Mobility User / Professional experiences
   ↓
Genuine external-human acceptance
```

### 13.10 Phase 14 — global scale platform

**Strategic purpose:** scale a validated product, not pre-emptively redesign it around unproven
infrastructure needs.

Potential work includes:

- broader reviewed evidence coverage;
- dedicated search when PostgreSQL becomes insufficient;
- graph infrastructure for validated graph traversal;
- event streaming and durable long-running orchestration when required;
- full telemetry/SLO/resilience stack;
- Kubernetes and multi-cloud/on-premise deployment profiles.

Phase 14 remains locked until Phase 13 acceptance and measured demand justify it.

---

## 14. Ongoing Operational Programme — Phase 10B Global Evidence Coverage

The Phase 10B software workflow is complete. Remaining work is evidence collection,
independent review, publication, and continuous freshness maintenance.

### 14.1 Coverage objective

The long-term vision targets:

- every required UN-recognized country;
- autonomous immigration jurisdictions and territories with independent rules;
- official immigration, embassy, gazette, legislation, education, accreditation, labour,
  sponsorship, investment, tax, and treaty sources where relevant.

A software-complete registry does not equal verified global coverage.

### 14.2 Operating rules

- Never infer an immigration-rule relationship from registry presence.
- Require reviewed authority and official-source evidence.
- Require independent assessment and source-certification decisions.
- Capture immutable baselines only after required reviews pass.
- Publish initial verified rules through separate proposal, review, and publication identities.
- Keep the global-coverage claim false until every required jurisdiction passes its gates.

### 14.3 Operating cycle

1. Select prioritized evidence gaps.
2. Research jurisdiction, authority, relationship, and official source.
3. Submit an atomic evidence batch.
4. Complete independent assessment and source-certification review.
5. Queue approved baseline captures.
6. Draft, independently review, and explicitly publish snapshot-pinned rules.
7. Reconcile readiness and maintain source freshness.

The last recorded readiness in historical delivery evidence is **82/243**. It is an operational
data state, not a software-completeness measure, and must be recalculated from the active
database before external use.

Key specifications:

- [GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md](GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md)
- [GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md](GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md)
- [INITIAL_RULE_ASSERTIONS_V10_19.md](INITIAL_RULE_ASSERTIONS_V10_19.md)
- [COVERAGE_READINESS_RECEIPTS_V10_20.md](COVERAGE_READINESS_RECEIPTS_V10_20.md)
- [COVERAGE_TRANCHE_OPERATIONS_V10_22.md](COVERAGE_TRANCHE_OPERATIONS_V10_22.md)

---

## 15. Austria Safety / Governance Invariants

These constraints remain unchanged while Phase 13 organization/runtime work proceeds.

### 15.1 Austria v4

- lifecycle: `draft`
- recommendation: `simulation_candidate`
- compatibility: `INTERNAL_SIMULATION_ONLY`
- production recommendation: `false`
- simulation only: `true`
- publication ready: `false`
- published: `false`

### 15.2 Occupation and certification state

- overall occupation result: `AMBIGUOUS`
- regional unknown-province state: `INSUFFICIENT_INFORMATION`
- qualification mapping: `UNRESOLVED`
- national 2026 source certification: `pending_review`
- regional 2026 source certification: `pending_review`

### 15.3 Material case boundaries

- binding Austrian job offer required;
- job offer absent and blocking;
- government application fee: EUR 218;
- canonical evidence gaps: 14;
- human review required.

Do not publish Austria v4, approve pending certifications, weaken human review, or claim
unsupported legal certainty as part of unrelated organization/runtime work.

---

## 16. Stabilized Platform — Phase 12

Phase 12 is delivered and stabilized. Historical stabilization detail is retained in the
changelog and Phase 12 specifications.

Completed stabilization areas:

- runtime database alignment;
- secure portal-session correction;
- error-contract/test repair;
- frontend/browser regression coverage;
- governed automation and portal/partner/government workflows.

The Phase 12.8.7 client experience remains a PWA/mobile-web foundation and must not be described
as a native iOS or Android application.

---

## 17. Security, Compliance and Trust Baseline

The product direction requires:

- RBAC now and ABAC as partner/corporate boundaries mature;
- tenant isolation before partner or corporate access;
- signed/expiring document access;
- encryption in transit and at rest;
- managed secrets and key rotation;
- consent, retention, deletion, and data-residency controls;
- immutable audit evidence for sensitive transitions;
- least-privilege service and human identities;
- rate limiting and abuse detection;
- backups, recovery exercises, and incident response;
- no visa, legal, tax, scholarship, employment, or investment claim without verified evidence
  and the required review state.

Security controls are product behavior, not merely infrastructure settings.

Reference: [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md).

---

## 18. Phase 14 — Global Scale Platform

**Status: NOT STARTED.** Implement only after Phase 13 acceptance and measured demand.

Potential scale work includes:

### 18.1 Coverage and data scale

- expand reviewed evidence coverage;
- maintain jurisdiction/source freshness at higher volume;
- introduce additional operational quality metrics only when coverage semantics are reliable.

### 18.2 Search and knowledge systems

- OpenSearch/Elasticsearch only when PostgreSQL search is measured as insufficient;
- Qdrant/semantic search where validated retrieval use cases require it;
- Neo4j only when validated graph traversal needs a dedicated graph database.

### 18.3 Workflow and event scale

- durable event streaming when cross-service volume/recovery requirements justify it;
- Temporal-class orchestration when long-running workflow durability requires it;
- continue n8n-class business automation where appropriate.

### 18.4 Observability and reliability

- OpenTelemetry;
- Prometheus/Grafana;
- centralized logs/Loki-class tooling;
- distributed tracing;
- SLOs;
- backup/recovery exercises;
- stronger multi-tenant operational controls.

### 18.5 Deployment scale

- Kubernetes only when operational complexity is justified;
- cloud/on-premise deployment profiles based on customer/security requirements;
- no infrastructure adoption solely because it is fashionable or available.

---

## 19. Completed Delivery Index

| Phase | Outcome | Evidence |
|---|---|---|
| 1-5 | Local-first platform, CRM, intake, Truth Engine, documents, eligibility, controlled agents, audit, RBAC | [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md) |
| 6 | Foundation and repository alignment | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 7 | Regulatory intelligence, monitored official sources, immutable snapshots, reviewed changes, verified rules | [TRUTH_ENGINE_SPEC.md](TRUTH_ENGINE_SPEC.md) |
| 8 | Universal profile, governed pathways, deterministic comparison, operational timelines | [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md) |
| 9 | Document extraction, validation, integrity findings, reminders, controlled access | [DOCUMENT_INTELLIGENCE_FOUNDATION_V9_0.md](DOCUMENT_INTELLIGENCE_FOUNDATION_V9_0.md) |
| 10A | Self-updating regulatory intelligence, controlled classification, graph projection, pathway impacts | [CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md](CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md) |
| 10B software | Registry, evidence batches, onboarding, baseline capture, rule assertions, readiness receipts, tranche operations | [COVERAGE_TRANCHE_OPERATIONS_V10_22.md](COVERAGE_TRANCHE_OPERATIONS_V10_22.md) |
| 10C-10E | Global dashboards, reviewed ranking, immutable multi-year mobility scenarios | [MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md](MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md) |
| 11 | Corporate, business, wealth, investment, family-office, tax/treaty mobility | [BUSINESS_WEALTH_ADVISORY_V11_4.md](BUSINESS_WEALTH_ADVISORY_V11_4.md) |
| 12 | Client/ecosystem portals, partner APIs, governed automation, appointments, submissions, assignments, checklists, reminders | [GOVERNED_AUTOMATION_FOUNDATION_V12_3.md](GOVERNED_AUTOMATION_FOUNDATION_V12_3.md) |
| 13.0-13.15 | AI organization governance, bounded departments, Board Room, external validation, correctness gate | [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md), [EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md](EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md) |
| 13.16.0 | Design System & Information Architecture foundation | Phase 13.16 documentation / changelog |
| 13.16.1A-E3D | Durable organization persistence, Contribution/Activity model, Observatory reconciliation, legacy writer coverage, immutable coverage epoch | [DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md](DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md) |

---

## 20. Delivery Governance

Every software slice must include:

- accountable product/runtime ownership;
- acceptance criteria tied to canonical product intent;
- migration and rollback paths when data changes;
- least-privilege authorization and tenant boundaries;
- audit for sensitive actions/transitions;
- provenance/Truth Engine integration for regulated claims;
- backend tests and frontend build/type validation where applicable;
- browser-level validation for critical user journeys where applicable;
- security, privacy, consent, retention, and operational notes;
- `docs/ROADMAP.md` and `docs/CHANGELOG.md` updates;
- an explicit statement of what remains incomplete.

### 20.1 Status definitions

- **Implemented** — code exists; acceptance is not yet complete.
- **Delivered** — focused verification passes.
- **Complete / PASS** — phase/slice exit criteria and required quality gates pass.
- **Operationally ongoing** — software is complete but live evidence, review, monitoring,
  freshness, or data expansion continues.
- **Locked** — prerequisite release gate has not passed.
- **Blocked** — a specific external or technical dependency prevents progress.

A UI without authoritative backend, permissions, audit, and tests is not a completed capability.
A role card without runtime registration, authority enforcement, and an output contract is not
an operational agent.

### 20.2 Unlock discipline

A later slice must not be marked started merely because implementation could technically begin.
The roadmap unlock state must follow accepted prerequisite evidence.

Examples:

- 13.16.2 is unlocked because 13.16.1 is COMPLETE / PASS; later 13.16.x slices remain sequentially gated;
- 13.17 remains locked until the integrated experience layer is ready;
- Phase 14 remains locked until Phase 13 acceptance and measured demand.

### 20.3 Documentation discipline

Use the documents for different purposes:

- **ROADMAP.md** — product direction, phase intent, current state, unlock order, major gates;
- **CHANGELOG.md** — chronological implementation and acceptance evidence;
- **feature specs** — exact behavioral/architectural contracts;
- **Git** — exact source history;
- **Alembic** — exact schema evolution.

This separation keeps the roadmap detailed enough to explain the project without turning it back
into a 2,000-line chronological log.

---

## 21. Definition of Directional Compliance

A feature is aligned with the Global Mobility AIOS vision when it:

1. advances a capability in the canonical product scope;
2. preserves official-source provenance and jurisdiction/effective-date semantics;
3. uses controlled agents rather than autonomous authority;
4. includes human review and audit evidence where risk requires it;
5. extends shared profile, case, document, rule, event, work, or organization models rather
   than creating an isolated demo path;
6. includes migrations, tests, API contracts, operational notes, and security review where
   applicable;
7. makes uncertainty and incomplete evidence visible;
8. does not claim publication, certification, legal certainty, historical completeness, or
   production authority that has not actually been established;
9. improves a coherent end-to-end mobility operating system rather than optimizing one page or
   agent in isolation.

---

## 22. Historical Evidence and Source of Truth

Use these sources in this order:

1. **Current product/delivery direction:** this `ROADMAP.md`.
2. **Canonical vision:** [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md).
3. **Release/acceptance history:** [CHANGELOG.md](CHANGELOG.md).
4. **Feature contracts and detailed evidence:** versioned documents under `docs/`.
5. **Exact implementation history:** Git commits.
6. **Database evolution:** Alembic migration chain.

Core references:

- [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md)
- [TRUTH_ENGINE_SPEC.md](TRUTH_ENGINE_SPEC.md)
- [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- [DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md](DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md)
- [ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md](ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md)

The roadmap deliberately preserves **strategic depth and phase intent** while avoiding repeated
historical test logs, backup hashes, one-off debugging transcripts, and closed-slice acceptance
narratives. Those records remain in the changelog, feature evidence, Git, and migration history.

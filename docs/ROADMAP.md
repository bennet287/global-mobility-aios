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
understand and operate. The Owner / Board experience is canonically the **Global Mobility AIOS
Cockpit**. The **Board Room is a module inside the Cockpit**, not the name of the entire Owner
control surface.

Capabilities include:

- Global Mobility AIOS Cockpit for Owner / Board entry, governance, intelligence, and intervention;
- Board Room as the executive decision and reserved-authority module inside the Cockpit;
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

**As of:** 2026-08-17
**Development branch:** `roadmap/global-mobility-aios-v11`
**Accepted 13.16.1 / E3D implementation baseline:** `a503fe8b8a41cff6908751ba24688ed03fa535ec`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

**Code migration head:** `0076_organization_position_active_identity`

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
| Phase 13.16.2 | **COMPLETE / PASS** | Premium role shells, controlled preserved-SQLite reconciliation, Cockpit executive-authority hierarchy, discoverable compact rail, and light/dark visual foundation accepted from baseline `4e6aaa5`; Alembic 0075 and all critical runtime reads are green |
| Phase 13.16.3 | **COMPLETE / PASS** | Unified Owner Control Center accepted through 13.16.3C: Owner focus, capability architecture, Tier-1 organization, active-identity integrity, operational-intelligence reads, department drill-down, and governed human-intervention routing are complete without weakening backend authorization or direct blocker/dependency/work/legal outcome boundaries |
| Phase 13.16.4 | **COMPLETE / PASS** | Bounded department workspaces from the Cockpit drill-down into `/workspace/[department]`, with owned work, blockers, dependencies, human requests, Contributions, material Activity, executive ownership, and governed intervention; does not mutate blockers/dependencies/work/legal outcomes directly |
| Phase 13.16.5 | **COMPLETE / PASS** | Cross-department friction surface from the Owner control surfaces, showing blockers and dependencies whose owning department differs from the affected department, with human-action indicators, escalation signals, department workspace links, and governed intervention; no direct blocker/dependency/work/legal-outcome mutation |
| Phase 13.16.6 | **UNLOCKED / NOT STARTED** | Owner decision and escalation inbox is the next product slice after the Technology Radar V1 docs-only checkpoint |
| Phase 13.16.7-13.16.10 | **LOCKED** | Later experience slices remain sequentially gated by accepted delivery of 13.16.6 and subsequent slices |
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

13.16.2 closure evidence:

- Complete API suite: **791 passed, 5 skipped, 0 failed**; the only warning is the pre-existing Starlette/httpx test-client deprecation warning.
- Fresh-migration / reconciliation regression: **6 passed, 0 failed**.
- Frontend premium design-foundation suite: **16 passed, 0 failed**.
- Frontend request/auth suite: **4 passed, 0 failed**.
- Next.js 15.2.4 production build: **PASS**; the accepted route set includes `/cockpit`, `/board-room`, `/`, `/my-mobility`, and `/portal`, with the captured build generating **39/39 static pages**.
- Repository policy and release consistency: **PASS**.
- `git diff --check`: **PASS**; the Windows LF-to-CRLF notice for `design-foundation.test.mjs` is informational and not a whitespace failure.
- Preserved developer SQLite physical schema: **PASS** with **118 registered model tables**, **118 actual model tables**, **119 physical tables** including the Alembic infrastructure table, and database revision `0075_legacy_schema_reconciliation`.
- Runtime smoke: **5/5 HTTP 200** for `/health`, WorkItems, Decisions, Board Packet, and CRM summary.
- Browser acceptance confirmed the premium Cockpit light/dark hierarchy, fixed-width discoverable control rail with hover/focus names, Human Board → CEO → **9 active L3 officers** → **10 operational domains** → governed AIOS execution, Owner Attention, contextual Global Mobility Pulse, and explicit durable-Activity coverage state.
- No PostgreSQL migration command was part of the 13.16.2 closure flow; the preserved PostgreSQL environments remain outside this SQLite-focused reconciliation and visual-acceptance slice.

**Current Phase 13.16 state: 13.16.1, 13.16.2, 13.16.3, 13.16.4, and 13.16.5 are COMPLETE / PASS. Technology Radar V1 is a docs-only platform-evolution checkpoint. 13.16.6 Owner decision and escalation inbox is UNLOCKED / NOT STARTED and remains the next product slice.**

### 8.2 Preserved database boundaries

- The preserved authoritative integration PostgreSQL environment remains intentionally at
  `0073_austria_candidate_integrity` and must not be migrated casually.
- The isolated Phase 13.16.1 PostgreSQL service is the bounded 0074 transaction-test
  environment.
- Developer SQLite is preserved and must not be reset merely to make a test convenient.

---

### 13.16.2 live visual-acceptance refinements


### Preserved developer SQLite reconciliation gate

The live 13.16.2 visual review exposed a preserved developer-database schema drift that had been hidden by the earlier migration gate. The database contains the full registered table set but is missing a bounded set of columns from revisions 0072, 0073, and 0074, and it does not have a usable Alembic revision row. This is an environment-compatibility issue, not a reason to reset developer data.

The controlled repair path is revision `0075_legacy_schema_reconciliation` plus `scripts/reconcile_preserved_sqlite.py`. The script may adopt the preserved schema at 0074 only after confirming that there are no missing application/model tables, no unexpected non-model tables, and that all missing columns are contained in the approved reconciliation whitelist. The Alembic-owned `alembic_version` table is treated explicitly as migration infrastructure rather than application-schema drift; this matters because the earlier failed direct Alembic replay created an empty version table before stopping on the already-existing `leads` table. The script creates an integrity-checked SQLite backup before mutation, applies only 0075, and then requires both physical ORM parity and an actual 0075 Alembic database revision. The authoritative PostgreSQL environment remains untouched.

The preserved SQLite reconciliation gate is now **PASS in the developer environment**: the database is at `0075_legacy_schema_reconciliation`, physical schema parity is restored, and the previously failing WorkItems, Decisions, Board Packet, and CRM summary endpoints all return HTTP 200. The backup remains preserved under `.local`; the authoritative PostgreSQL environment remains untouched.

The browser review of Cockpit, Operations, and My Mobility established the following shell-quality requirements before this slice can close:

- Product UI must not expose roadmap phase numbers or implementation-language explanations.
- The Owner control model must be understandable without conflating Cockpit with Board Room.
- My Mobility should use customer-facing journey language and differentiated case/pathway/document/timeline/action/message cues.
- Partial backend failures must remain visible without presenting raw prototype-style error copy.
- Floating assistance must not obscure role-shell governance or user guidance.
- Premium quality is the baseline: warm ivory, deep ink/navy, restrained depth, high-quality iconography, selective editorial serif plus operational sans, deliberate spacing, and subtle motion rather than generic admin-dashboard chrome.
- Cockpit must feel like a human-owned AI operating system rather than a static consulting website: live organization state should dominate the first viewport, not marketing copy.
- The navigation should behave as a spatially stable compact premium control rail on wide desktop, using icon/title affordances without hover expansion covering live Cockpit content; mobile remains a full labelled drawer and navigation visibility remains non-authoritative.
- Data shown for "wow" must be real. The premium Cockpit preview may compose existing Board Packet, Observatory, Global Intelligence, and durable Activity APIs, but it must not fabricate health percentages, jurisdiction quality scores, historical Activity, or authority state.
- The full Owner Control Center remains Phase 13.16.3; the 13.16.2 premium foundation proves its design language and safe live-data composition without absorbing later department/blocker/decision workflow slices.
- Screenshot acceptance of the signature pass exposed three concrete presentation defects that must be corrected before closure: department nodes may not collide in Organization Pulse, the compact rail may not expand over the live workspace merely on hover, and Global Mobility geography may not rely on crude decorative continent silhouettes. The corrected direction uses a stable six-node organization field, a non-expanding desktop control rail, and a true latitude/longitude coordinate field with region labels and only explicitly mapped jurisdiction markers.
- Owner destinations should read as a unified control dock rather than another row of generic rounded cards, reducing repetitive SaaS-card chrome while preserving the same deep links.

### 8.3 Technology Radar / Platform Evolution track — FROZEN V1

The project now maintains a parallel **Technology Radar / Platform Evolution track** for
third-party and open-source infrastructure candidates. This is an architecture/evaluation track,
not a dependency list and not a replacement for the sequential product roadmap.

Authoritative documents:

- [TECHNOLOGY_RADAR_V1.md](TECHNOLOGY_RADAR_V1.md)
- [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md)
- [ADR/0002-provider-neutral-platform-adapters.md](ADR/0002-provider-neutral-platform-adapters.md)

The frozen architecture principle is **AIOS semantic sovereignty**: third-party infrastructure may
parse, execute, retrieve, observe, scan, render, evaluate, or enforce an AIOS-defined capability,
but it may not become authoritative for domain meaning, legal status, evidence/certification
state, human-review requirements, publication state, organizational authority, or business
outcome semantics.

Initial V1 classifications:

- **ADOPT / EARLY PILOT:** Docling, Presidio, urlwatch, Promptfoo, OpenTelemetry, ClamAV;
- **PILOT / BENCHMARK:** PaddleOCR, Unlimited-OCR, pgvector, Qdrant, Pydantic AI, Langfuse,
  Gotenberg, Typst;
- **STRATEGIC PILOT:** Temporal, OpenFGA;
- **RESEARCH:** DSPy, EU DSS, Fides, OpenLineage;
- **NARROW / CONDITIONAL:** OPA, OpenFeature;
- **BENCHMARK ONLY:** Haystack, MarkItDown.

Wave 0 is **documentation/architecture only**. It adds no runtime dependency, container, migration,
feature flag, database mutation, or placeholder interface. Actual AIOS-owned runtime contracts
appear only when the first real implementation needs them.

This checkpoint does **not** reorder Phase 13.16. Phase 13.16.5 remains COMPLETE / PASS and
**13.16.6 Owner decision and escalation inbox remains the next product slice**.

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

#### Preserved SQLite schema-integrity gate

Live Board Room and Operations smoke exposed a pre-existing physical-schema drift in the preserved developer `gmai.db`: the database was stamped at `0074_durable_contribution_activity_model`, but `leads` lacked the eight structured case columns introduced by 0073, while `organizational_work_items` and `executive_decisions` lacked the durable extension columns, constraints, and indexes introduced by 0074. This made current ORM reads fail with `no such column` and surfaced as HTTP 500 responses from WorkItems, Decisions, Board Packet, and CRM summary endpoints.

The repair policy is forward-only and data-preserving:

- add `0075_legacy_schema_reconciliation` as a compatibility-safe migration; correctly migrated 0074 databases no-op through it;
- reconcile only missing 0073/0074 Lead, WorkItem, and ExecutiveDecision schema elements and restore the intended structured-intake Lead backfill without overwriting already-populated values;
- keep the preserved authoritative `gmai-postgres` integration database untouched at 0073 during this local remediation;
- strengthen the normal migration check so a local SQLite database cannot report PASS merely because code has an Alembic head and registered metadata while its physical columns are stale;
- back up the preserved SQLite file before applying 0075, verify schema parity afterward, and re-run the failing live endpoints before 13.16.2 closure.

This is a schema-integrity remediation discovered during real application smoke, not a change to Austria legal state, Activity history semantics, authorization, or the role-shell information architecture.

---

## 10. Active Execution Lane

Work proceeds in this order. A later programme must not hide an earlier red release gate.

| Order | Programme | State | Unlock condition |
|---|---|---|---|
| 1 | Phase 10B evidence operations | **ONGOING** | Continue independent jurisdiction review without claiming global completeness |
| 2 | 13.15 Round 6 correctness | **COMPLETE / PASS** | Closed |
| 3 | 13.16.0 design/IA foundation | **CLOSED / PASS** | Closed |
| 4 | 13.16.1 durable Contribution & Activity model | **COMPLETE / PASS** | Closed after E3D coverage-epoch acceptance |
| 5 | 13.16.2 role-based application shells and navigation | **COMPLETE / PASS** | Closed after premium visual, schema-reconciliation, runtime, frontend, API, repository, and migration acceptance |
| 6 | 13.16.3 Unified Owner Control Center | **COMPLETE / PASS** | 13.16.2 COMPLETE / PASS |
| 7 | 13.16.4 Department workspaces | **COMPLETE / PASS** | Closed |
| 8 | 13.16.5 Cross-department dependencies and blocker view | **COMPLETE / PASS** | Closed |
| 9 | 13.16.6 Owner decision and escalation inbox | **UNLOCKED / NEXT** | Technology Radar V1 docs-only checkpoint does not change product ordering |
| 10 | 13.16.7-13.16.9 role-based experience delivery | **LOCKED** | Deliver slices sequentially after 13.16.6 |
| 11 | 13.16.10 integrated responsive/accessibility acceptance | **LOCKED** | 13.16.2-13.16.9 delivered |
| 12 | 13.17 genuine external-human acceptance | **LOCKED** | 13.16.10 PASS |
| 13 | Phase 14 scale work | **LOCKED** | Phase 13 PASS + measured demand |

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

**E3D is COMPLETE / PASS. 13.16.1 is COMPLETE / PASS. 13.16.2 is COMPLETE / PASS. 13.16.3 is COMPLETE / PASS through 13.16.3C.**

### 10.3 Closed slice — 13.16.2 role-based application shells and navigation

**Goal:** turn the accepted backend governance/Observatory foundation into coherent role-based
entry points without weakening server-side authorization or breaking deep operational routes.

The first experience-layer slice should establish:

- the canonical **Global Mobility AIOS Cockpit** as the Owner / Board shell, centered on
  organizational health, work, decisions, blockers, evidence, validation, governance, and
  intelligence, while keeping **Board Room** as a module inside the Cockpit;
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

**13.16.2 implementation from baseline `4e6aaa5b372a0cd4171d1199fb0315961eb691f6`:**

- added `/cockpit` as the canonical Owner / Board entry route;
- retained `/board-room` as the executive decision module and compatible deep link;
- retained `/` as the Professional / Operator Operations Workspace;
- added `/my-mobility` as the case-first Mobility User shell and retained `/portal` as the secure token-bound data surface;
- replaced the single global navigation taxonomy with persisted Cockpit / Operations / My Mobility navigation contexts while preserving existing deep routes;
- kept navigation context explicitly non-authoritative: server-side authentication, role checks, evidence gates, publication controls, and human-review requirements remain the security and authority boundary;
- preserved the rich full Owner Control Center as the next sequential slice while allowing 13.16.2 to prove the premium visual language against existing read-only/live read APIs;
- replaced the interim wide SaaS-style sidebar direction with a compact premium control rail: fixed 88px wide-desktop width, icon-first navigation with immediate floating name/role labels on hover and keyboard focus, a scrollable route body, pinned utility state, and full-label mobile drawer without masking the Cockpit canvas;
- redesigned the Cockpit first viewport around real organization state instead of a static hero: governed runtime state, active positions, active work, Contributions, open risks, and an Organization Pulse derived from the Board Packet and Observatory;
- added a real Owner Attention composition from Board decisions, risk escalations, pending human requests, and overdue work;
- added a reviewed Global Mobility Pulse using the existing Global Intelligence dashboard and a durable Activity stream using `/api/v1/organization/activities`; no synthetic health percentage, fake activity, or destination-quality score is introduced;
- retained explicit Activity coverage semantics so pre-epoch history remains visibly partial rather than reconstructed;
- refined the premium Cockpit signature after live visual review: reduced headline dominance, converted Organization Pulse from a static department grid into a live governed-runtime fabric with data-backed department nodes and non-semantic control-flow motion, elevated Owner Attention into a dedicated authority-ring state, replaced the generic orbit graphic with a contextual geographic world view for recognized jurisdiction codes, and gave the honest zero-Activity state a deliberate coverage visualization rather than synthetic events;
- replaced prototype-style C/O/M experience glyphs with distinct Owner, Operator, and Mobility symbols while preserving the same role-shell routes and non-authoritative navigation semantics.

13.16.2 is **COMPLETE / PASS**. Acceptance closed on 2026-08-15 with Alembic `0075_legacy_schema_reconciliation`; physical SQLite parity at 118 registered / 118 actual model tables plus the Alembic infrastructure table; 6/6 migration regressions; 16/16 premium design-foundation tests; 4/4 request/auth tests; a successful Next.js production build; 791 API tests passed with 5 expected skips and 0 failures; repository policy, release consistency, and `git diff --check` PASS; and 5/5 critical runtime smoke endpoints returning HTTP 200. Browser review accepted the premium light/dark Cockpit, executive-authority hierarchy, discoverable compact rail, Owner Attention, Global Mobility Pulse, and durable-Activity coverage presentation. At that 13.16.2 closure checkpoint, Phase 13.16.3 was **IN PROGRESS**; subsequent sections record its later COMPLETE / PASS closure through 13.16.3C.

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
| **13.16.2** | Role-based application shells and navigation | **COMPLETE / PASS** |
| **13.16.3** | Unified Owner Control Center | **COMPLETE / PASS** |
| **13.16.4** | Department workspaces | **COMPLETE / PASS** |
| **13.16.5** | Cross-department dependencies and blocker view | **COMPLETE / PASS** |
| **13.16.6** | Owner decision and escalation inbox | **UNLOCKED / NOT STARTED** |
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

Implemented foundation:

- **Global Mobility AIOS Cockpit** is the canonical Owner / Board entry point at `/cockpit`.
- **Board Room** remains a module inside the Cockpit at `/board-room`; it is not renamed into the whole Owner experience.
- Professional / Operator entry remains the Operations Workspace at `/`.
- Mobility User entry is `/my-mobility`, while `/portal` remains the secure token-bound case workspace and data-access boundary.
- The shared premium control rail exposes explicit **Cockpit**, **Operations**, and **My Mobility** contexts with persisted presentation preference so overlapping deep routes remain reachable without one giant global navigation tree. On wide desktop it remains icon-first and spatially stable instead of expanding across Cockpit content on hover; native title/accessible labels preserve discoverability, while mobile remains a full labelled drawer.
- Existing deep routes remain reachable during incremental migration.
- Authorization remains backend-enforced; navigation visibility is not a permission system.
- 13.16.2 now includes a bounded, read-only premium Cockpit composition using existing Board Packet, Observatory, Global Intelligence, and durable Activity APIs to validate the design language. Its accepted visual direction includes a live governed-runtime Organization Pulse with non-colliding department placement, a dedicated Owner Authority state, a coordinate-based Global Intelligence field plotting only recognized jurisdiction centroids, a unified dark Owner control dock, and an explicit Activity coverage empty state. These are presentation/composition layers only: full organizational-health workflows, department workspaces, blocker/dependency operations, decision handling, and intervention orchestration remain in 13.16.3 and later slices.

### 11.6 13.16.3 — Unified Owner Control Center

**Premium product direction:** the Owner experience must feel like a high-trust premium enterprise operating system: deep navy/graphite anchor surfaces against warm ivory, selective editorial serif with operational sans, restrained depth, refined motion, beautiful information density, and distinct visual personality without becoming an all-black sci-fi interface. The recognizable visual signature should be the live Organization Pulse plus Owner Attention, reviewed global-mobility intelligence, and trustworthy Activity/Contribution context.

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

#### 11.6.1 13.16.3A — Interactive Organization Pulse + Owner Attention

**State:** COMPLETE / PASS — ACCEPTED 2026-08-16.

This first bounded capability slice turns the accepted premium shell into an interactive Owner control surface without adding a new backend authority model:

- CEO, active L3 executive officers, and operational domains are selectable in Organization Pulse using keyboard-accessible `aria-pressed` controls.
- The selected focus is resolved from the live Board Packet hierarchy and Observatory department snapshots, then exposes real span-of-control, active work, open blockers, active Contributions, linked pending human requests, and the most recent durable Activity or work signal in the loaded window.
- Executive portfolio ownership continues to follow existing `reports_to_position_key` ancestry; unresolved ownership remains unresolved rather than being guessed.
- Owner Attention now counts only **Board-pending decisions plus open risks explicitly marked `requires_board_attention`**. Generic open risks are not silently promoted into Owner authority.
- The reserved-authority queue renders the actual current Board decision/risk records. Pending human-action requests remain a clearly separated delegated-human lane and are not counted as Owner authority unless they are escalated into a Board-reserved record.
- The frontend adds read-only helpers for `/api/v1/organization/observatory/departments` and `/api/v1/organization/human-action-requests`; backend authorization remains authoritative and no write, delegation, publication, Activity, or Austria-safety semantics change.
- Activity remains canonical: if no durable signal exists in the selected scope/window, the Cockpit says so instead of inventing one.
- Screenshot-driven interaction polish keeps span-of-control language consistent: executive focus excludes the selected officer from its downstream-position count, domain focus reports operational positions directly, and CEO focus distinguishes executives, domains, and downstream positions.
- The Organization Pulse and Owner Attention now size to their actual content instead of stretching to an artificial shared height; this removes the large empty region between focus inspection and AIOS while keeping the Owner lane compact.
- Focus metrics are grouped as Execution, Governance, Evidence, and Human attention without changing their underlying Observatory values; operational-domain selection remains a first-class peer to executive selection.

**A acceptance:** premium design-foundation **18 passed**; request/auth **4 passed**; Next.js 15.2.4 production build **PASS** with **39/39 static pages**; interactive browser review confirmed selectable CTO/CISO/domain focus, truthful zero-state Owner Attention, consistent downstream counts, and compact content-led layout; repository policy, release consistency, and `git diff --check` passed. No backend write authority, delegation, Activity reconstruction, or synthetic Owner work was introduced.

#### 11.6.2 13.16.3A.1 — Organization Capability Architecture + live inventory

**State:** COMPLETE / PASS — LIVE INVENTORY RECONCILED 2026-08-16.

The interactive Cockpit exposed a structural truth: the nine-officer executive council is mature enough to remain, but the functional organization below it is too shallow for the product and operating model Global Mobility AIOS is becoming. The code-defined foundation at this gate contained **34 position specs** (Human Board + CEO + nine L3 officers + 23 non-executive positions). The authoritative read-only live audit on 2026-08-16 reported **34 active positions, zero live extras, and zero missing foundation keys**. The earlier browser count of 35 was therefore not used as a mutation basis; the audited database state is the acceptance source of truth.

This slice added a **planning-only, machine-readable capability architecture** plus a **read-only audit command**. The A.1 audit itself did **not** feed `ensure_foundation_positions()`, create positions, repair the live organization, change reporting lines, alter authority, or claim that planned positions represent hired humans. A target position is an organizational capability/ownership slot; later execution may be human-owned, human-supervised, agent-assisted, or automated only within separately accepted authority contracts.

**Executive-council decision:** keep the current nine L3 officers — COO, CTO, CISO, CPO, CFO, CLO, CMO, CCO, and CHRO. Do not add CIO, CRO, IT Director, or another C-suite layer merely to make the org chart look complete. CTO remains the product/platform technology executive; CISO remains an independent peer reporting to CEO rather than reporting through CTO.

**Target capability architecture:**

| Owner | Priority capabilities | Boundary / direction |
|---|---|---|
| **CTO** | Engineering Leadership; Application Engineering; Platform & Reliability; Quality Engineering; Data & AI Engineering; Architecture & Engineering Enablement | Build/run/enable the product and platform; security challenge remains independent under CISO |
| **CISO** | Security Engineering & AppSec; IAM; Security GRC; Security Operations & Incident Response; Threat & Vulnerability Management | Security control ownership and assurance; privacy/legal interpretation remains CLO; platform implementation partners with CTO |
| **COO** | Global Mobility Operations; Document & Evidence Operations; Authority & Filing Operations; Client Success; Partner Operations; Operational Excellence; Commercial Operations; Operational Intelligence; **Global Mobility Intelligence** | COO owns operational research/evidence workflows; CLO remains governance partner for regulatory/legal interpretation and no autonomous filing authority is introduced |
| **CPO** | Product Management; Product Design & UX Research; Product Operations & Analytics; Accessibility & Content Experience | Product owns what/why and customer experience; CTO owns engineering implementation |
| **CLO** | Commercial & Corporate Legal; Global Mobility / Immigration Regulatory; Privacy & Data Protection; Public Policy & Government Regulation; Legal Compliance & Regulatory Assurance | Human-governed legal interpretation, privacy, regulatory challenge, and assurance; unsupported legal certainty remains prohibited |
| **CFO** | FP&A; Accounting & Controller; Tax & Treasury; Procurement & Vendor Management; FinOps / Cloud Economics | Procurement and FinOps are cross-functional with CTO/CISO/CLO rather than isolated purchasing authority |
| **CMO** | Product Marketing; Growth & Demand; Brand & Content; Lifecycle & CRM; Marketing Operations & Analytics | Positioning/growth lifecycle; CCO remains reputation/public-affairs owner |
| **CCO** | Corporate Communications & PR; Public Affairs & Government Relations; Crisis & Issues Communications; Executive & Stakeholder Communications | CCO explicitly means Chief Communications Officer; legal policy interpretation remains CLO |
| **CHRO** | People Operations; Talent Acquisition; Learning & Performance; Culture & Engagement; Workforce Planning & People Analytics | Human workforce/capability planning and people evidence; no autonomous hiring/termination authority |
| **Human Board (future assurance)** | Independent AI Governance & Assurance | Future Board-level assurance capability, not a new C-suite officer and not part of the immediate runtime expansion |

The target registry contains **49 capability domains**. At A.1 it mapped all **23 current non-executive foundation positions**, marked **46 additional capability positions as planned**, and flagged five current positions for **review rather than deletion**: `head_of_product`, `sales_summary`, `business_intelligence`, `marketing_manager`, and `culture_recruitment_lead`. A.2 promotes only the first 13 Technology + Security capability slots into the foundation, leaving **33 positions planned**. Planned does **not** mean “create all remaining positions now”; the architecture remains a long-lived target used to choose small justified tranches.

**Priority model:**

1. **Tier 1 — product/safety/mission critical:** Technology & Engineering, Security, Global Mobility Operations, Global Mobility Intelligence, Legal/Regulatory, and core Product capabilities.
2. **Tier 2 — company operating maturity:** Finance, People, Customer Success/Partner Operations, Product Operations, procurement/FinOps.
3. **Tier 3 — growth/reputation:** Marketing and Communications expansion.
4. **Future:** Board-level independent AI governance/assurance after the operating model is mature enough to justify it.

**A.1 live-audit acceptance:** `python scripts/audit_organization_capabilities.py --database-url sqlite:///D:/global-mobility-aios/gmai.db` returned **7 focused tests PASS**, `foundation_positions=34`, `live_active_positions=34`, `live_extra_position_keys=[]`, `live_missing_foundation_keys=[]`, `live_status=matches_foundation`, and `runtime_mutation_performed=false`; repository policy, release consistency, and `git diff --check` also passed. No reset, repair, or position creation occurred in A.1.

#### 11.6.3 13.16.3A.2 — Tier-1 organization foundation expansion

**State:** COMPLETE / PASS — TECHNOLOGY + SECURITY TRANCHE 1 ACCEPTED 2026-08-16.

The live audit resolved the foundation state cleanly, so the first runtime tranche is bounded to **13 additive Technology + Security capability positions**. The foundation expands from **34 → 47 positions** only after controlled live application; no existing position is deleted, suspended, reassigned, or contract-repaired.

**Technology tranche (9):**

- `lead_software_engineer` → VP Engineering (L2)
- `backend_api_engineer` → Lead Software Engineer (L1)
- `frontend_product_engineer` → Lead Software Engineer (L1)
- `platform_engineer` → VP Engineering (L2)
- `site_reliability_engineer` → Platform Engineer (L1)
- `qa_automation_engineer` → VP Engineering (L1)
- `data_engineer` → VP Engineering (L1)
- `ai_ml_platform_engineer` → VP Engineering (L1)
- `developer_experience_engineer` → Lead Architect (L1)

**Security tranche (4):**

- `application_security_engineer` → Security Lead (L1)
- `iam_engineer` → Security Lead (L1)
- `security_grc_lead` → CISO (L2)
- `vulnerability_management_engineer` → Security Lead (L1)

These positions are **organizational capability slots, not newly hired people and not newly executable agents**. Their foundation contracts set `execution_enabled=false`, `execution_posture=organization_capability_only`, empty delegated/direct action authority, `external_action_authorized=false`, `self_approval_allowed=false`, explicit prohibited authority, and no role-card/runtime adapter. Existing CTO and CISO executable delegation sets remain unchanged (`vp_engineering` + `lead_architect` for CTO; `security_lead` + `threat_analyst` for CISO).

A guarded local helper, `scripts/apply_organization_foundation_tranche.py`, provides read-only preflight by default and refuses unexpected live extras, missing pre-existing foundation keys, missing global OrganizationControl, or non-SQLite targets. `--apply` creates an integrity-checked backup and then performs only additive `ensure_foundation_positions()` registration with audit records. It performs no delete, suspension, contract repair, delegation expansion, schema migration, or authority grant.

**A.2 live acceptance:** guarded preflight identified exactly the 13 approved Technology/Security keys and no unrelated organization drift. Controlled SQLite apply completed additively after an integrity-checked backup. The read-only post-apply audit returned `foundation_positions=47`, `live_active_positions=47`, `live_extra_position_keys=[]`, `live_missing_foundation_keys=[]`, `live_missing_technology_security_tranche_keys=[]`, and `live_status=matches_foundation`. Physical SQLite schema and migration checks passed at `0075_legacy_schema_reconciliation`; repository policy, release consistency, and `git diff --check` passed. Focused tranche regression closed at **11 passed, 0 failed**. The complete API suite closed at **801 passed, 5 skipped, 0 failed** with only the known Starlette/httpx test-client deprecation warning. Runtime smoke closed **5/5 HTTP 200** for health, Board Packet, Observatory summary, Observatory departments, and human-action requests. Browser review confirmed the expanded live organization at **9 executives, 19 operational domains, and 45 downstream positions** beneath CEO, with CTO/CISO portfolios materially expanded while all 13 new capability slots remain non-executable and delegation sets unchanged.

**Later accepted tranches remain sequential:**

2. **Global Mobility Operations + Intelligence + Legal/Regulatory:** case/pathway/document/filing operations, jurisdiction research, evidence/source certification, mobility intelligence, immigration-regulatory counsel, privacy, and regulatory assurance.
3. **Product + Finance + People maturity:** remove no legacy role automatically; resolve `head_of_product`/other review items through explicit compatibility decisions.
4. **Commercial/Marketing/Communications maturity:** only after operational ownership and product-market workflows justify deeper specialization.

Every runtime tranche must define reporting, authority level, role contract, evidence requirements, prohibited authority, runtime availability, migration/data impact (if any), Cockpit ownership, tests, and rollback/compatibility behavior. No planned position automatically gains executable runtime authority simply by being registered.

#### 11.6.4 13.16.3A.3 — Global Mobility Operations + Global Mobility Intelligence + Legal/Regulatory

**State:** COMPLETE / PASS.

**Intent:** expand the Tier-1 mission organization beneath COO and CLO before blocker/dependency ownership becomes authoritative in the Cockpit. The tranche covers case/pathway/document/filing operations, jurisdiction research, evidence/source certification, mobility intelligence, immigration-regulatory counsel, privacy/data protection, and regulatory assurance.

**Implemented bounded foundation tranche (14 capability positions):**

- `mobility_operations_lead` → COO (L2)
- `case_operations_specialist` → Global Mobility Operations Lead (L1)
- `pathway_operations_specialist` → Global Mobility Operations Lead (L1)
- `document_evidence_operations_lead` → COO (L2)
- `evidence_quality_specialist` → Document & Evidence Operations Lead (L1)
- `authority_filing_operations_lead` → COO (L2)
- `submission_readiness_specialist` → Authority & Filing Operations Lead (L1)
- `jurisdiction_research_lead` → COO (L2)
- `regulatory_intelligence_analyst` → Jurisdiction Research Lead (L1)
- `evidence_source_certification_lead` → COO (L2)
- `mobility_intelligence_analyst` → Jurisdiction Research Lead (L1)
- `immigration_regulatory_counsel` → CLO (L2)
- `privacy_data_protection_counsel` → CLO (L2)
- `regulatory_assurance_counsel` → CLO (L2)

The code foundation therefore moves from **47 to 61 positions** only after the reviewed patch is applied; the capability registry moves from **33 to 19 still-planned positions**. Existing executive composition remains unchanged. The 14 promoted positions are organizational capability slots, not claims of 14 newly hired humans and not newly executable agents. Their contracts use the same accepted capability-only posture as A.2: `execution_enabled=false`, `execution_posture=organization_capability_only`, empty delegated/direct action authority, `external_action_authorized=false`, `self_approval_allowed=false`, no role card/runtime adapter, and explicit prohibited direct authority including `authority.submit`, `policy.publish`, `legal.opinion.final`, and `compliance.certify`. Existing COO/Legal delegation sets are not expanded.

The guarded `scripts/apply_organization_foundation_tranche.py` helper is generalized to an explicit `--tranche` registry. It refuses non-SQLite targets, unexpected live extras, missing non-tranche foundation positions, or an incomplete earlier tranche; before `--apply` it remains read-only. The A.3 apply path creates an integrity-checked preserved-SQLite backup and uses additive `ensure_foundation_positions(..., repair_contracts=False)` only. The read-only audit now reports both accepted tranche registries and their live-missing sets. No schema migration is introduced.

Functional acceptance is complete: focused regressions passed, the controlled apply reached **61/61** distinct foundation identities, schema/release checks passed, complete API regression passed at **803 passed / 5 skipped**, runtime reads remained HTTP 200, and COO/CLO Cockpit focus was visually accepted. Final closure is blocked only by the active-identity integrity discrepancy discovered during visual review: Board Packet reported 62 active rows while the read-only capability audit reported 61 distinct active `position_key` identities. Diagnostic evidence proved one semantically identical duplicate active `board` row created within milliseconds on 2026-08-15. No autonomous legal opinion, filing, publication, certification, or unsupported regulatory certainty is authorized; no Austria safety boundary may be weakened.

#### 11.6.4.1 13.16.3A.3R — OrganizationPosition active-identity integrity reconciliation

**State:** COMPLETE / PASS.

**Intent:** close the row-count/identity-count observability gap without deleting organization history or masking the duplicate. The integrity slice makes active-position identity explicit and fail-closed before 13.16.3B can depend on organization counts.

- Strengthen `scripts/audit_organization_capabilities.py` to report both active database rows and distinct active position identities, plus duplicate keys/row IDs; duplicate active identities force `live_status=reconcile_required`.
- Strengthen `scripts/apply_organization_foundation_tranche.py` and `ensure_foundation_positions()` to refuse foundation mutation/bootstrap while duplicate active identities exist rather than silently collapsing them by `position_key`.
- Add guarded local-SQLite `scripts/reconcile_duplicate_organization_positions.py`: read-only preflight by default; only semantically identical duplicate active foundation rows are eligible; no physical FK may point to `organization_positions`; an integrity-checked backup is mandatory; the oldest row remains canonical; redundant rows are suspended, assigned non-colliding archival versions, recorded in audit history, and never deleted.
- Add `0076_organization_position_active_identity`, a data-preserving migration that refuses unresolved duplicates, restores the original `(position_key, version)` uniqueness contract when a preserved legacy database has lost it, and then creates a cross-dialect partial unique active-identity index on `organization_positions.position_key WHERE status='active'`. This preserves the 0056 version-identity invariant while preventing the concurrent bootstrap race from creating a second active row for the same position identity.
- A.3R migration regression correction: a normal fresh 0075 database already carries `uq_org_position_version` from migration 0056, so it correctly rejects two `board@v1` rows before 0076 executes. The 0076 refusal regression must therefore emulate the actual preserved-SQLite drift (stamped 0075 physical schema with the original version-unique constraint absent) rather than trying to create an impossible duplicate through the fresh ORM schema.
- A.3R full-suite regression-scope correction: `test_0075_reconciles_stamped_legacy_extension_drift` is a 0075-specific compatibility test and asserts the database remains stamped at `0075_legacy_schema_reconciliation`. Once 0076 became head, allowing that fixture to run `upgrade head` incorrectly pushed its intentionally minimal 0075-only schema into 0076, where `organization_positions` is deliberately required. The regression now upgrades explicitly to 0075; fresh-head and preserved-like 0076 behavior remain covered by the dedicated 0076 migration tests.
- Preserved PostgreSQL environments remain untouched during the local reconciliation. 0076 must be regression-tested against fresh SQLite and offline/isolated PostgreSQL before any preserved PostgreSQL upgrade is considered.

Acceptance requires: duplicate-aware audit showing `active_rows=62`, 61 distinct keys, duplicate `board`; reconciliation preflight identifying the older Board row as canonical and the newer row as redundant; integrity-backed apply suspending exactly one row; post-apply 61 active rows / 61 distinct keys / zero duplicates; Alembic upgrade to 0076; schema/migration/repo/release checks; focused identity regressions; complete API regression; runtime Board Packet/Cockpit count of 61; and idempotent reconciliation preflight.

**Final A.3R acceptance:** corrected organization regressions passed **14/14**; corrected 0076 migration regressions passed **3/3**; the 0075-specific stamped-legacy compatibility regression passed **1/1** after being pinned to its intended migration boundary. Duplicate-aware audit identified exactly one semantically identical active `board` duplicate. The guarded reconciliation created an integrity-checked backup, preserved the oldest `board@v1` row active, archived the redundant row as `board@v2` suspended, deleted nothing, and changed no authority/delegation. Post-reconciliation audit returned **61 active rows / 61 distinct active keys / zero duplicates / zero extra / zero missing**. Alembic upgraded only the preserved developer SQLite database from 0075 to `0076_organization_position_active_identity`; local schema and migration checks passed at 118 registered / 118 actual model tables plus `alembic_version`, `physical_schema=ok`, and database revision 0076. Reconciliation and A.3 tranche preflights are idempotent with `apply_required=false`. Repository policy, release consistency, and `git diff --check` passed. The complete post-0076 API suite passed at **806 passed / 5 skipped / 0 failed** with only the known Starlette/httpx deprecation warning. Final browser acceptance showed **9 executives, 26 live operational domains, and 59 downstream positions**, which with the Human Board and CEO gives the accepted **61 active OrganizationPosition rows**; the former 62-row discrepancy is closed. Preserved PostgreSQL environments remain untouched.

#### 11.6.4.2 13.16.3A.3 / A.3R checkpoint closure — COMPLETE / PASS

The Tier-1 mission-ownership foundation and the active-position identity repair are accepted together from committed baseline `94a453bd16f00b974442d856a8eeff682a83956c`. The organization closes at **61 active OrganizationPosition rows / 61 distinct active position identities / zero duplicate active keys**, with **9 executives, 26 live operational domains, and 59 downstream positions** visible in Cockpit. The 14 A.3 capability slots remain organizational-capability-only with no execution/delegation expansion.

Integrity closure preserved history rather than deleting it: the oldest Human Board row remains canonical `board@v1 active`; the semantically identical race-created duplicate is retained as `board@v2 suspended` with reconciliation provenance. `0076_organization_position_active_identity` restores durable `(position_key, version)` protection where legacy drift removed it and enforces one active row per `position_key`. The preserved developer SQLite database is at 0076; preserved PostgreSQL environments were not migrated.

Acceptance evidence: organization integrity regressions **14/14 PASS**; 0076 migration regressions **3/3 PASS**; corrected 0075 compatibility regression **1/1 PASS**; complete API **806 passed, 5 skipped, 0 failed**; local schema and migration gates **PASS** at 118 registered / 118 actual model tables plus `alembic_version`; repository policy **PASS**; release consistency **PASS** at `0076_organization_position_active_identity`; `git diff --check` **PASS**; reconciliation and A.3 tranche preflights both idempotent with `apply_required=false`; runtime organization reads remained HTTP 200; browser review accepted COO/CLO focus and the post-reconciliation organization count. No Austria safety boundary, publication/certification state, human-review requirement, or autonomous legal/filing authority was weakened.

#### 11.6.5 13.16.3B — Owner blockers, dependencies, and live operational intelligence

**State:** COMPLETE / PASS.

Once Tier-1 ownership is credible, continue the Unified Owner Control Center with blocker/dependency visibility, live durable Activity, Contribution/evidence health, and department/executive intervention signals. This ordering prevents the Cockpit from assigning blockers to an unrealistic or ambiguous organization model.

**Intent:** make operational friction visible to the Owner without turning the Cockpit into a task manager.

- Load open blockers, active dependencies, running work items, and pending human requests into the Cockpit.
- Render a new **Operational Intelligence** panel with four scoped lanes: **Open blockers**, **Active dependencies**, **Overdue active work**, and **Pending human requests**.
- Scope each lane by the selected `organizationFocus` (CEO / executive / domain) using live department and position filters.
- Add an evidence-health line using existing Observatory `contribution_sources` coverage.
- Surface data freshness from the newest Board Packet / Observatory / Global Intelligence timestamp.
- Link Owner Attention metrics (pending human requests, overdue work) to the relevant Operational Intelligence lane anchors; Board decisions and Board-attention risks continue to link to Board Room.
- Preserve read-only composition: no inline blocker mitigation, dependency waiver, work assignment, or publication authority is added to the Cockpit.

**Acceptance:** design-foundation regressions **19/19 PASS**; request/auth tests **1/1 PASS** for the new organization read endpoints; complete API **806 passed, 5 skipped, 0 failed**; Next.js 15.2.4 production build **PASS** with **39/39 static pages**; repository policy, release consistency, migration/schema checks, and `git diff --check` **PASS** at Alembic `0076_organization_position_active_identity`; runtime smoke confirms `/api/v1/organization/blockers?status=open`, `/api/v1/organization/work-item-dependencies?status=active`, and `/api/v1/organization/work-items/records?status_filter=running` return HTTP 200. No Alembic change, no preserved PostgreSQL migration, no Austria safety boundary weakened.

#### 11.6.6 13.16.3C — Live intervention controls + department-level drill-down

**State:** COMPLETE / PASS.

**Intent:** let the Owner move from organization-wide signal detection into a bounded department context and request governed human follow-up without turning Cockpit into an unrestricted command surface or pre-empting the richer department workspaces in 13.16.4.

- When an operational domain is selected, expose a **Department drill-down** derived from the already-loaded organization graph, Observatory metrics, work records, blockers, dependencies, pending human requests, and durable Activity.
- Show the resolved executive owner, active domain positions, operating-state counts, and the newest durable signal without synthesizing department history.
- Add a **Governed intervention** control to open blockers, active dependencies, and overdue work. The only Cockpit mutation introduced in this slice is creation of an existing `OrganizationHumanActionRequest` through `POST /api/v1/organization/human-action-requests`.
- Intervention requests require explicit instructions and select a bounded request type (`review`, `provide_information`, or `acknowledgement`), required human role (`operator` or `reviewer`), and priority. Backend authentication/authorization remains authoritative; rejected commands are surfaced rather than optimistically applied.
- Dependency interventions attach the human request to the downstream work item while retaining dependency provenance in `source_object_type`, `source_object_id`, and `source_object_version`.
- Use a stable target/version request key so replay of the same accepted intervention is idempotent under the existing human-action command contract.
- Explicitly **do not** mitigate/resolve/waive blockers, waive/satisfy dependencies, complete/cancel/reassign work, make Board decisions, publish/certify evidence, issue final legal conclusions, or alter organization control from this Cockpit intervention form. Those commands remain in their governed operational/authority surfaces.
- 13.16.4 remains responsible for full department workspaces; 13.16.3C is a focused Owner drill-down and intervention-routing layer only.

**Acceptance:** design-foundation **20/20 PASS**; existing 13.16.3B organization read-client regression **1/1 PASS**; governed intervention request-client regression **1/1 PASS**; Next.js 15.2.4 production build **PASS** with **39/39 static pages**; repository policy and release consistency **PASS** at Alembic `0076_organization_position_active_identity`; `git diff --check` **PASS**; runtime smoke **7/7 HTTP 200** across health, Board Packet, Observatory departments, blockers, dependencies, work items, and human-action requests; browser review **PASS** for the `Global Mobility Operations` department drill-down showing the resolved COO owner, three real positions, truthful zero operating-state counts, and no synthetic durable signal. The live preserved database contained no legitimate blocker, dependency, overdue work, or pending human request, so no artificial HumanActionRequest was created merely to exercise the intervention form. The backend/API implementation is unchanged from the accepted **806 passed, 5 skipped, 0 failed** 13.16.3B baseline. No Alembic change, preserved PostgreSQL migration, or Austria safety-boundary change occurred.

**13.16.3C is COMPLETE / PASS. Phase 13.16.3 is COMPLETE / PASS. 13.16.4 Department workspaces is COMPLETE / PASS. 13.16.5 Cross-department dependencies and blockers is UNLOCKED / NOT STARTED.**

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

**Acceptance:** design-foundation **21/21 PASS**; organization read-client **2/2 PASS**; Next.js 15.2.4 production build **PASS** with **39/39 pages** including `/workspace/[department]`; repository policy, migration, and local DB schema **PASS** at Alembic `0076_organization_position_active_identity`; `git diff --check` **PASS**; complete API regression **806 passed, 5 skipped, 0 failed**; runtime smoke **8/8 HTTP 200** across `/health`, Board Packet, Observatory departments, blockers, dependencies, work items, human-action requests, and contributions. The new `/workspace/[department]` page loads a Board Packet, Observatory departments, scoped work, open blockers, active dependencies, pending human requests, Contributions, and material Activity, resolves executive ownership from the organization graph, validates the department against Observatory rows, and reuses the 13.16.3C governed `OrganizationHumanActionRequest` intervention form. It does not resolve/waive blockers, satisfy/waive dependencies, complete/reassign work, make Board decisions, publish/certify evidence, issue legal conclusions, or alter organization control. **13.16.4 is COMPLETE / PASS. 13.16.5 Cross-department dependencies and blockers is COMPLETE / PASS. 13.16.6 Owner decision and escalation inbox is UNLOCKED / NOT STARTED.**

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

**Acceptance:** design-foundation **22/22 PASS**; organization read-client **2/2 PASS** (unchanged from 13.16.4); Next.js 15.2.4 production build **PASS** with **40/40 pages** including `/cross-department-friction`; repository policy, migration, and local DB schema **PASS** at Alembic `0076_organization_position_active_identity`; `git diff --check` **PASS**; complete API regression **806 passed, 5 skipped, 0 failed**; runtime smoke **8/8 HTTP 200** across `/health`, Board Packet, Observatory departments, blockers, dependencies, work items, human-action requests, and contributions. The new `/cross-department-friction` page loads organization-wide work items, open blockers, active dependencies, pending human requests, and material Activity, identifies blockers whose owning department differs from the affected work's department and dependencies where downstream/upstream work belongs to different departments, surfaces human-action status, escalation/overdue signals, the latest durable Activity, deep links into each affected `/workspace/[department]`, and a governed `OrganizationHumanActionRequest` intervention form. It does not resolve/waive blockers, satisfy/waive dependencies, complete/reassign work, make Board decisions, publish/certify evidence, issue legal conclusions, or alter organization control. **13.16.5 is COMPLETE / PASS. 13.16.6 Owner decision and escalation inbox is UNLOCKED / NOT STARTED.**

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

- 13.16.2 through 13.16.5 are COMPLETE / PASS; 13.16.6 Owner decision and escalation inbox is UNLOCKED / NOT STARTED and remains the next product slice, while 13.16.7-13.16.10 remain sequentially gated;
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

### 13.16.2 visual freeze — final Cockpit acceptance correction (2026-08-15)

The premium shell is visually frozen after final local acceptance gates passed. Browser review found two final issues after the signature pass: the six-department Organization Pulse could visually omit peer nodes despite reporting six visible departments, and the honest zero-Activity surface did not yet make the canonical coverage boundary visually legible. The final bounded correction therefore moves department rendering to a deterministic two-row field with data-counted connector buses and converts the Activity empty state into a truthful coverage-boundary instrument. It does not add synthetic organization hierarchy, synthetic Activity, invented jurisdiction data, or new product capability.

The accepted 13.16.2 visual foundation remains: premium compact control rail; deep-ink/warm-ivory Cockpit language; restrained editorial serif + operational sans; data-led command surface; Owner Attention authority state; contextual geographic Global Mobility field; and unified Owner Control Dock. Further visual work in 13.16.3 must be driven by live Owner capability and interaction rather than another shell redesign.

### 13.16.2 visual-freeze amendment — executive authority hierarchy (2026-08-15)

Final Owner review identified one remaining structural omission in Organization Pulse: the premium Cockpit was visually flattening active L3 officers such as CTO and CISO into department totals instead of showing the executive-authority layer that already exists in the canonical organization runtime. The visual freeze is therefore amended once, without changing authority semantics or creating positions.

Organization Pulse now derives active executive leadership strictly from current `OrganizationPosition` rows where `reports_to_position_key == "ceo"` and `authority_level == "L3"`. Present officers (for example COO, CTO, CISO, CPO, CFO, CLO, CMO, CCO, or CHRO) render only when they actually exist in the Board Packet. Operational domains are derived from the remaining active organization positions and resolve their executive portfolio by walking the existing `reports_to_position_key` chain; unresolved ownership is shown explicitly rather than invented.

The Owner hierarchy presented by the Cockpit is therefore: **Human Board → CEO → active L3 executive leadership → operational domains → governed AIOS execution**. This is a read-only visualization of the existing organization graph. It does not create CTO/CISO or any other officer, alter delegations, change authorization, repair governance records, reconstruct Activity, or expand autonomous authority. Local browser acceptance and the full 13.16.2 gates passed; this hierarchy is now part of the frozen premium foundation and 13.16.3 returns to live Owner capability rather than shell redesign.

### 13.16.2 visual-freeze usability amendment — discoverable compact navigation (2026-08-15)

Owner review rejected an icon-only rail with no immediate name discovery as impractical. The premium control rail therefore remains compact and spatially stable, but every desktop rail control exposes its real product name on hover and keyboard focus through a floating label outside the 88px rail. This preserves Cockpit canvas space without requiring users to memorize glyphs or restoring the earlier full-rail hover expansion that masked workspace content.

This usability amendment ships together with the executive-authority Organization Pulse refinement in one cumulative patch. The accepted hierarchy remains **Human Board → CEO → active L3 executive leadership → operational domains → governed AIOS execution** and is still derived only from live organization data. Hover labels are presentation-only and do not replace backend authorization, mutate organization state, or change route ownership. Browser acceptance passed; 13.16.2 is frozen and 13.16.3 returns to live Owner capability rather than shell redesign.

#### 13.16.2 visual acceptance refinement — dark-mode surface hierarchy

Visual acceptance found that the premium dark theme had become too uniformly dark: the Cockpit canvas, information panels, executive leadership cards, Owner Attention states, and supporting dialog-like surfaces could visually merge. The accepted design direction keeps dark mode as the flagship Cockpit presentation but requires an explicit luminance/elevation hierarchy: the page canvas remains the deepest level; primary Cockpit surfaces are visibly lifted; executive and status/dialog surfaces receive a further restrained elevation step; and borders/highlights remain subtle but discoverable. This refinement is presentation-only and does not alter authority, organization state, durable Activity semantics, intelligence meaning, or safety controls.

#### 13.16.2 acceptance correction — 0075 architecture boundary + warning-clean build

The first complete API acceptance rerun after the premium visual freeze reached **790 passed, 5 skipped, 1 failed**. The sole failure was a stale architecture-boundary assertion in `test_openapi_and_phase_architecture_boundaries` that still prohibited any `0075` migration even though `0075_legacy_schema_reconciliation` is now the accepted, data-preserving local-schema reconciliation head. The correction now requires that exact 0075 migration and continues to fail if any numbered migration later than 0075 appears, preserving the phase boundary rather than weakening it.

The same acceptance run produced a successful Next.js 15.2.4 production build with all **39/39 static pages** generated, but Autoprefixer reported one mixed-support warning for `align-items: end` in the new Organization Pulse layer heading. The bounded correction uses `flex-end` for that selector only. No runtime API behavior, authorization, organization state, Activity semantics, intelligence meaning, governance, publication, Austria safety state, or database contents change. The corrected architecture boundary and production build passed, and the complete API rerun closed at **791 passed, 5 skipped, 0 failed**.

### 13.16.2 closure acceptance — COMPLETE / PASS (2026-08-15)

Phase 13.16.2 is closed from baseline `4e6aaa5b372a0cd4171d1199fb0315961eb691f6`. The accepted experience foundation establishes **Global Mobility AIOS Cockpit** as the Owner / Board control experience, keeps **Board Room** as a module inside Cockpit, preserves `/` as the Professional / Operator Operations shell, adds `/my-mobility` as the Mobility User shell, and retains `/portal` as the secure token-bound case-data surface. Navigation remains presentation context only; server authorization remains authoritative.

The visual foundation is frozen at the accepted premium direction: warm ivory plus layered deep-ink/graphite themes; selective editorial serif plus operational sans; fixed compact control rail with discoverable hover/focus names; data-led Cockpit composition; Owner Attention; contextual Global Mobility Pulse; explicit durable-Activity coverage presentation; and the live read-only authority hierarchy **Human Board → CEO → active L3 executive leadership → operational domains → governed AIOS execution**. Final browser evidence showed **9 active L3 officers** and **10 operational domains** from the current Board Packet; the UI does not create or infer missing officers.

Closure evidence: migration regression **6 passed**; design-foundation **16 passed**; request/auth **4 passed**; complete API **791 passed, 5 skipped, 0 failed**; Next.js 15.2.4 production build **PASS** with the accepted route set and captured **39/39 static pages**; repository policy **PASS**; release consistency **PASS** at `0075_legacy_schema_reconciliation`; physical preserved-SQLite parity **PASS** with 118 registered/actual model tables and only `alembic_version` as infrastructure; `git diff --check` **PASS**; and runtime smoke **5/5 HTTP 200** across `/health`, WorkItems, Decisions, Board Packet, and CRM summary. The remaining Starlette/httpx warning is a known test-client deprecation warning and is not a 13.16.2 functional failure.

`0075_legacy_schema_reconciliation` remains the forward, data-preserving compatibility repair that restored the preserved developer SQLite schema; `0076_organization_position_active_identity` now enforces durable OrganizationPosition identity uniqueness after the data-preserving Board duplicate reconciliation. Neither migration authorizes historical Activity reconstruction, weakens review gates, changes Austria publication/certification state, or migrates the preserved PostgreSQL environments. Phase **13.16.3 Unified Owner Control Center is COMPLETE / PASS** through **13.16.3C**. Interactive executive/domain focus, an authority-correct Owner queue, capability architecture, Technology + Security, Tier-1 Global Mobility Operations + Intelligence + Legal/Regulatory, active-position identity integrity, Operational Intelligence, department drill-down, and governed human-follow-up routing are accepted. The preserved organization remains **61 active rows / 61 distinct active identities / zero duplicates** at Alembic 0076, and no direct blocker/dependency/work/legal-outcome authority was added to Cockpit. **Phase 13.16.4 Department workspaces is COMPLETE / PASS: the Cockpit drill-down now deep-links into `/workspace/[department]` as a bounded operational unit with owned work, blockers, dependencies, human requests, Contributions, material Activity, executive ownership, and governed intervention, without resolving, waiving, completing, reassigning, publishing, certifying, or altering organization control. Phase 13.16.5 Cross-department dependencies and blockers is COMPLETE / PASS: the Owner control surfaces now expose `/cross-department-friction` with organization-wide cross-department blockers and dependencies, human-action indicators, escalation/overdue signals, durable Activity, deep links into each affected department workspace, and the same governed intervention form, without direct blocker/dependency/work/legal-outcome mutation. 13.16.6 Owner decision and escalation inbox is UNLOCKED / NOT STARTED.**

### 13.16.3A.1 organization capability architecture — planning contract (2026-08-16)

- Added a planning-only capability registry covering the current nine-officer executive council plus 49 target capability domains across Technology, Security, Operations, Global Mobility Intelligence, Product, Legal, Finance, Marketing, Communications, People, and future Board assurance.
- The registry maps every current non-executive foundation position, proposes missing capabilities without registering them, and flags overlapping legacy positions for review rather than deletion.
- Added a read-only capability-audit command to reconcile the code-defined 34-position foundation with the live preserved developer organization before any mutation; it must report `runtime_mutation_performed=false`.
- Explicitly kept CISO independent from CTO, rejected premature CIO/CRO expansion, and made COO operational owner of Global Mobility Intelligence with CLO as regulatory/legal governance partner.
- Live audit completed with 34 active positions matching all 34 foundation specs, no extras/missing keys, 7 focused tests PASS, repository policy PASS, release consistency PASS, and no runtime mutation. The earlier browser count was not used as a mutation basis.

### 13.16.3A.2 Technology + Security foundation tranche 1 — implementation contract (2026-08-16)

- Promoted exactly 13 previously planned Technology/Security capability slots into `POSITION_SPECS`, expanding the code foundation from 34 to 47 positions while keeping the existing nine-officer executive council unchanged.
- Added nine CTO-side capability slots across Application Engineering, Platform & Reliability, Quality Engineering, Data & AI Engineering, and Architecture/Engineering Enablement; added four CISO-side slots for AppSec, IAM, Security GRC, and vulnerability management.
- New capability slots are intentionally **non-executable**: no runtime adapter/role card, no delegated or direct action authority, no external action authority, no self-approval, and explicit prohibited authority. Existing CTO/CISO executable delegation sets are unchanged.
- Added focused regression coverage for additive foundation registration, reporting lines, non-executable contracts, and unchanged executable delegation sets. Updated the capability architecture so these 13 keys are `existing`, leaving 33 planned positions and the five legacy review items unchanged.
- Added `scripts/apply_organization_foundation_tranche.py`, a guarded SQLite-only preflight/apply helper that refuses unrelated drift, requires the existing global OrganizationControl, backs up the preserved DB before mutation, and performs only additive foundation registration with audit records.
- No Alembic/schema migration, Activity reconstruction, work/decision backfill, publication/certification change, Austria safety change, PostgreSQL mutation, or autonomous-authority expansion is included. Controlled preserved-SQLite application and browser acceptance are recorded in the checkpoint closure below.

### 13.16.3A / A.1 / A.2 checkpoint closure — COMPLETE / PASS (2026-08-16)

The first Unified Owner Control Center checkpoint is accepted from immutable baseline `a6ab946748b80430502d0f21108187913b4ed7ca`. 13.16.3A makes the premium Cockpit interactive and authority-correct; A.1 establishes the machine-readable organization capability architecture and reconciles the preserved live foundation at 34/34 without mutation; A.2 additively establishes the first Technology + Security capability tranche and closes at 47/47 live positions.

Acceptance evidence: design-foundation **18/18 PASS**; request/auth **4/4 PASS**; Next.js production build **PASS** with **39/39 static pages**; focused organization tranche regressions **11/11 PASS**; complete API **801 passed, 5 skipped, 0 failed**; preserved SQLite physical schema and migration checks **PASS** at `0075_legacy_schema_reconciliation`; repository policy, release consistency, and `git diff --check` **PASS**; runtime smoke **5/5 HTTP 200** for the critical Owner-read surfaces; post-apply organization audit **47 foundation / 47 live / zero extra / zero missing**. Browser review confirmed **9 executives, 19 operational domains, 45 downstream positions**, expanded CTO/CISO portfolios, and no synthetic Owner authority or Activity. The 13 newly registered Technology/Security capability slots remain non-executable with empty delegated/direct action authority, no self-approval, and unchanged existing CTO/CISO executable delegation sets.

**13.16.3A.3, 13.16.3A.3R, 13.16.3B, 13.16.3C, 13.16.4, and 13.16.5 are COMPLETE / PASS.** The Tier-1 Global Mobility Operations + Intelligence + Legal/Regulatory foundation is live at 61/61 active OrganizationPosition identities; the duplicate Board row was preserved as suspended historical `board@v2`, the canonical `board@v1` remains active, Alembic 0076 is accepted, and row/identity counts converge. Cockpit now combines Operational Intelligence with selected-domain department drill-down and governed human-follow-up routing; that drill-down deep-links into bounded `/workspace/[department]` operational units with owned work, blockers, dependencies, human requests, Contributions, material Activity, resolved executive ownership, and the same governed intervention form; and the Owner control surfaces now include `/cross-department-friction`, surfacing blockers and dependencies whose owning department differs from the affected department, with human-action indicators, escalation/overdue signals, durable Activity, workspace deep links, and governed intervention. All surfaces preserve truthful zero states, backend authorization, and the prohibition on direct blocker/dependency/work/legal-outcome mutation. **13.16.6 Owner decision and escalation inbox is UNLOCKED / NOT STARTED.**

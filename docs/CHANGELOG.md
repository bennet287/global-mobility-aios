# Global Mobility AIOS — Active Changelog

This is the current changelog from the post-`f0688a8` baseline onward. The complete historical changelog through the sealed Phase 13.16.7 baseline remains preserved at [archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md](archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md). Git history preserves the exact previous versions of this active changelog.

---

## 2026-08-19 — Human-Like Agent Organization Architecture V1 — CANONICAL DOCS CHECKPOINT / PUSHED

### Purpose

Expanded Technology Radar V1.1 from a capability-provider list into a concrete architecture direction for a **human-like, high-performance Global Mobility AIOS organization**.

The target is:

> **Human in interaction. Machine-like in reliability.**

Permanent principles added/frozen:

- **Natural interaction, deterministic accountability.**
- **Team outcomes over agent competition.**
- **Activity is broad; authority is narrow.**
- **Autonomy is earned and measured through quality, SLA performance, governed outcomes, and bounded authority.**
- **Results matter more than provider competition, while AIOS Semantic Sovereignty remains non-negotiable.**

### Canonical architecture document

Created:

- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md`

Architecture commit:

- `f7216c523c3de96a15eeb7c8d6698b62b52934e4` — `docs: define human-like agent organization architecture`

The document defines:

- Human Owner / Board → Cockpit → AI CEO → Organization OS → Agent Organization Fabric → AIOS Execution Broker → finished work → governed outcome → Learning & Quality;
- Munder Difflin + OpenWorker as complementary, not competing, A+ references;
- Mission above WorkItems;
- Dynamic Squads;
- natural agent-to-agent communication;
- `AgentMessage ⊂ OrganizationActivity`;
- AgentConversation;
- distributed/proportional human intervention;
- Session → Position → Department → Organization memory scopes;
- AgentRelationship;
- Capability Registry;
- SLA contracts;
- KPI / OKR semantics;
- Definition of Done;
- peer review before unnecessary human escalation;
- progressive intervention / circuit breaker;
- workload/capacity management;
- organizational rituals;
- organizational learning;
- Live Organization / Cockpit direction;
- implementation waves 5A–5E.

### Munder Difflin + OpenWorker architecture decision

**Munder Difflin (`chaitanyagiri/munder-difflin`) remains A+** as the principal architecture/reference direction for:

- persistent agent identities;
- agent-to-agent messages/mailboxes;
- conversations;
- long-term/shared working memory;
- supervisor/orchestrator patterns;
- dependency-aware coordination;
- scheduled missions / heartbeat;
- human intervention;
- budget/cost telemetry;
- OpenTelemetry;
- progressive circuit breakers;
- skills/capability discovery;
- live organization visualization.

**OpenWorker (`andrewyng/openworker`) remains A+** as the principal finished-work/Coworker reference for:

- real deliverables;
- files/terminal/tools;
- MCP;
- connectors;
- scheduled work;
- external actions;
- model portability;
- consequential-action approvals;
- unattended approval inbox patterns;
- local-first coworker execution.

AIOS does not choose a framework winner merely for architectural neatness when complementary capabilities produce better governed outcomes.

A new conceptual **AIOS Execution Broker** owns capability composition using AIOS-defined criteria such as capability, authority, SLA, workload, evidence requirements, human-review requirements, historical quality, rework/correction rate, provider health, privacy/data-use, cost, and fallback availability.

### OrganizationActivity correction

The architecture now explicitly records:

```text
AgentMessage ⊂ OrganizationActivity
```

Natural conversation is legitimate organizational activity, including questions, clarifications, requests, suggestions, handoffs, warnings, peer review, acknowledgements, disagreements, and routine coordination.

The authority boundary remains strict:

```text
conversation ≠ authority
message ≠ ExecutiveDecision
memory ≠ Evidence
memory ≠ VerifiedRule
provider event log ≠ canonical AIOS OrganizationActivity automatically
```

Provider-native events/messages are normalized into AIOS-owned semantics where appropriate.

### Human intervention / authority

The escalation principle is now explicit:

> **Resolve autonomously where permitted. Collaborate before escalating. Escalate to the lowest level with the necessary expertise or authority. Reserve Board attention for genuinely Board-level matters.**

Board Room remains a reserved-authority module inside Cockpit rather than a generic human-review inbox.

### Performance model

Added first-class architecture direction for:

- **SLAs** — acknowledge/start/respond/complete/review/freshness/escalation/blocker-age semantics;
- **KPIs** — delivery, quality, collaboration, economics, safety/governance, human effort;
- **OKRs** — strategic improvement above operational KPIs;
- **Definition of Done** — explicit completion criteria for material Missions.

Individual metrics are diagnostic. **Team/Mission outcome is the primary performance unit.**

### Progressive intervention

Target intervention ladder:

```text
NORMAL
→ STEER
→ ASSIST / PEER SUPPORT
→ REASSIGN
→ CONSTRAIN
→ SUSPEND SPECIFIC AGENT / CAPABILITY
→ EXECUTIVE / HUMAN ESCALATION
→ EMERGENCY ORGANIZATION STOP
```

This supports the Phase 13.17 human finding that `Pause Organization` must not appear to be a normal troubleshooting fallback.

### Technology Radar synchronization

Updated:

- `docs/TECHNOLOGY_RADAR_V1_1.md`
- commit `370244064a59c147ba9043f758307f403747ae5c` — `docs: expand Technology Radar for human-like agent organization`

Key Radar updates:

- accepted product baseline corrected to sealed Phase 13.16.10;
- active product slice corrected to owner-led Phase 13.17 IN PROGRESS / PAUSED;
- Munder Difflin added as A+ Agent Organization Fabric reference;
- OpenWorker retained as complementary A+ Coworker/finished-work reference;
- Qdrant promoted to A benchmark against pgvector;
- Execution Broker added;
- Mission / Dynamic Squad / AgentConversation / Activity semantics added;
- SLA/KPI/OKR/Definition of Done added;
- progressive intervention and Live Organization added;
- Wave 5 split into 5A–5E;
- Wave 1 marked COMPLETE;
- Wave 2 recorded IN PROGRESS with Docling started and Presidio next;
- Learning & Quality made continuous.

### Third-party boundary synchronization

Updated:

- `docs/THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md`
- commit `5a5b0e9f89f7dd62c7193fb3ff6926d771072152` — `docs: align platform boundaries with agent organization fabric`

The principles now explicitly protect AIOS ownership of Mission, WorkItem, AgentConversation, canonical OrganizationActivity, Capability Registry, SLA/KPI/OKR, Definition of Done, authority and evidence while allowing external providers to supply communication, memory, orchestration, execution, tools, connectors, schedules, budgets, circuit breakers and visualization behind AIOS-owned contracts.

### ROADMAP synchronization

Updated:

- `docs/ROADMAP.md`
- commit `11a82c0fad8ba6d4fa177ce7b877aec0343a5514` — `docs: align roadmap with human-like agent organization architecture`

The active roadmap now records:

- Phase 13.17 as owner-led human acceptance IN PROGRESS / PAUSED, not independent external validation;
- Wave 1 COMPLETE;
- Wave 2 Docling STARTED / Presidio next;
- Munder + OpenWorker complementary A+ direction;
- AIOS Execution Broker;
- Mission, squads, conversations/activity, memory, relationships, capabilities;
- SLA/KPI/OKR/Definition of Done;
- Wave 5A–5E implementation gates;
- Live Organization and organizational learning;
- no automatic Wave 5 runtime adoption.

### Boundary / acceptance truth

This architecture checkpoint is **docs-only**.

It does **not**:

- install Munder Difflin;
- install OpenWorker;
- start Temporal/OpenFGA/Pydantic AI/Qdrant runtime work;
- add a Mission/Conversation/SLA/KPI database model yet;
- add migrations/tables;
- change backend authorization;
- change evidence/certification/publication semantics;
- mutate the preserved database;
- change frontend runtime behavior;
- mark Phase 13.17 PASS;
- resolve any Phase 13.17 O-/P- finding merely through documentation.

No complete API regression, Next.js build, design regression, browser acceptance, database checker, or local repository seal was rerun by these direct GitHub documentation writes. The latest accepted runtime evidence remains the immediately preceding Docling pilot acceptance below and is **carried forward, not represented as rerun**.

No GitHub CI PASS is claimed by this checkpoint.

---

## 2026-08-19 — Technology Radar V1.1 Wave 2 Docling pilot STARTED — optional document normalization

- Added bounded, optional, disabled-by-default `apps/api/app/services/docling_adapter.py`.
- Integrated Docling into the existing document extraction pipeline with safe fallback to the existing extraction stack when disabled/missing/failing.
- Added `DOCLING_ENABLED`, disabled by default.
- Added `docling>=2.15.0` to `apps/api/requirements-ai.txt` rather than the core API dependency set.
- Added regression coverage for disabled, missing-package, success, conversion failure and result serialization/truncation.
- Preserved the Document Intelligence Boundary: Docling normalization is not authenticity, legal sufficiency, evidence validity or authority.

### Acceptance

- Docling adapter regression: **6/6 PASS**;
- document intelligence regression: **5/5 PASS**;
- complete API regression: **873 passed / 5 skipped / 0 failed**;
- repository policy: **PASS**;
- release consistency: **PASS** at `0076_organization_position_active_identity`;
- Docker production profile: **PASS**;
- database migration/schema consistency: **PASS**;
- local physical-schema parity: **118 registered / 118 actual model tables / 119 physical including `alembic_version`**;
- Next.js 15.2.4 production build: **41/41 PASS**;
- design foundation: **28/28 PASS**;
- preserved `gmai.db`: unchanged.

**Presidio remains the next queued Wave 2 pilot.**

---

## 2026-08-19 — Technology Radar V1.1 Wave 1 ClamAV pilot COMPLETE / PASS

- Added optional disabled-by-default ClamAV upload malware scanning.
- Infected uploads are rejected before storage.
- Scanner unavailability remains policy-controlled and safe by default for local development.
- A clean malware scan is an engineering safety signal, not evidence authenticity/legal validity.

### Acceptance

- malware-scan regression: **11/11 PASS**;
- document-upload regression: **2/2 PASS**;
- complete API regression: **867 passed / 5 skipped / 0 failed**;
- repository/release/Docker/database/schema checks: **PASS**;
- Next.js build: **41/41 PASS**;
- design foundation: **28/28 PASS**;
- preserved `gmai.db`: unchanged.

Wave 1 (`Promptfoo + OpenTelemetry + ClamAV`) became **COMPLETE** at this checkpoint.

---

## 2026-08-19 — Technology Radar V1.1 Wave 1 OpenTelemetry pilot COMPLETE / PASS

- Added optional disabled-by-default FastAPI/OpenTelemetry instrumentation and OTLP export.
- Missing packages/configuration degrade safely without preventing API startup.
- OpenTelemetry remains engineering trace only and does not replace OrganizationActivity, AuditLog, evidence provenance or authority.

### Acceptance

- telemetry regression: **3/3 PASS** with environment-dependent SDK skip recorded;
- complete API regression: **856 passed / 5 skipped / 0 failed**;
- repository/release/Docker/database/schema checks: **PASS**;
- Next.js build: **41/41 PASS**;
- design foundation: **28/28 PASS**;
- preserved `gmai.db`: unchanged.

---

## 2026-08-19 — Technology Radar V1.1 Wave 1 Promptfoo pilot COMPLETE / PASS

- Added bounded deterministic Promptfoo role-card safety evaluation under `eval/promptfoo/`.
- Added matching pytest safety invariants so the standard API gate retains the AIOS-owned safety contract independently of Promptfoo installation.
- Role-card invariants cover human review/oversight, no regulated-outcome guarantees, legal-advice boundary, source/provenance awareness and explicit blocked actions/prohibitions.
- Promptfoo remains evaluation tooling, never production authority.

### Acceptance

- role-card safety regression: **42/42 PASS**;
- Promptfoo evaluation: **40/40 PASS**;
- complete API regression: **853 passed / 5 skipped / 0 failed**;
- repository/release/Docker/database/schema checks: **PASS**;
- Next.js build: **41/41 PASS**;
- design foundation: **28/28 PASS**;
- preserved `gmai.db`: unchanged.

---

## 2026-08-18 — Phase 13.17 owner-led human acceptance CHECKPOINT / PAUSED

- Began genuine human-use acceptance against the sealed Phase 13.16.10 local application.
- The evaluator is the product Owner; therefore this is **owner-led human acceptance, not independent third-party validation**.
- Preserved unbiased scenario testing before explaining intended semantics.
- Recorded Owner/Board findings O-01 through O-12 and Professional findings P-01/P-02.
- Major themes include evidence/governance terminology, global-pause mental model, role separation, icon-only navigation, professional next-action clarity and decision-context wording.
- No finding was marked fixed simply because intended semantics were explained after testing.
- Evaluation paused after Professional Task 1; resume point is Professional Task 2.

Durable checkpoint:

- `docs/PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md`
- checkpoint commit `24aa74109c749a2752c08eaca007917978eb1bcd`

Phase 13.17 remains **IN PROGRESS / PAUSED**, not PASS.

---

## 2026-08-18 — Phase 13.16.10 COMPLETE / PASS — responsive, accessibility and integrated role acceptance

- Added mobile navigation focus containment, Escape/focus-return semantics and scroll containment.
- Strengthened secure Portal loading/error/accessibility semantics without changing token/device-bound authorization.
- Strengthened focus visibility, touch targets and narrow-screen resilience.
- Human visual review found and corrected two real mobile composition defects in Cockpit and Operations before seal.

### Acceptance

- design foundation: **28/28 PASS**;
- request/auth: **4/4 PASS**;
- Next.js 15.2.4 build: **41/41 PASS**;
- repository/release/Docker/database/schema checks: **PASS**;
- complete API regression: **811 passed / 5 skipped / 0 failed**, carried forward for the frontend/test-only boundary;
- integrated browser semantic/keyboard verifier: **PASS**;
- corrected mobile geometry/human visual review: **PASS**;
- preserved `gmai.db` SHA256 `23FC012AF3FA89804A84A9C8DD75C0C68515B23AEF1813CC5460D6D73808CD31`: unchanged.

Seal commit:

- `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`
- `feat: complete integrated role experience acceptance`

No GitHub CI status is implied by these local acceptance results.

---

## 2026-08-18 — Phase 13.16.9 COMPLETE / PASS — Evidence and provenance UX consolidation

- Added one shared presentational evidence/provenance grammar across Professional Case, Pathway Catalogue, Independent Source Review and Document Intelligence.
- Preserved distinctions among official source, snapshot, human/source review, VerifiedRule, pathway evidence, case evidence, historical/superseded state and unresolved gaps.
- Preserved context-alignment rules from 13.16.8 and backend publication/certification authority.

### Acceptance

- design foundation **26/26 PASS**;
- request/auth **4/4 PASS**;
- Next.js build **41/41 PASS**;
- repository/release/Docker/database/schema checks **PASS**;
- complete API regression **811 passed / 5 skipped / 0 failed** carried forward for the frontend-only boundary;
- human visual review of four evidence-heavy surfaces **PASS**;
- automated semantic verifier **not claimed PASS** because of settled-DOM harness false negatives;
- preserved database unchanged.

Seal commit:

- `c97b2189e94a6753ab902dd192bbd5b2e41073d0`

---

## 2026-08-18 — Phase 13.16.8 COMPLETE / PASS — Governed Professional / Operator experience

- Refined the existing Operations and native case workspace instead of creating a parallel Professional dashboard.
- Restored Eligibility as a first-class Professional navigation destination.
- Established the professional reading order: context → blockers/uncertainty → governed next actions → evidence/review → technical provenance.
- Persisted PathwayComparison remains the current-decision anchor; mismatched/historical records stay inspectable but cannot silently influence current blockers/readiness.
- Opening a case remains read-only with respect to eligibility evaluation, pathway comparison generation, timeline activation, evidence certification and authority submission.

### Acceptance

- design foundation **25/25 PASS**;
- request/auth **4/4 PASS**;
- Next.js build **41/41 PASS**;
- repository/release/Docker/database/schema checks **PASS**;
- complete API regression **811 passed / 5 skipped / 0 failed**;
- browser/runtime acceptance across aligned, mismatch and sparse/uncertain cases **PASS**;
- preserved database unchanged.

Seal commit:

- `2dc3637820f6fdbb75628e2632a07bdbe336aa19`

---

## 2026-08-18 — Technology Radar V1.1 original platform-evolution architecture checkpoint

- Promoted `TECHNOLOGY_RADAR_V1_1.md` as the active Radar while freezing V1 as historical evidence.
- Established strategic-fit tiers and provider-neutral adoption principles.
- Added OpenWorker as the initial A+ AIOS Coworker reference.
- Added Internal Learning & Quality, correction-learning, training/evaluation lineage and `AIOSDataUsagePolicy` direction.
- Preserved EU-compliance-aware lawful-learning boundaries.
- Established Radar waves without automatically installing candidates.

The 2026-08-19 Human-Like Agent Organization checkpoint above **extends** this V1.1 direction with Munder Difflin, Execution Broker, human-like organization semantics, SLA/KPI/OKR discipline, Live Organization and Waves 5A–5E. It does not invalidate the original semantic-sovereignty boundary.

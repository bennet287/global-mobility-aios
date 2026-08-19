# Global Mobility AIOS

> **A governed, transparent, high-autonomy digital organization for global mobility.**

Global Mobility AIOS is being built as an AI-operated professional organization for the movement of people, talent, families, businesses, and capital across borders.

It combines global-mobility intelligence, case/work orchestration, official-source evidence, document intelligence, persistent AI employees, governed execution, organizational memory, human professional review, and Human Owner / Board oversight inside one auditable operating environment.

The project is deliberately more ambitious than an immigration chatbot, CRM with AI, workflow-automation product, multi-agent demo, generic SaaS admin panel, or agent framework wrapped in a UI.

The active architecture direction is:

> **Global Mobility AIOS V1.3 — High-Autonomy Organization + Organizational Immune System + Earned Autonomy + Board Transparency & Decision Lineage.**

The central operating philosophy is:

> **The safety infrastructure exists to enable autonomy, not suppress it.**

> **Board by exception. Transparency by default.**

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

---

## Current Development Line

Active development now continues on:

```text
roadmap/global-mobility-aios-v12
```

V12 was created directly from the frozen V11 checkpoint:

```text
roadmap/global-mobility-aios-v11
└── dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
    └── roadmap/global-mobility-aios-v12
```

**V11 is intentionally preserved as a frozen architecture/recovery/reference checkpoint.**

All new V1.3 implementation work should proceed on V12 unless an explicit decision says otherwise.

The V12 branch transition itself is recorded in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

---

## 1. What We Are Building

Global Mobility AIOS aims to operate the complete global-mobility lifecycle as one connected professional system:

```text
Human / Business Goal
        ↓
Profile + circumstances + constraints
        ↓
Mobility strategy
        ↓
Country / pathway discovery
        ↓
Eligibility + alternatives
        ↓
Evidence requirements + collection
        ↓
Official rules + regulatory intelligence
        ↓
Risk + cost + timeline + dependencies
        ↓
Document preparation + consistency
        ↓
Professional review where required
        ↓
Application / filing preparation
        ↓
Human / Board authority where required
        ↓
Submission / external action
        ↓
Authority response
        ↓
Remediation / follow-up
        ↓
Post-arrival / relocation / compliance
        ↓
Renewal / status progression
        ↓
Permanent residence
        ↓
Citizenship / business / investment /
long-term global mobility strategy
```

The long-term objective is not simply to answer global-mobility questions. AIOS should increasingly be capable of **performing the organizational work required to reach reliable mobility outcomes**.

That includes:

- profile and case intake;
- pathway discovery and comparison;
- eligibility reasoning;
- official-source research;
- Evidence and provenance management;
- regulatory intelligence;
- document preparation and validation;
- blocker/dependency management;
- application preparation;
- professional review;
- authorized external execution;
- authority-response handling;
- post-arrival and renewal work;
- long-term residence/citizenship strategy;
- organizational learning from outcomes.

---

## 2. What Global Mobility AIOS Is Not

The project should not collapse into any one of the following:

- a visa chatbot;
- a study-abroad search site;
- an immigration CRM;
- a document uploader;
- a recommendation engine;
- a collection of independent AI agents;
- a generic AI company operating system;
- an approval queue where humans supervise every AI action;
- an autonomous legal/tax/investment decision-maker without the required professional or human authority.

Global Mobility specialization remains the product anchor. General organizational capabilities should emerge from solving real global-mobility work well, not replace that domain focus.

---

## 3. Human Authority Model

The **Human Owner / Board is the supreme authority** of Global Mobility AIOS.

Supreme authority does not mean routine operational involvement.

The intended hierarchy is:

```text
                 HUMAN OWNER / BOARD
                   SUPREME AUTHORITY
                          │
               Constitution / Strategy
               Reserved Powers / Limits
                          │
                          ▼
                       AI CEO
                 Operational Executive
                          │
             ┌────────────┼────────────┐
             │            │            │
       Department     Department    Department
          Head           Head          Head
             │            │            │
       Specialists   Specialists   Specialists
             │            │            │
             └────────────┼────────────┘
                          │
                    AI Workforce
```

The Board defines:

- organizational constitution;
- strategy;
- reserved powers;
- authority ceilings;
- autonomy policy;
- legal/policy human-review floors;
- risk tolerance;
- major organizational changes;
- executive authority.

Normal healthy work should happen below the Board.

> **The Board governs the organization; it does not manually operate it.**

---

## 4. Board by Exception

The Board should not routinely approve:

- internal research;
- routine case analysis;
- agent collaboration;
- document drafting;
- Evidence extraction;
- WorkItem updates;
- normal scheduling;
- low-risk tool usage;
- ordinary retries;
- routine bounded operational decisions.

The Board should primarily become involved in:

- constitutionally reserved actions;
- government submissions where human authority is required;
- major legal/regulatory commitments;
- exceptional financial commitments;
- major policy changes;
- critical autonomy expansions;
- unresolved high-risk contradictions;
- critical incidents;
- major strategic/executive decisions.

AIOS should perform as much preparation as possible before a Board decision is requested.

The target experience is:

```text
AI organization researches
        ↓
Evidence verified
        ↓
Application / action prepared
        ↓
Independent verification where required
        ↓
Pre-mortem / policy checks
        ↓
READY
        ↓
Human Board
[Approve] [Modify] [Return] [Submit]
```

> **AIOS does the work. The Board makes the important decisions.**

---

## 5. Board Transparency

High autonomy must never create organizational opacity.

The Board should have on-demand visibility into relevant:

- agent-to-agent conversations;
- delegation chains;
- decisions and recommendations;
- Evidence and SourceSnapshots;
- VerifiedRules;
- tool usage;
- external actions;
- policy decisions;
- contradictions;
- escalations;
- incidents and circuit breakers;
- autonomy promotions/downgrades;
- execution history;
- learning outcomes.

This is a transparency right, not a requirement to watch everything continuously.

```text
Board visibility ≠ Board interruption
```

Cockpit should summarize healthy operation while preserving drill-down:

```text
Organization
→ Department
→ Mission
→ Case
→ WorkItem
→ Agent
→ Conversation
→ Decision
→ Evidence / Rule / Tool Action
→ Final Outcome
```

---

## 6. Decision Lineage

Every material decision should eventually be reconstructable.

Example:

```text
FINAL ELIGIBILITY STATE
        ▲
EligibilityTransition
        ▲
Command Gateway Authorization
        ▲
Independent Verification
        ▲
Agent Recommendation
        ▲
Evidence
        ▲
VerifiedRules
        ▲
SourceSnapshots
        ▲
Official-source Research / Tool Actions
```

Relevant collaboration should also be reconstructable:

```text
Question raised
      ↓
Agent collaboration
      ↓
Missing Evidence identified
      ↓
Evidence collected
      ↓
Contradiction resolved
      ↓
Recommendation
      ↓
Verification
      ↓
Decision
```

Structured decision rationale is the governance artifact. Hidden model chain-of-thought is not the audit mechanism.

---

## 7. AI Employees, Not Stateless Prompts

AI workers are intended to become persistent organizational employees with durable identity and continuity.

An employee model may include:

```text
Agent Identity
│
├── Position
├── Department
├── Manager
├── Responsibilities
├── Expertise
│
├── Missions
├── WorkItems
├── Assigned cases
│
├── Working memory
├── Long-term memory
├── Organizational memory access
├── Relationships
├── Previous decisions
│
├── Tools
├── Connector permissions
├── Data permissions
├── Authority profile
├── Autonomy profile
├── Budget
│
├── Performance history
├── Quality history
├── Incident history
└── Learning history
```

The accepted organization foundation already includes persistent `OrganizationPosition` identities and an explicit reporting structure.

Current accepted organization facts include:

- 61 active `OrganizationPosition` identities;
- zero duplicate active position keys after active-identity reconciliation;
- 9 L3 executive roles beneath the CEO;
- 26 operational domains;
- 59 positions downstream of the CEO;
- capability-only positions that remain non-executable until explicitly authorized;
- preserved Human Board and CEO governance;
- bounded executive delegation rather than title-based authority.

The active-identity contract is enforced at Alembic revision:

```text
0076_organization_position_active_identity
```

---

## 8. Memory Is Not Truth

AIOS should support strong memory without allowing memory to become authoritative truth automatically.

```text
Agent Memory ≠ Canonical AIOS Truth
```

The model distinguishes:

| Layer | Purpose |
|---|---|
| Working memory | Current reasoning/run |
| Agent memory | Past tasks, conversations and experiences |
| Organizational memory | Shared organizational knowledge |
| Canonical AIOS truth | Governed case facts, Evidence, VerifiedRules and authoritative state |

A consequential decision should refresh important facts against governed current evidence where required.

> **Memory provides continuity. Evidence provides authority.**

---

## 9. Context Broker

Agents should receive the context required for the task, not unrestricted access to all organizational data.

The Context Broker principle is:

> **More relevant truth, not more tokens.**

A future `ContextBundle` may include:

```text
Agent identity
Position / authority
Mission
Current WorkItem
Relevant case facts
Relevant Evidence
Applicable VerifiedRules
Known unknowns
Known contradictions
Relevant previous decisions
Relevant collaboration summary
Allowed tools
Sensitivity profile
Policy version
Context version/hash
```

Additional context should be purpose-scoped and lazy-loaded.

Material `AgentRun` lineage should bind the effective context, model/program versions, tools, policy, authority, Evidence/rule versions, cost, latency and outcome.

---

## 10. Capability, Authority, Autonomy and Risk

V1.3 explicitly separates four concepts:

```text
Capability = what the runtime can technically do
Authority  = what the organization permits
Autonomy   = how independently it may exercise that authority
Risk       = consequence of the specific action
```

Permanent rule:

```text
CAN DO ≠ MAY DO
```

An agent may technically be capable of sending email while being authorized only for specific classes of communication.

---

## 11. Earned Autonomy — A0 to A5

Autonomy is capability-specific, not a single score for an entire agent.

| Level | Meaning |
|---|---|
| A0 | Prohibited |
| A1 | Human executes |
| A2 | AI prepares; approval required |
| A3 | Autonomous with mandatory review |
| A4 | Autonomous with monitoring and valid recovery controls |
| A5 | Fully autonomous bounded operation |

Example:

```text
Austria Immigration Specialist

Official-source research       A5
Document extraction            A5
Evidence assessment            A4
Eligibility assessment         A4
Client explanation             A3
Evidence certification         A2
Government submission          Board / human reserved as required
```

Autonomy should progress through measured performance:

```text
SHADOW
   ↓
RECOMMEND
   ↓
SUPERVISED
   ↓
AUTONOMOUS
   ↓
HIGH-TRUST AUTONOMOUS
```

`AutonomyEvidenceProfile` should use real outcomes such as Evidence grounding, acceptance/modification/rejection, contradiction rate, policy compliance, critical errors, incident outcomes and recovery performance.

Agents cannot self-promote.

---

## 12. Decision Readiness

Decision Readiness is a routing and quality signal, not a substitute for governance.

Potential auditable components include:

- Evidence completeness;
- source authority;
- rule freshness;
- required fact completeness;
- cross-source consistency;
- contradictions;
- historical capability reliability;
- deterministic validation;
- limited agent-confidence metadata.

Permanent rule:

> **Scores route; gates authorize.**

For example:

```text
Readiness 98%
BUT mandatory Evidence missing
→ BLOCK
```

or:

```text
Readiness 100%
BUT action is Board reserved
→ BOARD GATE
```

A scalar score never overrides mandatory Evidence, authority, policy, contradiction, concurrency, verification or human-review requirements.

---

## 13. Risk-Tiered Verification

Governance cost should be proportional to consequence.

| Risk | Typical work | Verification |
|---|---|---|
| R0 | summarization / brainstorming | single agent |
| R1 | routine internal operation | agent + cheap deterministic checks |
| R2 | client-facing preparation | Evidence validation |
| R3 | eligibility/material recommendation | blind independent verification |
| R4 | certification/regulatory publication | independent verification + fresh source validation + appropriate authority |
| R5 | government submission / critical reserved action | full AI preparation + required Human/Board gate |

Independent verification should be genuinely independent: the verifier forms its conclusion before seeing the first agent's answer.

---

## 14. AI-to-AI Escalation

Uncertainty should normally be resolved through the organization before reaching humans.

```text
Specialist
    ↓
Peer Specialist
    ↓
Senior Specialist
    ↓
Department Head
    ↓
AI CEO
    ↓
Human where unresolved or required
```

V1.3 distinguishes:

- **uncertainty escalation** — the organization cannot confidently resolve a problem;
- **authority escalation** — the work may be fully prepared, but the action belongs to a human/Board authority class.

A 99% ready action can still require a Board decision because of authority rather than uncertainty.

---

## 15. Materiality, Canonicalization and Command Gateway

Not every AI action needs maximum governance overhead.

A Materiality Registry should distinguish routine cognition from material organizational action.

Material actions should use a typed governance envelope containing concepts such as:

```text
action_type
actor
subject / aggregate
expected_version
proposed_change
Evidence references
authority context
rationale
Decision Readiness snapshot
risk tier
consequence class
idempotency key
trace identity
```

Agent reasoning can remain flexible.

Canonical truth cannot.

```text
LLM / provider / tool interpretation
        ↓
Typed AIOS candidate
        ↓
Schema validation
        ↓
Deterministic domain checks
        ↓
Evidence / authority / policy checks
        ↓
Canonical result
```

The Command Gateway is the material mutation boundary for autonomous agents.

It is **not** a universal human-approval gateway.

Healthy action should normally be:

```text
Agent
  ↓
MaterialAction
  ↓
Identity / authority / scope
  ↓
Evidence / policy / contradiction
  ↓
Expected-version / idempotency
  ↓
AUTO EXECUTE
```

---

## 16. Organizational Immune System

V1.3 introduces an explicit cross-cutting quality/safety layer:

```text
Organizational Immune System
│
├── Evidence Integrity Monitor
├── Contradiction Detector
├── Anomaly Detector
├── Decision Readiness Engine
├── Capability Performance Monitor
├── Dynamic Autonomy Manager
├── Circuit Breakers
├── Rate / Budget Protection
├── Blast-Radius Controller
├── Incident Detector
├── Root-Cause Classifier
├── Escalation Router
├── Shadow Evaluation Engine
└── Learning Feedback
```

The desired behavior is:

> **Almost invisible during healthy operation; highly capable when abnormal behavior appears.**

The safety system itself must be explainable and Board-inspectable.

---

## 17. Recovery Semantics

Not every action can honestly be rolled back.

V1.3 distinguishes:

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
APPEND_ONLY_CORRECTION
```

Examples:

```text
WorkItem reassignment
→ REVERSIBLE
```

```text
Incorrect external communication
→ COMPENSATABLE
→ send correction
```

```text
Government submission
→ IRREVERSIBLE
→ stronger pre-execution controls
```

```text
Evidence certification later revoked
→ APPEND_ONLY_CORRECTION
```

Recovery semantics belong to consequential commands, not arbitrary database rows.

---

## 18. Performance and Scalability Doctrine

The architecture must not pay maximum governance cost for every action.

### P1 — Pay for risk

Verification effort scales with consequence, uncertainty and novelty.

### P2 — Recompute only what changed

Readiness/Evidence/policy state should be incremental and version-aware.

### P3 — Load only what is needed

Context is purpose-scoped, lazy, composable and versioned.

### P4 — Block only when necessary

Verification modes are distinct:

```text
PRE_COMMIT
POST_COMMIT
BACKGROUND
```

### P5 — Centralize governance, distribute execution

One authority model does not require one global execution mutex.

### P6 — Cache only exact governed state

Verifier reuse must be tied to the relevant Evidence/facts/rules/policy/jurisdiction/effective dates/program/model versions.

### P7 — Instrument from day one

Measure latency, cost, retries, source freshness, verification cost, incident rate, false/missed escalations, Board workload, autonomy rate and transparency lag.

Conceptual rule:

> **Governance Cost ∝ Risk × Uncertainty × Novelty**

---

## 19. Product Surfaces

### Global Mobility AIOS Cockpit

The **Cockpit** is the top-level Human Owner / Board organizational command surface.

It should answer:

> **Is the organization healthy, effective, transparent, and operating within the authority granted to it?**

The target Cockpit includes:

```text
Cockpit
│
├── Organization
├── Missions
├── Agents
├── Performance
├── Quality
├── Risk
├── Incidents
├── Autonomy
├── Transparency
├── Search / Intelligence
└── Board Room
```

### Board Room

**Board Room is a module inside the Cockpit**, not the name of the entire Owner experience.

It is reserved for genuinely Board-level decisions, strategy, reserved authority, critical incidents, major autonomy/policy decisions and executive escalation.

### Operations

The professional/operator experience converges cases, Evidence, provenance, reviews, next actions, deadlines, blockers, specialist work and authority workflow.

### My Mobility

The mobility-user experience is journey-centric rather than governance-centric. It should explain goals, pathways, Evidence, unknowns, actions, deadlines, cost, risk and long-term progression in plain language.

### Department workspaces

Department surfaces compose real organizational state for specific units while preserving backend authority boundaries.

---

## 20. Durable Organization Model

Important existing organizational concepts include:

- `OrganizationPosition`;
- `OrganizationalWorkItem`;
- `OrganizationBlocker`;
- `OrganizationWorkItemDependency`;
- `OrganizationHumanActionRequest`;
- `OrganizationContribution`;
- `OrganizationActivity`.

V1.3 extends the conceptual domain toward:

```text
AgentCapability
AgentAuthority
AutonomyEvidenceProfile
ContextBundle
AgentRun
AgentConversation
AgentMessage
ConversationSummary
MaterialAction
DecisionReadinessSnapshot
ConsequentialActionProposal
HumanReview
BoardDecision
DecisionLineage
ToolActionRecord
PolicyDecision
Incident
CircuitBreakerEvent
RecoveryAction
LearningRecord
CuratedLearningExample
```

These are conceptual target entities. Their presence in this README does **not** claim that all have been implemented or persisted already.

---

## 21. Evidence and Trust Model

Global Mobility AIOS operates in domains where attractive answers can still be dangerously wrong.

Consequential claims must be grounded in the required evidence and review state.

The trust ladder remains:

```text
L0 model speculation
L1 conversation / memory / hypothesis
L2 retrieved information
L3 captured SourceSnapshot
L4 governed Evidence
L5 reviewed candidate
L6 VerifiedRule / certified governed fact
L7 governed case conclusion
L8 approved authority-bearing action
```

Forbidden shortcuts include:

```text
L1 ↛ L6
L2 ↛ L7
L6 ↛ L8 automatically
```

Permanent distinctions:

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

---

## 22. Current Delivery Status

Current active development branch:

```text
roadmap/global-mobility-aios-v12
```

Frozen reference/recovery branch:

```text
roadmap/global-mobility-aios-v11
@ dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

Current accepted delivery position:

| Programme | State |
|---|---|
| Phases 1–9 | Complete — core platform, Truth Engine, profiles, pathways, timelines and document intelligence |
| Phase 10 software | Complete — self-updating intelligence foundation, registry workflows, dashboards, ranking and multi-year planning |
| Phase 10B evidence operations | Operationally ongoing — jurisdiction evidence onboarding, independent review, publication and freshness |
| Phase 11 | Complete — corporate, business, wealth, investment, family-office and tax/treaty mobility |
| Phase 12 | Complete / stabilized — portals, partner APIs, governed automation and agency/government workflow foundations |
| Phase 13.0–13.15 | Complete / PASS where gated — organization governance, department runtime and correctness foundations |
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
| **Phase 13.17** | **IN PROGRESS / PAUSED BY EVALUATOR — owner-led human acceptance continues in parallel** |
| Phase 14 | NOT STARTED / demand-gated — measured scale after validated demand |

Phase 13.17 is a parallel human-acceptance stream. It does not globally block Technology Radar or High-Autonomy Organization work, and its findings remain unresolved until corrected, retested or explicitly dispositioned.

---

## 23. V1.3 Implementation Programme on V12

The current implementation sequence is defined in detail by [`docs/ROADMAP.md`](docs/ROADMAP.md).

Track C target stages are:

```text
V1.3-A  Constitutional Contracts
V1.3-B  Minimal Governance Kernel
V1.3-C  Transparency Foundation
V1.3-D  Context & Agent Identity
V1.3-E  First Governed Vertical Workflow
V1.3-F  Decision Readiness
V1.3-G  Independent Verification
V1.3-H  Organizational Immune System
V1.3-I  Earned Autonomy
V1.3-J  Agent Organization Runtime
V1.3-K  Execution / Coworker Runtime
V1.3-L  Live Organization
V1.3-M  Board Transparency Experience
V1.3-N  Learning & Optimization
```

Transparency is intentionally introduced early rather than retrofitted after autonomy expands.

Implementation should proceed through **real vertical mobility workflows**, not giant abstract frameworks built in isolation.

---

## 24. Coordinated Parallel Evolution

Development continues across three coordinated tracks.

### Track A — Product / Human Experience

- Phase 13.17 human acceptance;
- bounded UX corrections;
- Cockpit / Operations / My Mobility refinement;
- explainability and traceability.

### Track B — Technology Radar / Platform Evolution

Current direction includes:

- Wave 1 pilots complete / trial-eligible;
- Wave 2 Docling pilot in progress;
- Presidio queued;
- further technologies adopted only through evidence-driven research/pilot/trial gates.

### Track C — High-Autonomy Organization

- constitutional contracts;
- governance kernel;
- Transparency Layer;
- Context Broker;
- agent identity/memory;
- Decision Readiness;
- independent verification;
- Organizational Immune System;
- earned autonomy;
- runtime adapters;
- Live Organization;
- learning/optimization.

No track globally stops the others, but shared contracts and discovered constraints must be reconciled before incompatible changes land.

---

## 25. Technology Radar and External Runtimes

Global Mobility AIOS remains provider- and framework-independent.

The architectural relationship is:

```text
                         AIOS
                          │
             ┌────────────┴────────────┐
             │                         │
     Agent Runtime Port        Execution Runtime Port
             │                         │
        Adapter(s)                 Adapter(s)
             │                         │
     Munder / Other        OpenWorker / Other
```

Munder Difflin remains an experimental / controlled-research candidate for agent-organization concepts.

OpenWorker remains a replaceable finished-work/execution-runtime reference.

Neither provider owns AIOS organizational semantics, Evidence, VerifiedRules, authority, Missions, WorkItems, canonical activity or business truth.

> **External frameworks provide capability. AIOS owns meaning and authority.**

---

## 26. Latest Accepted Quality Baseline

Latest accepted runtime evidence carried forward into the V12 branch includes:

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
```

The preserved developer `gmai.db` remains unchanged across the documentation-only V1.3 architecture checkpoint.

These results are carried forward from accepted runtime checkpoints. They are **not represented as rerun by documentation-only commits**.

No GitHub CI PASS should be inferred unless a real status/check is attached to the relevant commit.

---

## 27. Performance and Success Metrics

V1.3 should ultimately improve:

```text
Autonomous completion             ↑
Quality                           ↑
Evidence grounding                ↑
Decision traceability             ↑
Board transparency                ↑
Capability reliability            ↑
```

while reducing:

```text
Board operational workload        ↓
Critical errors                   ↓
False / missed escalations        ↓
Cost per outcome                  ↓
Latency                           ↓
Unexplained decisions             ↓
Opaque organizational activity    ↓
```

Important runtime metrics include:

- autonomous completion rate;
- human interventions per material actions;
- Board decisions per organizational actions;
- critical-error rate;
- Evidence-grounding rate;
- human modification/rejection rate;
- false/missed escalation rate;
- contradiction rate;
- source freshness;
- capability reliability;
- workflow completion time;
- p50/p95 action latency;
- cost per completed workflow;
- retry/stale rate;
- incident frequency;
- recovery effectiveness;
- lineage completeness;
- transparency lag.

---

## 28. Architecture at a Glance

```text
                         HUMAN OWNER / BOARD
                           SUPREME AUTHORITY
                                  │
                     Global Mobility AIOS Cockpit
                                  │
               ┌──────────────────┼──────────────────┐
               │                  │                  │
          Organization       Transparency        Board Room
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  │
                               AI CEO
                                  │
                    Organizational Runtime
                                  │
                  Departments / AI Employees
                                  │
                 Memory / Collaboration / Tools
                                  │
                           Agent Reasoning
                                  │
                           Proposed Intent
                                  │
                                  ▼
                     Organizational Immune System
                                  │
                         Canonicalization Gateway
                                  │
                           Material Action
                                  │
                           Command Gateway
                                  │
                      ┌───────────┴───────────┐
                      │                       │
                AUTO EXECUTE              ESCALATE
                      │                       │
                      │              AI / Professional / Board
                      │
                      ▼
                  Canonical State
                      │
             Activity / Lineage / Learning
                      │
                Transparency Layer
                      │
                    Cockpit
```

---

## 29. Technology Stack

### Web

- Next.js 15.2.4
- React 19
- TypeScript
- App Router
- browser OCR through Tesseract.js where applicable

### API

- Python 3.12-class runtime
- FastAPI
- SQLModel / SQLAlchemy ecosystem
- Alembic
- pytest

### Data / local infrastructure

- PostgreSQL for authoritative relational deployment/integration use
- preserved SQLite developer database for local continuity and compatibility testing
- Redis
- Qdrant
- MinIO / S3-compatible object storage
- n8n for bounded automation

### AI direction

- provider-independent hosted/local models;
- structured agent contracts;
- provenance-aware retrieval;
- deterministic authority outside model prompts;
- runtime adapters rather than provider-owned semantics;
- risk-tiered execution and verification.

---

## 30. Repository Layout

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
├── scripts/                  # Repository, migration, audit and acceptance helpers
├── docker-compose.yml
├── alembic.ini
└── .env.example
```

---

## 31. Quick Start

### Docker-oriented local environment

PowerShell:

```powershell
Copy-Item .env.example .env.docker
docker compose up --build
```

Bash:

```bash
cp .env.example .env.docker
docker compose up --build
```

Common endpoints:

```text
API health       http://localhost:8000/health
API docs         http://localhost:8000/docs
Web              http://localhost:3000
n8n              http://localhost:5678
MinIO console    http://localhost:9001
Qdrant dashboard http://localhost:6333/dashboard
```

### Host-side API + web development

Example PowerShell:

```powershell
cd D:\global-mobility-aios
& .\.venv\Scripts\Activate.ps1

cd .\apps\api
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd D:\global-mobility-aios\apps\web
npm install
npm run dev
```

---

## 32. Development and Acceptance Commands

### API regression

```powershell
& .\.venv\Scripts\python.exe -m pytest apps/api/tests -q
```

### Frontend design foundation

```powershell
cd .\apps\web
npm run test:design-foundation
```

### Production web build

```powershell
npm run build
```

### Repository policy

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

Acceptance remains evidence-driven. Unit tests, runtime/browser acceptance, migration safety, authorization checks, repository policy and preserved-data invariants each prove different things.

---

## 33. Preserved Database Guardrails

Current guardrails include:

- preserve the developer SQLite database;
- migrations must be forward, bounded and data-preserving;
- accepted developer SQLite revision is `0076_organization_position_active_identity`;
- the repository currently registers 118 application/model tables;
- `alembic_version` is migration infrastructure, not application-schema drift;
- preserved PostgreSQL environments should not be migrated casually for convenience;
- isolated PostgreSQL environments should be used for bounded migration/transaction contracts;
- test/demo data must not be fabricated in preserved environments merely to make a UI look populated.

---

## 34. Repository Governance

Important contribution principles:

1. Human Owner / Board remains supreme authority.
2. Backend authorization is the source of executable authority.
3. Do not introduce direct mutation shortcuts for UI convenience.
4. Keep regulated claims Evidence-backed and appropriately review-gated.
5. Conversation and memory do not silently become canonical truth.
6. Material autonomous writes cross AIOS governance boundaries.
7. Preserve optimistic concurrency for parallel autonomous work.
8. Keep OrganizationActivity semantic rather than fabricating history from mutable state.
9. Preserve database history unless a reviewed migration/reconciliation explicitly changes it.
10. Keep Board transparency and decision lineage in scope for material organizational behavior.
11. Update roadmap/changelog documentation when delivery state materially changes.
12. Run bounded quality gates appropriate to the slice before claiming PASS.
13. Keep V11 frozen unless an explicit decision authorizes changing it; continue active V1.3 development on V12.

Key repository-policy references:

- [`docs/REPOSITORY_POLICY.md`](docs/REPOSITORY_POLICY.md)
- [`docs/ADR/0001-approved-repository-strategy.md`](docs/ADR/0001-approved-repository-strategy.md)
- `.github/workflows/repo-policy-check.yml`
- `scripts/check_repo_policy.py`

---

## 35. Key Documentation

Start here:

- **Active V1.3 architecture:** [`docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`](docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md)
- **Canonical active roadmap:** [`docs/ROADMAP.md`](docs/ROADMAP.md)
- **Active changelog:** [`docs/CHANGELOG.md`](docs/CHANGELOG.md)
- **Product vision:** [`docs/GLOBAL_MOBILITY_AIOS_VISION_V1.md`](docs/GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- **AI organization governance:** [`docs/AI_ORGANIZATION_GOVERNANCE_V13_0.md`](docs/AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- **Technology Radar:** [`docs/TECHNOLOGY_RADAR_V1_1.md`](docs/TECHNOLOGY_RADAR_V1_1.md)
- **Third-party adoption principles:** [`docs/THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md`](docs/THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md)
- **Repository policy:** [`docs/REPOSITORY_POLICY.md`](docs/REPOSITORY_POLICY.md)

V1.2 and earlier architecture documents remain historical foundations and design evidence. V1.3 supersedes them for active implementation direction while preserving their strongest invariants.

---

## 36. Current Direction

The accepted product baseline is **Phase 13.16.10 — COMPLETE / PASS**.

Phase 13.17 owner-led human acceptance remains **IN PROGRESS / PAUSED BY EVALUATOR** and continues as a parallel feedback stream rather than a global stop gate.

Active development now proceeds on **V12**.

The active architecture direction is:

> **High-Autonomy Organization + Organizational Immune System + Earned Autonomy + Board Transparency & Decision Lineage.**

The project should become more capable without becoming less governed or less transparent.

AI employees may hold meaningful capability-specific delegated authority and should complete most healthy work autonomously. Quality should come primarily from governed Evidence, deterministic material-state validation, risk-tiered independent verification, authority/policy controls, concurrency protection, anomaly detection, circuit breakers, bounded blast radius, consequence-aware recovery and labeled learning.

The Human Owner / Board remains supreme authority and operates primarily by exception, with on-demand visibility into material decisions, agent collaboration, Evidence, rules, tool actions, incidents, autonomy changes and decision lineage.

The next implementation focus is **V1.3-A Constitutional Contracts**, followed by the Minimal Governance Kernel and early Transparency Foundation, while Phase 13.17 and Technology Radar work continue in parallel.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the complete coordinated delivery programme.

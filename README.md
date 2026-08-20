# Global Mobility AIOS

> **A governed, transparent, self-improving, high-autonomy AI-operated professional organization for global mobility.**

Global Mobility AIOS is being built to perform the professional organizational work required to move people, talent, families, businesses and capital across borders.

It combines global-mobility intelligence, official-source Evidence, document intelligence, case/work orchestration, persistent AI employees, an AI executive hierarchy, dynamic Mission Squads, provider-independent runtimes, Skills and tools, organizational memory, governed execution, human professional review, organizational learning and Human Owner / Board oversight inside one auditable operating environment.

The project is deliberately more ambitious than an immigration chatbot, CRM with AI, workflow-automation product, multi-agent demo, generic SaaS admin panel or agent framework wrapped in a UI.

The canonical architecture direction is:

> **Global Mobility AIOS V1.3 + AIOS Organization Fabric + Organizational Immune System + Earned Autonomy + Context Broker + Board Transparency & Decision Lineage + controlled Munder Difflin v0.4.4 donor adoption.**

Operating principles:

> **AIOS does the work. Humans govern the exceptions and retained authority.**

> **The safety infrastructure exists to enable autonomy, not suppress it.**

> **Board by exception. Transparency by default.**

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

---

## Current Development Line

Active development:

```text
roadmap/global-mobility-aios-v12
```

Frozen V11 reference:

```text
roadmap/global-mobility-aios-v11
└── V12 fork origin: dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

V11 remains a frozen architecture/recovery/reference checkpoint. New V1.3 implementation proceeds on V12 unless explicitly reopened.

Current accepted product baseline: **Phase 13.16.10 — COMPLETE / PASS**.  
Phase 13.17 owner-led human acceptance remains **IN PROGRESS / PAUSED BY EVALUATOR**.  
V1.3-A, B.1, B.2, C.1, C.2 and C.3 are sealed; V1.3-C.4 Board/Cockpit Transparency Read Contract is implemented with canonical acceptance pending.

---

## Final Combined Architecture

The complete canonical combined project architecture is documented in:

- [`docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`](docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md)
- [`docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`](docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md)
- [`docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`](docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md)

The combined architecture is summarized below.

```text
                         HUMAN OWNER / BOARD
                           SUPREME AUTHORITY
                                  │
                    GLOBAL MOBILITY AIOS COCKPIT
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
 Living Organization      TRANSPARENCY LAYER            Board Room
       │                          │                          │
       └──────────────────────────┼──────────────────────────┘
                                  │
                                AI CEO
                                  │
                        Executive Hierarchy
                                  │
               Departments + Dynamic Mission Squads
                                  │
                     Persistent AI Employees
                                  │
                           CONTEXT BROKER
                                  │
                          ContextBundles
                                  │
                    AIOS ORGANIZATION FABRIC
                                  │
     Communication / Missions / Presence / Memory / Skills
                                  │
                         AGENT RUNTIME FABRIC
                                  │
                  API / CLI / Local / Specialized
                                  │
                       TOOL / CONNECTOR PLANE
                                  │
                         Material Intent
                                  │
                  ORGANIZATIONAL IMMUNE SYSTEM
                                  │
       Risk R0–R5 / Readiness / Verification / Recovery
                                  │
                         EARNED AUTONOMY
                            A0 → A5
                                  │
                  Authority / Canonicalization
                                  │
                           COMMAND GATEWAY
                                  │
                       CANONICAL AIOS STATE
                                  │
           Evidence / Rules / Cases / Decisions / Outcomes
                                  │
                    ORGANIZATIONAL FLIGHT RECORDER
                                  │
                  Learning / Replay / Shadow Evaluation
                                  │
                     ORGANIZATIONAL IMPROVEMENT
```

Transparency, governance, the Immune System and learning are cross-cutting rather than merely sequential.

---

## Human Authority Model

The **Human Owner / Board is the supreme authority** of Global Mobility AIOS.

No AI CEO, employee, runtime, model, Skill, connector, Munder-derived component or external framework may grant itself authority beyond Board-defined limits.

Normal healthy work should happen below the Board.

> **The Board governs the organization; it does not manually operate it.**

---

## Board Transparency

Operational autonomy must never create organizational opacity.

The Board has on-demand visibility into relevant:

- agent-to-agent conversations;
- delegation chains;
- decisions/recommendations;
- Evidence and SourceSnapshots;
- VerifiedRules;
- tool and external actions;
- policy decisions;
- contradictions/escalations;
- incidents/circuit breakers;
- autonomy promotions/downgrades;
- execution history;
- recovery and learning outcomes.

```text
Board visibility ≠ Board interruption
```

Target drill-down:

```text
Organization
→ Department
→ Mission
→ Case
→ WorkItem
→ Squad
→ Agent
→ Conversation
→ Decision
→ Tool Action
→ Evidence / Rule
→ Canonical Effect
→ Outcome
```

---

## Context Broker

Agents receive purpose-scoped context, not unrestricted organizational data.

> **More relevant truth, not more tokens.**

A `ContextBundle` may contain employee identity, authority, autonomy, Mission, WorkItem, case facts, relevant Evidence, VerifiedRules, SourceSnapshots, known unknowns, contradictions, relevant prior decisions/collaboration summaries, allowed tools/connectors, sensitivity, risk tier, policy version and context hash.

Context should be lazy-loaded and material AgentRun lineage should bind the effective ContextBundle.

---

## Capability, Authority, Autonomy and Risk

These remain separate:

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

---

## Earned Autonomy — A0 to A5

Autonomy is capability-specific, not one rating for an entire employee.

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
Government submission          Human / Board reserved
```

Operational maturity may progress separately through:

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

Agents cannot self-promote.

---

## Decision Readiness and Risk-Tiered Verification

> **Scores route; gates authorize.**

Decision Readiness never overrides mandatory Evidence, authority, policy, contradictions, concurrency, verification or human-review requirements.

| Risk | Typical work | Verification |
|---|---|---|
| R0 | brainstorming / summarization | single agent |
| R1 | routine internal operation | cheap deterministic checks |
| R2 | client-facing preparation | Evidence validation |
| R3 | eligibility / material recommendation | blind independent verification |
| R4 | certification / regulatory publication | independent verification + fresh source + proper authority |
| R5 | government submission / critical reserved action | full AI preparation + required Human/Board authority |

---

## Organizational Immune System

The Immune System is a cross-cutting quality and safety layer:

```text
Evidence Integrity Monitor
Contradiction Detector
Anomaly Detector
Decision Readiness Engine
Capability Performance Monitor
Dynamic Autonomy Manager
Circuit Breakers
Runtime Health Monitor
Rate / Budget Protection
Blast-Radius Controller
Incident Detector
Root-Cause Classifier
Escalation Router
Shadow Evaluation Engine
Learning Feedback
```

Target behavior:

> **Almost invisible during healthy operation; highly capable when abnormal behavior appears.**

---

## Munder Difflin v0.4.4 Adoption

Munder Difflin is now a **frozen strategic donor / controlled adoption programme**, not a competing architecture.

High-value donor areas include:

- Hive messaging and routing;
- runtime/provider abstraction;
- CLI/PTY execution;
- Skills;
- task coordination;
- circuit breaking;
- triggers/schedules/heartbeats;
- webhook/integration patterns;
- memory mechanics;
- transcripts and telemetry;
- token/cost tracking;
- graph/live-scene mechanics;
- engineering worktrees and IDE concepts;
- voice/realtime concepts.

AIOS rejects Munder assumptions that conflict with its architecture, including SQLite/file state as authoritative truth, GOD-style implicit unlimited authority, direct material state mutation by agents and the retro pixel-office presentation.

See [`docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`](docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md).

---

## Living Organization

Munder's 2D office concept is completely transformed into a premium modern **2D/2.5D Living Organization** with persistent modern cartoon AI employees.

Visible behavior must derive from real state:

```text
employee approaches colleague
→ real AgentConversation

employees cluster
→ real collaboration

employee joins Mission Room
→ actual Mission participation

cross-department movement
→ real delegation/handoff

warning state
→ Immune System intervention

AI CEO appears
→ actual executive involvement

employee approaches Board Room
→ real authority escalation
```

No fake organizational activity should be generated merely to make the interface look busy.

Living Organization is also a Board Transparency navigation layer.

---

## Product Surfaces

### Global Mobility AIOS Cockpit

Top-level Human Owner / Board surface for organization health, strategy, performance, quality, risk, autonomy, incidents, transparency, AI Economics, learning and the Living Organization.

### Board Room

Reserved-authority module **inside Cockpit**, not the name of the entire Owner experience.

### Operations

Professional/operator workspace for cases, Evidence, documents, applications, review, exceptions, blockers, authority workflows and remediation.

### My Mobility

Journey-centric end-user experience for goals, pathways, progress, Evidence needs, documents, deadlines, costs, risk, messages, application status and future mobility.

### Employer / Partner / Professional Surfaces

Role-specific experiences that reuse the same canonical identity, Evidence, authority and case model.

---

## Trust Model

```text
L0  model speculation
L1  conversation / memory / hypothesis
L2  retrieved information
L3  captured SourceSnapshot
L4  governed Evidence
L5  reviewed candidate
L6  VerifiedRule / certified governed fact
L7  governed case conclusion
L8  approved authority-bearing action
```

Forbidden shortcuts:

```text
L1 ↛ L6
L2 ↛ L7
L6 ↛ L8 automatically
```

> **Memory provides continuity. Evidence provides authority.**

---

## Delivery Dependency

```text
Governance / Constitutional Contracts
          ↓
Transparency Foundation
          ↓
Context + Organization Semantics
          ↓
Munder-derived Organization Fabric
          ↓
Powerful execution
          ↓
Living Organization
          ↓
Organizational Learning
```

> **Governance before unrestricted execution. Transparency before increased autonomy.**

---

## Current Quality Baseline

Historical accepted product baseline:

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
```

Later V1.3 acceptance records are preserved in [`docs/ROADMAP.md`](docs/ROADMAP.md) and [`docs/CHANGELOG.md`](docs/CHANGELOG.md). Historical evidence must not be represented as rerun unless it actually was rerun.

---

## Repository Layout

```text
global-mobility-aios/
├── apps/
│   ├── api/
│   └── web/
├── agents/
├── workflows/
├── knowledge/
├── infrastructure/
├── docs/
├── scripts/
├── docker-compose.yml
├── alembic.ini
└── .env.example
```

---

## Quick Start

Docker-oriented environment:

```powershell
Copy-Item .env.example .env.docker
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

Host-side API example:

```powershell
cd D:\global-mobility-aios
& .\.venv\Scripts\Activate.ps1
cd .\apps\api
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Web:

```powershell
cd D:\global-mobility-aios\apps\web
npm install
npm run dev
```

---

## Acceptance Commands

```powershell
& .\.venv\Scripts\python.exe -m pytest apps/api/tests -q
& .\.venv\Scripts\python.exe scripts/check_repo_policy.py --root .
& .\.venv\Scripts\python.exe scripts/check_release_consistency.py
& .\.venv\Scripts\python.exe scripts/check_database_migrations.py
```

Frontend:

```powershell
cd .\apps\web
npm run test:design-foundation
npm run build
```

Git whitespace guard:

```bash
git diff --check
```

Acceptance remains evidence-driven. Tests, migration checks, runtime/browser acceptance, authorization checks, repository policy and preserved-data invariants prove different things.

---

## Permanent Architectural Invariants

1. Human Owner / Board is supreme authority.
2. Board governs by exception.
3. Transparency is a right, not an approval requirement.
4. Operational autonomy must never create organizational opacity.
5. Memory is not canonical truth.
6. Evidence provides authority.
7. Capability ≠ Authority ≠ Autonomy ≠ Risk.
8. Autonomy is capability-specific.
9. Agents cannot self-promote autonomy.
10. Scores route; gates authorize.
11. Risk determines verification cost.
12. Independent verification should be genuinely independent.
13. Conversation does not create authority.
14. Provider output does not become canonical truth automatically.
15. Context is purpose-scoped and lazy.
16. Material actions cross typed governance boundaries.
17. Command Gateway is the material mutation boundary.
18. Governance enables autonomy rather than universal approval queues.
19. Concurrency is versioned and idempotent.
20. Consequential actions require honest recovery semantics.
21. External frameworks provide capability; AIOS owns meaning and authority.
22. Live organization visuals reflect genuine organizational activity.
23. Organizational learning is outcome-driven and governed.
24. Global Mobility remains the product specialization.
25. Munder Difflin is a donor subsystem, not the governing architecture.

---

## Final North Star

> **Global Mobility AIOS is a governed, transparent, self-improving, high-autonomy AI-operated professional organization for global mobility. Persistent AI employees operate under an AI CEO, executive hierarchy and Human Owner / Board constitution; form dynamic Mission Squads; receive purpose-scoped truth through a Context Broker; use provider-independent runtimes, Skills, tools and connectors; maintain organizational memory; and proactively execute work across the complete mobility lifecycle. Their power is bounded through Evidence, explicit authority, capability-specific A0–A5 Earned Autonomy, R0–R5 risk-tiered verification, Decision Readiness, the Organizational Immune System, Canonicalization and Command Gateways, complete Transparency and Decision Lineage. Munder Difflin v0.4.4 supplies major runtime and organization-fabric donor capabilities while AIOS retains exclusive ownership of meaning, authority and canonical truth.**

Short form:

> **AIOS is not an application containing agents. It is a governed AI organization that happens to expose itself through software.**

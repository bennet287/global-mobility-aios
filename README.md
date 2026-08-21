# Global Mobility AIOS

> **A governed, evidence-grounded, transparent and cost-intelligent high-autonomy digital organization for global mobility.**

Global Mobility AIOS is being built to perform the professional organizational work required to move people, talent, families, businesses and capital across borders.

It combines global-mobility intelligence, official-source Evidence, document intelligence, case/work orchestration, persistent AI employees, an AI executive hierarchy, dynamic Mission Squads, provider-independent runtimes, Skills and tools, organizational memory, governed execution, human professional review, organizational learning and Human Owner / Board oversight inside one auditable operating environment.

The project is deliberately more ambitious than an immigration chatbot, CRM with AI, workflow-automation product, multi-agent demo, generic SaaS admin panel or agent framework wrapped in a UI.

The canonical architecture direction is:

> **Global Mobility AIOS V1.3 + governed Organization Fabric + Context Intelligence + provider-independent Model Routing + Organizational Immune System + Earned Autonomy + Board Transparency, with Munder, Plasma and LLMLingua used only behind AIOS-owned boundaries.**

Operating principles:

> **AIOS does the work. Humans govern the exceptions and retained authority.**

> **The safety infrastructure exists to enable autonomy, not suppress it.**

> **Board by exception. Transparency by default.**

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

> **Quality first. Cost intelligence second. Premium compute only where it produces measurable additional value.**

> **No new major framework by default: prove a measured architectural gap before adding another donor/runtime framework.**

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

Current V1.3 organization state:

```text
H.1                              SEALED
H.2.1                            SEALED
H.2.2                            SEALED
H.2.2 classification refinement SEALED
H.2.3                            SEALED
H.2.4                            SEALED
H.2 bounded foundation          CLOSED
V1.3-I.1 autonomy profile/evidence
                                  DESIGN ENTRY OPEN / IMPLEMENTATION NOT STARTED
```

Latest accepted Production Proof is run `32505228943` on technical candidate `25b19728e7dc35f3f0450f6ae839fa57fe36c1e4` (4/4 lanes PASS). H.2 closure is an architectural stage decision built on accepted evidence; it introduces no new runtime behavior.

---

## Final Combined Architecture

The complete canonical combined project architecture is documented in:

- [`docs/GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md`](docs/GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md) — active canonical combined architecture
- [`docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`](docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md) — constitutional high-autonomy source
- [`docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`](docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md) — historical predecessor
- [`docs/TECHNOLOGY_RADAR_V1_3_1.md`](docs/TECHNOLOGY_RADAR_V1_3_1.md) — active technology/adoption direction
- [`docs/V1_3_H2_FOUNDATION_CLOSURE_AND_I1_ENTRY_2026-08-21.md`](docs/V1_3_H2_FOUNDATION_CLOSURE_AND_I1_ENTRY_2026-08-21.md) — H→I stage decision
- [`docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`](docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md)
- [`docs/PLASMA_AIOS_ADOPTION_V1.md`](docs/PLASMA_AIOS_ADOPTION_V1.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md)

The combined architecture is summarized below.

```text
                     HUMAN OWNER / BOARD
                       SUPREME AUTHORITY
                              │
                   GLOBAL MOBILITY AIOS
                         COCKPIT
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
     Organization        Transparency        Board Room
          │
        AI CEO
          │
   ORGANIZATION RUNTIME
          │
Persistent Employees
Missions / WorkItems / Squads
          │
     ┌────┴──────────────────────────────┐
     │                                   │
CONTEXT INTELLIGENCE              EXECUTION FABRIC
     │                                   │
Context Broker                       Runtime Ports
     │                                   │
├── Evidence                     ├── AIOS Native
├── VerifiedRules                ├── Munder-derived
├── Memory                       ├── Plasma Fractal
├── Knowledge                    └── other adapters
│   └── Plasma Wiki
└── ContextCompressionPort
    └── LLMLingua-2
        SELECTED PRIMARY PILOT
     │
Context integrity
     │
ContextBundle
     │
Model Router
     │
deterministic / local / hosted / frontier
     │
AgentRun
     │
Typed Proposed Intent
     │
Canonicalization
     │
Evidence / Readiness /
Verification / Policy
     │
Immune-System restrictive preflight
     │
Command Gateway
     │
ALLOW / BLOCK / ESCALATE
     │
Canonical State
     │
Activity / Decision / Tool /
Context / Cost Lineage
     │
Outcome
     │
Learning + Performance
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

## Context Intelligence, Model Routing and AI Economics

The Context Broker remains the sovereign boundary for purpose-scoped context. External knowledge and compression mechanisms sit beneath AIOS-owned contracts.

```text
Evidence / VerifiedRules / Memory / Knowledge
                  ↓
             Context Broker
                  ↓
     protected vs compressible partition
                  ↓
        ContextCompressionPort
                  ↓
       LLMLingua-2 primary pilot
                  ↓
     compression-integrity validation
                  ↓
          derived ContextBundle
```

Permanent boundaries:

```text
compression output != source truth
retrieved knowledge != executable authority
model self-confidence != capability eligibility
```

For initial R3–R5 work, mandatory Evidence, critical VerifiedRules, exact money/dates/identifiers, authority/autonomy/risk constraints, policy constraints, contradictions, material-action parameters and source/version identifiers default to **zero semantic compression**.

Plasma Wiki is a controlled project/organizational knowledge pilot beneath Context Broker. It is not Evidence, a VerifiedRule or canonical legal truth. Custom `.wiki/wiki.py` hooks remain excluded from the first pilot.

The Model Router may select only among runtimes/models that have earned capability eligibility through measured AIOS evaluation. Official regulatory sources remain authoritative; models synthesize governed SourceSnapshots/Evidence rather than becoming the source.

AI Economics optimizes beneath constitutional quality floors:

> **Minimize total governed outcome cost subject to authority, risk, required quality, Evidence, verification, privacy, SLA and reliability constraints.**

Budget pressure may reroute, defer, restrict or escalate. It may never silently lower required quality.

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

The Immune System is a cross-cutting **restrict-only** quality and safety layer. It may detect, constrain, quarantine, downgrade, block or escalate, but it never grants authority, autonomy or permission:

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
Transparency + Context + Organization Semantics
          ↓
Governed Eligibility / Decision Readiness / Verification
          ↓
H.2 bounded Immune safety/measurement foundation — CLOSED
          ↓
I.1 canonical capability-specific autonomy truth — DESIGN ENTRY OPEN
          ↓
Organization Fabric + Context Intelligence + Model Routing
          ↓
Bounded recursive execution / Living Organization
          ↓
Governed learning + performance + AI Economics
```

> **Governance before unrestricted execution. Transparency before increased autonomy.**

---

## Current Quality Baseline

Historical product checkpoint remains preserved in Git history and acceptance records.

Latest accepted V1.3 Production Proof evidence:

```text
H.2.4 technical candidate                  e7584b90fc967e828960ae0730a35d8646fba74f
H.2.4 Production Proof                     32500438187 — 4/4 jobs PASS
H.2.2 classification candidate             25b19728e7dc35f3f0450f6ae839fa57fe36c1e4
H.2.2 classification Production Proof      32505228943 — 4/4 jobs PASS
Backend regression                         1138 passed / 10 skipped / 1 warning / 0 failed
PostgreSQL governed suite                  93 passed / 1 warning / 0 failed
Alembic                                    0001 → 0077 PASS
Registered SQLModel tables                 119
Physical PostgreSQL schema                 PASS
```

Historical evidence must not be represented as rerun unless it actually was rerun. H.2 closure and I.1 design entry are architecture/stage decisions, not new runtime acceptance claims.

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
26. Compression output is derived context, not source truth.
27. Retrieved knowledge is data, not executable authority.
28. A model earns capability eligibility through measured evaluation, not self-reported confidence.
29. Child delegation may narrow parent scope but never expand it.
30. The Organizational Immune System may restrict or stop; it never creates permission.
31. Quality first; cost intelligence second; premium compute must earn its additional cost.

---

## Final North Star

> **Global Mobility AIOS is a governed, evidence-grounded, transparent and cost-intelligent high-autonomy digital organization that coordinates persistent AI employees to perform global-mobility work through dynamic Missions, purpose-scoped context, earned capability-specific autonomy, risk-tiered verification, governed execution and Human Owner / Board sovereignty. Munder, Plasma, LLMLingua and model providers supply bounded capabilities behind AIOS-owned contracts; AIOS retains exclusive ownership of organizational meaning, Evidence, authority, autonomy, risk, canonical truth and consequences.**

Short form:

> **AIOS is not an application containing agents. It is a governed AI organization that happens to expose itself through software.**

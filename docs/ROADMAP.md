# Global Mobility AIOS — Active V12 Product, Platform & High-Autonomy Roadmap

**Roadmap generation:** V12.9  
**Date:** 2026-08-20  
**Active development branch:** `roadmap/global-mobility-aios-v12`  
**V12 fork origin:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`  
**Frozen V11 reference branch:** `roadmap/global-mobility-aios-v11`  
**Final V11 documentation-cleanup head:** `ac130deaafa7aa44068e9459facbda2b4df327d6`  
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR  
**Active organization architecture:** `HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md` + `GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`  
**Munder donor baseline:** `v0.4.4` — strategic donor / controlled adoption programme  
**V1.3-A:** Constitutional Contracts — COMPLETE / PASS / SEALED  
**V1.3-B.1:** Minimal Governance Kernel — COMPLETE / PASS / SEALED AS B FOUNDATION  
**V1.3-B.2:** Governed WorkItem Assignment — COMPLETE / PASS / SEALED  
**V1.3-C.1:** Transparency Trace Foundation — COMPLETE / PASS / SEALED  
**V1.3-C.2:** Non-Executing Material Attempt Transparency — COMPLETE / PASS / SEALED  
**V1.3-C.3:** Explicit Governance → Effect Causation — COMPLETE / PASS / SEALED  
**Current Track C slice:** V1.3-C.4 — Board/Cockpit Transparency Read Contract — IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING  
**Technology Radar state:** Wave 1 PILOT COMPLETE / TRIAL-ELIGIBLE; Wave 2 IN PROGRESS; Munder donor adoption architecture accepted for controlled implementation planning  
**Code migration head:** `0076_organization_position_active_identity`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This is the canonical active roadmap for V12.9. It preserves the accepted V12 product/runtime truth while incorporating the final combined AIOS + Munder Difflin architecture direction.

> **V11 preserves the checkpoint. V12 proves and implements the direction.**

---

## 1. Product identity

Global Mobility AIOS is being built as a **governed, transparent, self-improving, high-autonomy AI-operated professional Global Mobility organization**.

It is not intended to become merely an immigration chatbot, visa questionnaire, generic AI assistant, CRM with AI, document uploader, workflow engine, disconnected multi-agent demo, generic SaaS/admin surface, browser agent or human approval queue.

Target identity:

> **Persistent AI employees research, reason, collaborate, remember, use tools, manage work, prepare professional outputs, make authorized decisions, execute bounded real-world operations and learn from outcomes while the Human Owner / Board retains supreme strategic and reserved authority.**

Operating principles:

> **AIOS does the work. Humans govern the exceptions and retained authority.**

> **The safety infrastructure exists to enable autonomy, not suppress it.**

> **Board by exception. Transparency by default.**

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

Canonical combined architecture:

- `docs/GLOBAL_MOBILITY_AIOS_FINAL_COMBINED_ARCHITECTURE_V1.md`
- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`
- `docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`

---

## 2. Complete mobility lifecycle target

```text
Goal
→ profile / circumstances / constraints / consent
→ mobility strategy
→ country and pathway discovery
→ eligibility and alternatives
→ Evidence requirements and collection
→ official rules and regulatory intelligence
→ risk / cost / timeline / dependencies
→ documents and consistency
→ professional / regulated review where required
→ application preparation
→ Decision Readiness / verification
→ Human / Board authority where required
→ submission / appointment / external action
→ authority response
→ remediation / follow-up / appeal where applicable
→ relocation / post-arrival obligations
→ renewal / status change / family progression
→ long-term residence
→ citizenship / business / investment / long-term mobility strategy
```

The lifecycle must support changing goals, employers and jurisdictions; rejected applications; expired Evidence; superseded rules; family dependencies; long-lived case history; and future mobility strategy.

---

## 3. Current product/runtime truth

| Programme | State |
|---|---|
| Phases 1–9 | Complete — core platform, Truth Engine, profiles, pathways, timelines and document foundations |
| Phase 10 software | Complete — self-updating intelligence, registry workflow, ranking and multi-year planning foundation |
| Phase 10B evidence operations | Ongoing — jurisdiction Evidence onboarding, independent review, publication and freshness |
| Phase 11 | Complete — corporate, business, wealth, investment, family-office and tax/treaty mobility |
| Phase 12 | Complete / stabilized — portals, partner APIs, governed automation and authority-workflow foundations |
| Phase 13.0–13.15 | Complete / PASS where gated — AI organization governance and correctness foundations |
| Phase 13.16.0–13.16.10 | COMPLETE / PASS — role experiences, Contribution/Activity, Cockpit, workspaces, My Mobility, Operations, Evidence/provenance and responsive/accessibility acceptance |
| Phase 13.17 | IN PROGRESS / PAUSED BY EVALUATOR — owner-led genuine human acceptance |
| Phase 14 | NOT STARTED / demand-gated — measured scale after validated demand |

Phase 13.17 remains a real human-acceptance stream and does not become PASS merely because architecture/runtime work progresses.

---

## 4. Historical compatibility contract — protected

The active V12 roadmap intentionally preserves historical markers protected by repository regression tests and meaningful to current Evidence provenance.

`v10.22` introduced **multi-batch tranche operations** around the governed jurisdiction Evidence workflow.

Historical database lineage includes:

```text
0032_initial_rule_assertions
```

The exact markers below must remain present:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

No Munder adoption changes these historical contracts.

---

## 5. Accepted quality evidence

### Carried-forward product baseline

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
Preserved gmai.db             unchanged at accepted checkpoint
```

These are historical accepted results and must never be represented as rerun unless actually rerun.

### V1.3-A acceptance

```text
Constitutional tests          13 passed / 1 warning / 0 failed
Repository policy             PASS
v10.22 regression rerun       1 passed / 1 warning
Full API regression           886 passed / 5 skipped / 1 warning / 0 failed
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual tables
```

### V1.3-B.1 acceptance

```text
Governance Kernel focused     19 passed / 1 warning / 0 failed
Repository policy             PASS
Full API regression           905 passed / 5 skipped / 1 warning / 0 failed
Migration check               PASS
```

### V1.3-B.2 acceptance

```text
B.1 + B.2 focused             25 passed / 1 warning / 0 failed
Repository policy             PASS
Full API regression           911 passed / 5 skipped / 1 warning / 0 failed
Migration check               PASS
```

### V1.3-C.1 acceptance

```text
B.1 + B.2 + C.1 focused       31 passed / 1 warning / 0 failed
Repository policy             PASS
Full API regression           917 passed / 5 skipped / 1 warning / 0 failed
Migration check               PASS
```

### V1.3-C.2 acceptance

```text
Repository policy             PASS
Full API regression           922 passed / 5 skipped / 1 warning / 0 failed
Migration check               PASS
```

### V1.3-C.3 acceptance

Canonical prescribed Windows V12 acceptance was reported all green by the Human Owner. Exact final pytest counts were not restated and are deliberately not invented.

No GitHub CI PASS is claimed without attached status/check evidence.

---

## 6. Human Owner / Board and Board by exception

The Human Owner / Board remains supreme authority. No employee, model, runtime, Munder-derived subsystem, connector or policy engine may supersede it.

Normal healthy work remains below the Board. Board attention focuses on constitutionally reserved actions, legally required human actions, critical incidents, major policy/autonomy changes, major strategic decisions, exceptional legal/regulatory/financial commitments and irreversible actions requiring retained authority.

```text
Board visibility ≠ Board interruption
```

---

## 7. Transparency Layer — permanent and cross-cutting

Transparency must remain explicit throughout the implementation programme rather than being retrofitted after autonomy expands.

Target coverage includes:

- AgentRuns;
- conversations/messages;
- delegation chains;
- Missions/WorkItems;
- decisions/recommendations;
- Evidence/SourceSnapshots/VerifiedRules;
- tool actions;
- external actions;
- policy/governance decisions;
- Command Gateway effects;
- contradictions/escalations;
- incidents/circuit breakers;
- autonomy changes;
- recovery;
- learning outcomes.

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

Current C.4 establishes the first bounded Board-facing transparency read contract. Later stages expand coverage rather than replacing it.

---

## 8. Context Broker

The Context Broker remains a core upcoming V1.3 dependency.

> **More relevant truth, not more tokens.**

ContextBundles should be purpose-scoped, versioned and lazy. Material AgentRun lineage must bind the effective context, authority/autonomy, Evidence/rule versions, policy, model/program, tools, cost, latency and outcome.

---

## 9. Capability, Authority, Autonomy and Risk

Permanent separation:

```text
Capability = what the runtime can technically do
Authority  = what the organization permits
Autonomy   = how independently it may exercise that authority
Risk       = consequence of the specific action
```

```text
CAN DO ≠ MAY DO
```

---

## 10. Earned Autonomy — A0 to A5

Autonomy remains capability-specific.

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

Operational maturity can progress independently through:

```text
SHADOW → RECOMMEND → SUPERVISED → AUTONOMOUS → HIGH-TRUST AUTONOMOUS
```

Agents cannot self-promote.

---

## 11. Decision Readiness and R0–R5 verification

> **Scores route; gates authorize.**

| Risk | Typical work | Verification |
|---|---|---|
| R0 | brainstorming / summarization | single agent |
| R1 | routine internal operation | cheap deterministic checks |
| R2 | client-facing preparation | Evidence validation |
| R3 | eligibility / material recommendation | blind independent verification |
| R4 | certification / regulatory publication | independent verification + fresh source + proper authority |
| R5 | government submission / critical reserved action | full AI preparation + required Human/Board authority |

Readiness can never override mandatory Evidence, authority, policy, contradiction, concurrency, verification or human-review floors.

---

## 12. Organizational Immune System

Target components:

```text
Evidence Integrity Monitor
Contradiction Detector
Anomaly Detector
Decision Readiness Engine
Capability Performance Monitor
Dynamic Autonomy Manager
Circuit Breakers
Runtime Health Monitor
Rate Protection
Budget Protection
Blast-Radius Controller
Incident Detector
Root-Cause Classifier
Escalation Router
Shadow Evaluation Engine
Learning Feedback
```

Munder-derived circuit-breaker/runtime telemetry work belongs inside this system, not beside it.

---

## 13. AIOS Organization Fabric — final combined architecture addition

The final combined architecture introduces an explicit AIOS Organization Fabric containing:

- persistent employee runtime binding;
- Organizational Communication Fabric;
- Mission/work coordination;
- Dynamic Mission Squads;
- presence and heartbeats;
- Mission Rooms;
- agent relationships;
- Skills / Capability Registry runtime;
- memory mechanics;
- Event Nervous System;
- scheduling/triggers/webhooks;
- runtime telemetry.

This is the principal destination for compatible Munder donor features.

---

## 14. Munder Difflin v0.4.4 adoption programme

Munder is no longer described merely as an informal architecture reference. It is a **frozen strategic donor / controlled adoption programme**.

Canonical adoption document:

`docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`

High-value donor areas:

- Hive messaging/router;
- runtime/provider abstraction;
- CLI/PTY execution;
- Skills;
- task coordination;
- circuit breaking;
- triggers/schedules/heartbeats;
- webhooks/integration patterns;
- memory mechanics;
- transcripts/telemetry;
- token/cost tracking;
- graph/live-scene mechanics;
- worktrees/IDE;
- voice/realtime concepts.

Hard rejects:

- SQLite/file state as canonical authority;
- GOD-style unlimited implicit authority;
- direct material mutation bypassing AIOS governance;
- provider-owned organizational semantics;
- retro pixel-office UI as final product design.

Each subsystem is classified DIRECT REUSE / PORT / ADAPT / REIMPLEMENT / REJECT before implementation.

---

## 15. Agent Runtime Fabric

The combined target introduces a provider-neutral runtime fabric:

```text
Persistent AI Employee
        ↓
Context Broker
        ↓
AIOS Agent Runtime Port
        ↓
Hosted/API / CLI / Local / Specialized runtime
        ↓
Tools / reasoning
        ↓
Typed AIOS intent
```

Employee identity remains independent from provider/model/runtime session.

Runtime selection may later consider capability, risk, quality history, privacy, latency, cost, context requirements, availability and verification independence.

---

## 16. Organizational Communication Fabric

Munder Hive mechanics may accelerate typed AIOS communication acts such as REQUEST, QUERY, INFORM, PROPOSE, CHALLENGE, AGREE, DISAGREE, REFUSE, DELEGATE, REVIEW, WARN, ESCALATE, ACKNOWLEDGE and COMPLETE.

Permanent distinctions:

```text
conversation != authority
message != decision
provider transcript != canonical OrganizationActivity automatically
```

---

## 17. Dynamic Squads, Mission Rooms and relationships

Stable departments remain the durable hierarchy. Dynamic Mission Squads provide temporary cross-functional teams for particular outcomes.

Mission Rooms hold collaborative working context such as objective, plan, participants, working facts, hypotheses, known unknowns, Evidence refs, rules, contradictions, decisions, blockers, dependencies and timeline.

Mission Room state does not become canonical truth automatically.

AgentRelationship history may improve future team composition and verifier selection.

---

## 18. Event Nervous System

Munder-derived triggers/schedules/heartbeats/webhooks should feed an AIOS Event Nervous System:

```text
Event
 ↓
Trigger
 ↓
Policy
 ↓
Mission / WorkItem
 ↓
Employee / Squad
```

Example events include source changes, Rule review dates, passport/permit expiry, stale Evidence, incoming documents, authority/employer messages, deadlines, appointments, payments, SLA breaches, incidents and completed dependencies.

---

## 19. Organizational Flight Recorder

The combined architecture adds a first-class Flight Recorder spanning:

```text
Mission
Delegation
WorkItems
AgentRuns
ContextBundles
Conversations
Models/providers
Skills
Tools
Evidence
VerifiedRules
Policy decisions
Verification
Command Gateway
Canonical effects
Cost
Latency
Retries
Incidents
Recovery
Outcome
```

It complements Decision Lineage and feeds Board Transparency, incident analysis, replay, autonomy evaluation and learning.

---

## 20. Replay, Shadow Employees and learning

Future controlled optimization should support:

```text
Historical Mission
→ Replay with changed model/program/context/team/skill/rules/verifier
→ Compare quality / grounding / cost / latency / risk
```

and:

```text
Production Employee
        ├── real result
        └── Shadow Employee → no authority → compare
```

Outcome-driven LearningRecords should feed governed improvement proposals rather than uncontrolled self-modification.

---

## 21. AI Economics

Munder token/cost telemetry should feed an AI Economics layer capable of measuring organization, department, Mission, case, employee, capability, provider, model and tool costs.

Optimize:

```text
Quality × Risk × Latency × Cost
```

Budgets may exist at organization, department, Mission, employee, capability, tool and provider levels.

---

## 22. Living Organization — complete modern transformation

The Live Organization target is now explicit:

> **Premium modern 2D/2.5D Living Organization with persistent modern cartoon AI employees and semantic animation derived from genuine runtime state.**

Munder's pixel-office presentation is not adopted. Useful scene/event synchronization mechanics may be studied or adapted.

Semantic visual rules:

```text
employee approaches colleague → real conversation
employees cluster → real collaboration
employee enters Mission Room → actual Mission participation
cross-department movement → real delegation/handoff
review-space movement → independent verification
warning state → Immune System intervention
AI CEO appears → actual executive involvement
Board Room movement → real authority escalation
```

No fabricated busyness.

Living Organization also becomes a Transparency navigation surface.

---

## 23. Product surfaces

### Global Mobility AIOS Cockpit

Top-level Owner/Board surface for organization health, Living Organization, Missions, departments, workforce, intelligence, decisions, performance, quality, risk, autonomy, transparency, Immune System, incidents, AI Economics, organizational learning and Board Room.

### Board Room

Reserved-authority module inside Cockpit.

### Operations

Professional/operator workspace for cases, Evidence, documents, applications, review, exceptions, blockers, authority workflow and remediation.

### My Mobility

Journey-centric end-user experience for goals, pathways, progress, Evidence needs, deadlines, costs, risk, messages, application status and future mobility.

### External-role surfaces

Employer/partner/professional/authority experiences reuse the same canonical identity, Evidence, authority and case model.

---

## 24. Performance and scalability doctrine

1. Pay for risk.
2. Recompute only what changed.
3. Load only what is needed.
4. Block only when necessary.
5. Centralize governance, distribute execution.
6. Cache only exact governed state.
7. Instrument from day one.

Verification modes may include PRE_COMMIT, POST_COMMIT and BACKGROUND where safe.

> **Governance Cost ∝ Risk × Uncertainty × Novelty**

---

## 25. Target implementation programme

The original V1.3 stages remain the governing sequence but are expanded by the combined architecture:

```text
V1.3-A   Constitutional Contracts                          COMPLETE / SEALED
V1.3-B   Minimal Governance Kernel                        COMPLETE / SEALED
V1.3-C   Transparency Foundation                          IN PROGRESS (C.4 acceptance pending)
V1.3-D   Context Broker + Agent Identity + Runtime Profiles
V1.3-E   First Governed Vertical Workflow
V1.3-F   Decision Readiness
V1.3-G   Independent Verification + Peer Review Network
V1.3-H   Organizational Immune System + circuit breaking
V1.3-I   Earned Autonomy
V1.3-J   AIOS Organization Fabric + Munder donor integration
V1.3-K   Agent Runtime / Coworker Execution + connectors
V1.3-L   Living Organization + modern character system + Organization Graph
V1.3-M   Full Board Transparency Experience + Flight Recorder
V1.3-N   Organizational Learning + Replay + Shadow Employees + AI Economics
```

Implementation should proceed through real vertical mobility workflows rather than giant abstract frameworks in isolation.

---

## 26. Munder adoption slices

```text
M0   frozen donor provenance
M1   runtime/provider abstraction
M2   communication/router
M3   persistent employee runtime binding
M4   Mission/WorkItem coordination
M5   Dynamic Squads
M6   presence + heartbeat
M7   Skills / Capability Registry
M8   relationships
M9   circuit breaker integration
M10  transcripts + telemetry
M11  tool/action lineage
M12  AI Economics inputs
M13  triggers/scheduling
M14  webhooks/integration broker
M15  memory mechanics
M16  Organization/Decision Graph
M17  Living Organization runtime
M18  modern character system
M19  executive voice/realtime
M20  engineering worktrees/IDE
M21  optional desktop runtime
```

These are subordinate implementation slices, not a replacement roadmap.

---

## 27. Coordinated parallel evolution

### Track A — Product / Human Experience

- Phase 13.17 human acceptance;
- bounded UX corrections;
- Cockpit / Operations / My Mobility refinement;
- accessibility;
- explainability;
- transparency experience.

### Track B — Technology Radar / Platform Evolution

- evidence-driven external technology pilots;
- document/OCR/privacy/observability work;
- provider/runtime evaluation;
- Munder donor adoption;
- replaceable infrastructure.

### Track C — High-Autonomy Organization

- governance;
- transparency;
- Context Broker;
- Organization Fabric;
- Decision Readiness;
- independent verification;
- Immune System;
- Earned Autonomy;
- runtime execution;
- Living Organization;
- organizational learning.

No track globally stops the others, but shared contracts must be reconciled before incompatible changes land.

---

## 28. Permanent architectural invariants

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

## 29. Immediate next work

The immediate implementation truth remains **V1.3-C.4 canonical acceptance pending**. The combined architecture documentation does not bypass that gate.

After C.4 acceptance, Track C should proceed into the Context/identity foundation required before deep Munder-derived runtime integration.

Recommended near-term order:

```text
1. Seal V1.3-C.4 acceptance
2. Context Broker / ContextBundle foundation
3. Agent Runtime Profile + employee/runtime identity separation
4. Organization Fabric communication contract
5. First bounded Munder donor pilot behind AIOS contracts
6. Decision Readiness / verification progression
7. Immune System and Earned Autonomy expansion
8. Later Living Organization and learning layers
```

Phase 13.17 and Technology Radar work continue in parallel.

---

## 30. Final north star

> **Global Mobility AIOS is a governed, transparent, self-improving, high-autonomy AI-operated professional organization for global mobility. Persistent AI employees operate under an AI CEO, executive hierarchy and Human Owner / Board constitution; form dynamic Mission Squads; receive purpose-scoped truth through a Context Broker; use provider-independent runtimes, Skills, tools and connectors; maintain organizational memory; and proactively execute work across the complete mobility lifecycle. Their power is bounded through Evidence, explicit authority, capability-specific A0–A5 Earned Autonomy, R0–R5 risk-tiered verification, Decision Readiness, the Organizational Immune System, Canonicalization and Command Gateways, complete Transparency and Decision Lineage. Munder Difflin v0.4.4 supplies major runtime and organization-fabric donor capabilities while AIOS retains exclusive ownership of meaning, authority and canonical truth.**

Short form:

> **AIOS is not an application containing agents. It is a governed AI organization that happens to expose itself through software.**

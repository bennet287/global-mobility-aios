# Global Mobility AIOS — Active Product, Platform & Organization Roadmap

**Roadmap generation:** V11.5 / High-Autonomy Organization Architecture V1.3 alignment
**Date:** 2026-08-19
**Development branch:** `roadmap/global-mobility-aios-v11`
**Repository checkpoint before this documentation update:** `c192e7d5ba56088388527d3406c30f6ab2315e2f`
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR
**Technology Radar state:** Wave 1 PILOT COMPLETE / TRIAL-ELIGIBLE; Wave 2 IN PROGRESS with Docling pilot started; Presidio queued
**Active organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md) — proposed canonical implementation direction
**Architecture foundation retained:** V1.2 runtime-governance invariants remain foundational and are extended, not discarded
**Code migration head:** `0076_organization_position_active_identity`
**Current patch type:** documentation/architecture/roadmap only; no runtime implementation is claimed

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This is the canonical active roadmap for product direction, platform evolution, organizational architecture, implementation sequencing, acceptance, and project governance.

Historical delivery detail remains in [CHANGELOG.md](CHANGELOG.md), Git history, and archived roadmap/changelog snapshots.

---

## 1. Executive summary

Global Mobility AIOS is being built as a **governed, transparent, high-autonomy digital organization for global mobility**.

The project is deliberately more ambitious than ordinary immigration software, generic SaaS, a CRM with AI, or a multi-agent demo.

The system is intended to combine:

- global mobility strategy and pathway discovery;
- official-source and regulatory intelligence;
- eligibility and scenario reasoning;
- Evidence, documents, provenance, consistency, risk, cost, and timelines;
- application/submission workflow;
- long-lived case and client continuity;
- professional/regulated review where needed;
- post-arrival, renewal, residence, citizenship, family, business, investment, and tax-residency progression;
- a real AI organizational structure with AI CEO, departments, positions, specialists, Missions, WorkItems, collaboration, memory, tools, authority, and measurable performance;
- an Organizational Immune System that enables high autonomy without relying on humans to inspect every action;
- a Transparency Layer that gives the Human Owner / Board on-demand visibility into decisions, conversations, evidence, policies, tool actions, escalations, incidents, autonomy changes, and outcomes;
- a premium Cockpit that summarizes organizational health while allowing deep drill-down whenever the Board wants to investigate.

The project direction is:

> **Build an AI-operated professional Global Mobility organization capable of doing the majority of useful organizational work autonomously, while remaining grounded, measurable, secure, explainable, and completely accountable to a Human Owner / Board.**

---

## 2. Vision

Global mobility is fragmented across immigration rules, government sources, documents, employers, schools, family constraints, tax/residency implications, timelines, costs, appointments, submissions, professional advice, email threads, and long-term life goals.

Users should not have to manually coordinate disconnected tools, search engines, spreadsheets, government pages, consultants, email threads, and memory.

Global Mobility AIOS should become the **intelligence and operating layer that understands the complete mobility journey and organizes the work required to achieve the user's goal**.

Long-term vision:

> **A person, family, employer, founder, investor, professional, or institution should be able to state a mobility objective and have AIOS continuously organize the strategy, evidence, rules, work, decisions, submissions, follow-up, and long-term progression required to reach it.**

The organization should feel human in interaction and organizational continuity, while being machine-like in reliability, traceability, consistency, and scalability.

---

## 3. What the project must not become

Global Mobility AIOS should not collapse into:

- a visa chatbot;
- a static eligibility questionnaire;
- a document uploader;
- a generic CRM;
- a conventional case-management SaaS;
- a dark sci-fi agent dashboard;
- an agent framework showcase;
- a collection of model prompts;
- a generic autonomous browser;
- a human-approval queue;
- a technology architecture with no proven mobility product value.

Technology, agents, and infrastructure exist to improve mobility outcomes. They are not the product by themselves.

---

## 4. North-star mobility lifecycle

The long-term lifecycle remains branching and revisable:

```text
Dream / Goal / Business Need
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
Study / Work / Family / Business / Investment / Remote-work move
        ↓
Documents + consistency + preparation
        ↓
Professional / regulated review where required
        ↓
Application / filing preparation
        ↓
Human / Board authority where required
        ↓
Submission / appointment / authority interaction
        ↓
Authority response
        ↓
Remediation / follow-up
        ↓
Relocation / post-arrival / operation
        ↓
Renewal / status change / family progression
        ↓
Long-term residence
        ↓
Citizenship / business / investment / global-mobility strategy
```

AIOS must support changed goals, multiple jurisdictions, alternative pathways, rejected applications, superseded rules, expired Evidence, changed employers, family dependencies, new business structures, and long-lived mobility histories.

---

## 5. Primary user and organizational surfaces

### Global Mobility AIOS Cockpit

The Human Owner / Board command, intelligence, transparency, quality, risk, autonomy, and organizational-health surface.

Cockpit is the top-level control surface.

### Board Room

A **reserved authority module inside Cockpit**, not the name of the whole Owner experience and not a generic review inbox.

### Operations

Professional / Operator workspace for case work, Evidence, decisions, client workflow, human reviews, applications, and governed action.

### My Mobility

Mobility User experience focused on goals, progress, choices, evidence/document requests, timelines, and understandable next steps.

### `/my-mobility`

Non-sensitive orientation/access surface.

### `/portal`

Secure token/device-bound personalized client workspace.

Future partner/employer/authority-facing surfaces should follow the same truth, evidence, identity, and authority architecture rather than inventing separate semantics.

---

## 6. Product visual direction

The product should feel like **premium enterprise software with a distinct AI operating-system identity**, not a generic SaaS/admin dashboard and not dark sci-fi.

Preferred direction remains:

- deep navy / graphite;
- warm ivory;
- selective editorial serif paired with a modern operational sans;
- restrained glass/depth;
- high-quality iconography;
- subtle, meaningful motion;
- luxury-level spacing and typography;
- beautiful information density;
- strong hierarchy and role clarity;
- distinct personalities for Cockpit, Board Room, Operations, and My Mobility.

Live Organization visuals must come from real canonical runtime state, not decorative fake agent animation.

---

## 7. Central V1.3 operating model

V1.3 extends V1.2 with a clearer operating purpose:

> **The safety infrastructure exists to enable autonomy, not suppress it.**

The target is:

```text
High Autonomy
        +
Strong Evidence / Deterministic Governance
        +
Organizational Immune System
        +
Earned Capability-Specific Authority
        +
Board Transparency / Decision Lineage
```

The Human Board should not supervise every operation. The organization should resolve most work itself and escalate only when uncertainty, risk, policy, law, or reserved authority requires it.

---

## 8. Human Owner / Board authority model

The Human Owner / Board remains the **supreme authority** of Global Mobility AIOS.

This does not mean constant operational involvement.

```text
Human Owner / Board
        ↓
Constitution / Strategy / Reserved Powers
        ↓
AI CEO
        ↓
Departments / Department Heads
        ↓
Specialists / AI Employees
```

The Board retains ultimate authority over:

- constitutional rules;
- strategy;
- autonomy ceilings;
- reserved powers;
- major organizational changes;
- critical legal/regulatory/financial commitments;
- classes of irreversible autonomous external action;
- executive authority;
- organization-wide emergency intervention.

Normal work occurs below the Board.

---

## 9. Board by exception

The Board should not routinely receive internal research, normal collaboration, drafting, low-risk WorkItem updates, ordinary scheduling, routine retries, or safe operational actions.

The Board should primarily see:

- reserved government submissions;
- major legal/regulatory commitments;
- major financial commitments;
- major policy changes;
- critical autonomy expansions;
- unresolved high-risk contradictions;
- critical incidents;
- executive/strategic decisions;
- legally/policy-required human authority.

When Board authority is required, AIOS should present finished work with Evidence, rationale, validation, material risk, and concise actions such as:

```text
APPROVE
MODIFY
RETURN
SUBMIT
```

---

## 10. Board Transparency — permanent invariant

The Board does not need to watch everything, but it must be able to inspect anything materially important.

Permanent V1.3 rule:

> **Operational autonomy must never create organizational opacity.**

The Board should have on-demand visibility into:

- agent-to-agent conversations;
- relevant messages;
- delegation chains;
- decisions/recommendations;
- Evidence and source snapshots;
- VerifiedRules;
- tool usage;
- external actions;
- escalations;
- contradictions;
- corrections;
- incidents;
- autonomy changes;
- policy decisions;
- learning outcomes.

The Transparency Layer should summarize by default and preserve drill-down.

```text
Board visibility ≠ Board interruption
```

---

## 11. Transparency experience

Cockpit should use progressive disclosure:

```text
Organization
→ Department
→ Mission
→ Case
→ WorkItem
→ Agent
→ Conversation
→ Decision
→ Evidence / Rule / Tool Action / Event
```

The Board should be able to answer:

- Why was this case classified this way?
- Which agents worked on it?
- What did they discuss?
- Which Evidence supported the conclusion?
- Which VerifiedRules were used?
- Which policy authorized the action?
- Which tool performed an external action?
- Why was an agent capability promoted/downgraded?
- What happened before an incident?
- What changed after a human correction?

Transparency summaries must never replace underlying governed records where policy requires preservation.

---

## 12. Decision Lineage

Every material decision should be reconstructable as a causal/support chain.

```text
Final state
  ↑
Command authorization
  ↑
Verification
  ↑
Agent recommendation
  ↑
Evidence
  ↑
VerifiedRules
  ↑
SourceSnapshots
  ↑
Official-source research
```

The Board should also be able to inspect meaningful conversation/delegation history that shaped the outcome.

Decision Lineage, Conversation Lineage, Activity Lineage, and Tool-Action Lineage are first-class target concepts.

---

## 13. Agents are organizational employees

AIOS agents should not behave as stateless prompts.

Target employee model:

```text
Agent
├── identity
├── position
├── department
├── manager
├── responsibilities
├── expertise
├── Missions / WorkItems / cases
├── working memory
├── long-term memory
├── organizational relationships
├── previous decisions
├── tools / connectors
├── data permissions
├── authority profile
├── autonomy profile
├── budget
├── quality/performance history
├── error/incident history
└── learning history
```

The system should preserve continuity across time and organizational work.

---

## 14. Memory vs canonical truth

Memory is important but non-authoritative.

```text
Agent Memory ≠ Canonical AIOS Truth
```

Layers:

| Layer | Purpose |
|---|---|
| Working memory | current run/reasoning |
| Agent memory | past tasks, conversations, experiences |
| Organizational memory | shared organizational knowledge |
| Canonical AIOS truth | governed facts, Evidence, VerifiedRules, authoritative state |

Permanent principle:

> **Memory provides continuity. Evidence provides authority.**

Consequential work should refresh critical facts/rules rather than trusting old memory.

---

## 15. Context Broker

Agents receive **more relevant truth, not more tokens**.

`ContextBundle` should be:

- task/purpose-scoped;
- tenant/case-scoped;
- sensitivity-aware;
- provenance-aware;
- versioned;
- hashed;
- reconstructable;
- lazy/composable.

Core content may include:

```text
agent identity / authority
mission / WorkItem
relevant case facts + provenance
Evidence
VerifiedRules
SourceSnapshots when needed
unknowns
contradictions
prior decisions
conversation summary
allowed tools
sensitivity classification
policy version
context version/hash
```

Additional context slices should load on demand.

---

## 16. Reconstructable AgentRun

Material `AgentRun` lineage should bind to:

- context bundle/hash;
- model/provider/version;
- prompt/program version;
- role-card version;
- tool/connector versions;
- policy version;
- authority/autonomy profile;
- Evidence/VerifiedRule versions;
- timestamp;
- latency;
- cost;
- outcome;
- trace identifier.

This supports Board transparency, debugging, incident analysis, evaluation, and learning.

---

## 17. Capability, authority, autonomy, and risk

These are separate dimensions.

```text
Capability = what the runtime can technically do
Authority  = what the organization permits
Autonomy   = how independently it may act
Risk       = consequence of the specific action
```

Permanent rule:

```text
CAN DO ≠ MAY DO
```

A runtime may be capable of sending email while an agent is authorized only for routine client status messages, not regulated representation or Board-reserved submissions.

---

## 18. Capability-specific autonomy A0–A5

| Level | Meaning |
|---|---|
| A0 | prohibited |
| A1 | human executes |
| A2 | AI prepares; approval required |
| A3 | autonomous with mandatory post-review |
| A4 | autonomous with monitoring and valid recovery controls |
| A5 | fully autonomous bounded operation |

Autonomy belongs to capability + context.

Example:

```text
Austria Immigration Specialist

Official-source research       A5
Document extraction            A5
Evidence assessment            A4
Eligibility analysis           A4
Client explanation             A3
Evidence certification         A2
Government submission          A0 / Board reserved
```

---

## 19. Earned autonomy

Autonomy should increase through measured performance:

```text
SHADOW
→ RECOMMEND
→ SUPERVISED
→ AUTONOMOUS
→ HIGH-TRUST AUTONOMOUS
```

`AutonomyEvidenceProfile` should track capability-level evidence such as:

- qualifying volume;
- grounding rate;
- human acceptance/modification/rejection;
- contradiction rate;
- policy compliance;
- critical errors;
- source freshness;
- SLA performance;
- recovery outcomes;
- incident history.

An agent never self-grants higher authority.

---

## 20. Dynamic autonomy downgrade

The immune system may temporarily restrict a capability when abnormal signals appear.

Restrictions should be scope-limited when possible:

```text
RWR+ Eligibility A4 → temporary A2
EU Blue Card remains A4
Document preparation remains A5
```

Root-cause classification should distinguish agent failure from source/tool/policy/distribution-change failure.

Every autonomy change must be explainable and visible in Cockpit.

---

## 21. Risk tiers R0–R5

| Risk | Example | Default verification |
|---|---|---|
| R0 | summarization/brainstorming | single agent |
| R1 | routine internal work | agent + cheap deterministic checks |
| R2 | client-facing preparation | Evidence validation |
| R3 | eligibility/material recommendation | blind independent verification |
| R4 | certification/regulatory publication | independent verification + fresh source validation + appropriate authority |
| R5 | government submission / critical reserved action | full AI preparation + human/Board gate |

Risk classification belongs to AIOS policy/materiality rules.

---

## 22. Decision Readiness

Decision Readiness is a routing/quality signal, not a permission oracle.

Potential components:

```text
Evidence completeness
Source authority
Rule freshness
Required fact completeness
Cross-source consistency
Contradictions
Historical capability reliability
Deterministic validation
Agent confidence
```

Each component should have an auditable source.

Model self-confidence is only metadata and should not dominate material decisions.

---

## 23. Scores route; gates authorize

Permanent invariant:

> **No material action is approved by a Decision Readiness scalar alone.**

Example:

```text
Readiness 98%
Mandatory Evidence missing
→ BLOCK
```

```text
Readiness 100%
Action Board-reserved
→ BOARD GATE
```

Required hard gates include identity, authority, scope, Evidence, policy, contradiction state, expected version, required verification, and action-specific preconditions.

---

## 24. Independent verification

High-risk verification should be independent rather than performative.

A verifier should form a conclusion before seeing the originating agent's conclusion.

```text
Evidence
 /    \
A      B
\      /
 compare
```

Agreement is a quality signal. Disagreement becomes an explicit contradiction/investigation path.

Verification depth is risk-tiered to control latency/cost.

---

## 25. AI-to-AI escalation before human escalation

Uncertainty should normally flow through:

```text
Specialist
→ Peer Specialist
→ Senior Specialist
→ Department Head
→ AI CEO
→ Human if unresolved/required
```

Humans should be the exception path, not the first retry mechanism.

---

## 26. Uncertainty vs authority escalation

### Uncertainty escalation

The organization cannot resolve confidence/evidence/contradictions.

### Authority escalation

The organization is ready but the action is legally/policy/constitutionally reserved.

A 99% readiness government submission may still require Board authority.

These must remain separate in data, routing, and UX.

---

## 27. HumanReviewReason

Target reasons:

```text
UNCERTAINTY
CONTRADICTION
INSUFFICIENT_EVIDENCE
OUTSIDE_AUTHORITY
POLICY_REQUIRED
LEGAL_REQUIRED
BOARD_RESERVED
ANOMALY
EXCEPTION
```

Board Room/Professional queues should immediately explain why a human is involved.

---

## 28. Materiality Registry

Not every action receives full governance overhead.

Illustrative classification:

| Action | Material? | Risk |
|---|---:|---:|
| Official-source search | No | R0 |
| Document summary | No | R0 |
| Internal draft note | No | R0 |
| WorkItem assignment | Yes | R1 |
| Evidence candidate | Yes | R2 |
| Eligibility transition | Yes | R3 |
| Evidence certification | Yes | R4 |
| VerifiedRule publication | Yes | R4 |
| Consequential external communication | Yes | R3/R4 |
| Government submission | Yes | R5 |

The registry should be versioned and policy-owned.

---

## 29. Material Action Envelope

Common target envelope:

```text
MaterialAction
├── action_type
├── actor
├── subject
├── aggregate
├── expected_version
├── proposed_change
├── evidence_refs
├── authority_context
├── rationale
├── readiness_snapshot
├── risk_tier
├── consequence_class
├── idempotency_key
├── trace_id
└── requested_at
```

Domain payloads remain typed.

---

## 30. Canonicalization Gateway

The V1.2 semantic firewall remains foundational:

```text
free-form interpretation
        ↓
typed AIOS candidate
        ↓
schema validation
        ↓
deterministic domain checks
        ↓
Evidence / authority / policy checks
        ↓
canonical result
```

Material truth must not be created directly from model opinion, memory, conversation, retrieval, or provider-local events.

---

## 31. Progressive canonicalization

Do not formalize every business concept before product delivery.

Implement material schemas and validators workflow by workflow.

Initial vertical targets should focus on the real workflows already present in the product, such as Evidence → eligibility recommendation → review → canonical eligibility transition.

Later slices can formalize VerifiedRule publication, external communication, application submission, and other consequential actions.

---

## 32. Command Gateway

The Command Gateway remains the only autonomous-agent production mutation path for material canonical state.

It is not a human approval gateway.

```text
Agent
→ MaterialAction
→ identity/authority/scope
→ Evidence/policy/contradiction
→ expected-version/idempotency
→ AUTO EXECUTE or ESCALATE/BLOCK
```

Autonomous agents/runtimes do not receive arbitrary production ORM/SQL/domain-write access.

---

## 33. Distributed execution, one governance model

The Command Gateway is logically centralized as an authority contract but may be physically distributed/sharded.

Different tenants/cases/missions should execute concurrently.

Partition by aggregate where appropriate.

This avoids turning governance into a global serialization bottleneck.

---

## 34. Optimistic concurrency

Material writes require expected-version/precondition semantics.

Stale proposals reject rather than overwriting newer accepted state.

Protect against retry storms with:

- idempotency;
- bounded retries;
- backoff;
- aggregate-level serialization where necessary;
- mission/case sharding.

CRDTs should only be used for genuinely mergeable collaboration state, not authoritative regulated state.

---

## 35. Organizational Immune System

Core target components:

```text
Evidence Integrity Monitor
Contradiction Detector
Anomaly Detector
Decision Readiness Engine
Capability Performance Monitor
Dynamic Autonomy Manager
Circuit Breakers
Rate/Budget Protection
Blast-Radius Controller
Incident Detector
Root-Cause Classifier
Escalation Router
Shadow Evaluation Engine
Learning Feedback
```

The immune system should be almost invisible in healthy operation and highly capable when abnormal behavior emerges.

---

## 36. Circuit breakers and blast radius

Examples:

- unexpected bulk mutation → stop affected capability;
- contradiction spike → temporary scope-limited restriction;
- authority API schema change → suspend submission path;
- runaway model/tool loop → terminate run;
- expired VerifiedRule → disable dependent automatic conclusion;
- abnormal cross-scope access → block material action.

Even trusted agents remain bounded by tenant, case, department, jurisdiction, capability, volume, financial, tool, and external-communication limits.

---

## 37. Incident aggregation

Many low-level failures should become one organizational incident rather than dozens of Board alerts.

The Cockpit should aggregate correlated failures, preserve affected cases/actions, show root cause and automated containment, and request Board action only if actual Board authority is needed.

---

## 38. Consequence-aware recovery

Every consequential command should declare one of:

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
APPEND_ONLY_CORRECTION
```

Recovery is modeled at business-command level, not as a requirement to "rollback 118 tables."

Irreversible actions require stronger pre-execution controls and pre-mortem checks.

Audit history alone is not rollback.

---

## 39. Learning architecture

Use three distinct layers:

```text
OrganizationActivity
        ↓
LearningRecord
        ↓
CuratedLearningExample
```

Outcome labels remain explicit:

```text
PROPOSED
ACCEPTED
MODIFIED
REJECTED
CONTRADICTED
STALE
SUPERSEDED
HUMAN_CORRECTED
EXECUTION_FAILED
PARTIAL
ROLLED_BACK
```

Not every event becomes training truth.

Human corrections should become high-quality labeled learning signals.

---

## 40. Performance & scalability doctrine

The architecture must not pay the maximum safety cost on every operation.

### P1 — Pay for risk

Verification effort scales with risk, uncertainty, and novelty.

### P2 — Recompute only what changed

Readiness/evidence/policy components are incremental and version-aware.

### P3 — Load only what is needed

Context is purpose-scoped, lazy, composable, and versioned.

### P4 — Block only when necessary

Use PRE_COMMIT, POST_COMMIT, and BACKGROUND verification modes.

### P5 — Centralize governance, distribute execution

One authority model; many workers/shards.

### P6 — Cache only exact governed state

Verifier cache keys include relevant Evidence, case facts, VerifiedRules, policy, jurisdiction/effective dates, and verifier/model/program versions.

### P7 — Instrument from day one

Measure latency, cost, context size, retries, false/missed escalations, source freshness, Board workload, autonomy, transparency lag, incidents, and recovery.

Conceptual rule:

> **Governance Cost ∝ Risk × Uncertainty × Novelty**

---

## 41. External platform strategy

AIOS Semantic Sovereignty remains permanent.

External technology may implement capabilities but does not own domain truth, authority, Evidence semantics, VerifiedRule semantics, Board decisions, Mission/WorkItem meaning, or canonical Activity.

Preferred structure:

```text
AIOS-owned capability contract
        ↓
Adapter / Runtime Port
        ↓
External technology
```

This keeps providers replaceable.

---

## 42. Munder Difflin posture

Munder Difflin remains an **experimental reference / controlled research candidate**, not a committed architecture dependency.

A compatibility spike should test:

- identity mapping;
- hierarchy;
- messaging;
- delegation;
- memory;
- scheduling;
- failure handling;
- tool permissions;
- observability;
- multi-tenancy;
- authority compatibility;
- transparency compatibility;
- AIOS semantic sovereignty.

Possible outcomes include ADOPT, TRIAL, WRAP, BORROW PATTERN, FORK, or REJECT.

---

## 43. OpenWorker / Coworker posture

OpenWorker or alternatives may provide files, documents, browser, terminal, email, calendar, MCP, connectors, scheduled work, and external action execution behind AIOS-owned adapters.

They do not own canonical AIOS authority or business semantics.

---

## 44. Tool security and sandboxing

Agents should receive only the tools their capability requires.

Execution isolation should scale with risk:

```text
lightweight tool call
→ bounded worker
→ isolated browser
→ strong terminal sandbox
→ hardened sensitive external-action environment
```

Do not give every agent every tool, secret, network route, or production capability.

---

## 45. Resumable external operations

Slow government sites/APIs, model providers, document services, email, and external connectors should not hold expensive agent execution resources.

Use resumable `ExecutionJob`/event-driven continuation patterns:

```text
agent requests operation
→ job created
→ resources released
→ external result arrives
→ OrganizationActivity
→ Mission resumes
```

---

## 46. Policy Engine

Material actions may depend on role, capability, autonomy, tenant, jurisdiction, privacy, risk, professional-review, and Board-reserved policies.

Policy decisions must be:

- versioned;
- explainable;
- auditable;
- efficient;
- linked into Decision Lineage.

---

## 47. Organizational transparency and sensitive data

Board transparency does not mean secrets or protected data are indiscriminately displayed.

Transparency should show organizational meaning while enforcing lawful sensitivity controls.

Examples may require privileged views for medical, legal-privileged, highly sensitive identity, employee, or credential-related information.

Sensitivity controls protect people and legal obligations; they do not create hidden agent authority.

---

## 48. Core logical entities

Expected conceptual entities include:

```text
Organization
Department
Position
Agent
AgentCapability
AgentAuthority
AutonomyEvidenceProfile

Mission
WorkItem
Case

Evidence
SourceSnapshot
VerifiedRule

ContextBundle
AgentRun
AgentConversation
AgentMessage
ConversationSummary

MaterialAction
Command
PolicyDecision
DecisionReadinessSnapshot

ConsequentialActionProposal
HumanReview
BoardDecision

OrganizationActivity
DecisionLineage
ActivityLineage
ToolActionRecord

LearningRecord
CuratedLearningExample

Incident
CircuitBreakerEvent
RecoveryAction
TransparencyIndex
```

These are conceptual entities. Do not create all persistence structures before a real workflow needs them.

---

## 49. Current accepted product baseline

### Phase 13.16.8 — Professional / Operator — COMPLETE / PASS

Accepted reading order:

```text
Decision / context
  ↓
Blockers + uncertainty
  ↓
Governed next actions
  ↓
Supporting Evidence / review state
  ↓
Technical provenance
```

Historical/mismatched Evidence remains inspectable but cannot silently support current conclusions.

### Phase 13.16.9 — Evidence / provenance UX — COMPLETE / PASS

Shared grammar distinguishes official source, immutable snapshot, review/certification, VerifiedRule, pathway Evidence, case Evidence, superseded history, and unresolved gaps.

### Phase 13.16.10 — Integrated responsive/accessibility acceptance — COMPLETE / PASS

Accepted evidence includes:

- design foundation **28/28 PASS**;
- request/auth **4/4 PASS**;
- Next.js build **41/41 PASS**;
- complete API regression **811 passed / 5 skipped / 0 failed** carried forward for the frontend-only boundary;
- browser/mobile/keyboard/Portal acceptance PASS;
- preserved `gmai.db` SHA256 `23FC012AF3FA89804A84A9C8DD75C0C68515B23AEF1813CC5460D6D73808CD31` unchanged.

No GitHub CI status is inferred from these local acceptance records.

---

## 50. Phase 13.17 — ongoing owner-led human acceptance

**State:** IN PROGRESS / PAUSED BY EVALUATOR.

Phase 13.17 is an ongoing genuine human-acceptance stream led by the Product Owner. It is not independent third-party validation and does not globally block Technology Radar or V1.3 architecture development.

Current unresolved themes include:

- click-through traceability;
- plain-language evidence/governance concepts;
- powerful-control semantics;
- diagnosis/routing;
- blocker/dependency direction;
- role-context navigation;
- icon + text navigation;
- Professional next-action clarity;
- pathway/context-alignment terminology.

Resume point remains Professional Task 2 when the Owner chooses to continue.

Important rule:

> Architecture text does not fix a Phase 13.17 product finding. Findings remain unresolved until corrected, retested, or explicitly dispositioned.

---

## 51. Coordinated Parallel Evolution

The project intentionally advances three tracks in parallel.

### Track A — Product / Human Experience

- Phase 13.17 human acceptance;
- bounded UX corrections;
- Cockpit / Operations / My Mobility refinement;
- role clarity;
- evidence/provenance explainability;
- mobile/responsive/accessibility;
- professional workflow quality;
- real human acceptance evidence.

### Track B — Technology Radar / Platform Evolution

- Wave 2 document/privacy intelligence;
- Wave 3 regulatory monitoring;
- Wave 4 AI runtime/retrieval/quality;
- future output technologies where product need justifies them;
- benchmarks, pilots, security/data-flow review, adoption/rejection.

### Track C — High-Autonomy Organization

- constitutional contracts;
- governance kernel;
- Transparency foundation;
- Context Broker / Agent identity;
- governed vertical workflows;
- Decision Readiness;
- independent verification;
- Organizational Immune System;
- earned autonomy;
- agent/runtime adapters;
- execution/coworker runtime;
- Live Organization;
- Board Transparency experience;
- learning/optimization.

Parallel means **no artificial stop-and-wait**. It also does not mean uncontrolled implementation. Shared contracts and discovered constraints must be reconciled before incompatible delivery.

---

## 52. Technology Radar V1.1 — current state

Canonical Radar:

- [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md)

Adoption lifecycle remains evidence-driven:

```text
REFERENCE → RESEARCH → BENCHMARK → PILOT → TRIAL → ADOPT
```

Inclusion is not adoption.

### Current A+ state

| Technology | Capability | Current state |
|---|---|---|
| Promptfoo | AI quality/safety evaluation | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | neutral telemetry | PILOT COMPLETE / TRIAL-ELIGIBLE |
| ClamAV | malware scanning | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | document normalization | PILOT IN PROGRESS |
| Presidio | privacy/PII gateway | QUEUED PILOT |
| urlwatch | source monitoring | QUEUED PILOT |
| Munder Difflin | agent-organization reference | REFERENCE / CONTROLLED RESEARCH / EXPERIMENTAL |
| OpenWorker | finished-work execution reference | REFERENCE / CONTROLLED RESEARCH |
| Temporal | durable execution | DEFERRED PILOT |
| OpenFGA | relationship authorization | DEFERRED PILOT |

Specialist state remains:

- pgvector — BENCHMARK;
- Qdrant — BENCHMARK against pgvector;
- Pydantic AI — research/pilot candidate;
- Langfuse — research/pilot candidate behind OpenTelemetry;
- PaddleOCR / Unlimited-OCR — gap-triggered benchmark only;
- DSPy — research;
- Gotenberg / Typst — queued when professional-output need exists;
- EU DSS — research.

---

## 53. Technology Wave 1 / Wave 2 runtime truth

### Wave 1

Promptfoo, OpenTelemetry, and ClamAV are **PILOT COMPLETE / TRIAL-ELIGIBLE**.

They are not automatically `ADOPT`.

### Wave 2

Current path:

```text
ClamAV
  ↓
Docling
  ↓
measure current document/OCR quality
  ↓
Presidio / Privacy Gateway
  ↓
Evidence / document intelligence
```

Current truth:

- Docling pilot started;
- Presidio queued next;
- specialist OCR is gap-triggered after measured need.

Latest accepted runtime evidence before this docs-only V1.3 checkpoint:

- API **873 passed / 5 skipped / 0 failed**;
- Next.js **41/41 PASS**;
- design foundation **28/28 PASS**;
- preserved `gmai.db` unchanged.

These results are carried forward and **not claimed as rerun by this documentation update**.

---

## 54. Track C implementation programme — V1.3

### V1.3-A — Constitutional Contracts

**Intent:** freeze the minimum organization constitution before deeper autonomy.

**Deliverables:**

- Board supremacy;
- Board Transparency invariant;
- reserved authority registry;
- capability/authority/autonomy/risk definitions;
- Materiality Registry contract;
- R0–R5 definitions;
- A0–A5 definitions;
- HumanReviewReason;
- consequence/recovery classes;
- retention/transparency obligations.

**Acceptance:** docs/contracts are internally consistent, machine-readable policy direction identified, no runtime claims.

### V1.3-B — Minimal Governance Kernel

**Intent:** create a small reliable authorization/mutation foundation.

**Deliverables:**

- Actor identity;
- capability authority;
- MaterialAction envelope;
- expected version;
- idempotency;
- policy-decision foundation;
- Command Gateway foundation;
- OrganizationActivity trace IDs.

**Acceptance:** unauthorized or stale material writes fail; authorized low-risk test action can execute without human approval; audit/lineage is present.

### V1.3-C — Transparency Foundation

**Intent:** make observability/accountability native before autonomy expands.

**Deliverables:**

- AgentConversation / AgentMessage semantics;
- activity classes;
- material retention rules;
- DecisionLineage foundation;
- ActivityLineage;
- ToolActionRecord;
- trace correlation;
- transparency query surfaces.

**Acceptance:** Board/developer can reconstruct a governed test decision from action back to evidence/policy/actor; material conversation/tool activity is traceable.

### V1.3-D — Context & Agent Identity

**Deliverables:**

- persistent Agent identity;
- Position/Department linkage;
- ContextBundle;
- version/hash;
- AgentRun lineage;
- working vs long-term vs organizational memory boundaries;
- purpose-scoped retrieval.

**Acceptance:** material run is reconstructable and does not require unrestricted database context.

### V1.3-E — First Governed Vertical Workflow

**Intent:** prove the architecture against real mobility work instead of only abstract infrastructure.

Preferred shape:

```text
Evidence
→ reasoning
→ typed candidate
→ verification
→ command
→ canonical state
→ activity
→ Decision Lineage
→ transparency
```

**Acceptance:** complete end-to-end workflow with real existing domain semantics and no shortcut around evidence/authority.

### V1.3-F — Decision Readiness

**Deliverables:**

- readiness component registry;
- deterministic/auditable inputs;
- versioned formula/routing policy;
- hard gates;
- incremental recomputation;
- DecisionReadinessSnapshot;
- explanation output;
- telemetry.

**Acceptance:** score cannot bypass hard gates; changed evidence invalidates affected readiness components; stable components are reused safely.

### V1.3-G — Independent Verification

**Deliverables:**

- blind verifier mode;
- contradiction comparison;
- R3/R4/R5 routing;
- PRE_COMMIT / POST_COMMIT / BACKGROUND modes;
- verifier cache keyed to governed-state hash;
- verification lineage.

**Acceptance:** verifier cannot simply mirror first conclusion; disagreement is preserved; low-risk work avoids unnecessary multi-agent cost.

### V1.3-H — Organizational Immune System

**Deliverables:**

- anomaly signals;
- contradiction-rate monitoring;
- circuit breakers;
- blast-radius limits;
- root-cause classification;
- scope-limited quarantine;
- incident aggregation;
- escalation routing;
- transparent intervention records.

**Acceptance:** simulated abnormal behavior is contained without organization-wide unnecessary shutdown; false-positive handling and override are visible.

### V1.3-I — Earned Autonomy

**Deliverables:**

- shadow mode;
- AutonomyEvidenceProfile;
- promotion criteria;
- capability-specific promotion;
- automated lower-level promotion where policy permits;
- dynamic downgrade;
- recovery criteria;
- governance review;
- autonomy history.

**Acceptance:** autonomy changes are evidence-based, explainable, reversible/reviewable, and never self-granted.

### V1.3-J — Agent Organization Runtime

**Intent:** evaluate runtime candidates behind AIOS contracts.

Munder Difflin is one experimental reference, not a required destination.

**Evaluate:** identity, hierarchy, messaging, memory, delegation, scheduling, failure handling, tools, observability, multi-tenancy, authority, transparency, AIOS sovereignty.

**Exit options:** ADOPT / TRIAL / WRAP / BORROW / FORK / REJECT.

### V1.3-K — Execution / Coworker Runtime

**Deliverables:** bounded files, documents, browser, terminal, email, calendar, MCP/connectors, scheduled execution, external actions, resumable jobs, execution sandbox classes.

OpenWorker or alternatives remain replaceable adapters.

### V1.3-L — Live Organization

**Deliverables:** real agent/mission/work/conversation/incidents/autonomy/quality/cost/performance state in Cockpit.

No fake animated agents. Visual truth must derive from canonical AIOS organization state.

### V1.3-M — Board Transparency Experience

**Deliverables:**

- Organization Explorer;
- Decision Explorer;
- Conversation Explorer;
- Case Timeline;
- Evidence/Rule lineage;
- Tool Activity Explorer;
- Agent History;
- Incident Timeline;
- Autonomy History;
- organization-wide search.

### V1.3-N — Learning & Optimization

**Deliverables:** LearningRecords, correction analysis, readiness calibration, policy tuning, routing optimization, false/missed escalation analysis, evaluation datasets, curated learning examples, permitted model/prompt improvement.

---

## 55. Track C dependency logic

Not every V1.3 package is a hard stop for the next.

Recommended dependency logic:

```text
A Constitutional Contracts
        ↓
B Governance Kernel
        ├────────→ C Transparency Foundation
        └────────→ D Context & Agent Identity
                         ↓
                   E First Vertical Workflow
                         ↓
              F Readiness + G Verification
                         ↓
                 H Immune System
                         ↓
                 I Earned Autonomy
                         ↓
          J Agent Runtime / K Execution Runtime
                         ↓
               L Live Organization
                         ↓
          M Board Transparency Experience
                         ↓
               N Learning/Optimization
```

Bounded J/K research can begin earlier, but deep production mutation integration must respect the relevant governance contracts.

---

## 56. Product-pull discipline without product blocking

Track C should remain ambitious and continue while Phase 13.17 runs.

However, implementation should prefer real vertical workflow needs over speculative abstraction.

Rule:

> **When choosing what production control-plane feature to implement next, prefer the smallest governance mechanism that safely increases useful autonomy in a real mobility workflow.**

This avoids architecture becoming the product while still allowing architecture/platform research to move rapidly.

---

## 57. Runtime acceptance gates for V1.3-A+

### Canonicalization

- unstructured model/provider events cannot directly become authority;
- memory cannot directly become Evidence/VerifiedRule;
- material classifications end in typed AIOS schemas + deterministic validators;
- material decision has traceable support.

### Mutation path

- agent-originated material production write outside Command Gateway fails;
- arbitrary provider/MCP production-domain mutation is unavailable;
- policy/legal/Board gate cannot be bypassed;
- idempotency prevents duplicate consequential execution.

### Concurrency

- stale expected version rejects;
- accepted newer state cannot be overwritten by stale proposal;
- stale run receives refreshed relevant context;
- retries are bounded/backed off.

### Readiness

- readiness inputs are auditable;
- scalar score cannot override hard gates;
- incremental invalidation works;
- risk-specific threshold policy is versioned.

### Verification

- independent verification is genuinely blind before comparison;
- low-risk work does not pay high-risk verification cost;
- contradiction outcome is preserved;
- verifier cache invalidates on governed input change.

### Immune system

- circuit-breaker cause is explainable;
- scope-limited restriction works;
- root-cause class can distinguish source/tool/agent failures;
- Board can inspect but need not act;
- correlated failures aggregate into incidents.

### Transparency

- material actions have trace IDs;
- Decision Lineage is reconstructable;
- relevant conversation/tool activity can be inspected;
- summaries link to underlying governed records;
- secrets are not leaked;
- sensitivity controls are enforced.

### Autonomy

- autonomy is capability-specific;
- promotion requires evidence profile;
- agent cannot self-promote;
- downgrade is explainable/reviewable;
- Board/professional authority is respected.

### Recovery

- consequence class is explicit;
- reversible action has real inverse/restore semantics;
- compensatable action records compensation;
- irreversible action cannot pretend to be reversible;
- append-only correction preserves history.

### Learning

- rejected/modified/contradicted outcomes retain labels;
- canonical accepted state remains distinct from proposal text;
- CuratedLearningExample is not automatically created from every activity;
- human correction lineage is preserved.

---

## 58. Performance acceptance targets

V1.3 should be instrumented before scale claims.

Measure:

- p50/p95 material-action latency;
- Context Broker assembly latency;
- average/percentile context size;
- readiness component recomputation rate;
- cache hit/miss/invalidation;
- verifier latency/cost;
- Command Gateway latency;
- stale retry rate;
- circuit-breaker false-positive rate;
- escalation volume;
- Board workload;
- incident aggregation efficiency;
- transparency indexing latency;
- external execution wait time;
- cost per completed workflow.

No universal numeric SLO is frozen in this docs checkpoint; thresholds should be established from measured runtime baselines.

---

## 59. Quality and autonomy success metrics

Primary organizational metrics should include:

```text
% work completed autonomously
Human interventions / 100 material actions
Board decisions / 1,000 organizational actions
Critical error rate
Evidence-grounding rate
Human modification/rejection rate
False escalation rate
Missed escalation rate
Contradiction rate
Source freshness
Capability reliability
Workflow completion time
Cost per completed outcome
Stale/retry rate
Incident frequency
Recovery effectiveness
Decision-lineage completeness
Conversation/material-action traceability
```

Desired direction:

```text
Autonomous completion ↑
Quality ↑
Evidence grounding ↑
Traceability ↑
Board transparency ↑
Capability reliability ↑

Board operational workload ↓
Critical errors ↓
False/missed escalations ↓
Cost per outcome ↓
Latency ↓
Opaque decisions ↓
```

---

## 60. Cockpit target information architecture

Long-term Cockpit modules:

```text
Global Mobility AIOS Cockpit
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

Top-level Cockpit should summarize organizational health and exceptions.

Board Room remains reserved for strategic/reserved decisions.

Transparency/search enables deep investigation without cluttering the default experience.

---

## 61. Illustrative Cockpit target metrics

Illustrative UX only; not current runtime claims:

```text
Organization Health                     98.7%

Completed today                       12,461
Autonomously completed                12,287
AI-resolved exceptions                   163
Professional escalations                   8
Board decisions                            3
Critical incidents                         0

Evidence grounding                      99.4%
Human acceptance                         98.9%
Critical error                            0.03%

A4/A5 capabilities                          42
Temporary restrictions                       2
Promotion candidates                          4

Material decisions today                   287
Traceable material decisions              100%
Unresolved lineage gaps                      0
```

The point is not the exact numbers. The desired UX is an owner seeing organizational state and only a small number of decisions requiring attention.

---

## 62. Board organization-wide search target

Future queries should include:

- Why was this applicant marked ineligible?
- Which agents contributed to this decision?
- What did the agents discuss?
- Which source/VerifiedRule supported it?
- Who changed the canonical case state?
- Why was autonomy changed?
- Which government submissions occurred in a time window?
- Which cases rely on a given rule?
- Which contradictions remain unresolved?
- Which capabilities are degrading in quality?

Search answers must be grounded in governed activity/lineage, not invented summaries.

---

## 63. Professional layer and human review routing

Not every human review belongs to the Board.

Governance may route to:

```text
AI Specialist
→ Senior AI Specialist
→ AI Department Head
→ Human Professional / Authorized Specialist
→ AI CEO
→ Board
```

The appropriate level depends on uncertainty, legal/professional policy, authority, and reserved powers.

This protects Board attention while preserving accountable human floors.

---

## 64. Phase 14 relationship

Phase 14 remains a scale programme for a validated product.

It does **not** mean all platform or agent-organization work waits until Phase 14.

Technology Radar and V1.3 foundations may proceed in bounded parallel slices before Phase 14.

Phase 14 should benefit from already-proven governance, observability, transparency, and high-autonomy primitives rather than starting them from scratch.

---

## 65. Repository and acceptance discipline

Every project patch should:

1. verify branch/SHA/current remote state;
2. inspect canonical documents;
3. freeze exact implementation boundary;
4. preserve unrelated user work;
5. implement incrementally;
6. run focused tests appropriate to changed behavior;
7. run broader acceptance where required;
8. perform browser/runtime review for user-facing changes;
9. update `ROADMAP.md` for every project patch;
10. update `CHANGELOG.md` for meaningful delivery;
11. inspect exact diff/whitespace;
12. commit/push truthfully;
13. verify remote branch state;
14. preserve database/release invariants;
15. avoid claiming tests/CI/PASS that were not actually run;
16. create immutable local archive when sealing from the canonical local repository where applicable.

Documentation-only architecture checkpoints must not be represented as runtime implementation.

---

## 66. Preserved database and runtime truth

The project deliberately treats preserved databases and accepted runtime evidence as evidence, not disposable demo state.

Current repository documentation records:

- 118 application/model tables;
- current migration head `0076_organization_position_active_identity`;
- preserved `gmai.db` invariants from accepted checkpoints.

No documentation architecture update should mutate preserved database state.

---

## 67. Canonical documents

Primary active documents:

- [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [REPOSITORY_POLICY.md](REPOSITORY_POLICY.md)
- [DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md](DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md)
- [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- **[HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md)** — active high-autonomy implementation direction
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md) — retained foundational predecessor
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md) — predecessor
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md) — predecessor
- [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md)
- [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md)
- [ADR/0002-provider-neutral-platform-adapters.md](ADR/0002-provider-neutral-platform-adapters.md)
- [PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md](PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md)
- [CHANGELOG.md](CHANGELOG.md)

---

## 68. Frozen architecture invariants

1. Human Owner / Board remains supreme authority.
2. Board governs primarily by exception, not routine approval.
3. Operational autonomy must never create organizational opacity.
4. Board has on-demand visibility into material organizational activity subject to lawful sensitivity controls.
5. Agent conversations contributing to material outcomes remain sufficiently reconstructable.
6. Material decisions require Decision Lineage.
7. AI agents may hold genuine delegated authority.
8. Authority is capability-specific and bounded.
9. Autonomy is earned from measured evidence and never self-granted.
10. Memory provides continuity but does not automatically become truth.
11. Material truth crosses typed deterministic canonicalization.
12. Material autonomous mutations cross the Command Gateway.
13. Decision Readiness routes work; it never overrides hard gates.
14. Verification depth scales with risk, uncertainty, and novelty.
15. Legal/policy human requirements override readiness scores.
16. Parallel agents use explicit concurrency/version protection.
17. External frameworks provide capability; AIOS owns semantics and authority.
18. The Organizational Immune System must itself be explainable.
19. Circuit breakers/autonomy restrictions should be scope-limited when possible.
20. Irreversible actions receive stronger pre-execution controls.
21. Recovery semantics are reversible, compensatable, irreversible, or append-only correction.
22. Learning preserves labeled outcomes/corrections rather than treating agent statements as truth.
23. Governance cost scales with risk instead of being maximal for every operation.
24. Context is purpose-scoped, lazy, composable, and versioned.
25. One governance model does not require one physical execution bottleneck.
26. Transparency summaries do not replace required underlying governed records.
27. Secrets/protected sensitive data remain secure even under Board transparency.
28. Every material authority decision is explainable through actor, action, Evidence, policy, outcome, and lineage.
29. Conversation is Activity but not authority.
30. Provider-local state/logs do not silently become canonical AIOS truth.
31. Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.

---

## 69. Current delivery decision

As of this roadmap checkpoint:

- Phase 13.17 remains **IN PROGRESS / PAUSED BY EVALUATOR** and continues as an owner-led parallel human-acceptance stream.
- Product, Technology Radar, and High-Autonomy Organization work proceed through **Coordinated Parallel Evolution**.
- Wave 1 remains **PILOT COMPLETE / TRIAL-ELIGIBLE**.
- Wave 2 remains **IN PROGRESS** with Docling started and Presidio queued.
- V1.3 becomes the active proposed high-autonomy implementation direction and extends V1.2 rather than discarding its control primitives.
- Board is supreme authority but should operate by exception.
- Board Transparency, Decision Lineage, Conversation/Tool Lineage, and on-demand drill-down are first-class architecture requirements.
- Agents are treated as persistent organizational employees with real capability-specific delegated authority.
- Autonomy is earned, evidence-based, measurable, and dynamic.
- Decision Readiness is a routing signal; hard gates authorize.
- Verification is risk-tiered and blind/independent for material work where required.
- The Organizational Immune System is intended to protect high autonomy without creating constant human approval.
- Command Gateway and deterministic canonicalization remain foundational.
- Consequence-aware recovery replaces any simplistic universal-rollback interpretation.
- Munder Difflin remains experimental/controlled research; no integration commitment is implied.
- OpenWorker remains a replaceable execution-runtime reference behind AIOS contracts.
- This documentation checkpoint does **not** claim V1.3 runtime implementation.

---

## 70. Long-term flywheel

```text
Real Work
   ↓
Outcomes
   ↓
Corrections / Incidents / Human Feedback
   ↓
Labeled Organizational Learning
   ↓
Evaluation / Calibration
   ↓
Policy / Context / Agent / Model Improvement
   ↓
Earned Autonomy
   ↓
Better Global Mobility Outcomes
   ↓
More Real Work
```

The objective is for AIOS to become more capable while human operational workload decreases and quality/traceability increase.

---

## 71. Defining project principles

> **Human in interaction. Machine-like in reliability.**

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

> **The safety infrastructure exists to enable autonomy, not suppress it.**

> **Scores route; gates authorize.**

> **Memory provides continuity. Evidence provides authority.**

> **More relevant truth, not more tokens.**

> **Governance Cost ∝ Risk × Uncertainty × Novelty.**

> **Board by exception. Transparency by default.**

> **Governed outcome quality matters more than framework ownership.**

---

## 72. Final project direction

Global Mobility AIOS is intended to become more than software that helps a person complete a visa task.

It should become a **transparent AI-operated professional organization** capable of understanding goals, organizing work, preserving institutional memory, gathering and governing Evidence, tracking changing regulations, coordinating specialized AI employees, producing professional outputs, executing authorized actions, learning from corrections, and escalating intelligently.

The Human Board retains supreme authority but should not have to operate the organization manually.

The architecture therefore aims for:

```text
Maximum useful autonomy
        +
Minimum necessary human interruption
        +
Strong deterministic/evidence boundaries
        +
Measured quality
        +
Bounded consequence
        +
Complete Board inspectability
```

This is the direction to implement incrementally through real vertical mobility workflows without reducing the ambition of the project.

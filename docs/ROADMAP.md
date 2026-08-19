# Global Mobility AIOS — Active V12 Implementation Roadmap

**Roadmap generation:** V12.0  
**Date:** 2026-08-19  
**Active development branch:** `roadmap/global-mobility-aios-v12`  
**Frozen predecessor branch:** `roadmap/global-mobility-aios-v11`  
**Frozen V11 checkpoint:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449` — `docs: define high-autonomy v1.3 architecture`  
**V12 branch origin:** created directly from the frozen V11 checkpoint above  
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR  
**Technology Radar state:** Wave 1 PILOT COMPLETE / TRIAL-ELIGIBLE; Wave 2 IN PROGRESS with Docling pilot started; Presidio queued  
**Active organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md)  
**Architecture foundation:** V1.2 runtime-governance invariants remain foundational and are extended, not discarded  
**Code migration head:** `0076_organization_position_active_identity`  
**Roadmap status:** active implementation roadmap for V12; this document does not itself claim runtime implementation

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

---

## 1. Document and branch relationship

V11 and V12 now have deliberately different roles.

### V11 — frozen reference checkpoint

`roadmap/global-mobility-aios-v11` is frozen at `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`.

It preserves:

- the accepted product/runtime baseline carried through Phase 13.16.10;
- Phase 13.17 as the active owner-led human-acceptance stream;
- Roadmap V11.5;
- the V1.3 architecture checkpoint;
- the V1.3 Transparency Layer / Board Transparency direction;
- the complete V11-era README and changelog state.

V11 should not receive new implementation changes unless the Human Owner explicitly reopens it.

### V12 — active implementation line

`roadmap/global-mobility-aios-v12` begins from exactly the V11 frozen checkpoint and is the active line for all subsequent implementation, architecture realization, product corrections, Technology Radar work, transparency work, and high-autonomy runtime development.

This V12 roadmap is therefore an **implementation roadmap**, not a rewrite of V11 history.

> **V11 preserves the checkpoint. V12 proves and implements the direction.**

---

## 2. Executive project definition

Global Mobility AIOS is being built as a **governed, transparent, high-autonomy digital organization for global mobility**.

It is not intended to become merely:

- an immigration chatbot;
- a visa eligibility questionnaire;
- a CRM with AI features;
- a document uploader;
- a generic workflow engine;
- a multi-agent demo;
- a generic SaaS admin dashboard;
- or an agent framework wrapped in a UI.

The target is an AI-operated professional organization in which persistent AI employees can research, reason, collaborate, remember, use tools, manage Missions and WorkItems, prepare professional outputs, make authorized decisions, execute bounded operations, learn from outcomes, and escalate intelligently.

The Human Owner / Board remains the supreme authority.

The defining operating model is:

> **High autonomy + strong evidence + deterministic governance + an Organizational Immune System + earned capability-specific authority + complete Board inspectability.**

---

## 3. Long-term mobility lifecycle

AIOS should eventually coordinate the complete mobility lifecycle:

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
Documents + consistency + preparation
        ↓
Professional / regulated review where required
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
Relocation / post-arrival obligations
        ↓
Renewal / status progression / family progression
        ↓
Long-term residence
        ↓
Citizenship / business / investment / global-mobility strategy
```

The system must support changed goals, alternative pathways, multiple jurisdictions, superseded rules, expired Evidence, changed employers, family dependencies, rejected applications, long-lived cases, and future mobility planning.

---

## 4. Current product truth

Current accepted delivery remains:

| Programme | State |
|---|---|
| Phases 1–9 | Complete — core platform, profiles, pathways, timelines, document intelligence and Truth Engine foundations |
| Phase 10 software | Complete — self-updating intelligence foundation, registry workflows, ranking and multi-year planning |
| Phase 10B evidence operations | Ongoing — jurisdiction evidence onboarding, review, publication and freshness |
| Phase 11 | Complete — corporate, business, wealth, investment, family-office and tax/treaty mobility |
| Phase 12 | Complete / stabilized — portals, partner APIs, governed automation and agency/government workflow foundations |
| Phase 13.0–13.15 | Complete / PASS where gated — AI organization governance and correctness foundations |
| Phase 13.16.0–13.16.10 | COMPLETE / PASS — role experiences, Contribution/Activity, Cockpit, workspaces, My Mobility, Operations, Evidence/provenance and integrated responsive/accessibility acceptance |
| **Phase 13.17** | **IN PROGRESS / PAUSED BY EVALUATOR** — owner-led human acceptance |
| Phase 14 | NOT STARTED / demand-gated — measured scale after validated demand |

Phase 13.17 remains real human feedback and does not become PASS merely because other work advances.

---

## 5. Carried-forward quality baseline

Latest accepted runtime evidence before the V1.3/V12 documentation work remains:

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
Preserved gmai.db             unchanged at accepted checkpoint
```

These results are carried forward and must not be represented as rerun by documentation-only commits.

No GitHub CI PASS is claimed unless a real attached status/check exists for the relevant commit.

---

## 6. Product surfaces

### Global Mobility AIOS Cockpit

Top-level Human Owner / Board command, organizational intelligence, transparency, health, risk, quality and autonomy surface.

### Board Room

Reserved authority module inside Cockpit. It is not the name of the entire Owner experience and must not become a generic approval inbox.

### Operations

Professional / Operator workspace for cases, Evidence, regulated workflow, applications, reviews, decisions and client work.

### My Mobility

Mobility-user experience organized around goals, progress, options, documents, evidence requests, deadlines, cost, risk and understandable next actions.

### Portal / partner / employer / authority surfaces

These may expand over time, but must reuse the same evidence, identity, authority, privacy and canonical-state model rather than inventing parallel truth systems.

---

## 7. Human authority model

The Human Owner / Board remains the **supreme constitutional authority**.

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

Supreme authority does not imply constant operational involvement.

The Board should govern the organization rather than operate it.

Reserved authority includes classes such as constitutional changes, major strategic decisions, critical autonomy changes, selected irreversible external actions, legally required human accountability, and other explicit Board-reserved powers.

---

## 8. Board by exception

Normal healthy organizational work should remain below the Board:

- research;
- routine case analysis;
- agent-to-agent collaboration;
- document preparation;
- Evidence extraction;
- WorkItem assignment and updates;
- scheduling;
- bounded tool use;
- internal coordination;
- retries;
- low-risk operational decisions.

The Board should primarily see:

- Board-reserved government submissions;
- major legal/regulatory commitments;
- exceptional financial commitments;
- major organizational policy changes;
- critical autonomy expansions;
- unresolved high-risk contradictions;
- critical incidents;
- executive/strategic decisions;
- actions for which law/policy explicitly requires accountable human authority.

> **AIOS does the work. The Board makes the important decisions.**

---

## 9. Board Transparency invariant

V12 must implement the V1.3 transparency principle:

> **Operational autonomy must never create organizational opacity.**

The Board must have on-demand visibility into material organizational activity, including relevant:

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
- incidents;
- circuit-breaker events;
- autonomy promotions/downgrades;
- execution history;
- learning outcomes.

This does not mean flooding Cockpit with raw events.

```text
Board visibility ≠ Board interruption
```

Cockpit should summarize by default and allow deep drill-down when the Board chooses.

---

## 10. Transparency Layer and lineage

Transparency must be implemented early rather than retrofitted after autonomy expands.

Target flow:

```text
material event
→ durable canonical/activity record
→ lineage correlation
→ transparency indexing / summarization
→ Cockpit summary
→ on-demand drill-down
```

Material outcomes should eventually be reconstructable through:

```text
Canonical outcome
        ↑
Command authorization
        ↑
Verification
        ↑
Agent recommendation
        ↑
Evidence / VerifiedRules
        ↑
SourceSnapshots
        ↑
Research / tool actions
```

Relevant conversation and delegation history should also be traceable.

Structured rationales, Evidence, rules, policy and lineage are governance artifacts. Hidden model chain-of-thought is not the audit mechanism.

---

## 11. AI employees, identity and memory

Agents should evolve from transient prompt executions into persistent organizational employees with:

- durable identity;
- Position and Department;
- manager and organizational relationships;
- responsibilities and expertise;
- assigned Missions, WorkItems and cases;
- working memory;
- long-term memory;
- organizational memory access;
- previous decisions;
- tools and connectors;
- data permissions;
- authority and autonomy profiles;
- budgets;
- quality, performance, incident and learning history.

Permanent distinction:

> **Memory provides continuity. Evidence provides authority.**

Memory may guide work but cannot silently become Evidence, VerifiedRule or canonical case truth.

---

## 12. Context Broker

Agents should receive purpose-scoped `ContextBundle`s rather than unrestricted database access or maximum-token prompts.

Target bundle fields include:

```text
agent identity / position
mission / WorkItem
case / aggregate identity
relevant case facts
relevant Evidence
applicable VerifiedRules
SourceSnapshots where required
known unknowns
known contradictions
relevant decision/conversation summaries
allowed tools
sensitivity profile
authority / autonomy context
policy version
context version
context hash
```

Additional context should be lazy-loaded.

> **More relevant truth, not more tokens.**

Material `AgentRun` lineage should bind to context hash/version, model/provider/version, prompt/program version, role card, tools/connectors, Evidence/rule versions, authority/autonomy policy and outcome.

---

## 13. Capability, authority, autonomy and risk

These remain separate dimensions:

```text
Capability = what the runtime can technically do
Authority  = what AIOS permits
Autonomy   = how independently the actor may exercise that authority
Risk       = consequence of the specific action
```

Permanent rule:

```text
CAN DO ≠ MAY DO
```

External runtimes, tools and models never gain authority merely because they technically support an operation.

---

## 14. A0–A5 capability-specific autonomy

Autonomy remains capability/context specific:

```text
A0  prohibited
A1  human executes
A2  AI prepares; approval required
A3  autonomous with mandatory review
A4  autonomous with monitoring and valid recovery controls
A5  fully autonomous bounded operation
```

Example:

```text
Austria Immigration Specialist

Official-source research       A5
Document extraction            A5
Evidence assessment            A4
Eligibility assessment         A4
Client explanation             A3
Evidence certification         A2
Government submission          Board-reserved / policy-defined
```

Do not reduce an employee to one global autonomy number.

---

## 15. Earned autonomy

Autonomy should progress through measured evidence:

```text
SHADOW
→ RECOMMEND
→ SUPERVISED
→ AUTONOMOUS
→ HIGH-TRUST AUTONOMOUS
```

`AutonomyEvidenceProfile` should ultimately consider:

- qualifying case/execution volume;
- Evidence grounding;
- human acceptance;
- modification/rejection rate;
- contradiction rate;
- policy compliance;
- critical errors;
- source freshness compliance;
- SLA performance;
- incident/recovery outcomes.

Agents cannot self-promote.

Autonomy downgrades should be capability/scope-limited where possible, explainable, recorded, reviewable and recoverable.

---

## 16. Risk tiers and verification

Risk is separate from autonomy.

| Tier | Example | Default verification direction |
|---|---|---|
| R0 | summarization / brainstorming | single agent |
| R1 | normal internal operation | agent + inexpensive deterministic checks |
| R2 | client-facing preparation | agent + Evidence validation |
| R3 | eligibility/material recommendation | blind independent verification |
| R4 | certification/regulatory publication | independent verification + fresh source validation + appropriate authority |
| R5 | government submission / critical reserved action | full AI preparation + Human/Board gate |

Verification should not be maximal for every action.

The second verifier should form its conclusion independently before seeing the first agent's conclusion where blind verification is required.

---

## 17. Decision Readiness

Decision Readiness is a routing/quality signal, not authorization by itself.

Potential auditable inputs include:

- Evidence completeness;
- deterministic source-authority tier;
- rule freshness;
- required-fact completeness;
- cross-source consistency;
- contradictions;
- historical capability reliability;
- deterministic validation;
- limited agent-confidence metadata.

Permanent rule:

> **Scores route; gates authorize.**

A high readiness score cannot override:

- missing mandatory Evidence;
- insufficient authority;
- failed policy;
- unresolved blocking contradiction;
- stale expected version;
- missing required verification;
- legal/professional human requirement;
- Board-reserved authority.

Readiness should be incremental/version-aware so unchanged components are not recomputed unnecessarily.

---

## 18. Materiality and MaterialAction

Do not apply maximum governance overhead to every thought or message.

Target Materiality Registry examples:

| Action | Material? | Typical risk |
|---|---:|---:|
| Official-source search | No | R0 |
| Summarize document | No | R0 |
| Draft internal note | No | R0 |
| Assign WorkItem | Yes | R1 |
| Create Evidence candidate | Yes | R2 |
| Eligibility transition | Yes | R3 |
| Certify Evidence | Yes | R4 |
| Publish VerifiedRule | Yes | R4 |
| Consequential external communication | Yes | R3/R4 |
| Government submission | Yes | R5 |

Common target envelope:

```text
MaterialAction
├── action_type
├── actor
├── subject / aggregate
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

## 19. Canonicalization Gateway

V1.2's semantic firewall remains foundational:

```text
LLM / provider / tool interpretation
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

Permanent constraints remain:

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

Canonicalization should be implemented progressively, workflow by workflow, not by attempting to formally model every mobility transition before useful delivery.

---

## 20. Command Gateway

The Command Gateway is the controlled mutation boundary for material autonomous production state.

It is **not** a universal human approval gateway.

Healthy authorized flow should be:

```text
Agent
→ MaterialAction
→ identity / authority / scope
→ Evidence / policy / contradiction
→ expected-version / idempotency
→ required verification / readiness
→ AUTO EXECUTE
```

Human involvement occurs only when required by law, policy, uncertainty, risk or reserved authority.

The gateway should remain logically centralized as a governance contract while execution may be physically distributed/sharded.

---

## 21. Optimistic concurrency

Material writes retain expected-version/precondition semantics.

```text
Agent A reads Case v43
Agent B reads Case v43

A commits → v44

B submits expected_version=43
actual_version=44
→ STALE
→ refresh / rebase / reevaluate
```

Required protections include:

- idempotency;
- bounded retries;
- backoff;
- aggregate-level serialization where needed;
- case/mission sharding.

CRDT-style merging is appropriate only for genuinely mergeable collaborative data, not authoritative regulated state.

---

## 22. Organizational Immune System

V12 must incrementally implement the V1.3 safety/quality layer:

```text
Organizational Immune System
├── Evidence integrity monitoring
├── contradiction detection
├── anomaly detection
├── Decision Readiness
├── capability performance monitoring
├── dynamic autonomy management
├── circuit breakers
├── rate / budget protection
├── blast-radius controls
├── incident detection / aggregation
├── root-cause classification
├── escalation routing
├── shadow evaluation
└── learning feedback
```

The immune system should be mostly invisible during healthy operation and active when abnormal signals appear.

> **Human review is the final safety net, not the primary QA system.**

Every material immune-system intervention must be explainable and Board-inspectable.

---

## 23. Circuit breakers, blast radius and incidents

Example automatic protections:

```text
unexpected bulk mutation
→ stop affected capability

critical contradiction spike
→ scope-limited restriction

government API/schema change
→ suspend affected external path

runaway tool/model loop
→ terminate run

expired governing rule
→ block dependent autonomous conclusion
```

Blast radius can be bounded by tenant, case, department, jurisdiction, capability, tool, volume, financial limit and communication limit.

Correlated failures should aggregate into an organizational `Incident` rather than flooding the Board with duplicate alerts.

Root cause should distinguish at least agent failure, source failure, tool failure, policy mismatch, regulation/distribution change, missing context, external outage, data corruption and unknown causes.

---

## 24. Consequence-aware recovery

Every consequential action should identify realistic recovery semantics:

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
APPEND_ONLY_CORRECTION
```

Examples:

- WorkItem reassignment → reversible;
- incorrect external message → compensatable with correction;
- delivered email / government submission → irreversible external side effect;
- Evidence certification later invalidated → append-only correction/revocation.

Recovery semantics belong to consequential commands/business actions, not generic rollback across every database table.

Irreversible actions require stronger pre-execution checks and pre-mortem validation.

---

## 25. Learning architecture

Target pipeline:

```text
OrganizationActivity
        ↓
LearningRecord
        ↓
CuratedLearningExample
```

Preserve labels such as:

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

Human corrections and verified outcomes should become high-quality learning/evaluation signals where lawful purpose, consent and retention rules permit.

---

## 26. Performance and scalability doctrine

The cumulative cost of governance is a first-class risk.

V12 follows these principles:

### P1 — Pay for risk

Verification effort scales with consequence, uncertainty and novelty.

### P2 — Recompute only what changed

Readiness, Evidence and policy components should be incremental/version-aware.

### P3 — Load only what is needed

Context is purpose-scoped, lazy, composable and versioned.

### P4 — Block only when necessary

Distinguish:

```text
PRE_COMMIT
POST_COMMIT
BACKGROUND
```

### P5 — Centralize governance, distribute execution

One authority model must not become one global execution mutex.

### P6 — Cache exact governed state only

Verifier/cache identity must include relevant Evidence, facts, rules, policy, jurisdiction, effective dates and program/model versions.

### P7 — Instrument from day one

Measure latency, cost, retries, verification overhead, context size, source freshness, false/missed escalations, Board workload, incident rate and autonomy rate.

Conceptual principle:

> **Governance Cost ∝ Risk × Uncertainty × Novelty**

---

## 27. External runtime and provider independence

AIOS must survive replacement or disappearance of any external agent/execution framework.

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

AIOS owns:

- Mission / WorkItem semantics;
- Evidence and VerifiedRule meaning;
- authority and policy;
- canonical OrganizationActivity;
- Decision Lineage;
- case state;
- certification/publication semantics;
- organizational truth.

### Munder Difflin

Remains experimental / controlled research until a compatibility spike proves fit.

### OpenWorker

Remains a replaceable Coworker/finished-work execution reference behind AIOS-owned contracts.

> **AIOS Semantic Sovereignty is permanent.**

---

## 28. Technology Radar state

Current accepted state remains:

| Technology | Capability | State |
|---|---|---|
| Promptfoo | AI quality/safety evaluation | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | neutral telemetry | PILOT COMPLETE / TRIAL-ELIGIBLE |
| ClamAV | malware scanning | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | document normalization | PILOT IN PROGRESS |
| Presidio | privacy gateway | QUEUED PILOT |
| urlwatch | source monitoring | QUEUED PILOT |
| Munder Difflin | agent organization runtime reference | CONTROLLED RESEARCH |
| OpenWorker | Coworker/execution runtime reference | CONTROLLED RESEARCH |
| Temporal | durable execution | DEFERRED PILOT |
| OpenFGA | relationship authorization | DEFERRED PILOT |

Radar inclusion does not equal adoption.

Lifecycle remains evidence-driven:

```text
REFERENCE → RESEARCH → BENCHMARK → PILOT → TRIAL → ADOPT
```

or explicit rejection where appropriate.

---

## 29. Coordinated parallel evolution

The project continues through three coordinated tracks.

### Track A — Product / Human Experience

- Phase 13.17 human acceptance;
- bounded UX corrections;
- Cockpit / Operations / My Mobility refinement;
- role clarity;
- evidence/provenance explainability;
- real workflow usability.

### Track B — Technology Radar / Platform Evolution

- document/privacy intelligence;
- regulatory monitoring;
- runtime/retrieval/quality experiments;
- professional-output technologies when justified;
- explicit adopt/reject evidence.

### Track C — High-Autonomy Organization

- governance contracts;
- Transparency Foundation;
- persistent agents and context;
- governed vertical workflows;
- Decision Readiness;
- independent verification;
- Organizational Immune System;
- earned autonomy;
- runtime adapters;
- Live Organization;
- learning and optimization.

No track globally blocks the others. Shared contracts and discovered constraints must be reconciled before incompatible changes are merged.

---

## 30. V1.3 implementation programme on V12

### V1.3-A — Constitutional Contracts

Formalize:

- Human Board supremacy;
- Board Transparency invariant;
- reserved powers;
- capability authority;
- autonomy semantics;
- materiality/risk tiers;
- HumanReviewReason;
- recovery/consequence classes;
- transparency/retention obligations.

Acceptance requires explicit contracts and tests where runtime behavior already exists. Documentation alone is not runtime completion.

### V1.3-B — Minimal Governance Kernel

Implement incrementally:

- actor identity;
- capability authority;
- expected-version contract;
- idempotency;
- `MaterialAction` foundation;
- policy decision foundation;
- Command Gateway foundation;
- trace identity;
- canonical `OrganizationActivity` integration.

### V1.3-C — Transparency Foundation

Implement early:

- agent conversation/message capture contracts;
- activity classes;
- trace correlation;
- `ToolActionRecord` target;
- Decision Lineage foundation;
- transparency queries;
- retention/sensitivity boundaries.

### V1.3-D — Context & Agent Identity

Implement:

- durable agent identity;
- Positions / Departments;
- `ContextBundle`;
- context hash/version;
- `AgentRun` lineage;
- working/long-term/organizational memory boundaries;
- scoped conversation retrieval.

### V1.3-E — First Governed Vertical Workflow

Choose one real mobility workflow and exercise:

```text
Evidence
→ contextual agent reasoning
→ typed candidate
→ verification as risk requires
→ Command Gateway
→ canonical state
→ OrganizationActivity
→ Decision Lineage
→ Transparency
→ LearningRecord where meaningful
```

This is the critical proof point. Architecture components should be hardened from real workflow evidence rather than built to maximum generality in isolation.

### V1.3-F — Decision Readiness

Implement:

- auditable readiness components;
- versioned formula;
- hard gates;
- incremental recomputation;
- readiness snapshots;
- Board/Professional explanation output;
- calibration telemetry.

### V1.3-G — Independent Verification

Implement:

- blind peer verification;
- contradiction comparison;
- risk-tier routing;
- PRE_COMMIT / POST_COMMIT / BACKGROUND modes;
- cache/hash identity;
- verification lineage.

### V1.3-H — Organizational Immune System

Introduce incrementally:

- anomaly signals;
- circuit breakers;
- blast-radius controls;
- root-cause classification;
- scope-limited quarantine;
- incident aggregation;
- escalation routing;
- Board-inspectable intervention history.

### V1.3-I — Earned Autonomy

Implement:

- shadow mode;
- `AutonomyEvidenceProfile`;
- promotion criteria;
- capability-specific autonomy change;
- automatic temporary restriction;
- recovery criteria;
- human/Board override and review;
- autonomy-change lineage.

### V1.3-J — Agent Organization Runtime

Run bounded compatibility evaluation for external/runtime candidates against:

- identity;
- hierarchy;
- messaging;
- memory;
- delegation;
- scheduling;
- failure handling;
- tool permissions;
- observability;
- authority mapping;
- transparency compatibility;
- multitenancy/security;
- AIOS Semantic Sovereignty.

### V1.3-K — Execution / Coworker Runtime

Implement provider-neutral bounded execution for capabilities such as:

- files;
- documents;
- browser;
- terminal/code;
- email;
- calendar;
- MCP/connectors;
- scheduled execution;
- external actions;
- resumable external jobs.

### V1.3-L — Live Organization

Bring real runtime organization state into Cockpit:

- agents;
- departments;
- Missions;
- WorkItems;
- collaboration;
- blocked work;
- incidents;
- autonomy;
- quality;
- cost;
- performance;
- material activity.

No simulated/fake activity should be presented as live organizational truth.

### V1.3-M — Board Transparency Experience

Build Cockpit drill-down capabilities such as:

- Organization Explorer;
- Decision Explorer;
- Conversation Explorer;
- case/activity timeline;
- Tool Activity Explorer;
- Evidence/Rule lineage;
- incident timeline;
- autonomy history;
- organization-wide governed search.

### V1.3-N — Learning & Optimization

Deepen:

- LearningRecords;
- human correction lineage;
- capability performance;
- readiness calibration;
- policy tuning;
- false/missed escalation analysis;
- evaluations;
- curated learning datasets where lawful;
- evidence-backed autonomy expansion.

---

## 31. Implementation dependency direction

The programme is not intended as a rigid months-long waterfall.

A useful dependency shape is:

```text
A Constitutional Contracts
        ↓
B Governance Kernel
   ┌────┴─────┐
   ↓          ↓
C Transparency   D Context / Agent Identity
   └────┬─────┘
        ↓
E First Governed Vertical Workflow
        ↓
F Readiness + G Verification
        ↓
H Immune System
        ↓
I Earned Autonomy
        ↓
J/K Runtime expansion
        ↓
L Live Organization
        ↓
M Board Transparency Experience
        ↓
N Learning / Optimization
```

Bounded research for J/K may proceed in parallel, but runtime adoption must not bypass the contracts established by A–I.

---

## 32. First vertical-workflow rule

The single most important implementation discipline on V12 is:

> **Do not build every governance component to full generality before one real mobility workflow proves it is needed.**

The first governed vertical slice should be meaningful enough to exercise:

- real case/context;
- Evidence;
- VerifiedRules;
- agent identity;
- a material recommendation/transition;
- risk classification;
- verification;
- authority;
- Command Gateway;
- canonical state;
- activity/lineage;
- transparency;
- a real human/professional interaction where required.

This is how V12 converts architecture strength into implementation evidence.

---

## 33. Product validation priority

The architecture is ahead of external validation. V12 must actively close that gap.

Phase 13.17 remains valuable but owner-led acceptance is not independent market validation.

The project should progress toward:

```text
owner-led acceptance
        ↓
external professional usability session
        ↓
real mobility workflow / real case
        ↓
first 10 external cases
        ↓
repeatable jurisdiction workflow
        ↓
first paying professional / organization
        ↓
measured product demand
```

Important validation measures include:

- workflow completion;
- time saved;
- human correction rate;
- abandonment/drop-off;
- professional trust;
- critical errors;
- Evidence quality;
- willingness to reuse/pay;
- repeatability across similar cases.

This does not reduce the long-term vision. It provides evidence that the architecture solves real work.

---

## 34. Legal, privacy and data-governance work

V12 should progressively make explicit the policies the architecture is designed to support, including as relevant:

- GDPR lawful basis by data class/use;
- special-category data handling;
- purpose limitation;
- retention/deletion/correction;
- model-provider data-use boundaries;
- cross-border data transfer controls;
- agent-memory retention;
- conversation retention/classification;
- LearningRecord / training eligibility;
- professional/legal-advice boundaries;
- representation/submission authority;
- consent and client authorization;
- security/secret handling;
- Board transparency with lawful sensitivity controls.

Architecture capability is not itself legal validation. External professional/legal review should be obtained where appropriate before regulated production use.

---

## 35. Operational maturity direction

As V1.3 runtime capability grows, operational controls should mature with it:

- SLOs for material actions and key workflows;
- p50/p95 latency;
- incident-response runbooks;
- provider outage handling;
- circuit-breaker recovery procedures;
- external-job retries/queues;
- production observability;
- data backup/recovery verification;
- emergency autonomy restriction;
- security event handling;
- controlled deployment/rollback;
- cost/budget telemetry.

The architecture assumes mature operations eventually; V12 must build that maturity incrementally rather than pretending it already exists.

---

## 36. Cockpit direction

The Cockpit should answer:

> **Is my organization healthy, effective, transparent and operating within the authority I granted it?**

Target information categories include:

```text
Organization Health
Work / Missions
Quality
Evidence grounding
Autonomy
Incidents / Risk
Agent performance
Cost / latency
Transparency / lineage completeness
Board decisions required
```

The Board should be able to drill from organization-level summaries to:

```text
Organization
→ Department
→ Mission
→ Case
→ WorkItem
→ Agent
→ Conversation
→ Decision
→ Evidence / Rule
→ Tool action
→ Final outcome
```

Illustrative UX metrics must never be confused with actual runtime values.

---

## 37. Success metrics

V12 should increasingly measure:

```text
% work completed autonomously
human interventions per 100 material actions
Board decisions per 1,000 organizational actions
critical error rate
Evidence-grounding rate
human modification / rejection rate
false escalation rate
missed escalation rate
contradiction rate
source freshness
capability reliability
workflow completion time
p50 / p95 material-action latency
cost per completed workflow
stale / retry rate
incident frequency
recovery effectiveness
Decision Lineage completeness
material action traceability
conversation/tool lineage completeness
```

Desired direction:

```text
Autonomous completion             ↑
Quality                           ↑
Evidence grounding                ↑
Decision traceability             ↑
Board transparency                ↑
Capability reliability            ↑
External validation               ↑

Board operational workload        ↓
Critical errors                   ↓
False/missed escalations          ↓
Cost per outcome                  ↓
Latency                           ↓
Unexplained decisions             ↓
Opaque organizational activity    ↓
```

---

## 38. Repository and delivery discipline

Every V12 project patch should:

1. verify active branch/SHA/remote state;
2. inspect canonical docs and current runtime truth;
3. freeze exact patch scope;
4. preserve unrelated user work;
5. implement incrementally;
6. run focused tests appropriate to changed behavior;
7. run broader acceptance when the change requires it;
8. perform browser/runtime acceptance for user-facing changes;
9. update `ROADMAP.md` for every project patch;
10. update `CHANGELOG.md` for meaningful delivery;
11. inspect diff and whitespace;
12. stage/publish only intended files;
13. commit truthfully;
14. push and verify remote state;
15. preserve DB/migration/release invariants;
16. never claim tests, CI, runtime integration or PASS evidence that was not actually observed.

Documentation-only architecture changes must remain explicitly documentation-only.

---

## 39. Frozen architectural invariants

1. Human Owner / Board remains supreme authority.
2. Board governs primarily by exception, not routine approval.
3. Operational autonomy must never create organizational opacity.
4. Board has on-demand visibility into material organizational activity subject to lawful sensitivity controls.
5. Material decisions require reconstructable Decision Lineage.
6. Agent conversations contributing to material outcomes remain sufficiently reconstructable.
7. AI agents may hold real delegated authority.
8. Authority is capability-specific and bounded.
9. Autonomy is earned from measured evidence and never self-granted.
10. Memory provides continuity but does not automatically become truth.
11. Material truth crosses typed/deterministic canonicalization.
12. Material autonomous mutations cross the Command Gateway.
13. Decision Readiness routes work; it never overrides hard gates.
14. Verification depth scales with risk, uncertainty and novelty.
15. Legal/policy human requirements override readiness scores.
16. Parallel agents use explicit concurrency/version protection.
17. External frameworks provide capability; AIOS owns semantics and authority.
18. The Organizational Immune System must itself be explainable.
19. Circuit breakers/autonomy restrictions should be scope-limited where possible.
20. Irreversible actions receive stronger pre-execution controls.
21. Recovery semantics distinguish reversible, compensatable, irreversible and append-only correction.
22. Learning preserves labeled outcomes/corrections rather than treating agent output as truth.
23. Governance cost scales with risk instead of being maximal for every operation.
24. Context is purpose-scoped, lazy, composable and versioned.
25. One governance model does not require one physical execution bottleneck.
26. Transparency summaries do not replace required underlying governed records.
27. Secrets/protected sensitive data remain secure even under Board transparency.
28. Every material authority decision is explainable through actor, action, Evidence, policy, outcome and lineage.
29. Conversation is Activity but not authority.
30. Provider-local state/logs do not silently become canonical AIOS truth.
31. Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.

---

## 40. Immediate V12 priorities

Unless new product evidence requires reprioritization, the active implementation direction is:

### Priority 1 — V1.3-A Constitutional Contracts

Freeze the runtime-facing contracts for Board supremacy/transparency, reserved authority, capability authority, materiality, risk tiers, autonomy, HumanReviewReason, consequence/recovery and retention/transparency obligations.

### Priority 2 — V1.3-B Minimal Governance Kernel

Create the smallest production-quality runtime primitives required to enforce those contracts.

### Priority 3 — V1.3-C Transparency Foundation

Implement traceability early so later autonomy does not create opaque behavior.

### Priority 4 — V1.3-D Context & Agent Identity

Give agents durable organizational identity and reconstructable purpose-scoped context.

### Priority 5 — V1.3-E First Governed Vertical Workflow

Prove the architecture on one serious end-to-end mobility workflow before generalizing it further.

In parallel:

- Phase 13.17 human acceptance continues when the Owner resumes it;
- bounded Product/Human Experience fixes continue from evidence;
- Docling Wave 2 work may continue;
- Presidio remains queued behind the accepted Wave 2 sequence;
- Munder/OpenWorker remain controlled research rather than architecture dependencies.

---

## 41. Canonical documents for V12

Start with:

- [ROADMAP.md](ROADMAP.md) — this active V12 implementation roadmap;
- [CHANGELOG.md](CHANGELOG.md) — V12 delivery history;
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md) — full active architecture direction;
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md) — foundational predecessor/invariants;
- [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md) — product vision;
- [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md) — platform evaluation track;
- [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md) — semantic-sovereignty boundary;
- [PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md](PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md) — current human-acceptance checkpoint;
- [REPOSITORY_POLICY.md](REPOSITORY_POLICY.md) — repository/dependency policy.

For the exact frozen V11 roadmap/README/changelog checkpoint, inspect branch `roadmap/global-mobility-aios-v11` at `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`.

---

## 42. Final V12 direction

V11 proved and documented a strong product baseline and froze the V1.3 architecture direction.

V12 exists to turn that direction into **measured runtime reality** without sacrificing the working checkpoint.

The project should continue ambitiously, but implementation evidence now matters more than adding architecture for its own sake.

The V12 target is therefore:

```text
Real mobility workflow
        +
Persistent AI employees
        +
Evidence-backed decisions
        +
Deterministic material-state governance
        +
Risk-tiered verification
        +
Organizational Immune System
        +
Earned autonomy
        +
Complete Board transparency
        +
External user validation
```

> **Give AI employees enough authority to genuinely operate the organization. Give AIOS enough governance and intelligence to keep that autonomy reliable. Give the Human Board enough transparency and authority to understand, inspect and control the organization whenever necessary.**

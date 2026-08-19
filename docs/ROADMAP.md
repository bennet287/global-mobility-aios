# Global Mobility AIOS — Active V12 Product, Platform & High-Autonomy Roadmap

**Roadmap generation:** V12.1  
**Date:** 2026-08-19  
**Active development branch:** `roadmap/global-mobility-aios-v12`  
**V12 fork origin:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`  
**Frozen V11 reference branch:** `roadmap/global-mobility-aios-v11`  
**Final V11 documentation-cleanup head:** `ac130deaafa7aa44068e9459facbda2b4df327d6`  
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR  
**Active organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md)  
**Current Track C slice:** V1.3-A — Constitutional Contracts — IMPLEMENTED / FOCUSED CONTRACT TEST PASS / BROADER REPOSITORY ACCEPTANCE NOT YET CLAIMED  
**Technology Radar state:** Wave 1 PILOT COMPLETE / TRIAL-ELIGIBLE; Wave 2 IN PROGRESS with Docling started; Presidio queued  
**Code migration head:** `0076_organization_position_active_identity`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This document is the canonical active roadmap for V12. It describes the project vision, current delivery truth, architecture direction, implementation sequence, validation strategy, operational discipline, and the evidence required before any phase is marked PASS.

---

## 1. Repository generation model

The repository now has intentionally separate V11 and V12 roles.

### V11 — preserved reference checkpoint

V11 preserves the mature product/runtime state through Phase 13.16.10, the Phase 13.17 human-acceptance checkpoint, the V1.3 architecture design created before the branch split, and the final V11-aligned product/delivery roadmap.

V12 originally forked from V11 at:

```text
dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

After the fork, V11 received one final documentation-only cleanup so its own roadmap matched its own README. Its final reference head is:

```text
ac130deaafa7aa44068e9459facbda2b4df327d6
```

That later V11 cleanup does not alter the historical V12 fork origin.

### V12 — active implementation line

All new V1.3 implementation, Product/Human Experience corrections, Technology Radar work, Transparency implementation, runtime control-plane work, and validation evidence should proceed on V12 or bounded descendant branches unless the Human Owner explicitly decides otherwise.

> **V11 preserves the checkpoint. V12 proves and implements the direction.**

---

## 2. What Global Mobility AIOS is

Global Mobility AIOS is being built as a **governed, transparent, high-autonomy digital organization for global mobility**.

It is deliberately not intended to become merely:

- an immigration chatbot;
- a visa questionnaire;
- an immigration CRM with AI features;
- a document uploader;
- a generic workflow engine;
- a generic multi-agent demonstration;
- a generic SaaS/admin dashboard;
- a browser agent with mobility branding;
- a human-approval queue;
- or an agent framework wrapped in a UI.

The target is a professional AI-operated organization in which persistent AI employees can:

- understand mobility goals and circumstances;
- research current official sources;
- reason about pathways and eligibility;
- collaborate with other specialized employees;
- preserve working, agent and organizational memory;
- collect and evaluate Evidence;
- use governed tools and connectors;
- manage Missions, WorkItems and cases;
- prepare professional outputs;
- make decisions inside delegated authority;
- execute bounded operations;
- detect contradictions and abnormal behavior;
- learn from outcomes and human corrections;
- escalate intelligently;
- and remain completely accountable to the Human Owner / Board.

The short project identity is:

> **An AI-operated Global Mobility organization where humans govern the exceptions and the AI organization performs the work.**

---

## 3. Complete long-term mobility lifecycle

AIOS should eventually coordinate the complete mobility lifecycle rather than solving isolated visa tasks.

```text
Human / Business Goal
        ↓
Profile + circumstances + constraints + consent
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
Submission / appointment / external action
        ↓
Authority response
        ↓
Remediation / follow-up / appeal where applicable
        ↓
Relocation / post-arrival obligations
        ↓
Renewal / change of status / family progression
        ↓
Permanent or long-term residence
        ↓
Citizenship / business / investment / long-term global-mobility strategy
```

The lifecycle must support changed goals, alternative pathways, multiple jurisdictions, rejected applications, expired Evidence, superseded rules, changed employers, family dependencies, long-lived case history, and future mobility strategy.

---

## 4. Current product/runtime truth

Current accepted delivery truth remains:

| Programme | State |
|---|---|
| Phases 1–9 | Complete — core platform, Truth Engine, profiles, pathways, timelines and document-intelligence foundations |
| Phase 10 software | Complete — self-updating intelligence foundation, registry workflows, ranking and multi-year planning |
| Phase 10B evidence operations | Ongoing — jurisdiction evidence onboarding, independent review, publication and freshness |
| Phase 11 | Complete — corporate, business, wealth, investment, family-office and tax/treaty mobility |
| Phase 12 | Complete / stabilized — portals, partner APIs, governed automation and agency/government workflow foundations |
| Phase 13.0–13.15 | Complete / PASS where gated — AI organization governance and correctness foundation |
| Phase 13.16.0–13.16.10 | COMPLETE / PASS — role experiences, Contribution/Activity, Cockpit, workspaces, My Mobility, Operations, Evidence/provenance and responsive/accessibility acceptance |
| **Phase 13.17** | **IN PROGRESS / PAUSED BY EVALUATOR** — owner-led human acceptance |
| Phase 14 | NOT STARTED / demand-gated — measured scale after validated demand |

Phase 13.17 remains real acceptance feedback and does not become PASS merely because architecture/runtime work progresses.

---

## 5. Carried-forward accepted quality baseline

Latest accepted runtime evidence before V12 implementation remains:

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
Preserved gmai.db             unchanged at accepted checkpoint
```

These are carried-forward accepted results. They must never be represented as rerun by a later documentation-only or bounded contract patch unless those tests were actually executed again.

GitHub CI PASS must not be claimed unless an attached check/status exists for the relevant commit.

---

## 6. Primary product surfaces

### Global Mobility AIOS Cockpit

The top-level Human Owner / Board surface for organizational health, strategy, risk, quality, autonomy, incidents, transparency and exceptional decisions.

Cockpit should answer:

> **Is my organization healthy, effective, grounded and operating inside the authority I granted it?**

rather than:

> Which hundreds of tasks do I need to approve?

### Board Room

Board Room is a **reserved authority module inside Cockpit**. It is not the name of the entire Owner experience and must not become a generic review inbox.

### Operations

Professional / Operator workspace for cases, Evidence, regulated workflow, applications, reviews, decisions, client work and governed human intervention.

### My Mobility

Mobility-user experience organized around goals, progress, options, documents, evidence requests, deadlines, costs, risks and understandable next actions.

### Portal / employer / partner / authority surfaces

These may expand over time, but must reuse the same identity, Evidence, authority, privacy and canonical-state model rather than inventing parallel truth systems.

---

## 7. Premium product direction

The product should feel like premium enterprise software with a distinct AI operating-system identity, not generic SaaS and not dark sci-fi.

Preferred direction remains:

- deep navy / graphite;
- warm ivory;
- selective editorial serif + modern operational sans;
- restrained glass/depth;
- high-quality iconography;
- subtle purposeful motion;
- luxury-level spacing and typography;
- beautiful information density;
- clear hierarchy and role separation;
- distinct personalities for Cockpit, Board Room, Operations and My Mobility;
- live organization visuals based on real canonical state, never decorative fake activity.

---

## 8. Central V1.3 operating philosophy

V1.3 extends the V1.2 constitutional/governance foundation rather than replacing it.

The purpose of the control architecture is:

> **The safety infrastructure exists to enable autonomy, not suppress it.**

The target operating equation is:

```text
High Autonomy
        +
Strong Evidence
        +
Deterministic Governance
        +
Organizational Immune System
        +
Earned Capability-Specific Authority
        +
Complete Board Inspectability
```

Permanent principle:

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

---

## 9. Human Owner / Board authority

The Human Owner / Board remains the **supreme constitutional authority** of Global Mobility AIOS.

No agent, AI CEO, model, runtime, tool, policy engine, external provider or delegated authority can supersede it.

The Board establishes and controls:

- constitution;
- strategic direction;
- reserved powers;
- autonomy ceilings;
- legal/policy floors;
- major governance policy;
- executive appointment/removal authority;
- critical emergency controls;
- classes of irreversible/reserved actions;
- intervention and override authority.

Supreme authority does not imply operational micromanagement.

> **The Board should govern the organization, not operate it.**

---

## 10. Board by exception

Routine healthy work should normally remain below the Board:

- internal research;
- routine case analysis;
- agent collaboration;
- task assignment;
- document drafting;
- Evidence extraction;
- ordinary WorkItem updates;
- scheduling;
- retries;
- bounded tool use;
- low-risk operational decisions.

Board attention should focus on genuinely reserved/exceptional matters such as:

- Board-reserved government submissions;
- major legal/regulatory commitments;
- exceptional financial commitments;
- major policy changes;
- major autonomy expansions;
- unresolved high-risk Evidence/rule conflicts;
- critical incidents;
- unresolved senior organizational conflicts;
- constitutional or strategic changes.

> **AIOS does the work. The Board makes the important decisions.**

---

## 11. Board Transparency invariant

Permanent rule:

> **Operational autonomy must never create organizational opacity.**

The Board must have on-demand visibility into relevant:

- agent-to-agent conversations;
- delegation chains;
- decisions and recommendations;
- Evidence;
- SourceSnapshots;
- VerifiedRules;
- tool usage;
- external actions;
- policy decisions;
- contradictions;
- escalations;
- incidents;
- circuit-breaker events;
- autonomy promotions/downgrades;
- recovery actions;
- execution history;
- learning outcomes.

This is an inspection right, not a mandatory approval requirement.

```text
Board visibility ≠ Board interruption
```

Cockpit should summarize normal healthy work and allow deep drill-down when the Board chooses.

---

## 12. Transparency and lineage target

Material outcomes should eventually be reconstructable through Decision Lineage:

```text
Canonical outcome
        ↑
Command authorization
        ↑
Independent verification where required
        ↑
Agent recommendation
        ↑
Evidence / VerifiedRules
        ↑
SourceSnapshots
        ↑
Research / tool actions
```

Relevant collaboration should also be reconstructable:

```text
Question / contradiction
        ↓
Agent conversation / delegation
        ↓
Missing Evidence discovered
        ↓
Evidence gathered
        ↓
Contradiction resolved
        ↓
Recommendation
        ↓
Verification
        ↓
Decision
```

Structured rationales, Evidence, policy and lineage are the governance artifacts. Hidden model chain-of-thought is not the audit mechanism.

---

## 13. Memory vs truth

AI employees should have rich continuity, but memory is not authority.

```text
Agent Memory ≠ Canonical AIOS Truth
```

Layers:

| Layer | Purpose |
|---|---|
| Working memory | current run/reasoning |
| Agent memory | previous conversations, tasks and experiences |
| Organizational memory | shared organizational knowledge |
| Canonical AIOS truth | governed facts, Evidence, VerifiedRules and authoritative state |

Permanent principle:

> **Memory provides continuity. Evidence provides authority.**

Consequential decisions should refresh against current governed Evidence, rules, source state, effective dates, case facts and policy.

---

## 14. Context Broker

Agents should receive purpose-scoped, versioned `ContextBundle`s instead of unrestricted database access or maximum-token prompts.

Core context may include:

```text
Agent identity
Position / Department
Authority / autonomy context
Mission / WorkItem
Case / aggregate identity
Relevant facts
Evidence
Applicable VerifiedRules
SourceSnapshots where needed
Known unknowns
Known contradictions
Relevant previous decisions
Conversation summaries
Allowed tools
Sensitivity classification
Policy version
Context version
Context hash
```

Additional slices should load lazily.

> **More relevant truth, not more tokens.**

Every material `AgentRun` should eventually be reconstructable against the exact context/model/program/tool/policy/rule versions used.

---

## 15. Capability, authority, autonomy and risk

These are separate dimensions:

```text
Capability = what the runtime can technically do
Authority  = what AIOS permits
Autonomy   = how independently the actor may exercise authority
Risk       = consequence of the particular action
```

Permanent rule:

```text
CAN DO ≠ MAY DO
```

External tools/frameworks gain no organizational authority merely because they support an operation technically.

---

## 16. V1.3-A — Constitutional Contracts

### Current state

**IMPLEMENTED / FOCUSED CONTRACT TEST PASS / BROADER REPOSITORY ACCEPTANCE NOT YET CLAIMED**

Implementation commit:

```text
7779c1f8e5d3db2e72e047667774284d7cc5f5af
feat: freeze v1.3 constitutional contracts
```

Delivered files:

```text
apps/api/app/core/organization_constitution.py
apps/api/tests/test_organization_constitution.py
docs/ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md
```

### Why this phase exists

The pre-V12 runtime already has valuable deterministic role/path authorization and organization-governance schemas, but some future-facing concepts still appear as loose values such as `risk_level` strings or `requires_board_approval` booleans.

V1.3-A creates a single typed constitutional vocabulary before V1.3-B begins wiring real runtime decisions through it.

### Frozen runtime-facing vocabulary

V1.3-A now defines:

- Board supremacy invariant;
- Board Transparency invariant;
- authorization invariant: **scores route; deterministic gates authorize**;
- A0–A5 autonomy levels;
- R0–R5 risk tiers;
- `HumanReviewReason`;
- consequence/recovery classes;
- organizational activity classes;
- reserved authority classes;
- initial `MaterialActionType` vocabulary;
- immutable Materiality Registry;
- immutable activity transparency policy;
- stable autonomy/risk semantics.

### Focused acceptance evidence

Executed against the new isolated contract module:

```text
python -m py_compile organization_constitution.py
pytest test_organization_constitution.py

13 passed in 0.07s
```

The tests verify:

- complete A0–A5 ladder;
- complete R0–R5 ladder;
- exact HumanReviewReason taxonomy;
- exact consequence/recovery classes;
- reserved authority categories;
- every declared MaterialActionType has a registry rule;
- non-material cognition defaults to R0;
- government submission is material, R5 and Board-reserved;
- every activity class is Board-inspectable;
- MATERIAL/AUTHORITY activity requires durable full lineage;
- conversational activity may compact after policy retention without eliminating the Board inspection right;
- constitutional registries are read-only;
- Board supremacy/transparency/hard-gate invariants are encoded.

### Important non-claims

This phase does **not** yet:

- change database schema;
- change migration head `0076_organization_position_active_identity`;
- mutate `gmai.db`;
- change existing route authorization behavior;
- change current `WorkItemCreate` API compatibility;
- implement `MaterialAction` persistence;
- implement Command Gateway execution;
- implement Decision Readiness;
- implement independent verification;
- implement the Organizational Immune System;
- implement earned-autonomy promotion/demotion;
- implement Transparency indexing/UI;
- integrate Munder/OpenWorker;
- resolve Phase 13.17 findings;
- prove the full API regression;
- prove GitHub CI PASS.

### V1.3-A remaining acceptance before final PASS/seal

Before marking V1.3-A fully sealed, run from the canonical repository checkout:

1. focused constitutional tests;
2. repository policy checks;
3. any import/type/static checks normally required by repository policy;
4. broader API regression if the project acceptance policy requires it for the core-module addition;
5. confirm no migration/schema drift;
6. verify remote branch/diff;
7. record the exact acceptance evidence in the changelog.

Until those canonical-repository checks are run, status remains **implemented / focused-test pass**, not complete project-wide PASS.

---

## 17. A0–A5 autonomy semantics

Frozen meanings:

| Level | Meaning |
|---|---|
| A0 | Prohibited |
| A1 | Human executes |
| A2 | AI prepares; approval required |
| A3 | Autonomous with mandatory review |
| A4 | Autonomous with monitoring and valid recovery controls |
| A5 | Fully autonomous bounded operation |

Autonomy applies to a capability/context, not an entire agent.

Example target:

```text
Austria Immigration Specialist
Official-source research       A5
Document extraction            A5
Evidence assessment            A4
Eligibility analysis           A4
Client explanation             A3
Evidence certification         A2
Government submission          Board-reserved / policy-defined
```

---

## 18. R0–R5 risk tiers

Risk belongs to the action, not the employee.

| Tier | Default direction |
|---|---|
| R0 | summarization, brainstorming and other non-material cognition |
| R1 | routine internal operation + cheap deterministic checks |
| R2 | client-facing preparation + Evidence validation |
| R3 | material recommendation/eligibility + blind independent verification |
| R4 | certification/regulatory publication + blind verification + fresh source validation + appropriate authority |
| R5 | government submission / critical reserved action + full preparation + Human/Board gate |

Verification cost should scale with consequence rather than being maximal everywhere.

---

## 19. Human review reasons

Frozen `HumanReviewReason` values:

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

A human may therefore be required even with very high readiness because the reason can be authority, law or policy rather than uncertainty.

---

## 20. Materiality Registry

Initial constitutional registry:

| Action type | Material | Default risk | Board reserved |
|---|---:|---:|---:|
| `official_source.search` | no | R0 | no |
| `document.summary` | no | R0 | no |
| `internal.note` | no | R0 | no |
| `work_item.assignment` | yes | R1 | no |
| `evidence.candidate` | yes | R2 | no |
| `eligibility.transition` | yes | R3 | no |
| `evidence.certification` | yes | R4 | no by base constitution |
| `verified_rule.publication` | yes | R4 | no by base constitution |
| `external_communication.consequential` | yes | R3 | no by base constitution |
| `government.submission` | yes | R5 | yes |

Later jurisdiction/workflow policy may strengthen requirements. It may not silently downgrade constitutional minimums or remove explicit Board-reserved status without a governed change.

---

## 21. Organization activity transparency classes

V1.3-A freezes:

```text
CONVERSATIONAL
COLLABORATIVE
OPERATIONAL
MATERIAL
AUTHORITY
```

| Class | Board inspectable | Durable record | Full lineage | Policy compaction |
|---|---:|---:|---:|---:|
| CONVERSATIONAL | yes | not always | no | allowed |
| COLLABORATIVE | yes | yes | not always | allowed |
| OPERATIONAL | yes | yes | not always | allowed |
| MATERIAL | yes | yes | yes | not allowed |
| AUTHORITY | yes | yes | yes | not allowed |

This formalizes the earlier principle that transparency does not mean retaining every low-value token forever, while material authority-bearing history must remain reconstructable.

---

## 22. Consequence-aware recovery

Frozen recovery classes:

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
APPEND_ONLY_CORRECTION
```

Examples:

- WorkItem reassignment → potentially REVERSIBLE;
- incorrect external communication → COMPENSATABLE;
- government submission → IRREVERSIBLE;
- Evidence certification later revoked → APPEND_ONLY_CORRECTION.

Recovery semantics belong to business commands, not arbitrary database rows.

Irreversible actions require stronger pre-execution controls and pre-mortem validation.

---

## 23. Scores route; gates authorize

Permanent invariant:

> **No material action is authorized by a Decision Readiness scalar alone.**

Conceptually:

```text
Identity valid
AND Authority valid
AND Scope valid
AND Mandatory Evidence present
AND Policy gates pass
AND No blocking contradiction
AND Expected version matches
AND Required verification completed
AND Readiness threshold satisfied
→ EXECUTE
```

Examples:

```text
Readiness 98% + mandatory Evidence missing → BLOCK
Readiness 100% + Board-reserved government submission → BOARD GATE
```

---

## 24. Canonicalization Gateway

V1.2 semantic sovereignty remains foundational:

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

Permanent constraints:

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

Canonicalization should be implemented progressively, workflow by workflow.

---

## 25. Command Gateway target

The Command Gateway is the planned controlled mutation boundary for material autonomous production state.

It is **not** a universal human approval gateway.

Healthy future flow:

```text
Agent
→ MaterialAction
→ identity / authority / scope
→ Evidence / policy / contradiction
→ expected-version / idempotency
→ required verification / readiness
→ AUTO EXECUTE
```

Human involvement happens only where law, policy, authority, uncertainty or consequence requires it.

---

## 26. Optimistic concurrency

Parallel agents require explicit version protection.

```text
Agent A reads Case v43
Agent B reads Case v43
A commits → v44
B submits expected_version=43
actual_version=44
→ STALE
→ refresh / rebase / reevaluate
```

Use:

- expected-version/precondition checks;
- idempotency;
- bounded retries;
- backoff;
- aggregate serialization where necessary;
- tenant/case/mission sharding.

CRDT-style approaches are reserved for genuinely mergeable collaborative state, not authoritative regulated state.

---

## 27. Organizational Immune System target

The V1.3 safety/quality layer should eventually include:

```text
Evidence Integrity Monitor
Contradiction Detector
Anomaly Detector
Decision Readiness Engine
Capability Performance Monitor
Dynamic Autonomy Manager
Circuit Breakers
Rate / Budget Protection
Blast-Radius Controller
Incident Detector
Root-Cause Classifier
Escalation Router
Shadow Evaluation Engine
Learning Feedback
```

Desired behavior:

> **Almost invisible during healthy operation, extremely capable when abnormal behavior happens.**

Every material intervention must be explainable from observable signals, policy and recorded Evidence.

---

## 28. Incident and circuit-breaker principles

Examples:

```text
Unexpected bulk mutations
→ stop affected capability

Contradiction spike
→ temporary scoped restriction

Government API schema change
→ suspend affected submission path

Agent acts outside normal scope
→ block material actions

Runaway tool/model loop
→ terminate run

Expired VerifiedRule
→ block dependent autonomous conclusion
```

Restrictions should be scope-limited where possible.

Correlated failures should aggregate into one organizational incident rather than flooding the Board.

---

## 29. Learning architecture

Use three distinct levels:

```text
OrganizationActivity
        ↓
LearningRecord
        ↓
CuratedLearningExample
```

Outcome labels should remain explicit, including:

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

Human corrections are high-value labeled learning signals.

---

## 30. Performance and scalability doctrine

### P1 — Pay for risk

Verification effort scales with consequence, uncertainty and novelty.

### P2 — Recompute only what changed

Readiness, Evidence and policy components should be incremental/version-aware.

### P3 — Load only what is needed

Context should be purpose-scoped, lazy, composable and versioned.

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

Verifier/cache identity should include relevant Evidence, case facts, VerifiedRules, policy, jurisdiction, effective dates and program/model versions.

### P7 — Instrument from day one

Measure latency, cost, context size, verification overhead, retries, false/missed escalations, source freshness, Board workload, incident rate, autonomy rate and transparency lag.

Conceptual principle:

> **Governance Cost ∝ Risk × Uncertainty × Novelty**

---

## 31. External runtime / provider independence

AIOS must survive replacement or disappearance of any external model, agent or execution framework.

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

AIOS owns Mission/WorkItem meaning, Evidence, VerifiedRules, authority, canonical activity, Decision Lineage, case state and organizational truth.

> **AIOS Semantic Sovereignty is permanent.**

---

## 32. Technology Radar state

Current state:

| Technology | Capability | State |
|---|---|---|
| Promptfoo | AI quality/safety evaluation | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | neutral telemetry | PILOT COMPLETE / TRIAL-ELIGIBLE |
| ClamAV | malware scanning | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | document normalization | PILOT IN PROGRESS |
| Presidio | privacy gateway | QUEUED PILOT |
| urlwatch | source monitoring | QUEUED PILOT |
| Munder Difflin | agent organization reference | CONTROLLED RESEARCH |
| OpenWorker | execution/Coworker reference | CONTROLLED RESEARCH |
| Temporal | durable execution | DEFERRED PILOT |
| OpenFGA | relationship authorization | DEFERRED PILOT |

Adoption lifecycle remains evidence-driven:

```text
REFERENCE → RESEARCH → BENCHMARK → PILOT → TRIAL → ADOPT
```

or explicit REJECT where appropriate.

Technology exists to improve mobility outcomes. AIOS must not reorganize itself around a fashionable framework.

---

## 33. Coordinated parallel evolution

Three primary project tracks continue in parallel.

### Track A — Product / Human Experience

- Phase 13.17 human acceptance;
- bounded UX corrections;
- Cockpit / Operations / My Mobility refinement;
- role clarity;
- evidence/provenance explainability;
- mobile/responsive/accessibility quality;
- real workflow usability.

### Track B — Technology Radar / Platform Evolution

- document/privacy intelligence;
- regulatory monitoring;
- runtime/retrieval/quality experiments;
- professional-output technologies when justified;
- explicit adoption/rejection evidence.

### Track C — High-Autonomy Organization

- constitutional contracts;
- Governance Kernel;
- Transparency Foundation;
- persistent agent/context architecture;
- governed vertical workflows;
- Decision Readiness;
- independent verification;
- Organizational Immune System;
- earned autonomy;
- runtime adapters;
- Live Organization;
- Board Transparency experience;
- learning/optimization.

No track globally blocks the others. Shared contracts and discoveries must be reconciled before incompatible delivery.

---

## 34. Validation & commercial proof lane

Architecture quality must be converted into external evidence.

This cross-cutting lane should progress through:

```text
Owner-led acceptance
        ↓
External professional usability
        ↓
Real mobility workflow / real case
        ↓
First external cases
        ↓
Repeatable jurisdiction workflow
        ↓
First paying professional / organization
        ↓
Measured demand
```

Track C must not become endless control-plane design without proving a real professional workflow.

The most important future proof point is one real mobility case completed substantially by AIOS with a real external user/professional and fully reconstructable Evidence/decision lineage.

---

## 35. Legal, privacy and data-governance maturity

V12 must also convert principles into explicit governed policy over time, including:

- GDPR lawful basis by data class/purpose;
- purpose limitation;
- special-category data handling;
- retention/deletion/correction rights;
- model-provider data-use boundaries;
- cross-border transfers;
- agent-memory retention;
- LearningRecord eligibility;
- CuratedLearningExample eligibility;
- privilege/confidentiality handling;
- professional/legal representation boundaries;
- jurisdiction-specific submission authority;
- human-accountability requirements.

Board transparency must coexist with lawful sensitivity controls.

---

## 36. V1.3 implementation sequence

### V1.3-A — Constitutional Contracts

**State:** IMPLEMENTED / focused 13-test PASS / repository-wide acceptance not yet claimed.

See Section 16 and [ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md](ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md).

### V1.3-B — Minimal Governance Kernel

Implement a deliberately small foundation:

- actor identity;
- capability authority;
- expected-version contract;
- idempotency;
- `MaterialAction` envelope;
- deterministic policy-decision foundation;
- Command Gateway foundation;
- trace identity;
- canonical `OrganizationActivity` integration.

Acceptance direction:

- unauthorized material action fails;
- stale action fails;
- duplicate consequential action is blocked by idempotency;
- an authorized low-risk action can execute without human approval;
- activity/trace record is created;
- existing runtime compatibility remains preserved.

### V1.3-C — Transparency Foundation

Implement early:

- AgentConversation / AgentMessage capture semantics;
- activity classification;
- retention/sensitivity boundaries;
- trace correlation;
- `ToolActionRecord` foundation;
- Decision Lineage foundation;
- transparency query surfaces.

Acceptance direction:

- Board/developer can reconstruct a governed test decision from action back to actor/policy/Evidence;
- material conversation/tool activity is traceable;
- secrets are not exposed;
- normal activity is summarized rather than spammed.

### V1.3-D — Context & Agent Identity

Implement:

- persistent agent identity;
- Position / Department linkage;
- `ContextBundle`;
- version/hash;
- `AgentRun` lineage;
- working vs long-term vs organizational memory boundaries;
- purpose-scoped retrieval.

Acceptance direction:

- a material run is reconstructable;
- context is scoped rather than unrestricted;
- memory cannot silently become canonical truth.

### V1.3-E — First Governed Vertical Workflow

Use a real mobility workflow:

```text
Evidence
→ contextual agent reasoning
→ typed candidate
→ risk-required verification
→ Command Gateway
→ canonical state
→ OrganizationActivity
→ Decision Lineage
→ Transparency
→ LearningRecord where meaningful
```

This is the critical architecture proof point.

### V1.3-F — Decision Readiness

Implement:

- auditable readiness components;
- versioned formula/routing;
- hard gates;
- incremental recomputation;
- `DecisionReadinessSnapshot`;
- Board/Professional explanation output;
- calibration telemetry.

### V1.3-G — Independent Verification

Implement:

- blind peer verification;
- contradiction comparison;
- R3/R4/R5 routing;
- PRE_COMMIT / POST_COMMIT / BACKGROUND modes;
- exact-state cache/hash identity;
- verification lineage.

### V1.3-H — Organizational Immune System

Implement incrementally:

- anomaly signals;
- contradiction-rate monitoring;
- circuit breakers;
- blast-radius limits;
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
- capability-specific promotion;
- lower-risk automated promotion where policy permits;
- dynamic downgrade;
- recovery criteria;
- governance review;
- autonomy history.

### V1.3-J — Agent Organization Runtime

Evaluate runtime candidates against:

- identity;
- hierarchy;
- messaging;
- memory;
- delegation;
- scheduling;
- failure handling;
- tools;
- observability;
- multitenancy;
- authority compatibility;
- transparency compatibility;
- AIOS semantic sovereignty.

External candidate outcomes may be ADOPT / TRIAL / WRAP / BORROW / FORK / REJECT.

### V1.3-K — Execution / Coworker Runtime

Implement provider-neutral bounded execution for:

- files;
- documents;
- browser;
- terminal/code;
- email;
- calendar;
- MCP/connectors;
- scheduled work;
- external actions;
- resumable execution jobs;
- sandbox classes.

### V1.3-L — Live Organization

Bring canonical runtime state into Cockpit:

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
- performance.

No fake/simulated activity where the product claims live organization state.

### V1.3-M — Board Transparency Experience

Build:

- Organization Explorer;
- Decision Explorer;
- Conversation Explorer;
- Case Timeline;
- Evidence/Rule lineage;
- Tool Activity Explorer;
- Agent History;
- Incident Timeline;
- Autonomy History;
- organization-wide grounded search.

### V1.3-N — Learning & Optimization

Deepen:

- LearningRecords;
- human correction analysis;
- capability performance;
- readiness calibration;
- policy tuning;
- routing optimization;
- false/missed escalation analysis;
- evaluation datasets;
- curated learning examples;
- permitted model/program improvement.

---

## 37. Dependency logic

Recommended dependency shape:

```text
A Constitutional Contracts
        ↓
B Governance Kernel
        ├────────→ C Transparency Foundation
        └────────→ D Context & Agent Identity
                         ↓
                 E Vertical Workflow
                         ↓
              F Readiness + G Verification
                         ↓
                 H Immune System
                         ↓
                 I Earned Autonomy
                         ↓
        J Agent Runtime + K Execution Runtime
                         ↓
               L Live Organization
                         ↓
          M Board Transparency Experience
                         ↓
               N Learning/Optimization
```

Bounded J/K research may happen earlier, but production mutation integration must respect the governance contracts already accepted.

---

## 38. Current immediate implementation priority

The active engineering priority is:

### First — seal V1.3-A correctly

Run the new constitutional tests from the canonical repository checkout and the repository-policy/appropriate broader checks. Record the exact evidence. Do not call V1.3-A full PASS before that evidence exists.

### Then — V1.3-B Minimal Governance Kernel

The first B slice should avoid a giant framework. Prefer a minimal vertical contract that maps one real existing low-risk organization action into:

```text
Actor
→ MaterialAction
→ deterministic authority/policy evaluation
→ expected version / idempotency
→ canonical action
→ traceable OrganizationActivity
```

The objective is to prove the kernel, not generalize every domain action immediately.

---

## 39. First vertical workflow direction

The architecture should ultimately be proven using a real mobility workflow, for example:

```text
Blocked mobility case
        ↓
Agent receives scoped ContextBundle
        ↓
Evidence retrieved / missing Evidence identified
        ↓
VerifiedRules checked
        ↓
Eligibility candidate
        ↓
Decision Readiness
        ↓
Independent verifier if R3
        ↓
Command Gateway
        ↓
Professional/Human escalation only if required
        ↓
Canonical eligibility transition
        ↓
OrganizationActivity + Decision Lineage
        ↓
Board-inspectable transparency
        ↓
Learning outcome
```

That one workflow should exercise many architecture layers against real product behavior.

---

## 40. Cockpit target information architecture

Long-term Cockpit:

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

Top level should summarize health and exceptions. Board Room remains reserved. Transparency/search allows deep investigation without cluttering the default experience.

---

## 41. Board organization-wide search target

Future grounded queries should support questions such as:

- Why was this applicant marked ineligible?
- Which agents contributed?
- What did they discuss?
- Which Evidence supported the conclusion?
- Which VerifiedRule/source was used?
- Who changed canonical case state?
- Why was an agent capability downgraded?
- Which government submissions happened in a time window?
- Which cases rely on a given rule?
- Which contradictions remain unresolved?
- Which capabilities are declining in quality?

Answers must be grounded in governed lineage rather than invented summaries.

---

## 42. Success metrics

The project should measure outcomes rather than infrastructure volume.

Primary metrics:

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
p50/p95 material-action latency
Cost per completed workflow
Stale/retry rate
Incident frequency
Recovery effectiveness
Decision-lineage completeness
Conversation/material-action traceability
External user success
Professional acceptance
Repeat usage / willingness to pay when measured
```

Desired direction:

```text
Autonomous completion ↑
Quality ↑
Evidence grounding ↑
Traceability ↑
Board transparency ↑
Capability reliability ↑
External validation ↑

Board operational workload ↓
Critical errors ↓
False/missed escalations ↓
Cost per outcome ↓
Latency ↓
Opaque decisions ↓
```

---

## 43. Repository / acceptance discipline

Every meaningful patch should:

1. verify branch/SHA/current remote state;
2. inspect relevant canonical docs/contracts;
3. freeze exact implementation boundary;
4. preserve unrelated work;
5. implement incrementally;
6. run focused tests appropriate to changed behavior;
7. run broader acceptance where required;
8. perform browser/runtime review for user-facing changes;
9. update `ROADMAP.md` for project-delivery state;
10. update `CHANGELOG.md` for meaningful delivery;
11. inspect exact diff/whitespace;
12. commit/push truthfully;
13. verify remote branch state;
14. preserve migration/database/release invariants;
15. never claim tests, CI, runtime implementation or PASS without evidence.

---

## 44. Frozen architecture invariants

1. Human Owner / Board is supreme authority.
2. Board governs mainly by exception rather than routine approval.
3. Operational autonomy must never create organizational opacity.
4. Board has on-demand visibility into material organizational activity subject to lawful sensitivity controls.
5. Agent collaboration contributing to material outcomes remains sufficiently reconstructable.
6. Material decisions require Decision Lineage.
7. AI employees may hold real delegated authority.
8. Authority is capability-specific and bounded.
9. Autonomy is capability-specific and earned from evidence.
10. Agents cannot self-promote their authority/autonomy.
11. Rich memory does not automatically become canonical truth.
12. Memory provides continuity; Evidence provides authority.
13. Material truth crosses typed deterministic canonicalization.
14. Material autonomous mutations cross the Command Gateway once that runtime exists.
15. Decision Readiness routes; hard gates authorize.
16. Verification depth scales with risk, uncertainty and novelty.
17. Legal/policy human requirements override confidence/readiness.
18. Parallel agents use explicit version/concurrency controls.
19. External frameworks provide capability; AIOS owns semantics and authority.
20. The Organizational Immune System must be explainable.
21. Circuit breakers/autonomy changes should be scope-limited where possible.
22. Irreversible actions receive stronger pre-execution controls.
23. Recovery semantics distinguish reversible, compensatable, irreversible and append-only correction.
24. Learning preserves labeled outcomes/corrections rather than treating agent statements as truth.
25. Governance cost scales with risk rather than being maximal for every operation.
26. Context is purpose-scoped, lazy, composable and versioned.
27. One governance model does not require one physical execution bottleneck.
28. Transparency summaries do not replace required underlying governed records.
29. Secrets and protected data remain secure under Board transparency.
30. Conversation is OrganizationActivity but not authority.
31. Provider-local state/logs do not silently become canonical AIOS truth.
32. Agents may be wrong while thinking; AIOS may not be wrong silently when committing truth.

---

## 45. Final project direction

Global Mobility AIOS is intended to become more than software that helps complete immigration tasks.

It should become a **transparent AI-operated professional Global Mobility organization** capable of understanding goals, organizing work, preserving institutional memory, gathering and governing Evidence, tracking changing regulations, coordinating specialized AI employees, producing professional outputs, executing authorized actions, learning from corrections, detecting abnormal behavior, containing mistakes and escalating intelligently.

The Human Board retains supreme authority without becoming the organization's manual operator.

The implementation target is:

```text
Maximum useful autonomy
        +
Minimum necessary human interruption
        +
Strong deterministic / Evidence boundaries
        +
Measured quality
        +
Bounded consequence
        +
Complete Board inspectability
        +
Real external product proof
```

The project should continue ambitiously, but every increase in architectural sophistication must increasingly be justified by runtime evidence and real mobility outcomes.

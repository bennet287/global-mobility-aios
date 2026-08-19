# Global Mobility AIOS — Active V12 Product, Platform & High-Autonomy Roadmap

**Roadmap generation:** V12.3  
**Date:** 2026-08-20  
**Active development branch:** `roadmap/global-mobility-aios-v12`  
**V12 fork origin:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`  
**Frozen V11 reference branch:** `roadmap/global-mobility-aios-v11`  
**Final V11 documentation-cleanup head:** `ac130deaafa7aa44068e9459facbda2b4df327d6`  
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR  
**Active organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md)  
**V1.3-A:** Constitutional Contracts — **COMPLETE / PASS / SEALED**  
**Current Track C slice:** V1.3-B — Minimal Governance Kernel — **IN PROGRESS; B.1 IMPLEMENTED / ISOLATED FOCUSED TEST PASS / CANONICAL REPOSITORY ACCEPTANCE PENDING**  
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

### Historical compatibility milestone — v10.22

The active V12 roadmap intentionally preserves selected older delivery markers that are still protected by repository regression tests and remain meaningful architectural history.

`v10.22` introduced **multi-batch tranche operations** around the already-governed jurisdiction Evidence workflow. The work scaled planning and preparation across multiple reviewed evidence batches while explicitly preserving human review boundaries: it did not add automatic source certification, legal interpretation, assertion approval, VerifiedRule publication, snapshot mutation, or global coverage claims.

The canonical implementation note remains [COVERAGE_TRANCHE_OPERATIONS_V10_22.md](COVERAGE_TRANCHE_OPERATIONS_V10_22.md), and the historical database evolution associated with that delivery lineage includes migration marker `0032_initial_rule_assertions`.

This historical marker is retained in the active roadmap so later roadmap rewrites do not accidentally erase repository acceptance contracts or the provenance of the governed coverage-operations foundation.

---

## 5. Accepted quality and current V1.3 evidence

### Carried-forward product baseline

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
Preserved gmai.db             unchanged at accepted checkpoint
```

These are carried-forward accepted results and must never be represented as rerun unless they actually were.

### V1.3-A final canonical acceptance — 2026-08-20

The canonical Windows V12 checkout produced:

```text
Constitutional contract tests  13 passed / 1 warning / 0 failed in 0.14s
Repository policy              PASS
v10.22 regression rerun        1 passed / 1 warning in 0.08s
Full API regression            886 passed / 5 skipped / 1 warning / 0 failed in 337.70s
Migration check                PASS
Migration head                 0076_organization_position_active_identity
Registered tables              118
Physical schema                OK
Local DB schema check          PASS
Registered / actual tables     118 / 118
Physical tables                119 incl. alembic_version
git diff --check               clean
git status                     clean / synchronized V12
```

The single warning is the existing Starlette/httpx TestClient deprecation warning and is not a V1.3-A blocker.

See [V1_3_A_ACCEPTANCE_2026-08-20.md](V1_3_A_ACCEPTANCE_2026-08-20.md) for the exact acceptance record.

V1.3-A is therefore:

```text
COMPLETE
PASS
SEALED
```

No GitHub CI PASS is claimed without attached status/check evidence.

### V1.3-B.1 implementation evidence

B.1 was published in commit:

```text
d351ad85f5c3464178b56dd9da6ac5c83090a27a
feat: start v1.3-b governance kernel
```

Its isolated pre-publish focused suite produced:

```text
19 passed in 0.05s
```

This is implementation evidence only. Canonical V12 checkout acceptance for B.1 remains pending.

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

> **The safety infrastructure exists to enable autonomy, not suppress it.**

Target operating equation:

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

The Board must have on-demand visibility into relevant agent collaboration, decisions, Evidence, SourceSnapshots, VerifiedRules, tools, external actions, policy decisions, contradictions, escalations, incidents, circuit-breaker events, autonomy changes, recovery actions, execution history and learning outcomes.

This is an inspection right, not a mandatory approval requirement.

```text
Board visibility ≠ Board interruption
```

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

Relevant collaboration should also be reconstructable from question/contradiction through Evidence gathering, resolution, recommendation, verification and decision.

Structured rationales, Evidence, policy and lineage are governance artifacts. Hidden model chain-of-thought is not the audit mechanism.

---

## 13. Memory vs truth

```text
Agent Memory ≠ Canonical AIOS Truth
```

| Layer | Purpose |
|---|---|
| Working memory | current run/reasoning |
| Agent memory | previous conversations, tasks and experiences |
| Organizational memory | shared organizational knowledge |
| Canonical AIOS truth | governed facts, Evidence, VerifiedRules and authoritative state |

> **Memory provides continuity. Evidence provides authority.**

---

## 14. Context Broker

Agents should receive purpose-scoped, versioned `ContextBundle`s instead of unrestricted database access or maximum-token prompts.

Core context may include Agent identity, Position/Department, authority/autonomy context, Mission/WorkItem, case/aggregate identity, relevant facts, Evidence, VerifiedRules, SourceSnapshots, known unknowns/contradictions, previous decisions, conversation summaries, allowed tools, sensitivity classification, policy version, context version and context hash.

> **More relevant truth, not more tokens.**

---

## 15. Capability, authority, autonomy and risk

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

---

## 16. V1.3-A — Constitutional Contracts

### Final state

**COMPLETE / PASS / SEALED**

Implementation commit:

```text
7779c1f8e5d3db2e72e047667774284d7cc5f5af
feat: freeze v1.3 constitutional contracts
```

Delivered:

```text
apps/api/app/core/organization_constitution.py
apps/api/tests/test_organization_constitution.py
docs/ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md
docs/V1_3_A_ACCEPTANCE_2026-08-20.md
```

V1.3-A freezes:

- Board supremacy invariant;
- Board Transparency invariant;
- **scores route; deterministic gates authorize**;
- A0–A5 autonomy levels;
- R0–R5 risk tiers;
- `HumanReviewReason`;
- consequence/recovery classes;
- organizational activity classes;
- reserved authority classes;
- initial `MaterialActionType` vocabulary;
- immutable Materiality Registry;
- immutable activity transparency policy.

Final acceptance is recorded in Section 5 and the dedicated acceptance record. V1.3-A is the constitutional floor for all subsequent Track C implementation.

---

## 17. V1.3-B — Minimal Governance Kernel

### Current state

**IN PROGRESS — B.1 IMPLEMENTED / ISOLATED FOCUSED TEST PASS / CANONICAL REPOSITORY ACCEPTANCE PENDING**

B.1 implementation commit:

```text
d351ad85f5c3464178b56dd9da6ac5c83090a27a
feat: start v1.3-b governance kernel
```

Delivered:

```text
apps/api/app/services/organization_governance_kernel.py
apps/api/tests/test_organization_governance_kernel.py
docs/V1_3_B_MINIMAL_GOVERNANCE_KERNEL.md
```

The repository already had `OrganizationCommandContext`, canonical fingerprints, idempotency helpers, tenant-aware command utilities and durable `OrganizationActivity` append/stage mechanics. B.1 deliberately reuses those foundations rather than creating a competing command system.

B.1 adds:

- `CapabilityAuthority`;
- typed `MaterialAction` envelope;
- effective risk floor enforcement;
- deterministic authority/scope/risk evaluation;
- expected-version/precondition checks;
- idempotent replay/conflict decisions;
- typed policy disposition;
- A0–A5 execution/review routing;
- Board-reserved override protection;
- trace ID and Activity projection compatible with the existing Activity runtime.

Typed outcomes:

```text
AUTO_EXECUTE
BLOCK
REVIEW_REQUIRED
IDEMPOTENT_REPLAY
```

Important invariant already encoded in B.1:

```text
Government submission
R5
Board reserved
→ REVIEW_REQUIRED even at A5
```

B.1 is schema-neutral and does not yet execute a production domain mutation through the gateway. Canonical repository acceptance is the immediate next gate.

---

## 18. A0–A5 autonomy semantics

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

## 19. R0–R5 risk tiers

| Tier | Default direction |
|---|---|
| R0 | summarization, brainstorming and other non-material cognition |
| R1 | routine internal operation + cheap deterministic checks |
| R2 | client-facing preparation + Evidence validation |
| R3 | material recommendation/eligibility + blind independent verification |
| R4 | certification/regulatory publication + blind verification + fresh source validation + appropriate authority |
| R5 | government submission / critical reserved action + full preparation + Human/Board gate |

B.1 prevents an action from declaring a risk below its constitutional Materiality Registry floor.

---

## 20. Human review reasons

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

A human may be required even with high readiness because the reason can be authority, law or policy rather than uncertainty.

---

## 21. Materiality Registry

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

Later jurisdiction/workflow policy may strengthen requirements but may not silently downgrade constitutional minimums.

---

## 22. Organization activity transparency classes

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

B.1 currently projects governance evaluations into the existing physical `operational` Activity class while preserving constitutional `MATERIAL` / `AUTHORITY` class in payload. V1.3-C will deepen the Transparency Foundation without prematurely rewriting the database enum contract.

---

## 23. Consequence-aware recovery

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

---

## 24. Scores route; gates authorize

> **No material action is authorized by a Decision Readiness scalar alone.**

Target authorization logic:

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

B.1 currently implements the identity/authority/scope/risk/version/idempotency/policy/autonomy/reserved-authority subset. Evidence, contradiction, verification and Decision Readiness gates arrive in later roadmap slices.

---

## 25. Canonicalization Gateway

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

---

## 26. Command Gateway target

The Command Gateway is the controlled mutation boundary for material autonomous production state. It is **not** a universal human approval gateway.

B.1 establishes the deterministic evaluation foundation; B.2 should prove one reversible existing domain command through it.

Target healthy flow:

```text
Agent
→ MaterialAction
→ identity / authority / scope
→ Evidence / policy / contradiction
→ expected-version / idempotency
→ required verification / readiness
→ AUTO EXECUTE
```

---

## 27. Optimistic concurrency

```text
Agent A reads Case v43
Agent B reads Case v43
A commits → v44
B submits expected_version=43
actual_version=44
→ STALE
→ refresh / rebase / reevaluate
```

B.1 already provides the expected-version/precondition decision contract. Later integration must preserve bounded retries, backoff and aggregate serialization where needed.

---

## 28. Organizational Immune System target

Future components include Evidence Integrity Monitor, Contradiction Detector, Anomaly Detector, Decision Readiness Engine, Capability Performance Monitor, Dynamic Autonomy Manager, Circuit Breakers, Rate/Budget Protection, Blast-Radius Controller, Incident Detector, Root-Cause Classifier, Escalation Router, Shadow Evaluation and Learning Feedback.

> **Almost invisible during healthy operation, extremely capable when abnormal behavior happens.**

---

## 29. Incident and circuit-breaker principles

Examples:

```text
Unexpected bulk mutations → stop affected capability
Contradiction spike → temporary scoped restriction
Government API schema change → suspend affected submission path
Agent acts outside normal scope → block material actions
Runaway tool/model loop → terminate run
Expired VerifiedRule → block dependent autonomous conclusion
```

Restrictions should be scope-limited where possible and correlated failures should aggregate into organizational incidents rather than flooding the Board.

---

## 30. Learning architecture

```text
OrganizationActivity
        ↓
LearningRecord
        ↓
CuratedLearningExample
```

Outcome labels remain explicit, including PROPOSED, ACCEPTED, MODIFIED, REJECTED, CONTRADICTED, STALE, SUPERSEDED, HUMAN_CORRECTED, EXECUTION_FAILED, PARTIAL and ROLLED_BACK.

Not every event becomes training truth.

---

## 31. Performance and scalability doctrine

- **P1 Pay for risk** — verification effort scales with consequence, uncertainty and novelty.
- **P2 Recompute only what changed** — readiness/Evidence/policy components are version-aware.
- **P3 Load only what is needed** — context is purpose-scoped and lazy.
- **P4 Block only when necessary** — distinguish PRE_COMMIT / POST_COMMIT / BACKGROUND.
- **P5 Centralize governance, distribute execution** — one authority model must not become one global mutex.
- **P6 Cache exact governed state only** — cache identity includes relevant Evidence/facts/rules/policy/jurisdiction/effective dates/program versions.
- **P7 Instrument from day one** — measure latency, cost, retries, verification overhead, context size, source freshness, escalation quality, Board workload and autonomy.

> **Governance Cost ∝ Risk × Uncertainty × Novelty**

---

## 32. External runtime / provider independence

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

## 33. Technology Radar state

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

```text
REFERENCE → RESEARCH → BENCHMARK → PILOT → TRIAL → ADOPT
```

or explicit REJECT where appropriate.

---

## 34. Coordinated parallel evolution

### Track A — Product / Human Experience

Phase 13.17 human acceptance, bounded UX corrections, Cockpit/Operations/My Mobility refinement, role clarity, Evidence/provenance explainability, responsive/accessibility quality and real workflow usability.

### Track B — Technology Radar / Platform Evolution

Document/privacy intelligence, regulatory monitoring, runtime/retrieval/quality experiments, professional-output technologies when justified and explicit adoption/rejection evidence.

### Track C — High-Autonomy Organization

Constitutional contracts, Governance Kernel, Transparency Foundation, persistent agent/context architecture, governed vertical workflows, Decision Readiness, independent verification, Organizational Immune System, earned autonomy, runtime adapters, Live Organization, Board Transparency experience and learning/optimization.

No track globally blocks the others. Shared contracts and discoveries must be reconciled before incompatible delivery.

---

## 35. Validation & commercial proof lane

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

Track C must not become endless control-plane design without proving real professional work.

---

## 36. Legal, privacy and data-governance maturity

V12 must convert principles into explicit governed policy over time, including GDPR lawful basis by data class/purpose, purpose limitation, special-category data handling, retention/deletion/correction rights, model-provider data-use boundaries, cross-border transfers, agent-memory retention, LearningRecord/CuratedLearningExample eligibility, privilege/confidentiality, professional/legal representation boundaries, jurisdiction-specific submission authority and human-accountability requirements.

Board transparency must coexist with lawful sensitivity controls.

---

## 37. V1.3 implementation sequence

### V1.3-A — Constitutional Contracts

**State:** **COMPLETE / PASS / SEALED**.  
See [ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md](ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md) and [V1_3_A_ACCEPTANCE_2026-08-20.md](V1_3_A_ACCEPTANCE_2026-08-20.md).

### V1.3-B — Minimal Governance Kernel

**State:** **IN PROGRESS**. B.1 deterministic governance evaluation is implemented; canonical V12 checkout acceptance is pending.

B.1 provides actor/capability authority, `MaterialAction`, expected-version and idempotency decisions, deterministic policy disposition, Board-reserved routing, autonomy routing, trace identity and Activity projection.

After B.1 acceptance, B.2 should integrate one existing reversible low-risk organization action through the kernel and canonical Activity path.

### V1.3-C — Transparency Foundation

Implement AgentConversation/AgentMessage capture semantics, activity classification, retention/sensitivity boundaries, trace correlation, `ToolActionRecord`, Decision Lineage foundation and transparency queries.

### V1.3-D — Context & Agent Identity

Implement persistent agent identity, Position/Department linkage, `ContextBundle`, version/hash, `AgentRun` lineage, memory boundaries and purpose-scoped retrieval.

### V1.3-E — First Governed Vertical Workflow

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

Implement auditable readiness components, versioned routing, hard gates, incremental recomputation, `DecisionReadinessSnapshot`, explanation output and calibration telemetry.

### V1.3-G — Independent Verification

Implement blind peer verification, contradiction comparison, R3/R4/R5 routing, PRE_COMMIT/POST_COMMIT/BACKGROUND modes, exact-state cache identity and verification lineage.

### V1.3-H — Organizational Immune System

Implement anomaly signals, contradiction monitoring, circuit breakers, blast-radius limits, root-cause classification, scope-limited quarantine, incident aggregation, escalation routing and Board-inspectable intervention history.

### V1.3-I — Earned Autonomy

Implement shadow mode, `AutonomyEvidenceProfile`, promotion criteria, capability-specific promotion, dynamic downgrade, recovery criteria, governance review and autonomy history.

### V1.3-J — Agent Organization Runtime

Evaluate runtime candidates against identity, hierarchy, messaging, memory, delegation, scheduling, failure handling, tools, observability, multitenancy, authority/transparency compatibility and AIOS Semantic Sovereignty.

### V1.3-K — Execution / Coworker Runtime

Implement provider-neutral bounded execution for files, documents, browser, terminal/code, email, calendar, MCP/connectors, scheduled work, external actions, resumable jobs and sandbox classes.

### V1.3-L — Live Organization

Bring canonical agents, departments, Missions, WorkItems, collaboration, blocked work, incidents, autonomy, quality, cost and performance into Cockpit. No fake/simulated activity where the product claims live state.

### V1.3-M — Board Transparency Experience

Build Organization Explorer, Decision Explorer, Conversation Explorer, Case Timeline, Evidence/Rule lineage, Tool Activity Explorer, Agent History, Incident Timeline, Autonomy History and grounded organization-wide search.

### V1.3-N — Learning & Optimization

Deepen LearningRecords, human-correction analysis, capability performance, readiness calibration, policy/routing optimization, escalation analysis, evaluation datasets and curated learning examples.

---

## 38. Dependency logic

```text
A Constitutional Contracts [SEALED]
        ↓
B Governance Kernel [ACTIVE]
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

Bounded J/K research may happen earlier, but production mutation integration must respect accepted governance contracts.

---

## 39. Current immediate implementation priority

### First — canonical acceptance of V1.3-B.1

After pulling `d351ad85...`, run from the canonical V12 checkout:

```text
pytest apps/api/tests/test_organization_governance_kernel.py -q
scripts/check_repo_policy.py --root .
pytest apps/api/tests -q
git diff --check
git status -sb
```

Because B.1 is schema-neutral, the migration head should remain `0076_organization_position_active_identity`. If broader acceptance is clean, record exact evidence and mark B.1 PASS.

### Then — V1.3-B.2 first real governed command

Choose one **existing, reversible, low-risk organization operation** and route it through:

```text
Actor
→ MaterialAction
→ deterministic authority/policy evaluation
→ expected version / idempotency
→ existing domain command
→ canonical OrganizationActivity
→ trace correlation
```

Acceptance must prove unauthorized/stale/conflicting actions are blocked, an authorized low-risk action can execute without unnecessary human approval, exact replay is idempotent, and the result is traceable.

Do not migrate every command at once.

---

## 40. First vertical workflow direction

A later V1.3-E proof should use a real mobility workflow such as:

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

---

## 41. Cockpit target information architecture

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

Top level summarizes health and exceptions. Board Room remains reserved.

---

## 42. Board organization-wide search target

Future grounded queries should answer why a case was decided, which agents contributed, what Evidence/rules/sources were used, who changed canonical state, why autonomy changed, which government submissions happened, which cases rely on a rule, which contradictions remain unresolved and which capabilities are declining.

Answers must be grounded in governed lineage rather than invented summaries.

---

## 43. Success metrics

Primary metrics include autonomous completion %, human interventions per 100 material actions, Board decisions per 1,000 organizational actions, critical error rate, Evidence grounding, human modification/rejection, false/missed escalation, contradiction rate, source freshness, capability reliability, workflow completion time, p50/p95 material-action latency, cost/outcome, stale/retry rate, incident frequency, recovery effectiveness, Decision Lineage completeness, conversation/material-action traceability, external user success, professional acceptance and repeat usage/willingness to pay when measured.

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

## 44. Repository / acceptance discipline

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

Roadmap rewrites must preserve intentionally regression-protected historical milestones such as `v10.22`, **multi-batch tranche operations**, and `0032_initial_rule_assertions` where tests encode them as repository continuity contracts.

---

## 45. Frozen architecture invariants

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

## 46. Final project direction

Global Mobility AIOS should become a **transparent AI-operated professional Global Mobility organization** capable of understanding goals, organizing work, preserving institutional memory, gathering and governing Evidence, tracking changing regulations, coordinating specialized AI employees, producing professional outputs, executing authorized actions, learning from corrections, detecting abnormal behavior, containing mistakes and escalating intelligently.

The Human Board retains supreme authority without becoming the organization's manual operator.

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

The project should remain ambitious, but every increase in architectural sophistication must increasingly be justified by runtime evidence and real mobility outcomes.

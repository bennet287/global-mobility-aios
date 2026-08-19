# Global Mobility AIOS — Active V12 Product, Platform & High-Autonomy Roadmap

**Roadmap generation:** V12.5  
**Date:** 2026-08-20  
**Active development branch:** `roadmap/global-mobility-aios-v12`  
**V12 fork origin:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`  
**Frozen V11 reference branch:** `roadmap/global-mobility-aios-v11`  
**Final V11 documentation-cleanup head:** `ac130deaafa7aa44068e9459facbda2b4df327d6`  
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR  
**Active organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md)  
**V1.3-A:** Constitutional Contracts — **COMPLETE / PASS / SEALED**  
**V1.3-B.1:** Minimal Governance Kernel — **COMPLETE / PASS / SEALED AS B FOUNDATION**  
**V1.3-B.2:** Governed WorkItem Assignment — **COMPLETE / PASS / SEALED**  
**Current Track C slice:** V1.3-C.1 — Transparency Trace Foundation — **IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING**  
**Technology Radar state:** Wave 1 PILOT COMPLETE / TRIAL-ELIGIBLE; Wave 2 IN PROGRESS with Docling started; Presidio queued  
**Code migration head:** `0076_organization_position_active_identity`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This is the canonical active roadmap for V12. It combines product direction, current delivery truth, V1.3 high-autonomy architecture, external-validation discipline, technology evolution and the evidence required before any slice is marked PASS.

---

## 1. Repository generation model

### V11 — frozen reference checkpoint

V11 preserves the mature product/runtime checkpoint, Phase 13.17 human-acceptance state and its own V11-aligned README/roadmap history.

Final V11 reference head:

```text
ac130deaafa7aa44068e9459facbda2b4df327d6
```

V11 must not receive V12 implementation, V1.3-B/C runtime changes, Technology Radar experiments or later roadmap state unless the Human Owner explicitly reopens it.

### V12 — active implementation line

V12 forked from V11 at:

```text
dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

The later V11 documentation cleanup does not change that fork origin.

> **V11 preserves the checkpoint. V12 proves and implements the direction.**

---

## 2. Project identity

Global Mobility AIOS is being built as a **governed, transparent, high-autonomy AI-operated professional Global Mobility organization**.

It is explicitly not intended to become merely:

- an immigration chatbot;
- a visa questionnaire;
- a generic AI assistant;
- a generic CRM with AI features;
- a document uploader;
- a generic workflow engine;
- a disconnected collection of agents;
- an agent framework wrapped in a dashboard;
- a generic SaaS/admin surface;
- a browser agent with mobility branding;
- or a human approval queue.

Target identity:

> **A governed, transparent, high-autonomy AI-operated professional Global Mobility organization in which persistent AI employees research, reason, collaborate, remember, use tools, manage work, prepare professional outputs, make authorized decisions, execute bounded real-world operations and learn from outcomes — while the Human Owner / Board retains supreme strategic and reserved authority.**

Short form:

> **AIOS does the work. Humans govern the exceptions and retained authority.**

---

## 3. Complete long-term mobility lifecycle

The intended organization must eventually coordinate the full lifecycle rather than isolated visa tasks:

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
→ Human / Board authority where required
→ submission / appointment / external action
→ authority response
→ remediation / follow-up / appeal where applicable
→ relocation / post-arrival obligations
→ renewal / status change / family progression
→ long-term residence
→ citizenship / business / investment / long-term mobility strategy
```

The lifecycle must support changing goals, changing employers, rejected applications, multiple jurisdictions, expired Evidence, superseded rules, family dependencies and long-running institutional history.

---

## 4. Current product/runtime truth

| Programme | State |
|---|---|
| Phases 1–9 | Complete — core platform, Truth Engine, profiles, pathways, timelines, document foundations |
| Phase 10 software | Complete — intelligence/registry/ranking/planning foundation |
| Phase 10B evidence operations | Ongoing — jurisdiction Evidence onboarding, review, publication and freshness |
| Phase 11 | Complete — corporate, business, wealth, investment, family-office and tax/treaty mobility |
| Phase 12 | Complete / stabilized — portals, partner APIs, governed automation and authority-workflow foundations |
| Phase 13.0–13.15 | Complete / PASS where gated — AI organization governance and correctness foundations |
| Phase 13.16.0–13.16.10 | COMPLETE / PASS — role experiences, Contribution/Activity, Cockpit, workspaces, My Mobility, Operations, Evidence/provenance and responsive/accessibility acceptance |
| **Phase 13.17** | **IN PROGRESS / PAUSED BY EVALUATOR** — owner-led genuine human acceptance |
| Phase 14 | NOT STARTED / demand-gated — measured scale after validated demand |

Phase 13.17 does not become PASS simply because V1.3 runtime work progresses.

---

## 5. Historical compatibility contract — v10.22

The active roadmap intentionally preserves selected older milestones that are still protected by repository regression tests and remain meaningful implementation provenance.

`v10.22` introduced **multi-batch tranche operations** around the governed jurisdiction Evidence workflow. It improved batch planning/preparation while preserving human review boundaries and did not create automatic source certification, legal interpretation, assertion approval, VerifiedRule publication or global coverage claims.

Canonical document:

[Coverage Tranche Operations v10.22](COVERAGE_TRANCHE_OPERATIONS_V10_22.md)

Historical database lineage includes:

```text
0032_initial_rule_assertions
```

These exact markers must remain present so roadmap rewrites do not erase repository continuity contracts.

---

## 6. Accepted quality evidence

### Carried-forward accepted product baseline

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
Preserved gmai.db             unchanged at accepted checkpoint
```

These are historical accepted results and must not be represented as rerun unless actually rerun.

### V1.3-A final acceptance — 2026-08-20

```text
Constitutional tests          13 passed / 1 warning / 0 failed
Repository policy             PASS
v10.22 regression rerun       1 passed / 1 warning
Full API regression           886 passed / 5 skipped / 1 warning / 0 failed
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual tables
Physical tables               119 incl. alembic_version
git diff --check              clean
git status                    clean / synchronized
```

See [V1_3_A_ACCEPTANCE_2026-08-20.md](V1_3_A_ACCEPTANCE_2026-08-20.md).

### V1.3-B.1 final acceptance — 2026-08-20

```text
Governance Kernel focused     19 passed / 1 warning / 0 failed in 0.16s
Repository policy             PASS
Full API regression           905 passed / 5 skipped / 1 warning / 0 failed in 325.63s
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual tables
Physical tables               119 incl. alembic_version
git diff --check              clean
git status                    clean / synchronized
```

See [V1_3_B1_ACCEPTANCE_2026-08-20.md](V1_3_B1_ACCEPTANCE_2026-08-20.md).

### V1.3-B.2 final acceptance — 2026-08-20

```text
B.1 + B.2 focused             25 passed / 1 warning / 0 failed in 3.08s
Repository policy             PASS
Full API regression           911 passed / 5 skipped / 1 warning / 0 failed in 316.36s
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS (canonical Windows checkout)
git diff --check              clean
git status                    clean / synchronized
```

See [V1_3_B2_ACCEPTANCE_2026-08-20.md](V1_3_B2_ACCEPTANCE_2026-08-20.md).

The warning remains the pre-existing Starlette/httpx TestClient deprecation warning.

No GitHub CI PASS is claimed without attached check/status evidence.

---

## 7. Product surfaces

### Global Mobility AIOS Cockpit

The top-level Human Owner / Board control surface for organization health, strategy, performance, quality, risk, incidents, autonomy and transparency.

Cockpit should answer:

> **Is my organization healthy, effective, grounded and operating inside the authority I granted it?**

### Board Room

Board Room is a reserved-authority module **inside Cockpit**, not the name of the entire Owner experience and not a generic approval inbox.

### Operations

Professional/operator workspace for cases, Evidence, applications, governed reviews, regulated workflow and human intervention where actually required.

### My Mobility

Mobility-user experience organized around goals, progress, options, documents, Evidence requests, deadlines, costs, risks and understandable next actions.

### Portal / employer / partner / authority surfaces

These must reuse common identity, Evidence, authority, privacy and canonical-state semantics rather than becoming parallel truth systems.

---

## 8. Premium product direction

The product should feel like premium enterprise software with a distinct AI operating-system identity, not generic SaaS and not dark sci-fi.

Preferred direction:

- deep navy / graphite;
- warm ivory;
- selective editorial serif + modern operational sans;
- restrained glass/depth;
- high-quality iconography;
- subtle purposeful motion;
- luxury-level spacing and typography;
- beautiful information density;
- clear role and authority hierarchy;
- live organization visuals based on canonical runtime state, never decorative fake activity.

---

## 9. Constitutional hierarchy

```text
Human Owner / Board
        ↓
AI CEO
        ↓
Departments / Department Heads
        ↓
Specialist AI employees
        ↓
Context / memory / tools / collaboration
        ↓
Governance + Organizational Immune System
        ↓
Canonicalization / Command Gateway for material actions
        ↓
Canonical AIOS state
        ↓
Activity / lineage / learning
```

Permanent invariant:

> **The Human Owner / Board is the supreme authority of Global Mobility AIOS. No agent, AI executive, model, automation, framework, policy engine or delegated authority can supersede it.**

The Board should govern through constitution, delegation, reserved powers and exception handling rather than operating routine workflow.

---

## 10. Board by exception

Routine healthy work should normally remain below the Board:

- research;
- routine case analysis;
- agent collaboration;
- WorkItem assignment;
- drafting;
- extraction;
- scheduling;
- retries;
- ordinary tool use;
- low-risk bounded decisions.

Board attention should focus on retained authority and genuine exceptions:

- Board-reserved government submissions;
- constitutional/strategic changes;
- major policy/autonomy changes;
- major legal/regulatory commitments;
- exceptional finance;
- critical incidents;
- unresolved high-risk Evidence/rule conflicts;
- unresolved senior conflicts;
- critical irreversible actions.

> **Board by exception. Transparency by default.**

---

## 11. Board Transparency invariant

> **Operational autonomy must never create organizational opacity.**

The Board must be able to inspect material organizational actions, decisions, delegation, agent collaboration, Evidence, VerifiedRules, SourceSnapshots, tool actions, external actions, escalations, incidents, autonomy changes, corrections and outcomes, subject to lawful sensitivity controls.

Transparency is not mandatory approval and should not flood the Board.

Progressive drill-down target:

```text
Organization
→ Department
→ Mission
→ Case
→ WorkItem
→ Agent
→ Conversation
→ Decision
→ Evidence / Rule / ToolAction / Event
```

---

## 12. Memory, Evidence and canonical truth

```text
Working memory
Agent memory
Organizational memory
Canonical AIOS truth
```

Permanent principle:

> **Memory provides continuity. Evidence provides authority.**

Trust ladder target:

```text
L0 model speculation
L1 conversation / memory / hypothesis
L2 retrieved information
L3 SourceSnapshot
L4 governed Evidence
L5 reviewed candidate
L6 VerifiedRule / certified fact
L7 governed case conclusion
L8 approved authority-bearing action
```

No silent L1→L6, L2→L7 or L6→L8 promotion.

---

## 13. Context Broker target

Agents should receive purpose-scoped versioned `ContextBundle`s rather than unrestricted database access or maximum-token prompts.

A material bundle may include:

- Agent identity / Position / Department;
- authority/autonomy context;
- Mission / WorkItem;
- case/aggregate identity;
- relevant canonical facts;
- Evidence;
- VerifiedRules;
- SourceSnapshots where needed;
- unknowns and contradictions;
- relevant previous decisions;
- conversation summary;
- allowed tools;
- sensitivity classification;
- policy version;
- context version/hash.

> **More relevant truth, not more tokens.**

---

## 14. Capability, authority, autonomy and risk

These are permanently separate:

```text
Capability = what runtime can technically do
Authority  = what AIOS permits
Autonomy   = how independently authority may be exercised
Risk       = consequence of the particular action
```

```text
CAN DO ≠ MAY DO
```

---

## 15. A0–A5 autonomy semantics

| Level | Meaning |
|---|---|
| A0 | prohibited |
| A1 | human executes |
| A2 | AI prepares; approval required |
| A3 | autonomous with mandatory post-review |
| A4 | autonomous with monitoring and valid recovery controls |
| A5 | fully autonomous bounded operation |

Autonomy is capability/context-specific, never one global score for an agent.

---

## 16. R0–R5 risk tiers

| Tier | Direction |
|---|---|
| R0 | non-material cognition / summarization |
| R1 | routine internal operation + cheap deterministic checks |
| R2 | client-facing preparation + Evidence validation |
| R3 | material recommendation/eligibility + independent verification |
| R4 | certification/regulatory publication + deeper verification + fresh source validation |
| R5 | government submission / critical reserved action + full preparation + Human/Board gate |

Risk belongs to the action, not the employee.

---

## 17. HumanReviewReason

Frozen reasons:

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

A human can be required even with high confidence because authority, law or policy can independently require one.

---

## 18. Materiality Registry

Initial constitutional registry:

| Action | Material | Risk | Board reserved |
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

Jurisdiction/workflow policy may strengthen these requirements but may not silently weaken constitutional minimums.

---

## 19. Consequence-aware recovery

Frozen classes:

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
APPEND_ONLY_CORRECTION
```

Examples:

- WorkItem reassignment → REVERSIBLE;
- incorrect external communication → COMPENSATABLE;
- government submission → IRREVERSIBLE;
- later-revoked Evidence certification → APPEND_ONLY_CORRECTION.

Recovery belongs to business commands rather than pretending every database write is universally rollbackable.

---

## 20. Scores route; deterministic gates authorize

Permanent invariant:

> **No material action is authorized by a Decision Readiness scalar alone.**

Target authorization:

```text
Identity valid
AND Authority valid
AND Scope valid
AND mandatory Evidence present
AND Policy gates pass
AND no blocking contradiction
AND Expected version matches
AND required verification completed
AND readiness threshold satisfied
→ execute
```

Examples:

```text
Readiness 98% + mandatory Evidence missing → BLOCK
Readiness 100% + Board-reserved government submission → BOARD GATE
```

---

## 21. Canonicalization and semantic sovereignty

```text
LLM / tool / provider interpretation
        ↓
typed AIOS candidate
        ↓
schema validation
        ↓
deterministic domain checks
        ↓
Evidence / rule / authority / policy
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

External frameworks provide capability/execution; AIOS owns meaning, authority and canonical semantics.

---

## 22. V1.3-A — Constitutional Contracts

**State:** COMPLETE / PASS / SEALED.

Implementation:

```text
7779c1f8e5d3db2e72e047667774284d7cc5f5af
feat: freeze v1.3 constitutional contracts
```

Key files:

- `apps/api/app/core/organization_constitution.py`;
- `apps/api/tests/test_organization_constitution.py`;
- [ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md](ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md);
- [V1_3_A_ACCEPTANCE_2026-08-20.md](V1_3_A_ACCEPTANCE_2026-08-20.md).

A is the frozen vocabulary/constitutional floor for later B–N implementation.

---

## 23. V1.3-B.1 — Minimal Governance Kernel

**State:** COMPLETE / PASS / SEALED AS B FOUNDATION.

Implementation:

```text
d351ad85f5c3464178b56dd9da6ac5c83090a27a
feat: start v1.3-b governance kernel
```

Accepted contracts:

- `CapabilityAuthority`;
- typed `MaterialAction`;
- authority/capability/scope evaluation;
- constitutional risk floor;
- expected-version/precondition decision;
- idempotent replay/conflict decision;
- deterministic policy disposition;
- A0–A5 execution/review routing;
- Board-reserved protection;
- trace identity;
- OrganizationActivity projection compatible with current physical Activity schema.

See [V1_3_B_MINIMAL_GOVERNANCE_KERNEL.md](V1_3_B_MINIMAL_GOVERNANCE_KERNEL.md) and [V1_3_B1_ACCEPTANCE_2026-08-20.md](V1_3_B1_ACCEPTANCE_2026-08-20.md).

---

## 24. V1.3-B.2 — Governed WorkItem Assignment

**State:** COMPLETE / PASS / SEALED.

Selected first real action:

```text
work_item.assignment
R1
REVERSIBLE
```

Delivered:

```text
apps/api/app/services/organization_governed_work.py
apps/api/tests/test_organization_governed_work.py
docs/V1_3_B2_GOVERNED_WORK_ASSIGNMENT.md
docs/V1_3_B2_ACCEPTANCE_2026-08-20.md
```

Accepted runtime path:

```text
Actor
→ CapabilityAuthority
→ MaterialAction
→ deterministic gateway
→ durable idempotency
→ expected-version precondition
→ existing WorkItem mutation
→ existing audit + semantic Activity
→ governance Activity / trace
→ one atomic commit
```

### Accepted B.2 design choices

1. No migration was added merely to prove the first command path.
2. Current `updated_at` is converted into a deterministic integer precondition token as a compatibility bridge.
3. New commands with stale preconditions fail closed.
4. Exact successful-command retries resolve durable idempotency before stale-version rejection, because the first successful execution necessarily advanced aggregate state.
5. Conflicting reuse of the same idempotency key fails closed.
6. A2 remains review-required and cannot mutate directly.
7. WorkItem mutation, assignment audit, semantic Activity and governance Activity commit atomically for AUTO_EXECUTE.
8. Governance Activity failure rolls back the whole unit of work rather than creating an opaque autonomous mutation.

Canonical acceptance:

```text
25 passed, 1 warning in 3.08s
Repository policy PASS
911 passed, 5 skipped, 1 warning in 316.36s
Database migration check PASS
Local DB schema check PASS
git diff --check clean
git status clean / synchronized
```

See [V1_3_B2_GOVERNED_WORK_ASSIGNMENT.md](V1_3_B2_GOVERNED_WORK_ASSIGNMENT.md) and [V1_3_B2_ACCEPTANCE_2026-08-20.md](V1_3_B2_ACCEPTANCE_2026-08-20.md).

---

## 25. V1.3-B conclusion and transition

B now has enough runtime evidence to support the next architectural dependency without expanding the Governance Kernel horizontally merely because more abstractions are possible.

Accepted B foundation:

```text
B.1 deterministic Governance Kernel
        +
B.2 first real atomic R1 domain mutation
```

A dedicated integer aggregate-version migration, persistent policy registry and additional governed command types remain legitimate future work, but should be introduced when a real vertical workflow demonstrates the need.

The active dependency therefore moves to V1.3-C Transparency Foundation.

---

## 26. V1.3-C — Transparency Foundation

Planned early because autonomy without reconstructability is unacceptable.

### C.1 — Transparency Trace Foundation

**State:** IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING.

Delivered:

```text
apps/api/app/services/organization_transparency.py
apps/api/tests/test_organization_transparency.py
docs/V1_3_C1_TRANSPARENCY_TRACE_FOUNDATION.md
```

The B.2 governed WorkItem path now also propagates the Governance Kernel `trace_id` as the correlation key of the resulting semantic WorkItem Activity.

C.1 therefore makes one real material action reconstructable as:

```text
Governance authorization
        +
resulting WorkItem organization effect
        ↓
shared trace identity
        ↓
tenant-scoped durable OrganizationActivity query
        ↓
structured Board-inspectable trace
```

C.1 adds typed transparency projection/query contracts while reusing the existing `OrganizationActivity` substrate. Existing pre-V1.3 Activities remain Board-inspectable but are not silently assigned fake constitutional retention/lineage semantics.

Focused coverage includes:

- shared governance/effect trace correlation;
- governed action reconstruction;
- strict tenant isolation;
- legacy/unclassified Activity handling;
- fail-closed malformed governance trace detection;
- WorkItem Activity-history visibility.

Canonical acceptance must run before C.1 can be marked PASS.

### Later C slices

Implement only as runtime need becomes concrete:

- explicit causation/activity-lineage links;
- persistence of blocked/review-required governance attempts;
- AgentConversation / AgentMessage semantics;
- retention/sensitivity boundaries;
- ToolActionRecord foundation;
- DecisionLineage / ActivityLineage across Evidence/Rules/Tools;
- Board/Cockpit transparency query surfaces.

Acceptance target for the broader C phase:

- reconstruct a governed test decision from outcome back to actor/policy/Evidence;
- trace material collaboration/tool actions;
- hide secrets appropriately;
- summarize normal activity rather than Board-spam it.

See [V1_3_C1_TRANSPARENCY_TRACE_FOUNDATION.md](V1_3_C1_TRANSPARENCY_TRACE_FOUNDATION.md).

---

## 27. V1.3-D — Context & Agent Identity

Implement:

- persistent Agent identity;
- Position / Department linkage;
- `ContextBundle`;
- context version/hash;
- AgentRun lineage;
- working vs long-term vs organizational memory boundaries;
- purpose-scoped retrieval.

Acceptance target:

- material run reconstructable;
- scoped context rather than unrestricted data access;
- memory cannot silently become canonical truth.

---

## 28. V1.3-E — First Governed Mobility Vertical

This is the major architecture proof point and must be based on a real mobility workflow rather than another generic framework.

Target form:

```text
Case / Mission
→ scoped ContextBundle
→ Evidence / missing Evidence
→ VerifiedRules
→ eligibility candidate
→ risk-required verification
→ Command Gateway
→ canonical state
→ OrganizationActivity
→ Decision Lineage
→ Transparency
→ LearningRecord where meaningful
```

Austria is a strong first validation jurisdiction because the project already has meaningful Austria-oriented product context and it can support a tightly scoped professional workflow.

The final pathway selection should be frozen based on real user/professional validation rather than architecture preference alone.

---

## 29. V1.3-F — Decision Readiness

Implement:

- auditable readiness components;
- versioned formula/routing;
- hard gates;
- incremental recomputation;
- `DecisionReadinessSnapshot`;
- professional/Board explanation;
- calibration telemetry.

Readiness routes work. It does not override mandatory authority/Evidence/policy gates.

---

## 30. V1.3-G — Independent Verification

For R3+ introduce blind verification so reviewer conclusion is formed before exposure to the original recommendation.

Modes:

```text
PRE_COMMIT
POST_COMMIT
BACKGROUND
```

Cache only against exact governed-state identity including relevant Evidence/rules/policy/program/model versions.

---

## 31. V1.3-H — Organizational Immune System

Incrementally add:

- Evidence Integrity Monitor;
- contradiction detector;
- anomaly detector;
- Decision Readiness monitoring;
- capability performance;
- circuit breakers;
- rate/budget protection;
- blast-radius limits;
- incident detector;
- root-cause classifier;
- escalation router;
- shadow evaluation;
- learning feedback.

Desired behavior:

> **Almost invisible when healthy; extremely capable when abnormal behavior occurs.**

Every intervention must be explainable from observable signals/policy, not opaque model intuition.

---

## 32. V1.3-I — Earned Autonomy

Progression:

```text
SHADOW
→ RECOMMEND
→ SUPERVISED
→ AUTONOMOUS
→ HIGH-TRUST AUTONOMOUS
```

Track evidence per agent × capability, including volume, grounding, human acceptance/modification/rejection, contradictions, critical errors, source freshness, recovery and incidents.

Agents may never self-promote authority/autonomy.

Downgrades should be scope-limited, visible, reversible and explainable where possible.

---

## 33. V1.3-J/K — Agent and Execution Runtimes

### J — Agent Organization Runtime

Evaluate candidates against identity, hierarchy, messaging, memory, delegation, scheduling, failure handling, tools, observability, multitenancy, authority compatibility and transparency compatibility.

External candidate outcomes:

```text
ADOPT / TRIAL / WRAP / BORROW / FORK / REJECT
```

### K — Execution / Coworker Runtime

Provider-neutral bounded execution for files, documents, browser, terminal/code, email, calendar, MCP/connectors, scheduled work, external actions, resumable jobs and sandbox classes.

Munder Difflin remains an experimental reference. OpenWorker remains a replaceable execution/coworker reference. Neither owns AIOS semantics or authority.

---

## 34. V1.3-L/M/N — Live Organization, Board Transparency, Learning

### L — Live Organization

Bring canonical Agents, Departments, Missions, WorkItems, collaboration, blocked work, incidents, autonomy, quality, cost and performance into Cockpit.

No fake/simulated activity where the UI claims live organizational state.

### M — Board Transparency Experience

Build Organization Explorer, Decision Explorer, Conversation Explorer, Case Timeline, Evidence/Rule lineage, Tool Activity Explorer, Agent History, Incident Timeline, Autonomy History and grounded organization-wide search.

### N — Learning & Optimization

Deepen LearningRecords, human-correction analysis, capability performance, readiness calibration, policy/routing tuning, false/missed escalation analysis, evaluation datasets and curated learning examples.

Not every Activity becomes training truth.

---

## 35. Coordinated parallel evolution

### Track A — Product / Human Experience

- Phase 13.17 genuine human acceptance;
- bounded UX corrections;
- Cockpit / Operations / My Mobility refinement;
- role clarity;
- Evidence/provenance explainability;
- responsive/accessibility quality;
- professional next-action clarity.

### Track B — Technology Radar / Platform Evolution

- Promptfoo / OpenTelemetry / ClamAV trial evidence;
- Docling pilot;
- Presidio next;
- source-monitoring/privacy/document technologies;
- explicit adoption/rejection evidence;
- no framework-driven architecture changes without measured benefit.

### Track C — High-Autonomy Organization

A–N architecture implementation described above.

### Track D — Real-World Validation & Commercial Proof

Architecture must increasingly be justified by external evidence:

```text
owner-led acceptance
→ first external mobility professional
→ first real case
→ first 10 cases
→ first 50 cases
→ first paying professional / organization
→ first repeatable jurisdiction workflow
→ first professional team
```

Measure time saved, AI acceptance, human correction, workflow completion, trust, drop-off, critical errors, willingness to pay and repeat usage.

Do not delay Track D until the architecture is “finished.”

---

## 36. Technology Radar

| Technology | Capability | State |
|---|---|---|
| Promptfoo | AI quality/safety evaluation | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | neutral telemetry | PILOT COMPLETE / TRIAL-ELIGIBLE |
| ClamAV | malware scanning | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | document normalization | PILOT IN PROGRESS |
| Presidio | privacy gateway | QUEUED PILOT |
| urlwatch | source monitoring | QUEUED PILOT |
| Munder Difflin | agent organization reference | CONTROLLED RESEARCH |
| OpenWorker | execution/coworker reference | CONTROLLED RESEARCH |
| Temporal | durable execution | DEFERRED PILOT |
| OpenFGA | relationship authorization | DEFERRED PILOT |
| pgvector / Qdrant | retrieval | BENCHMARK WHEN NEEDED |
| Pydantic AI / Langfuse | AI/runtime observability candidates | RESEARCH / CANDIDATE |
| DSPy | program optimization | RESEARCH |
| Gotenberg / Typst | professional output | FUTURE EVALUATION |
| EU DSS | signature/document trust | RESEARCH |

Lifecycle:

```text
REFERENCE → RESEARCH → BENCHMARK → PILOT → TRIAL → ADOPT
```

or explicit REJECT.

---

## 37. Legal, privacy and data-governance workstream

Convert principles into explicit policy over time:

- GDPR lawful basis by data class/purpose;
- purpose limitation;
- special-category data handling;
- retention/deletion/correction rights;
- model-provider data-use boundaries;
- cross-border transfers;
- Agent-memory retention;
- LearningRecord / CuratedLearningExample eligibility;
- privilege/confidentiality;
- professional/legal representation boundaries;
- jurisdiction-specific submission authority;
- consent and human-accountability requirements.

Board transparency must coexist with lawful sensitivity controls.

---

## 38. Performance and scalability doctrine

### P1 — Pay for risk

Verification effort scales with consequence, uncertainty and novelty.

### P2 — Recompute only what changed

Use version-aware Evidence/readiness/policy calculations.

### P3 — Load only what is needed

Context is purpose-scoped, lazy, composable and versioned.

### P4 — Block only when necessary

Use PRE_COMMIT, POST_COMMIT and BACKGROUND modes appropriately.

### P5 — Centralize governance, distribute execution

One authority model does not imply one global execution mutex.

### P6 — Cache exact governed state only

Cache identity must include relevant Evidence, facts, VerifiedRules, policy, jurisdiction/effective dates and model/program versions.

### P7 — Instrument from day one

Measure p50/p95 latency, cost, context size, retries/staleness, gateway latency, escalations, overrides, critical errors, source freshness, Board load, autonomy and transparency lag.

> **Governance Cost ∝ Risk × Uncertainty × Novelty**

---

## 39. First governed vertical workflow direction

After the minimal B/C/D foundations are sufficient, prove them through one real mobility workflow rather than continuing horizontal abstraction.

Example shape:

```text
Blocked mobility case
→ Mission / WorkItem
→ scoped ContextBundle
→ Evidence / missing Evidence
→ VerifiedRules
→ eligibility candidate
→ Decision Readiness
→ blind reviewer where R3
→ Command Gateway
→ professional/human escalation only when required
→ canonical transition
→ OrganizationActivity + Decision Lineage
→ Board-inspectable transparency
→ Learning outcome
```

This workflow should become the bridge between architecture quality and external professional validation.

---

## 40. Cockpit target information architecture

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

Top level summarizes health and exceptions; drill-down exposes evidence and lineage without turning the Board into an operator.

---

## 41. Organization-wide grounded search target

Future Board/professional questions should include:

- Why was this applicant marked ineligible?
- Which agents contributed?
- What Evidence supported the conclusion?
- Which VerifiedRule/source was used?
- Who changed canonical case state?
- Why was autonomy downgraded?
- Which government submissions occurred in a period?
- Which cases depend on a rule?
- Which contradictions remain unresolved?
- Which capabilities are declining in quality?

Answers must be grounded in governed lineage, not invented summaries.

---

## 42. Outcome metrics

Primary metrics should increasingly include:

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
Repeat usage
Willingness to pay when measured
```

Desired direction:

```text
Autonomy ↑
Quality ↑
Evidence grounding ↑
Traceability ↑
Board transparency ↑
External validation ↑

Board operational workload ↓
Critical errors ↓
False/missed escalations ↓
Cost per outcome ↓
Opaque decisions ↓
```

---

## 43. Repository and acceptance discipline

Every meaningful patch should:

1. verify branch/SHA/remote state;
2. inspect canonical docs/contracts;
3. freeze exact implementation boundary;
4. preserve unrelated work;
5. implement incrementally;
6. run focused acceptance;
7. run broader acceptance where required;
8. run browser/runtime checks for user-facing changes;
9. update ROADMAP for delivery state;
10. update CHANGELOG for meaningful delivery;
11. inspect diff/whitespace;
12. commit/push truthfully;
13. verify remote state;
14. preserve migration/database/release invariants;
15. never claim docs=runtime, pilot=adopt, tests=PASS if not run, or CI PASS without attached evidence.

Historical regression-protected roadmap markers such as `v10.22`, **multi-batch tranche operations** and `0032_initial_rule_assertions` must remain preserved.

---

## 44. Frozen V1.3 invariants

1. Human Owner / Board is supreme.
2. Board governs mainly by exception.
3. Autonomy cannot create opacity.
4. Board has on-demand material visibility.
5. Material collaboration remains reconstructable.
6. Material decisions require lineage.
7. Agents may hold real delegated authority.
8. Authority is capability-specific and bounded.
9. Autonomy is earned and capability-specific.
10. Agents cannot self-promote authority/autonomy.
11. Memory is not canonical truth.
12. Memory provides continuity; Evidence provides authority.
13. Material truth crosses typed deterministic canonicalization.
14. Material autonomous mutations cross the Command Gateway as runtime integration expands.
15. Scores/readiness route; deterministic gates authorize.
16. Verification depth scales with risk/uncertainty/novelty.
17. Legal/policy human requirements override confidence.
18. Parallel agents use explicit version/concurrency controls.
19. External frameworks provide capability; AIOS owns semantics/authority.
20. Immune-system intervention must be explainable.
21. Restrictions should be scope-limited where possible.
22. Irreversible actions receive stronger prechecks.
23. Recovery distinguishes reversible/compensatable/irreversible/append-only correction.
24. Learning preserves labeled outcomes/corrections.
25. Governance cost scales with risk rather than being maximal everywhere.
26. Context is scoped/lazy/versioned.
27. Governance is not a global execution mutex.
28. Summaries do not replace required underlying records.
29. Secrets/protected data remain secure under transparency.
30. Conversation is Activity but not authority.
31. Provider-local state/logs do not silently become canonical AIOS truth.
32. Agents may be wrong while thinking; AIOS may not be wrong silently when committing truth.

---

## 45. Immediate next action

Current engineering state:

```text
V1.3-A     COMPLETE / PASS / SEALED
V1.3-B.1   COMPLETE / PASS / SEALED AS FOUNDATION
V1.3-B.2   COMPLETE / PASS / SEALED
V1.3-C.1   IMPLEMENTED / CANONICAL ACCEPTANCE PENDING
```

The immediate next action is canonical C.1 acceptance, not additional B framework expansion.

If C.1 passes, seal it and choose the next bounded transparency requirement from the first real mobility vertical: blocked/review-attempt persistence, explicit causation, Board/Cockpit query contract, or Evidence/tool/decision lineage.

At the same time, Track A Phase 13.17 and Track D external-validation preparation should continue independently rather than waiting for the complete V1.3 architecture.

---

## 46. Final direction

Global Mobility AIOS should become a **transparent AI-operated professional Global Mobility organization** capable of understanding goals, organizing work, preserving institutional continuity, gathering/governing Evidence, tracking regulations, coordinating specialized AI employees, producing professional outputs, executing authorized actions, detecting/containing mistakes, learning from correction and escalating intelligently.

The Human Board retains supreme authority without becoming the organization's manual operator.

Implementation target:

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

Every increase in architectural sophistication must increasingly be justified by runtime evidence and real mobility outcomes.
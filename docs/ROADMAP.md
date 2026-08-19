# Global Mobility AIOS — Active V12 Product, Platform & High-Autonomy Roadmap

**Roadmap generation:** V12.6  
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
**V1.3-C.1:** Transparency Trace Foundation — **COMPLETE / PASS / SEALED**  
**Current Track C slice:** V1.3-C.2 — Non-Executing Material Attempt Transparency — **IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING**  
**Technology Radar state:** Wave 1 PILOT COMPLETE / TRIAL-ELIGIBLE; Wave 2 IN PROGRESS with Docling started; Presidio queued  
**Code migration head:** `0076_organization_position_active_identity`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This is the canonical active roadmap for V12. It describes the product, the preserved runtime truth, the high-autonomy organization architecture, the active implementation sequence, the acceptance evidence required before each slice becomes PASS, and the external product-validation path that must increasingly justify further architectural expansion.

---

## 1. Repository generation model

### V11 — frozen reference checkpoint

V11 preserves the mature product/runtime checkpoint through Phase 13.16.10, the Phase 13.17 human-acceptance state, the V1.3 architecture design created before the branch split, and its own final V11-aligned product/delivery roadmap.

Final V11 reference head:

```text
ac130deaafa7aa44068e9459facbda2b4df327d6
```

V11 must not receive V12 implementation, V1.3-B/C runtime work, Technology Radar experiments, or later V12 roadmap state unless the Human Owner explicitly reopens it.

### V12 — active implementation line

V12 originally forked from V11 at:

```text
dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

The later V11 documentation-only cleanup does not alter that historical V12 fork origin.

> **V11 preserves the checkpoint. V12 proves and implements the direction.**

---

## 2. What Global Mobility AIOS is

Global Mobility AIOS is being built as a **governed, transparent, high-autonomy AI-operated professional Global Mobility organization**.

It is deliberately not intended to become merely:

- an immigration chatbot;
- a visa questionnaire;
- a generic AI assistant;
- a CRM with AI features;
- a document uploader;
- a generic workflow engine;
- a disconnected multi-agent demonstration;
- an agent framework wrapped in a dashboard;
- a generic SaaS/admin surface;
- a browser agent with mobility branding;
- or a human approval queue.

Target identity:

> **A governed, transparent, high-autonomy AI-operated professional Global Mobility organization in which persistent AI employees research, reason, collaborate, remember, use tools, manage work, prepare professional outputs, make authorized decisions, execute bounded real-world operations and learn from outcomes — while the Human Owner / Board retains supreme strategic and reserved authority.**

Short form:

> **AIOS does the work. Humans govern the exceptions and retained authority.**

---

## 3. Complete mobility lifecycle target

The organization should eventually coordinate the whole mobility lifecycle rather than isolated visa tasks:

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

The lifecycle must support changing goals, employers and jurisdictions; rejected applications; expired Evidence; superseded rules; family dependencies; long-lived case history; and future mobility strategy.

---

## 4. Current product/runtime truth

| Programme | State |
|---|---|
| Phases 1–9 | Complete — core platform, Truth Engine, profiles, pathways, timelines and document foundations |
| Phase 10 software | Complete — self-updating intelligence, registry workflow, ranking and multi-year planning foundation |
| Phase 10B evidence operations | Ongoing — jurisdiction Evidence onboarding, independent review, publication and freshness |
| Phase 11 | Complete — corporate, business, wealth, investment, family-office and tax/treaty mobility |
| Phase 12 | Complete / stabilized — portals, partner APIs, governed automation and authority-workflow foundations |
| Phase 13.0–13.15 | Complete / PASS where gated — AI organization governance and correctness foundations |
| Phase 13.16.0–13.16.10 | COMPLETE / PASS — role experiences, Contribution/Activity, Cockpit, workspaces, My Mobility, Operations, Evidence/provenance and responsive/accessibility acceptance |
| **Phase 13.17** | **IN PROGRESS / PAUSED BY EVALUATOR** — owner-led genuine human acceptance |
| Phase 14 | NOT STARTED / demand-gated — measured scale after validated demand |

Phase 13.17 remains real human acceptance work and does not become PASS merely because V1.3 architecture/runtime work progresses.

---

## 5. Historical compatibility contract — v10.22

The active V12 roadmap intentionally preserves selected historical delivery markers that remain protected by repository regression tests and are meaningful provenance for the current governed Evidence foundation.

`v10.22` introduced **multi-batch tranche operations** around the governed jurisdiction Evidence workflow. It improved multi-batch planning and preparation while preserving human-review boundaries and did not add automatic source certification, legal interpretation, assertion approval, VerifiedRule publication, snapshot mutation, or global coverage claims.

Canonical historical note:

[Coverage Tranche Operations v10.22](COVERAGE_TRANCHE_OPERATIONS_V10_22.md)

Historical database lineage includes:

```text
0032_initial_rule_assertions
```

The exact markers `v10.22`, **multi-batch tranche operations**, and `0032_initial_rule_assertions` must remain present so roadmap rewrites do not erase repository continuity contracts.

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

These are historical accepted results and must never be represented as rerun unless they actually were rerun.

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
Local DB schema               PASS
git diff --check              clean
git status                    clean / synchronized
```

See [V1_3_B2_ACCEPTANCE_2026-08-20.md](V1_3_B2_ACCEPTANCE_2026-08-20.md).

### V1.3-C.1 final acceptance — 2026-08-20

```text
B.1 + B.2 + C.1 focused       31 passed / 1 warning / 0 failed in 5.40s
Repository policy             PASS
Full API regression           917 passed / 5 skipped / 1 warning / 0 failed in 317.64s
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual tables
Physical tables               119 incl. alembic_version
git diff --check              clean
git status                    clean / synchronized
```

See [V1_3_C1_ACCEPTANCE_2026-08-20.md](V1_3_C1_ACCEPTANCE_2026-08-20.md).

The single warning remains the pre-existing Starlette/httpx TestClient deprecation warning.

No GitHub CI PASS is claimed without attached check/status evidence.

---

## 7. Product surfaces

### Global Mobility AIOS Cockpit

The top-level Human Owner / Board surface for organization health, strategy, performance, quality, risk, incidents, autonomy and transparency.

Cockpit should answer:

> **Is my organization healthy, effective, grounded and operating inside the authority I granted it?**

rather than becoming a list of hundreds of approvals.

### Board Room

Board Room is a **reserved-authority module inside Cockpit**. It is not the name of the entire Owner experience and must not become a generic review inbox.

### Operations

Professional/operator workspace for cases, Evidence, regulated workflow, applications, reviews, decisions and governed human intervention.

### My Mobility

Mobility-user experience organized around goals, progress, options, documents, Evidence requests, deadlines, costs, risks and understandable next actions.

### Portal / employer / partner / authority surfaces

These must reuse the same identity, Evidence, authority, privacy and canonical-state model rather than inventing parallel truth systems.

---

## 8. Premium product direction

The product should feel like premium enterprise software with a distinct AI operating-system identity, not generic SaaS/admin and not dark sci-fi.

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
- distinct personalities for Cockpit, Board Room, Operations and My Mobility;
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

The Board governs mainly through constitution, delegation, reserved powers and exception handling.

> **The Board should govern the organization, not operate it.**

---

## 10. Board by exception

Routine healthy work should normally remain below the Board:

- internal research;
- routine case analysis;
- agent collaboration;
- WorkItem assignment;
- drafting and extraction;
- scheduling and retries;
- ordinary bounded tool use;
- low-risk operational decisions.

Board attention should focus on retained authority and genuine exceptions:

- Board-reserved government submissions;
- constitutional/strategic changes;
- major policy or autonomy changes;
- major legal/regulatory commitments;
- exceptional finance;
- critical incidents;
- unresolved high-risk Evidence/rule conflicts;
- unresolved senior conflicts;
- critical irreversible actions.

> **Board by exception. Transparency by default.**

---

## 11. Board Transparency invariant

Permanent rule:

> **Operational autonomy must never create organizational opacity.**

The Board must be able to inspect material organizational actions, decisions, delegation, relevant collaboration, Evidence, VerifiedRules, SourceSnapshots, tool actions, external actions, escalations, incidents, autonomy changes, corrections and outcomes, subject to lawful sensitivity controls.

This is an inspection right, not a mandatory approval requirement.

```text
Board visibility ≠ Board interruption
```

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

Agents should receive purpose-scoped, versioned `ContextBundle`s rather than unrestricted database access or maximum-token prompts.

A material bundle may include Agent identity, Position/Department, authority/autonomy context, Mission/WorkItem, case/aggregate identity, relevant facts, Evidence, VerifiedRules, SourceSnapshots, unknowns/contradictions, prior decisions, conversation summaries, allowed tools, sensitivity classification, policy version and context version/hash.

> **More relevant truth, not more tokens.**

---

## 14. Capability, authority, autonomy and risk

```text
Capability = what runtime can technically do
Authority  = what AIOS permits
Autonomy   = how independently authority may be exercised
Risk       = consequence of the particular action
```

Permanent rule:

```text
CAN DO ≠ MAY DO
```

### A0–A5 autonomy

| Level | Meaning |
|---|---|
| A0 | prohibited |
| A1 | human executes |
| A2 | AI prepares; approval required |
| A3 | autonomous with mandatory post-review |
| A4 | autonomous with monitoring and valid recovery controls |
| A5 | fully autonomous bounded operation |

Autonomy is capability/context-specific, never one global score for an agent.

### R0–R5 risk

| Tier | Direction |
|---|---|
| R0 | non-material cognition / summarization |
| R1 | routine internal operation + inexpensive deterministic checks |
| R2 | client-facing preparation + Evidence validation |
| R3 | material recommendation/eligibility + independent verification |
| R4 | certification/regulatory publication + deeper verification + fresh source validation |
| R5 | government submission / critical reserved action + full preparation + Human/Board gate |

Risk belongs to the action, not the employee.

---

## 15. HumanReviewReason

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

A human may be required even with high confidence because authority, law or policy can independently require one.

---

## 16. Materiality Registry

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

## 17. Consequence-aware recovery

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

Recovery belongs to business commands rather than pretending every real-world outcome can be rolled back like a database row.

---

## 18. Scores route; deterministic gates authorize

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

## 19. Canonicalization and semantic sovereignty

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

## 20. V1.3-A — Constitutional Contracts

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

A is the frozen constitutional vocabulary for B–N implementation.

---

## 21. V1.3-B — Minimal Governance Kernel

### B.1 — deterministic foundation

**State:** COMPLETE / PASS / SEALED AS B FOUNDATION.

Implementation:

```text
d351ad85f5c3464178b56dd9da6ac5c83090a27a
feat: start v1.3-b governance kernel
```

Accepted contracts include `CapabilityAuthority`, typed `MaterialAction`, authority/capability/scope evaluation, risk floors, expected-version decisions, idempotency replay/conflict, deterministic policy disposition, A0–A5 routing, Board-reserved protection, trace identity and current-Activity-compatible governance projection.

See [V1_3_B_MINIMAL_GOVERNANCE_KERNEL.md](V1_3_B_MINIMAL_GOVERNANCE_KERNEL.md) and [V1_3_B1_ACCEPTANCE_2026-08-20.md](V1_3_B1_ACCEPTANCE_2026-08-20.md).

### B.2 — first real governed mutation

**State:** COMPLETE / PASS / SEALED.

Selected action:

```text
work_item.assignment
R1
REVERSIBLE
```

Accepted runtime path:

```text
Actor
→ CapabilityAuthority
→ MaterialAction
→ deterministic gateway
→ durable successful-command idempotency
→ expected-version precondition
→ existing WorkItem mutation
→ existing audit + semantic Activity
→ governance Activity / trace
→ one atomic commit
```

Accepted B.2 design choices:

1. no migration merely to prove the first command path;
2. `updated_at`-derived precondition token as a bounded compatibility bridge;
3. stale new commands fail closed;
4. successful retries resolve durable idempotency before false stale rejection;
5. conflicting idempotency reuse fails closed;
6. A2 cannot mutate directly;
7. WorkItem mutation, audit, semantic Activity and governance Activity commit atomically;
8. governance Activity storage failure prevents opaque autonomous mutation.

See [V1_3_B2_GOVERNED_WORK_ASSIGNMENT.md](V1_3_B2_GOVERNED_WORK_ASSIGNMENT.md) and [V1_3_B2_ACCEPTANCE_2026-08-20.md](V1_3_B2_ACCEPTANCE_2026-08-20.md).

### B conclusion

B now has enough runtime evidence to support downstream architecture without adding more framework breadth merely because it is possible.

Potential later B work—explicit aggregate version columns, persisted policy registry, additional governed command types—must be demand-driven by the real vertical workflow.

---

## 22. V1.3-C — Transparency Foundation

Autonomy without reconstructability is unacceptable, so C begins before broader agent/runtime expansion.

### C.1 — Transparency Trace Foundation

**State:** COMPLETE / PASS / SEALED.

Delivered:

```text
apps/api/app/services/organization_transparency.py
apps/api/tests/test_organization_transparency.py
docs/V1_3_C1_TRANSPARENCY_TRACE_FOUNDATION.md
docs/V1_3_C1_ACCEPTANCE_2026-08-20.md
```

Accepted shape:

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

C.1 reuses `OrganizationActivity`, keeps legacy/unclassified Activity Board-inspectable without fabricating historical constitutional semantics, and fails closed on malformed/ambiguous governance traces.

### C.2 — Non-Executing Material Attempt Transparency

**State:** IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING.

Delivered:

```text
apps/api/app/services/organization_governed_work_transparency.py
apps/api/tests/test_organization_transparency_attempts.py
docs/V1_3_C2_NON_EXECUTING_ATTEMPT_TRANSPARENCY.md
```

C.2 closes the next transparency gap:

```text
Material action attempt
        ↓
Governance Kernel
        ↓
BLOCK or REVIEW_REQUIRED
        ↓
NO domain mutation
        +
trace-scoped durable governance Attempt Activity
        ↓
Board-inspectable trace
```

#### Successful-command idempotency remains separate

Sealed B.2 success identity remains:

```text
governance:<idempotency_key>
```

C.2 non-executing attempt identity is:

```text
governance:attempt:<trace_id>
```

This prevents a past denial/review result from masquerading as a successful replay record after legitimate authority or policy changes.

The C.2 attempt record preserves structured action/governance metadata but does not capture hidden chain-of-thought.

Focused tests cover A2 review visibility, stale-version block visibility, scope-denied visibility, later successful execution after legitimate authority increase, and fail-closed attempt-storage behavior.

### Later C slices — only when vertical evidence requires them

Candidates include:

- explicit causation/activity-lineage links;
- bounded Board/Cockpit transparency query DTO/API;
- AgentConversation / AgentMessage semantics;
- retention/sensitivity boundaries;
- ToolActionRecord;
- Evidence / VerifiedRule / SourceSnapshot decision lineage;
- aggregation of repetitive attempts without losing drill-down history.

Broader C acceptance target:

- reconstruct a governed decision from outcome back to actor/policy/Evidence;
- trace material collaboration/tool actions;
- hide secrets and legally sensitive data appropriately;
- summarize normal activity rather than Board-spam it.

---

## 23. V1.3-D — Context & Agent Identity

Implement only after the minimum C visibility floor is sufficient:

- persistent Agent identity;
- Position / Department linkage;
- `ContextBundle`;
- context version/hash;
- AgentRun lineage;
- working vs long-term vs organizational memory boundaries;
- purpose-scoped retrieval.

Acceptance target:

- material AgentRun reconstructable;
- scoped context rather than unrestricted data access;
- memory cannot silently become canonical truth.

---

## 24. V1.3-E — First Governed Mobility Vertical

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

Austria remains a strong first validation jurisdiction because the product already has meaningful Austria-oriented context and can support a tightly scoped professional workflow.

Final pathway selection should be frozen from real user/professional validation rather than architecture preference alone.

---

## 25. V1.3-F — Decision Readiness

Implement:

- auditable readiness components;
- versioned formula/routing;
- hard gates;
- incremental recomputation;
- `DecisionReadinessSnapshot`;
- professional/Board explanation;
- calibration telemetry.

Readiness routes work. It does not override mandatory authority, Evidence, policy or verification gates.

---

## 26. V1.3-G — Independent Verification

For R3+ introduce blind verification so the reviewer forms a conclusion before exposure to the original recommendation.

Modes:

```text
PRE_COMMIT
POST_COMMIT
BACKGROUND
```

Cache only against exact governed-state identity including relevant Evidence, facts, rules, policy, program and model versions.

---

## 27. V1.3-H — Organizational Immune System

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

Every intervention must be explainable from observable signals and policy rather than opaque model intuition.

---

## 28. V1.3-I — Earned Autonomy

Progression:

```text
SHADOW
→ RECOMMEND
→ SUPERVISED
→ AUTONOMOUS
→ HIGH-TRUST AUTONOMOUS
```

Track evidence per agent × capability, including volume, grounding, human acceptance/modification/rejection, contradictions, critical errors, freshness, recovery and incidents.

Agents may never self-promote authority/autonomy.

Downgrades should be scope-limited, visible, reversible and explainable where possible.

---

## 29. V1.3-J — Agent Organization Runtime

Evaluate runtime candidates against identity, hierarchy, messaging, memory, delegation, scheduling, failure handling, tools, observability, multitenancy, authority compatibility and transparency compatibility.

Candidate outcomes:

```text
ADOPT / TRIAL / WRAP / BORROW / FORK / REJECT
```

AIOS retains semantic/authority sovereignty regardless of framework choice.

---

## 30. V1.3-K — Execution / Coworker Runtime

Provider-neutral bounded execution for files, documents, browser, terminal/code, email, calendar, MCP/connectors, scheduled work, external actions, resumable jobs and sandbox classes.

Munder Difflin remains an experimental reference. OpenWorker remains a replaceable execution/coworker reference. Neither owns AIOS semantics or authority.

---

## 31. V1.3-L — Live Organization

Bring canonical Agents, Departments, Missions, WorkItems, collaboration, blocked work, incidents, autonomy, quality, cost and performance into Cockpit.

No fake or simulated activity where the UI claims live organizational state.

---

## 32. V1.3-M — Board Transparency Experience

Build progressive, grounded inspection surfaces such as:

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

The Board should receive summaries and exceptions at the top level with drill-down access to the durable underlying record.

---

## 33. V1.3-N — Learning & Optimization

Deepen LearningRecords, human-correction analysis, capability performance, readiness calibration, policy/routing tuning, false/missed escalation analysis, evaluation datasets and curated learning examples.

Not every Activity becomes training truth.

---

## 34. V1.3 dependency sequence

```text
A Constitutional Contracts
        ↓
B Minimal Governance Kernel
        ↓
C Transparency Foundation
        ↘
         D Context & Agent Identity
          ↓
E First Governed Mobility Vertical
        ↓
F Decision Readiness + G Independent Verification
        ↓
H Organizational Immune System
        ↓
I Earned Autonomy
        ↓
J Agent Runtime + K Execution Runtime
        ↓
L Live Organization
        ↓
M Board Transparency Experience
        ↓
N Learning & Optimization
```

C starts early because transparency is a prerequisite for trustworthy autonomy, not a UI feature to bolt on later.

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
- no framework-driven architecture change without measured benefit.

### Track C — High-Autonomy Organization

V1.3 A–N implementation described above.

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
- Which material attempts were blocked and why?
- Which actions were routed to review?
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
Blocked material attempts / 1,000 actions
Review-routed material attempts / 1,000 actions
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
3. freeze the exact implementation boundary;
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
7. Material attempts that are blocked or review-routed must not silently disappear.
8. Agents may hold real delegated authority.
9. Authority is capability-specific and bounded.
10. Autonomy is earned and capability-specific.
11. Agents cannot self-promote authority/autonomy.
12. Memory is not canonical truth.
13. Memory provides continuity; Evidence provides authority.
14. Material truth crosses typed deterministic canonicalization.
15. Material autonomous mutations cross the Command Gateway as runtime integration expands.
16. Scores/readiness route; deterministic gates authorize.
17. Verification depth scales with risk/uncertainty/novelty.
18. Legal/policy human requirements override confidence.
19. Parallel agents use explicit version/concurrency controls.
20. External frameworks provide capability; AIOS owns semantics/authority.
21. Immune-system intervention must be explainable.
22. Restrictions should be scope-limited where possible.
23. Irreversible actions receive stronger prechecks.
24. Recovery distinguishes reversible/compensatable/irreversible/append-only correction.
25. Learning preserves labeled outcomes/corrections.
26. Governance cost scales with risk rather than being maximal everywhere.
27. Context is scoped/lazy/versioned.
28. Governance is not a global execution mutex.
29. Summaries do not replace required underlying records.
30. Secrets/protected data remain secure under transparency.
31. Conversation is Activity but not authority.
32. Provider-local state/logs do not silently become canonical AIOS truth.
33. Agents may be wrong while thinking; AIOS may not be wrong silently when committing truth.

---

## 45. Immediate next action

Current engineering state:

```text
V1.3-A     COMPLETE / PASS / SEALED
V1.3-B.1   COMPLETE / PASS / SEALED AS FOUNDATION
V1.3-B.2   COMPLETE / PASS / SEALED
V1.3-C.1   COMPLETE / PASS / SEALED
V1.3-C.2   IMPLEMENTED / CANONICAL ACCEPTANCE PENDING
```

Immediate action: run canonical C.2 acceptance before expanding Transparency further.

Required focused chain:

```text
pytest apps/api/tests/test_organization_governance_kernel.py \
       apps/api/tests/test_organization_governed_work.py \
       apps/api/tests/test_organization_transparency.py \
       apps/api/tests/test_organization_transparency_attempts.py -q
```

Then repository policy, full API regression, migration/schema checks, `git diff --check`, and clean synchronized status.

If C.2 passes, select the next smallest requirement from the first mobility vertical. Preferred candidates are explicit causation, a bounded Board/Cockpit transparency query contract, or Evidence/tool/decision lineage. Do not expand all C abstractions at once.

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

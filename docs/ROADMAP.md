# Global Mobility AIOS — Active Product & Delivery Roadmap

**Roadmap generation:** V11.4 / Technology Radar V1.1 runtime-governance alignment  
**Date:** 2026-08-19  
**Development branch:** `roadmap/global-mobility-aios-v11`  
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active product slice:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR  
**Current Technology Radar state:** Wave 1 PILOT COMPLETE; Wave 2 IN PROGRESS with Docling pilot started  
**Human-like organization architecture:** V1.2 CANONICAL / RUNTIME-GOVERNANCE INVARIANTS FROZEN  
**Code migration head:** `0076_organization_position_active_identity`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This is the canonical active strategic/delivery roadmap. Historical detail remains in `CHANGELOG.md`, Git history, and archived roadmap/changelog snapshots.

---

## 1. Product definition

Global Mobility AIOS is a **governed global mobility intelligence operating system** for the movement of people, talent, families, businesses, and capital across borders.

It is not merely a visa chatbot, document uploader, CRM, agent demo, generic SaaS dashboard, or disconnected automation collection.

The product combines:

- CRM, identity, intake, consent, and long-lived case continuity;
- universal mobility profiles and goal/constraint context;
- official-source and regulatory intelligence;
- pathway discovery/versioning/comparison and eligibility reasoning;
- evidence, provenance, documents, cost, risk and timelines;
- appointments, submissions, agency/authority workflow;
- post-arrival / renewal / residence / citizenship progression;
- governed agents, executives, departments and position contracts;
- Missions, WorkItems, Blockers, Dependencies, Conversations, Human Actions, Decisions, Contributions, Activity and audit state;
- role-specific experiences for Owner/Board, Professionals/Operators, Mobility Users and future partners/employers;
- a human-like AI organization that communicates naturally while remaining measurable, grounded and accountable.

North-star mobility lifecycle:

```text
Dream / Goal
   ↓
Profile + constraints
   ↓
Country / pathway discovery
   ↓
Eligibility + evidence + risk + cost + timeline
   ↓
Study / Work / Family / Business / Investment / Remote-work move
   ↓
Documents / submissions / appointments / authority decisions
   ↓
Post-arrival / operation
   ↓
Renewal / status change / family progression
   ↓
Long-term residence
   ↓
Citizenship / global mobility strategy
```

---

## 2. Product surfaces

- **Global Mobility AIOS Cockpit** — Human Owner / Board control, oversight, quality and organization-intelligence surface.
- **Board Room** — reserved Owner/Board authority module inside Cockpit.
- **Operations** — Professional / Operator experience.
- **My Mobility** — Mobility User experience.
- `/my-mobility` — non-sensitive orientation/access.
- `/portal` — secure token/device-bound personalized client workspace.

Backend authorization remains authoritative. Navigation, persona, prompt wording, model/provider identity or UI visibility never grants domain/business/legal authority.

Visual direction remains premium enterprise AIOS: deep navy/graphite, warm ivory, selective serif + operational sans, restrained depth, premium iconography, subtle meaningful motion, strong information density and role clarity.

---

## 3. Permanent architecture invariants

1. **AIOS Semantic Sovereignty** — external technology implements capabilities; AIOS owns meaning.
2. **Evidence before regulated certainty** — memory, conversation, retrieval, OCR, normalization, model output and source diffs are not legal truth by themselves.
3. **Broad cognition, scoped context** — agents receive sufficient relevant context, not unrestricted unrelated sensitive data.
4. **Narrow mutation** — important authoritative writes use typed AIOS commands and validation.
5. **Deterministic authority** — authority comes from authenticated identity/position/contracts, never prompt/persona/model confidence.
6. **Consequential action proposal-first** — important real-world/domain changes are prepared by agents and reviewed/modified/approved by the appropriate human unless a separately accepted bounded autonomy policy exists.
7. **Distributed review, centralized oversight** — human review happens at the lowest appropriate surface; material oversight converges in Cockpit.
8. **Board Room remains reserved** — not a generic human-review inbox.
9. **Conversation is Activity but not authority** — `AgentMessage ⊂ OrganizationActivity`; conversation does not silently create Decision/Evidence/VerifiedRule.
10. **Memory informs work, not truth** — memory may trigger retrieval/research but is not Evidence or VerifiedRule.
11. **Provider logs are non-authoritative inputs** — provider events require AIOS normalization before canonical Activity/domain state.
12. **Canonicalization is deterministic at the material boundary** — an LLM may interpret, but final material classification resolves through typed AIOS schemas and deterministic validators.
13. **Command Gateway mutation monopoly** — autonomous agents/runtimes do not receive arbitrary production-domain write access.
14. **Optimistic concurrency** — material commands must fail stale rather than overwrite accepted newer state.
15. **Rollback/compensation is first-class** — A3/A4 and consequential actions declare reversibility/side-effect semantics where relevant.
16. **Learning outcomes stay labeled** — proposals, modifications, rejections, contradictions, stale states, supersession and human corrections do not collapse into training truth.
17. **Truthful unknowns** — missing/mismatched evidence remains unknown/not-established.
18. **Natural interaction, deterministic accountability.**
19. **Team outcomes over agent competition.**
20. **Results matter more than framework competition.**
21. **Autonomy is capability-specific and never self-granted.**
22. **Finished work over chat alone.**
23. **Atomic/versioned/reversible state where possible.**
24. **Internal Learning & Quality** — permitted operational outcomes/corrections should improve AIOS without assuming universal training permission.
25. **Preserved databases are evidence** — no demo mutation of preserved `gmai.db`.
26. **Austria simulation safety remains frozen** — uncertain simulation state is never promoted to production certainty.

Five hard canonicalization constraints:

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

Final runtime principle:

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

---

## 4. Accepted product baseline

### 13.16.8 — Professional / Operator — COMPLETE / PASS

Accepted professional reading order:

```text
Decision / context
  ↓
Blockers + uncertainty
  ↓
Governed next actions
  ↓
Supporting evidence / review state
  ↓
Technical provenance
```

Historical/mismatched evidence remains inspectable but cannot silently support current conclusions.

### 13.16.9 — Evidence / provenance UX — COMPLETE / PASS

Shared grammar distinguishes official source, immutable snapshot, review/certification, VerifiedRule, pathway evidence, case evidence, superseded history and unresolved gaps.

### 13.16.10 — Integrated responsive/accessibility acceptance — COMPLETE / PASS

Accepted evidence includes:

- design foundation **28/28 PASS**;
- request/auth **4/4 PASS**;
- Next.js build **41/41 PASS**;
- complete API regression **811 passed / 5 skipped / 0 failed** carried forward for the frontend-only boundary;
- browser/mobile/keyboard/Portal acceptance PASS;
- preserved `gmai.db` SHA256 `23FC012AF3FA89804A84A9C8DD75C0C68515B23AEF1813CC5460D6D73808CD31` unchanged.

No GitHub CI status is inferred from these local acceptance records.

---

## 5. Current product delivery

| Slice | State | Intent |
|---|---|---|
| 13.16.8 | COMPLETE / PASS | Professional / Operator workspace |
| 13.16.9 | COMPLETE / PASS | evidence/provenance presentation |
| 13.16.10 | COMPLETE / PASS | integrated responsive/accessibility role experience |
| **13.17** | **IN PROGRESS / PAUSED** | owner-led human acceptance |
| Final Phase 13 disposition | LOCKED | after findings corrected/retested or explicitly dispositioned |
| Phase 14 | NOT STARTED / DEMAND-GATED | scale validated product |

### Phase 13.17

The evaluator is the product Owner. Evidence is genuine human use, but not independent third-party validation.

Checkpoint:

- [PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md](PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md)

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

Architecture/platform work does **not wait** for this phase to finish. Existing findings still remain unresolved evidence until corrected/retested/dispositioned.

---

## 6. Parallel delivery model

The project intentionally advances three coordinated tracks.

### Track A — Product / Human Experience

- Phase 13.17 acceptance;
- bounded corrections;
- Operations/Cockpit/My Mobility refinement;
- role clarity;
- explainability and traceability.

### Track B — Technology Radar / Platform Evolution

- Wave 2 document/privacy intelligence;
- Wave 3 regulatory monitoring;
- Wave 4 AI runtime/retrieval/quality;
- Wave 6 output technologies when needed.

### Track C — Human-Like Organization / Agent Runtime Control Plane

- deterministic Canonicalization contracts;
- Command Gateway mutation monopoly;
- provenance-aware ContextBundle;
- optimistic concurrency;
- proposal-first consequential actions;
- rollback/compensation;
- tiered OrganizationActivity;
- capability autonomy;
- Munder Difflin research/pilot;
- OpenWorker/Coworker research/pilot;
- Live Organization;
- labeled organizational learning.

Parallel means **no artificial stop-and-wait**. It does not mean unbounded implementation. Every slice keeps exact scope, tests, rollback, authority/evidence constraints and roadmap/changelog discipline.

---

## 7. Technology Radar V1.1

Canonical documents:

- [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md)
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md)
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md) — predecessor
- [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md)
- [ADR/0002-provider-neutral-platform-adapters.md](ADR/0002-provider-neutral-platform-adapters.md)

### Adoption lifecycle

```text
REFERENCE → RESEARCH → BENCHMARK → PILOT → TRIAL → ADOPT
```

Fit and adoption state are separate.

### A+ current state

| Technology | Capability | Adoption state |
|---|---|---|
| Promptfoo | AI quality/safety evaluation | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | neutral telemetry | PILOT COMPLETE / TRIAL-ELIGIBLE |
| ClamAV | malware scanning | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | document normalization | PILOT IN PROGRESS |
| Presidio | Privacy Gateway | QUEUED PILOT |
| urlwatch | source monitoring | QUEUED PILOT |
| **Munder Difflin** | Agent Organization Fabric / Live Organization | **REFERENCE / CONTROLLED RESEARCH** |
| **OpenWorker** | Coworker / finished-work execution | **REFERENCE / CONTROLLED RESEARCH** |
| Temporal | durable execution | DEFERRED PILOT |
| OpenFGA | relationship authorization | DEFERRED PILOT |

### A specialist state

- pgvector — BENCHMARK;
- Qdrant — BENCHMARK against pgvector;
- Pydantic AI — research/pilot candidate;
- Langfuse — research/pilot candidate behind OpenTelemetry;
- PaddleOCR / Unlimited-OCR — gap-triggered benchmark only;
- DSPy — research;
- Gotenberg / Typst — queued when professional-output need exists;
- EU DSS — research.

---

## 8. Wave 1 / Wave 2 current runtime truth

### Wave 1 — COMPLETE at pilot level

- Promptfoo pilot complete;
- OpenTelemetry pilot complete;
- ClamAV pilot complete.

These are `PILOT COMPLETE / TRIAL-ELIGIBLE`, not automatically `ADOPT`.

### Wave 2 — IN PROGRESS

Current path:

```text
ClamAV
  ↓
Docling
  ↓
measure current OCR/document quality
  ↓
Presidio / Privacy Gateway
  ↓
Evidence / document intelligence
```

Current:

- Docling pilot started;
- Presidio next queued;
- specialist OCR only if measured Docling/current-stack gaps justify it.

Latest accepted runtime evidence before the docs-only architecture updates:

- API **873 passed / 5 skipped / 0 failed**;
- Next.js **41/41 PASS**;
- design foundation **28/28 PASS**;
- preserved `gmai.db` unchanged.

These are carried forward and not represented as rerun by docs-only architecture commits.

---

## 9. Human-Like High-Autonomy Architecture V1.2

Canonical architecture:

- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md)

Core target:

```text
Human Owner / Board
        ↓
Cockpit / Owner Command
        ↓
AI CEO
        ↓
Organization OS / Domain Truth
        ↓
AIOS Context Broker
        ↓
Agent Organization Fabric
        ↓
Agent cognition / conversation / memory
        ↓
Proposed Intent
        ↓
Canonicalization Gateway
  optional LLM interpretation
  + typed deterministic classification
        ↓
Command Gateway
  only autonomous-agent production mutation path
        ↓
Authority + Grounding + Consistency
        ↓
Expected-version / concurrency check
        ↓
Internal bounded action
        OR
Consequential Action Proposal
        ↓
Human approve / modify / return / reject where required
        ↓
Atomic/versioned/idempotent execution
        ↓
Rollback/compensation metadata
        ↓
OrganizationActivity + Audit
        ↓
Labeled Learning & Quality
```

---

## 10. Munder Difflin + OpenWorker

They remain complementary A+ references.

### Munder Difflin informs

- identities;
- conversations/mailboxes;
- memory;
- orchestration;
- dependencies;
- scheduling;
- budgets;
- circuit breakers;
- capabilities/skills;
- live organization visibility.

### OpenWorker informs

- finished deliverables;
- files/artifacts;
- tools/terminal;
- MCP;
- connectors;
- scheduled work;
- external actions;
- approval inbox;
- model portability;
- outcome-oriented Coworker UX.

### AIOS Execution Broker owns composition

Routing may consider:

- capability;
- SLA urgency;
- expected quality;
- evidence requirements;
- workload/capacity;
- correction/rework history;
- cost;
- privacy/data-use constraints;
- provider health;
- fallback availability.

> **Governed outcome quality matters more than framework ownership.**

---

## 11. Runtime control plane

### 11.1 Context Broker

Provides task/tenant/purpose/sensitivity-scoped, provenance-aware context rather than unrestricted agent database access.

Future `ContextBundle` should preserve:

```text
context_bundle_id
mission_id
case_id?
context_version
generated_at
facts[] + provenance/support state
evidence[]
verified_rules[]
source_snapshots[]
unknowns[]
contradictions[]
agent capability / authority context
context_hash
```

`AgentRun` should bind to the bundle/hash plus model, prompt/program, role-card, tool and connector versions.

### 11.2 Canonicalization Gateway

May use LLM interpretation, but material classifications such as Decision/VerifiedRule/certification/publication/eligibility/external action must resolve through typed AIOS schemas and deterministic rules.

### 11.3 Command Gateway

Only typed governed commands create important authoritative mutations after identity, authority, capability, evidence, contradiction, version/precondition, review, idempotency and transaction checks.

Autonomous runtimes do not receive arbitrary production-domain database writes.

### 11.4 Optimistic concurrency

Material commands bind to `expected_version` / expected state / precondition hash where appropriate.

```text
read V14
→ another accepted mutation creates V15
→ proposal still expects V14
→ STALE
→ reject
→ refresh ContextBundle
→ re-evaluate
```

### 11.5 Rollback / compensation

A3/A4 and consequential commands should declare where relevant:

```text
reversible
compensation_command
previous_version
side_effects
external_side_effects
rollback_deadline
```

A4 requires meaningful rollback/compensation, not merely an audit log.

---

## 12. Consequential Action Proposal

First-class proposal lifecycle:

```text
DRAFT
  ↓
PROPOSED
  ↓
AIOS VALIDATION
  ↓
HUMAN REVIEW
  ├── APPROVE
  ├── MODIFY
  ├── RETURN FOR REVISION
  └── REJECT
  ↓
APPROVED
  ↓
FINAL VERSION / PRECONDITION CHECK
  ↓
EXECUTE
  ↓
VERIFY
```

Explicit proposal-first action classes:

- send email / external communication;
- change eligibility;
- certify evidence;
- submit application;
- change/publish VerifiedRule;
- change client status.

Agents should prepare as much as possible: draft payload, evidence, rationale, impact, attachments, validation and uncertainty. The human should review **the finished proposed action**, not redo the work from scratch.

Review goes to the lowest appropriate human surface, not automatically Board Room.

Human modifications preserve proposal-to-final lineage for quality/learning.

---

## 13. Truth and anti-hallucination controls

Trust ladder:

```text
L0 model speculation
L1 conversation / memory
L2 retrieved information
L3 source snapshot
L4 governed Evidence
L5 reviewed candidate
L6 VerifiedRule / certified fact
L7 governed case conclusion
L8 approved authority-bearing action
```

Hard transitions:

```text
L1 cannot jump to L6
L2 cannot jump to L7
L6 does not automatically create L8
```

Material agent results should carry support/evidence/uncertainty/contradiction metadata. Model self-confidence is not a permission control.

Contradiction detection should compare proposals against current Evidence, VerifiedRules, source authority/effective date, supersession, case facts, pathway version, decisions, accepted prior state and current aggregate version.

Default failure recovery:

```text
self-correct
  ↓
peer review
  ↓
specialist review
  ↓
human where required
```

Peer agreement is useful but not proof; high-risk work should also use independent evidence/deterministic checks.

---

## 14. Capability-specific autonomy and sandbox

Suggested autonomy scale:

```text
A0 prohibited
A1 human execution required
A2 human approval required
A3 autonomous + mandatory post-review
A4 autonomous + monitoring / real rollback or compensation
A5 fully autonomous bounded internal operation
```

Autonomy belongs to capability + context, not simply agent identity.

Powerful runtimes use a bounded sandbox for filesystem, network, secrets, shell, connectors, cost, time and production mutation access.

Performance may recommend an autonomy change; the agent cannot grant itself authority.

Future `AutonomyEvidenceProfile` may track executions, acceptance, modification, rejection, contradiction, grounding, SLA, incident and rollback rates before recommending a level change.

---

## 15. OrganizationActivity tiering

Canonical relationship remains:

```text
AgentMessage ⊂ OrganizationActivity
```

Runtime class should be explicit:

```text
CONVERSATIONAL
COLLABORATIVE
OPERATIONAL
MATERIAL
AUTHORITY
```

Suggested treatment:

- **CONVERSATIONAL** — high volume; human-inspectable; compress/summarize after retention window where policy permits.
- **COLLABORATIVE** — handoffs/peer review/shared findings; structured and analytics-friendly.
- **OPERATIONAL** — durable work execution history.
- **MATERIAL** — long-term durable and Cockpit-visible where appropriate.
- **AUTHORITY** — highest durability / immutable-tamper-evident target linked to exact approved payload and AuditLog.

Conversation remains showable to permitted humans even when long-term storage uses summarization/retention policy.

---

## 16. Mission / SLA / KPI / OKR / Definition of Done

`Mission` is the outcome-level concept above WorkItems.

Mission may include objective, owner, participants, service class, SLA, KPIs, Definition of Done, conversations, WorkItems, dependencies, blockers, artifacts, proposals, decisions and outcome.

### SLA

- acknowledge;
- start;
- respond;
- complete;
- review;
- freshness;
- escalation;
- blocker age;
- retry/recovery.

### KPI

- delivery;
- quality;
- grounding/provenance;
- collaboration;
- cost;
- human effort;
- proposal acceptance/modification/rejection;
- contradiction/stale-proposal/rollback rates;
- governance compliance.

**Mission/team outcome is primary. Individual metrics are diagnostic.**

### OKR

Strategic improvement above operational KPIs.

### Definition of Done

Material work requires explicit deliverables, evidence/provenance, uncertainty, required reviews/proposal disposition, SLA status, verified result and recorded outcome/exception/rollback state.

---

## 17. Learning & Quality

Three separate layers:

1. Operational Intelligence;
2. Evaluation & Quality;
3. Training & Optimization.

Learning must preserve labeled outcome states such as:

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

Never:

```text
everything agents said
→ training truth
```

Prefer:

```text
proposal
+ validation result
+ human correction/modification
+ final accepted outcome
→ labeled learning example
```

Architecture/quality capability may progress in parallel. Real-client-data training/reuse requires explicit data-use/legal/compliance treatment, sensitivity controls, retention/deletion, tenant policy and lineage.

---

## 18. Progressive intervention

```text
NORMAL
→ STEER
→ ASSIST / PEER SUPPORT
→ REASSIGN
→ CONSTRAIN
→ SUSPEND SPECIFIC AGENT / CAPABILITY
→ EXECUTIVE / HUMAN ESCALATION
→ EMERGENCY ORGANIZATION STOP
```

`Pause Organization` is emergency-only.

---

## 19. Live Organization

Future Cockpit visualization may show:

- departments/positions;
- Missions;
- agents working/waiting/blocked/collaborating;
- conversation/delegation flows;
- Dynamic Squads;
- SLA risk;
- workload/capacity;
- proposal queues;
- cost/quality;
- interventions;
- direct conversation with CEO/executives/specialists.

Visual truth must come from AIOS-owned normalized state, not provider animation alone.

---

## 20. Platform Evolution implementation sequence

These tracks may progress in parallel with product acceptance.

### Wave 5A — Runtime Control Plane / Immune System

- deterministic Canonicalization Gateway contracts;
- Command Gateway as sole autonomous-agent production mutation path;
- provenance-aware Context Broker / ContextBundle;
- expected-version / optimistic concurrency;
- idempotency / preconditions;
- ConsequentialActionProposal;
- review/modify/approve/reject lifecycle;
- evidence sufficiency;
- contradiction detection;
- capability autonomy;
- sandbox;
- rollback/compensation metadata;
- labeled LearningRecord outcome model.

### Wave 5B — Organization Semantics

- Mission;
- AgentConversation;
- tiered conversational OrganizationActivity;
- Dynamic Squad;
- Capability Registry;
- memory scopes;
- AgentRelationship;
- SLA;
- KPI/OKR;
- Definition of Done.

5A and 5B may progress together where dependencies permit. Deep external-agent mutation capability depends on the relevant 5A controls existing.

### Wave 5C — Munder Difflin Agent Organization Fabric

Controlled research/pilot behind AIOS-owned contracts.

### Wave 5D — Execution Broker + OpenWorker / Coworker

Controlled research/pilot for finished work, files/tools/MCP/connectors and proposal-gated external actions.

### Wave 5E — Live Organization / Cockpit

Premium visualization and direct interaction.

### Wave 5F — Organizational Learning & Optimization

Improve routing, team composition, proposal quality, contradiction recovery, autonomy recommendations, SLA, model/runtime selection and capacity decisions from permitted labeled outcomes.

---

## 21. Runtime acceptance gates for Wave 5A+

### Canonicalization

- unstructured message cannot directly become `ExecutiveDecision`;
- memory cannot directly become Evidence/VerifiedRule;
- provider event does not automatically become canonical Activity;
- final material classification uses typed schema + deterministic validators.

### Mutation path

- agent-originated production write outside Command Gateway fails;
- arbitrary provider/MCP DB mutation is unavailable;
- required human gate cannot be bypassed;
- idempotency prevents duplicate consequential execution.

### Concurrency

- stale expected version rejects;
- accepted V15 cannot be overwritten by proposal based on V14;
- stale re-evaluation receives refreshed context.

### Rollback

- reversible action exposes compensation;
- A4 requires valid rollback/compensation semantics;
- irreversible external effects cannot masquerade as reversible.

### Learning

- rejected/modified/contradicted outcomes retain labels;
- accepted canonical state remains distinguishable from proposal text;
- context/model/program/tool versions are reconstructable.

### Activity

- conversational messages remain legitimate Activity;
- activity class is explicit;
- AUTHORITY Activity has highest-durability/tamper-evident treatment target;
- provider logs remain non-authoritative until normalized.

---

## 22. Phase 14 relationship

Phase 14 remains a scale programme for a validated product. It does **not** mean all platform/architecture development must wait until Phase 14.

Technology Radar and human-like organization foundations may proceed as bounded parallel tracks before Phase 14 when their scope and safety contracts are explicit.

---

## 23. Acceptance / repository discipline

Every implementation slice must:

1. verify branch/SHA and clean baseline;
2. read canonical docs;
3. freeze exact boundary;
4. implement incrementally;
5. run focused/broad acceptance appropriate to the change;
6. perform browser/runtime review for user-facing work;
7. update ROADMAP every project patch;
8. update CHANGELOG for meaningful delivery;
9. stage exact files only;
10. check staged diff/whitespace;
11. commit/push truthfully;
12. verify local == remote;
13. verify clean tree;
14. preserve database/release invariants;
15. create immutable local archive when sealing from the canonical local repository.

Never claim PASS evidence that was not actually run.

No Phase 13.17 finding is fixed merely because architecture text explains the intended design.

---

## 24. Canonical documents

- [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [REPOSITORY_POLICY.md](REPOSITORY_POLICY.md)
- [DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md](DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md)
- [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md)
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md) — predecessor
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md) — predecessor
- [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md)
- [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md)
- [ADR/0002-provider-neutral-platform-adapters.md](ADR/0002-provider-neutral-platform-adapters.md)
- [PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md](PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md)
- [CHANGELOG.md](CHANGELOG.md)

---

## 25. Current decision

- Phase 13.17 remains **IN PROGRESS / PAUSED**, owner-led.
- Product acceptance and platform/architecture work proceed **in parallel**.
- Wave 1 is **PILOT COMPLETE / TRIAL-ELIGIBLE**.
- Wave 2 is **IN PROGRESS** with Docling started and Presidio queued.
- Munder Difflin and OpenWorker are complementary A+ references.
- Human-Like High-Autonomy Architecture V1.2 is the active organization direction.
- Wave 5A Runtime Control Plane and Wave 5B Organization Semantics may proceed as bounded architecture/implementation slices without waiting for Phase 13.17 completion.
- Material canonicalization must end in typed/deterministic AIOS rules, not an unconstrained LLM decision.
- Command Gateway is the sole production mutation path for autonomous agents/runtimes.
- Material writes use optimistic concurrency/version checks.
- Consequential actions remain proposal-first: agents prepare work; appropriate humans approve/modify/return/reject before execution where required.
- Rollback/compensation and learning outcome labels are first-class runtime requirements.
- No docs-only checkpoint installs Munder/OpenWorker or proves runtime behavior.

Long-term flywheel:

> **Work → Outcomes → Corrections → Intelligence → Evaluation → Training/Optimization where permitted → Better AIOS → Better Work.**

Defining runtime principle:

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

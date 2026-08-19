# Global Mobility AIOS — Technology Radar V1.1

**Status:** ACTIVE CANONICAL V1.1 — platform evolution / evaluation / controlled implementation track  
**Date:** 2026-08-19  
**Accepted product baseline:** Phase 13.16.10 COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active product slice:** Phase 13.17 — owner-led human acceptance, IN PROGRESS / PAUSED BY EVALUATOR  
**Platform evolution:** continues in parallel through bounded implementation slices  
**Current Radar runtime state:** Wave 1 complete; Wave 2 in progress with Docling pilot started  
**Canonical organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md)  
**Historical architecture predecessor:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md)  
**Historical Radar predecessor:** [TECHNOLOGY_RADAR_V1.md](TECHNOLOGY_RADAR_V1.md)

Technology Radar V1.1 identifies external/open-source technologies and architecture patterns that can materially strengthen Global Mobility AIOS without allowing third-party frameworks to define AIOS domain semantics, organizational authority, evidence truth, legal status, certification/publication state, or business outcomes.

The Radar is not a dependency manifest. Inclusion means a capability/technology is strategically relevant. Runtime adoption still requires a bounded implementation slice, benchmark or acceptance contract, security/data-flow review, rollback, and exit strategy.

---

## 1. Permanent architecture principles

### 1.1 AIOS Semantic Sovereignty

> **Third-party infrastructure may implement, accelerate, execute, retrieve, parse, monitor, observe, scan, render, evaluate, optimize, coordinate, remember, connect, or otherwise support an AIOS-defined capability, but it may never become authoritative for AIOS domain meaning, legal status, evidence state, certification state, publication state, human-review requirements, organizational authority, Mission/WorkItem semantics, ExecutiveDecision semantics, Contribution semantics, canonical OrganizationActivity semantics, or business outcomes.**

Preferred pattern:

```text
AIOS domain / Organization OS
        ↓
AIOS-owned capability contract
        ↓
AIOS adapter / Execution Broker
        ↓
external runtime / technology
```

### 1.2 Human-like organization principles

> **Human in interaction. Machine-like in reliability.**

> **Broad cognition. Scoped context. Narrow mutation. Deterministic authority. Reversible execution.**

> **Natural interaction, deterministic accountability.**

> **Activity is broad; authority is narrow.**

> **Team outcomes over agent competition.**

> **Results matter more than provider competition.**

> **Agents may be creative in cognition. AIOS must be conservative in truth.**

> **Consequential actions are proposal-first unless an explicitly bounded autonomy policy permits direct execution.**

### 1.3 Five hard canonicalization invariants

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

Useful promotion paths remain allowed through AIOS-owned validation/canonicalization.

---

## 2. Fit and adoption state are separate

V1.1 now separates **strategic fit** from **adoption state**.

Strategic fit answers:

> How valuable could this technology be to AIOS?

Adoption state answers:

> How much implementation evidence do we currently have?

Canonical lifecycle:

```text
REFERENCE
  ↓
RESEARCH
  ↓
BENCHMARK
  ↓
PILOT
  ↓
TRIAL
  ↓
ADOPT
```

`PILOT COMPLETE / TRIAL-ELIGIBLE` is intentionally different from `ADOPT`.

---

## 3. Technology fit tiers and current adoption state

### 3.1 A+ — strongest strategic fit

| Technology | AIOS capability | Adoption state |
|---|---|---|
| **Promptfoo** | AI regression / adversarial / quality evaluation | **PILOT COMPLETE / TRIAL-ELIGIBLE** |
| **OpenTelemetry** | vendor-neutral engineering telemetry | **PILOT COMPLETE / TRIAL-ELIGIBLE** |
| **ClamAV** | untrusted-upload malware scanning / quarantine boundary | **PILOT COMPLETE / TRIAL-ELIGIBLE** |
| **Docling** | document normalization / structured document intelligence | **PILOT IN PROGRESS** |
| **Presidio** | Privacy Gateway / sensitive-data processing | **QUEUED PILOT** |
| **urlwatch** | official-source change monitoring | **QUEUED PILOT** |
| **Munder Difflin (`chaitanyagiri/munder-difflin`)** | Agent Organization Fabric / natural multi-agent coordination / Live Organization | **REFERENCE / CONTROLLED RESEARCH** |
| **OpenWorker (`andrewyng/openworker`)** | AIOS Coworker / finished-work execution / tools-connectors-deliverables | **REFERENCE / CONTROLLED RESEARCH** |
| **Temporal** | durable timers, waits, retries, signals, resumption | **DEFERRED PILOT** |
| **OpenFGA** | relationship authorization behind AIOS authority semantics | **DEFERRED PILOT** |

### 3.2 A — specialist technologies

| Technology | Intended capability | Adoption state |
|---|---|---|
| **pgvector** | governed semantic retrieval | **BENCHMARK** |
| **Qdrant** | dedicated semantic retrieval alternative | **BENCHMARK against pgvector** |
| **Pydantic AI** | typed production AI/agent runtime | **RESEARCH / PILOT CANDIDATE** |
| **Langfuse** | LLM/agent engineering observability behind OpenTelemetry | **RESEARCH / PILOT CANDIDATE** |
| **PaddleOCR** | specialist OCR / extraction | **GAP-TRIGGERED BENCHMARK ONLY** |
| **Unlimited-OCR** | advanced OCR/VLM extraction | **GAP-TRIGGERED BENCHMARK ONLY** |
| **DSPy** | offline AI-program optimization | **RESEARCH** |
| **Gotenberg** | commodity PDF/document conversion | **QUEUED WHEN OUTPUT NEED EXISTS** |
| **Typst** | premium professional report generation | **QUEUED WHEN OUTPUT NEED EXISTS** |
| **EU DSS** | EU electronic-signature validation | **RESEARCH** |

### 3.3 Conditional / fallback

- Fides;
- OpenLineage;
- OPA;
- OpenFeature;
- Haystack;
- MarkItDown.

A candidate is removed because another technology demonstrably wins the **same capability**, not because an unrelated framework is more fashionable.

---

## 4. Munder Difflin + OpenWorker — coordinated, not competing

### Munder Difflin role

Principal reference for:

- persistent agent identities;
- agent-to-agent messages/mailboxes;
- conversations;
- shared/long-term memory mechanics;
- orchestration / supervisor patterns;
- dependency-aware coordination;
- scheduled missions;
- human intervention patterns;
- agent budgets / cost telemetry;
- circuit breakers;
- skills / capability discovery;
- live organization visualization.

### OpenWorker role

Principal reference for:

- finished deliverables;
- files/artifacts;
- tools / terminal;
- MCP;
- connectors;
- scheduled work;
- external application actions;
- model portability;
- consequential-action approval patterns;
- unattended approval inbox;
- local-first coworker execution.

### Combined rule

```text
Munder organization strengths
        +
OpenWorker finished-work strengths
        +
AIOS-native services / deterministic logic
        ↓
AIOS Execution Broker
        ↓
best governed result for the Mission
```

Neither Munder nor OpenWorker owns Mission, WorkItem, Evidence, VerifiedRule, ExecutiveDecision, canonical OrganizationActivity, case state, certification/publication, or authority semantics.

---

## 5. AIOS high-autonomy control plane

Before powerful agent execution is allowed to mutate important state, AIOS should provide an explicit control plane.

### 5.1 Context Broker

Provides scoped `ContextBundle` based on:

- tenant;
- actor/position;
- Mission/case purpose;
- minimum necessary;
- sensitivity;
- tool/provider recipient;
- jurisdiction;
- data-use constraints.

### 5.2 Canonicalization Gateway

Normalizes non-authoritative inputs such as:

- agent messages;
- memory;
- provider events;
- model outputs;
- retrieval;
- OCR;
- source monitoring;
- OpenWorker/Munder events.

It may produce:

- telemetry-only event;
- OrganizationActivity;
- WorkItem/Mission candidate;
- Evidence candidate;
- VerifiedRule candidate;
- Decision candidate;
- ConsequentialActionProposal;
- conflicted/unsupported result.

### 5.3 Command Gateway

Authoritative mutations occur through typed AIOS commands with checks for:

- identity;
- deterministic authority;
- capability scope;
- tenant/case scope;
- evidence sufficiency;
- contradictions;
- state/version preconditions;
- required human/professional/source/certification gate;
- idempotency;
- transaction safety.

### 5.4 Execution Sandbox

Powerful runtimes should use bounded:

- filesystem;
- network;
- secrets;
- shell;
- connectors;
- cost/token budget;
- execution time;
- production-data mutation paths.

---

## 6. Consequential Action Proposal

The future product should let agents **prepare almost all of the work** while humans retain efficient review/modification for consequential actions.

Proposal lifecycle:

```text
DRAFT
  ↓
PROPOSED
  ↓
HUMAN REVIEW
  ├── APPROVE
  ├── MODIFY
  ├── RETURN FOR REVISION
  └── REJECT
  ↓
APPROVED
  ↓
EXECUTE
  ↓
VERIFY RESULT
  ↓
COMPLETED / FAILED / PARTIAL
```

Explicit proposal-first action classes:

1. **send email / external communication**;
2. **change eligibility**;
3. **certify evidence**;
4. **submit application**;
5. **change / publish VerifiedRule**;
6. **change client status**.

The agent may draft, assemble evidence, preflight, explain impact, and recommend the action. The appropriate human reviews/modifies/approves. Review occurs at the lowest appropriate surface, not automatically in Board Room.

A later, separately governed policy may permit direct execution for a narrowly defined low-risk action class after sufficient acceptance evidence; no agent self-grants that autonomy.

---

## 7. Capability-specific autonomy

Autonomy belongs to **capability + context**, not simply an agent name.

```text
A0  prohibited
A1  human execution required
A2  human approval required
A3  autonomous with mandatory post-review
A4  autonomous with monitoring / rollback
A5  fully autonomous bounded internal operation
```

Examples:

```text
Global Intelligence
source search              A5
snapshot capture           A5
candidate extraction       A4
VerifiedRule proposal      A3/A4
VerifiedRule publication   A2/A1
```

```text
OpenWorker
create internal report     A5
draft client email         A5
send client email          A2
submit authority form      A2/A1
```

Performance may create an `AutonomyChangeRecommendation`. Authority expansion itself remains governed.

---

## 8. Truth / grounding architecture

### 8.1 Trust ladder

```text
L0  model speculation
L1  conversation / memory / working hypothesis
L2  retrieved external information
L3  captured source snapshot
L4  governed Evidence
L5  reviewed rule/evidence candidate
L6  VerifiedRule / certified governed fact
L7  governed case conclusion
L8  approved authority-bearing decision / external action
```

Hard constraints:

```text
L1 cannot jump directly to L6
L2 cannot jump directly to L7
L6 does not automatically create L8
```

### 8.2 Evidence sufficiency

Model confidence is metadata, not permission.

Material results should expose:

- support state;
- evidence IDs;
- source IDs;
- VerifiedRule IDs;
- assumptions;
- uncertainty;
- contradictions;
- missing facts.

### 8.3 Contradiction detection

Material proposals should be checked against current:

- VerifiedRules;
- Evidence;
- source authority/effective date;
- supersession;
- case facts;
- pathway/version;
- ExecutiveDecisions;
- accepted prior state.

Unsupported/conflicted outputs normally return to the agent for self-correction before unnecessary human escalation.

---

## 9. Natural communication and OrganizationActivity

Canonical relationship:

```text
AgentMessage ⊂ OrganizationActivity
```

Routine organizational conversation may be legitimate Activity without becoming formal authority-bearing state.

Examples:

- question;
- clarification;
- suggestion;
- disagreement;
- handoff;
- request;
- warning;
- peer review;
- acknowledgement;
- progress update.

Conversation may generate an intent/proposal. It does not silently create Decision/Evidence/VerifiedRule/authority.

Provider events are normalized by AIOS before becoming canonical Activity.

---

## 10. Mission / organization performance model

### Mission

Outcome-level concept above WorkItems. May contain:

- objective;
- Definition of Done;
- owner/participants;
- service class / SLA;
- KPIs;
- WorkItems;
- conversations;
- dependencies;
- blockers;
- artifacts;
- proposals;
- decisions;
- outcome.

### Dynamic Squad

Temporary cross-department collaboration around a Mission while permanent organization/authority remains intact.

### SLA

Potential dimensions:

- acknowledge;
- start;
- respond;
- complete;
- review;
- freshness;
- escalation;
- blocker age.

### KPI

Measure delivery, quality, collaboration, economics, human effort and governance.

**Mission/team result is the primary performance unit.** Individual metrics are diagnostic.

### OKR

Strategic objectives above operational KPIs.

### Definition of Done

A Mission is not finished merely because an agent says so. Material work should meet explicit deliverable, evidence, review, SLA, proposal/action and outcome criteria.

---

## 11. Progressive intervention

```text
NORMAL
  ↓
STEER
  ↓
ASSIST / PEER SUPPORT
  ↓
REASSIGN
  ↓
CONSTRAIN
  ↓
SUSPEND SPECIFIC AGENT / CAPABILITY
  ↓
EXECUTIVE / HUMAN ESCALATION
  ↓
EMERGENCY ORGANIZATION STOP
```

Constraint examples:

- proposal-only mode;
- narrower context;
- no external actions;
- additional peer review;
- lower tool/cost budget;
- model/runtime switch;
- narrower Mission scope.

`Pause Organization` remains an emergency safety control, not normal troubleshooting.

---

## 12. Distributed human review

Review occurs at the lowest appropriate level:

```text
Mobility User
→ personal facts / personal choices

Professional / Operator
→ case / eligibility / evidence / document / application / client workflow

Qualified source/certification reviewer
→ rule/evidence certification where required

Department Lead / Executive
→ delegated organizational decisions

Human Owner / Board
→ reserved strategic / organization-wide authority
```

Board Room remains reserved rather than becoming a generic approval queue.

---

## 13. Docling / OCR simplification rule

Do not add specialist OCR merely because it is on the Radar.

```text
representative document corpus
        ↓
measure Docling + existing fallback stack
        ↓
identify real gaps
        ↓
benchmark PaddleOCR / Unlimited-OCR only against those gaps
        ↓
adopt only if measurable value exists
```

Potential gaps include scan quality, languages, tables, handwriting, layout fidelity, throughput and accuracy.

---

## 14. Learning & Quality

Keep three layers distinct:

1. Operational Intelligence;
2. Evaluation & Quality;
3. Training & Optimization.

The platform may build operational/evaluation capability in parallel with the product. Training/reuse involving real client data requires the applicable data-use policy, purpose, legal/compliance treatment, sensitivity controls, retention/deletion, tenant policy, lineage and legal/privacy review.

Learning signals may include:

- corrections;
- proposal modifications/rejections;
- approvals;
- SLA misses;
- routing failures;
- peer disagreement;
- contradiction recoveries;
- provider/runtime quality;
- external-action failures;
- successful collaboration patterns.

Compliance enables lawful learning; it does not imply universal reuse permission.

---

## 15. Platform Evolution waves

Technology Radar waves are parallel implementation tracks, not a rule that everything must wait for Phase 13 closure.

### Wave 0 — Architecture & Governance — COMPLETE

- Semantic Sovereignty;
- provider-neutral adapters;
- Learning & Quality direction;
- Coworker boundary;
- Agent Organization direction;
- Human Owner Command;
- SLA/KPI/OKR direction;
- high-autonomy control architecture.

### Wave 1 — Quality Foundation — COMPLETE

- Promptfoo bounded pilot complete;
- OpenTelemetry bounded pilot complete;
- ClamAV bounded pilot complete.

These are **PILOT COMPLETE / TRIAL-ELIGIBLE**, not automatically production-standard `ADOPT` merely because the pilot passed.

### Wave 2 — Document & Privacy Intelligence — IN PROGRESS

Current:

- Docling pilot in progress;
- Presidio queued.

OCR specialists are gap-triggered only after Docling/current-stack measurement.

Latest accepted runtime evidence before this docs checkpoint remains:

- API: **873 passed / 5 skipped / 0 failed**;
- Next.js: **41/41 PASS**;
- design foundation: **28/28 PASS**;
- preserved `gmai.db` unchanged.

These are carried forward, not rerun by this documentation update.

### Wave 3 — Regulatory Monitoring

`official source → monitored change → candidate → AI analysis → source/reviewer gate → VerifiedRule`

Never `website changed → law automatically changed`.

### Wave 4 — AI Runtime / Retrieval / Quality

- Pydantic AI;
- pgvector vs Qdrant;
- DSPy;
- Langfuse behind OpenTelemetry;
- evaluation/runtime quality.

### Wave 5A — High-Autonomy Control Plane

- Context Broker;
- Canonicalization Gateway;
- Command Gateway;
- ConsequentialActionProposal;
- human modify/approve/reject lifecycle;
- evidence sufficiency;
- contradiction detection;
- capability-scoped autonomy;
- sandbox;
- versioned/atomic mutation.

### Wave 5B — Organization Semantics

- Mission;
- AgentConversation;
- conversational/collaborative OrganizationActivity;
- Dynamic Squad;
- Capability Registry;
- memory scopes;
- AgentRelationship;
- SLA;
- KPI/OKR;
- Definition of Done.

5A and 5B may progress as coordinated parallel slices.

### Wave 5C — Munder Difflin Agent Organization Fabric

Controlled research/pilot behind AIOS-owned contracts.

### Wave 5D — Execution Broker + OpenWorker / Coworker

Controlled research/pilot for files/tools/MCP/connectors/finished work and proposal-gated external actions.

### Wave 5E — Live Organization / Cockpit

Premium AIOS-native visualization and direct organizational interaction.

### Wave 5F — Organizational Learning & Optimization

Improve routing, collaboration, SLA, team composition, runtime/model choice, proposal quality and capacity decisions from permitted outcomes.

### Wave 6 — Professional Output

- Gotenberg;
- Typst;
- EU DSS;
- premium governed reports/artifacts.

### Continuous — Learning & Quality

Evaluation, quality analytics, correction learning, data/training lineage and permitted improvement run across waves.

---

## 16. Product-roadmap relationship

Phase 13.17 human acceptance and Technology Radar/platform architecture continue **in parallel**.

```text
Product / UX track
Phase 13.17 human acceptance + corrections

        || PARALLEL WITH ||

Platform evolution
Wave 2 → Wave 3 → Wave 4

        || PARALLEL WITH ||

Human-like organization architecture
Wave 5A / 5B foundations → 5C / 5D pilots → 5E / 5F
```

Parallel progress does not allow evidence bypass:

- unresolved Phase 13.17 findings remain unresolved until corrected/retested/dispositioned;
- a docs checkpoint is not a runtime PASS;
- architecture work may proceed without pretending product acceptance is complete.

Phase 14 remains a scale programme rather than the only place platform evolution may occur.

---

## 17. Standard candidate-evaluation contract

Every runtime candidate still requires evaluation of:

### Domain correctness

- preserves AIOS semantics;
- provider state cannot become domain truth by accident;
- provider output remains distinguishable.

### Safety / governance

- scoped context;
- no unauthorized mutation;
- proposal/approval handling;
- evidence/review boundaries;
- failure cannot silently become success.

### Technical quality

- accuracy / recall where relevant;
- latency / throughput;
- determinism;
- failure behavior;
- observability;
- resource cost;
- reproducibility.

### Operational fit

- deployment;
- self-hosting;
- backup/recovery;
- data residency;
- tenancy;
- secrets/network/filesystem access;
- monitoring/supportability.

### Learning/data-use fit

- processing purpose;
- allowed data-use categories;
- minimum necessary;
- special-category handling;
- retention/deletion;
- training/evaluation lineage.

### Exit cost

- removable without rewriting core domain semantics;
- external IDs remain mappings;
- rebuild/export path exists;
- alternatives can compete behind AIOS-owned contracts.

---

## 18. Current decision

1. **Phase 13.17 remains IN PROGRESS / PAUSED** as owner-led human acceptance. It is not independent third-party validation.
2. **Platform evolution continues in parallel.** It does not wait for a tiny Coworker pilot or full Phase 13 closure before architecture/foundation work may proceed.
3. **Wave 1 is complete at pilot level;** its technologies are now `PILOT COMPLETE / TRIAL-ELIGIBLE`, not ambiguously `ADOPT / EARLY PILOT`.
4. **Wave 2 is in progress** with Docling pilot started and Presidio queued.
5. **Munder Difflin and OpenWorker remain complementary A+ references** under AIOS-owned semantics.
6. **Wave 5A high-autonomy control plane is now first-class architecture.**
7. Consequential actions—email sending, eligibility changes, evidence certification, application submission, VerifiedRule changes, and client-status changes—are **proposal-first human collaboration workflows**.
8. Human reviewers may approve, modify, return or reject proposals at the lowest appropriate role surface.
9. The architecture does not install Munder Difflin/OpenWorker or add new runtime dependencies by documentation alone.

Long-term flywheel:

> **Work → Outcomes → Corrections → Intelligence → Evaluation → Training/Optimization where permitted → Better AIOS → Better Work.**
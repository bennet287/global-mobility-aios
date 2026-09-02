# Global Mobility AIOS — Technology Radar V1.1

**Status:** ACTIVE CANONICAL V1.1 — platform evolution / evaluation / controlled implementation track  
**Date:** 2026-08-19  
**Accepted product baseline:** Phase 13.16.10 COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active product slice:** Phase 13.17 — owner-led human acceptance, IN PROGRESS / PAUSED BY EVALUATOR  
**Platform evolution:** continues in parallel through bounded implementation slices  
**Current Radar runtime state:** Wave 1 complete; Wave 2 in progress with Docling pilot started  
**Canonical organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md)  
**Architecture predecessor:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md)  
**Historical Radar predecessor:** [TECHNOLOGY_RADAR_V1.md](TECHNOLOGY_RADAR_V1.md)

Technology Radar V1.1 identifies external/open-source technologies and architecture patterns that can materially strengthen Global Mobility AIOS without allowing third-party frameworks to define AIOS domain semantics, organizational authority, evidence truth, legal status, certification/publication state, or business outcomes.

The Radar is not a dependency manifest. Inclusion means a capability/technology is strategically relevant. Runtime adoption still requires a bounded implementation slice, benchmark or acceptance contract, security/data-flow review, rollback, concurrency behavior, mutation-path review, and exit strategy.

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
AIOS Context / Canonicalization / Command / Execution layers
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

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

### 1.3 Five hard canonicalization invariants

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

Useful promotion paths remain allowed through AIOS-owned validation/canonicalization.

### 1.4 Five non-negotiable runtime rules

1. **Canonicalization cannot be LLM-only for material state.** LLM interpretation may assist, but final classification of `ExecutiveDecision`, `VerifiedRule`, Evidence certification, publication, eligibility transitions, client status, application submission, or external action must resolve through typed AIOS schemas and deterministic validators.
2. **Command Gateway is the only autonomous-agent production mutation path.** No Munder/OpenWorker/model/MCP/tool process receives arbitrary production-domain write access.
3. **Material writes use optimistic concurrency / expected-version checks.** Stale proposals fail closed and must rebase/re-evaluate.
4. **Learning preserves outcome labels.** Proposed/accepted/modified/rejected/contradicted/stale/superseded/human-corrected/failed/rolled-back states remain distinguishable.
5. **Rollback/compensation is first-class.** A3/A4 and consequential execution must declare reversibility/side-effect semantics where relevant.

---

## 2. Fit and adoption state are separate

V1.1 separates **strategic fit** from **adoption state**.

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

Neither may bypass the Command Gateway for canonical production mutations.

---

## 5. AIOS high-autonomy runtime control plane

### 5.1 Context Broker

Provides a provenance-aware `ContextBundle` scoped by:

- tenant;
- actor/position;
- Mission/case purpose;
- minimum necessary;
- sensitivity;
- tool/provider recipient;
- jurisdiction;
- data-use constraints.

Target fields include:

```text
context_bundle_id
mission_id
case_id?
generated_at
context_version
facts[] + support/provenance
evidence[]
verified_rules[]
source_snapshots[]
unknowns[]
contradictions[]
agent capability/authority context
context_hash
```

`AgentRun` should bind to the context bundle/hash and model/prompt/program/role-card/tool/connector versions for reproducibility.

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

**Material final classification is never LLM-only.**

For Decision/VerifiedRule/certification/publication/eligibility/client-status/application/external-action state, the final classification must validate through typed AIOS schemas and deterministic rules.

### 5.3 Command Gateway

Authoritative agent-originated mutations occur through typed AIOS commands with checks for:

- identity;
- deterministic authority;
- capability scope;
- tenant/case scope;
- evidence sufficiency;
- contradictions;
- state/version preconditions;
- required human/professional/source/certification gate;
- idempotency;
- transaction safety;
- reversibility/compensation metadata where relevant.

No external runtime may obtain arbitrary production-domain DB writes.

### 5.4 Optimistic concurrency

Material commands should carry `expected_version` / expected state / precondition hash as appropriate.

```text
Agent A reads V14
Agent B reads V14

A commits accepted change
→ V15

B submits expected_version=14
actual_version=15
→ STALE
→ no overwrite
→ refresh ContextBundle
→ re-evaluate / rebase
```

Concurrency safety is a first-class autonomous-organization invariant.

### 5.5 Execution Sandbox

Powerful runtimes use bounded:

- filesystem;
- network;
- secrets;
- shell;
- connectors;
- cost/token budget;
- execution time;
- production-data mutation paths.

Production mutation remains Command-Gateway-only.

### 5.6 Rollback / compensation

A3/A4 and consequential execution should declare when relevant:

```text
reversible
compensation_command
previous_version
side_effects
external_side_effects
rollback_deadline
rollback_preconditions
```

A4 is only valid where rollback/compensation is meaningful.

Government submission or delivered email is not treated as truly reversible merely because it is audited.

---

## 6. Consequential Action Proposal

The product should let agents **prepare almost all of the work** while humans retain efficient review/modification for consequential actions.

Proposal lifecycle:

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
FINAL VERSION / CONCURRENCY CHECK
  ↓
EXECUTE
  ↓
VERIFY RESULT
  ↓
COMPLETED / FAILED / PARTIAL / COMPENSATED
```

Explicit proposal-first action classes:

1. **send email / external communication**;
2. **change eligibility**;
3. **certify evidence**;
4. **submit application**;
5. **change / publish VerifiedRule**;
6. **change client status**.

The agent may draft, assemble evidence, preflight, explain impact, and recommend the exact action. The appropriate human reviews/modifies/approves. Review occurs at the lowest appropriate surface, not automatically in Board Room.

Human modifications should preserve proposal-to-final lineage.

A later, separately governed policy may permit direct execution for a narrowly defined low-risk action class after sufficient acceptance evidence; no agent self-grants that autonomy.

---

## 7. Capability-specific autonomy

Autonomy belongs to **capability + context**, not simply an agent name.

```text
A0  prohibited
A1  human execution required
A2  human approval required
A3  autonomous with mandatory post-review
A4  autonomous with monitoring / real rollback or compensation
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
prepare external action    A4
send client email          A2
submit authority form      A2/A1
```

Performance may create an `AutonomyChangeRecommendation`. Authority/autonomy expansion itself remains governed.

Future `AutonomyEvidenceProfile` should measure executions, acceptance, modification, rejection, contradiction, material error, grounding, SLA and rollback/incident rates.

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

This becomes a machine-readable epistemology, not just documentation.

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
- accepted prior state;
- current aggregate version/preconditions.

Unsupported/conflicted outputs normally return to the agent for self-correction before unnecessary human escalation.

### 8.4 Recovery

```text
self-correct
  ↓
peer review where useful
  ↓
specialist review
  ↓
human where required
```

Peer agreement is a signal, not truth. High-risk work should combine independent evidence retrieval and deterministic validation with reasoning review.

---

## 9. Natural communication and tiered OrganizationActivity

Canonical relationship:

```text
AgentMessage ⊂ OrganizationActivity
```

Routine organizational conversation may be legitimate Activity without becoming formal authority-bearing state.

Canonical activity classes:

```text
CONVERSATIONAL
COLLABORATIVE
OPERATIONAL
MATERIAL
AUTHORITY
```

Suggested runtime treatment:

- **CONVERSATIONAL** — high-volume, human-inspectable, policy-governed compression/summarization after retention window where permitted.
- **COLLABORATIVE** — handoffs/peer review/shared findings, structured for collaboration analytics.
- **OPERATIONAL** — durable execution/work history.
- **MATERIAL** — long-term durable, strongly indexed, Cockpit-compressed where appropriate.
- **AUTHORITY** — highest durability / immutable-tamper-evident target linked to exact approved state and AuditLog.

Conversation remains inspectable to permitted humans. Compression must not erase meaningful reconstructability required by policy.

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
- blocker age;
- retry/recovery.

### KPI

Measure delivery, quality, collaboration, economics, human effort, grounding, proposal quality, stale-proposal rate, contradiction rate, rollback rate and governance.

**Mission/team result is the primary performance unit.** Individual metrics are diagnostic.

### OKR

Strategic objectives above operational KPIs.

### Definition of Done

A Mission is not finished merely because an agent says so. Material work should meet explicit deliverable, evidence, review, SLA, proposal/action, result, concurrency and rollback/exception criteria.

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

Learning/evaluation records should preserve labels such as:

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

The platform may build operational/evaluation capability in parallel with the product. Training/reuse involving real client data requires the applicable data-use policy, purpose, legal/compliance treatment, sensitivity controls, retention/deletion, tenant policy, lineage and legal/privacy review.

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
- high-autonomy runtime-control architecture.

### Wave 1 — Quality Foundation — COMPLETE

- Promptfoo bounded pilot complete;
- OpenTelemetry bounded pilot complete;
- ClamAV bounded pilot complete.

These are **PILOT COMPLETE / TRIAL-ELIGIBLE**, not automatically production-standard `ADOPT` merely because the pilot passed.

### Wave 2 — Document & Privacy Intelligence — IN PROGRESS

Current:

- Docling pilot in progress;
- Presidio queued;
- OCR specialists are gap-triggered only after Docling/current-stack measurement.

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

### Wave 5A — Runtime Control Plane / Immune System

- deterministic Canonicalization Gateway contracts;
- Command Gateway as sole autonomous-agent production mutation path;
- provenance-aware Context Broker / ContextBundle;
- expected-version / optimistic concurrency;
- idempotency / preconditions;
- ConsequentialActionProposal;
- human modify/approve/reject lifecycle;
- evidence sufficiency;
- contradiction detection;
- capability-scoped autonomy;
- sandbox;
- rollback/compensation metadata;
- labeled LearningRecord outcome model.

### Wave 5B — Organization Semantics

- Mission;
- AgentConversation;
- tiered conversational/collaborative OrganizationActivity;
- Dynamic Squad;
- Capability Registry;
- memory scopes;
- AgentRelationship;
- SLA;
- KPI/OKR;
- Definition of Done.

5A and 5B may progress as coordinated parallel slices, but deep external-agent mutation depends on the relevant 5A controls existing.

### Wave 5C — Munder Difflin Agent Organization Fabric

Controlled research/pilot behind AIOS-owned contracts.

### Wave 5D — Execution Broker + OpenWorker / Coworker

Controlled research/pilot for files/tools/MCP/connectors/finished work and proposal-gated external actions.

### Wave 5E — Live Organization / Cockpit

Premium AIOS-native visualization and direct organizational interaction.

### Wave 5F — Organizational Learning & Optimization

Improve routing, collaboration, SLA, team composition, runtime/model choice, proposal quality, contradiction recovery, autonomy recommendations and capacity decisions from permitted labeled outcomes.

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

Every runtime candidate must be evaluated not only for capability, but for its compatibility with the AIOS control plane.

### Domain correctness

- preserves AIOS semantics;
- provider state cannot become domain truth by accident;
- provider output remains distinguishable;
- material canonicalization can terminate in typed/deterministic AIOS contracts.

### Mutation safety

- provider can operate without arbitrary production DB writes;
- all autonomous mutations can route through Command Gateway;
- expected-version/precondition information can be preserved;
- idempotency can be enforced;
- provider-native retry cannot duplicate consequential effects.

### Rollback / consequence

- side effects can be classified;
- reversible actions expose compensation;
- irreversible actions can be forced into stricter autonomy/proposal modes;
- exact approved payload/result can be preserved.

### Safety / governance

- scoped context;
- no unauthorized mutation;
- proposal/approval handling;
- evidence/review boundaries;
- failure cannot silently become success;
- provider event logs do not automatically become canonical Activity.

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
- training/evaluation lineage;
- outcome labels preserved separately from raw proposal text.

### Exit cost

- removable without rewriting core domain semantics;
- external IDs remain mappings;
- rebuild/export path exists;
- alternatives can compete behind AIOS-owned contracts.

---

## 18. Runtime acceptance contract for Wave 5A+

### Canonicalization

- unstructured message cannot directly become `ExecutiveDecision`;
- memory cannot directly become Evidence/VerifiedRule;
- provider event does not automatically become canonical Activity;
- material final classification uses typed AIOS schema + deterministic validation.

### Mutation

- agent-originated production write outside Command Gateway fails;
- arbitrary provider/MCP DB mutation is unavailable;
- required human gate cannot be bypassed;
- duplicate consequential execution is prevented by idempotency.

### Concurrency

- stale expected version rejects;
- accepted V15 is never silently overwritten by proposal based on V14;
- stale proposals re-evaluate against refreshed context.

### Rollback

- reversible actions declare compensation;
- A4 requires meaningful rollback/compensation;
- irreversible side effects remain stricter-autonomy actions.

### Learning

- rejected/modified/contradicted/stale outcomes retain labels;
- canonical accepted state remains distinguishable from proposal text;
- context/model/program/tool versions remain reconstructable.

### Activity

- conversational messages are legitimate Activity;
- `activity_class` is explicit;
- AUTHORITY activity receives highest durability/tamper-evident treatment target;
- provider logs remain non-authoritative until normalized.

---

## 19. Current decision

1. **Phase 13.17 remains IN PROGRESS / PAUSED** as owner-led human acceptance. It is not independent third-party validation.
2. **Platform evolution continues in parallel.** It does not wait for a tiny Coworker pilot or full Phase 13 closure before architecture/foundation work may proceed.
3. **Wave 1 is complete at pilot level;** its technologies are now `PILOT COMPLETE / TRIAL-ELIGIBLE`, not ambiguously `ADOPT / EARLY PILOT`.
4. **Wave 2 is in progress** with Docling pilot started and Presidio queued.
5. **Munder Difflin and OpenWorker remain complementary A+ references** under AIOS-owned semantics.
6. **Wave 5A Runtime Control Plane / Immune System is first-class architecture.**
7. Material canonicalization must end in typed/deterministic AIOS rules, not an unconstrained LLM classification.
8. Command Gateway is the sole autonomous-agent production mutation path.
9. Material writes use optimistic concurrency/version checks.
10. Consequential actions—email sending, eligibility changes, evidence certification, application submission, VerifiedRule changes, and client-status changes—remain **proposal-first human collaboration workflows**.
11. Human reviewers may approve, modify, return or reject proposals at the lowest appropriate role surface.
12. Rollback/compensation and labeled learning outcomes are non-negotiable runtime requirements.
13. The architecture does not install Munder Difflin/OpenWorker or add new runtime dependencies by documentation alone.

Long-term flywheel:

> **Work → Outcomes → Corrections → Intelligence → Evaluation → Training/Optimization where permitted → Better AIOS → Better Work.**

Defining runtime principle:

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

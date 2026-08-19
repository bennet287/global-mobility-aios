# Global Mobility AIOS — Active Changelog

This is the current changelog from the post-`f0688a8` baseline onward. The complete historical changelog through the sealed Phase 13.16.7 baseline remains preserved at [archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md](archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md). Git history preserves exact previous versions of this active changelog.

---

## 2026-08-19 — Human-Like High-Autonomy Architecture V1.1 — OWNER-APPROVED CANONICAL DOCS CHECKPOINT / PUSHED

### Owner decision

The project will **not pause architecture/platform evolution until a tiny Coworker workflow or full Phase 13.17 acceptance is completed first**.

Global Mobility AIOS will continue through coordinated parallel tracks:

1. product/human acceptance and bounded UX correction;
2. Technology Radar/platform evolution;
3. human-like organization/high-autonomy control architecture.

Parallel progress does not weaken acceptance discipline. Every implementation slice still requires bounded scope, safety/evidence/authority boundaries, testing appropriate to the change, rollback/exit thinking, ROADMAP/CHANGELOG synchronization, and truthful PASS claims.

### New canonical architecture

Created:

- `docs/HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md`

Commit:

- `2c2b0fd4c8f5579f73f582fe5ea317bef52f864c` — `docs: define controlled high-autonomy organization architecture v1.1`

V1.1 supersedes the previous V1 document for active architecture direction while preserving V1 as historical architecture evidence.

Core target:

> **Human in interaction. Machine-like in reliability.**

New permanent control principle:

> **Broad cognition. Scoped context. Narrow mutation. Deterministic authority. Reversible execution.**

Additional permanent principles:

- natural interaction, deterministic accountability;
- activity is broad; authority is narrow;
- team outcomes over agent competition;
- results matter more than provider competition;
- agents may be creative in cognition; AIOS must be conservative in truth;
- consequential actions are proposal-first unless a separately accepted bounded autonomy policy permits direct execution;
- autonomy is capability-specific and never self-granted.

### Updated architecture stack

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
AIOS Canonicalization Gateway
  ↓
AIOS Command Gateway
  ↓
Authority + Grounding + Consistency checks
  ↓
Internal bounded action
    OR
Consequential Action Proposal
  ↓
appropriate human approve / modify / return / reject
  ↓
atomic/versioned governed execution
  ↓
OrganizationActivity + Audit
  ↓
Learning & Quality
```

### High-autonomy control plane

V1.1 makes the following first-class AIOS architecture components:

- **Context Broker** — task/tenant/purpose/sensitivity-scoped `ContextBundle` rather than unrestricted sensitive-data access;
- **Canonicalization Gateway** — interprets model/memory/provider/tool events into AIOS meaning;
- **Command Gateway** — typed authoritative mutations with identity, authority, evidence, contradiction, version/precondition, gate and transaction checks;
- **ConsequentialActionProposal** — human collaboration object for important actions;
- **capability-specific autonomy** — autonomy belongs to capability + context rather than agent identity;
- **execution sandbox** — scoped filesystem/network/secrets/shell/connectors/cost/time/mutation access;
- **evidence sufficiency + contradiction detection** — model self-confidence is not permission;
- **atomic/versioned/reversible state** — bad/rejected proposals do not corrupt prior accepted state.

### Five hard canonicalization invariants retained

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

Useful promotion paths remain allowed:

```text
conversation/message
→ intent/candidate
→ AIOS validation
→ proposal/command
→ governed state
```

```text
memory
→ hypothesis/retrieval hint
→ governed source/evidence lookup
→ candidate
→ review/validation
→ Evidence / VerifiedRule where requirements are met
```

### AgentMessage remains OrganizationActivity

The human-like organization principle remains:

```text
AgentMessage ⊂ OrganizationActivity
```

Natural questions, clarification, disagreement, warnings, handoffs, peer review, acknowledgement and coordination are legitimate organizational activity and do not require a WorkItem/human gate merely to exist.

The strict boundary is that conversation does not silently create legal/evidence/authority state.

### Consequential actions — proposal-first human collaboration

The Owner approved a proposal-first architecture for the following important agent-helpful actions:

1. send email / external communication;
2. change eligibility;
3. certify evidence;
4. submit application;
5. change/publish VerifiedRule;
6. change client status.

Agents should do as much useful preparation as possible before human involvement.

Typical lifecycle:

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
```

For example, an agent may prepare an email with recipient/body/attachments and case rationale; the human modifies or approves the finished proposal instead of drafting from scratch.

An eligibility proposal should show current vs proposed state, evidence/rules, missing facts, contradictions and downstream impact.

An application-submission proposal should show the exact payload/attachments/preflight state before the external side effect.

A VerifiedRule proposal requires official-source/snapshot/effective-date/supersession grounding and the applicable source/certification review before canonical publication/change.

### Human review remains distributed

Proposal review goes to the **lowest appropriate human role**, not automatically Owner/Board:

```text
Mobility User
→ personal facts / choices

Professional / Operator
→ case / eligibility / evidence / client communication / application work

Qualified source/certification reviewer
→ required rule/evidence certification

Department Lead / Executive
→ delegated organizational decisions

Human Owner / Board
→ reserved strategic / organization-wide authority
```

The Owner can inspect/intervene broadly, but Board Room remains a reserved-authority module.

### Trust / anti-hallucination architecture

V1.1 formalizes a trust ladder:

```text
L0 model speculation
L1 conversation / memory
L2 retrieved information
L3 source snapshot
L4 governed Evidence
L5 reviewed candidate
L6 VerifiedRule / certified governed fact
L7 governed case conclusion
L8 approved authority-bearing action
```

Hard constraints:

```text
L1 cannot jump directly to L6
L2 cannot jump directly to L7
L6 does not automatically create L8
```

Material agent results should expose support state, evidence/source/VerifiedRule references, assumptions, uncertainty, missing facts and contradictions.

Model self-confidence is metadata, not a mutation/authority mechanism.

### Contradiction / recovery model

Before important state changes, AIOS should compare proposals against current Evidence, VerifiedRules, source authority/effective dates, supersession, case facts, pathway/version, ExecutiveDecisions and prior accepted state.

Default recovery:

```text
unsupported/conflicted
  ↓
self-correct
  ↓
peer review where useful
  ↓
specialist review
  ↓
human only where still required
```

Peer agreement is useful but is not proof; high-risk work should also use deterministic checks and independent evidence retrieval/review.

### Capability autonomy model

Suggested scale:

```text
A0 prohibited
A1 human execution required
A2 human approval required
A3 autonomous + mandatory post-review
A4 autonomous + monitoring / rollback
A5 fully autonomous bounded internal operation
```

Autonomy attaches to capability + context.

Performance may produce an autonomy-change recommendation; an agent cannot promote its own authority/autonomy.

### Munder Difflin + OpenWorker remain complementary

**Munder Difflin (`chaitanyagiri/munder-difflin`)** remains the A+ strategic reference for the Agent Organization Fabric: identities, messages/mailboxes, memory, orchestration, scheduling, budgets, circuit breaking, skills and Live Organization concepts.

**OpenWorker (`andrewyng/openworker`)** remains the A+ strategic reference for Coworker/finished-work execution: files/artifacts, tools/terminal, MCP, connectors, schedules, external actions, approval inbox and model portability.

The architecture does not force an artificial winner when the technologies provide complementary capability.

**AIOS Execution Broker** owns composition and routing based on Mission result quality, SLA, evidence needs, workload, human-review needs, cost, privacy/data-use, provider health and fallback.

### Technology Radar classification cleanup

Updated:

- `docs/TECHNOLOGY_RADAR_V1_1.md`

Commit:

- `c90361c3cf077c54e132bca575589ecf4ea2656a` — `docs: align Technology Radar with controlled high-autonomy architecture`

Strategic fit and adoption state are now separate.

Canonical adoption lifecycle:

```text
REFERENCE → RESEARCH → BENCHMARK → PILOT → TRIAL → ADOPT
```

Current key state:

- Promptfoo — A+ / PILOT COMPLETE / TRIAL-ELIGIBLE;
- OpenTelemetry — A+ / PILOT COMPLETE / TRIAL-ELIGIBLE;
- ClamAV — A+ / PILOT COMPLETE / TRIAL-ELIGIBLE;
- Docling — A+ / PILOT IN PROGRESS;
- Presidio — A+ / QUEUED PILOT;
- urlwatch — A+ / QUEUED PILOT;
- Munder Difflin — A+ / REFERENCE / CONTROLLED RESEARCH;
- OpenWorker — A+ / REFERENCE / CONTROLLED RESEARCH;
- Temporal/OpenFGA — deferred pilot;
- pgvector/Qdrant — benchmark.

This removes the ambiguous `ADOPT / EARLY PILOT` classification.

### Docling / OCR simplification

PaddleOCR / Unlimited-OCR are now **gap-triggered benchmarks**, not automatic next dependencies.

Sequence:

```text
measure Docling + current fallback stack
→ identify actual document/OCR gaps
→ benchmark specialist OCR only against those gaps
→ adopt only when measurable value exists
```

### ROADMAP synchronization

Updated:

- `docs/ROADMAP.md`

Commit:

- `b00856546a287ec605bd74073c6383c8482b7ca3` — `docs: align roadmap with parallel high-autonomy architecture track`

Roadmap V11.3 now explicitly states:

- Phase 13.17 remains IN PROGRESS / PAUSED;
- product/human acceptance and architecture/platform work proceed in parallel;
- architecture progress does not clear unresolved Phase 13.17 findings;
- Wave 1 is pilot-complete, not automatically ADOPT;
- Wave 2 is in progress;
- high-autonomy architecture is a first-class Track C;
- Wave 5A = High-Autonomy Control Plane;
- Wave 5B = Organization Semantics;
- Wave 5C = Munder Agent Organization Fabric;
- Wave 5D = Execution Broker + OpenWorker/Coworker;
- Wave 5E = Live Organization;
- Wave 5F = Organizational Learning & Optimization;
- 5A/5B may progress as coordinated parallel slices;
- Wave 5 architecture does not need to wait for complete Phase 13.17 closure.

### Third-party principles synchronization

Updated:

- `docs/THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md`

Commit:

- `84920366b629ec256e27184f0ba09753fed35b13` — `docs: harden provider boundaries for proposal-first agent execution`

The principles now allow third-party runtimes to execute/draft/propose broadly while explicitly protecting AIOS ownership of canonicalization, typed commands, proposal approval/modification state, Evidence, VerifiedRule, ExecutiveDecision, canonical Activity and business outcomes.

### Learning & Quality

The architecture retains three distinct layers:

1. Operational Intelligence;
2. Evaluation & Quality;
3. Training & Optimization.

Architecture/quality work may progress in parallel. Real-client-data training/reuse remains subject to explicit processing purpose, legal/compliance treatment, sensitivity, tenant/data-use, retention/deletion and lineage controls.

Potential learning signals include corrections, proposal modifications/rejections, approvals, SLA misses, routing failures, peer disagreements, contradiction recoveries and provider/runtime outcomes.

### Boundary / acceptance truth

This V1.1 architecture synchronization is **documentation-only**.

It does not:

- install Munder Difflin;
- install OpenWorker;
- add Context Broker / Gateway / proposal runtime code yet;
- create new tables/migrations yet;
- change backend authorization yet;
- mutate the preserved database;
- change frontend runtime behavior;
- mark Phase 13.17 PASS;
- resolve O-/P- human findings merely through documentation.

No complete API regression, Next.js build, browser acceptance, database checker or local repository seal was rerun by these direct GitHub documentation writes.

Latest accepted runtime evidence remains the Docling pilot checkpoint below and is carried forward, **not represented as rerun**.

No GitHub CI PASS is claimed by this docs checkpoint unless a real attached status exists.

---

## 2026-08-19 — Human-Like Agent Organization Architecture V1 — CANONICAL DOCS CHECKPOINT / PUSHED

V1 established the initial human-like organization architecture:

- Human in interaction / machine-like reliability;
- Munder Difflin + OpenWorker complementary A+ direction;
- AIOS Execution Broker;
- Mission / Dynamic Squad;
- AgentConversation;
- `AgentMessage ⊂ OrganizationActivity`;
- memory scopes / relationships;
- Capability Registry;
- SLA/KPI/OKR/Definition of Done;
- progressive intervention;
- Live Organization;
- organization learning.

V1.1 above supersedes V1 for active implementation direction by adding the high-autonomy control plane, proposal-first consequential actions, trust ladder, contradiction/self-correction architecture, capability-scoped autonomy/sandbox and explicit parallel-delivery decision.

V1 architecture commit:

- `f7216c523c3de96a15eeb7c8d6698b62b52934e4`

---

## 2026-08-19 — Technology Radar V1.1 Wave 2 Docling pilot STARTED

- Added bounded optional disabled-by-default `docling_adapter.py`.
- Integrated normalization into the existing document-intelligence extraction flow with safe fallback.
- Added `DOCLING_ENABLED` and AI-only dependency placement.
- Preserved the rule that normalization is not authenticity, legal sufficiency, evidence validity or authority.

Acceptance:

- Docling adapter **6/6 PASS**;
- document intelligence **5/5 PASS**;
- complete API **873 passed / 5 skipped / 0 failed**;
- repository/release/Docker/database/schema checks **PASS**;
- Next.js **41/41 PASS**;
- design foundation **28/28 PASS**;
- preserved `gmai.db` unchanged.

Presidio remains queued next. Specialist OCR is now gap-triggered by actual Docling/current-stack measurement.

---

## 2026-08-19 — Technology Radar V1.1 Wave 1 ClamAV pilot COMPLETE / PASS

- Added optional disabled-by-default upload malware scanning.
- Infected uploads reject before storage.
- Clean scan remains engineering safety signal, not evidence validity.

Acceptance:

- malware-scan **11/11 PASS**;
- document-upload **2/2 PASS**;
- API **867 passed / 5 skipped / 0 failed**;
- repository/release/Docker/database/schema checks **PASS**;
- Next.js **41/41 PASS**;
- design foundation **28/28 PASS**;
- preserved database unchanged.

Wave 1 became complete at pilot level.

---

## 2026-08-19 — Technology Radar V1.1 Wave 1 OpenTelemetry pilot COMPLETE / PASS

- Added optional disabled-by-default FastAPI/OpenTelemetry instrumentation / OTLP export.
- Missing packages/configuration degrade safely.
- OpenTelemetry remains engineering telemetry, not semantic Activity/Audit/Evidence/authority.

Acceptance:

- telemetry **3/3 PASS** with environment-dependent SDK skip recorded;
- API **856 passed / 5 skipped / 0 failed**;
- repository/release/Docker/database/schema checks **PASS**;
- Next.js **41/41 PASS**;
- design foundation **28/28 PASS**;
- preserved database unchanged.

---

## 2026-08-19 — Technology Radar V1.1 Wave 1 Promptfoo pilot COMPLETE / PASS

- Added deterministic role-card safety evaluation.
- Added matching pytest invariants independent of Promptfoo installation.
- Promptfoo remains evaluation tooling, never production authority.

Acceptance:

- role-card safety **42/42 PASS**;
- Promptfoo **40/40 PASS**;
- API **853 passed / 5 skipped / 0 failed**;
- repository/release/Docker/database/schema checks **PASS**;
- Next.js **41/41 PASS**;
- design foundation **28/28 PASS**;
- preserved database unchanged.

---

## 2026-08-18 — Phase 13.17 owner-led human acceptance CHECKPOINT / PAUSED

- Began genuine human-use acceptance against sealed 13.16.10.
- Evaluator is product Owner; therefore owner-led, not independent third-party validation.
- Recorded Owner findings O-01 through O-12 and Professional P-01/P-02.
- No finding was fixed merely because intended semantics were later explained.
- Paused after Professional Task 1; resume point is Professional Task 2.

Checkpoint:

- `docs/PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md`
- commit `24aa74109c749a2752c08eaca007917978eb1bcd`

Phase 13.17 remains IN PROGRESS / PAUSED.

---

## 2026-08-18 — Phase 13.16.10 COMPLETE / PASS

- responsive/accessibility/integrated role experience accepted after bounded mobile corrections;
- design foundation **28/28 PASS**;
- request/auth **4/4 PASS**;
- Next.js **41/41 PASS**;
- API **811 passed / 5 skipped / 0 failed** carried forward for frontend-only boundary;
- browser/mobile/keyboard/Portal acceptance PASS;
- preserved `gmai.db` unchanged.

Seal:

- `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`

---

## 2026-08-18 — Phase 13.16.9 COMPLETE / PASS

- shared evidence/provenance presentation grammar across four evidence-heavy Professional surfaces;
- context-alignment and certification/publication authority preserved;
- design **26/26 PASS**;
- request/auth **4/4 PASS**;
- Next.js **41/41 PASS**;
- API **811 passed / 5 skipped / 0 failed** carried forward;
- human visual review PASS;
- automated semantic verifier false-negative / not claimed PASS;
- preserved database unchanged.

Seal:

- `c97b2189e94a6753ab902dd192bbd5b2e41073d0`

---

## 2026-08-18 — Phase 13.16.8 COMPLETE / PASS

- governed Professional/Operator workspace and case reading order accepted;
- context-aligned evidence composition preserved;
- design **25/25 PASS**;
- request/auth **4/4 PASS**;
- Next.js **41/41 PASS**;
- API **811 passed / 5 skipped / 0 failed**;
- browser/runtime acceptance PASS;
- preserved database unchanged.

Seal:

- `2dc3637820f6fdbb75628e2632a07bdbe336aa19`

---

## 2026-08-18 — Technology Radar V1.1 original platform-evolution checkpoint

- established active Radar V1.1 / provider-neutral architecture;
- added OpenWorker initial Coworker reference;
- added Internal Learning & Quality, correction-learning and lineage direction;
- preserved compliance-aware lawful-learning boundaries;
- established implementation waves without automatic adoption.

The V1 and V1.1 human-like organization checkpoints above extend this architecture without weakening AIOS Semantic Sovereignty.
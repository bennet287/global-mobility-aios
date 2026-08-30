# Global Mobility AIOS — Master Necessity-Driven Roadmap

**Roadmap generation:** V12.34 — Technology Radar V1.3.6 aggressive R3 execution queue; K.1 COMPLETE / PASS / SEALED; L Live Organization IMPLEMENTED / ACCEPTANCE PENDING
**Date:** 2026-08-30
**Active development branch:** `roadmap/global-mobility-aios-v12`
**V12 fork origin:** `dd2f2cd6e9e47179b1fd744ba3f56daf7c787449`
**Frozen V11 reference branch:** `roadmap/global-mobility-aios-v11`
**Final V11 documentation-cleanup head:** `ac130deaafa7aa44068e9459facbda2b4df327d6`
**Accepted product baseline:** Phase 13.16.10 — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`
**Active human-acceptance stream:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR
**Active organization architecture:** `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md` + `HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`
**Frontend / UX programme:** `AIOS_FRONTEND_DESIGN_UX_PROGRAMME_V1.md`
**Enterprise integration architecture:** `ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md`
**Active Technology Radar:** `TECHNOLOGY_RADAR_V1_3_6.md`
**Integration & Capability Radar:** `AIOS_INTEGRATION_CAPABILITY_RADAR_V1.md`
**Munder donor programme:** `MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`
**Last sealed organization/runtime checkpoint:** K.1 — COMPLETE / PASS / SEALED on technical candidate `9a7df63511e45f6a0945ae933929522314a04ec3`
**K.1 canonical proof:** GitHub Actions Production Proof `32582805820` — 4/4 PASS; Repository Policy `32582805835`; Woodpecker push #17 and PR #18 — 4/4 PASS
**Latest fully green L technical checkpoint:** `34597abf24a348a28b25e15dccb1a22fa35b3998` — Woodpecker PR Pipeline #77 4/4 PASS; eight commits after fresh-retrieval checkpoint `a85384e6...`; historical exact-checkpoint proof only
**Accepted L live-runtime evidence:** `V1_3_L_LIVE_RUNTIME_ACCEPTANCE_EVIDENCE_2026-08-30.md` — real Gemini success, guarded fresh retrieval, real failure, owner materialization and exact replay; professional review + final exact-current-head proof remain
**Supplemental L domain corroboration:** `V1_3_L_AI_DOMAIN_CORROBORATION.md` — blind fresh-source multi-provider harness implemented; no corroboration result or professional-review substitution claimed
**Runtime-evidence documentation baseline:** `eb890463a36e0b3c9a615bb2255c41730cd80646` — source head before this V12.30 documentation-only receipt; final exact-current-head proof remains pending
**Historical 2026-08-25 pre-reconciliation source head:** `38f028f8c3123fdb5678a2ad1e9ff80ddeec35d8`
**Current product milestone:** L — Live Organization
**Forward CI direction:** self-hosted Woodpecker; historical GitHub Actions proofs remain historical evidence
**Code migration head:** `0081_capability_autonomy_evidence_evaluation_policy`

<!-- CURRENT_MIGRATION_HEAD: 0081_capability_autonomy_evidence_evaluation_policy -->

> **Product necessity pulls technology into the project. Technology does not push the product around.**

> **Nothing necessary gets forgotten, but nothing gets implemented merely because it appears in a Radar, donor programme or architecture document.**

> **Governance before unrestricted execution. Transparency before increased autonomy. Production proof before acceptance.**

---

## 1. Purpose and roadmap authority

`ROADMAP.md` is the master orchestration document for Global Mobility AIOS.

It answers:

```text
WHAT is the next necessary product capability?
WHY is it necessary now?
WHAT dependencies must be satisfied?
WHICH supporting workstreams are allowed to advance?
WHAT proof closes the milestone?
WHAT becomes primary only after acceptance?
```

Detailed documents remain canonical for their own domains, but they do not independently determine implementation order.

```text
ROADMAP.md                         MASTER — WHAT + WHEN + WHY
│
├─ Architecture documents         HOW SYSTEM BOUNDARIES ARE STRUCTURED
├─ Frontend / UX Programme        HOW HUMAN EXPERIENCE EVOLVES
├─ Technology Radar               CANDIDATE TECHNOLOGY + ADOPTION EVIDENCE
├─ Integration Radar              EXTERNAL CAPABILITY DECISIONS
├─ Donor programmes               SAFE REUSE / ADAPT / REIMPLEMENT RULES
├─ Acceptance records             PROOF OF COMPLETION
└─ CHANGELOG                      WHAT ACTUALLY CHANGED
```

If a child document appears to imply an implementation order that conflicts with this roadmap, this roadmap controls scheduling until the conflict is explicitly reconciled.

---

## 2. Governing necessity sequence

Every substantive capability follows this sequence:

```text
NEED
 ↓
PRODUCT CAPABILITY
 ↓
ARCHITECTURAL GAP
 ↓
BUILD vs INTEGRATE vs ADAPT DONOR
 ↓
DESIGN + IMPLEMENT
 ↓
VERIFY
 ↓
ACCEPT
 ↓
NEXT NECESSARY CAPABILITY
```

A discovered technology, donor feature or integration is not itself a product need.

A technology may move from evaluation into implementation only when all of the following are true:

1. a current or near-term product capability has a demonstrated gap;
2. the owning architectural boundary is clear;
3. native build vs integration vs donor adaptation has been compared;
4. authority, privacy, data ownership and recovery implications are understood;
5. the selected approach has a bounded acceptance path;
6. the work does not displace a more necessary product dependency without an explicit reason.

---

## 3. Work classification

Every active item must have one scheduling classification.

### PRIMARY

The current product milestone. It receives implementation priority and determines what supporting work is necessary.

### REQUIRED ENABLEMENT

A dependency that must be satisfied for the current milestone to be accepted because the product cannot be truthful, safe, operable or verifiable without it.

### SUPPORTING PARALLEL

Useful work that directly strengthens the current or immediately next milestone but is not allowed to become a competing programme or delay primary proof without evidence.

### DEFERRED / DEMAND-GATED

Valid future capability whose implementation trigger has not arrived.

Permanent rule:

> **A candidate can be important without being current.**

---

## 4. Product identity

Global Mobility AIOS is a **governed, evidence-grounded, transparent and cost-intelligent high-autonomy digital organization for global mobility**.

It is not merely:

- an immigration chatbot;
- a visa questionnaire;
- a CRM with AI;
- a document uploader;
- a generic multi-agent framework;
- a SaaS admin dashboard;
- a human approval queue;
- a generic ERP;
- an autonomous legal/tax/investment decision-maker outside retained authority.

Target identity:

> **Global Mobility AIOS coordinates persistent AI employees to perform global-mobility work through purpose-scoped context, governed Evidence, earned capability-specific autonomy, risk-tiered verification, durable organizational execution and Human Owner / Board sovereignty.**

Operating principles:

> **AIOS does the work. Humans govern exceptions and retained authority.**

> **Board by exception. Transparency by default.**

> **Agents may be wrong while thinking; AIOS may not be wrong silently when committing truth.**

> **No new major framework by default; prove a measured architectural gap first.**

> **No necessary production infrastructure should remain absent merely because it is not a differentiating AI feature.**

---

## 5. Complete mobility lifecycle target

The long-term product target remains the complete mobility lifecycle:

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
→ Decision Readiness / verification
→ Human / Board authority where required
→ submission / appointment / external action
→ authority response
→ remediation / follow-up / appeal where applicable
→ relocation / post-arrival obligations
→ renewal / status change / family progression
→ long-term residence
→ citizenship / business / investment / long-term mobility strategy
```

The lifecycle must support changed goals, employers and jurisdictions; rejected applications; expired Evidence; superseded rules; family dependencies; long-lived case history; reassessment; and future mobility strategy.

L/M/N are not the end of the product. They establish the organizational operating capability needed to expand this lifecycle without losing truth, authority or provenance.

---

## 6. Constitutional ownership

Permanent separation:

```text
Capability = what runtime can technically do
Authority  = what organization permits
Autonomy   = how independently authority may be exercised
Risk       = consequence of the specific action
```

Permanent rule:

```text
CAN DO != MAY DO
```

AIOS remains canonical for:

- Human Owner / Board sovereignty;
- `OrganizationPosition`;
- WorkItem / Mission meaning;
- Evidence / SourceSnapshots / VerifiedRules;
- canonical case and mobility state;
- authority / autonomy / risk;
- Decision Readiness;
- materiality;
- Command Gateway outcomes;
- Organizational Immune System policy;
- canonical organizational Activity / Decision lineage.

External infrastructure may provide capability but may not redefine those semantics.

---

## 7. Current accepted state

| Stage | State | Meaning |
|---|---|---|
| A Constitutional Contracts | COMPLETE / PASS / SEALED | constitutional risk/authority/transparency foundation |
| B Minimal Governance Kernel | COMPLETE / PASS / SEALED | bounded Command Gateway/governance kernel |
| C Transparency Foundation | COMPLETE / PASS / SEALED through C.4 | Board-inspectable trace/read contracts |
| D Context + persistent employee/runtime | COMPLETE / PASS / SEALED through D.3 | OrganizationPosition, ContextBundle and runtime separation |
| E First Governed Mobility Vertical | COMPLETE / PASS / SEALED through E.2 | governed mobility proposal path |
| F Decision Readiness | COMPLETE / PASS / SEALED | deterministic routing/quality signal |
| G Independent Verification + canonical eligibility | COMPLETE / PASS / SEALED through G.5 | blind verification, canonical effect, reassessment |
| H.1–H.2 bounded Immune foundation | COMPLETE / PASS / SEALED / BOUNDED FOUNDATION CLOSED | restrict-only measurement/safety foundation |
| I.1 Capability-specific autonomy profile | COMPLETE / PASS / SEALED | canonical A0–A5 capability/context truth |
| I.2 Shadow autonomy evidence | COMPLETE / PASS / SEALED | immutable exact-profile observations |
| I.3 Promotion eligibility policy | COMPLETE / PASS / SEALED | Board-authored eligibility only, no autonomy mutation |
| I.4 Qualified + temporal evidence evaluation | COMPLETE / PASS / SEALED | promotion-grade evidence qualification, no autonomy mutation |
| Outcome Evaluation baseline | PROVEN BASELINE | outcome evidence before autonomy mutation |
| J.1 Austria Agent Organization Runtime | COMPLETE / PASS / SEALED | native Austria organization topology + runtime bindings |
| K.1 Bounded Specialist Execution / Coworker Runtime | COMPLETE / PASS / SEALED | durable specialist execution evidence + stronger owner synthesis gate |
| L Live Organization | IMPLEMENTED / ACCEPTANCE PENDING | live-provider/fresh-retrieval/failure/owner-replay runtime evidence accepted; independent professional review and final exact-current-head proof remain |
| M Board Transparency Experience | NOT STARTED | full owner/Board transparency experience after L acceptance |
| N Learning & Optimization | NOT STARTED | measured learning, performance, AI economics and controlled optimization |

No actual autonomy mutation mechanism is accepted or implemented.

---

## 8. K.1 accepted baseline

Technical candidate:

```text
9a7df63511e45f6a0945ae933929522314a04ec3
```

Accepted proof:

```text
GitHub Actions Production Proof 32582805820 — 4/4 PASS
Repository Policy Check         32582805835 — PASS
SQLite                          1194 passed / 20 skipped / 1 warning / 0 failed
PostgreSQL 16                   103 passed / 1 warning / 0 failed
Migration head                  0081_capability_autonomy_evidence_evaluation_policy
Registered application tables  124
Woodpecker push #17             4/4 PASS
Woodpecker PR #18               4/4 PASS
```

Permanent K.1 invariants remain:

- exact replay does not duplicate current-work output, AgentRun or execution attempt;
- stale/mismatched context/runtime/provenance fails closed;
- provider/model identity is non-authorizing;
- WorkItem completion alone is insufficient for owner synthesis;
- no external side effects are authorized merely by runtime availability.

Acceptance record:

`docs/V1_3_K1_BOUNDED_SPECIALIST_EXECUTION_ACCEPTANCE_2026-08-22.md`

---

## 9. Three-horizon master direction

### NOW — L Live Organization

**Classification:** PRIMARY

L must prove that the governed organization operates as a real product capability, not merely as service functions or synthetic dashboard state.

Current bounded path:

```text
canonical Austria objective
→ canonical pathway authority / Evidence / VerifiedRule / source-snapshot lineage
→ guarded fresh official-source equivalence check where freshness is claimed
→ accepted K.1 specialist WorkItems
→ current ContextBundles / runtime bindings
→ bounded specialist executions
→ durable specialist outputs
→ owner synthesis readiness
→ Board/admin-human bounded owner-synthesis command
→ one durable owner OrganizationalActionOutput
→ one MATERIAL OrganizationActivity
→ root objective completion
→ exact replay without duplicate evidence
→ Board-safe persisted projection
→ Owner Cockpit Live Organization surface
```

Current L implementation exists. The real guarded live-runtime cycle, independent provider-failure behavior and exact owner replay are now evidenced, but acceptance remains open until independent professional review and final exact-current-head technical proof are observed.

Latest **fully green historical L technical checkpoint**:

```text
34597abf24a348a28b25e15dccb1a22fa35b3998
Woodpecker PR Pipeline #77 — 4/4 PASS
```

`34597abf...` is eight commits after the guarded fresh-retrieval checkpoint `a85384e6...`. The #77 green proof therefore covers a later L descendant containing the fresh-retrieval implementation plus subsequent Live Organization frontend/acceptance hardening. It remains historical technical/product proof only. The separate 2026-08-30 runtime receipt records the later real guarded live-provider cycle; it does not convert #77 into current-head proof or establish independent professional correctness.

Repository-truth reconciliation on 2026-08-25:

```text
later source-bearing branch head
38f028f8c3123fdb5678a2ad1e9ff80ddeec35d8

first reconciliation docs head
c1735ceba35669ffd52bae1a15827d1fa9983a65

GitHub Actions on 38f028f8...
V12 Production Proof       32700187321 — FAILURE, no executed job steps
Repository Policy Check    32700187332 — FAILURE, no executed job steps

GitHub Actions on c1735ceb...
V12 Production Proof       32795279600 — FAILURE, no executed job steps
Repository Policy Check    32795279598 — FAILURE, no executed job steps
```

Those GitHub Actions runs are **runner/infrastructure startup evidence, not repository-test evidence**. They neither prove nor disprove the corresponding repository heads. Because source changes occurred after `34597abf...`, the #77 green checkpoint must not be relabeled as current-head proof. This proof-order correction advances the branch again, so exact-head proof remains pending after this documentation-only change.

#### L REQUIRED ENABLEMENT

Current status of the acceptance capabilities:

1. **LATEST FULLY GREEN TECHNICAL CHECKPOINT — `34597abf...`, Woodpecker #77 4/4 PASS; FINAL EXACT-CURRENT-HEAD RE-VERIFICATION PENDING** after professional-review and acceptance-documentation changes are complete;
2. **COMPLETE — browser/product behavior proof** for the bounded Cockpit read/command/failure/replay surface; route-controlled browser proof is UX/product proof, not backend integration proof;
3. **COMPLETE — truthful UX states** for current organization state, missing evidence, blocked work and retained authority;
4. **IMPLEMENTED — professional-review workflow/compiler** for the Austria benchmark; implementation alone is not professional correctness evidence;
5. **REMAINING — first real independent professionally reviewed Austria tranche**, used to discover disagreement/error classes before setting a larger target;
6. **COMPLETE — real live-model success + provider-failure evidence and one guarded real fresh-retrieval L-cycle**, including Board owner materialization and exact replay, recorded in `docs/V1_3_L_LIVE_RUNTIME_ACCEPTANCE_EVIDENCE_2026-08-30.md`;
7. **COMPLETE — Evidence / VerifiedRule / source-snapshot lineage** wherever the bounded Austria regulated claims enter the L cycle;
8. **COMPLETE — operational correlation** sufficient to diagnose latency, retries and runtime/provider failure without confusing telemetry with canonical Activity.

Operational execution and reviewer handoff are documented in `docs/L_LIVE_ORGANIZATION_ACCEPTANCE_OPERATIONS.md`.

#### L UX work

UX work starts before and alongside implementation, but UX capability is the requirement—not a specific design tool.

```text
UX0 experience / information-architecture audit
→ UX1 bounded design-system foundation required by real L/M surfaces
→ UX2 Live Organization co-design against actual L contracts
```

Rules:

- UX0 and UX2 operate on real current routes/contracts, including `/cockpit/live-organization`;
- UX1 builds only primitives/tokens/patterns actually required by L/M;
- Penpot is the preferred design environment, not an L acceptance prerequisite by name;
- Storybook remains a candidate component workbench until bounded adoption proves value;
- mock design state may never be represented as accepted live organization state.

#### L production foundation

**Observability/correlation:** REQUIRED ENABLEMENT for operational maturity of L.

OpenTelemetry is the current preferred/trial-eligible implementation direction because an optional vendor-neutral pilot already exists. The requirement is traceable L behavior; OpenTelemetry itself does not become business truth.

```text
engineering telemetry != canonical OrganizationActivity
```

**Backup / isolated restore:** SUPPORTING PARALLEL production foundation. It becomes a release/deployment blocker when the deployment target requires recoverability proof; it must not displace current L product proof merely because backup tooling exists.

**Secrets management:** SUPPORTING PARALLEL production foundation. Introduce a secrets-manager boundary when a real credential lifecycle requires it; do not migrate secrets speculatively.

#### V1.3.6 Tranche 1 research

**Classification:** SUPPORTING PARALLEL RESEARCH / NO PRODUCT OR RUNTIME ADOPTION.

Technology Radar V1.3.6 records R2 architecture-fit research for:

```text
AIOS-native Skill Registry
OpenFGA / OPA / Cedar / SpiceDB authority candidates
MCP 2026-07-28 / A2A 1.0 governed gateways
Cybersecurity Skill Registry
Inspect AI / Promptfoo / garak Red Team Lab candidates
```

The tranche adds no production dependency, migration, adapter, authority grant or M implementation. Its aggressive execution amendment authorizes isolated synthetic R3 labs without another general radar-scheduling decision:

```text
Wave A: OpenFGA vs OPA | MCP gateway | Inspect AI + Promptfoo
Wave B: A2A | Skill Registry | OpenTelemetry | backup/PITR restore | SecretsPort/OpenBao
```

At most three R3 lanes may run concurrently. Candidates must prove, advance, hold with a named trigger or be rejected on a fixed clock. Production adoption remains separately gated. Radar work must not delay professional Austria review or final L proof.

Canonical research index: `docs/TECHNOLOGY_RADAR_V1_3_6.md`.

#### L donor use

Munder Difflin is a SUPPORTING PARALLEL donor only where a demonstrated L/UX2 gap exists.

Relevant candidates include:

- presence/heartbeat mechanics;
- event synchronization;
- transcripts/tool signals;
- runtime/cost telemetry concepts;
- live-organization scene mechanics.

Rejected donor assumptions remain rejected:

- donor authority model;
- donor state as canonical AIOS truth;
- direct authoritative mutation;
- pixel-art/game-like presentation as the product design language;
- decorative/random activity that implies work not present in canonical state.

#### Post-L extraction rule

The Austria objective/runtime and Live Organization services are intentionally allowed to remain route-specific while L acceptance is stabilizing. After L is sealed — or when a second country/route creates demonstrated duplication — extract only proven seams such as:

- mobility-domain canonical-source resolution;
- reusable specialist execution-evidence reasoning;
- route/country-agnostic objective-topology validation;
- read-model, owner-synthesis/materialization, lineage-validation and lifecycle/replay responsibilities.

Do not perform a broad Austria-to-generic refactor before L acceptance merely to reduce file size. A second vertical should validate the abstraction rather than be forced into a speculative DSL.

### NEXT — M Board Transparency Experience

**Classification:** PRIMARY only after L acceptance.

M turns accepted Live Organization truth into the complete Human Owner / Board transparency experience.

Expected capability set:

```text
UX3 Cockpit + Board Room
→ organization / objective / employee drill-down
→ evidence + provenance inspection
→ risk / authority / autonomy inspection
→ incidents / blockers / intervention paths
→ performance / quality / latency / cost visibility
→ reusable accessible frontend components
→ truthful organization visualization where operationally useful
```

Munder living-organization mechanics may be adapted only where they improve comprehension of accepted AIOS state.

M does not create new business truth for presentation.

### THEN — N Learning & Optimization

**Classification:** PRIMARY only after M acceptance.

N converts accumulated outcomes and runtime evidence into measured improvement.

Expected capability set:

- outcome measurement;
- professional modification/rejection analysis;
- runtime performance optimization;
- AI Economics / cost per successful governed outcome;
- provider/model routing evaluation;
- retrieval/context optimization;
- evaluation evolution;
- organizational learning;
- controlled autonomy evolution only when outcome evidence justifies it.

No autonomy increase is implied merely by having more telemetry or more model options.

### LATER — mobility lifecycle expansion

After L/M/N establish the operating system, the roadmap returns to the next highest-value lifecycle gap.

Potential capabilities include:

- identity / SSO;
- communications;
- e-signature;
- external authority workflows;
- post-approval operations;
- business/corporate mobility expansion;
- ERP/accounting;
- payments;
- additional jurisdictions and professional verticals.

Their exact order is selected by product necessity, not by this list order.

---

## 10. Technology Radar role

The Technology Radar is a **decision/support layer**, not an implementation roadmap.

It answers:

```text
What technology could satisfy a demonstrated capability gap?
What evidence have we gathered?
What is its adoption state?
What risks, costs and replacement implications exist?
```

It does not answer:

```text
What should the team implement next?
```

That answer belongs here in `ROADMAP.md`.

Radar states such as `RESEARCH`, `PILOT`, `TRIAL-ELIGIBLE`, `WATCH`, `DEFER`, `ADOPT` or `REJECT` describe evidence/adoption posture, not scheduling priority.

Examples:

- OpenTelemetry is pulled forward because L has a concrete correlation need;
- ERPNext/Odoo remain deferred because ERP is not on the current product dependency path;
- LLMLingua-2 remains a selected context-compression pilot but advances only when a measured context/runtime need warrants it;
- Promptfoo remains useful evaluation infrastructure but does not become a milestone by itself;
- Hy4 Preview is a `RESEARCH → BOUNDED PILOT` developer-tooling candidate for sanitized comparison on an existing L/UX2 frontend surface; it is not a production AIOS runtime, an L dependency or permission to start M;
- a new generic agent framework remains rejected by default unless a measured gap cannot be solved cleanly with current runtime contracts.

---

## 11. Donor programme role

Donor programmes are capability accelerators, not alternative architectures or product roadmaps.

For every donor capability:

```text
product need
→ measured gap
→ donor candidate
→ DIRECT REUSE / PORT / ADAPT / REIMPLEMENT / REJECT
→ AIOS-owned boundary
→ bounded proof
```

Munder Difflin, Plasma, LLMLingua and future donors remain subordinate to AIOS semantics and current product necessity.

Vendoring, pinning or documenting a donor never means production adoption.

---

## 12. Enterprise integration role

Enterprise integrations are **dependency- and demand-triggered**.

Permanent boundaries:

> **Identity providers authenticate; AIOS authorizes.**

> **Telemetry observes AIOS truth; it does not become AIOS truth.**

> **Secrets may be injected into runtimes; they may not become context or memory.**

> **External execution requires governed intent, provenance, idempotency and recovery semantics.**

> **ERP/accounting may own bounded back-office ledgers; it never owns mobility truth or Board authority.**

> **No integration may bypass the Command Gateway for a material action.**

Current scheduling posture:

| Capability | Classification | Trigger |
|---|---|---|
| L telemetry correlation | REQUIRED ENABLEMENT | real L runtime/cockpit diagnosis |
| Backup / isolated restore | SUPPORTING PARALLEL | production recoverability requirement |
| Secrets manager | SUPPORTING PARALLEL | real secret lifecycle / rotation requirement |
| Identity / SSO | DEFERRED until dependency | multi-user/deployment authentication need |
| Communications Gateway | DEFERRED until dependency | governed outbound communication capability |
| E-signature | DEFERRED until dependency | signed-document workflow enters product path |
| ERP/accounting | DEMAND-GATED | real commercial/back-office ledger demand |
| Payments | DEMAND-GATED | typed financial execution need + authority model |

---

## 13. UX / frontend role

Frontend design is a first-class product workstream, not a late cosmetic layer.

It must begin early enough to influence product semantics and interaction, while remaining grounded in canonical contracts.

```text
canonical product need
→ real read/write contract
→ information architecture
→ interaction design
→ reusable implementation
→ accessibility/responsive/state verification
→ browser/product proof
```

Preferred tooling may change without changing the product requirement.

Penpot, Storybook, Hy4 Preview or future design/development tools can improve execution, but no tool or model is constitutional product authority. Any hosted-model frontend pilot must use sanitized context and remain subject to the existing truth, privacy, accessibility, build and browser-proof gates.

Next.js/React remains production frontend authority until explicitly changed through the same necessity-driven process.

---

## 14. Acceptance gate

Acceptance is the gate between primary milestones.

For every substantive milestone, apply the relevant dimensions from this sequence:

```text
implementation
→ focused tests
→ schema/migration verification where affected
→ PostgreSQL/concurrency proof where state races matter
→ frontend tests/types/build where affected
→ browser E2E/accessibility/responsive proof where product interaction matters
→ security/privacy/authority checks where affected
→ repository policy + complete PR diff hygiene
→ Woodpecker forward proof
→ documentation reconciliation
→ COMPLETE / PASS / SEALED only after observed evidence
```

A running test is not a PASS.

A documentation commit does not inherit a previous runtime PASS automatically.

A design frame is not product proof.

A deterministic fallback test is not live-model correctness proof.

A deterministic J→K→L backend test may prove integration/lineage while still proving nothing about real-provider response quality.

A source-curated benchmark is not professional correctness proof.

A backup file is not recovery proof.

A telemetry span is not canonical OrganizationActivity.

Only after acceptance does the next dependent milestone become the primary implementation target.

---

## 15. Current L acceptance dimensions

L must eventually prove, as applicable to the accepted scope:

1. one real persisted Austria objective/owner cycle;
2. exact WorkItem/execution/runtime provenance;
3. owner synthesis only from current valid specialist evidence;
4. persisted material OrganizationActivity/Decision state;
5. deterministic replay without duplicate current evidence;
6. explicit PostgreSQL concurrent owner-synthesis behavior;
7. fail-closed blocked/tampered/stale state behavior;
8. Board/admin-human bounded operator command path;
9. Cockpit consumption backed only by persisted AIOS truth;
10. browser interaction for the real command/read/failure path;
11. Evidence/VerifiedRule lineage where regulated claims are used;
12. authority/autonomy/provider-model non-authority visibility;
13. latency/retry/governance measurements;
14. operational correlation sufficient to diagnose the L cycle;
15. professional review before professional/legal correctness claims;
16. live-model/retrieval/provider-failure evaluation before realistic AI-reasoning claims;
17. no simulated completion/history used to populate the live experience.

The exact acceptance record may split these into bounded proof slices, but no slice may silently claim evidence belonging to another.

---

## 16. Product surfaces

### Global Mobility AIOS Cockpit

Top-level Human Owner / Board organizational command surface.

Target modules include:

```text
Organization
Missions / objectives
Agents / positions
Performance
Quality
Risk
Incidents
Autonomy
Transparency
Search / intelligence
Board Room
```

### Board Room

A module inside Cockpit for reserved decisions, strategy, critical incidents, major policy/autonomy decisions and executive escalation.

### Operations

Professional/operator surface converging cases, Evidence, reviews, next actions, deadlines, blockers, specialist work and authority workflow.

### My Mobility

Journey-centric user experience: goals, pathways, Evidence, unknowns, actions, deadlines, cost, risk and long-term progression in plain language.

### Department workspaces

Department-specific composed views over canonical organization state without creating new authority paths.

---

## 17. Evidence / truth hierarchy

```text
L0 model speculation
L1 conversation / memory / hypothesis
L2 retrieved information
L3 SourceSnapshot
L4 governed Evidence
L5 reviewed candidate
L6 VerifiedRule / certified governed fact
L7 governed case conclusion
L8 approved authority-bearing action
```

Forbidden shortcuts remain:

```text
L1 ↛ L6
L2 ↛ L7
L6 ↛ L8 automatically
```

> **Memory provides continuity. Evidence provides authority.**

---

## 18. Earned autonomy and Immune System

Capability-specific A0–A5 semantics remain:

| Level | Meaning |
|---|---|
| A0 | Prohibited |
| A1 | Human executes |
| A2 | AI prepares; approval required |
| A3 | Autonomous with mandatory review |
| A4 | Autonomous with monitoring and valid recovery controls |
| A5 | Fully autonomous bounded operation |

Progression remains evidence-driven:

```text
SHADOW
→ RECOMMEND
→ SUPERVISED
→ AUTONOMOUS
→ HIGH-TRUST AUTONOMOUS
```

I.1–I.4 establish evidence/policy foundations only. They do not authorize self-promotion.

The Organizational Immune System may observe, classify, restrict, circuit-break, block and escalate.

> **The Immune System may restrict or stop. It never manufactures permission.**

---

## 19. Context Intelligence

The Context Broker remains responsible for purpose-scoped context, Evidence/VerifiedRule retrieval, organizational memory, relevance, freshness, sensitivity, contradictions, context lineage and optional compression eligibility.

> **More relevant truth, not more tokens.**

LLMLingua-2 remains a pilot behind an AIOS-owned `ContextCompressionPort`; compressed context remains derived execution context, never source truth.

Its pilot status does not grant it implementation priority over current L needs.

---

## 20. Outcome and production metrics

Product/organization metrics include:

- autonomous completion rate;
- human interventions per material actions;
- Board decisions per organizational actions;
- Evidence grounding rate;
- professional modification/rejection rate;
- contradiction rate;
- source freshness;
- capability reliability;
- workflow completion time;
- p50/p95 latency;
- cost per successful governed outcome;
- incident frequency;
- recovery effectiveness;
- lineage completeness;
- transparency lag.

Production/integration metrics include:

- trace completeness;
- mean time to diagnose runtime failures;
- credential exposure events;
- secret rotation/revocation success;
- backup restore success/time;
- RPO/RTO evidence;
- integration availability;
- duplicate external action rate;
- reconciliation completeness;
- provider-specific coupling;
- replacement effort;
- integration operating cost.

Metrics guide prioritization only when tied to an actual product or production need.

---

## 21. Historical compatibility contract — protected

The active V12 roadmap preserves historical markers meaningful to Evidence provenance and repository compatibility.

`v10.22` introduced **multi-batch tranche operations** around governed jurisdiction Evidence workflow.

Historical migration lineage includes:

```text
0032_initial_rule_assertions
```

Protected exact markers:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

These markers must not be erased by later organization-runtime, CI, autonomy, integration, UX or roadmap-reorganization work.

---

## 22. Schema / storage guardrails

Current accepted migration head:

```text
0081_capability_autonomy_evidence_evaluation_policy
```

Current accepted application-table count at K.1 and the latest fully green L technical checkpoint:

```text
124
```

Physical PostgreSQL schema includes the infrastructure `alembic_version` table in addition to the 124 registered application tables.

No schema change is implied by this roadmap reconciliation.

Guardrails:

- migrations are forward, bounded and data-preserving;
- preserved developer SQLite history must not be fabricated/rewritten for UI appearance;
- PostgreSQL remains authoritative deployment/integration relational target;
- isolated PostgreSQL environments are preferred for migration/concurrency contracts;
- external integrations do not gain direct canonical DB mutation shortcuts;
- legacy tenant-qualification gaps are corrected when the affected capability is on the active dependency path or when they create a demonstrated security/integrity risk.

---

## 23. Current roadmap horizon map

```text
NOW — L LIVE ORGANIZATION
│
├─ PRIMARY
│  └─ close real persisted L product operation
│
├─ LATEST FULLY GREEN TECHNICAL/PRODUCT CHECKPOINT
│  ├─ 34597abf / Woodpecker #77 4/4 — historical exact-checkpoint proof
│  ├─ descendant of guarded fresh-retrieval checkpoint a85384e6
│  ├─ real J→K→L backend lineage + replay proof
│  ├─ Cockpit Board command/read/failure product behavior
│  ├─ Evidence / VerifiedRule / source-snapshot lineage
│  └─ operational L-cycle correlation
│
├─ CURRENT EXACT-HEAD PROOF
│  └─ PENDING — later source/docs commits do not inherit 34597abf PASS
│
├─ REMAINING ACCEPTANCE EVIDENCE
│  ├─ first real independent professionally reviewed Austria tranche
│  ├─ real configured-provider success + real provider-failure evidence
│  └─ real guarded fresh-retrieval Austria L-cycle
│
├─ SUPPORTING PARALLEL
│  ├─ backup / isolated restore foundation
│  ├─ secrets boundary when a real credential lifecycle requires it
│  └─ selective Munder analysis for demonstrated L/UX2 gaps
│
└─ DEFERRED UNTIL L SEAL / DEMONSTRATED SECOND-VERTICAL NEED
   ├─ broad Austria-to-generic runtime extraction
   ├─ broad IdP migration
   ├─ governed outbound communications platform work
   ├─ e-signature implementation
   ├─ ERP/accounting
   └─ payments

NEXT — M BOARD TRANSPARENCY EXPERIENCE
│
├─ UX3 Cockpit + Board Room
├─ organization visualization
├─ evidence/provenance drill-down
├─ risk/authority/autonomy interactions
├─ reusable accessibility/component proof
└─ donor adaptations only where proven useful

THEN — N LEARNING & OPTIMIZATION
│
├─ outcome measurement
├─ runtime performance
├─ AI Economics
├─ model/provider routing evaluation
├─ context/retrieval optimization
├─ organizational learning
└─ controlled autonomy evolution only from evidence

LATER — NEXT NECESSARY MOBILITY LIFECYCLE CAPABILITY
└─ integrations/infrastructure are pulled in by the chosen product dependency
```

---

## 24. Current non-goals

The current roadmap does not authorize:

- government submission;
- autonomous client send;
- payments;
- contract signing;
- external irreversible action;
- autonomy mutation;
- Dynamic Autonomy Manager behavior;
- automatic promotion/demotion;
- full ERP implementation;
- broad production SSO migration merely because IdPs are on the Radar;
- another generic agent framework;
- fake live-organization state;
- implementation of a donor feature merely because the donor contains it;
- adoption of Penpot, Storybook, OpenTelemetry or any other tool as constitutional product authority.

---

## 25. Definition of success

The next project maturity increase must come from demonstrated product operation and professional correctness rather than additional architecture alone.

Success path:

```text
real customer / mobility case
→ official-source retrieval and governed Evidence
→ specialist execution
→ owner synthesis
→ human/professional review where required
→ customer/operator-facing explanation and next action
→ tracked outcome
→ professional correctness evidence
→ measurable quality / latency / cost / recovery
```

The project succeeds when architecture, UX, infrastructure, integrations, Radars and donors all serve that path without becoming independent reasons to build.

> **ROADMAP.md determines when and why. Architecture determines where. UX determines how humans experience it. Radars identify candidate technology. Donor programmes define safe reuse. Woodpecker and acceptance records determine whether it is complete.**

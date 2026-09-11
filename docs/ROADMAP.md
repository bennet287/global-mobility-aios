# Global Mobility AIOS — Master Product Roadmap

**Roadmap generation:** 2026.09 — product-direction reset after Mobility and Operator convergence
**Date:** 2026-09-11
**Roadmap authority:** this file is the master WHAT / WHEN / WHY scheduler for Global Mobility AIOS.
**Current sealed redesign baseline:** Phase 13 spatial-focus merge `a75f041d469957ce0573a483c5d431826edda475`
**Code migration head:** `0081_capability_autonomy_evidence_evaluation_policy`

<!-- CURRENT_MIGRATION_HEAD: 0081_capability_autonomy_evidence_evaluation_policy -->

> **Product necessity pulls technology into the project. Technology does not push the product around.**

> **Aggressive capability research. Conservative production authority.**

---

## 1. What Global Mobility AIOS is

Global Mobility AIOS is a governed AI operating system for running high-consequence global-mobility work as a transparent digital organization.

It is not a generic chatbot, a loose swarm of agents, a workflow engine with AI labels, or a virtual office whose animation invents work. The destination is a persistent digital organization in which a Human Owner / Board remains supreme authority while an AI CEO coordinates departments, persistent AI employees, Missions, WorkItems, evidence, decisions, incidents, communication and learning.

The organization may become highly autonomous, but every consequential effect must remain attributable, reconstructable and bounded by authority, risk, evidence and provenance.

### Product north star

> **A governed, evidence-grounded, transparent, cost-intelligent, high-autonomy digital organization that the Human Owner can understand, inspect and steer as naturally as a real company.**

The finished product must answer from real system state: what the organization is trying to achieve; who is working on it; what evidence is being used; what is blocked or uncertain; what employees are discussing or handing off; what was decided and under what authority; what requires the Owner / Board; what work cost; what happened previously; what is likely to happen next; and what the organization learned.

---

## 2. Canonical document map and mandatory read order

The roadmap is the master scheduler, but it does **not** supersede specialized canonical specifications. Future sessions must not treat separate documents as optional islands or infer that a roadmap rewrite deleted their requirements.

### Mandatory session entry path

1. `docs/ROADMAP.md` — master product direction, programme order, current/next work and cross-programme integration map.
2. `docs/aios-v2/README.md` — canonical AIOS V2 session entry point and concise active programme boundary.
3. `docs/aios-v2/AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md` — product destination, redesign principles, six-system model and acceptance philosophy.
4. `docs/aios-v2/AIOS_V2_MASTER_PLAN_EXECUTION_RECONCILIATION_2026-09-08.md` — execution/governance bridge. Historical state/SHA snapshots inside it are evidence from its date, not newer than this roadmap.
5. `docs/aios-v2/AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md` — canonical employee, department, skills, tools, memory, learning and capability/authority architecture.
6. `docs/aios-v2/AIOS_V2_VISUAL_REDESIGN_EXECUTION_DIRECTIVE_2026-09-09.md` — mandatory visible-redesign quality law and anti-generic/anti-AI-slop rules.
7. `docs/aios-v2/AIOS_V2_EFFICIENT_PROOF_LADDER.md` — development-versus-final-seal proof strategy: iterate narrowly, seal broadly.
8. `docs/aios-v2/AIOS_V2_MIGRATION_AND_FINAL_ACCEPTANCE_CHECKLIST.md` — final migration and whole-product acceptance inventory. Individual checkbox/state snapshots may lag accepted implementation and must be reconciled before final closure.

Historical phase audits, PR-specific acceptance records and design references remain supporting evidence and should be read when the active task touches their subject or a regression requires historical context.

### Authority and precedence

When documents appear to disagree, use this order:

1. canonical truth, evidence, authority, security and domain contracts;
2. AIOS Constitution / accepted governance rules;
3. this master roadmap for current programme scheduling and current/next phase state;
4. the Complete Redesign Master Plan for product/redesign destination;
5. Employee Capability & Skills Architecture for employee/capability/skills semantics;
6. active execution directives and proof/acceptance specifications;
7. dated reconciliation/status snapshots;
8. external repositories, design references and donor patterns;
9. implementation convenience.

A newer accepted exact-head implementation may make an old status snapshot stale; it does not silently repeal the permanent architectural or acceptance rule in that document.

### No-orphan requirement

Every unfinished requirement in a canonical companion specification must satisfy at least one of these conditions:

- mapped to an active/future roadmap phase;
- explicitly marked already satisfied by accepted implementation;
- explicitly deferred with rationale;
- explicitly superseded by a named accepted contract.

Before Phase 13 final closure and again before post-redesign capability work begins, perform a companion-spec reconciliation so unfinished requirements cannot disappear simply because they live in another file.

### Historical compatibility markers

Historical roadmap milestone identifiers that are referenced by repository tests remain discoverable here even after the roadmap reset. In particular, the accepted coverage-tranche operations milestone **v10.22**, its **multi-batch tranche operations** capability, and the historical migration marker `0032_initial_rule_assertions` remain part of the preserved programme record; detailed evidence lives in `docs/COVERAGE_TRANCHE_OPERATIONS_V10_22.md`. These markers preserve compatibility and traceability only—they do not redefine the current Phase 13–22 execution sequence or the current migration head.

---

## 3. Operating model

```text
HUMAN OWNER / BOARD
        │
        ▼
AIOS COCKPIT / OPERATOR SURFACE
        │
        ▼
AI CEO
        │
        ├── Departments
        │      └── persistent AI employees / specialist capabilities
        ├── Missions
        │      └── WorkItems / dependencies / blockers
        ├── Evidence / SourceSnapshots / VerifiedRules
        ├── AgentRuns / communication / durable activity
        ├── ExecutiveDecisions / escalations / incidents
        └── learning / optimization
        │
        ▼
GOVERNED CANONICAL STATE
```

The Cockpit is the Human Owner's operating surface. The Board Room is a module inside that operating surface, not the whole product. Living HQ is the spatial visual operating surface through which the Owner can understand the organization as a company rather than as a database dashboard.

---

## 4. Truth, authority and governance model

External models, providers, skills and donor frameworks provide capability. AIOS owns organizational meaning, truth and authority.

Permanent distinctions:

```text
Memory       != Truth
Conversation != Authority
Telemetry    != Canonical Organization Activity
Capability   != Authority
Authority    != Autonomy
Autonomy     != Risk
External runtime != AIOS organization
Animation    != canonical state
Prediction   != canonical state
Scores route; gates authorize
```

Core invariants: Human Owner / Board remains supreme authority; Board by exception and transparency by default; CAN DO is distinct from MAY DO; capability, authority, autonomy and risk remain separate; memory and conversation cannot silently become truth/authority; external runtimes remain replaceable; scores route while governed gates authorize; canonical truth cannot silently inherit model error; compression cannot remove governance meaning; cost optimization cannot override quality; frontier intelligence is an escalation resource; consequential effects cross governed boundaries and remain reconstructable; autonomy is earned capability-by-capability; the visual organization represents real organizational state; **the organization causes the animation, animation never silently causes the organization**; predictive/environmental layers remain non-authoritative; UI interaction is not a business action without an explicit command boundary; tool observation is not evidence merely because an agent saw it; self-improvement must remain bounded, reviewable, reversible and attributable.

---

## 5. Product surfaces

Global Mobility AIOS develops as five connected surfaces: **Mobility**, **Operator/Cockpit**, **Living HQ**, **Board/Governance**, and **Learning & Optimization**.

Mobility provides one coherent client journey across Overview, My Case, Documents, Timeline and Messages from canonical mobility state. Operator is the professional command surface for work, profiles, pathways, evidence, tools, communications, decisions and history. Living HQ is the flagship spatial representation of the actual AI organization. Board/Governance handles consequential decisions, escalations, authority, risk and exceptions. Learning & Optimization uses measured outcomes to propose improvements without silently rewriting governance.

---

## 6. Current product state

Mobility and Operator visual convergence are sealed. Living HQ character, architecture, room, smart-object, WebGPU and presentation foundations exist. Phase 13A spatial-focus polish is sealed at merge `a75f041d469957ce0573a483c5d431826edda475`.

Permanent M.4.1 presentation mapping remains:

```text
working         → focused work pulse
blocked         → blocked attention pulse
awaiting_owner  → waiting
queued          → waiting
completed       → settled idle
unknown         → static

presentationOnly  = true
presenceClaimed   = false
locomotionAllowed = false
```

Walking, conversations, coffee breaks, room entry, handoffs or richer animation may only be promoted when the relevant canonical semantics exist; they cannot be invented for entertainment.

---

## 7. Immediate execution programme — Phase 13 Living HQ flagship convergence

### 13A — Spatial focus polish — SEALED

Overview / Departments / Chambers / Infrastructure focus modes, contextual HUD, presentation-only emphasis, explicit no-authority/no-presence claims, and desktop/phone proof. Accepted merge: `a75f041d469957ce0573a483c5d431826edda475`.

### 13B — Entity focus inspector — NEXT

Inspect department / employee / room / smart-object projections using only governed render-model data. Surface semantic state, presentation state, WorkItem linkage, department work/blocker counts and room/smart-object metrics. Preserve the exact contract: `Selection changes view focus only; it cannot mutate AIOS.`

### 13C — Contextual drill-down

Connect spatial selections to richer read-only inspectors; keep local selection separate from canonical commands; expose lineage/evidence without turning the scene into a dashboard farm.

### 13D — Canonical handoff visualization

Only durable handoff/activity semantics may produce handoff visuals. Show origin, destination, WorkItem and state; distinguish queued/accepted/blocked/completed; never infer transfer from shared Mission membership.

### 13E — Governed conversation visualization

Only canonical communication/activity may produce semantic conversation cues. Decorative social behavior must remain explicitly non-semantic or be omitted where it could imply work.

### 13F — Mission-room and Board escalation convergence

Mission rooms reflect real Mission/WorkItem state; blocked/escalated work routes to appropriate governance surfaces; Board activity reflects actual escalation/decision records; no fake occupancy.

### 13G — Living HQ final visual acceptance + companion-spec reconciliation

Desktop/phone visual proof, responsive/reduced-motion/forced-colors acceptance, performance budget, truth-state assertions and Owner-led visual acceptance. Before closure, reconcile the canonical companion documents and classify every unfinished redesign requirement as satisfied, mapped, deferred or superseded.

---

## 8. Post-redesign priority — Autonomous Global Regulatory Intelligence

This programme is explicitly preserved from `docs/aios-v2/README.md` and `AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md`; it must **not** be lost behind generic platform phases.

Goal: strengthen Global Intelligence into a high-autonomy **Global Immigration Intelligence Department** capable of maintaining visa/residence/work/study/family/business/talent/digital-nomad/permanent-residence knowledge across jurisdictions with minimal routine human intervention while keeping legal/publication authority evidence-driven.

Target loop:

```text
official-source discovery
 → authority/source certification
 → immutable SourceSnapshot
 → multilingual assertion extraction
 → independent machine verification
 → contradiction + source-hierarchy analysis
 → temporal/effective-date/supersession analysis
 → deterministic schema/unit/date/currency checks
 → adversarial/falsification checks
 → pathway/eligibility regression
 → versioned promotion policy
 → automatic VerifiedRule promotion when safely machine-verifiable
 → continuous drift detection / quarantine / rollback
```

Human specialists remain the exception path for genuine ambiguity, authoritative contradiction, insufficient evidence, novel/high-consequence interpretation or unresolved machine disagreement. LLM confidence is diagnostic metadata, never legal authority.

Publication classes remain part of the programme: deterministic/routine Class A; stronger-gated structured eligibility Class B; interpretive/high-consequence Class C with specialist exception judgment; and conflicted/insufficient Class D which never promotes. Promotion policy is versioned and employees cannot increase their own authority class.

Self-correction is mandatory: stale, superseded, contradicted or regression-failing rules must support quarantine/demotion/rollback and dependency-impact propagation while historical decisions preserve the exact rule/source fingerprints used at the time.

Coverage must be explicit by jurisdiction, pathway, source class, language and rule type. The eligibility engine consumes VerifiedRules rather than independently reinterpreting the open web for each case.

Evaluation must precede broad authority using a growing multilingual/multi-jurisdiction gold corpus, adversarial tests and false-promotion-focused metrics. The primary KPI is **correct autonomous throughput at an acceptably tiny false-promotion rate**, not raw automation percentage.

Delivery programme:

1. reconcile existing regulatory intelligence, SourceSnapshot, VerifiedRule, pathway and professional-review contracts;
2. establish jurisdiction/authority/certified-source registry and coverage graph;
3. implement multilingual assertion extraction plus independent verification;
4. add temporal/supersession, contradiction and authority-hierarchy reasoning;
5. add deterministic rule compiler and pathway/eligibility regression harness;
6. add adversarial/mutation verification;
7. implement versioned automatic-promotion classes plus quarantine/demotion/rollback;
8. build continuous evaluation/calibration corpus;
9. pilot bounded Class A/B autonomous publication and expand only from measured evidence;
10. scale jurisdiction/source coverage without Austria hard-coding;
11. integrate real department/work/coverage/verification state into Operator/Owner/Living HQ.

**North star:** automate research, verification, promotion, monitoring and correction as far as evidence permits; escalate judgment, not routine work.

---

## 9. Platform capability expansion

These platform phases support the regulatory-intelligence programme and the wider digital organization. Their ordering may interleave with the department programme only where a concrete dependency requires it.

### Phase 14 — AIOS Native Skills Registry

Adopt selectively from the SKILL.md ecosystem/`antigravity-awesome-skills`: portable definitions, validation, discovery metadata, curated role bundles and workflow recipes. AIOS adds durable ID/version, compatible roles, allowed/denied tools, mutation classification, authority tier, evidence behavior, risk, budget, output contract, tests and revocation. Do not bulk-import external catalogues.

This phase implements the registry portion of `AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md`; learned/imported skill acquisition never implies authority acquisition.

### Phase 15 — Agent Lifecycle Governance Hooks

Introduce governed pre/post tool-use, tool failure, permission request/denial, task lifecycle, subagent lifecycle, session lifecycle, compaction and cancellation signals. Inspiration may come from `open-agent-sdk-typescript`, but signals enter existing AIOS activity/evidence/governance boundaries and remain telemetry until normalized into canonical meaning.

### Phase 16 — Runtime Reliability & Cost Intelligence

Gap-audit before adoption. Evaluate model routing, budgets, loop/stall detection, cancellation/circuit breakers, bounded retry, checkpoint/recovery, governance-preserving context compaction, OpenTelemetry-compatible observability and provider health/quality history. PraisonAI and other donors are mechanism references, not orchestration replacements.

### Phase 17 — Agent Security Assurance

Use OWASP Agentic AI/LLM guidance, AI verification standards, multi-agent threat modelling, MCP security, agent identity/authorization, secure tool invocation, prompt-injection boundaries, skill/tool supply-chain integrity, provenance integrity, adversarial regression and security incident response. Tests must target AIOS authority semantics, not generic scanner counts.

### Phase 18 — Enterprise Governance, Risk & Compliance

Map canonical evidence and governance into useful enterprise controls: risk linkage, policy/control ownership, audit-ready evidence export, approval/exception lineage, incident tracking, capability authorization reviews and standards mappings where product/customer need justifies them.

### Phase 19 — Organizational Learning & Optimization

Measure provider/model performance, employee/skill success and corrections, repeated blockers, source reliability, cost per successful outcome, routing/handoff quality, escalation, decision reversal and time-to-resolution. Learning begins as proposals; promotion requires governed acceptance.

### Phase 20 — Earned Autonomy

Grant autonomy capability-by-capability with bounded scope, authority ceiling, risk class, budget, rollback, audit, quality threshold, revocation and periodic review. No global autonomous mode bypasses governance.

### Phase 21 — External Interoperability

Evaluate MCP, A2A-style interoperability, coding agents, enterprise connectors, local/open models and sandboxed execution only when product need requires them. Every integration requires identity, authority, provenance, timeout, failure and replay boundaries.

### Phase 22 — Production Operations & Scale

Deployment architecture, justified PostgreSQL/Redis/worker scaling, backup/restore, disaster recovery, secrets lifecycle, observability/alerting, load testing, privacy/retention, tenancy/isolation, release/rollback, runbooks and cost controls. AIOS remains primarily the governed control plane; large-model inference stays external unless evidence supports another model.

---

## 10. External repository adoption ledger

Repository research is a donor programme, not an architecture vote.

**Adopt selectively:** `awesome-ai-organization` for organizational coverage/roles/workflow/HITL/audit/cost-quality patterns; `agency-agents` for role design and measurable specialist responsibilities; `munder-difflin` for live-office legibility, avatar representation, handoff/status visualization, human gates, budgets/circuit breakers/isolation concepts without importing its file-hive runtime or fake activity; `antigravity-awesome-skills` for skill-format/discovery ideas; `open-agent-sdk-typescript` for lifecycle/permission/budget/cancellation/subagent concepts; PraisonAI for gap-audited routing/guardrails/telemetry/recovery/loop detection/compaction/interoperability; `career-ops` for bounded workflow/canonical-status/human-final-decision/browser-proof patterns.

**Research-only/constrained:** Automaton may inform protected rules, audited versioned self-change, heartbeat/resource degradation and rate limits, but sovereign self-replication, autonomous self-funding, unrestricted self-modification and no-human-operator governance are rejected. MiroFish may inform graph/persona/memory/simulation visualization concepts, but simulation is not organizational truth and AGPL code is not copied without an explicit licensing decision. Security/pentesting collections contribute defensive standards/testing methods only; offensive utilities are not AIOS product dependencies.

The companion session-entry ledger may contain additional donor decisions (for example runtime seams, memory research and engineering-hardening references). Those decisions remain valid unless explicitly reconciled/superseded here; the no-orphan rule applies to them too.

---

## 11. UI / UX direction

AIOS should feel like a premium operating system for a living digital company rather than an admin template: modern, spatial, information-dense without clutter; environment-as-interface where useful; cinematic depth for hierarchy; original miniature employee characters with recognizable role families; modern HQ architecture rather than pixel towers; contextual HUDs/inspectors; clear separation of live truth, prediction, history and presentation.

Motion communicates supported state—focus, blocked attention, waiting, completion, canonical handoffs, genuine escalation and scene navigation. Decorative ambience cannot imply false work, presence or authority.

Every flagship slice considers desktop/phone, keyboard, reduced motion, forced colors/high contrast, readable fallback, predictable focus semantics and bounded rendering cost. The Visual Redesign Execution Directive remains mandatory: old content inside V2 chrome is not a completed redesign, and generic SaaS/AI-slop output is rejected even when CI is green.

---

## 12. Engineering and proof discipline

**Exact-head acceptance:** only the intended candidate head can be accepted; older green runs are historical evidence.

**Bounded PRs:** one semantic purpose per PR; do not mix unrelated roadmap/runtime/schema/visual changes.

**Stale-branch rule:** if a parent gate changes, reconstruct dependent work onto the newly sealed base before acceptance.

**Failure classification:** distinguish deterministic product regression, literal/source-contract regression, browser flake, external browser/dependency infrastructure failure, backend/database failure and policy/hygiene failure before changing code.

**Efficient proof:** follow `AIOS_V2_EFFICIENT_PROOF_LADDER.md`: iterate narrowly; seal broadly. Targeted browser/screenshot proof should find visual defects before expensive full proof, while final required quality gates remain mandatory.

**Truth-contract compatibility:** established literal truth statements may be CI-enforced; explanatory copy cannot erase sealed contracts.

---

## 13. What we deliberately do not build

AIOS does not become a generic multi-agent clone, ungoverned swarm, bulk-imported prompt catalogue, crypto/self-replicating organism, simulated office inventing human-like activity, security exploitation toolkit, all-purpose GRC suite, unnecessary model-hosting project, or second canonical state hidden in frontend/renderers/memory/external runtimes.

---

## 14. Immediate order of work

```text
1. Seal this master-roadmap + canonical-companion reconciliation.
2. Reconstruct Living HQ Entity Focus onto that sealed base.
3. Prove and seal the entity inspector.
4. Continue contextual Living HQ drill-down.
5. Promote richer handoff/conversation visuals only from canonical semantics.
6. Complete Living HQ final visual acceptance and companion-spec reconciliation.
7. Begin Autonomous Global Regulatory Intelligence reconciliation/coverage foundation.
8. Build AIOS Native Skills Registry where required by employee/regulatory capability work.
9. Add lifecycle governance hooks through existing canonical boundaries.
10. Perform runtime-reliability gap audit before importing mechanisms.
11. Establish Agent Security Assurance before expanding consequential autonomy.
12. Continue regulatory-intelligence verification/promotion/evaluation programme.
13. Add enterprise GRC only where customer/audit needs justify it.
14. Build measured learning and earned autonomy.
15. Add interoperability and production scale as product dependencies require.
```

---

## 15. Definition of destination

Global Mobility AIOS is successful when the Human Owner can open the product and understand a real, continuously operating AI organization without reading logs or trusting theatrical simulation.

The system should make it possible to see what the company is doing, inspect why it is doing it, trace what evidence and authority produced each consequential outcome, intervene when necessary, replay what happened, measure cost and quality, and safely grant more autonomy where performance earns it.

The long-term advantage is not the number of agents, models, animations or integrations. It is the combination of capable AI employees, durable organizational memory, canonical evidence and decisions, explicit authority, visible organizational state, reliable execution, measured learning and earned autonomy.

That combination is the direction of Global Mobility AIOS.

# Global Mobility AIOS — Master Product Roadmap

**Roadmap generation:** 2026.09 — product-direction reset after Mobility and Operator convergence  
**Date:** 2026-09-11  
**Roadmap authority:** this file is the master WHAT / WHEN / WHY scheduler for Global Mobility AIOS.  
**Current sealed redesign baseline:** Phase 13F merge `310b73a2eec63f9f0b2f3a0d53752867c1097359`  
**Active programme:** Phase 13G.1 — Living HQ Architectural World Redesign  
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

1. `docs/ROADMAP.md` — master product direction, programme order, current/next work and cross-programme integration map.
2. `docs/aios-v2/README.md` — canonical AIOS V2 session entry point and active programme boundary.
3. `docs/aios-v2/AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md` — product destination, redesign principles, six-system model and acceptance philosophy.
4. `docs/aios-v2/AIOS_V2_MASTER_PLAN_EXECUTION_RECONCILIATION_2026-09-08.md` — execution/governance bridge; dated SHA/status snapshots are historical evidence.
5. `docs/aios-v2/AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md` — employee, department, skills, tools, memory, learning and capability/authority architecture.
6. `docs/aios-v2/AIOS_V2_VISUAL_REDESIGN_EXECUTION_DIRECTIVE_2026-09-09.md` — mandatory visible-redesign quality law and anti-generic/anti-AI-slop rules.
7. `docs/aios-v2/AIOS_V2_EFFICIENT_PROOF_LADDER.md` — iterate narrowly, seal broadly.
8. `docs/aios-v2/AIOS_V2_MIGRATION_AND_FINAL_ACCEPTANCE_CHECKLIST.md` — final migration and whole-product acceptance inventory.
9. `docs/aios-v2/AIOS_V2_PHASE_13G1_ARCHITECTURAL_WORLD_REDIRECT_2026-09-11.md` — Owner rejection record and architectural redirect.
10. `docs/aios-v2/AIOS_V2_PHASE_13G1_VISUAL_OUTCOME_EXECUTION_PLAN_2026-09-11.md` — exact visual outcome, spatial programme, work packages and acceptance gates for the active Living HQ correction.

### Authority and precedence

When documents appear to disagree, use this order: canonical truth/evidence/authority/security/domain contracts; AIOS Constitution/accepted governance; this roadmap for current scheduling; Complete Redesign Master Plan; Employee Capability & Skills Architecture; active execution/proof directives; dated reconciliation snapshots; external references/donor patterns; implementation convenience.

A newer accepted exact-head implementation may make an old status snapshot stale; it does not silently repeal permanent architectural or acceptance rules.

### No-orphan requirement

Every unfinished requirement in a canonical companion specification must be mapped to an active/future roadmap phase, explicitly marked satisfied by accepted implementation, explicitly deferred with rationale, or explicitly superseded by a named accepted contract.

### Historical compatibility markers

Historical identifiers referenced by repository tests remain discoverable after roadmap updates. The accepted coverage-tranche operations milestone **v10.22**, its **multi-batch tranche operations** capability, and historical migration marker `0032_initial_rule_assertions` remain preserved programme records. They are traceability markers, not current execution authority.

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

Human Owner / Board remains supreme authority. CAN DO remains distinct from MAY DO. Capability, authority, autonomy and risk remain separate. Memory and conversation cannot silently become truth/authority. External runtimes remain replaceable. Canonical truth cannot silently inherit model error. Consequential effects remain reconstructable. Autonomy is earned capability-by-capability. The visual organization represents real organizational state: **the organization causes the animation, animation never silently causes the organization**. UI interaction is not a business action without an explicit command boundary.

---

## 5. Product surfaces

Global Mobility AIOS develops as five connected surfaces: **Mobility**, **Operator/Cockpit**, **Living HQ**, **Board/Governance**, and **Learning & Optimization**.

Mobility provides the client journey across Overview, My Case, Documents, Timeline and Messages. Operator is the professional command surface. Living HQ is the flagship spatial representation of the actual AI organization. Board/Governance handles consequential decisions, escalations, authority, risk and exceptions. Learning & Optimization uses measured outcomes to propose improvements without silently rewriting governance.

---

## 6. Current product state

Mobility and Operator visual convergence are sealed.

Living HQ Phase 13A–13F semantics are sealed. The stable redesign base after 13F is merge `310b73a2eec63f9f0b2f3a0d53752867c1097359`.

The first Phase 13G closure candidate, PR #146, passed automated proof but **failed explicit Owner visual acceptance**. The Owner determined that the visible result still looked materially like the previous creature/card/square-room system and did not deliver the required modern-office transformation. PR #146 therefore remains Draft and must not be merged in that rejected visual state.

This rejection is an acceptance result, not a cosmetic preference to bypass. Phase 13 is not sealed.

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

Walking, conversations, coffee breaks, room entry, handoffs or richer animation may only be promoted when relevant canonical semantics exist; they cannot be invented for entertainment.

---

## 7. Immediate execution programme — Phase 13 Living HQ flagship convergence

### 13A — Spatial focus polish — SEALED

Overview / Departments / Chambers / Infrastructure focus modes, contextual HUD, presentation-only emphasis, explicit no-authority/no-presence claims and desktop/phone proof.

### 13B — Entity focus inspector — SEALED

Read-only department / employee / room / smart-object inspection from governed render-model data. Permanent contract: `Selection changes view focus only; it cannot mutate AIOS.`

### 13C — Contextual drill-down — SEALED

Richer read-only inspectors with lineage/evidence/authority posture while local selection remains separate from canonical commands.

### 13D — Canonical handoff visualization — SEALED

Handoff visuals originate only from durable canonical handoff/activity semantics. Shared Mission membership never implies transfer.

### 13E — Governed conversation visualization — SEALED

Semantic conversation cues originate only from canonical communication/activity. Decorative social behavior cannot imply work.

### 13F — Mission-room and Board escalation convergence — SEALED

Mission/WorkItem/blocker/risk/decision/human-action context is surfaced from canonical state without fake occupancy or inferred Board action. Accepted merge: `310b73a2eec63f9f0b2f3a0d53752867c1097359`.

### 13G — Final visual acceptance + companion reconciliation — BLOCKED BY OWNER VISUAL REJECTION

The initial 13G candidate demonstrated that green CI alone does not satisfy the flagship visual requirement. Closure is split into an architectural correction followed by final acceptance.

### 13G.1 — Architectural World Redesign — ACTIVE

**Outcome:** the Living HQ must read at first glance as a premium contemporary digital-company headquarters, not a dashboard/card grid whose boxes are styled as rooms.

The Owner-approved visual direction is one continuous architectural office world with believable depth, circulation, glass partitions, timber/stone/carpet/metal material language, real workplace furniture, planting, lighting, windows, open-plan work areas, specialist glass rooms, executive Board space, miniature employees integrated into the environment, and restrained world-anchored AIOS HUDs.

#### Non-negotiable five-second acceptance test

Without reading labels, a first-time viewer must perceive a modern premium headquarters, one connected workplace, open working areas plus glass specialist/executive spaces, miniature employees belonging inside the environment, and a live digital organization.

If the first impression is cards, square rooms, tiles, panels, game board, pixel tower, neon sci-fi pods, repeated creatures or conventional admin dashboard, the candidate fails regardless of automated test status.

#### Desktop composition target

- left/foreground: AIOS identity integrated into architecture or a real display surface;
- centre foreground/midground: Operations / Mission open-plan floor with desk clusters, monitors, chairs, planting and miniature employees;
- centre/background: Evidence Lab behind glass with focused analysis language;
- centre-right: Technology/build cluster integrated into the open floor;
- right/background: premium glass Board/Executive room with genuine conference table and executive seating;
- right/foreground: lounge/shared workplace fabric;
- throughout: circulation, ceiling/lighting, glazing/windows, floor/material transitions and foreground/midground/background depth.

Functional zones are spatial parts of one HQ. They must not be standalone rectangular UI cards masquerading as architecture.

#### Character target

The repeated generic creature/card presentation is rejected. Replace it with an original miniature workforce system differentiated through silhouette, face/head/hair, wardrobe, accessories, workstation context and restrained department identity. CEO, Technology/CTO, Regulatory/Evidence and Operations archetypes must be recognisable before reading role text. Characters belong inside desks/chairs/zones rather than floating avatar cards.

#### HUD target

World first, HUD second. Use compact contextual overlays anchored to zones/entities. Rich inspectors appear on selection. The architecture must remain understandable when labels/HUDs are mentally removed.

#### 13G.1A — Continuous architectural shell — NEXT

Replace the visible three-room/card axis with one continuous office-world shell. Establish elevated camera/perspective, continuous floor, architectural ceiling and lighting, windows/glazing, circulation, major glass partitions, material zones and depth layers. Preserve canonical room keys and semantic DOM contracts even when visual geometry changes completely.

**Gate:** screenshot clearly reads as one modern office before detailed furniture/character polish.

#### 13G.1B — Workplace interiors

Build Operations/Mission, Technology, Evidence, Board and shared/lounge interiors with distinct furniture, equipment, material and lighting identities.

**Gate:** each zone is recognisable spatially without relying on large labels.

#### 13G.1C — Miniature workforce art system

Replace the rejected creature/card presentation and integrate differentiated miniature workforce characters into the office environment while preserving M.4.1 truth mapping.

**Gate:** CEO / Technology / Regulatory-Evidence / Operations archetypes are distinguishable without role text and no floating-avatar-card impression remains.

#### 13G.1D — World-anchored governed intelligence

Recompose existing spatial focus, inspector, handoff, conversation, Mission/blocker/evidence/Board context as restrained world-anchored cues and contextual drill-down.

**Gate:** governed state remains discoverable while architecture stays visually dominant.

#### 13G.1E — Cinematic depth and supported life

Tune lighting, glass, material separation, depth, shadows, focus transitions and allowed ambient/state-driven motion. Monitor glow, light sweep and supported state pulses are allowed; fake walking/talking/occupancy/work are not.

**Gate:** desktop has foreground/midground/background depth and no neon-box/pixel-tower appearance.

#### 13G.1F — Mobile HQ composition

Create a dedicated HQ viewport plus spatial focus/drill-down model. Do not stack a desktop room/card grid vertically.

**Gate:** phone remains intentional, spatial, readable, touch-safe and free of horizontal body overflow.

#### 13G.1G — Owner visual proof

Generate exact-head desktop and phone screenshots before expensive final sealing. Owner visual acceptance is mandatory.

**Gate:** explicit Owner acceptance. Green CI cannot override visual rejection.

### 13G.2 — Final acceptance and companion reconciliation

Only after 13G.1G passes, reconstruct useful closure work from Draft PR #146 onto the accepted architectural base. Run Repository Policy, targeted Living HQ browser proof, V12 Production Proof, Q17 performance and Q18 asset profiling on one exact candidate head. Inspect desktop/phone/Q17/Q18 artifacts. Reconcile ROADMAP, README, migration/final checklist and companion specs. Merge only the exact accepted head and verify the actual merge commit/tree/parents/signature.

### Phase 13 permanent visual truth boundary

The architectural correction changes presentation, not canonical organization semantics. Room presentation does not assert occupancy. Character placement does not assert physical presence or employee location. Mission-room presentation does not route work. Evidence Lab presentation does not certify evidence. Board-room presentation does not constitute Board action. Handoff and conversation cues remain canonical-only. Local spatial selection remains view state only. No visual element may create work, evidence, decision, authority, presence, occupancy or availability.

---

## 8. Post-redesign priority — Autonomous Global Regulatory Intelligence

After redesign completion, strengthen Global Intelligence into a high-autonomy **Global Immigration Intelligence Department** maintaining visa/residence/work/study/family/business/talent/digital-nomad/permanent-residence knowledge across jurisdictions with minimal routine human intervention while keeping legal/publication authority evidence-driven.

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

Human specialists remain the exception path for genuine ambiguity, authoritative contradiction, insufficient evidence, novel/high-consequence interpretation or unresolved machine disagreement. LLM confidence is diagnostic metadata, never legal authority. The primary KPI is **correct autonomous throughput at an acceptably tiny false-promotion rate**, not raw automation percentage.

---

## 9. Platform capability expansion

### Phase 14 — AIOS Native Skills Registry

Portable skill definitions, validation, discovery metadata, curated role bundles and workflow recipes with durable ID/version, compatible roles, allowed/denied tools, mutation classification, authority tier, evidence behavior, risk, budget, output contract, tests and revocation. Learned/imported capability never implies authority acquisition.

### Phase 15 — Agent Lifecycle Governance Hooks

Governed pre/post tool-use, tool failure, permission request/denial, task/subagent/session lifecycle, compaction and cancellation signals through existing AIOS boundaries.

### Phase 16 — Runtime Reliability & Cost Intelligence

Gap-audit routing, budgets, loop/stall detection, cancellation/circuit breakers, bounded retry, checkpoint/recovery, governance-preserving context compaction, observability and provider quality history before adoption.

### Phase 17 — Agent Security Assurance

Agentic-AI threat modelling, identity/authorization, secure tool invocation, prompt-injection boundaries, skill/tool supply-chain integrity, provenance integrity, adversarial regression and incident response.

### Phase 18 — Enterprise Governance, Risk & Compliance

Risk linkage, policy/control ownership, audit-ready evidence export, approval/exception lineage, incident tracking, capability authorization reviews and justified standards mappings.

### Phase 19 — Organizational Learning & Optimization

Measure provider/model performance, employee/skill success and corrections, repeated blockers, source reliability, cost per successful outcome, routing/handoff quality, escalation, decision reversal and time-to-resolution. Learning begins as proposals.

### Phase 20 — Earned Autonomy

Grant autonomy capability-by-capability with bounded scope, authority ceiling, risk class, budget, rollback, audit, quality threshold, revocation and periodic review.

### Phase 21 — External Interoperability

Evaluate MCP, A2A-style interoperability, coding agents, enterprise connectors, local/open models and sandboxed execution only when product need requires them, with identity/authority/provenance/failure boundaries.

### Phase 22 — Production Operations & Scale

Deployment architecture, justified PostgreSQL/Redis/worker scaling, backup/restore, disaster recovery, secrets lifecycle, observability/alerting, load testing, privacy/retention, tenancy/isolation, release/rollback, runbooks and cost controls.

---

## 10. External repository adoption ledger

Repository research is a donor programme, not an architecture vote.

Adopt selectively: `awesome-ai-organization` for organizational coverage/roles/workflow/HITL/audit/cost-quality patterns; `agency-agents` for role design and measurable specialist responsibilities; `munder-difflin` for live-office legibility, avatar representation, handoff/status visualization, human gates, budgets/circuit breakers/isolation concepts without importing its file-hive runtime or fake activity; `antigravity-awesome-skills` for skill-format/discovery ideas; `open-agent-sdk-typescript` for lifecycle/permission/budget/cancellation/subagent concepts; PraisonAI for gap-audited routing/guardrails/telemetry/recovery/loop detection/compaction/interoperability; `career-ops` for bounded workflow/canonical-status/human-final-decision/browser-proof patterns.

Automaton is constrained to protected rules, audited versioned self-change, heartbeat/resource degradation and rate-limit concepts; sovereign self-replication, autonomous self-funding, unrestricted self-modification and no-human-operator governance are rejected. MiroFish may inform graph/persona/memory/simulation visualization, but simulation is not organizational truth and AGPL code is not copied without an explicit licensing decision.

---

## 11. UI / UX direction

AIOS should feel like a premium operating system for a living digital company rather than an admin template: modern, spatial and information-dense without clutter.

For Living HQ specifically, **environment-as-interface is now mandatory**. The architectural office world is the hero surface. HUDs and inspectors augment it. The Owner-approved direction is premium contemporary office architecture with open-plan workplace, glass specialist/executive rooms, warm timber, neutral stone/concrete/textile, matte metal, plants, real furniture, windows, architectural lighting and miniature employees integrated into the scene.

Old content inside V2 chrome is not a completed redesign. Generic SaaS/AI-slop output, repeated creatures, room cards, pixel towers and cosmetic relabeling are rejected even when CI is green.

Motion communicates supported state. Decorative ambience cannot imply false work, presence or authority. Every flagship slice considers desktop/phone, keyboard, reduced motion, forced colors/high contrast, readable fallback, predictable focus semantics and bounded rendering cost.

---

## 12. Engineering and proof discipline

**Exact-head acceptance:** only the intended candidate head can be accepted.

**Bounded PRs:** one semantic/visual purpose per PR.

**Stale-branch rule:** reconstruct dependent work onto newly sealed bases.

**Failure classification:** distinguish deterministic product regression, literal/source-contract regression, browser flake, external dependency failure, backend/database failure and policy/hygiene failure before changing code.

**Efficient proof:** iterate narrowly; seal broadly. For 13G.1A–F, use targeted build/browser/screenshot proof and inspect visual artifacts before expensive final V12 sealing. After Owner visual acceptance, full exact-head gates remain mandatory.

**Truth-contract compatibility:** established literal truth statements may be CI-enforced and must remain discoverable.

---

## 13. What we deliberately do not build

AIOS does not become a generic multi-agent clone, ungoverned swarm, bulk-imported prompt catalogue, crypto/self-replicating organism, simulated office inventing human-like activity, security exploitation toolkit, all-purpose GRC suite, unnecessary model-hosting project, or second canonical state hidden in frontend/renderers/memory/external runtimes.

---

## 14. Immediate order of work

```text
1. Phase 13G.1A — replace room-card geometry with the continuous architectural shell.
2. Inspect desktop visual proof; reject immediately if it still reads as boxes/cards.
3. Phase 13G.1B — build distinct Operations, Technology, Evidence, Board and shared interiors.
4. Phase 13G.1C — replace repeated creature presentation with integrated miniature workforce art.
5. Phase 13G.1D — anchor governed intelligence to the world without creating a dashboard farm.
6. Phase 13G.1E — establish cinematic depth, materials, lighting and supported environmental life.
7. Phase 13G.1F — build intentional mobile HQ viewport + drill-down.
8. Phase 13G.1G — obtain explicit Owner desktop/phone visual acceptance.
9. Phase 13G.2 — reconstruct final reconciliation, run exact-head full proof, reconcile docs and seal Phase 13.
10. Begin Autonomous Global Regulatory Intelligence only after redesign is genuinely sealed.
11. Build Native Skills Registry and lifecycle governance where regulatory/employee capability work requires them.
12. Establish security, reliability, learning and earned-autonomy foundations before consequential expansion.
13. Add interoperability and production scale as concrete product dependencies require.
```

---

## 15. Definition of destination

Global Mobility AIOS is successful when the Human Owner can open the product and understand a real, continuously operating AI organization without reading logs or trusting theatrical simulation.

The system should make it possible to see what the company is doing, inspect why it is doing it, trace what evidence and authority produced each consequential outcome, intervene when necessary, replay what happened, measure cost and quality, and safely grant more autonomy where performance earns it.

For the Living HQ flagship, success additionally means the organization is perceived as a believable premium modern headquarters before it is perceived as software chrome. The environment makes canonical organizational state legible; it never invents that state.

The long-term advantage is not the number of agents, models, animations or integrations. It is the combination of capable AI employees, durable organizational memory, canonical evidence and decisions, explicit authority, visible organizational state, reliable execution, measured learning and earned autonomy.

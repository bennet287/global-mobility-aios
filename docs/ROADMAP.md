# Global Mobility AIOS — Master Product Roadmap

**Roadmap generation:** 2026.09 — post-Phase-13G autonomous-operations reset
**Date:** 2026-09-12
**Roadmap authority:** this file is the master WHAT / WHEN / WHY scheduler for Global Mobility AIOS.
**Current sealed redesign baseline:** Phase 13G merge `2ffa8f2ba10a82e3dc9dad031b9869c74c33d543`
**Active programme:** Autonomous Global Regulatory Intelligence — RI.A1 verification routing
**Active implementation:** Draft PR #148 — `feature/autonomous-global-regulatory-intelligence`
**Code migration head:** `0081_capability_autonomy_evidence_evaluation_policy`

<!-- CURRENT_MIGRATION_HEAD: 0081_capability_autonomy_evidence_evaluation_policy -->

> **Product necessity pulls technology into the project. Technology does not push the product around.**

> **Aggressive capability research. Conservative production authority.**

> **Automate evidence, routing, checking, preparation and reversible execution aggressively. Automate consequential truth or external commitments only when stronger evidence and policy gates independently justify it.**

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
9. `docs/aios-v2/AIOS_V2_PHASE_13G1_ARCHITECTURAL_WORLD_REDIRECT_2026-09-11.md` — historical Owner rejection and architectural redirect record.
10. `docs/aios-v2/AIOS_V2_PHASE_13G1_VISUAL_OUTCOME_EXECUTION_PLAN_2026-09-11.md` — historical execution record for the accepted Living HQ correction.
11. `docs/aios-v2/AIOS_V2_PHASE_13G2_CLOSURE_RECONCILIATION_2026-09-12.md` — Phase 13G acceptance/closure evidence and permanent truth boundary.

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

### Automation safety law

Every autonomous capability must declare all of the following before production promotion:

- canonical inputs and freshness requirements;
- permitted outputs and mutation class;
- evidence/provenance requirements;
- authority ceiling and human-only boundaries;
- idempotency/retry behavior;
- timeout, cancellation and circuit-breaker behavior;
- rollback/reconciliation behavior;
- audit/contribution emission;
- failure and disagreement routing;
- measurable quality threshold and revocation condition.

No capability may earn authority merely because a model is capable of performing it.

---

## 5. Product surfaces

Global Mobility AIOS develops as five connected surfaces: **Mobility**, **Operator/Cockpit**, **Living HQ**, **Board/Governance**, and **Learning & Optimization**.

Mobility provides the client journey across Overview, My Case, Documents, Timeline and Messages. Operator is the professional command surface. Living HQ is the flagship spatial representation of the actual AI organization. Board/Governance handles consequential decisions, escalations, authority, risk and exceptions. Learning & Optimization uses measured outcomes to propose improvements without silently rewriting governance.

---

## 6. Current product state

Mobility and Operator visual convergence are sealed.

Phase 13 Living HQ flagship convergence is sealed and merged. The authoritative Phase 13G merge is:

`2ffa8f2ba10a82e3dc9dad031b9869c74c33d543`

Phase 13G replaced the rejected room/card direction with the accepted continuous premium headquarters world, integrated miniature workforce, real-time governed organization-state presentation, intentional phone composition and final exact-head proof. The earlier PR #146 rejection remains historical evidence explaining why visual acceptance cannot be reduced to green CI.

Permanent Living HQ truth boundaries remain:

```text
presentationOnly  = true
presenceClaimed   = false
locomotionAllowed = false
```

Canonical handoffs/conversations/governance events may drive presentation only when their durable records exist. Character placement does not assert physical presence. Room presentation does not assert occupancy. Selection remains view state. Living HQ does not create work, evidence, authority or decisions.

The active programme is now **Autonomous Global Regulatory Intelligence**. Draft PR #148 begins RI.A1 by continuously routing detected regulatory changes into `machine_verification_candidate` or `human_exception` while explicitly preserving `canonical_write_allowed = false`.

---

## 7. Phase 13 Living HQ flagship convergence — SEALED

### 13A–13F — semantic and governance foundation — SEALED

Spatial focus, entity inspection, contextual drill-down, canonical handoff visualization, governed conversation visualization, Mission/Board convergence and their truth boundaries are accepted.

### 13G.1A–13G.1G — architectural/live-world redesign — SEALED

Continuous architectural shell, workplace interiors, miniature workforce art, real-time state binding, canonical event reactions, ambient/cinematic depth and mobile HQ composition are accepted.

### 13G.1H — Owner visual/live-behavior acceptance — SEALED

Owner acceptance was explicitly recorded against accepted visual/live behavior. Green CI alone remains insufficient for future flagship visual acceptance.

### 13G.2 — closure reconciliation — SEALED

Final candidate `199c6ee4771d5bbac1a5b1c4aba84947392f2af6` passed exact-head Repository Policy, Living HQ Browser Proof and V12 Production Proof. Phase 13G was merged as `2ffa8f2ba10a82e3dc9dad031b9869c74c33d543`.

### Phase 13 permanent visual truth boundary

The architectural/live-world implementation changes presentation, not canonical organization semantics. Room presentation does not assert occupancy. Character placement does not assert physical presence or employee location. Mission-room presentation does not route work. Evidence Lab presentation does not certify evidence. Board-room presentation does not constitute Board action. Handoff and conversation cues remain canonical-only. Local spatial selection remains view state only. The real-time rule is one-way: canonical organization state may drive Living HQ presentation; Living HQ animation may never silently write canonical organization state.

---

## 8. Active programme — Autonomous Global Regulatory Intelligence and Safe AIOS Automation

### 8.1 Programme outcome

The goal is not merely to add more regulatory agents. The goal is to turn AIOS into a **self-maintaining, self-checking, evidence-grounded global mobility operating organization** whose routine work is automated end-to-end while ambiguity, legal interpretation and consequential external commitments remain safely governed.

The target regulatory loop is:

```text
official-source discovery / known-source monitoring
        ↓
authority + trust-root validation
        ↓
immutable SourceSnapshot / parser evidence
        ↓
change / new-program discovery
        ↓
deterministic evidence routing
        ↓
independent machine verification + falsification
        ↓
contradiction / source hierarchy / temporal analysis
        ↓
structured rule or pathway proposal
        ↓
impact graph + regression across dependent products/cases
        ↓
policy-governed promotion OR human exception
        ↓
continuous freshness / drift / rollback / reassessment
```

The broader AIOS automation loop is:

```text
OBSERVE
  → COLLECT EVIDENCE
  → VERIFY
  → CLASSIFY RISK
  → PREPARE OR EXECUTE WITHIN AUTHORITY
  → AUDIT / CONTRIBUTE
  → RECONCILE OUTCOME
  → LEARN FROM OVERRIDES / FAILURES
```

No LLM output is canonical merely because it sounds plausible. **No evidence → no regulated factual claim.**

### 8.2 Principal bottlenecks to solve before increasing autonomy

#### Bottleneck A — trust-root coverage

A monitoring system is only as global as its certified authority/source graph. Known-source automation does not discover ministries, renamed portals, gazettes, APIs or newly launched programme pages by itself.

**Resolution:** build discovery separately from certification. AIOS may discover and score candidate sources automatically, but a candidate cannot become a trust root merely because a model thinks the domain looks official. Certification requires jurisdiction/authority linkage, HTTPS/domain checks, trusted-source cross-links or other deterministic provenance, versioned review and explicit revocation/supersession behavior.

**Quality gate:** source-discovery recall can increase without increasing false certification. Trust-root false positives are a release-blocking defect.

#### Bottleneck B — human-review throughput becoming the new system bottleneck

If every detected change creates mandatory manual review, monitoring scales faster than professional review capacity and the queue eventually becomes stale.

**Resolution:** split the pipeline into machine-verifiable routine changes versus genuine exceptions. Automate evidence collection, diffing, classification, cross-source checking, contradiction search, effective-date parsing, dependency impact and review-pack preparation. Reserve human attention for unresolved ambiguity/high consequence rather than routine inspection.

**Quality gate:** measure exception rate, queue age, reviewer time per resolved item, machine-candidate precision and false-promotion rate. Never optimize raw automation percentage at the expense of correctness.

#### Bottleneck C — stale truth that remains apparently authoritative

A verified fact can become wrong without a publication event inside AIOS if the source disappears, changes structure, becomes inaccessible or stops being monitored.

**Resolution:** freshness SLAs by evidence class, source health scoring, stale/degraded states, confidence decay, alternate-source retrieval, retry/backoff, and explicit quarantine when freshness cannot be restored.

**Quality gate:** stale evidence cannot retain the same authority presentation as freshly verified evidence.

#### Bottleneck D — regulatory change detection without downstream impact closure

Detecting a rule change is low value if affected pathways, document requirements, assessments, timelines and active cases remain based on the old rule.

**Resolution:** dependency/impact graph with immutable historical assessments. New evidence creates reassessment candidates; it never rewrites history. Rank affected active cases by urgency/materiality and create governed WorkItems automatically.

**Quality gate:** every published/superseded rule can answer which downstream objects depend on it and whether each object is current, unaffected, pending reassessment or resolved.

#### Bottleneck E — hallucination entering through interpretation rather than retrieval

Even perfect source retrieval does not prevent a model from over-interpreting a sentence, missing an exception or merging two legal concepts.

**Resolution:** separate `fact`, `inference`, `recommendation`; require claim-level provenance; deterministic numeric/date/currency/unit parsing; source-text anchors; independent verifier/falsifier; model disagreement detection; explicit unresolved status when interpretation cannot be grounded.

**Quality gate:** model confidence is never used as legal authority. Evidence confidence is derived from source authority, freshness, agreement, parser certainty, completeness and contradiction status.

#### Bottleneck F — queue explosion and autonomous-work loops

As regulatory, document, case, engineering and organization automations begin generating WorkItems for one another, the system can create duplicate work, retry storms, recursive handoffs and low-value queue growth.

**Resolution:** idempotency keys, deduplication windows, causal lineage, per-capability budgets, dependency-aware scheduling, retry classification, max-depth/loop detection, circuit breakers, cancellation and backpressure. CEO prioritization routes existing governed work; it does not invent infinite work.

**Quality gate:** every automatically created WorkItem has a causal source, deduplication key, owner, termination condition and bounded retry/hand-off path.

#### Bottleneck G — external actions are qualitatively riskier than internal preparation

Sending, submitting, booking, deleting, paying or modifying external systems creates commitments that are harder to reverse than internal analysis.

**Resolution:** separate internal automation from external mutation. Drafting/preparation may reach higher autonomy earlier. External action requires connector identity, explicit authority, precondition validation, dry-run/preview where possible, idempotency, receipt/reconciliation and an escalation path for partial failure.

**Quality gate:** no external action is considered successful until AIOS has reconciled the external receipt/state, not merely because a connector call returned 200.

#### Bottleneck H — automation that cannot prove it is improving quality

More autonomous actions can quietly increase hidden error rate or cost.

**Resolution:** every promoted capability gets outcome telemetry: success, override, correction, rollback, false-positive/negative where measurable, latency, cost, reviewer effort saved and incident rate. Promotion and demotion are evidence-driven.

**Quality gate:** autonomy is revocable and periodically reviewed; promotion requires measured performance on the exact capability and risk class.

### 8.3 Autonomy ladder — standard across AIOS

Autonomy is assigned per capability, not per employee or globally.

| Level | Meaning | Typical examples |
|---|---|---|
| **L0 — Observe** | read/analyse only | source health, production telemetry |
| **L1 — Recommend** | propose/draft | legal-change interpretation, client advice draft |
| **L2 — Prepare** | create governed internal artifacts/work | WorkItems, review packs, reassessment candidates |
| **L3 — Execute reversible** | safe/idempotent internal or reversible action | scheduled source retrieval, deterministic classification, reminders |
| **L4 — Execute governed** | consequential action only under strict evidence/policy gates | future narrow VerifiedRule promotion where independently machine-verifiable |
| **L5 — Human-only / explicit authorization** | irreversible/high-liability/external commitment | government submission, destructive record action, unresolved legal interpretation |

Promotion between levels requires measured evidence and a revocation path. There is no global “autonomous mode.”

### 8.4 Regulatory Intelligence execution plan

#### RI.A1 — Evidence-aware verification routing — ACTIVE / DRAFT PR #148

Continuously evaluate pending `RegulatoryChange` records and route them into `machine_verification_candidate` or `human_exception` using existing source certification, jurisdiction/authority consistency, immutable snapshot provenance, structured-program evidence, deterministic classification evidence and materiality.

Permanent RI.A1 boundary: `canonical_write_allowed = false`. RI.A1 cannot approve changes, publish/supersede `VerifiedRule`, mutate pathways or rewrite client assessments.

**Exit gate:** deterministic routing tests; idempotent audit behavior; no canonical-write path; exact-head Repository Policy + backend/PostgreSQL regression + V12 production proof.

#### RI.A2 — Independent machine verification and falsification

For RI.A1 candidates, construct a machine-verification packet from evidence stronger than the proposer: secondary authoritative source where available, independent extraction/pass, effective-date checks, numeric/date/currency/unit validation, source-scope/domain match, contradictory active-rule search and adversarial “what would make this interpretation wrong?” checks.

The verifier must not share an unexamined free-form conclusion with the proposer. Shared raw evidence is allowed; shared reasoning is not treated as independent proof.

**Exit gate:** known positive/negative/contradictory fixtures; evidence packet is reproducible; unresolved disagreement routes to human exception; no automatic publication yet.

#### RI.A3 — Temporal rule lifecycle and contradiction watchdog

Continuously detect overlapping effective periods, multiple active rules for the same semantic key, superseded rules still referenced, future-effective changes, retired programmes, broken provenance, unavailable trust roots and source hierarchy conflicts.

Create a durable regulatory-integrity incident rather than silently selecting a winner.

**Exit gate:** contradiction fixtures cannot silently resolve; temporal replay can explain what rule was authoritative at a historical timestamp.

#### RI.A4 — Dependency impact propagation and reassessment orchestration

Connect published/superseded regulatory truth to affected `MobilityPathwayVersion`, document requirements, eligibility/comparison assessments, timelines and active cases. Preserve historical outputs; create explicit reassessment candidates and prioritized WorkItems instead of rewriting old results.

Priority should account for submission/expiry deadline, regulatory materiality, client impact and evidence confidence.

**Exit gate:** every test rule change produces a complete affected-object inventory with zero silent historical mutation.

#### RI.A5 — New-program discovery and pathway incubation

Monitor complete authority catalogues, sitemaps/APIs/gazettes and certified page families for programmes absent from AIOS. Build a candidate programme dossier: authority, source, start/effective dates, target population, requirements, fees, quota/closure state, evidence and unresolved fields.

New programme discovery is not publication. AIOS must prove the programme exists and that the evidence is within a certified scope before pathway compilation.

**Exit gate:** known new/renamed/retired programme fixtures; duplicate programme suppression; uncertain identity routes to exception.

#### RI.A6 — Structured rule/pathway compiler

Compile verified assertions into typed rules/pathway-version proposals rather than embedding free-form model prose in business logic. Validate schema, units, threshold semantics, conditions/exceptions, document dependencies and temporal scope.

**Exit gate:** deterministic compiler tests and round-trip explanation from structured rule back to exact evidence anchors.

#### RI.A7 — Controlled machine promotion pilot

Only after RI.A1–A6 evidence exists, permit a very narrow class of low-ambiguity changes to reach L4: e.g. deterministic fee/threshold/date/program-status changes where certified authoritative evidence agrees, no contradiction exists, parser confidence is high, effective date is explicit, downstream regression passes and rollback is defined.

No interpretive legal rule starts here.

**Exit gate:** shadow-mode comparison against human decisions; predefined minimum sample; zero critical false promotions; automatic demotion/kill-switch; complete audit/replay.

#### RI.A8 — Continuous freshness, drift, quarantine and rollback

Establish source/fact freshness SLAs, parser-drift detection, schema-change detection, source disappearance handling, confidence decay, quarantine states and recovery workflows. Machine-promoted truth must be reversible through governed supersession/rollback rather than destructive history edits.

**Exit gate:** stale/unreachable/parser-broken fixtures visibly degrade authority and cannot continue as silently “fresh.”

### 8.5 Cross-project automation programme

Regulatory Intelligence is the first proving ground. The same safety architecture should then be applied to the rest of AIOS.

#### AUTO.DOC — Document autonomy

```text
upload
 → malware/content safety boundary
 → classify document
 → extract fields
 → normalize
 → deterministic field validation
 → cross-document consistency
 → expiry/legalization/translation checks
 → requirement mapping
 → confidence routing
 → human exception only for uncertain/high-risk fields
```

High-confidence extraction may become canonical only when the field type has deterministic validators and calibrated quality evidence. OCR/model confidence alone is insufficient.

**Key optimization:** human reviewers should inspect uncertain fields and contradictions, not reread every document.

#### AUTO.CASE — Case readiness, deadlines and reassessment

Continuously calculate operational case readiness from canonical requirements/evidence; generate missing-document/blocker WorkItems; track expiry, authority and renewal deadlines; escalate according to urgency; create reassessment tasks after rule changes.

AIOS may assert operational readiness. It must not claim authority approval probability as legal fact.

#### AUTO.COMMS — Grounded communications

Generate client/operator messages from a deterministic fact payload containing canonical case status, verified documents, missing items, deadlines and actions. LLMs perform wording/translation, not factual discovery. Numeric/date/entity invariants are checked after generation and before send.

Start at draft-only. Promote selected low-risk reminders only after send/reconciliation/override evidence is strong.

#### AUTO.ORG — Event-driven organizational work

Canonical events create bounded WorkItems automatically:

- regulatory change → Compliance/Regulatory work;
- affected pathway/case → Mobility/Operations work;
- document gap/expiry → Case Operations work;
- production failure → CTO/Engineering incident;
- security anomaly → Security incident;
- recurring product-quality regression → Product/QA work.

AI employees consume governed queues with explicit tools/outputs/authority ceilings. They do not free-run by inventing tasks because they “seem useful.”

#### AUTO.HANDOFF — Real departmental handoffs

When one governed WorkItem reaches an explicit terminal/transfer condition, create the next department's WorkItem with causal lineage, acceptance criteria and evidence bundle. This later allows Living HQ to visualize genuine cross-department activity rather than decorative movement.

#### AUTO.QA — Autonomous quality engineering

Every code/configuration change should progress through change-class-aware proof: unit/integration, schema/migration, policy, API contracts, frontend type/build, browser proof, accessibility, screenshot regression and performance where relevant. Classify failures before retrying or editing code. Known infrastructure flakes may be retried; deterministic product failures may not be papered over by reruns.

Add AI-assisted log/screenshot interpretation only on top of deterministic proof.

#### AUTO.OPS — Production reliability automation

Monitor API/database latency, worker queues, failed tasks, retry storms, source-monitor failures, provider errors, token/cost anomalies and connector reconciliation failures. Automatically create incidents, gather evidence, correlate deployments and recommend rollback. Automatic rollback should begin only in reversible/staging scopes and later graduate by evidence.

#### AUTO.MODEL — Cost/quality-aware model routing

Use deterministic code whenever deterministic code is sufficient. Route extraction/classification/synthesis to the cheapest model/provider meeting measured quality for that capability. Track provider quality history, latency, cost and failure rate. High-risk disagreement invokes independent verification rather than simply a more expensive single model.

#### AUTO.LEARN — Evidence-based process improvement

Measure human override/correction, time-to-resolution, repeated blockers, false escalations, retry causes, handoff quality and cost per successful outcome. AIOS may propose changed thresholds/routing/skills, but learning begins as a proposal and must not silently alter authority policy.

### 8.6 Programme-wide anti-hallucination contract

All regulated or operationally consequential claims must be representable internally as:

```text
claim
claim_kind = fact | inference | recommendation
source_id / source_snapshot_id where applicable
verified_rule_id / pathway_version_id where applicable
effective_at / valid_at
input profile or case version
verification status
contradiction status
freshness status
evidence-derived confidence
generated_at
```

For regulated facts, missing provenance means the system must downgrade the statement to an unverified observation or refuse to assert it.

A second model agreeing with the first model is not independent evidence. Independent evidence means independent authoritative source/provenance, deterministic validation, or a separately controlled verification process.

### 8.7 Performance and scale optimization without quality loss

Optimization order is mandatory:

1. eliminate unnecessary LLM calls with deterministic parsing/rules;
2. cache immutable evidence/results by content hash and version;
3. deduplicate causal work before scheduling;
4. batch safe independent retrieval/classification work;
5. parallelize only tasks without ordering/authority dependencies;
6. use cheap models for low-risk structured work after quality calibration;
7. reserve frontier models/ensembles for genuinely hard reasoning;
8. reduce human review by improving evidence packs, not by weakening gates;
9. compact context from canonical summaries/provenance rather than dropping required facts;
10. scale workers/databases only after queue/latency evidence identifies the bottleneck.

Do not optimize by lowering evidence requirements, hiding stale state, skipping regression, suppressing exceptions or turning hard failures into optimistic defaults.

### 8.8 Core programme metrics

The programme should track at least:

- false-promotion rate, especially critical false promotions;
- machine-candidate precision/recall where labelled evidence exists;
- human-exception rate and median/95th-percentile queue age;
- time from official-source change to verified impact closure;
- freshness SLA compliance and stale-truth exposure time;
- percentage of consequential claims with complete provenance;
- downstream reassessment completeness after rule change;
- human minutes per resolved regulatory/document/case item;
- automation retry/loop/circuit-breaker incidence;
- autonomous action rollback/reconciliation failure rate;
- cost per successfully resolved WorkItem/outcome;
- human override/correction rate by capability/autonomy level.

**Primary KPI:** correct autonomous throughput with near-zero critical false promotion. Raw automation percentage is not a success metric.

---

## 9. Platform capability expansion

### Phase 14 — AIOS Native Skills Registry

Portable skill definitions, validation, discovery metadata, curated role bundles and workflow recipes with durable ID/version, compatible roles, allowed/denied tools, mutation classification, authority tier, evidence behavior, risk, budget, output contract, tests and revocation. Learned/imported capability never implies authority acquisition.

### Phase 15 — Agent Lifecycle Governance Hooks

Governed pre/post tool-use, tool failure, permission request/denial, task/subagent/session lifecycle, compaction and cancellation signals through existing AIOS boundaries.

### Phase 16 — Runtime Reliability & Cost Intelligence

Gap-audit routing, budgets, loop/stall detection, cancellation/circuit breakers, bounded retry, checkpoint/recovery, governance-preserving context compaction, observability and provider quality history before adoption. Phase 16 supplies the runtime controls required by AUTO.ORG/AUTO.OPS and higher autonomy levels.

### Phase 17 — Agent Security Assurance

Agentic-AI threat modelling, identity/authorization, secure tool invocation, prompt-injection boundaries, skill/tool supply-chain integrity, provenance integrity, adversarial regression and incident response.

### Phase 18 — Enterprise Governance, Risk & Compliance

Risk linkage, policy/control ownership, audit-ready evidence export, approval/exception lineage, incident tracking, capability authorization reviews and justified standards mappings.

### Phase 19 — Organizational Learning & Optimization

Measure provider/model performance, employee/skill success and corrections, repeated blockers, source reliability, cost per successful outcome, routing/handoff quality, escalation, decision reversal and time-to-resolution. Learning begins as proposals.

### Phase 20 — Earned Autonomy

Grant autonomy capability-by-capability with bounded scope, authority ceiling, risk class, budget, rollback, audit, quality threshold, revocation and periodic review. Phase 20 consumes the evidence generated by the autonomy ladder and programme metrics rather than enabling autonomy by configuration alone.

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

For Living HQ, environment-as-interface remains mandatory and Phase 13G's accepted architectural direction is sealed. Future automation work should become visible through genuine canonical work state, WorkItems, incidents, handoffs, evidence posture and governance events rather than decorative animation.

Motion communicates supported state. Canonical dynamics derive only from real organization records. Decorative ambience cannot imply false work, presence or authority. Every flagship slice considers desktop/phone, keyboard, reduced motion, forced colors/high contrast, readable fallback, predictable focus semantics and bounded rendering cost.

Automation surfaces must make **why**, **evidence**, **authority**, **confidence/freshness**, **what changed**, **what will happen next**, and **how to stop/revoke** understandable without forcing the Owner to inspect logs.

---

## 12. Engineering and proof discipline

**Exact-head acceptance:** only the intended candidate head can be accepted.

**Bounded PRs:** one semantic/visual purpose per PR.

**Stale-branch rule:** reconstruct dependent work onto newly sealed bases.

**Failure classification:** distinguish deterministic product regression, literal/source-contract regression, browser flake, external dependency failure, backend/database failure and policy/hygiene failure before changing code.

**Efficient proof:** iterate narrowly; seal broadly. Use targeted tests/proofs during a slice, then run required exact-head full proof before acceptance.

**Truth-contract compatibility:** established literal truth statements may be CI-enforced and must remain discoverable.

**Shadow mode before consequential autonomy:** capabilities proposed for L4 must first run without canonical/external mutation against real or representative workloads so disagreement/override/error rates are measurable.

**No optimistic fallback:** when evidence or dependencies are missing, consequential workflows must degrade to explicit unknown/blocked/exception states rather than inventing defaults.

**Reconciliation is part of execution:** connector/API calls, retries and asynchronous workers are not complete until their resulting canonical/external state is reconciled.

**Backpressure is a correctness feature:** overload must slow, queue, deduplicate or shed low-priority work rather than silently dropping evidence or lowering gates.

---

## 13. What we deliberately do not build

AIOS does not become a generic multi-agent clone, ungoverned swarm, bulk-imported prompt catalogue, crypto/self-replicating organism, simulated office inventing human-like activity, security exploitation toolkit, all-purpose GRC suite, unnecessary model-hosting project, or second canonical state hidden in frontend/renderers/memory/external runtimes.

We also do not optimize for “maximum autonomy” as a vanity metric. We do not let model agreement substitute for evidence, silently rewrite historical assessments after rules change, certify newly discovered sources automatically, auto-submit government/legal commitments without explicit earned authority, or allow AI employees to create recursive unbounded work because they believe more work might be useful.

---

## 14. Immediate order of work

```text
1. RI.A1 — finish verification-routing proof on Draft PR #148; keep canonical_write_allowed=false.
2. Fix only concrete RI.A1 regressions; obtain exact-head Repository Policy + V12/backend/PostgreSQL proof.
3. Seal RI.A1 before adding publication authority or broad source discovery.
4. RI.A2 — build independent machine verification/falsification packets.
5. RI.A3 — build temporal contradiction/provenance/freshness watchdog.
6. RI.A4 — close the loop from verified rule change to pathway/case reassessment WorkItems.
7. RI.A5 — add new-program/source-family discovery while preserving human-controlled trust-root certification.
8. RI.A6 — compile verified evidence into typed rule/pathway proposals with deterministic regression.
9. Run RI.A7 controlled machine-promotion only in shadow mode first; promote a narrow low-ambiguity class only after measured evidence.
10. RI.A8 — complete freshness/quarantine/rollback lifecycle.
11. In parallel only where dependencies are already mature, begin AUTO.DOC deterministic document routing and AUTO.QA failure classification; do not create competing canonical stores.
12. Build Phase 14–17 platform controls as demanded by the automation slices: skills registry, lifecycle hooks, runtime reliability/cost and security assurance.
13. Expand to AUTO.CASE, AUTO.COMMS, AUTO.ORG and AUTO.OPS after evidence/reconciliation/queue controls are proven.
14. Use Phase 19/20 metrics to earn higher autonomy capability-by-capability; demote automatically when quality degrades.
15. Add interoperability and production scale only when measured bottlenecks justify them.
```

### Workstream parallelization rule

Parallel work is allowed only when two slices do not mutate the same canonical contracts and neither depends on the other's unsealed semantics. Visual polish, deterministic QA tooling or isolated document extraction may proceed beside regulatory work; competing changes to authority, evidence, WorkItem lifecycle or autonomy policy must serialize through one accepted base.

---

## 15. Definition of destination

Global Mobility AIOS is successful when the Human Owner can open the product and understand a real, continuously operating AI organization without reading logs or trusting theatrical simulation.

The system should make it possible to see what the company is doing, inspect why it is doing it, trace what evidence and authority produced each consequential outcome, intervene when necessary, replay what happened, measure cost and quality, and safely grant more autonomy where performance earns it.

The mature product should require humans primarily for strategy, unresolved ambiguity, genuine professional judgment, exceptional/high-consequence decisions and explicit external commitments—not for repetitive retrieval, comparison, data entry, queue routing, regression checking or evidence packaging that machines can perform more reliably.

The long-term advantage is not the number of agents, models, animations or integrations. It is the combination of capable AI employees, durable organizational memory, canonical evidence and decisions, explicit authority, visible organizational state, reliable execution, measured learning and **autonomy that increases only when the system can prove it deserves it**.
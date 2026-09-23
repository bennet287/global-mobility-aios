# Global Mobility AIOS — Master Product Roadmap

**Roadmap generation:** 2026.09 — post-Phase-13G autonomous-operations reset
**Date:** 2026-09-23
**Roadmap authority:** this file is the master WHAT / WHEN / WHY scheduler for Global Mobility AIOS.
**Current sealed redesign baseline:** Phase 13G merge `2ffa8f2ba10a82e3dc9dad031b9869c74c33d543`
**Active programme:** Phase 16 — Runtime Reliability, Metering and Orchestration Foundations
**Current checkpoint:** Phase 16 runtime reliability is sealed through cooperative soft-timeout handling (PR #171, merge `14d7bfdd238ca93a10310541702c216fc9561f4b`) and stale-running reconciliation (PR #173, merge `c4ff75f24801eb52a82da2ac09cc724ffe872534`); explicit AgentRun cancellation is the next bounded runtime slice. System-1/AX evaluation remains recorded by PR #167.
**Code migration head:** `0084_organization_agent_lifecycle`

<!-- CURRENT_MIGRATION_HEAD: 0084_organization_agent_lifecycle -->

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

## 2. Roadmap relationship to repository information architecture

This file owns **WHAT / WHEN / WHY** and cross-programme sequencing. It does not own the engineering cold-start sequence, repository mechanics, a live branch head, or acceptance evidence.

Engineering sessions enter through `AGENTS.md`, which leads through the execution playbook, current project state, this roadmap, task-relevant architecture/specification/ADR material, real code/tests/GitHub proof, and finally the minimal session handoff. Do not treat this roadmap as a requirement to read every companion or historical document before acting.

### Task-scoped companion map

Use only the sources relevant to the selected slice:

- `docs/aios-v2/AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md` — durable product destination, redesign principles, six-system model, and acceptance philosophy.
- `docs/aios-v2/AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md` — durable employee, department, skills, tools, memory, learning, and capability/authority architecture.
- `docs/aios-v2/AIOS_V2_VISUAL_REDESIGN_EXECUTION_DIRECTIVE_2026-09-09.md` — visible-redesign quality law when a task changes material UI/UX or flagship visual behavior.
- `docs/aios-v2/AIOS_V2_EFFICIENT_PROOF_LADDER.md` — proof strategy when a task needs visual/product acceptance planning.
- `docs/aios-v2/AIOS_V2_MIGRATION_AND_FINAL_ACCEPTANCE_CHECKLIST.md` — whole-product migration/final-acceptance inventory when that stage is relevant.
- `docs/aios-v2/AIOS_V2_MASTER_PLAN_EXECUTION_RECONCILIATION_2026-09-08.md` and Phase 13G execution/closure records — dated historical evidence; permanent decisions remain relevant, dated SHA/status snapshots do not become current programme truth.
- `docs/ADR/` and phase-specific decision records — read when the selected slice touches the decision they own.

`docs/aios-v2/README.md` is a companion index for those materials, not a second project-state document.

### Authority and precedence

Repository-wide precedence is defined at the front door/playbook. In short: accepted canonical contracts/sealed decisions outrank stale prose; verified repository/schema/owning-system state proves implementation and live external state; accepted architecture/specification governs its domain; this roadmap schedules unfinished work; `PROJECT_STATE` summarizes the current programme; `SESSION_HANDOFF` is only a recovery pointer.

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

Autonomous Global Regulatory Intelligence RI.A1–RI.A8 is sealed and merged at `341ec1f0268cf483e868e85660978a4fbaac3e15`. Phase 14 — AIOS Native Skills Registry is sealed through its governed skill-assignment boundary. **Phase 15.1 — Governed Agent Lifecycle Foundation** is sealed and merged by PR #156 at `30774751a79e998fe80f648f1e172ab1b75c08d0`. **Phase 15.2 — Governed Lifecycle Transition Services** is sealed and merged by PR #158 at `30e6a9e691f4b82a326b2dc1cb267ef5bb938c35`. Phase 15 runtime hooks are sealed through the real connector and background `AgentRun` boundaries. Lifecycle identity and transitions do not grant authority, permissions, credentials, autonomy, tool access, work assignment or execution rights.

Phase 16.1 runtime provider-usage metering and Phase 16.2 deterministic failure classification/retry policy are sealed. Provider/model/token observations and `estimated_cost_usd` are diagnostic runtime evidence, not billing truth. Retry remains fail-closed: only classified provider transport failures retry. PR #171 seals cooperative AgentRun soft-timeout handling by reusing the existing Celery 240-second soft / 300-second hard limits; soft timeout is terminal and non-retryable. PR #173 seals stale-running reconciliation after the 300-second hard limit plus a 60-second grace window, using existing AgentRun + AuditLog truth and explicitly recording `cause_inferred=false` rather than claiming every stranded run was definitely hard-killed. Explicit AgentRun cancellation remains the next bounded runtime slice. PR #167 records the System-1/orchestration decision: Jev and Laya remain benchmark candidates only; Google AX remains deferred as a possible execution substrate until AIOS owns canonical timeout/cancellation, hard runtime budgets, actual cost metering, circuit breakers and reconciliation. Deterministic AIOS policy remains authoritative. No duplicate runtime state should be created merely to support lifecycle signals.

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

## 8. Autonomous Global Regulatory Intelligence and Safe AIOS Automation — RI.A1–RI.A8 SEALED

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

### 8.4 Regulatory Intelligence execution plan — SEALED

RI.A1 through RI.A8 are implemented and merged as the governed regulatory-intelligence baseline at `341ec1f0268cf483e868e85660978a4fbaac3e15`. The permanent operational boundary remains that machine publication and machine recovery execution stay OFF in production until separately earned and authorized.

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

### Phase 14 — AIOS Native Skills Registry — SEALED

Portable skill definitions, validation, discovery metadata, curated role bundles and workflow recipes with durable ID/version, compatible roles, allowed/denied tools, mutation classification, authority tier, evidence behavior, risk, budget, output contract, tests and revocation. Learned/imported capability never implies authority acquisition.

Phase 14 established the native skill registry, validation and evidence lifecycle, mutation audit, deterministic work-candidate matching and governed skill-assignment gate. Skill records may declare tool and permission requirements but cannot grant credentials, permissions, authority or autonomy.

### Phase 15 — Agent Lifecycle Governance Hooks — SEALED

Governed pre/post tool-use, tool failure, permission request/denial and background task lifecycle signals are sealed through existing AIOS boundaries. Session/subagent/compaction/cancellation signals are admitted only when a real canonical runtime operation exists; signal-only duplicate truth stores remain prohibited.

#### Phase 15.1 — Governed Agent Lifecycle Foundation — SEALED

PR #156 merged exact candidate `3b4ca1e2d2c7f00ebf54f309a6d59dca0d3d9ea3` as `30774751a79e998fe80f648f1e172ab1b75c08d0` after Repository Policy Check #1392 and V12 Production Proof #2022 passed. Migration `0084_organization_agent_lifecycle` establishes an `OrganizationAgent` record with canonical registry lineage, lifecycle status and timestamps. It remains separate from static implementation definitions and execution history, and grants no authority, permissions, credentials, autonomy, tool access, work assignment or execution rights.

#### Phase 15.2 — Governed Lifecycle Transition Services — SEALED

PR #158 merged exact candidate `6dcd1744a3c56bdab231f62bcfa76caf01df866d` as `30e6a9e691f4b82a326b2dc1cb267ef5bb938c35` after Repository Policy Check #1393 and V12 Production Proof #2023 passed. The admin-only service/API enforces the sealed forward lifecycle, serializes competing mutations at canonical `OrganizationAgent` truth, rejects invalid transitions, and commits bounded actor/reason/before/after evidence through the existing `AuditLog` infrastructure. It adds no migration or second lifecycle store and grants no authority, permissions, credentials, autonomy, tool access, work assignment, routing or execution.

#### Phase 15.3 — Governed Connector Runtime Signals — SEALED

PR #161 merged normalized exact candidate `da79e5383d9c714daa67a5ab9b1dc1479bf4e92d` as `2fa80c298642db579c3446c6e825ae220b65522d` after exact-head Repository Policy and V12 Production Proof passed. The existing external-delivery authorization and connector side-effect boundary now emits durable authorization-denial, pre-use, completion and failure evidence. It introduces no permission truth or execution grant, and consequence-tier durability must not be generalized into a database commit before every harmless internal tool call.

#### Phase 15.4 — Background AgentRun Lifecycle Evidence — SEALED

PR #163 merged exact candidate `0e4ed4505aac1fc16c89d706ef4b483c015b0c18` as `3944ddb7a21cd76e92eb3739b4fe95340ff43610` after exact-head Repository Policy and V12 Production Proof passed. The existing Celery/AgentRun path now preserves the real background lifecycle handoff into `pending_review` alongside its existing running, retry/queued and failure evidence. No session, subagent, compaction or cancellation store was invented. Those controls move into Phase 16 runtime reliability and are added only with a canonical operation to govern.

### Phase 16 — Runtime Reliability, Cost Intelligence & Economic Metering

Gap-audit routing, **real-money-equivalent work budgets**, per-work/agent/department cost attribution, loop/stall detection, cancellation/circuit breakers, bounded retry, checkpoint/recovery, governance-preserving context compaction, observability and provider quality history before adoption. Model tokens, paid APIs, tools, compute, retries and attributable human-review cost must be metered from actual provider/runtime evidence where available rather than estimated presentation state.

Current runtime reliability foundation: provider-usage observations are sealed by PR #165; deterministic failure classification and transport-only retry are sealed by PR #166; cooperative soft-timeout handling is sealed by PR #171; and stale-running reconciliation is sealed by PR #173. Explicit AgentRun cancellation is the remaining timeout/cancellation slice before moving to the next Phase 16 runtime control. These controls reuse existing AgentRun/Celery/AuditLog truth and do not create a second execution-state store merely for signals.

Before materially costly production execution, AIOS must expose the authorized budget, current spend and remaining budget to the governed runtime. Budget exhaustion is a hard pause/stop boundary unless a separately authorized allocation is granted. An employee may request additional resources with evidence and an expected completion/value case; it may not grant itself budget, bypass the limit, fabricate a result or treat unused budget as a spending target.

Phase 16 supplies the runtime and economic controls required by AUTO.ORG/AUTO.OPS and higher autonomy levels. **Activity is not a result, and spend is not value.**

### Phase 17 — Agent Security Assurance

Agentic-AI threat modelling, identity/authorization, secure tool invocation, prompt-injection boundaries, skill/tool supply-chain integrity, provenance integrity, adversarial regression and incident response.

### Phase 18 — Enterprise Governance, Risk & Compliance

Risk linkage, policy/control ownership, audit-ready evidence export, approval/exception lineage, incident tracking, capability authorization reviews and justified standards mappings.

### Phase 19 — Organizational Learning, Competency & Economic Outcomes

Measure provider/model performance, employee/skill success and corrections, repeated blockers, source reliability, cost per successful outcome, routing/handoff quality, escalation, decision reversal and time-to-resolution. Add evidence-backed organizational competency and outcome attribution without turning activity into a proxy for productivity.

#### Preflight competency gate

Before materially costly production work, evaluate the WorkItem requirements against the employee's **verified current organizational competency**, not merely a generic skill label: work requirements → capability/skill match → organization-specific competency and freshness/version check → tool/permission/authority prerequisites → estimated cost and authorized budget → READY | GAP | NOT_SUITABLE.

READY may proceed through normal authority/budget gates. GAP routes to bounded reskill/upskill and verification before production spend. NOT_SUITABLE routes/reassigns/escalates rather than forcing an economically irrational training/execution loop. Preflight is capability evidence only: **CAN DO != MAY DO**.

#### Evidence-backed reskilling

A detected gap may create a bounded learning objective using approved sources/material, organization procedures and explicit acceptance criteria. Learning does not become a skill/competency because an agent claims it learned. Promotion requires a versioned competency check, deterministic test or governed evaluation appropriate to the capability, with evidence and freshness/recertification rules. Validated organizational learning should be reusable so the company does not repeatedly pay employees to rediscover the same knowledge.

Production outcomes feed back into competency. Repeated correction/failure may trigger review, remediation, reskilling, restriction or retirement even when an older competency test passed. Failure attribution must distinguish employee capability failure from provider/tool failure, bad assignment, insufficient budget, external dependency, permission/human blockage and genuinely unresolved/impossible work.

#### Outcome and economic attribution

Maintain the semantic chain: **Employee → Work → Runtime evidence → Cost → Deliverable → Verified outcome → Attributable value/revenue/saving/risk reduction → Economic evaluation → Learning/resource proposal.**

A completed WorkItem is not automatically a successful outcome. Revenue/value attribution must preserve direct, shared and unknown/unattributed cases rather than fabricate causality. Economic evaluation should remain multidimensional: revenue, cost saving, risk avoided, quality, customer outcome, speed, human intervention and failed/unresolved expenditure. Avoid a single gameable employee ROI score.

Learning begins as proposals and may recommend changed training, skills, routing, model/tool choice or resource envelope; it must not silently alter authority policy.

#### Production economics and practical-result controls

Before meaningful spend, a WorkItem should carry an explicit expected-result contract where the domain permits it: acceptance criteria, expected outcome/value class, maximum authorized cost, and the evidence required to call the result successful. Competency alone does not make work economically sensible.

Expensive work should support **progressive funding** and evidence checkpoints rather than exposing the entire budget at once. Discovery, investigation and execution tranches may be released only when the preceding checkpoint still supports continuation. A **stop-loss** boundary should halt or escalate before budget exhaustion when repeated failure, negligible information gain, an impossible dependency, or deteriorating expected value makes further spend unjustified. Employees are not rewarded for consuming an allocation.

When a competency gap exists, AIOS should compare **reskill vs reassign** using expected cost, time, recurrence of the capability need, risk and available qualified capacity. Newly verified competencies may enter a bounded probationary state with lower-risk work, smaller budgets and stronger review until production outcomes establish the competency. Competencies may become stale or require recertification when regulations, organizational procedures, tools, APIs or other material dependencies change.

Training/reskilling expenditure, production expenditure, and failure/recovery expenditure should remain distinguishable in economic evidence. Opportunity cost should later inform scheduling across competing WorkItems so a positive result is not automatically treated as the best use of scarce organizational capital.

Economic evaluation must support portfolio roles whose value is not direct revenue. Revenue created, cost saved, loss/risk avoided, customer outcome, quality, strategic capability and unknown/unattributed value remain distinct. Savings or avoided-loss claims require a defensible baseline/counterfactual; otherwise attribution remains unknown rather than manufacturing impressive economics.

Permanent production laws:

- **NO SPEND WITHOUT PURPOSE.**
- **NO PRODUCTION WITHOUT VERIFIED READINESS.**
- **NO RESKILL WITHOUT A VERIFIED GAP.**
- **NO RESULT WITHOUT EVIDENCE.**
- **NO VALUE CLAIM WITHOUT ATTRIBUTION EVIDENCE.**
- **NO ADDITIONAL CAPITAL WITHOUT GOVERNANCE.**

### Phase 20 — Earned Autonomy & Resource Governance

Grant autonomy capability-by-capability with bounded scope, authority ceiling, risk class, budget, rollback, audit, quality threshold, revocation and periodic review. Phase 20 consumes verified competency, production-result and economic evidence rather than enabling autonomy or resource increases by configuration alone.

Resource allocation is governed organizational capital, not agent-owned money. Evidence-backed performance may support proposals to expand, maintain or reduce model/tool/compute budgets and operating scope. Repeated economically poor execution may trigger cheaper routing, tighter supervision, remediation/reskilling, restriction or retirement; strong performance may justify additional resources only through the appropriate authority boundary. Agents may request resources but never self-fund, hold autonomous wallets, accept external work, sign contracts, move money or expand their own authority merely to preserve their operation.

Permanent chain: **CAN DO != MAY DO != DID DO != CREATED VALUE**.

The organization must be able to answer: **what real resources did this employee/work consume, what verified result was produced, what value is supportably attributable, and what should change next?**

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

### Anti-bottleneck production design

Controls that prevent failure must not become a second source of operational failure. Control strength, synchronization and durability are proportional to consequence. Routine compliant work should use the shortest safe path; governance concentrates on exceptions and boundary crossings.

| Anti-bottleneck mechanism | Practical failure mode | Better production design |
| --- | --- | --- |
| Capability autonomy | autonomy levels become a sequential approval staircase | capability-specific pre-authorized operating envelopes; routine work executes directly inside the earned envelope |
| Governance by exception | routine work is over-classified as exceptional | measure exception rate/age and repair policies that repeatedly escalate safe routine work |
| Cached competency | constant revalidation or stale competency | version/freshness-aware reuse with event/dependency invalidation; recheck only after material change, expiry or performance trigger |
| Permission/authority reuse | repeated identical checks or stale authorization | bounded execution leases/contexts with immediate revocation semantics; cached authorization never becomes a new grant |
| Fast-path preflight | every subsystem independently recomputes eligibility | one bounded execution context from canonical competency, authority, permission, risk and budget truth |
| Human escalation | reviewer queues become stale | lowest-capable-authority routing, priority/SLA/aging and safe timeout behavior; escalate upward only when unresolved |
| CEO/Board coordination | executive becomes synchronous router for every action | distributed routine execution under canonical objectives/policies/budgets; executives handle strategy, conflicts, exceptions and material allocation |
| Progressive funding | tiny tranches create approval chatter | materiality-aware tranches/checkpoints; no approval per token/API call inside an authorized envelope |
| Budget enforcement | per-call bureaucracy or spend-to-budget behavior | bounded local spending envelope, actual metering, hard limit and material governed replenishment |
| Stop-loss | crude attempt limits kill valuable difficult work | failure class, information gain, progress, dependency state and expected value determine continuation |
| Evidence reuse | full evidence graph is reconstructed repeatedly | canonical fingerprints, dependency versions, incremental recomputation and selective retrieval |
| Durable audit | write amplification/transaction contention | durable pre/post evidence for consequential effects; efficient durable/batched metering for material paid operations; sampled/aggregated routine telemetry |
| Pre-tool durability | database commit before every harmless tool call | consequence-tier signal durability; reconstructable lineage for external mutation, lighter treatment for routine reads/calculations |
| Retry control | repeated deterministic failures consume capacity | classify failure before retry; bounded retries plus scoped circuit breakers; deterministic failures are not papered over |
| Deduplication | global duplicate search becomes expensive | deterministic idempotency/causal keys and bounded windows |
| Queue prioritization | reprioritization churn or easy-task starvation | stable priority classes with deadlines, consequence, aging/fairness, expected value and capacity |
| Backpressure | queues grow forever | admission control, bounded queues, deduplication, cancellation and shedding obsolete/low-value work while preserving evidence |
| Parallel execution | provider/database contention | concurrency budgets by tenant/provider/capability and dependency-aware parallelism |
| Capacity-aware routing | best employee/model becomes hotspot | route on fit, competency, quality, cost, load, deadline and probation needs rather than quality alone |
| Cheap-model routing | repeated cheap failures cost more overall | measured task/provider success-cost history with bounded escalation |
| Expensive-model escalation | difficult work always jumps to frontier inference | explicit complexity/risk thresholds and measured marginal benefit |
| Reskill vs reassign | optimizer spends too long deciding | deterministic thresholds first; deeper optimization only when material |
| Competency recertification | simultaneous expiry creates retraining storm | staggered expiry, dependency-triggered invalidation and reuse of valid organizational learning |
| Organizational learning | behavior churn after every task | accumulate evidence and batch governed learning proposals; never silently rewrite authority |
| Economic attribution | work waits for revenue/value evidence | separate operational completion from asynchronous economic attribution; outcomes may remain pending/unknown |
| Outcome verification | long-latency outcomes hold workers | durable pending-outcome state and asynchronous reconciliation |
| Agent handoffs | serialization/context reconstruction | direct ownership by default; hand off only for capability/authority/dependency reasons using compact structured artifacts |
| Context transport | full company/case/history resent every call | canonical references, selective retrieval, fingerprints and incremental compaction |
| Context compaction | repeated summaries lose facts/cost tokens | compact derived runtime/conversation context; reference canonical truth rather than rewriting it |
| Provider fallback | fallback violates assumptions/output shape | normalized capability/output contracts, provider validation and explicit degraded/unknown states |
| External reconciliation | missing confirmation blocks forever | bounded reconciliation with pending/unknown states and escalation; never fabricate confirmation |
| Circuit breakers | one failure stops unrelated work | scope breakers by provider/tool/capability/tenant |
| Observability | telemetry becomes production workload | aggregate/sample diagnostics where safe; full durable lineage for consequential/material events |
| Security assurance | heavyweight security checks on harmless operations | risk-tiered controls; strongest checks at credential/consequential/external boundaries |
| GRC/policy evaluation | policy engine becomes synchronous bureaucracy | deterministic/precompiled evaluation and reusable bounded decisions where policy permits |
| Production proof | exhaustive proof on every tiny runtime action | proof proportional to change/action risk while exact-head release acceptance remains mandatory |
| Living HQ updates | visualization polling overloads backend | event-driven/coalesced presentation; UI never enters execution critical path |
| Notifications | Owner/reviewer alert fatigue | aggregate, rank, deduplicate and suppress redundant alerts while preserving critical escalation |
| Multi-agent consensus | routine work waits for unnecessary agreement | consensus/review only when risk/evidence policy justifies it; model agreement is never authority |
| Bottleneck optimization | system scales guessed constraint | measure end-to-end lead time: queue + governance + dependency + provider + execution + reconciliation; scale measured constraint |
| Successful throughput | easy work crowds out important difficult work | balance priority, consequence, deadline, aging, expected value and capacity; raw throughput is not success |

**Fast-path invariant:** work admitted -> valid reusable competency/authority/permission/budget context -> capacity-aware assignment -> execute inside bounded envelope -> proportionate telemetry/evidence -> exception only when necessary -> asynchronous outcome/economic attribution.

**Anti-bottleneck laws:**
- **FAST PATH FOR ROUTINE WORK.**
- **GOVERNANCE BY EXCEPTION.**
- **AUTONOMY LEVELS ARE OPERATING ENVELOPES, NOT SEQUENTIAL APPROVAL STEPS.**
- **REUSE VERIFIED COMPETENCY, EVIDENCE AND AUTHORIZATION UNTIL A MATERIAL INVALIDATION EVENT.**
- **NO CENTRAL AGENT ON EVERY EXECUTION PATH.**
- **NO CONSENSUS WITHOUT A RISK OR EVIDENCE REASON.**
- **FAILURE CLASSIFICATION BEFORE RETRY.**
- **HUMAN ATTENTION IS A SCARCE ORGANIZATIONAL RESOURCE.**
- **DURABILITY AND CONTROL COST MUST BE PROPORTIONAL TO CONSEQUENCE.**
- **MEASURE END-TO-END LEAD TIME AND BOTTLENECKS BEFORE SCALING.**

---

## 13. What we deliberately do not build

AIOS does not become a generic multi-agent clone, ungoverned swarm, bulk-imported prompt catalogue, crypto/self-replicating organism, simulated office inventing human-like activity, security exploitation toolkit, all-purpose GRC suite, unnecessary model-hosting project, or second canonical state hidden in frontend/renderers/memory/external runtimes.

We also do not optimize for “maximum autonomy” as a vanity metric. We do not let model agreement substitute for evidence, silently rewrite historical assessments after rules change, certify newly discovered sources automatically, auto-submit government/legal commitments without explicit earned authority, or allow AI employees to create recursive unbounded work because they believe more work might be useful.

---

## 14. Immediate order of work

```text
1. Finish the Phase 16 timeout/cancellation tranche with explicit AgentRun cancellation semantics on top of the sealed soft-timeout and stale-running reconciliation boundaries.
2. Continue Phase 16 with hard runtime budgets/actual cost metering, scoped circuit breakers and runtime reconciliation before materially increasing autonomous execution.
3. Keep lifecycle identity separate from static agent definitions, `AgentRun` execution history, work assignment, credentials, permissions, authority and autonomy.
4. Add session/subagent/compaction lifecycle evidence only together with a real canonical runtime operation; never create a signal-only duplicate truth store.
5. Build Phase 17 security assurance before materially expanding external or consequential autonomous execution.
6. Build Phase 19 preflight competency: verify job-specific organizational readiness before meaningful production spend; GAP → bounded reskill + evidence-backed competency verification; NOT_SUITABLE → route/reassign/escalate.
7. Add canonical outcome/economic attribution: activity != result, completion != outcome, spend != value; preserve unknown/unattributed value rather than inventing ROI.
8. Use Phase 19/20 verified competency, result, correction and economic evidence to propose resource/autonomy changes capability-by-capability; no employee may self-grant budget, permissions, authority or autonomy.
9. Expand AUTO.DOC, AUTO.CASE, AUTO.COMMS, AUTO.ORG and AUTO.OPS only where their evidence/reconciliation/queue/economic controls are proven.
10. Add interoperability and production scale only when measured bottlenecks justify them.
```

### Workstream parallelization rule

Parallel work is allowed only when two slices do not mutate the same canonical contracts and neither depends on the other's unsealed semantics. Visual polish, deterministic QA tooling or isolated document extraction may proceed beside regulatory work; competing changes to authority, evidence, WorkItem lifecycle or autonomy policy must serialize through one accepted base.

---

## 15. Definition of destination

Global Mobility AIOS is successful when the Human Owner can open the product and understand a real, continuously operating AI organization without reading logs or trusting theatrical simulation.

The system should make it possible to see what the company is doing, inspect why it is doing it, trace what evidence and authority produced each consequential outcome, intervene when necessary, replay what happened, measure **real cost, verified results and supportably attributable economic value**, verify/reskill employees before costly work, and safely grant more resources or autonomy only where evidence earns it.

The mature product should require humans primarily for strategy, unresolved ambiguity, genuine professional judgment, exceptional/high-consequence decisions and explicit external commitments—not for repetitive retrieval, comparison, data entry, queue routing, regression checking or evidence packaging that machines can perform more reliably.

The long-term advantage is not the number of agents, models, animations or integrations. It is the combination of capable AI employees, durable organizational memory, canonical evidence and decisions, explicit authority, visible organizational state, reliable execution, measured learning and **autonomy that increases only when the system can prove it deserves it**.

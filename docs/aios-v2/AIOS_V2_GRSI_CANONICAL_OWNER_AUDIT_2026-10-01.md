# AIOS V2 — GRSI.A Canonical-Owner Duplicate / Gap Audit

**Programme:** Governed Recursive Self-Improvement (GRSI)  
**Slice:** GRSI.A — Canonical-owner duplicate/gap audit and invariant contract  
**Audit date:** 2026-10-01  
**Exact audited integration head:** `1b83478dab4afc523ee5c6c044511122ad5899e2`  
**Migration head at audit:** `0093_monetary_allocation`  
**Nature of this slice:** read-only architecture / ownership audit. No migration, no runtime mutation, no authority change.

---

## 1. Decision

GRSI does **not** need a new self-contained “self-improvement platform.” AIOS already has canonical owners for work, outcomes, decisions, human authorization, skills, autonomy evidence, replay, reproducibility, observability, agent identity/runtime binding, security, GRC, economics and release proof.

The audit found one material missing connective contract:

> **AIOS has no generic, authority-neutral owner for an improvement proposal and the lineage of one or more versioned capability candidates derived from a known baseline.**

That gap is narrower than a new recursive-agent subsystem. GRSI.B may therefore introduce only the minimum durable **Improvement Proposal + Candidate Lineage** state that existing owners cannot represent truthfully.

The permanent boundary remains:

> **Capability can recursively improve. Authority cannot recursively self-expand.**

An improvement proposal or candidate is evidence of a possible capability change. It is never, by itself, an activation, deployment, permission, tool grant, autonomy promotion, monetary authorization, production mutation, external-action authorization, or claim of improved outcome.

---

## 2. Audit method

The audit inspected the current canonical service/model/migration inventory rather than designing from the roadmap alone. It asked, for each concept needed by GRSI:

1. Does a current AIOS owner already represent this truth?
2. Is that owner semantically correct for GRSI, or would reuse overload its meaning?
3. If a gap exists, what is the smallest connective state needed?
4. What must explicitly remain delegated to existing owners?
5. Would introducing new state accidentally create a second source of authority, active-version truth, execution truth, evaluation truth, or economic truth?

No new durable state is justified merely because a future GRSI flow will need to reference a concept. Existing canonical owners remain authoritative wherever they already represent the concept.

---

## 3. Duplicate audit result

No generic recursive-self-improvement, improvement-proposal, improvement-candidate, or cross-artifact candidate-lineage owner exists in the current model/service inventory.

The repository does contain domain-specific uses of “candidate” and proposal concepts. Those are not GRSI duplicates. For example, regulatory/mobility candidate records exist for their own bounded domain semantics. They must not be generalized into an organization-wide self-improvement truth store merely because their names contain `candidate` or `proposal`.

Likewise, the native skill registry, autonomy-promotion policy, ExecutiveDecision, Contribution and WorkItem models already provide adjacent capabilities, but none truthfully owns a generic parent-baseline → candidate-artifact lineage across agents, skills, prompts, workflows, retrieval/context policy, model-routing profiles, evaluation suites, tool adapters and code/configuration changes.

**Conclusion:** no duplicate GRSI subsystem should be created, but a genuine connective lineage gap exists.

---

## 4. Canonical owner map

| GRSI concept | Existing canonical owner | Audit result | GRSI rule |
| --- | --- | --- | --- |
| Improvement objective / bounded work | `OrganizationalWorkItem` through `organization_governed_work` / `organization_work` | **Reuse** | Improvement activity is work. Do not create a GRSI task/scheduler store. |
| Verified organizational outcome / correction | `OrganizationContribution` | **Reuse** | Contributions remain outcome evidence, not proposal/candidate state. |
| Authorized approve/reject decision | `ExecutiveDecision` / `organization_decision` | **Reuse** | Decision may reference a candidate once candidate identity exists; decision does not become candidate storage. |
| Human review/action | `OrganizationHumanActionRequest` / `OrganizationHumanAction` | **Reuse** | Human authorization remains human-action/decision truth; GRSI must not create its own approval system. |
| Audit mutation evidence | existing command/audit infrastructure | **Reuse** | Candidate mutations, if later added, use normal audited command boundaries. |
| Skill definition/version/lifecycle | native skill registry + skill lifecycle/assignment/audit | **Reuse for skill artifacts** | A skill candidate may point at a skill artifact/version, but GRSI must not replace skill truth. |
| Capability autonomy truth | capability autonomy profile | **Reuse** | Candidate success never changes autonomy automatically. |
| Autonomy evidence/evaluation | autonomy evidence profile/evaluation policy | **Reuse for autonomy promotion** | Do not turn autonomy evaluation into generic candidate evaluation. |
| Autonomy promotion criteria | Board-authored autonomy promotion policy | **Reuse** | Generic capability-version promotion is not autonomy promotion. |
| Historical replay | `organization_replay` | **Reuse as evaluation input** | Replay remains read-only/non-authoritative; no candidate state is stored there. |
| Learned-procedure reproducibility | `organization_learning_reproducibility` | **Reuse as evidence input** | Reproducibility does not generate/activate/authorize a candidate or skill. |
| Recurrence / organizational observation | `organization_observatory` | **Reuse** | Observatory may later trigger a proposal; observation never mutates active capability. |
| Agent persistent identity/lifecycle | `OrganizationAgent` / `organization_agent_lifecycle` | **Reuse** | Candidate lineage does not create a second agent identity. |
| Runtime technical profile/binding | `organization_agent_runtime` + context authority/broker | **Reuse** | Runtime capability and available tools remain separate from authority. |
| Generic evidence/reference linkage | `OrganizationRecordReference` where target types are allowlisted | **Reuse / extend only when justified** | References link owners to existing targets; references are not candidate storage. |
| Security review / incident / AppSec evidence | existing Phase 17 owners and security WorkItems/evidence | **Reuse** | No GRSI security subsystem. |
| GRC review/control mapping | Phase 18 risk/control/standards owners | **Reuse** | GRSI evidence must not fabricate compliance or control effectiveness. |
| Provider-call accounting / monetary allocation | Phase 16 runtime-economics owners | **Reuse** | Candidate work cannot increase spend authority; current USD ceiling remains non-enforceable until its existing blockers are solved. |
| Release / CI / deployment evidence | repository CI + release/deployment acceptance owners | **Reuse** | Candidate promotion cannot bypass exact-head proof or target-host acceptance. |
| Active artifact version | artifact-specific canonical owner | **Reuse; never centralize in GRSI** | GRSI must not introduce a generic second “active version” truth store. |
| Improvement proposal | none generic | **Gap** | Minimal GRSI.B durable proposal identity is justified. |
| Parent/baseline → candidate lineage | none generic | **Gap** | Minimal GRSI.B candidate lineage is justified. |
| Generic current-vs-candidate evaluation campaign | none generic | **Later gap: GRSI.C** | Do not solve in GRSI.B; existing replay/repro/autonomy evidence are inputs, not this owner. |
| Candidate-specific cross-team review package | no generic candidate-bound owner | **Later gap: GRSI.D** | Reuse WorkItems/HumanActions/Decisions after candidate identity exists. |
| Generic shadow/canary execution engine | none, and not currently justified | **Do not build in GRSI.B** | Shadow/canary must attach to real execution seams and remain within existing authority. |
| Evidence-triggered automatic improvement opener | none | **Later gap: GRSI.G** | Observatory/incident/economic/security evidence may propose work later; no auto-mutation now. |

---

## 5. Why adjacent owners must not be overloaded

### 5.1 Contribution is outcome evidence, not candidate state

`OrganizationContribution` records governed outcomes and their supersession/retraction lineage. Treating a proposed agent/config/code change as a Contribution would imply an outcome before the candidate had produced one and would contaminate organizational outcome reporting.

GRSI may later reference Contributions as production-outcome evidence for a promoted generation. It must not use Contribution as the candidate itself.

### 5.2 WorkItem is execution/work truth, not immutable artifact lineage

A WorkItem can represent an improvement objective, research task, implementation task, evaluation task or review task. It should continue to own that work.

A WorkItem, however, does not truthfully identify a baseline artifact fingerprint, candidate artifact fingerprint, parent candidate, exact artifact/diff reference and immutable candidate lineage. Stuffing those semantics into free-form work output would make candidate identity dependent on workflow presentation rather than durable artifact lineage.

### 5.3 ExecutiveDecision is authority evidence, not the thing being decided

`ExecutiveDecision` is the right owner for an authorized approve/reject decision and already supports source identity/version concepts. It is not the right owner for the candidate artifact, because candidates can exist, be evaluated and be rejected without changing decision semantics.

GRSI.B should make a candidate referenceable by a Decision; it should not make the Decision the candidate.

### 5.4 Skill Registry is artifact-specific

The native skill registry correctly owns skill definitions, versions, origin, validation, fingerprints, eligibility and assignment semantics. It should remain the canonical owner when a GRSI candidate targets a skill.

GRSI also targets agents, instructions, workflows, retrieval/context policy, model-routing configuration, eval suites, adapters and code. Turning the skill registry into a generic improvement registry would weaken its bounded semantics and create misleading “skill” records for non-skill artifacts.

### 5.5 Autonomy promotion is not capability-version promotion

Autonomy promotion policy is explicitly Board-authored and governs movement between autonomy levels under evidence criteria. A better prompt, model route, workflow or code candidate can be promoted as the active implementation while keeping the exact same autonomy level.

Conversely, a candidate passing a quality benchmark is not evidence that it deserves more authority. GRSI must keep these decisions separate.

### 5.6 Replay and reproducibility are evidence inputs

Replay reconstructs historical canonical state and remains non-authoritative. Learning reproducibility proves a bounded repeated execution lineage and deliberately does not generate, validate, activate, assign or authorize a learned skill.

Both are valuable inputs to GRSI.C evaluation, but neither owns candidate identity or promotion.

### 5.7 Observatory detects signals; it does not self-modify

The Observatory can identify repeated patterns and future weakness/opportunity signals. Existing learning recurrence intentionally remains observation-only and keeps learned-skill eligibility closed until stronger attribution/reproducibility evidence exists.

GRSI.G may later allow qualifying signals to open bounded improvement work. That is separate from directly changing an active capability.

### 5.8 Agent lifecycle/runtime cannot be candidate authority

Agent lifecycle explicitly grants no authority, permissions, credentials, tools, work, routing, autonomy or execution. Runtime profiles describe technical capability; runtime binding intersects technical availability with freshly resolved governed tool allowance and is not an authorization decision.

GRSI candidates may target agent definitions/runtime configuration, but they do not become entitled to tools or production execution merely by existing.

---

## 6. Proven missing contract for GRSI.B

GRSI.B is justified to add an authority-neutral durable contract with two conceptual identities:

### 6.1 Improvement Proposal

The proposal should identify the bounded organizational reason to investigate a change, without changing the target capability.

Minimum semantics that no existing owner currently owns generically:

- tenant scope;
- proposal key / immutable record fingerprint;
- linked improvement-objective WorkItem;
- target artifact class and canonical target identity;
- exact baseline/current version or fingerprint known when the proposal is opened;
- observed weakness/opportunity and evidence references;
- hypothesis;
- expected improvement;
- acceptance/regression constraints at proposal time;
- proposing actor/position/department identity;
- lifecycle that means proposal state only, never authority state;
- creation/update/supersession evidence.

The proposal must not duplicate WorkItem title/status/assignment, Decision approval status, Contribution outcome state, skill lifecycle, autonomy state or budget authority.

### 6.2 Improvement Candidate Lineage

A proposal may produce zero, one or many candidates. A candidate should identify a proposed capability artifact/version relative to a baseline/parent.

Minimum semantics that no existing owner currently owns generically:

- proposal identity;
- candidate key / immutable record fingerprint;
- target artifact class and canonical target identity;
- baseline/parent version and/or fingerprint;
- optional parent candidate identity for recursive/iterative candidate generations;
- candidate version/fingerprint;
- immutable artifact/diff reference appropriate to the target type;
- proposer identity;
- implementing actor/team identity where available;
- implementation provenance such as model/provider/runtime metadata when material;
- hypothesis inherited or narrowed from the proposal;
- expected improvement and acceptance constraints;
- candidate lifecycle representing only candidate preparation state;
- rejection/withdrawal/supersession lineage where applicable.

Candidate state must **not** contain or imply:

- active production version;
- authority/autonomy level;
- credentials or permission grants;
- allowed tools;
- monetary allocation;
- deployment authorization;
- external-action authorization;
- independent-evaluation pass/fail truth before GRSI.C owns it;
- human/governance approval truth already owned by Decision/HumanAction;
- production outcome truth already owned by Contributions/domain outcomes.

---

## 7. Candidate lifecycle boundary

GRSI.B may need a small candidate-preparation lifecycle, but its labels must be deliberately non-authorizing. A reasonable bounded shape to validate during implementation is conceptually:

```text
proposed
  → materializing
  → evaluation_ready
  → withdrawn | rejected
```

This is not yet a sealed enum. The implementation slice must audit actual use cases before freezing it.

Critically, states such as `active`, `authorized`, `deployed`, `production`, `approved_for_external_action`, `autonomous`, or `budget_granted` do not belong in the candidate-lineage owner. Those truths belong to their canonical systems.

Promotion in GRSI.F must resolve through the artifact-specific active-version owner and an authorized Decision/release path, not by setting a GRSI candidate row to `active` and treating that as production truth.

---

## 8. Target artifact identity boundary

A generic candidate contract needs to address multiple artifact classes without becoming a polymorphic authority database.

GRSI.B should prefer **typed target identity + exact immutable external/canonical reference** over copying entire target artifacts into a new generic table.

Potential target classes include:

- agent definition / role instruction;
- native skill;
- prompt/instruction contract;
- workflow graph or workflow configuration;
- retrieval/context construction policy;
- model/runtime/provider-routing profile;
- evaluation suite;
- tool adapter;
- software code/configuration release candidate;
- later, governed fine-tuning/training recipe or model artifact.

Each class keeps its real content and active-version truth in its owning system. The candidate lineage records **which immutable artifact/version is being evaluated and how it descends from the baseline**.

Do not create a generic blob store or duplicate Git/skill/config content merely for GRSI.

---

## 9. Evaluation independence boundary for GRSI.C

The audit confirms that GRSI.B should not attempt to solve independent evaluation.

Existing AIOS components already provide valuable inputs:

- deterministic tests and repository CI;
- historical replay;
- learning reproducibility;
- autonomy evidence evaluation for its specific autonomy domain;
- security findings/incidents;
- domain-specific validators;
- runtime/provider/cost observations;
- runtime profile `independence_group` as technical metadata.

None of these is a generic current-vs-candidate evaluation campaign owner.

GRSI.C should later bind a candidate to versioned case/evaluation sets, evaluator identity/independence requirements, baseline-vs-candidate measurements and regression constraints. The candidate author must not be its sole evaluator.

`independence_group` may contribute technical evidence about runtime separation, but it is not by itself proof of independent evaluation governance.

---

## 10. Cross-team review boundary for GRSI.D

Security, QA, domain, Platform/SRE and GRC review should continue to happen through governed WorkItems, findings/evidence, HumanActions and Decisions.

GRSI.D may add only the connective candidate-bound review requirement/projection that is necessary to answer:

- which reviews were required for this candidate/risk class;
- which canonical review artifacts satisfy each requirement;
- which remain absent/failed/unknown;
- whether promotion evidence is complete enough for an authorized decision.

It must not create a second security finding store, GRC control store, incident store or human approval store.

---

## 11. Shadow / canary boundary for GRSI.E

No generic shadow/canary execution engine is justified by the current audit.

Shadow and canary behavior must be attached to a real execution seam for the target artifact. A code candidate, skill candidate, retrieval candidate and model-routing candidate may require different execution owners and safety constraints.

Permanent rules:

- shadow output cannot silently mutate canonical or external state;
- canary remains inside the candidate's already-authorized authority/tool/resource envelope;
- candidate admission does not create new credentials, tools or spending authority;
- runtime/effect receipts remain owned by existing execution systems;
- rollback must act through the target artifact's real active-version/deployment owner.

GRSI.E should therefore be evidence/connective work over proven execution seams, not a universal hidden executor.

---

## 12. Promotion / rollback boundary for GRSI.F

There must be no generic GRSI “active version” table that competes with canonical artifact owners.

The future promotion sequence is:

```text
candidate identity
  → required evaluation/review evidence
  → authorized Decision / HumanAction where required
  → artifact-specific promotion or release command
  → artifact owner records active version
  → GRSI records/reference lineage and resulting decision/release evidence
```

Rollback follows the same principle through the artifact owner.

For code, Git/release/deployment state remains authoritative. For skills, the native skill lifecycle/registry remains authoritative. For autonomy, the autonomy profile/promotion policy remains authoritative. Other artifact classes must identify their owner before GRSI.F is implemented.

---

## 13. Economic and resource boundary

Current runtime economics does not establish an enforceable USD budget. The system still distinguishes recorded external monetary allocation from actual billed spend and from a provable pre-call monetary ceiling.

GRSI therefore must not claim that candidate-generation/evaluation spend is safely bounded in USD merely because a candidate has a cost estimate or a recorded allocation.

Until Phase 16's monetary blockers are genuinely closed:

- estimates remain estimates;
- provider call-count capacity is not a money budget;
- recorded USD allocation is not independently verified Board authority;
- actual/remaining USD cannot be fabricated;
- recursive improvement work cannot increase its own resource authority;
- materially costly autonomous candidate campaigns remain subject to existing production restrictions.

---

## 14. Security and governance invariant

The GRSI lineage owner must be intentionally powerless.

Creating or updating a proposal/candidate must never:

- mutate `ContextBundle.allowed_tools`;
- mutate agent credentials/secrets;
- change agent lifecycle to active;
- assign new work authority;
- change autonomy profile/level;
- establish or weaken autonomy promotion/evaluation policy;
- change monetary allocation/provider call capacity;
- deploy code/configuration;
- mutate external systems;
- certify security/GRC compliance;
- fabricate review/evaluation completion;
- change an artifact-specific active version.

This should be enforced both structurally and through focused regression tests in GRSI.B.

---

## 15. Proposed GRSI.B implementation boundary

GRSI.B may proceed because the audit has proven a real ownership gap. It should remain deliberately small.

Expected bounded implementation shape, subject to exact implementation audit:

1. `OrganizationImprovementProposal` — proposal identity and immutable target/baseline/hypothesis/constraint lineage.
2. `OrganizationImprovementCandidate` — proposal-linked candidate/parent/artifact fingerprint lineage.
3. Tenant-scoped read/write services with existing command/audit/idempotency conventions.
4. Minimal API schemas/routes only if a real operator/system caller exists in the current product boundary.
5. Tests proving tenant isolation, idempotency, immutable parent/baseline lineage, valid candidate parentage, and **zero authority side effects**.
6. Explicit tests that proposal/candidate creation does not change autonomy, permissions/tools, monetary allocation, active skill/agent state, deployment state or external actions.

GRSI.B should **not** include:

- generic evaluation campaign/result tables;
- shadow/canary executor;
- promotion/activation command;
- active-version registry;
- automatic Observatory trigger;
- new budget/spend subsystem;
- new security/GRC subsystem;
- new agent runtime;
- new work scheduler;
- model fine-tuning/training infrastructure.

Those belong to later slices only after their own duplicate/gap audits.

---

## 16. GRSI.A acceptance findings

GRSI.A is satisfied when the project preserves these conclusions:

1. **No duplicate self-improvement subsystem exists or is required.**
2. Existing canonical owners remain authoritative for work, outcome, decision, human action, skills, autonomy, replay/reproducibility, observability, agent lifecycle/runtime, references, security, GRC, economics and release/deployment evidence.
3. **A generic Improvement Proposal + Candidate Lineage owner is a real missing contract.**
4. That new contract must be authority-neutral and cannot become generic active-version, approval, evaluation, execution, deployment, autonomy or budget truth.
5. GRSI.C–H remain future slices and must reuse candidate identity plus existing canonical owners rather than being collapsed into GRSI.B.
6. Migration head remains `0093_monetary_allocation` after this audit slice; GRSI.A itself adds no migration.
7. Repository CI can validate this documentation/invariant slice, but does not constitute live production-host proof or recursive-self-improvement implementation.

---

## 17. Next slice

**GRSI.B — Improvement Proposal + Candidate Lineage** may now begin from an exact sealed integration head.

Before writing migration `0094`, GRSI.B must do one final implementation-level duplicate check against the then-current integration state and verify that no intervening merged work has introduced an equivalent canonical owner.

If the gap is still present, add only the minimal authority-neutral proposal/candidate lineage contract described above and prove through tests that creating a candidate cannot grant or modify authority.

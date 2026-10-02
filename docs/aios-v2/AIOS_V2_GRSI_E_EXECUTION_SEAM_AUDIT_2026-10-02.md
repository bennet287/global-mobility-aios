# AIOS V2 — GRSI.E Shadow / Canary Execution-Seam Audit

**Programme:** Governed Recursive Self-Improvement (GRSI)
**Slice:** GRSI.E preflight — proven execution seams before shadow/canary evidence
**Audit date:** 2026-10-02
**Exact audited integration head:** `04dd6bfbf76ac55e6bc9113b9037296b8663e674`
**Current migration head:** `0096_grsi_cross_team_review`
**Nature of this slice:** read-only architecture / ownership audit. No migration, runtime mutation, authority change, deployment, or candidate execution.

---

## 1. Decision

GRSI.E must not create a universal shadow/canary executor.

The current repository has the canonical work, authority, runtime, audit, review and deployment owners needed around a future experiment, but most candidate target classes still lack one essential capability:

> **There is no target-owned seam that can resolve the exact non-active candidate artifact and execute that candidate while preserving the active version and current authority envelope.**

One bounded exception exists today:

> **`code_configuration` candidates already have a real non-active shadow execution seam in repository CI.**

An exact candidate commit can be built, migrated, tested, scanned and browser-exercised by GitHub Actions without becoming the active production version. That is genuine external shadow evidence. It is not canary evidence, and AIOS currently has no candidate-bound verified receipt bridge that can ingest a GitHub Actions result without trusting a caller-supplied conclusion.

Therefore the next GRSI.E implementation should close the **code/configuration CI-proof bridge** first. It should not add a generic executor, experiment scheduler, active-version registry, or shadow-result store.

---

## 2. Permanent GRSI.E boundary

The GRSI.A audit already established:

- shadow output cannot silently mutate canonical or external state;
- canary execution must stay inside the candidate's already-authorized authority, tool, credential and resource envelope;
- candidate admission grants no new credentials, tools, budget, autonomy or external-action authority;
- runtime/effect receipts remain owned by the real execution system;
- rollback remains owned by the target artifact's real active-version/deployment owner;
- GRSI.E is connective evidence over proven execution seams, not a hidden executor.

The roadmap additionally requires capabilities proposed for consequential L4 autonomy to run in shadow mode without canonical/external mutation so disagreement, override and error rates can be measured.

These rules remain authoritative.

---

## 3. Existing owners that GRSI.E must reuse

| Concern | Existing owner | E rule |
| --- | --- | --- |
| Improvement candidate identity | `OrganizationImprovementCandidate` | Candidate id/version/fingerprint remains lineage only. |
| Evaluation | GRSI.C campaign/report | Evaluation is evidence, not admission or promotion. |
| Cross-team review/risk class | GRSI.D review package | Review completeness is readiness for a later authorized decision, not authorization. |
| Bounded experiment work | `OrganizationalWorkItem` | Reuse WorkItem; do not add a GRSI scheduler/task table. |
| Human/organizational admission | `ExecutiveDecision`, `OrganizationHumanActionRequest`, `OrganizationHumanAction` | Shadow/canary admission must resolve through existing authority truth. |
| Runtime binding | `organization_agent_runtime` | Technical binding is not authority and is not itself execution. |
| Agent execution receipts | `AgentRun`, semantic Activity, AuditLog | Reuse when a real target-specific candidate runtime exists. |
| Replay | `organization_replay` | Historical/read-only input only; replay is not candidate execution. |
| Skill truth | native skill registry/lifecycle | Do not create a GRSI skill executor. |
| Runtime economics | Phase 16 owners | No new spend authority or fabricated hard USD ceiling. |
| Code shadow execution | repository Git + exact-head GitHub Actions CI | Existing external owner; AIOS needs a verified candidate-bound receipt bridge. |
| Production canary/deployment | artifact release/deployment owner + `infrastructure/deployment/README.md` acceptance gate | No canary claim until the exact deployed commit/host/date has real acceptance evidence. |

---

## 4. Reusable experiment identity already exists in WorkItem

A new GRSI experiment-plan table is not justified.

`WorkItemCreate` already supports:

- `work_type`;
- `phase_key`;
- `risk_level`;
- `source_object_type`;
- `source_object_id`;
- `source_object_version`;
- bounded context.

A future E WorkItem can therefore identify a shadow/canary objective while setting:

```text
source_object_type = organization_improvement_candidate
source_object_id = <candidate UUID>
source_object_version = <candidate fingerprint>
```

Existing Decision/HumanAction governance can authorize that work. Existing runtime owners can emit their own receipts. GRSI must not duplicate those concepts.

---

## 5. Target-class execution audit

| Candidate target type | Current owner/seam | Exact non-active candidate execution today? | Finding |
| --- | --- | --- | --- |
| `organization_agent` | OrganizationAgent lifecycle + controlled-agent registry/runtime | **No** | Lifecycle stores identity/status only. Controlled execution resolves the static `CONTROLLED_AGENT_REGISTRY`; no candidate artifact override exists. |
| `native_skill` | Native skill registry/lifecycle + skill/work matching | **No** | Matching is explicitly diagnostic; `execution_granted=false`. Tool/permission prerequisites fail closed and no skill executor exists. |
| `instruction_contract` | Role-card loader / controlled-agent prompt construction | **No** | Role-card mapping loads canonical files by active agent name; there is no immutable non-active candidate resolver/injection seam. |
| `workflow` | Existing code/workflow definitions + WorkItems | **No generic seam** | WorkItems own work, but the current workflow runtime does not execute an arbitrary candidate workflow version by candidate fingerprint. |
| `context_policy` | Context broker | **No** | ContextBundle is rebuilt from current canonical state/policy; there is no alternate candidate-policy execution path. |
| `runtime_profile` | `bind_employee_runtime` | **Binding only** | A profile can produce an `EmployeeRuntimeBinding`, but the binding is not execution and no current agent tool/action dispatcher consumes it as a candidate runtime. |
| `evaluation_suite` | GRSI.C evaluation-set references | **No E runtime seam** | C can bind/evaluate versioned sets, but there is no shadow/canary execution owner for a candidate evaluation-suite artifact. |
| `tool_adapter` | Connector/tool-specific owners | **No** | No current executable agent `tool_id` dispatch seam consumes the governed allowance for arbitrary candidate adapters. |
| `code_configuration` | Git/repository CI + deployment acceptance | **Shadow: yes; canary: no** | Exact-head CI runs a non-active commit without production activation. AIOS lacks a verified candidate-bound GitHub Actions receipt bridge. Production-host canary remains unverified. |
| `training_recipe` | none proven | **No** | No governed training/fine-tuning executor is present. |

---

## 6. Replay is not shadow execution

`organization_replay` is useful evidence input but cannot be relabeled as GRSI.E execution.

Its projection is explicitly:

- `authoritative=false`;
- `mutations_allowed=false`;
- reconstructed from persisted historical activity.

Replay can provide representative workload/history for a target-specific shadow runner, but it does not run the candidate and cannot prove candidate behavior.

---

## 7. Runtime binding is not candidate execution

`AgentRuntimeProfile` deliberately describes technical capability, not authority. `bind_employee_runtime` re-resolves canonical ContextBundle state and intersects available tools with the current governed `allowed_tools`.

The output is an `EmployeeRuntimeBinding`, not an AgentRun or tool dispatch.

A candidate `runtime_profile` therefore cannot be declared shadow-tested merely because a binding object can be computed. A real consumer must execute the exact non-active profile while preserving the current authority envelope and emit canonical execution receipts.

---

## 8. Controlled-agent runtime cannot currently prove candidate shadow behavior

`run_controlled_agent` resolves the requested name through the static controlled-agent registry and builds the normal role-card/system-prompt path.

It does not accept:

- improvement candidate id;
- candidate fingerprint;
- alternate role-card/instruction artifact;
- alternate candidate runtime profile;
- candidate workflow graph.

Normal AgentRuns therefore prove active/static controlled-agent behavior, not the behavior of a GRSI candidate. They must not be rebound after the fact and called candidate evidence.

---

## 9. Code/configuration is the first proven E shadow seam

Repository CI is different.

A `code_configuration` candidate whose immutable artifact reference resolves to an exact Git commit can be executed by the existing CI owner without making that commit the production active version.

Useful existing proof types include:

- Repository Policy Check;
- CodeQL;
- V12 Production Proof, including isolated SQLite/PostgreSQL migration and regression tests, frontend production build/smoke, and browser proof.

This is valid **shadow-style engineering evidence** only when it is tied to the exact candidate commit.

It is not:

- deployment authorization;
- production activation;
- production outcome evidence;
- live-host canary evidence;
- proof of external-effect safety outside the CI environment.

---

## 10. Missing code/configuration receipt bridge

`OrganizationRecordReference` cannot currently point directly to a GitHub Actions run:

- target types are allowlisted local model types;
- target IDs are required to be UUIDs;
- target existence/state is resolved against local canonical models.

Using `ExternalValidationRun`, `AuditLog`, or another unrelated model merely to carry a CI URL would overload its semantics and create false provenance.

The concrete GRSI.E gap is therefore:

> **A bounded, read-only, candidate-bound repository CI proof bridge that verifies the repository, workflow/run identity, exact candidate head SHA and successful conclusion from the real CI owner, without creating execution or promotion authority.**

The bridge should prefer independently fetching/verifying the real CI owner over accepting a caller-supplied `success=true`.

No generic external-evidence blob store is justified by this audit.

---

## 11. Canary remains blocked

A code/configuration canary must use the real deployment/release owner and the whole-product target-host acceptance gate.

Current project truth remains:

- no production VPS acceptance bundle has been completed;
- V12 CI is not production deployment proof;
- rollback, HTTPS/browser journey, real dependency path, backup/restore, credential rotation, provider/object-store integrations and incident/recovery evidence still require target-host proof;
- materially costly autonomous execution still lacks a provable hard USD monetary ceiling.

Therefore no GRSI.E canary completion may be claimed from repository CI.

For non-code candidate types, canary additionally requires a target-specific runtime that can execute the exact non-active artifact inside the already-authorized envelope and reconcile every consequential effect.

---

## 12. Admission boundary

GRSI.D's `promotion_evidence_complete_for_decision` means only that evaluation/review evidence is complete enough to present to an authorized decision.

Before shadow/canary execution, the system must still have explicit existing authority evidence that admits the bounded experiment.

The future target-specific E path should preserve this chain:

```text
prepared candidate
  → closed successful GRSI.C evaluation
  → current GRSI.D review package complete for decision
  → authorized Decision / HumanAction admits bounded E WorkItem
  → target-specific non-active execution seam
  → canonical execution/effect receipts
  → GRSI.E read-only evidence projection
```

No step grants new authority merely because the candidate performed well.

---

## 13. Phase 16/17/19/20 dependency rule

The roadmap prohibits E/F admission until the dependencies required for the candidate's risk class are actually proven.

GRSI.E must not manufacture those proofs.

In particular:

- Phase 16 still lacks authoritative itemized billed-cost attribution and a provable hard pre-call USD ceiling;
- Phase 17 still has unresolved broader provenance/adversarial/incident and agent-to-tool entitlement seams;
- Phase 19 distinguishes activity from verified/attributable outcome and does not allow unsupported causality claims;
- Phase 20 autonomy/resource changes remain separately governed and are not earned by one candidate result.

A free/internal code CI shadow can proceed without pretending these open items are solved. A paid or consequential canary cannot use estimates, call-count limits or recorded allocation as a substitute for enforceable monetary/authority evidence.

---

## 14. Minimum contract before adding a target-specific E executor

For any non-code target, implementation must first prove all of the following at its canonical owner:

1. Resolve the exact immutable candidate artifact by target identity/version/fingerprint without copying it into a generic GRSI blob store.
2. Execute that non-active artifact without changing the canonical active version.
3. Bind execution to a fresh governed WorkItem/context and current authority envelope.
4. Structurally prevent canonical/external mutation in shadow mode.
5. For canary, constrain execution to the already-authorized tool/credential/resource scope.
6. Emit canonical runtime/effect receipts tied to the candidate fingerprint.
7. Preserve existing retry/cancellation/reconciliation semantics.
8. Preserve provider/cost evidence when paid execution occurs.
9. Route rollback through the target artifact's real owner.
10. Require explicit human/governance admission; no evaluation score self-admits the candidate.

Until one target owner satisfies this contract, adding a generic E executor is prohibited.

---

## 15. GRSI.E acceptance finding for this preflight

This audit does **not** seal GRSI.E.

It establishes:

1. no duplicate GRSI shadow/canary scheduler/executor should be created;
2. WorkItem already owns bounded experiment work and can carry exact candidate source lineage;
3. existing Decision/HumanAction owners must authorize admission;
4. existing runtime owners must own execution/effect receipts;
5. most target classes currently lack a non-active candidate execution seam;
6. `code_configuration` has a real external shadow seam in exact-head repository CI;
7. AIOS currently lacks a verified candidate-bound bridge to that external CI proof;
8. production canary remains blocked by real deployment/acceptance and relevant authority/economic prerequisites;
9. migration head remains `0096_grsi_cross_team_review`.

---

## 16. Next bounded implementation

**GRSI.E — code/configuration shadow CI proof bridge.**

Before writing any migration, inspect whether the bridge can remain a read-only projection/service over existing candidate + WorkItem truth and externally verified GitHub Actions run data.

If durable state is genuinely required, add only the minimum candidate-bound receipt linkage that the existing owners cannot represent. Do not add:

- a generic executor;
- a generic experiment scheduler;
- a second WorkItem;
- a second AgentRun;
- a generic active-version registry;
- deployment authority;
- new budget/spend authority;
- canary success truth without target-host receipts.

# AIOS V2 — GRSI.E Dependency Policy Owner Audit

**Programme:** Governed Recursive Self-Improvement (GRSI)
**Slice:** GRSI.E admission dependency policy owner audit
**Audit date:** 2026-10-02
**Exact audited integration head:** `843a1bee78f86bef84096c81c2f652596ce0c8e2`
**Current migration head:** `0096_grsi_cross_team_review`
**Nature of this slice:** read-only owner/gap audit. No runtime mutation, authority change, dependency waiver, candidate qualification, deployment or migration.

---

## 1. Question

The roadmap requires:

> No candidate may reach GRSI.E/F until the required Phase 16/17/19/20 runtime, security, economic, learning and authority dependencies for that candidate's risk class are actually proven.

GRSI.D now records the candidate risk class and review contract. GRSI.E can verify exact-head code/configuration CI, current GRSI.D review completeness and the current exact-WorkItem admission decision.

The remaining question is:

> **Which existing canonical owner defines which Phase 16/17/19/20 prerequisites are required for a GRSI candidate risk class?**

The answer from this audit is: **none**.

That is a real connective policy gap, not an invitation to overload an adjacent owner.

---

## 2. GRSI.D risk class is not the constitutional action-risk taxonomy

GRSI.D currently records candidate review risk as:

- `low`
- `medium`
- `high`
- `critical`

That risk class controls the candidate-bound cross-team review matrix.

The organization constitution separately defines material-action risk tiers:

- `R0`
- `R1`
- `R2`
- `R3`
- `R4`
- `R5`

Those tiers classify action materiality and constitutional/autonomy semantics. The constitution contains no rule mapping GRSI.D `low|medium|high|critical` to `R0..R5`, and no rule mapping either taxonomy to Phase 16/17/19/20 dependency contracts.

Inventing such a mapping inside GRSI.E would therefore create new policy while pretending to reuse the constitution.

**Finding:** the constitution is not the missing GRSI dependency-policy owner.

---

## 3. OrganizationControl is not a policy registry

`OrganizationControl` owns the organization control/pause state:

- control key;
- active/paused-style status;
- reason;
- changed-by lineage.

Phase 18 deliberately reuses that owner for explicit risk-to-global-control traceability.

It does not own:

- versioned policy semantics;
- candidate target classes;
- GRSI risk classes;
- Phase dependency requirements;
- prerequisite evidence contracts.

Adding JSON dependency policy to the global control row would mix emergency/control state with GRSI admission policy and make current policy lineage ambiguous.

**Finding:** do not extend `OrganizationControl` into the GRSI dependency-policy owner.

---

## 4. RiskEscalation is occurrence state, not admission policy

`RiskEscalation` records an identified risk:

- category/severity;
- evidence;
- containment;
- accountable/escalated positions;
- current risk status;
- Board-attention/emergency flags.

It is candidate/work-specific risk state. It does not define reusable policy for which cross-phase prerequisites apply to every candidate of a risk class.

A risk event can be evidence used by a policy resolver, but it cannot itself be the policy.

**Finding:** do not encode GRSI dependency rules into `RiskEscalation`.

---

## 5. Phase 20 autonomy profiles are capability-scoped, not GRSI-scoped

The Phase 20 owners are intentionally capability-specific:

- `CapabilityAutonomyProfile`;
- `CapabilityAutonomyEvidence`;
- `CapabilityAutonomyPromotionPolicy`;
- `CapabilityAutonomyEvidenceEvaluationPolicy`;
- their read-only GRC capability review projection.

They bind:

- one position;
- one capability key;
- one context scope;
- current autonomy level and Board ceiling;
- evidence policy version;
- promotion criteria and evidence observations.

They do not bind a GRSI candidate, candidate target type, candidate fingerprint or GRSI.D risk class.

The I.4 evidence-evaluation adapter is additionally explicit:

```text
I4_SUPPORTED_CAPABILITY = eligibility.proposal
I4_QUALIFICATION_CONTRACT = governed-eligibility-canonical-effect.v1
```

Using that adapter to qualify `code_configuration` would be false provenance.

The generic I.3 promotion policy is still attached to one current capability-autonomy profile and governs one-step autonomy promotion. It does not define GRSI cross-phase admission prerequisites.

**Finding:** Phase 20 policy evidence may become one dependency resolver where applicable, but it is not the GRSI dependency-policy owner.

---

## 6. Phase 18 GRC mappings do not create policy applicability

Phase 18 intentionally projects and links existing risk, control, decision, human-action, capability and standards evidence without asserting:

- policy applicability;
- control effectiveness;
- compliance;
- approval;
- causation.

A GRC reference can support a future dependency proof, but using reference presence as “Phase prerequisite satisfied” would violate Phase 18's semantics.

**Finding:** GRC traceability is evidence infrastructure, not the admission policy.

---

## 7. CountryPolicy and regulatory policy owners are domain-specific

`CountryPolicy` and regulatory policy machinery govern immigration/regulatory product behavior.

They do not govern internal GRSI engineering admission.

**Finding:** unrelated domain policy must not become the GRSI owner.

---

## 8. OrganizationActivity is an audit/semantic event owner, not sufficient current-policy truth

A Board-authored policy decision should emit a durable OrganizationActivity because policy establishment is material authority/governance evidence.

However, Activity alone is an event ledger. Using “latest activity by timestamp” as current GRSI dependency policy would make:

- supersession integrity;
- policy version continuity;
- idempotency;
- current-revision lookup;
- exact semantic fingerprinting

implicit instead of canonical.

Existing autonomy policies use a dedicated immutable/versioned table plus an exact Board decision Activity. That pattern is appropriate if new durable GRSI policy state is genuinely required.

**Finding:** reuse Activity for the decision/audit edge, but not as the sole policy store.

---

## 9. Existing GRSI owners do not already contain this policy

GRSI.B owns proposal/candidate lineage.

GRSI.C owns independent evaluation.

GRSI.D owns:

- candidate risk class;
- required cross-team review kinds;
- canonical review-artifact bindings;
- review-evidence completeness.

GRSI.E currently owns no durable state. Its code/configuration path is a read-only projection over:

- exact candidate artifact commit;
- exact candidate-bound WorkItem;
- GitHub Actions exact-head CI;
- current GRSI.D package;
- current exact-WorkItem ExecutiveDecision.

None of those owners defines which Phase 16/17/19/20 dependency contracts apply to a candidate risk class.

**Finding:** the missing policy is not hidden in existing GRSI state.

---

## 10. Confirmed gap

A real connective gap remains:

> **There is no canonical Board-governed, versioned GRSI admission dependency policy that maps candidate scope/risk to explicit prerequisite contract keys.**

The current GRSI.E projection is correct to fail closed with:

```text
unresolved_no_canonical_risk_class_mapping
```

Do not replace that blocker with hard-coded assumptions inside the shadow service.

---

## 11. Required separation: policy vs proof

The missing owner must define **what is required**.

It must not itself claim that a requirement is satisfied.

Future qualification should remain two-stage:

```text
Board-governed dependency policy
  → required dependency contract keys
  → contract-specific resolvers
  → canonical source evidence
  → satisfied | failed | pending | absent | unsupported
```

Examples of evidence owners that a resolver may consume later include:

- Phase 16 runtime/cost/budget evidence;
- Phase 17 security/provenance/incident/tool-enforcement evidence;
- Phase 19 verified outcome/competency/attribution evidence;
- Phase 20 capability/autonomy/authority evidence.

A generic boolean submitted by a caller is never enough.

---

## 12. Proposed canonical owner boundary

The smallest justified new owner is a **GRSI admission dependency policy**, not a generic enterprise policy framework.

Recommended semantic identity:

```text
tenant
target_type
execution_mode
candidate_risk_class
policy_version
required_dependency_contract_keys
```

Initial execution modes should be explicitly bounded, for example:

- `shadow`
- later `canary`
- later `promotion`

Do not create requirements for unsupported modes merely to fill a table.

The policy should be:

- authored by an authenticated Human Board/owner boundary;
- immutable per revision;
- sequentially versioned;
- supersedable only from the current revision;
- fingerprinted canonically;
- tenant scoped;
- linked to an exact Board-authored OrganizationActivity;
- authority-neutral by itself;
- unable to grant tools, credentials, autonomy, budget, deployment or external action.

---

## 13. Do not make dependency keys free-form evidence claims

A dependency key is safe only when the application has an explicit resolver contract for it.

The policy should not accept arbitrary strings such as:

```text
security_done
cost_ok
phase17_complete
```

unless code knows how to resolve that exact key to canonical owners and fail closed.

Recommended rule:

> **Policy may reference only a versioned allowlist of supported dependency contract keys. Unsupported keys are rejected, not stored and later interpreted by humans.**

This keeps policy declaration separate from evidence interpretation.

---

## 14. Do not hard-code a low/medium/high/critical matrix without Board policy

The roadmap says dependencies vary by candidate risk class, but it does not specify the matrix.

The implementation must not silently decide that, for example:

- low skips security;
- high requires every Phase;
- critical requires a monetary contract;
- code/configuration is exempt from learning evidence.

Those are governance decisions.

The code may enforce non-waivable constitutional invariants, but the candidate-class dependency matrix must come from an explicit authorized policy revision.

---

## 15. Exceptions must not become silent prerequisite waivers

If a future policy supports a bounded exception path, reuse existing:

- ExecutiveDecision;
- HumanAction;
- risk/exception lineage;
- audit evidence.

A dependency resolver must still report the underlying prerequisite status.

An exception may authorize a bounded action only where existing constitutional/roadmap rules permit it; it must not rewrite “failed” into “satisfied.”

Permanent safety/authority constraints remain non-waivable by a convenience flag.

---

## 16. Candidate-specific proof remains outside the policy row

Do not store per-candidate CI runs, review outcomes, incidents, cost measurements or autonomy evidence inside the policy.

The policy declares requirements.

The GRSI.E projection resolves those requirements against live canonical evidence for the exact:

- tenant;
- candidate;
- candidate fingerprint;
- target;
- WorkItem;
- execution mode.

This avoids a second evidence warehouse.

---

## 17. Why a new durable policy owner is justified

The duplicate audit found no existing owner with all required semantics:

1. reusable GRSI candidate scope;
2. GRSI risk class;
3. execution mode;
4. versioned required dependency set;
5. Board authorship;
6. supersession;
7. canonical current-policy lookup.

The closest policy owners are capability-autonomy policies, but their scope and evidence contracts are materially different.

Therefore one bounded GRSI policy table is justified if implementation proceeds.

This is new **connective policy truth**, not a duplicate governance subsystem.

---

## 18. Migration boundary

If implemented, this policy is genuine durable state and should receive the next migration after:

```text
0096_grsi_cross_team_review
```

The migration must preserve the repository's established rules:

- composite tenant/id integrity where referenced;
- sequential version checks;
- canonical fingerprint length;
- no self-supersession;
- downgrade refuses destructive removal when governed policy rows exist;
- SQLite/PostgreSQL parity;
- migration guard/ceiling updates in the same feature slice.

The audit itself does not advance the migration head.

---

## 19. What this policy still would not solve

Creating the policy owner does not automatically make GRSI.E qualified.

Qualification still requires supported resolvers for every required dependency contract.

Current project gaps remain real, including:

- Phase 16 authoritative billed-cost attribution / hard monetary ceiling where material spend applies;
- Phase 17 remaining provenance/adversarial/incident/executable agent-to-tool gaps;
- Phase 19 incomplete production-result attribution / reusable competency proof for broader scopes;
- Phase 20 only capability-specific autonomy evidence, not a generic GRSI authority proof;
- whole-product target-host production acceptance for any real canary/deployment claim.

The policy must make those gaps visible, not paper over them.

---

## 20. Next bounded slice

**GRSI.E dependency admission policy v1.**

Before implementation, freeze the first supported scope narrowly:

```text
target_type = code_configuration
execution_mode = shadow
candidate_risk_class = low | medium | high | critical
```

Then:

1. define the first supported dependency contract-key allowlist from real canonical owners;
2. implement Board-authored versioned policy state only for that scope;
3. add a read-only current-policy projection;
4. keep `grsi_e_qualified=false` until every required contract has an implemented canonical resolver;
5. do not add canary/promotion policy rows before their execution/release owners are proven.

This audit does **not** seal GRSI.E.

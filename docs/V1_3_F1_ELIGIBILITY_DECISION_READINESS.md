# V1.3-F.1 — Eligibility Decision Readiness

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** COMPLETE / PASS / SEALED

Acceptance record: `docs/V1_3_F1_ACCEPTANCE_2026-08-20.md`

## Purpose

F.1 is the first deterministic Decision Readiness slice downstream of the accepted E.2 eligibility-intent vertical.

It answers one narrow question:

> **Is this already-governed E.2 eligibility proposal sufficiently complete and internally consistent to enter genuinely independent verification?**

F.1 does **not** answer whether the applicant is legally eligible, does not authorize the material action, and does not mutate eligibility truth.

The bounded chain is:

```text
accepted E.2 REVIEW_REQUIRED proposal
→ durable E.2 governance attempt
→ fresh governed ContextBundle
→ current Lead / Profile / pathway state
→ deterministic F.1 readiness gates
→ READY_FOR_INDEPENDENT_VERIFICATION
   or NOT_READY
   or HUMAN_INPUT_REQUIRED
→ V1.3-G independent verification
```

Permanent rule:

> **Decision Readiness routes work; it does not authorize work.**

This is a concrete application of:

> **Scores route; deterministic gates authorize.**

The F.1 score is descriptive only. The state is derived from deterministic gate results, and even a READY state has no authorization effect.

## Input trust boundary

F.1 does not accept an arbitrary model response or free-form intent.

Its input is the typed `GovernedEligibilityTransitionIntentResult` produced by accepted E.2.

Before readiness gates are evaluated, F.1 verifies:

- E.2 schema identity;
- `mutated == false`;
- Command Gateway outcome is exactly `REVIEW_REQUIRED`;
- Gateway reason is exactly `POLICY_REVIEW_REQUIRED`;
- constitutional effective risk remains R3;
- typed intent fingerprint still matches the in-memory intent;
- the durable E.2 `OrganizationActivity` still exists;
- that Activity is an `eligibility_intent_attempt`;
- trace identity matches the Gateway evaluation;
- WorkItem identity matches the intent;
- durable intent/context/runtime-binding/profile/pathway fingerprints match the supplied proposal;
- the durable record itself preserves `eligibility.transition`, `REVIEW_REQUIRED`, `POLICY_REVIEW_REQUIRED`, R3, the proposing `OrganizationPosition` actor identity and the exact action fingerprint;
- the explicit E.2 `independent_verification_not_yet_satisfied` floor is still present.

A BLOCKed E.2 proposal cannot be reclassified by F.1. A0, authority denial, scope denial and other Command Gateway failures remain governance outcomes rather than readiness questions.

## Freshness boundary

F.1 rebuilds the governed ContextBundle before assessing readiness.

It requires:

```text
current ContextBundle.context_hash
    == accepted E.2 context_hash
    == E.2 EmployeeRuntimeBinding.context_hash
```

It also rechecks canonical fingerprints for:

- Lead;
- current immutable Profile;
- MobilityPathway + MobilityPathwayVersion.

A case, profile, pathway, Evidence, rule, policy or position-contract change therefore invalidates the accepted E.2 proposal before F.1 can route it forward.

## F.1 readiness states

```text
READY_FOR_INDEPENDENT_VERIFICATION
NOT_READY
HUMAN_INPUT_REQUIRED
```

### READY_FOR_INDEPENDENT_VERIFICATION

All deterministic F.1 gates pass.

This means only:

> the proposal may be handed to a genuinely independent verifier in V1.3-G.

It does **not** mean:

- eligibility is true;
- the recommendation is verified;
- the R3 verification floor is satisfied;
- the Command Gateway may auto-execute;
- canonical mutation is authorized;
- client-facing advice is authorized.

### NOT_READY

At least one deterministic known blocker fails.

Examples include:

- E.2 itself proposed `needs_documents` or `insufficient_information`;
- pathway publication/certification/provenance integrity is degraded;
- a known material factual precondition is explicitly unsatisfied.

### HUMAN_INPUT_REQUIRED

No deterministic failure is established, but a required fact is absent or unresolved and cannot be safely inferred.

Examples in F.1 include:

- nationality is missing;
- an explicit binding-job-offer fact is required but unresolved.

## The five F.1 deterministic gates

### 1. `proposal_state_actionable`

The E.2 proposal must be one of:

```text
potentially_eligible
potentially_ineligible
```

The following are not ready for independent eligibility verification:

```text
needs_documents
insufficient_information
```

### 2. `governed_authority_complete`

The current governed ContextBundle must have:

- no authority unknowns;
- no contradictions;
- governed pathway Evidence;
- governed VerifiedRules;
- an active CountryPolicy fingerprint.

Working-context JSON cannot satisfy this gate.

### 3. `required_case_facts_present`

The first bounded verifier-briefing fact set is:

```text
nationality
target_country
goal
```

These facts come from canonical Lead/Profile/intake state through `case_facts(...)`.

F.1 does not infer absent facts from model prose.

### 4. `pathway_publication_integrity`

F.1 deliberately reuses the existing pathway publication blocker implementation rather than creating a second interpretation of:

- core Evidence;
- required Evidence roles;
- source/snapshot consistency;
- source certification;
- VerifiedRule provenance;
- pathway jurisdiction/domain publication requirements.

The existing `_publication_evidence_blockers(...)` helper is currently reused inside the same service package.

This is an intentional bounded internal dependency. A public extraction should occur only when another real consumer proves that the contract is stable; F.1 does not create a generic readiness/publication framework merely for abstraction purity.

### 5. `material_fact_preconditions`

F.1 begins with one existing explicit structured pathway criterion already used elsewhere in AIOS:

```text
binding_job_offer_in_austria_required
```

When true:

- `has_job_offer == true` → PASS;
- `has_job_offer == false` → FAIL;
- unresolved `has_job_offer` → HUMAN_REQUIRED.

If the criterion exists with a non-boolean value, F.1 fails closed as canonical data integrity error.

F.1 does **not** pretend that this one criterion is a complete eligibility engine. Substantive route interpretation remains the responsibility of independent verification and later governed domain expansion.

## Readiness score

F.1 emits:

```text
readiness_score = passed deterministic gates / total deterministic gates
```

The initial gate count is five.

The score is informational/routing metadata only.

It is never used to relax:

- R3;
- Evidence requirements;
- authority;
- scope;
- policy;
- expected-version checks;
- independent verification;
- Human/Board retained authority.

A high score cannot authorize an action. A low LLM confidence cannot veto an otherwise gate-complete proposal, and a high LLM confidence cannot rescue a failed gate.

## Profile readiness is not Decision Readiness

The existing Profile model already contains:

```text
completeness_score
readiness_stage
```

with intake/profile stages such as:

```text
foundation
developing
pathway_ready
evidence_ready
```

Those values measure profile/intake completeness. They are useful context, but they are not the F.1 material-decision gate.

F.1 therefore does not reuse profile completeness as an authorization proxy.

A profile with a lower general completeness score can still be ready to enter independent verification if the concrete facts and governed authority required for this bounded proposal are present.

## Confidence is not authority

E.2 model confidence is deliberately ignored by F.1 gate logic.

For example:

```text
confidence = 0.01
all deterministic F.1 gates PASS
→ READY_FOR_INDEPENDENT_VERIFICATION

confidence = 1.00
one deterministic F.1 gate FAIL
→ NOT_READY
```

This preserves the permanent separation:

```text
model confidence ≠ readiness gate
readiness score  ≠ authorization
```

## Read-only posture

F.1 creates no:

- LLM call;
- AgentRun;
- OrganizationActivity;
- EligibilityAssessment;
- eligibility-state mutation;
- application-state mutation;
- external action;
- client-facing recommendation.

F.1 returns a typed deterministic result with a reproducible `readiness_fingerprint`.

The fingerprint excludes `assessed_at`, so repeated assessment over identical canonical state yields the same readiness identity.

## Result contract

`EligibilityDecisionReadinessResult` contains:

```text
schema_version
state
readiness_score
gates
intent_fingerprint
context_hash
profile_id
profile_version
pathway_version_id
readiness_fingerprint
assessed_at
ready_for_independent_verification
independent_verification_required = true
authorization_effect = false
canonical_commit_allowed = false
```

The final three safety properties are deterministic and cannot be supplied by a model.

## Why F.1 does not inspect arbitrary case documents yet

The current D.3 ContextBundle carries governed pathway Evidence/rules/policy, not a complete governed applicant-document Evidence set.

F.1 therefore does **not** query arbitrary `DocumentRecord` rows behind the ContextBundle and create a second truth path.

Applicant-document readiness should be added only through a governed case-Evidence/context adapter or another equally explicit authority contract.

This is intentionally conservative:

> **F.1 may be incomplete before it is allowed to become inconsistent with the Context Broker trust boundary.**

## Relationship to the legacy eligibility engine

`eligibility_engine.py` contains useful deterministic factors and scoring logic, but it still reads broader active rules, policy, documents and pathway matches directly from database state outside the accepted D.3 authority envelope.

F.1 therefore does not use its score as material Decision Readiness.

Reusable deterministic domain rules should migrate into ContextBundle-scoped consumers incrementally, based on real vertical needs.

## Tests

`apps/api/tests/test_organization_decision_readiness.py` covers, among other cases:

1. a valid E.2 R3 proposal becomes `READY_FOR_INDEPENDENT_VERIFICATION` only;
2. F.1 remains read-only and creates no new Activity or EligibilityAssessment;
3. repeated assessment over unchanged state produces the same readiness fingerprint;
4. very low model confidence does not block a gate-complete proposal;
5. low generic Profile completeness/readiness does not become the material gate;
6. `needs_documents` / `insufficient_information` proposals are `NOT_READY`;
7. missing nationality routes to `HUMAN_INPUT_REQUIRED` even with model confidence 1.0;
8. an explicitly missing Austrian binding job offer becomes `NOT_READY`;
9. an unresolved required job-offer fact becomes `HUMAN_INPUT_REQUIRED`;
10. degraded required non-core pathway Evidence/certification becomes `NOT_READY`;
11. an A0/BLOCK E.2 proposal cannot enter Decision Readiness;
12. case changes after E.2 acceptance invalidate the proposal;
13. forged in-memory intent changes are rejected against the durable E.2 fingerprint;
14. malformed supported structured pathway criteria fail closed.

The accepted full API regression after F.1 is `996 passed / 5 skipped / 1 warning / 0 failed`. The separate focused-test count is not invented because it was not restated in the acceptance evidence.

## Migration posture

F.1 introduces no database migration.

It reuses:

- E.2 typed intent and durable governance attempt;
- ContextBundle;
- Lead/Profile canonical state;
- MobilityPathwayVersion;
- pathway Evidence/publication rules;
- CountryPolicy;
- VerifiedRules;
- existing transparency projection.

## Accepted evidence

Canonical acceptance is recorded in `docs/V1_3_F1_ACCEPTANCE_2026-08-20.md`.

```text
Repository policy             PASS
Full API regression           996 passed / 5 skipped / 1 warning / 0 failed
Duration                      359.39s
Database migration check      PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS
Actual tables                 118
Physical tables               119 incl. alembic_version
git diff --check              clean
V12 branch                    clean / synchronized
```

No GitHub CI PASS is claimed without attached status/check evidence.

## Non-claims

F.1 does not claim:

- independent verification completion;
- eligibility truth;
- legal advice;
- canonical eligibility mutation;
- Decision Readiness completion beyond this first bounded eligibility slice;
- applicant-document Evidence readiness;
- provider-egress policy completion;
- generic readiness framework completion;
- Flight Recorder completion;
- Munder adoption;
- GitHub CI PASS.

## Direction after F.1

F.1 is accepted. V1.3-G should consume only:

```text
EligibilityDecisionReadinessResult.state
    == READY_FOR_INDEPENDENT_VERIFICATION
```

and then execute a genuinely independent verification path with meaningful independence in runtime/model/context/conclusion exposure as required by R3.

Only after G is accepted should the project reconsider the E.2 forced `HUMAN_REQUIRED` verification floor for an eligibility transition.

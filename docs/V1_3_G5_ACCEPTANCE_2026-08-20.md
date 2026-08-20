# Global Mobility AIOS — V1.3-G.5 Acceptance Record

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted implementation head:** `e50a67d5167ace79423c62b3a729c45a82032bb8`  
**Status:** COMPLETE / PASS / SEALED

## Acceptance statement

V1.3-G.5 — **Eligibility Reassessment / Supersession** is accepted and sealed.

G.5 extends the governed E.2 → F.1 → G.1 → G.2 → G.3/G.4 eligibility vertical from a first canonical eligibility revision to explicit, concurrency-safe, append-only reassessment with atomic supersession and historical idempotent replay.

The accepted contract preserves the existing Profile-version precondition and adds a distinct eligibility-revision precondition. It does not replace the Governance Kernel's `MaterialAction.expected_version`, does not introduce a generic versioned-effect framework, and does not weaken the Human Owner / Board, authority, risk, verification or transparency invariants.

## Canonical acceptance evidence

Observed Human Owner local acceptance on 2026-08-20:

```text
G.5 precondition + G.3 baseline          20 passed / 1 warning / 0 failed
G.5 E.2/G.2 integration                 38 passed / 1 warning / 0 failed
G.5 canonical-effect core               28 passed / 1 warning / 0 failed
E.2 → G.5 effect vertical               84 passed / 1 warning / 0 failed
G.4 + G.5 orchestration/API             15 passed / 1 warning / 0 failed
E.2 → G.5 full governed vertical        99 passed / 1 warning / 0 failed
Platform hardening                      8 passed / 1 warning / 0 failed
Repository policy                       PASS
Full API regression                     1075 passed / 5 skipped / 1 warning / 0 failed
Duration                                397.94s
Database migration check                PASS
Migration head                          0077_canonical_eligibility_assessment_revision
Registered tables                       119
Local DB schema                         PASS
Actual tables                           119
Physical tables                         120 incl. alembic_version
git diff --check                        clean
V12 branch                              clean / synchronized
```

The only observed warning is the existing Starlette/httpx TestClient deprecation warning. It is non-blocking and G.5 does not imply a dependency change.

No GitHub CI PASS is claimed because no attached GitHub status/check evidence was present for the accepted head.

## Accepted concurrency model

G.5 deliberately keeps two different optimistic-concurrency contracts:

```text
Profile precondition
  MaterialAction.expected_version = Profile.profile_version

Canonical eligibility precondition
  expected_eligibility_revision_version = current EligibilityAssessmentRevision.version
```

These values protect different state and must not be conflated.

Accepted transition semantics:

```text
no ACTIVE revision + expected eligibility revision = none
→ canonical v1 ACTIVE
```

```text
ACTIVE vN + expected eligibility revision = vN
→ prior vN SUPERSEDED
→ new vN+1 ACTIVE
→ new.supersedes_revision_id = prior.id
```

```text
ACTIVE revision + missing expected eligibility revision
→ fail closed
```

```text
ACTIVE vN + expected eligibility revision != vN
→ fail closed
```

```text
more than one ACTIVE canonical revision
→ fail closed / aggregate integrity error
```

There is no implicit reassessment and no last-write-wins behavior.

## E.2 contract

E.2 now resolves the canonical eligibility revision precondition before model/runtime execution and revalidates it after runtime latency.

The accepted `MaterialAction` continues to use:

```text
expected_version = Profile.profile_version
```

and carries the eligibility-specific concurrency facts inside the eligibility action contract:

```text
eligibility_aggregate_key
expected_eligibility_revision_version
expected_eligibility_revision_id
next_eligibility_revision_version
```

The durable E.2 governance attempt records those facts. Existing canonical eligibility state therefore cannot be silently reassessed and stale revision expectations fail before material work proceeds.

## G.2 contract

G.2 reconstructs the exact accepted E.2 `MaterialAction`, including the eligibility revision expectation, and revalidates the canonical eligibility revision before verification-floor authorization.

Fresh execution requires the revision precondition to remain current.

A narrowly-scoped replay reconstruction path may skip *current* revision validation only when resolving an already-durable historical canonical effect. That exception does not authorize new work.

## G.3 canonical reassessment transaction

G.3 now supports both first canonical creation and explicit reassessment through the same canonical-effect service.

For reassessment the transaction stages, as one unit:

```text
fresh final Command Gateway authorization
+ prior ACTIVE revision → SUPERSEDED
+ new EligibilityAssessment
+ new EligibilityAssessmentRevision vN+1 ACTIVE
+ supersedes_revision_id → prior revision
+ governance Activity
+ semantic MATERIAL Activity
```

Any failure rolls back the complete reassessment, including the prior revision lifecycle change. The previously active revision therefore remains ACTIVE when a new effect cannot be committed safely.

Prior assessment/revision content is never rewritten in place.

The existing `EligibilityAssessment.overall_score = 0.0` behavior remains a legacy compatibility placeholder only. G.5 does not reinterpret it as a computed eligibility score.

## Historical replay

G.5 separates historical effect identity from current aggregate state.

After:

```text
v1 ACTIVE
→ reassessment
→ v1 SUPERSEDED / v2 ACTIVE
```

an exact retry of the original v1 idempotency key resolves the durable v1 effect as:

```text
GatewayOutcome.IDEMPOTENT_REPLAY
```

without model calls and without requiring v1 to remain ACTIVE.

The same principle applies to later superseded revisions: supersession does not erase replayability or lineage.

Replay still validates the persisted action/effect/readiness/verification/floor/assessment/semantic lineage and fails closed on torn or conflicting durable state.

## G.4 orchestration

`orchestrate_governed_eligibility(...)` now accepts one optional domain-specific concurrency input:

```text
expected_eligibility_revision_version
```

Initial canonical creation omits it. Reassessment supplies the exact revision believed current.

The orchestration continues to obtain provider/runtime selection and `CapabilityAuthority` only from the trusted server-side `GovernedEligibilityExecutionPlan`.

Post-commit orchestration replay validates that a reused idempotency key carries the same eligibility revision expectation as the persisted effect. A conflicting expectation is rejected before either model runs.

## Governed HTTP boundary

`POST /api/v1/organization/eligibility/orchestrate` now permits the request field:

```json
{
  "expected_eligibility_revision_version": 1
}
```

with `>= 1` validation when supplied.

This is an optimistic-concurrency assertion, not authority or execution policy.

The request still cannot choose or replace:

- tenant authority;
- producer/verifier OrganizationPosition;
- provider;
- model;
- autonomy level;
- risk tier;
- allowed scope;
- `CapabilityAuthority`.

`ConfigDict(extra="forbid")` remains in force for untrusted fields.

The authenticated human initiator remains distinct from the material actor; the producer OrganizationPosition remains the governed action actor.

## Verification and authority invariants preserved

Every fresh reassessment still traverses the governed chain:

```text
explicit canonical revision precondition
→ E.2 governed proposal
→ F.1 Decision Readiness
→ G.1 blind independent verification
→ G.2 verification floor + Gateway re-evaluation
→ G.3 final fresh Command Gateway authorization
→ atomic supersession effect
```

G.5 does not bypass Decision Readiness, independent verification, R3 classification, deterministic authorization, autonomy rules, or Board-inspectable material lineage.

## Database and migration truth

G.5 required no migration. The existing `EligibilityAssessmentRevision` schema already had the required fields:

```text
version
lifecycle_status
supersedes_revision_id
```

Accepted database truth remains:

```text
migration head      0077_canonical_eligibility_assessment_revision
registered tables   119
actual tables       119
physical tables     120 including alembic_version
```

## Deliberate non-claims

G.5 does not claim:

- client-facing eligibility publication;
- application mutation;
- government submission;
- unrestricted external execution;
- generic optimistic-concurrency infrastructure;
- generic versioned-effect infrastructure;
- replacement of `session.expire_all()` freshness boundaries;
- automatic self-promotion of autonomy;
- Phase 13.17 PASS;
- GitHub CI PASS without attached checks.

## Program transition

With G.5 accepted, the canonical V1.3 programme may advance to:

> **V1.3-H — Organizational Immune System + circuit breaking**

The next stage should build on the now-versioned, replayable and Board-inspectable material-effect foundation rather than widening eligibility versioning into a generic framework prematurely.

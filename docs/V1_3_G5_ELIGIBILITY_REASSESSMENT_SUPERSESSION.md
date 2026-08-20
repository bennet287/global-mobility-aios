# Global Mobility AIOS — V1.3-G.5 Eligibility Reassessment / Supersession

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted implementation head:** `e50a67d5167ace79423c62b3a729c45a82032bb8`  
**Status:** COMPLETE / PASS / SEALED

## Purpose

G.5 extends the accepted governed eligibility vertical from one canonical revision to safe, append-only reassessment and supersession.

Permanent rule:

> **A reassessment may supersede canonical eligibility truth only when it explicitly names the exact canonical revision it believes is current.**

This preserves the existing Profile-version precondition and prevents last-write-wins reassessment.

The final accepted contract is not a generic versioning framework. It is a bounded eligibility-domain capability integrated into the already-governed E.2 → F.1 → G.1 → G.2 → G.3/G.4 chain.

## Why a second version precondition is required

The accepted E.2 `MaterialAction.expected_version` protects the immutable `Profile.profile_version` used to construct the eligibility proposal.

G.5 does not repurpose that field for canonical eligibility revision concurrency because doing so would trade away the Profile guard.

The sealed action contract therefore carries two distinct concurrency facts:

```text
Profile precondition
  MaterialAction.expected_version = Profile.profile_version

Canonical eligibility precondition
  expected_eligibility_revision_version = current EligibilityAssessmentRevision.version
```

These values protect different state and must never be conflated.

## Canonical revision precondition service

Bounded service:

```text
app.services.organization_eligibility_revision_precondition
```

Public contracts:

```text
eligibility_aggregate_key(...)
active_eligibility_revisions(...)
resolve_eligibility_revision_precondition(...)
require_eligibility_revision_precondition_current(...)
```

Typed failures:

```text
EligibilityRevisionPreconditionRequired
EligibilityRevisionPreconditionStale
EligibilityRevisionAggregateIntegrityError
```

Resolved contract:

```text
EligibilityRevisionPrecondition
```

with:

```text
tenant_key
aggregate_key
expected_revision_version
current_revision_id
current_revision_version
next_revision_version
supersedes_revision_id
is_reassessment
```

## Accepted transition semantics

### Initial canonical effect

```text
no ACTIVE canonical revision
+ expected revision = none
→ legal next revision = v1
→ supersedes_revision_id = none
```

Supplying an expected revision when none exists is stale and fails closed.

### Reassessment

```text
ACTIVE canonical revision = vN
+ expected revision = vN
→ legal next revision = vN+1
→ supersedes_revision_id = active revision id
```

### Missing expectation

```text
ACTIVE canonical revision exists
+ expected revision = none
→ FAIL CLOSED
```

There is no implicit reassessment.

### Stale expectation

```text
ACTIVE canonical revision = vN
+ expected revision != vN
→ FAIL CLOSED
```

### Broken aggregate

```text
more than one ACTIVE revision
→ FAIL CLOSED / aggregate integrity error
```

G.5 never attempts to guess which active row is authoritative.

## E.2 integration

E.2 resolves the eligibility revision precondition before provider/model execution.

It then revalidates the same precondition after runtime latency, alongside the existing canonical case/context and Profile freshness checks.

The material action retains:

```text
expected_version = Profile.profile_version
```

and carries the eligibility-specific revision contract in `proposed_change`:

```text
eligibility_aggregate_key
expected_eligibility_revision_version
expected_eligibility_revision_id
next_eligibility_revision_version
```

The durable E.2 governance attempt records the same facts so later stages reconstruct the accepted action rather than infer new concurrency state.

An already-existing canonical revision with no explicit reassessment expectation fails before model egress.

## G.2 integration

G.2 reconstructs the exact accepted E.2 `MaterialAction`, including the eligibility revision expectation.

Fresh verification-floor integration revalidates the canonical revision and fails closed if it moved after E.2.

A narrowly-scoped `require_current_revision=False` reconstruction path exists only to resolve durable historical replay. It does not authorize fresh reassessment and is not a bypass for normal execution.

## Time-of-check / time-of-use safety

The final accepted execution shape is:

```text
resolve expected canonical revision
→ governed E.2 proposal/runtime work
→ revalidate after runtime latency
→ F.1 Decision Readiness
→ G.1 blind independent verification
→ G.2 revision revalidation + verification floor
→ G.3 revision revalidation immediately before effect
→ fresh final Command Gateway authorization
→ atomic supersession transaction
```

An intervening canonical commit invalidates the earlier revision precondition.

## Atomic supersession contract

The G.3 canonical-effect transaction now supports both initial creation and explicit reassessment.

For reassessment, one transaction commits:

```text
fresh final authorization
+ prior ACTIVE revision → SUPERSEDED
+ new EligibilityAssessment
+ new EligibilityAssessmentRevision vN+1 ACTIVE
+ supersedes_revision_id → prior revision
+ canonical governance Activity
+ semantic MATERIAL Activity
```

Any failure rolls back the entire transition, including the lifecycle change on the prior revision.

Prior assessment/revision content is never rewritten in place.

There must be exactly one ACTIVE canonical revision for a healthy eligibility aggregate after commit.

## Historical replay

Historical effect identity is distinct from the currently active aggregate revision.

After:

```text
v1 ACTIVE
→ v2 ACTIVE / v1 SUPERSEDED
```

an exact retry of the original v1 idempotency key still resolves the original v1 canonical effect.

The replay path:

- does not call provider models again;
- does not require the persisted revision to remain ACTIVE;
- computes/validates effect identity against the persisted revision's actual version;
- preserves assessment, governance, verification-floor and semantic lineage checks;
- fails closed on torn or conflicting durable state.

The same principle applies to later revisions: supersession does not erase replayability.

## G.4 orchestration integration

The domain-specific G.4 orchestrator accepts:

```text
expected_eligibility_revision_version: int | None
```

Initial v1 creation omits it.

A reassessment must explicitly supply the version believed current.

The orchestrator continues to receive provider/runtime selection and `CapabilityAuthority` only through the trusted server-side `GovernedEligibilityExecutionPlan`.

A post-commit retry resolves durable effect lineage before model execution. Reusing an idempotency key with a different revision expectation is rejected before either model is called.

## Governed HTTP boundary

`POST /api/v1/organization/eligibility/orchestrate` now permits one additional request field:

```json
{
  "expected_eligibility_revision_version": 1
}
```

When supplied it must be at least `1`.

This field is a caller concurrency assertion only. It is not authority, autonomy, risk or execution policy.

Request JSON still cannot choose:

```text
tenant authority
producer/verifier OrganizationPosition
provider
model
autonomy level
risk tier
scope
CapabilityAuthority
```

`ConfigDict(extra="forbid")` remains in force.

The authenticated human initiator does not become the material actor. The producer `OrganizationPosition` remains the action actor.

## Verification and authorization invariants

Every new canonical reassessment still traverses:

```text
E.2 proposal
→ F.1 Decision Readiness
→ G.1 blind independent verification
→ G.2 verification-floor integration
→ fresh Command Gateway authorization
→ G.3 atomic canonical effect
```

The constitutional R3 floor remains intact.

Scores may route; deterministic gates authorize.

Independent verification does not become authority.

Provider output does not become canonical truth automatically.

Operational autonomy must not create organizational opacity.

## Database contract

No migration was required for G.5.

The existing `EligibilityAssessmentRevision` model already contains:

```text
version
lifecycle_status
supersedes_revision_id
```

Accepted database truth remains:

```text
0077_canonical_eligibility_assessment_revision
registered tables 119
actual tables     119
physical tables   120 including alembic_version
```

## Acceptance evidence

Canonical Human Owner local evidence:

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
Actual tables                           119
Physical tables                         120 incl. alembic_version
git diff --check                        clean
V12 branch                              clean / synchronized
```

Detailed acceptance record:

- `docs/V1_3_G5_ACCEPTANCE_2026-08-20.md`

The observed warning is the existing Starlette/httpx TestClient deprecation warning and is non-blocking.

No GitHub CI PASS is claimed without attached status/check evidence.

## Deliberate non-claims

G.5 does not claim:

- client-facing eligibility publication;
- application mutation;
- government submission;
- unrestricted external execution;
- generic versioned-effect infrastructure;
- generic optimistic-concurrency framework;
- replacement of conservative `session.expire_all()` freshness boundaries;
- automatic autonomy promotion;
- Phase 13.17 PASS;
- GitHub CI PASS without evidence.

## Programme transition

G.5 is COMPLETE / PASS / SEALED.

The canonical next V1.3 stage is:

> **V1.3-H — Organizational Immune System + circuit breaking**

The next stage should use the governed material-effect and transparency foundations to detect unsafe organizational conditions, constrain execution deterministically, and support recovery without converting every anomaly into Human Owner / Board interruption.

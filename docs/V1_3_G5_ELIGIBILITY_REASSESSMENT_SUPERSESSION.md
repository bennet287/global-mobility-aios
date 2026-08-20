# Global Mobility AIOS — V1.3-G.5 Eligibility Reassessment / Supersession

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTATION IN PROGRESS / PRECONDITION FOUNDATION ACCEPTANCE PENDING

## Purpose

G.5 extends the accepted governed eligibility vertical from one canonical revision to safe, append-only reassessment and supersession.

The first implementation unit is deliberately the concurrency contract, not the v2 mutation itself.

Permanent rule:

> **A reassessment may supersede canonical eligibility truth only when it explicitly names the exact canonical revision it believes is current.**

This preserves the existing Profile-version precondition and prevents last-write-wins reassessment.

## Why a second version precondition is required

The accepted E.2 `MaterialAction.expected_version` already protects the immutable `Profile.profile_version` used to construct the eligibility proposal.

G.5 must not repurpose that field for canonical eligibility revision concurrency because doing so would trade away the Profile guard.

Therefore the final G.5 action contract will carry two distinct facts:

```text
Profile precondition
  MaterialAction.expected_version = Profile.profile_version

Canonical eligibility precondition
  expected_eligibility_revision_version = current EligibilityAssessmentRevision.version
```

These values protect different state and must never be conflated.

## Implemented precondition foundation

New bounded service:

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

## Accepted transition semantics targeted by G.5

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

## Time-of-check / time-of-use safety

The new precondition object is intentionally re-resolvable.

Target execution shape:

```text
resolve expected canonical revision
→ governed proposal/runtime work
→ readiness
→ blind independent verification
→ verification-floor integration
→ re-resolve exact canonical revision immediately before effect
→ fresh final Command Gateway authorization
→ atomic supersession transaction
```

`require_eligibility_revision_precondition_current(...)` proves an intervening canonical commit invalidates an earlier precondition.

## Historical replay requirement

G.5 must preserve durable idempotent replay as historical truth.

After:

```text
v1 ACTIVE
→ v2 ACTIVE / v1 SUPERSEDED
```

an exact retry of the original v1 idempotency key must still resolve the original v1 canonical effect. It must not fail merely because v1 is no longer active.

Likewise, a later v3 must not erase the replayability of v1 or v2.

This requires G.3/G.4 replay validation to distinguish:

```text
historical effect identity
```

from:

```text
currently active aggregate revision
```

before G.5 is sealed.

## Atomic supersession requirement

The future G.5 effect transaction must commit as one unit:

```text
fresh final authorization
+ prior ACTIVE revision -> SUPERSEDED
+ new EligibilityAssessment
+ new EligibilityAssessmentRevision vN+1 ACTIVE
+ supersedes_revision_id -> prior revision
+ semantic MATERIAL Activity
```

Any failure must roll back the entire transition, including the lifecycle change on the prior revision.

Prior assessment/revision content is never rewritten in place.

## Material-action integration still required

The precondition foundation does **not yet** claim reassessment execution.

Before G.5 can be accepted, the expected canonical eligibility revision must be wired through the accepted E.2→F.1→G.1→G.2→G.3/G.4 chain so that:

1. E.2 validates it before and after runtime latency;
2. the reconstructed eligibility `MaterialAction` carries it without changing the existing Profile `expected_version` meaning;
3. the durable E.2 attempt records it;
4. G.2 revalidates it before verification-floor authorization;
5. G.3 revalidates it immediately before the effect transaction;
6. the G.4 request may supply only this concurrency expectation as data, never runtime/provider/authority policy;
7. exact replay verifies the expected revision belongs to the persisted effect lineage.

Until that integration exists, G.5 is **not** COMPLETE and no v2 effect is authorized.

## No migration in the precondition foundation

The existing `EligibilityAssessmentRevision` model already contains the required fields:

```text
version
lifecycle_status
supersedes_revision_id
```

No schema change is required merely to define the concurrency contract.

Canonical migration truth therefore remains:

```text
0077_canonical_eligibility_assessment_revision
registered tables 119
actual tables     119
physical tables   120 including alembic_version
```

## Deliberate non-claims

This implementation unit does not claim:

- v2+ canonical effect creation;
- lifecycle supersession mutation;
- G.4 HTTP reassessment support;
- replacement of `session.expire_all()`;
- generic versioned-effect infrastructure;
- generic optimistic-concurrency framework;
- client-facing eligibility publication;
- application mutation or government submission.

## Focused acceptance gate for this implementation unit

Before integrating the contract into E.2/G.2/G.3/G.4, verify at minimum:

```text
apps/api/tests/test_organization_eligibility_revision_precondition.py
apps/api/tests/test_organization_eligibility_effect.py
```

The focused tests must prove:

- initial v1 requires absence of an active canonical revision;
- existing v1 requires an explicit expected revision for reassessment;
- exact expected v1 resolves legal next version v2 and the correct supersedes target;
- stale/invalid expectations fail closed;
- an intervening canonical commit invalidates a previously resolved no-revision precondition;
- existing G.3 v1/replay behavior remains green.

ROADMAP/CHANGELOG remain at accepted V12.16 until this foundation and its downstream integration are observed through canonical local test evidence.

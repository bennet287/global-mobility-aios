# Global Mobility AIOS — V1.3-G.2 Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted implementation head:** `8d04aa4a990b0cab9b360277897ecf6e8d429780`  
**Status:** COMPLETE / PASS / SEALED

## Accepted capability

V1.3-G.2 establishes the accepted deterministic bridge between a durable, genuinely independent G.1 agreement and the existing V1.3 Command Gateway.

Accepted flow:

```text
E.2 governed eligibility proposal
→ F.1 READY_FOR_INDEPENDENT_VERIFICATION
→ G.1 blind independent AGREES verification
→ G.2 validates exact lineage and freshness
→ reconstruct the exact E.2 MaterialAction
→ remove only the temporary HUMAN_REQUIRED verification policy floor
→ existing Command Gateway re-evaluates with PolicyDisposition.ALLOW
→ authority / scope / risk / version / autonomy remain Gateway-owned
→ no canonical eligibility effect yet
```

Permanent rule:

> **Independent verification may satisfy the R3 verification floor; only the Command Gateway may determine whether the material action is authorized for execution.**

G.2 does not mutate eligibility truth and does not consume the canonical successful material-action idempotency slot that will belong to the future eligibility-effect transaction.

## Canonical local acceptance evidence

The Human Owner reported the following results on a clean synchronized checkout at the accepted implementation head.

```text
G.2 focused                    14 passed / 1 warning / 0 failed
G.1 + G.2                     29 passed / 1 warning / 0 failed
E.2 + F.1 + G.1 + G.2         56 passed / 1 warning / 0 failed
D.1–D.3 + E.1–E.2 + F.1–G.2  95 passed / 1 warning / 0 failed
Repository policy              PASS
Full API regression            1025 passed / 5 skipped / 1 warning / 0 failed
Full API duration              536.84s
Database migration check       PASS
Migration head                 0076_organization_position_active_identity
Registered tables              118
Physical schema                PASS
Local DB schema                PASS
Actual tables                  118
Physical tables                119 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

Known non-blocking warning remains:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

No dependency change is implied by this acceptance.

## Accepted G.2 invariants

### Verification-floor satisfaction is not authorization

A valid G.1 `AGREES` result allows G.2 to remove only the explicit temporary E.2 `HUMAN_REQUIRED` verification policy floor.

The existing Command Gateway still owns all other authorization decisions.

Accepted post-verification routing remains:

```text
A0      → BLOCK / AUTONOMY_PROHIBITED
A1/A2   → REVIEW_REQUIRED / AUTONOMY_REVIEW_REQUIRED
A3      → AUTO_EXECUTE / AUTHORIZED + post_review_required=true
A4/A5   → AUTO_EXECUTE / AUTHORIZED
```

Wrong actor authority, denied scope, excessive risk, stale expected version, policy denial or Board-reserved authority still fail through the existing Gateway rather than being overridden by verifier agreement.

### Exact action reconstruction

G.2 reconstructs the same accepted E.2 material action and requires the re-evaluated action fingerprint to equal the original E.2 fingerprint.

The accepted action contract remains:

```text
action_type       eligibility.transition
capability        mobility.eligibility
subject_type      lead_eligibility
subject_id        Lead.id
expected_version  Profile.profile_version
scope             <country>:<domain>
consequence       APPEND_ONLY_CORRECTION
```

The eligibility subject is therefore explicitly scoped to the accepted immutable profile version even though the subject identifier is the Lead.

### Freshness and lineage

Before re-evaluation, G.2 recomputes F.1 Decision Readiness and validates the durable G.1 result against the exact E.2 trace, attempt, proposer employee, runtime binding and verification fingerprint.

A case/context change after G.1 fails closed before a G.2 floor Activity is persisted.

Accepted lineage is:

```text
E.2 governance attempt
    ↓ causation_activity_id
G.1 independent verification Activity
    ↓ causation_activity_id
G.2 verification-floor re-evaluation Activity
```

All three remain correlated to the original E.2 trace and Board-inspectable through the existing transparency substrate.

### Canonical idempotency slot remains unused

G.2 persists a distinct deterministic floor record:

```text
governance:verification-floor:<verification_floor_fingerprint>
```

It deliberately does not write:

```text
governance:<original E.2 idempotency key>
```

The accepted tests prove an exact G.2 rerun reuses the same floor Activity without creating a duplicate and still leaves the future canonical governance slot unused.

That slot remains reserved for the transaction that actually commits the first canonical eligibility effect.

### No canonical mutation

G.2 creates no:

- `EligibilityAssessment`;
- Lead eligibility-state mutation;
- application mutation;
- client-facing recommendation;
- external communication;
- government submission;
- canonical successful material-action governance record.

Accepted result flags remain:

```text
verification_floor_satisfied  = true
gateway_authorized_for_execution = Gateway outcome dependent
eligible_for_effect_integration   = true only for AUTO_EXECUTE
canonical_effect_committed     = false
mutated                        = false
```

## No migration

G.2 introduces no database migration. The accepted migration head remains:

```text
0076_organization_position_active_identity
```

## CI truth

No GitHub CI PASS is claimed. Acceptance is based on the reported local canonical checks above; attached GitHub status checks were not present on the implementation head when inspected.

## Direction after G.2

The next bounded slice is the first canonical eligibility-effect contract.

Before any mutation is enabled, AIOS must explicitly define:

- canonical `EligibilityAssessment` identity;
- version / supersession semantics;
- immutable Profile-version binding;
- linkage to E.2 intent, F.1 readiness, G.1 verification and G.2 floor re-evaluation;
- canonical successful `governance:<idempotency_key>` ownership;
- semantic effect Activity and explicit causation;
- one atomic governance + effect transaction;
- replay/idempotency behavior;
- no automatic client-facing or external action.

The legacy eligibility router/engine must not be treated as proof that these new governed effect semantics already exist.

Do not generalize into a Peer Review Network, Mission Room, Flight Recorder or Munder runtime fabric before the first governed eligibility effect is proven end to end.

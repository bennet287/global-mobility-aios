# Global Mobility AIOS — V1.3-G.2 Eligibility Verification-Floor Integration

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** COMPLETE / PASS / SEALED

## Purpose

G.2 is the bounded bridge between the accepted G.1 blind independent-verification result and the existing V1.3 Command Gateway.

It answers one narrow question:

> When a durable, genuinely independent G.1 verifier agrees with an F.1-ready E.2 proposal, how may AIOS remove the temporary E.2 `HUMAN_REQUIRED` verification policy floor without letting the verifier itself authorize the eligibility action?

The answer is deliberately simple:

```text
accepted E.2 REVIEW_REQUIRED proposal
→ accepted F.1 READY_FOR_INDEPENDENT_VERIFICATION
→ accepted durable G.1 AGREES verification
→ G.2 validates exact lineage and freshness
→ rebuild the exact E.2 MaterialAction
→ policy_disposition changes only from HUMAN_REQUIRED to ALLOW
→ existing Command Gateway re-evaluates from scratch
```

G.2 does not change the generic governance kernel and does not mutate eligibility state.

Permanent rule:

> **Independent verification may satisfy the R3 verification floor; only the Command Gateway may determine whether the resulting material action is authorized for execution.**

## Why the governance kernel is unchanged

Repository verification established that `evaluate_material_action(...)` already owns the required deterministic gates in the right order:

1. tenant / actor authority;
2. capability / action authority;
3. scope;
4. risk ceiling;
5. expected version;
6. durable idempotency;
7. policy denial;
8. Board-reserved authority;
9. policy-required human review;
10. A0 prohibition;
11. A1/A2 review;
12. A3+ autonomous routing.

E.2 deliberately supplied `PolicyDisposition.HUMAN_REQUIRED` for A1–A5 because independent verification did not yet exist. A0 deliberately used `ALLOW` so prohibition remained `BLOCK / AUTONOMY_PROHIBITED`.

After accepted independent verification, G.2 supplies `PolicyDisposition.ALLOW` and changes nothing else.

The same Gateway therefore produces the correct post-verification semantics:

```text
A0      → BLOCK / AUTONOMY_PROHIBITED
A1/A2   → REVIEW_REQUIRED / AUTONOMY_REVIEW_REQUIRED
A3      → AUTO_EXECUTE / AUTHORIZED + post_review_required=true
A4/A5   → AUTO_EXECUTE / AUTHORIZED
```

Authority, scope, risk, version and Board-reserved checks still take precedence exactly as before.

## G.2 input contract

`integrate_eligibility_verification_floor(...)` consumes:

- the accepted E.2 `GovernedEligibilityTransitionIntentResult`;
- the accepted F.1 `EligibilityDecisionReadinessResult`;
- the accepted G.1 `GovernedIndependentEligibilityVerificationResult`;
- the current `CapabilityAuthority` for the proposing organizational employee.

G.2 accepts only a G.1 result that is durably `AGREES` and that still carries:

```text
independent_verification_completed          = true
eligible_for_verification_floor_integration = true
command_gateway_floor_satisfied             = false
authorization_effect                        = false
canonical_commit_allowed                    = false
```

The last three false values are important. G.1 is evidence of independent verification, not authority.

## Freshness and lineage validation

Before re-evaluating the action, G.2:

1. recomputes F.1 Decision Readiness;
2. requires the same readiness fingerprint;
3. verifies the G.1 result belongs to the exact E.2 trace, E.2 attempt, proposer employee and proposer runtime binding;
4. loads the durable G.1 Activity;
5. verifies its physical/constitutional transparency contract;
6. verifies its `AGREES` disposition and exact verification fingerprint;
7. verifies blind-review and non-authorizing flags;
8. loads the durable E.2 attempt;
9. recovers the original E.2 idempotency key;
10. reconstructs the same E.2 material action from current accepted objects.

A case/context change after G.1 causes F.1 freshness to fail before G.2 can create a verification-floor record.

## Exact MaterialAction reconstruction

G.2 reconstructs the E.2 action with the same semantic fields:

```text
action_type       eligibility.transition
capability        mobility.eligibility
subject_type      lead_eligibility
subject_id        Lead.id
expected_version  Profile.profile_version
scope             <country>:<domain>
consequence       APPEND_ONLY_CORRECTION
```

The proposed change remains:

```text
proposed_state
profile_id
profile_version
pathway_version_id
context_hash
runtime_binding_hash
intent_fingerprint
```

Evidence references remain the validated E.2 Evidence and VerifiedRule basis, and rationale remains the accepted E.2 rationale.

G.2 requires the newly computed Gateway action fingerprint to equal the original E.2 action fingerprint exactly.

That proves independent verification did not quietly alter the action being authorized.

## Verification-floor fingerprint

G.2 computes a deterministic floor fingerprint over:

- E.2 trace and action fingerprint;
- F.1 readiness fingerprint;
- G.1 verification fingerprint;
- current capability authority, including autonomy, risk ceiling and scopes.

This gives the re-evaluation a stable identity without consuming the canonical material-action idempotency slot.

## Canonical idempotency slot is deliberately NOT consumed

The existing successful material-command pattern reserves:

```text
governance:<idempotency_key>
```

for the governance authorization that is committed atomically with the real canonical effect.

G.2 does not yet perform that effect. If G.2 wrote the canonical success record now, the later effect command could observe `IDEMPOTENT_REPLAY` before any eligibility mutation had ever happened.

Therefore G.2 persists its own distinct record:

```text
governance:verification-floor:<verification_floor_fingerprint>
```

The future canonical eligibility-effect transaction keeps the original E.2 idempotency key and its canonical `governance:<idempotency_key>` slot untouched.

An exact G.2 rerun reuses the deterministic floor record rather than creating duplicate verification-floor Activities.

## Durable lineage

The accepted trace is:

```text
E.2 governance attempt
    ↓ causation_activity_id
G.1 independent verification Activity
    ↓ causation_activity_id
G.2 verification-floor re-evaluation Activity
```

All three share the original E.2 trace correlation key.

The G.2 record carries the Gateway projection, plus:

- G.2 schema/version;
- verification-floor fingerprint;
- `verification_floor_satisfied = true`;
- G.1 verification fingerprint and Activity id;
- F.1 readiness fingerprint;
- original E.2 action fingerprint;
- fresh Gateway authorization result;
- explicit no-effect/no-mutation flags.

## Floor satisfaction is not authorization

G.2 intentionally distinguishes:

```text
verification_floor_satisfied
```

from:

```text
gateway_authorized_for_execution
eligible_for_effect_integration
```

Examples:

```text
valid G.1 AGREES + A0
→ verification_floor_satisfied = true
→ Gateway BLOCK / AUTONOMY_PROHIBITED
→ eligible_for_effect_integration = false

valid G.1 AGREES + A1/A2
→ verification_floor_satisfied = true
→ Gateway REVIEW_REQUIRED / AUTONOMY_REVIEW_REQUIRED
→ eligible_for_effect_integration = false

valid G.1 AGREES + A3/A4/A5 + all other gates satisfied
→ verification_floor_satisfied = true
→ Gateway AUTO_EXECUTE / AUTHORIZED
→ eligible_for_effect_integration = true
```

Even the final case does not mean the eligibility effect has already been committed.

## Safety flags

G.2 always returns:

```text
canonical_effect_committed = false
mutated                    = false
```

`eligible_for_effect_integration` may become true only when the actual Gateway result is `AUTO_EXECUTE`.

G.2 creates no:

- `EligibilityAssessment`;
- Lead eligibility-state mutation;
- application mutation;
- external communication;
- government submission;
- client-facing recommendation;
- canonical `governance:<idempotency_key>` success record.

## Tests

`apps/api/tests/test_organization_eligibility_verification_floor.py` covers the bounded G.2 contract, including:

1. accepted G.1 agreement satisfies the verification floor and allows A5 Gateway authorization without mutation;
2. A0 remains prohibited;
3. A1 remains review-required;
4. A2 remains review-required;
5. A3 may auto-execute but remains post-review-required;
6. A4 may auto-execute;
7. A5 may auto-execute;
8. forged/non-agreeing verification is rejected;
9. stale case state after G.1 fails before G.2 persistence;
10. actor authority remains Gateway-owned;
11. scope remains Gateway-owned;
12. risk ceiling remains Gateway-owned;
13. exact G.2 reruns reuse the same floor record;
14. the canonical `governance:<idempotency_key>` slot remains unused;
15. trace causation remains E.2 → G.1 → G.2;
16. no `EligibilityAssessment` is created by G.2.

Parameterization collects 14 focused pytest cases in the accepted implementation.

## Migration posture

G.2 introduces no migration.

It reuses the accepted:

- Command Gateway;
- `CapabilityAuthority`;
- `MaterialAction`;
- E.2 durable attempt;
- F.1 deterministic readiness;
- G.1 durable blind verification;
- `OrganizationActivity` and trace transparency substrate.

## Acceptance evidence

Canonical acceptance is sealed in:

```text
docs/V1_3_G2_ACCEPTANCE_2026-08-20.md
```

Accepted evidence:

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
Local DB schema                PASS
Actual tables                  118
Physical tables                119 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

No GitHub CI PASS is claimed without attached check evidence.

## Non-claims

G.2 does not claim:

- canonical eligibility truth;
- an `EligibilityAssessment` versioning model;
- eligibility mutation;
- generic verification framework completion;
- generic Peer Review Network completion;
- provider-egress policy completion;
- GitHub CI PASS.

## Direction after G.2

The next bounded slice is the first canonical eligibility effect.

That slice must first define explicit `EligibilityAssessment` identity/version/lineage semantics instead of silently mutating the legacy aggregate.

Target shape:

```text
accepted G.2 eligible_for_effect_integration
→ canonical eligibility-effect contract
→ canonical governance:<idempotency_key> authorization
→ EligibilityAssessment effect
→ semantic Activity caused by governance authorization
→ one atomic transaction
```

Do not generalize this into a universal verification bus or Peer Review Network before the first governed eligibility effect is proven end to end.

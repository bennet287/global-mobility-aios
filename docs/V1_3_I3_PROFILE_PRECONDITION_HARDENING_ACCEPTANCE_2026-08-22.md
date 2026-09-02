# Global Mobility AIOS — V1.3 I.3 Profile-Precondition Hardening Acceptance — 2026-08-22

**Scope:** post-acceptance refinement of V1.3-I.3 Autonomy Promotion Eligibility Policy Foundation
**Status:** ACCEPTED / PASS / SEALED HARDENING
**Parent I.3 acceptance:** technical candidate `77b2e9adb30d69419158930b31c0bc10515cb6a7`, Production Proof run `32536826352`
**Hardening technical candidate:** `108231d75b4c7413c1759c003e121fdcca206d7c`
**Hardening Production Proof:** GitHub Actions run `32539026789`
**Migration head:** `0080_capability_autonomy_promotion_policy_foundation` — unchanged
**Registered application tables:** 123 — unchanged

## 1. Why this refinement exists

The accepted I.3 exact-profile binding already guaranteed that a policy written for an older I.1 profile could not become current eligibility policy after profile supersession.

A later adversarial review identified a narrower command-concurrency issue:

```text
I.3 writer observes current profile v1
→ concurrent I.1 transaction supersedes v1 with v2
→ I.3 writer could still report successful policy creation for now-historical v1
```

The resulting policy was safe and inert because I.3 policy truth is frozen to exact `profile_id`; it could not apply to v2 or change autonomy. However, a canonical Board write should also have linearizable success semantics: a new policy write must succeed only for a profile that is still current at the serialization point.

This refinement closes that gap without changing I.3 authority or autonomy semantics.

## 2. Accepted writer hardening

`establish_capability_autonomy_promotion_policy(...)` now accepts an optional optimistic caller precondition:

```text
expected_profile_id
```

When supplied, a mismatch with the observed current I.1 profile fails immediately with a stale-profile transition error.

For every new policy write, regardless of whether the optional caller precondition is supplied, the service additionally:

1. captures the current validated I.1 profile identity;
2. acquires the exact `CapabilityAutonomyProfile` row lock on PostgreSQL with `FOR UPDATE`;
3. reruns the canonical I.1 profile snapshot after acquiring that lock;
4. rejects the command if the locked profile is no longer the current leaf;
5. revalidates current autonomy level, evidence-policy version and Board ceiling under the profile lock;
6. acquires/validates the exact-profile policy lineage;
7. performs a final locked current-profile recheck before atomic audit/policy commit.

The I.1 supersession writer already locks the current profile row before appending its successor. Therefore I.1 supersession and I.3 policy establishment now serialize on the same canonical profile leaf.

## 3. Concurrency semantics proven

The accepted serialization rule is:

```text
if I.3 wins the current-profile row lock first:
    I.1 supersession waits until the policy transaction completes;
    the policy genuinely targeted the current profile at commit serialization.

if I.1 supersession wins the current-profile row lock first:
    v2 becomes current;
    the waiting I.3 writer resumes, revalidates v1, and rejects stale;
    no policy is persisted for the now-historical v1 command attempt.
```

This is stricter than merely making stale policy inert.

## 4. Accepted adversarial proof

Two new contracts are included.

### Fast backend contract

`test_organization_autonomy_promotion_profile_precondition.py` proves that:

- same-level v1 → v2 profile supersession can preserve A2 and the evidence-policy version;
- `expected_profile_id=v1` is rejected as stale;
- `expected_profile_id=v2` succeeds and binds exactly to v2.

### Real PostgreSQL lock-race contract

`test_postgres_i3_policy_rejects_profile_supersession_that_wins_profile_lock` deliberately creates the supersession-wins ordering:

1. lock I.1 v1 with `FOR UPDATE` in the supersession transaction;
2. start an I.3 writer for expected v1 in another PostgreSQL session;
3. prove through `pg_stat_activity.wait_event_type = Lock` that the I.3 writer is actually waiting on the profile lock;
4. append and commit I.1 v2 while the supersession transaction owns the lock;
5. allow I.3 to resume;
6. require stale-profile rejection;
7. prove zero policy rows were persisted for the stale v1 attempt.

The test exercises the real PostgreSQL transaction/row-lock contract rather than simulating it in SQLite.

## 5. Exact hardening Production Proof

GitHub Actions run `32539026789` checked out exact technical candidate:

```text
108231d75b4c7413c1759c003e121fdcca206d7c
```

Accepted results:

```text
Repository policy and constraints             PASS
Release consistency                           PASS — 0080
Python dependency constraints                 PASS
Diff hygiene                                  PASS

Backend regression (SQLite)                   1159 passed / 16 skipped / 1 warning / 0 failed
SQLite migration consistency                  PASS — 0080
SQLite registered application tables          123
SQLite actual application tables              123
SQLite physical schema                        PASS
Local schema contract                         PASS

Frontend dependency install/audit             PASS
Frontend design foundation                    PASS
Frontend request/auth                         PASS
Frontend TypeScript                           PASS
Frontend production build                     PASS
Frontend compiled-auth verification           PASS

PostgreSQL 16 Alembic                         PASS — 0001 → 0080
PostgreSQL migration/schema contract           PASS
PostgreSQL registered application tables      123
PostgreSQL physical schema                    PASS
PostgreSQL governed suite                     99 passed / 1 warning / 0 failed
I.3 profile-supersession lock race             PASS

V12 Production Proof run 32539026789          4 / 4 jobs PASS
```

The known Pydantic `model_metadata_json` protected-namespace warning remains visible and non-blocking.

A duplicate-key message on `organization_activity_streams` can appear in PostgreSQL service logs during intentionally adversarial concurrent canonical-write tests. The governed pytest suite passed; the service-log conflict is expected race pressure, not a failed proof.

## 6. No schema or authority expansion

This refinement introduces:

```text
no new table
no Alembic migration
no new API mutation route
no autonomy-level mutation
no Board-ceiling mutation
no CapabilityAuthority grant
no Command Gateway authority change
no automatic promotion/demotion
```

Migration remains `0080_capability_autonomy_promotion_policy_foundation` with 123 registered application tables.

## 7. Review disposition

The review that motivated this hardening contained several separate concerns. Their accepted disposition is:

```text
Production Proof unconfirmed             FALSE / review-environment limitation;
                                         authenticated exact-head proof exists.

Policy/profile supersession race         VALID / FIXED / PROVEN by this hardening.

I.2 caller-attested quality facts         VALID future pre-mutation concern;
                                         deferred to I.4 evidence qualification.

Static freshness / lifetime evidence     VALID future pre-mutation concern;
                                         deferred to I.4 temporal evaluation.

Unbounded evidence transparency          VALID production-scale concern;
                                         bounded/paginated read work remains later.

I.2 boolean/low-cardinality indexing      PLAUSIBLE optimization concern;
                                         measure query plans/workload before changing.
```

The deferred concerns do not grant permission to consume current `ELIGIBLE` as an autonomy-change command.

## 8. Future sequencing rule

I.3 remains a non-authorizing eligibility foundation.

Before any actual autonomy-changing increment can consume I.3 eligibility, the repository must separately establish and prove an I.4 boundary covering at least:

```text
typed/source-qualified autonomy evidence
deterministic derivation from canonical execution/review/verification/incident/recovery truth
policy-controlled temporal evaluation boundaries
maximum observation age / rolling windows where appropriate
minimum recent execution/review evidence
bounded or paginated provenance transparency
query-driven data-access/index hardening before production-scale evidence volume
```

No automatic promotion, downgrade or Dynamic Autonomy Manager is pre-authorized by this hardening.

## 9. Seal

The I.3 profile-precondition/concurrency hardening is **ACCEPTED / PASS / SEALED** on technical candidate `108231d75b4c7413c1759c003e121fdcca206d7c`, proven by GitHub Actions run `32539026789`.

The original I.3 acceptance record remains historically correct for the foundation candidate `77b2e9adb30d69419158930b31c0bc10515cb6a7`. This document records the later, separately proven command-concurrency refinement.
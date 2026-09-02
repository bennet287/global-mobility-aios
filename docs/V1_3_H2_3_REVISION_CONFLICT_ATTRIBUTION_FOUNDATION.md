# Global Mobility AIOS — V1.3 H.2.3 Eligibility Revision-Conflict Attribution Foundation

**Stage:** V1.3-H.2.3
**Status:** COMPLETE / PASS / SEALED
**Accepted technical candidate:** `17edeca46af2b9cc7e0a6111ec2b3270f4bb1283`
**Accepted Production Proof:** GitHub Actions run `32480405051`
**Implementation candidate:** `870520af3fc69e5f17145502ec6c8de079353daa`
**Parent accepted checkpoint:** V1.3-H.2.2 — `c5c2a68ac3a9caf2551204d61862b6ad0b6281eb`
**Parent accepted Production Proof:** run `32473526874`

## 1. Purpose

H.2.3 adds durable attribution for one already-proven G.5 failure mode: a reassessment reaches the canonical revision precondition with an expectation that was previously current but has already been superseded by a newer ACTIVE revision.

This increment is measurement/provenance only. It does not create a new circuit threshold, wider quarantine rule, authority grant, autonomy grant or recovery automation.

Permanent boundary:

> The Immune System may restrict or stop execution. It never grants authority, autonomy or permission.

H.2.3 additionally preserves:

> Optimistic-concurrency contention is not automatically a safety fault.

## 2. Exact attributed condition

A revision conflict is attributable in H.2.3 only when all of the following are true:

```text
canonical eligibility aggregate exists
exactly one ACTIVE canonical revision exists
caller supplied expected_eligibility_revision_version >= 1
expected revision < current ACTIVE revision version
conflict is detected by the initial G.5 precondition before producer provider egress
```

The canonical G.5 resolver exposes this exact case as `EligibilityRevisionPreconditionConflict`, a narrow subtype of the existing stale-precondition failure.

The following remain ordinary fail-closed G.5 errors and are not H.2.3 incidents:

```text
missing expected revision for reassessment
expected revision < 1
expected revision > current revision
expected revision supplied when no canonical revision exists
multiple ACTIVE revisions / aggregate corruption
tenant or aggregate integrity failures
revision changes discovered only during post-provider revalidation
request/schema errors
```

The lower-than-current rule is deliberate false-positive containment: it identifies a caller that demonstrably observed an older canonical revision, rather than treating an impossible future expectation as recurrence evidence.

## 3. Durable attribution pair

For one accepted pre-egress stale-reassessment conflict, AIOS persists one atomic pair in the existing aggregate immune stream:

```text
organization.immune.eligibility_revision_conflict_attributed.v1
+
organization.immune.eligibility_incident.v1
  kind = revision_conflict
```

The attribution records:

```text
failure_stage = g5_revision_precondition_pre_egress
conflict_basis = superseded_expected_revision
expected_revision_version
observed_current_revision_id
observed_current_revision_version
observed_current_lifecycle_status = active
provider_egress_occurred = false
control_effect = observation_only
authority_effect = none
recurrence_policy_applied = false
```

The observed revision identity is reconciled against the durable canonical revision row before a new attribution pair is written.

## 4. Replay and atomicity

H.2.3 follows the accepted H.2.2 pairing discipline without introducing a generic framework:

- attribution and warning are committed as one transactional pair;
- failure after attribution staging rolls back the pair;
- exact replay reuses the same pair;
- a torn pair fails closed;
- the same incident key cannot be replayed with a changed conflict snapshot;
- no timestamp-only duplicate attribution is created.

## 5. Circuit and recurrence semantics

`revision_conflict` remains an H.1 WARNING kind.

H.2.3 does not add it to the H.2.1 recurrence policy:

```text
severity                  = warning
automatic circuit action  = none
recurrence threshold      = none
blast radius              = none
circuit effect            = CLOSED remains CLOSED
authority effect          = none
autonomy effect           = none
```

Repeated revision-conflict observations therefore remain observation-only in this increment.

A future restrictive policy would require a separate accepted contract defining at minimum a measurement window, threshold, contention semantics, false-positive controls, blast radius and recovery behavior.

## 6. Recovery semantics

H.2.3 does not perform automatic recovery.

The operational recovery for a stale reassessment remains:

```text
reread the current canonical eligibility revision
construct a new reassessment against that exact current revision
submit with a fresh idempotency key
```

This is normal optimistic-concurrency recovery, not an authority or circuit-recovery action.

## 7. Accepted proof

The accepted candidate proves:

1. a real `v1 -> v2` stale reassessment expecting `v1` is attributed before provider egress;
2. producer and verifier providers receive zero calls for that stale attempt;
3. the durable attribution records expected `v1` and observed current `v2` identity;
4. the paired immune incident is `revision_conflict / warning` with no automatic circuit action;
5. missing expectations do not create revision-conflict incidents;
6. future expectations do not create revision-conflict incidents;
7. an expectation against a nonexistent canonical revision does not create an H.2.3 incident;
8. exact replay does not duplicate the pair;
9. repeated conflict observations do not open the aggregate circuit;
10. post-provider revision revalidation remains generic stale state and is not classified as the pre-egress subtype;
11. failure between attribution staging and incident persistence rolls back atomically;
12. replay with a changed conflict snapshot fails closed;
13. an incident-only/torn pair fails closed rather than being silently repaired;
14. fresh PostgreSQL 16 runs the H.2.3 normal and adversarial contracts successfully;
15. broad SQLite backend, frontend, migration/schema and repository-policy lanes remain green.

### 7.1 Accepted GitHub Production Proof

```text
run                                      32480405051
head                                     17edeca46af2b9cc7e0a6111ec2b3270f4bb1283
workflow conclusion                      completed / success
Repository policy and constraints        PASS
Backend regression (SQLite)              PASS
Frontend tests, types and build          PASS
PostgreSQL governance contracts          PASS
```

### 7.2 Backend SQLite evidence

```text
full backend regression                   1127 passed
skipped                                   8
known warning                              1
failed                                     0
Alembic SQLite 0001 -> 0077               PASS
migration/physical schema                 PASS
registered tables                         119
local schema contract                     PASS
```

### 7.3 PostgreSQL 16 evidence

```text
fresh PostgreSQL 16                       PASS
Alembic 0001 -> 0077                      PASS
migration head                            0077_canonical_eligibility_assessment_revision
registered SQLModel tables                119
physical schema                           PASS
governed eligibility suite                80 passed / 1 warning / 0 failed
H.2.3 normal attribution tests            PASS
H.2.3 adversarial false-positive tests    PASS
H.2.3 torn-pair fail-closed               PASS
H.2.3 rollback atomicity                  PASS
H.2.3 conflict-snapshot drift rejection   PASS
```

### 7.4 Frontend and repository evidence

The accepted run also proves constrained dependency installation, `pip check`, Python compilation, repository policy, release consistency, direct Python dependency constraints, `git diff --check HEAD^`, `npm ci`, the high-severity frontend dependency audit, design foundation tests, request/auth tests, TypeScript, Next.js production build and compiled-auth tests.

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

## 8. Acceptance note on the superseded failed run

The first H.2.3 proof run (`32479407154`) already passed repository policy, frontend and PostgreSQL. Its broad SQLite lane found one stale pre-H.2.3 regression assertion that expected the former generic `proposal stage failed` message. The H.2.3 behavior itself had correctly produced the new specific pre-egress revision-conflict error and zero provider calls.

Commit `17edeca46af2b9cc7e0a6111ec2b3270f4bb1283` changed only that legacy test expectation. No H.2.3 runtime implementation changed. The replacement run `32480405051` then passed all four Production Proof jobs.

## 9. Explicit non-claims

H.2.3 does not claim or authorize:

- revision-conflict recurrence thresholds;
- aggregate circuit opening from revision conflicts;
- cross-aggregate contention aggregation;
- user-, agent-, tenant- or provider-wide quarantine;
- automatic retry;
- automatic reassessment rebasing;
- automatic conflict resolution;
- post-provider race attribution;
- reassessment rollback policy;
- H.2 completion;
- Earned Autonomy.

## 10. Accepted checkpoint state

```text
H.1      COMPLETE / PASS / SEALED
H.2.1    COMPLETE / PASS / SEALED
H.2.2    COMPLETE / PASS / SEALED
H.2.3    COMPLETE / PASS / SEALED
H.2      IN PROGRESS
H.2.4    NOT STARTED
I        NOT STARTED
```

Any later restriction based on revision-conflict frequency must receive a separate failure-model, scope/window, threshold, blast-radius, false-positive and recovery contract before implementation.
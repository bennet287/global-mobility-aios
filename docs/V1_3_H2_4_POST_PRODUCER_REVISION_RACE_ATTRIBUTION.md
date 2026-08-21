# Global Mobility AIOS — V1.3 H.2.4 Post-Producer Revision-Race Attribution

**Stage:** V1.3-H.2.4
**Status:** IMPLEMENTATION CANDIDATE / PRODUCTION PROOF PENDING
**Parent accepted checkpoint:** V1.3-H.2.3 — `17edeca46af2b9cc7e0a6111ec2b3270f4bb1283`
**Parent reconciled branch head:** `6ce751047b3a1cdd96f601d7c313eb847feebb1a`

## 1. Purpose

H.2.4 covers one concrete optimistic-concurrency race that H.2.3 deliberately excluded.

A governed reassessment begins against the exact current canonical eligibility revision. The producer runtime is then called. While that producer call is in flight, another governed reassessment commits a newer canonical revision for the same aggregate. When E.2 revalidates the previously accepted revision precondition after producer latency, the original revision is no longer current.

The result is safe but operationally meaningful:

```text
producer provider egress occurred
verifier provider egress did not occur
canonical eligibility effect did not occur
stale producer work must not silently proceed
```

H.2.4 makes that bounded failure explainable and durable. It does not turn optimistic-concurrency contention into an automatic safety fault.

Permanent boundaries:

> The Immune System may restrict or stop execution. It never grants authority, autonomy or permission.

> Optimistic-concurrency contention is not automatically a safety fault.

## 2. Exact failure model

H.2.4 attribution is valid only when all of the following are true:

```text
canonical eligibility aggregate exists
exactly one ACTIVE revision vN exists
caller explicitly expects revision vN
E.2 accepts that exact revision precondition before producer egress
producer provider is called
another governed operation commits a newer ACTIVE revision vM where M > N
E.2 detects that advancement at its immediate post-producer revision revalidation
verifier provider has not been called
no canonical effect from the stale attempt has been committed
```

The accepted precondition must therefore be a real reassessment precondition:

```text
expected_revision_version == resolved_current_revision_version >= 1
resolved_current_revision_id is not null
```

The observed revision must be a later canonical revision in the same tenant and aggregate:

```text
observed_current_revision_version > resolved_current_revision_version
observed_current_revision_id != resolved_current_revision_id
```

## 3. Explicit exclusions

H.2.4 does not classify:

- H.2.3 pre-egress stale reassessment conflicts;
- missing revision expectations;
- future revision expectations;
- concurrent first-time canonical creation where the original precondition had no current revision;
- multiple-ACTIVE-revision corruption;
- missing/deleted canonical lineage;
- producer runtime/provider failure;
- malformed producer output;
- case/Profile/Evidence/policy/context drift;
- revision changes that occur during or after independent verifier runtime;
- G.2/G.3 pre-commit revision races;
- database transaction rollback;
- generic request/schema errors.

Those are different failure models and must not be collapsed into one incident class.

## 4. Canonical signal boundary

The low-level G.5 revalidation helper exposes `EligibilityRevisionPostResolutionAdvance` only when a previously accepted reassessment precondition is later observed to have advanced to a newer single ACTIVE canonical revision.

The low-level subtype describes canonical state only. It does not itself claim provider egress.

H.2.4 attribution is applied only by the E.2/G.4 orchestration path that knows the subtype was raised at the immediate revalidation boundary after a successful producer response.

This preserves H.2.3 semantics:

```text
EligibilityRevisionPreconditionConflict
    = stale conflict already known before provider egress

EligibilityRevisionPostResolutionAdvance
    = previously valid reassessment became stale later
```

## 5. Durable attribution pair

For one accepted H.2.4 race, AIOS persists one atomic pair in the existing aggregate immune stream:

```text
organization.immune.eligibility_revision_runtime_race_attributed.v1
+
organization.immune.eligibility_incident.v1
  kind = revision_conflict
  severity = warning
```

The attribution records at minimum:

```text
failure_stage = e2_revision_precondition_post_producer_egress
conflict_basis = canonical_revision_advanced_during_producer_runtime
expected_revision_version
resolved_revision_id
resolved_revision_version
observed_current_revision_id
observed_current_revision_version
observed_current_lifecycle_status = active
producer_egress_occurred = true
verifier_egress_occurred = false
canonical_effect_committed = false
execution_role = producer
position_key
runtime_profile_key
runtime_profile_version
runtime_profile_fingerprint
runtime_class
adapter_key
provider_key
model_key
independence_group
control_effect = observation_only
authority_effect = none
recurrence_policy_applied = false
automatic_retry_applied = false
```

Runtime identity comes only from the trusted server-side execution plan and reuses the accepted runtime-profile fingerprint contract.

## 6. Replay and atomicity

H.2.4 follows the already-accepted H.2.2/H.2.3 pairing discipline without introducing a generic incident framework:

- attribution and warning are committed as one transactional pair;
- an injected failure after attribution staging rolls back the pair;
- exact replay of the same attribution snapshot reuses the same pair;
- historical replay remains valid after a later canonical revision supersedes the revision that was ACTIVE when the incident was first recorded;
- replay validates the immutable persisted attribution before requiring any current-lifecycle condition;
- a torn pair fails closed;
- the same incident key cannot be replayed with changed revision snapshots;
- the same incident key cannot be replayed with changed trusted producer runtime identity;
- no timestamp-only duplicate attribution is created.

The `observed_current_lifecycle_status = active` field is an event-time fact. It does not require that historical revision to remain ACTIVE forever.

## 7. Circuit and recurrence semantics

The paired incident remains the existing H.1 `revision_conflict` WARNING.

H.2.4 adds no recurrence threshold and no automatic circuit action:

```text
severity                  = warning
automatic circuit action  = none
recurrence threshold      = none
blast radius              = none
circuit effect            = CLOSED remains CLOSED
authority effect          = none
autonomy effect           = none
```

Repeated H.2.4 observations therefore remain observation-only in this increment.

A future restrictive policy would require its own accepted measurement window, threshold, contention semantics, false-positive controls, blast radius and recovery contract.

## 8. Recovery semantics

H.2.4 does not automatically retry or rebase the stale reassessment.

The safe operational recovery remains:

```text
reread the current canonical eligibility revision
rebuild the reassessment against that exact revision
rerun governed reasoning/verification as required
submit with a fresh idempotency key
```

Automatically recycling the producer output would be unsafe because the output was generated against a superseded canonical state.

## 9. Why this is not REASSESSMENT_ROLLBACK

G.5 supersession is committed transactionally: governance Activity, assessment, predecessor lifecycle transition, new revision and semantic Activity succeed together or the database transaction rolls back.

A failed transaction therefore leaves no committed canonical effect that requires an Immune System rollback incident.

The V1.3 consequence model also states that recovery semantics belong to consequential business actions rather than blanket database rollback. Canonical eligibility history is append-only/superseding truth.

H.2.4 therefore attributes stale provider work; it does not manufacture rollback semantics around an already-atomic database transaction.

## 10. Implementation surface

The current candidate is intentionally bounded to:

```text
organization_eligibility_revision_precondition.py
  typed post-resolution advance signal

organization_eligibility_revision_runtime_race.py
  trusted atomic attribution + existing H.1 warning pair
  historical replay independent of later lifecycle advancement

organization_eligibility_orchestration.py
  only the post-producer exception boundary may assert provider egress

test_organization_eligibility_revision_runtime_race.py
  normal, adversarial and PostgreSQL cross-session proof

test_organization_eligibility_revision_runtime_race_adversarial.py
  historical attribution replay after a later canonical supersession

v12-production-proof.yml
  both H.2.4 test files included in the real PostgreSQL lane
```

No migration, new authority surface, generic anomaly framework or provider-health policy is introduced.

## 11. Proof obligations

The H.2.4 implementation candidate must prove at minimum:

1. a real accepted `v1` reassessment precondition can become `v2` during producer runtime;
2. the stale attempt calls the producer exactly once;
3. the stale attempt calls the verifier zero times;
4. the stale attempt commits no new canonical revision/effect;
5. the attribution records original `v1` and observed current `v2` identity;
6. trusted producer position/runtime/provider/model identity is durably fingerprinted;
7. the paired incident is `revision_conflict / warning` with no automatic circuit action;
8. concurrent first-time canonical creation does not create an H.2.4 attribution;
9. H.2.3 pre-egress conflicts remain H.2.3 and do not become H.2.4;
10. exact attribution replay does not duplicate the pair;
11. historical replay of a `v1 -> v2` incident still succeeds after a legitimate `v3` supersedes `v2`;
12. repeated H.2.4 races do not open the aggregate circuit;
13. failure between attribution staging and incident persistence rolls back atomically;
14. a torn pair fails closed;
15. replay with changed revision snapshot fails closed;
16. replay with changed trusted producer runtime identity fails closed;
17. a real PostgreSQL cross-session winner can advance the revision during producer runtime and produce the same bounded attribution;
18. broad SQLite backend, frontend, migration/schema and repository-policy lanes remain green.

## 12. Explicit non-claims

H.2.4 does not claim or authorize:

- revision-conflict recurrence thresholds;
- automatic circuit opening from H.2.4 races;
- cross-aggregate contention aggregation;
- provider/runtime health scoring;
- provider-, agent-, user- or tenant-wide quarantine;
- automatic retry;
- automatic reassessment rebasing;
- reuse of stale producer output;
- verifier-stage revision-race attribution;
- G.2/G.3 race attribution;
- reassessment rollback policy;
- H.2 completion;
- Earned Autonomy.

## 13. Current state

```text
H.1      COMPLETE / PASS / SEALED
H.2.1    COMPLETE / PASS / SEALED
H.2.2    COMPLETE / PASS / SEALED
H.2.3    COMPLETE / PASS / SEALED
H.2.4    IMPLEMENTATION CANDIDATE / PRODUCTION PROOF PENDING
H.2      IN PROGRESS
I        NOT STARTED
```

H.2.4 must not be marked accepted or sealed until its exact implementation candidate passes the full GitHub-hosted V12 Production Proof including the fresh PostgreSQL governed eligibility lane.

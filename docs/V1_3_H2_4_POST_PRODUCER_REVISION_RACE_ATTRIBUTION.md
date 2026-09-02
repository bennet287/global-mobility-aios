# Global Mobility AIOS — V1.3 H.2.4 Post-Producer Revision-Race Attribution

**Stage:** V1.3-H.2.4
**Status:** ACCEPTED / COMPLETE / PASS / SEALED
**Accepted technical candidate:** `e7584b90fc967e828960ae0730a35d8646fba74f`
**Accepted Production Proof:** GitHub Actions run `32500438187`
**Acceptance record:** `docs/V1_3_H2_4_ACCEPTANCE_2026-08-21.md`
**Superseded prior candidate:** `393629a4608d7fbba1fcc314dbadeb9426c767cc`
**Parent accepted checkpoint:** V1.3-H.2.3 — `17edeca46af2b9cc7e0a6111ec2b3270f4bb1283`
**Parent Production Proof:** run `32480405051`

## 1. Purpose

H.2.4 covers one concrete optimistic-concurrency race that H.2.3 deliberately excludes.

A governed reassessment begins against the exact current canonical eligibility revision. The producer runtime is then called. While that producer call is in flight, another governed reassessment advances the same canonical aggregate. Immediate post-producer revalidation detects that the originally accepted revision is no longer current before verifier egress or canonical effect.

The result is safe but operationally meaningful:

```text
producer provider egress occurred
verifier provider egress did not occur
canonical eligibility effect did not occur
stale producer work must not silently proceed
the detected race must remain durably explainable
```

H.2.4 makes that bounded failure explainable and durable. It does not turn optimistic-concurrency contention into an automatic safety fault.

Permanent boundaries:

> The Immune System may restrict or stop execution. It never grants authority, autonomy or permission.

> Optimistic-concurrency contention is not automatically a safety fault.

## 2. Exact failure model

H.2.4 attribution is valid only when all of the following are true:

```text
canonical eligibility aggregate exists
caller explicitly expects the exact current reassessment revision
E.2 accepts that exact precondition before producer egress
producer provider returns successfully
another governed operation advances the same aggregate during producer latency
E.2 detects that advancement at immediate post-producer revalidation
verifier provider has not been called
no canonical effect from the stale attempt has been committed
```

The accepted precondition is a real reassessment precondition:

```text
expected_revision_version == resolved_current_revision_version >= 1
resolved_current_revision_id is not null
```

The event-time observed revision is later than the resolved revision:

```text
observed_current_revision_version > resolved_current_revision_version
observed_current_revision_id != resolved_current_revision_id
```

`observed_current_lifecycle_status = active` is an **event-time statement**. It records that the observed revision was ACTIVE when the post-producer check detected the race. It is not a requirement that the same revision remain ACTIVE until the attribution write occurs.

## 3. Explicit exclusions

H.2.4 does not classify:

- H.2.3 pre-egress stale reassessment conflicts;
- missing revision expectations;
- future revision expectations;
- concurrent first-time canonical creation;
- multiple-ACTIVE-revision corruption;
- missing or corrupt canonical lineage;
- producer runtime/provider failure;
- malformed producer output;
- case/Profile/Evidence/policy/context drift;
- verifier-stage revision races;
- G.2/G.3 pre-commit revision races;
- database transaction rollback;
- generic request/schema errors.

Those are different failure models and must not be collapsed into one incident class.

## 4. Canonical signal boundary

The low-level G.5 revalidation helper exposes `EligibilityRevisionPostResolutionAdvance` only when a previously accepted reassessment precondition is later observed to have advanced.

That subtype describes canonical state only. It does not itself claim provider egress.

H.2.4 attribution is applied only at the E.2/G.4 orchestration boundary that knows the subtype was raised immediately after a successful producer response.

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

The attribution records:

```text
failure_stage = e2_revision_precondition_post_producer_egress
conflict_basis = canonical_revision_advanced_during_producer_runtime
expected_revision_version
resolved_revision_id
resolved_revision_version
observed_current_revision_id
observed_current_revision_version
observed_current_lifecycle_status = active  # event-time fact
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

Runtime identity comes only from the trusted server-side execution plan.

## 6. Event-time first-persistence reconciliation

The earlier H.2.4 candidate correctly allowed historical replay after later supersession, but first persistence still required the observed event-time revision to remain ACTIVE.

That left a real concurrency gap:

```text
v1 accepted
producer executes
v2 commits
post-producer check captures v1 -> v2 while v2 is ACTIVE
v3 commits before the FIRST attribution write
v2 becomes SUPERSEDED
prior first-write validation rejects v2
```

The stale execution remained fail-closed, but the durable explanation could be lost.

The accepted repair closes that gap.

Before first persistence, H.2.4 refreshes durable revision rows from the database and delegates complete aggregate-chain proof to:

```text
apps/api/app/services/organization_eligibility_lineage.py
validate_canonical_eligibility_aggregate_lineage(...)
```

That shared validator proves the complete current canonical aggregate:

```text
versions are contiguous from 1
exactly one latest revision is ACTIVE
all earlier revisions are SUPERSEDED
supersedes_revision_id forms the exact predecessor chain
every revision passes canonical G.1/G.2/G.3/semantic lineage validation
```

H.2.4 then requires:

```text
resolved revision ID exists in the validated aggregate
resolved version equals the captured resolved version
observed revision ID exists in the validated aggregate
observed version equals the captured event-time version
observed index is strictly after resolved index
```

Therefore a now-SUPERSEDED observed revision may still be persisted as the event-time observation when the current validated aggregate proves it remains legitimate canonical history.

No parallel H.2.4 canonical-lineage validator exists.

## 7. Replay and atomicity

Accepted H.2.4 follows the H.2.2/H.2.3 pairing discipline:

- attribution and warning commit as one transactional pair;
- an injected failure after attribution staging rolls the pair back;
- exact replay reuses the existing pair;
- a torn pair fails closed;
- changed revision snapshots under the same incident key fail closed;
- changed trusted producer runtime identity fails closed;
- historical replay remains valid after later legitimate supersession;
- first persistence also survives later legitimate supersession that happened before the write;
- no timestamp-only duplicate attribution is created.

## 8. Accepted race proof

The accepted proof covers both event-time supersession orderings:

```text
A. persist v1 -> v2 attribution, then v3 supersedes v2
B. detect v1 -> v2, then v3 supersedes v2, then perform FIRST attribution write
```

Ordering B is proven twice:

1. SQLite adversarial regression;
2. real PostgreSQL cross-session regression where the original Session deliberately still carries cached `v2 = ACTIVE` while a second Session commits `v3`.

The PostgreSQL proof demonstrates that H.2.4 refreshes database truth before reconciliation, persists the original event-time `v2 = ACTIVE` observation, and leaves durable canonical state as `v2 = SUPERSEDED`, `v3 = ACTIVE`.

## 9. Circuit and recurrence semantics

The paired incident remains the existing H.1 `revision_conflict` WARNING.

H.2.4 adds no recurrence threshold and no automatic circuit action:

```text
severity                  warning
automatic circuit action  none
recurrence threshold      none
blast radius               none
circuit effect             CLOSED remains CLOSED
authority effect           none
autonomy effect            none
```

Repeated H.2.4 observations remain observation-only.

## 10. Recovery semantics

H.2.4 does not automatically retry or rebase a stale reassessment.

Safe operational recovery remains:

```text
reread current canonical eligibility revision
rebuild reassessment against that exact revision
rerun governed reasoning/verification as required
submit with a fresh idempotency key
```

Automatically recycling producer output would be unsafe because it was generated against superseded canonical state.

## 11. Why this is not REASSESSMENT_ROLLBACK

G.5 supersession is transactional. Governance Activity, assessment, predecessor lifecycle transition, new revision and semantic Activity succeed together or the database transaction rolls back.

A failed transaction therefore leaves no committed canonical effect requiring an Immune System rollback incident.

H.2.4 attributes stale provider work; it does not manufacture rollback semantics around an already-atomic database transaction.

## 12. Accepted implementation surface

```text
organization_eligibility_revision_precondition.py
  typed post-resolution advance signal

organization_eligibility_revision_runtime_race.py
  trusted atomic attribution + existing H.1 warning pair
  fresh database-state reconciliation
  shared aggregate-lineage validation
  historical replay independent of later lifecycle advancement

organization_eligibility_orchestration.py
  only trusted post-producer boundary may assert provider egress

test_organization_eligibility_revision_runtime_race.py
  normal, exclusion and original PostgreSQL cross-session proof

test_organization_eligibility_revision_runtime_race_adversarial.py
  atomicity, torn-pair, identity/snapshot drift, historical replay,
  pre-persistence supersession, and PostgreSQL stale-session refresh proof

v12-production-proof.yml
  both H.2.4 test files included in the real PostgreSQL lane
```

Repair/hardening commits include:

```text
3c69772b37e1389075a5c2da4a02bc8f54796672
  fix: preserve H.2.4 event-time revision race attribution

405b9261d35fe9ada0e831953f9593f13096df82
  test: cover H.2.4 pre-persistence supersession race

c8d52e27c7cf2761d59a92691bf637624a88ecd5
  test: prove H.2.4 cross-session pre-persistence race

e7584b90fc967e828960ae0730a35d8646fba74f
  refactor: reuse canonical aggregate lineage for H.2.4
```

No migration, new authority surface, generic anomaly framework or provider-health policy is introduced.

## 13. Accepted Production Proof

```text
technical candidate                        e7584b90fc967e828960ae0730a35d8646fba74f
GitHub Actions run                         32500438187
workflow conclusion                        completed / success
Repository policy and constraints          PASS
Backend regression (SQLite)                PASS — 1135 passed / 10 skipped / 1 warning / 0 failed
Frontend tests, types and build            PASS
PostgreSQL governance contracts            PASS — 90 passed / 1 warning / 0 failed
Alembic                                    PASS — 0001 -> 0077
registered SQLModel tables                 119
physical schema                            PASS
Python dependency constraints              PASS — 25 direct dependencies
diff hygiene                               PASS — git diff --check HEAD^
```

Frontend proof includes Node 24, `npm ci`, zero vulnerabilities, 28/28 design-foundation tests, 4/4 request/auth tests, TypeScript, Next.js 16.3.1 production build and compiled-auth verification.

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

The prior run `32484882964` remains historical regression evidence but is superseded as acceptance evidence because it did not include the pre-persistence `v3` interleaving.

## 14. Separate H.2.2 classification follow-up

A separate verified finding remains for H.2.2: runtime-health attribution currently does not durably separate configuration/binding failures from provider transport/response failures with provider-egress provenance suitable for future provider-health scoring.

That issue is not part of H.2.4 and was deliberately not mixed into this repair. H.2.2 remains observation-only today.

## 15. Explicit non-claims

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

## 16. Current state

```text
H.1      COMPLETE / PASS / SEALED
H.2.1    COMPLETE / PASS / SEALED
H.2.2    COMPLETE / PASS / SEALED — classification refinement identified
H.2.3    COMPLETE / PASS / SEALED
H.2.4    COMPLETE / PASS / SEALED
H.2      IN PROGRESS
later H.2 increment  NOT STARTED / NOT PRE-AUTHORIZED
I        NOT STARTED
```

H.2.4 is sealed by the repaired event-time persistence proof on `e7584b9...` / run `32500438187`.

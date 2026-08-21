# Global Mobility AIOS — V1.3 H.2.1 Eligibility Warning Recurrence Guard

**Stage:** V1.3-H.2.1  
**Status:** COMPLETE / PASS / SEALED  
**Accepted candidate:** `9e63c358b9692529278595201250c4dc8bb1ff47`  
**Accepted Production Proof:** GitHub Actions run `32469756908`  
**Parent accepted baseline:** V1.3-H.1 — COMPLETE / PASS / SEALED  
**Scope:** `mobility.eligibility` canonical aggregate only

## 1. Purpose

H.2.1 is the first bounded production-transition guardrail after the accepted H.1 Eligibility Immune Circuit Foundation.

It does **not** introduce a generic anomaly platform, provider health scorer, cross-capability quarantine system, autonomy engine, or new authority model. It adds one deterministic recurrence rule to an already-governed R3 eligibility signal:

> Repeated independent-verifier disagreement on the same canonical eligibility aggregate may restrict future execution even though each individual disagreement remains a warning.

The constitutional boundary remains unchanged:

> The Immune System may restrict or stop execution. It does not grant authority, autonomy or permission.

## 2. Canonical scope

The guard is scoped to the existing canonical aggregate:

```text
eligibility:<tenant_key>:<lead_id>:<pathway_id>
```

It reuses the H.1 durable `OrganizationActivity` control stream. No new incident table, migration head, capability authority, request field or provider-controlled state is introduced.

## 3. Deterministic recurrence policy

Policy version:

```text
eligibility-immune-recurrence.v1
```

Accepted first policy:

```text
incident kind     = verifier_disagreement
threshold         = 3
scope             = exact tenant + canonical eligibility aggregate
recovery epoch    = stream start or most recent authorized circuit close
```

Behavior:

```text
1st verifier disagreement  -> WARNING / observable / circuit remains CLOSED
2nd verifier disagreement  -> WARNING / observable / circuit remains CLOSED
3rd verifier disagreement  -> WARNING + recurrence threshold reached
                            -> circuit OPEN in the same transaction
next fresh execution       -> blocked before producer/verifier provider egress
```

The threshold does not reclassify the third incident as CRITICAL. The individual signal remains a warning; the **pattern** causes the restrictive circuit transition.

## 4. Recovery epoch

The recurrence counter includes only matching warning incidents after the latest authorized `organization.immune.eligibility_circuit_closed.v1` Activity for the aggregate.

Therefore an authenticated human-admin recovery creates a new recurrence epoch for future work. Older warning history remains durable and Board-inspectable but does not permanently poison the aggregate.

Recovery continues to mean only:

```text
restores_execution_attempts_only = true
grants_authority                 = false
```

## 5. Signals intentionally excluded from H.2.1

H.2.1 does **not** apply the threshold to:

- `runtime_health_failure`;
- `revision_conflict`;
- `reassessment_rollback`;
- `insufficient_basis` (which is not currently an immune incident);
- structural integrity incidents, which already open immediately under H.1.

Those signals have materially different causes. Treating all warnings as one recurrence class would create false coupling between concurrency, provider/runtime availability and decision-quality disagreement.

## 6. Atomicity, serialization and idempotency

The existing aggregate Activity stream is the serialization boundary. On PostgreSQL, `stage_activity` locks the stream row while allocating the next sequence. The current circuit state and recurrence count are evaluated only after the threshold-crossing incident has been staged/flushed inside that serialization boundary.

That ordering matters: two concurrent threshold-crossing warnings cannot both act on a stale CLOSED circuit snapshot. The accepted PostgreSQL contract proves that concurrent writers serialize and produce exactly one restrictive OPEN transition.

When the threshold is reached, the warning incident and circuit-open Activity are committed as one transaction. Failure to stage the required open rolls back the incident too.

Incident idempotency remains keyed by the existing deterministic incident activity key. Replaying the threshold-crossing incident returns the durable incident/current circuit state and cannot append another open transition.

## 7. Accepted proof

H.2.1 was accepted only after the exact implementation candidate passed both focused local proof and the full V12 Production Proof workflow.

### 7.1 Focused local SQLite proof

Exact candidate:

```text
9e63c358b9692529278595201250c4dc8bb1ff47
```

Result:

```text
33 passed / 1 PostgreSQL-only skipped / 1 warning / 0 failed
```

Additional local checks:

```text
Python 3.13.12 constrained environment   PASS
pip check                                PASS
compileall                               PASS
repository policy                        PASS
release consistency                      PASS — Alembic 0077
Python dependency constraints            PASS — 25 direct dependencies
git diff --check                         PASS
working tree / origin                    clean and synchronized
```

### 7.2 Fresh local PostgreSQL 16 proof

Fresh Docker PostgreSQL 16 was created for the candidate and migrated from `0001_mvp1_baseline` through `0077_canonical_eligibility_assessment_revision`.

Result:

```text
Database migration check                 PASS
registered_tables                        119
physical_schema                          ok
database_revision                        0077_canonical_eligibility_assessment_revision
H.2.1 recurrence suite                   7 passed / 1 warning / 0 failed
```

The PostgreSQL-only simultaneous threshold-crossing contract executed and passed rather than skipping.

### 7.3 GitHub-hosted V12 Production Proof

Run:

```text
32469756908
```

Exact checkout:

```text
9e63c358b9692529278595201250c4dc8bb1ff47
```

All four jobs completed successfully:

```text
Repository policy and constraints   PASS
Backend regression (SQLite)         PASS
Frontend tests, types and build     PASS
PostgreSQL governance contracts     PASS
```

Backend CI result:

```text
1111 passed / 8 skipped / 1 warning / 0 failed
migration_heads = 0077_canonical_eligibility_assessment_revision
registered_tables = 119
physical_schema = ok
```

PostgreSQL CI result:

```text
64 passed / 1 warning / 0 failed
migration_heads = 0077_canonical_eligibility_assessment_revision
registered_tables = 119
physical_schema = ok
```

Frontend CI result:

```text
Node 24
npm ci                              PASS
npm audit --audit-level=high        PASS — 0 vulnerabilities
design foundation                   28/28 PASS
request/auth                        4/4 PASS
TypeScript                          PASS
Next.js 16.3.1 production build     PASS
compiled auth                       PASS
```

Repository-policy CI result:

```text
repository policy                   PASS
release consistency                 PASS
Python dependency constraints       PASS — 25 direct dependencies
diff hygiene                        PASS
```

The known Pydantic `model_metadata_json` protected-namespace warning remains visible and non-blocking. GitHub Actions also emits deprecation warnings for action runtimes that target Node 20 while the hosted runner forces Node 24; these warnings did not affect the application proof and are not H.2.1 defects.

## 8. Acceptance decision

All required H.2.1 invariants are proven:

1. one and two verifier disagreements remain warning-only;
2. the third disagreement opens only the exact aggregate circuit;
3. the open is restrictive-only and causally linked to the threshold-crossing incident;
4. unrelated warning kinds do not advance the threshold;
5. recurrence is aggregate-scoped;
6. replay cannot duplicate the open;
7. human-admin recovery creates a fresh recurrence epoch;
8. recurrence-open blocks fresh G.4 execution before provider egress;
9. PostgreSQL serialization prevents duplicate OPEN transitions under concurrent threshold crossing;
10. broad backend, PostgreSQL, frontend, repository-policy, dependency and migration proof remained green.

Therefore:

```text
V1.3-H.2.1 = COMPLETE / PASS / SEALED
```

## 9. Explicit non-claims

H.2.1 does not claim:

- rolling-time-window anomaly detection;
- provider/runtime health scoring;
- incident aggregation across capabilities;
- root-cause classification;
- automatic recovery;
- automatic authority or autonomy changes;
- organization-wide quarantine;
- completion of all H.2 work.

Those remain later evidence-driven increments, if justified.

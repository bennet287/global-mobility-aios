# Global Mobility AIOS — V1.3 H.2.1 Eligibility Warning Recurrence Guard

**Stage:** V1.3-H.2.1  
**Status:** IMPLEMENTATION CANDIDATE / ACCEPTANCE PENDING  
**Parent accepted baseline:** V1.3-H.1 — COMPLETE / PASS / SEALED  
**Parent Production Proof:** GitHub Actions run `32463849415`  
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

First policy:

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

The threshold does not reclassify the third incident as CRITICAL. The individual signal remains a warning; the **pattern** is what causes the restrictive circuit transition.

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

## 6. Atomicity and idempotency

The existing aggregate Activity stream is the serialization boundary. On PostgreSQL, `stage_activity` locks the stream row while allocating the next sequence. The recurrence count is evaluated after the new incident is staged/flushed and before commit.

When the threshold is reached, the warning incident and circuit-open Activity are committed as one transaction. Failure to stage the required open rolls back the incident too.

Incident idempotency remains keyed by the existing deterministic incident activity key. Replaying the threshold-crossing incident returns the durable incident/current circuit state and cannot append another open transition.

## 7. Required proof

H.2.1 is not accepted merely because code exists. The candidate must prove at least:

1. one and two verifier disagreements remain warning-only;
2. the third disagreement opens the exact aggregate circuit;
3. the open is restrictive only and causally linked to the threshold-crossing incident;
4. unrelated warning kinds do not contribute to the verifier-disagreement threshold;
5. recurrence is isolated by aggregate;
6. incident replay does not duplicate the open;
7. authorized human recovery starts a fresh recurrence epoch;
8. a recurrence-open circuit blocks fresh G.4 execution before provider egress;
9. the contracts pass both broad SQLite regression and the PostgreSQL governance lane;
10. repository policy, dependency constraints, migration/schema proof and frontend proof remain green through the V12 Production Proof workflow.

## 8. Explicit non-claims

This candidate does not claim:

- rolling-time-window anomaly detection;
- provider/runtime health scoring;
- incident aggregation across capabilities;
- root-cause classification;
- automatic recovery;
- automatic authority or autonomy changes;
- organization-wide quarantine;
- H.2 completion or acceptance.

Those remain later evidence-driven increments, if justified.

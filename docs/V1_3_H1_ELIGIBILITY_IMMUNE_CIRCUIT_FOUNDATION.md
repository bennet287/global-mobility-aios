# Global Mobility AIOS — V1.3-H.1 Eligibility Immune Circuit Foundation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTED / ACCEPTANCE PENDING

## Purpose

H.1 begins the Organizational Immune System from a real governed vertical rather than from a generic monitoring framework.

The first bounded target is the canonical eligibility aggregate introduced by G.3/G.5:

```text
eligibility:<tenant_key>:<lead_id>:<pathway_id>
```

H.1 adds durable incident signals and a restrictive circuit state for that aggregate using the already-canonical `OrganizationActivity` stream model.

Permanent rule:

> **The Immune System may reduce or stop execution, but it may never create authority, autonomy or permission that the normal governance path did not already grant.**

## Why H.1 is aggregate-scoped

A tenant-wide kill switch would have unnecessarily large blast radius.

A WorkItem-scoped breaker could be bypassed by creating a different WorkItem for the same canonical eligibility truth.

Therefore the first breaker is scoped to the stable canonical eligibility aggregate:

```text
tenant + Lead + stable pathway
```

This matches the G.3/G.5 truth boundary and keeps unrelated cases/pathways operational.

## Durable representation

H.1 introduces no new table or migration.

It uses append-only `OrganizationActivity` records on:

```text
stream_key = immune:eligibility:<aggregate_key>
source_object_type = eligibility_aggregate
source_object_id = <aggregate_key>
```

Activity types:

```text
organization.immune.eligibility_incident.v1
organization.immune.eligibility_circuit_opened.v1
organization.immune.eligibility_circuit_closed.v1
```

The latest circuit-control Activity determines current state.

No Activity history is rewritten in place.

## Incident classes

First-slice typed signals:

```text
CANONICAL_AGGREGATE_INTEGRITY
DURABLE_LINEAGE_INTEGRITY
RUNTIME_HEALTH_FAILURE
REVISION_CONFLICT
VERIFIER_DISAGREEMENT
REASSESSMENT_ROLLBACK
```

H.1 intentionally distinguishes structural integrity failure from normal governed disagreement/conflict.

### Critical / automatic circuit-open

```text
CANONICAL_AGGREGATE_INTEGRITY
DURABLE_LINEAGE_INTEGRITY
```

These mean AIOS can no longer safely identify one coherent canonical eligibility truth/lineage. Continuing material execution would risk silent corruption, so the circuit opens immediately.

### Warning / observable but non-opening

```text
RUNTIME_HEALTH_FAILURE
REVISION_CONFLICT
VERIFIER_DISAGREEMENT
REASSESSMENT_ROLLBACK
```

These are not automatically treated as organizational corruption:

- an optimistic revision conflict can be normal concurrency;
- verifier disagreement is a legitimate epistemic outcome;
- a transaction rollback may prove the safety boundary worked correctly;
- one runtime-health failure does not yet prove systemic failure.

Later H slices may add rate/recurrence policy after real operational evidence exists.

## Atomic critical transition

For a new critical incident:

```text
incident Activity
+ circuit-open Activity
→ one transaction
```

A critical incident must never become durable while its required restrictive circuit action is lost.

Synthetic failure of the second staged Activity must roll the whole unit back.

## Circuit guard

Public guard:

```text
require_eligibility_circuit_closed(...)
```

Current first-slice semantics:

```text
CLOSED → execution may continue to normal governance
OPEN   → raise EligibilityCircuitOpen
```

The guard itself does not authorize any action when CLOSED. It merely says the Immune System is not currently applying an additional restriction.

Normal E.2/F.1/G.1/G.2/G.3/G.4/G.5 authority, risk, verification, revision and Gateway checks remain mandatory.

## Opening authority

Automatic opening uses the infrastructure actor:

```text
actor_type = system
actor_id   = organization-immune-system
role       = operator
```

This actor is allowed only to append observable incident state and restrict execution.

It does not own `CapabilityAuthority` and does not become an `OrganizationPosition` employee identity.

## Recovery authority

H.1 deliberately has no automatic circuit recovery.

Closing a circuit restores the ability to *attempt* governed execution, so the first slice requires:

```text
authenticated human
+ admin role
```

Recovery appends a `circuit_closed` Activity that supersedes the current open control Activity.

Recovery payload explicitly records:

```text
restores_execution_attempts_only = true
grants_authority = false
```

Closing the breaker therefore does not grant autonomy or material-action authority.

## Historical replay semantics

Incident keys and recovery keys are idempotent.

A replay of an old recovery after a later critical incident must not close the newer circuit.

Example:

```text
incident A → OPEN
recovery A → CLOSED
incident B → OPEN
replay recovery A
→ remains OPEN
```

Historical idempotency may recover old records; it may not override newer control state.

## Isolation

Circuit state is tenant- and aggregate-scoped.

An open circuit for:

```text
tenant-a / aggregate-A
```

must not block:

```text
tenant-a / aggregate-B
tenant-b / aggregate-A-like identifier
```

## Deliberate non-claims

H.1 does not yet claim:

- automatic wiring from every E.2–G.5 exception into incident creation;
- G.4 orchestration preflight enforcement;
- tenant-wide or capability-wide circuit breaking;
- automatic recovery;
- recurrence thresholds or rolling-window anomaly policy;
- provider-wide/runtime-wide health scoring;
- earned-autonomy changes;
- generic incident-management infrastructure;
- Munder circuit-breaker adoption;
- new database schema.

Those follow only after this aggregate-scoped contract is locally accepted.

## Acceptance-pending focused gate

Run:

```text
apps/api/tests/test_organization_eligibility_immune_system.py
```

The focused tests must prove:

1. absent control state is CLOSED;
2. verifier disagreement is visible but does not open the circuit;
3. structural integrity failure opens and blocks the exact aggregate;
4. critical incident + open transition are atomic under rollback;
5. incident replay is idempotent and conflicting reuse fails closed;
6. recovery requires authenticated human admin;
7. recovery restores attempts only and grants no authority;
8. replay of an old recovery cannot close a newer open circuit;
9. tenant/aggregate isolation is preserved.

ROADMAP and CHANGELOG remain at accepted V12.17 until this foundation is verified through local evidence and the next wiring boundary is proven.

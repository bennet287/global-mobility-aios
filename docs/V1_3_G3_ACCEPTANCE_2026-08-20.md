# Global Mobility AIOS — V1.3-G.3 Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted implementation head:** `2df0069af54945b4f32a24192447198b6e1cee28`  
**Status:** COMPLETE / PASS / SEALED

## Scope accepted

V1.3-G.3 establishes the first canonical governed eligibility effect after the accepted E.2 → F.1 → G.1 → G.2 chain.

Accepted implementation:

```text
E.2 governed eligibility proposal
→ F.1 deterministic Decision Readiness
→ G.1 blind independent AGREES verification
→ G.2 verification-floor integration
→ fresh final Command Gateway authorization
→ canonical governance authorization Activity
→ EligibilityAssessment
→ EligibilityAssessmentRevision v1
→ semantic MATERIAL eligibility Activity
→ one atomic G.3 transaction
```

G.3 remains eligibility-specific. It does not establish a generic canonical-effect framework.

## Canonical model / migration

Accepted migration:

```text
0077_canonical_eligibility_assessment_revision
```

Accepted companion canonical model:

```text
EligibilityAssessmentRevision
```

The companion record makes an `EligibilityAssessment` part of the governed V1.3 canonical eligibility aggregate. Legacy `EligibilityAssessment` rows without a companion revision remain legacy/non-canonical for V1.3 purposes.

Accepted first aggregate identity:

```text
eligibility:<tenant_key>:<lead_id>:<pathway_id>
```

Accepted first-slice version semantics:

```text
version = 1
lifecycle_status = active
supersedes_revision_id = null
```

A second active canonical revision is intentionally refused until reassessment/supersession carries an explicit canonical revision precondition.

## Authorization / mutation contract

G.3 consumes only an accepted G.2 result and revalidates the accepted E.2/F.1/G.1/G.2 lineage.

Before a first effect it reconstructs the exact E.2 `MaterialAction`, preserves the original E.2 action fingerprint and idempotency key, revalidates the verification floor, and performs a fresh call to the unchanged Command Gateway.

Only:

```text
GatewayOutcome.AUTO_EXECUTE
```

may enter the canonical effect transaction.

Accepted autonomy behavior remains:

```text
A0      → no canonical effect
A1/A2   → no canonical effect
A3      → canonical effect allowed only after Gateway AUTO_EXECUTE,
          with post_review_required=true
A4/A5   → canonical effect allowed subject to all other Gateway gates
```

Authority, scope, risk, version, policy and Board-reserved checks remain Gateway-owned.

## Atomicity

A fresh authorized G.3 transaction stages:

```text
governance:<original E.2 idempotency key>
+ EligibilityAssessment
+ EligibilityAssessmentRevision
+ organization.eligibility.assessment_committed.v1
```

and commits once.

Accepted causal lineage:

```text
E.2 governance attempt
    ↓
G.1 independent verification
    ↓
G.2 verification-floor re-evaluation
    ↓
G.3 canonical governance authorization
    ↓
G.3 semantic EligibilityAssessment effect
```

The semantic effect is physical Activity class `decision` with constitutional class `MATERIAL`.

Synthetic mid-transaction failure is covered by the focused suite and must roll the G.3 governance/effect unit back instead of leaving partial canonical truth.

## Canonical idempotency / replay

G.3 is the first eligibility slice that consumes:

```text
governance:<original E.2 idempotency key>
```

Exact retry resolves the durable canonical result as `IDEMPOTENT_REPLAY` without duplicate assessment, revision or semantic Activity.

Replay validation is not based on the governance key alone. It verifies the persisted assessment/revision/semantic effect and the E.2 action, E.2 intent, F.1 readiness, G.1 verification, G.2 floor and G.3 effect fingerprints.

A torn or inconsistent persisted canonical state fails closed.

## Canonical assessment semantics

Accepted first governed assessment writes:

```text
status = E.2 proposed_state
overall_score = 0.0
confidence = E.2 informational confidence
profile_id/profile_version = accepted E.2 profile binding
target_country/domain = governed pathway
```

`overall_score = 0.0` does **not** mean a zero eligibility score was calculated. No canonical numerical eligibility score exists in the accepted E.2/F.1/G.1/G.2/G.3 contract. It is only a compatibility value for the legacy `EligibilityAssessment` column; governed read/API surfaces must not present it as a computed eligibility score.

## Non-effects

G.3 does not automatically:

- change Lead lifecycle/status;
- mutate an Application;
- publish eligibility to a client;
- send consequential external communication;
- submit anything to government;
- authorize a different material action;
- create reassessment/version-2 semantics;
- expose a new HTTP/worker orchestration surface.

## Canonical acceptance evidence

The Human Owner ran the acceptance checks on exact V12 head:

```text
2df0069af54945b4f32a24192447198b6e1cee28
```

### Migration-boundary repairs

The introduction of migration 0077 initially exposed two stale test assertions that still hard-coded migration 0076 as the repository ceiling/head. Those tests were corrected without changing production code.

Post-fix focused result:

```text
2 passed / 1 warning / 0 failed
```

Covered:

- fresh database upgrades to current schema;
- organization/OpenAPI architecture migration boundary through 0077.

### G.3 focused

```text
15 passed / 1 warning / 0 failed
Duration: 9.50s
```

### Full API regression

```text
1040 passed / 5 skipped / 1 warning / 0 failed
Duration: 505.33s
```

Known warning:

```text
StarletteDeprecationWarning:
Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

This remains a known non-blocking warning. No dependency change is implied by this acceptance.

### Migration / schema

Alembic upgrade to head completed successfully.

```text
Database migration check      PASS
database_url                  sqlite:///./gmai.db
migration_heads               0077_canonical_eligibility_assessment_revision
registered_tables             119
physical_schema               ok
database_revision             0077_canonical_eligibility_assessment_revision
```

Local schema:

```text
Local DB schema check         PASS
registered_tables             119
actual_tables                 119
physical_tables               120
infrastructure_tables         ["alembic_version"]
```

### Repository integrity

```text
Repository policy             PASS
Protected v10.22 regression   1 passed / 1 warning / 0 failed
git diff --check              clean
V12 branch                    clean / synchronized
```

The protected roadmap regression preserves:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

## GitHub / CI truth

The accepted local checkout was synchronized with `origin/roadmap/global-mobility-aios-v12` at the accepted implementation head before the acceptance-seal documentation commits.

No GitHub status checks were attached to the implementation head when inspected. Therefore this record makes **no GitHub CI PASS claim**.

## Result

```text
V1.3-G.3 First Canonical Eligibility Effect
COMPLETE / PASS / SEALED
```

This is the first accepted V1.3 vertical proving:

```text
persistent employee
→ governed context / Evidence
→ model proposal
→ deterministic validation
→ Command Gateway review
→ deterministic Decision Readiness
→ blind independent verification
→ verification-floor integration
→ fresh final authorization
→ atomic canonical organizational truth
```

Permanent conclusion:

> **The model may propose. Independent AI may verify. Deterministic gates and the Command Gateway authorize. Only AIOS commits canonical organizational truth.**

## Next bounded programme

With the first canonical effect accepted, the next work should consolidate and operationalize the proven vertical before broad Organization Fabric work:

1. extract stable eligibility vertical helpers only where semantics are now proven identical;
2. add a trusted governed HTTP/worker orchestration surface for E.2 → F.1 → G.1 → G.2 → G.3 rather than routing through the legacy immediate-persistence eligibility endpoint;
3. then define reassessment/supersession with an explicit expected canonical eligibility revision version.

No Mission Room, generic Peer Review Network, Flight Recorder or broad Munder runtime expansion is implied by G.3 acceptance.

# Global Mobility AIOS — V1.3-G.3 First Canonical Eligibility Effect

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** COMPLETE / PASS / SEALED

## Purpose

G.3 is the first V1.3 slice that converts an accepted governed eligibility proposal into durable canonical eligibility state.

It consumes only the already-proven vertical:

```text
E.2 governed eligibility proposal
→ F.1 READY_FOR_INDEPENDENT_VERIFICATION
→ G.1 blind independent AGREES verification
→ G.2 verification floor satisfied
→ G.2 Command Gateway result eligible_for_effect_integration
→ G.3 final Gateway authorization + canonical effect transaction
```

Permanent rule:

> **Independent verification satisfies a verification requirement; the Command Gateway authorizes the effect; the canonical effect is committed only in the same transaction as its final durable governance authorization.**

G.3 does not expose a new HTTP surface and does not authorize any client-facing or external action.

## Why legacy EligibilityAssessment persistence is not reused

The pre-V1.3 eligibility path uses `persist_eligibility_assessment(...)`, which creates an `EligibilityAssessment` and immediately commits it.

That path does not provide the new vertical with:

- canonical tenant/aggregate identity;
- explicit aggregate version;
- supersession lineage;
- final governance Activity identity;
- G.1/G.2 verification lineage;
- one atomic governance + effect + semantic Activity transaction.

G.3 therefore leaves legacy rows untouched and introduces a companion canonical revision record.

A legacy `EligibilityAssessment` without a canonical revision record remains legacy/non-canonical for V1.3 purposes.

## Canonical companion model

New model:

```text
EligibilityAssessmentRevision
```

New table:

```text
eligibility_assessment_revisions
```

Migration:

```text
0077_canonical_eligibility_assessment_revision
```

The companion record owns governed identity and lineage while preserving compatibility with the existing `EligibilityAssessment` table.

Core fields include:

```text
assessment_id
tenant_key
aggregate_key
version
lifecycle_status
supersedes_revision_id
lead_id
profile_id
profile_version
pathway_version_id
governance_activity_id
verification_activity_id
verification_floor_activity_id
semantic_activity_id
original_action_fingerprint
intent_fingerprint
readiness_fingerprint
verification_fingerprint
verification_floor_fingerprint
effect_fingerprint
post_review_required
```

## Aggregate identity

The first canonical aggregate key is:

```text
eligibility:<tenant_key>:<lead_id>:<pathway_id>
```

It deliberately uses stable `MobilityPathway.id`, not `MobilityPathwayVersion.id`, so a future reassessment may span later governed pathway versions without changing aggregate identity.

## First-slice version rule

G.3 implements only:

```text
version = 1
lifecycle_status = active
supersedes_revision_id = null
```

If an active canonical revision already exists for the same aggregate, G.3 fails closed.

This is deliberate. E.2 currently binds `eligibility.transition` optimistic concurrency to the immutable `Profile.profile_version`; it does not yet carry an expected canonical eligibility-assessment revision.

Therefore G.3 does **not** invent version-2/supersession semantics prematurely.

Future reassessment must first extend the material action contract with an explicit canonical eligibility revision precondition.

## Database concurrency boundary

The companion table enforces uniqueness for:

```text
(tenant_key, aggregate_key, version)
assessment_id
(tenant_key, governance_activity_id)
(tenant_key, effect_fingerprint)
```

For the current first-version-only slice, the aggregate/version uniqueness prevents two concurrent first canonical revisions from both being committed.

## Final authorization

G.3 reconstructs the exact accepted E.2 `MaterialAction` and the original E.2 idempotency key.

Before a first effect it revalidates G.2 and requires the same durable verification-floor fingerprint and Activity identity.

It then performs a fresh final call to the unchanged:

```text
evaluate_material_action(...)
```

with:

```text
PolicyDisposition.ALLOW
```

Only:

```text
GatewayOutcome.AUTO_EXECUTE
```

may enter the canonical effect transaction.

A0/A1/A2 therefore still cannot commit through G.3. A3 may commit with `post_review_required=true`; A4/A5 may commit subject to all other Gateway gates.

## Canonical idempotency

G.3 is the first eligibility slice to consume the original canonical slot:

```text
governance:<original E.2 idempotency key>
```

The persisted action fingerprint is the exact E.2 MaterialAction fingerprint.

Exact retries prioritize this durable canonical record before fresh case revalidation, matching the existing governed-effect idempotency doctrine. A later case/profile change must not cause an already-committed effect to be duplicated merely because a network/client retry arrives late.

A replay is accepted only if the canonical governance Activity resolves to exactly one consistent:

```text
EligibilityAssessment
EligibilityAssessmentRevision
semantic eligibility Activity
```

and all stored action/intent/readiness/verification/floor/effect fingerprints still agree.

A torn or corrupted persisted state fails closed rather than being silently repaired.

## Canonical assessment content

The first effect writes an `EligibilityAssessment` with:

```text
status = E.2 proposed_state
overall_score = 0.0
confidence = E.2 informational confidence
profile_id/profile_version = accepted E.2 profile binding
target_country/domain = governed pathway
```

`overall_score` is intentionally not synthesized from model confidence or Decision Readiness. There is no canonical eligibility score in the accepted E.2/F.1/G.1/G.2/G.3 contract.

For governed G.3 rows, `overall_score = 0.0` is only a compatibility value required by the legacy `EligibilityAssessment` shape. Governed read/API/UI surfaces must not interpret or present it as a calculated zero eligibility score.

The structured `assessment_json` records:

- G.3 schema version;
- canonical revision version;
- proposed state;
- pathway version;
- Evidence basis;
- VerifiedRule basis;
- E.2 rationale;
- ContextBundle/runtime binding fingerprints;
- E.2 intent fingerprint;
- F.1 readiness fingerprint;
- G.1 verification fingerprint/disposition;
- G.2 verification-floor fingerprint;
- explicit governed marker.

## Atomic transaction

For a fresh authorized effect, G.3 stages:

```text
canonical governance authorization Activity
+ EligibilityAssessment
+ EligibilityAssessmentRevision
+ semantic eligibility Activity
```

and commits once.

The final governance Activity is causally linked to the accepted G.2 floor Activity.

The semantic Activity is causally linked to the final canonical governance Activity.

Target chain:

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

G.3 validates the staged trace before commit. Any failure rolls the whole G.3 transaction back.

The already-accepted G.2 floor Activity is a prior durable prerequisite and is not part of the G.3 rollback unit.

## Transparency

The semantic effect uses:

```text
activity_class = decision
activity_type = organization.eligibility.assessment_committed.v1
constitutional_activity_class = MATERIAL
```

It is Board-inspectable, durable, full-lineage and non-compactable under the constitutional MATERIAL transparency rule.

The payload explicitly carries:

```text
client_facing = false
external_action_authorized = false
```

## A3 post-review

If the final Gateway authorizes at A3, G.3 persists:

```text
post_review_required = true
```

in both the canonical revision and semantic Activity.

G.3 does not falsely claim that the required post-review has already occurred.

## No silent legacy promotion

Existing legacy `EligibilityAssessment` rows are not automatically made canonical.

G.3 may create the first governed canonical revision even when unrelated legacy assessment rows exist for the Lead.

Only an assessment linked through `EligibilityAssessmentRevision` is a V1.3 governed canonical eligibility effect.

## No external effect

G.3 does not:

- change Lead lifecycle/status;
- mutate an Application;
- communicate a result to the client;
- send an external communication;
- submit anything to government;
- authorize another material action;
- expose a new HTTP endpoint.

The canonical eligibility assessment remains an internal organizational truth object. Client/external use remains separately governed.

## Tests

`apps/api/tests/test_organization_eligibility_effect.py` covers the first G.3 contract, including:

1. first canonical effect creates assessment + revision atomically;
2. full E.2 → G.1 → G.2 → G.3 causation/trace lineage;
3. exact retry returns durable idempotent replay with no duplicates;
4. exact retry still resolves after later case change;
5. A0/A1/A2 do not commit;
6. A3 commits with mandatory post-review flag;
7. forged G.2 floor identity is rejected;
8. stale case before first effect fails closed;
9. legacy assessments do not self-promote into canonical revisions;
10. implicit second canonical revision is refused until supersession semantics exist;
11. synthetic mid-transaction failure rolls back governance, assessment and revision;
12. torn persisted canonical state fails closed on replay;
13. Lead state is not changed and external/client action remains unauthorized.

Accepted focused result:

```text
15 passed / 1 warning / 0 failed
Duration: 9.50s
```

## Migration posture

G.3 introduces one migration:

```text
0077_canonical_eligibility_assessment_revision
```

Accepted schema truth:

```text
registered_tables = 119
actual_tables     = 119
physical_tables   = 120 incl. alembic_version
```

No existing eligibility row is rewritten by the migration.

## Acceptance

Canonical acceptance record:

- `docs/V1_3_G3_ACCEPTANCE_2026-08-20.md`

Accepted evidence includes:

```text
Migration-boundary repairs     2 passed / 1 warning / 0 failed
G.3 focused                    15 passed / 1 warning / 0 failed
Full API regression            1040 passed / 5 skipped / 1 warning / 0 failed
Duration                       505.33s
Repository policy              PASS
Protected v10.22 regression    1 passed / 1 warning / 0 failed
Migration check                PASS
Migration head                 0077_canonical_eligibility_assessment_revision
Registered tables              119
Local DB schema                PASS
Actual tables                  119
Physical tables                120 incl. alembic_version
git diff --check               clean
V12 branch                     clean / synchronized
```

No GitHub CI PASS is claimed because no attached status/check evidence was observed for the accepted implementation head.

## Non-claims

G.3 does not claim:

- eligibility reassessment/supersession support;
- a generic canonical-effect framework;
- client-facing eligibility publication;
- legal/professional sign-off where required;
- HTTP/worker orchestration for the new vertical;
- generic Peer Review Network completion;
- provider-egress policy completion;
- GitHub CI PASS.

## Direction after G.3

The first governed eligibility vertical has now proven proposal → readiness → independent verification → authorization → canonical effect end to end.

The next bounded work should consolidate and operationalize the proven vertical before broad Organization Fabric work:

1. extract stable duplicated vertical helpers where semantics are now proven identical (intent→domain mapping, system-agent command context, public pathway publication-integrity contract, eligibility action reconstruction/reference helpers);
2. expose a trusted governed HTTP/worker orchestration surface that calls the accepted vertical rather than the legacy immediate-persistence path;
3. then define reassessment/supersession using an explicit expected canonical eligibility revision version.

Do not jump to Mission Rooms, generic Peer Review Network, Flight Recorder or broad Munder runtime expansion before the accepted first vertical is operationally reachable through a governed surface.

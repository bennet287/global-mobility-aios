# V1.3-I.4 — Qualified + Temporal Autonomy Evidence Evaluation Foundation

**Date:** 2026-08-22
**Status:** COMPLETE / PASS / SEALED
**Accepted technical candidate:** `46727cd130923f4ede825965cea3a011537a930b`
**Accepted V12 Production Proof:** `32560318311` — 4/4 jobs PASS
**Standalone Repository Policy:** `32560318310` — PASS
**Parent checkpoints:** I.1, I.2 and I.3 — COMPLETE / PASS / SEALED; I.3 profile-precondition hardening — ACCEPTED / PASS / SEALED
**Acceptance record:** `docs/V1_3_I4_QUALIFIED_TEMPORAL_AUTONOMY_EVIDENCE_EVALUATION_ACCEPTANCE_2026-08-22.md`

## 1. Purpose

I.4 is the accepted pre-mutation evidence boundary between sealed I.3 eligibility criteria and any future capability-specific autonomy-changing command.

```text
I.1 canonical autonomy truth
→ I.2 immutable shadow observations
→ I.3 Board-authored eligibility criteria
→ I.4 qualified + time-bounded promotion-grade evidence evaluation
→ future autonomy mutation — NOT PART OF I.4
```

I.4 answers:

> Which current-profile observations are admissible as promotion-grade evidence now, which quality facts can be derived from canonical domain truth, and which required facts remain unavailable rather than trusted by attestation?

I.4 remains non-authorizing.

```text
qualified evidence ≠ promotion eligibility approval ≠ autonomy mutation ≠ authority grant
```

## 2. Why I.4 exists

Accepted I.2 intentionally permits trusted Human Board/admin and trusted SYSTEM measurement writers to record measurement facts. That is sufficient for a shadow measurement foundation but is not sufficient by itself for executable earned autonomy.

I.4 strengthens the evidence boundary without rewriting sealed I.2 history or pretending its attested measurement fields always had deterministic domain derivation.

The accepted I.4 contract addresses these risks:

- an I.2 observation may reference a same-tenant `OrganizationActivity`, but promotion-grade evidence must satisfy a capability-specific qualification adapter;
- quality facts used for promotion-grade evaluation must be derived where canonical domain truth supports them rather than copied from trusted I.2 flags;
- `freshness_compliant` remains historical I.2 observation truth and is not treated as a current temporal guarantee;
- promotion-grade evaluation uses explicit evaluation time and separate observation/source age bounds;
- evaluation candidate sets are bounded;
- Board summary transparency is bounded and detailed provenance is separately paged;
- I.2 index changes remain query-driven rather than aesthetic.

## 3. Permanent doctrine

I.4 preserves:

```text
Memory ≠ Truth
Capability ≠ Authority ≠ Autonomy ≠ Risk
Board ceiling remains supreme
agents cannot self-promote or self-grade into permission
provider/model output is not canonical authority
scores/confidence are not permission
eligibility is not permission
unknown derivation ≠ false
unknown derivation ≠ pass
```

A fact that cannot be deterministically derived from an accepted canonical source is represented as unavailable / not derivable. I.4 does not copy an I.2 attestation into a promotion-grade derived fact merely because the writer was trusted.

## 4. First supported qualification adapter — intentionally bounded

I.4 does not introduce a generic Activity-type whitelist for all future capabilities.

The first accepted source-qualification contract is:

```text
capability = eligibility.proposal
qualification_contract = governed-eligibility-canonical-effect.v1
```

An I.2 observation is source-qualified only when its `source_activity_id` resolves to the canonical G.3 semantic eligibility effect:

```text
organization.eligibility.assessment_committed.v1
```

and the existing shared canonical eligibility-lineage validator proves the complete durable chain:

```text
E.2 governed proposal
→ F.1 Decision Readiness
→ G.1 blind independent verification
→ G.2 verification floor
→ G.3 canonical authorization
→ canonical EligibilityAssessmentRevision
→ semantic eligibility effect
```

The qualifier uses the existing `organization_eligibility_lineage.py` contract rather than reimplementing a partial lineage locally.

No other Activity type is promotion-grade in I.4 v1. Unsupported capabilities/contexts fail closed rather than falling back to generic attestation.

## 5. Exact I.1 profile binding

I.4 evaluation policy is scoped to one exact immutable I.1 profile revision:

```text
tenant
+ profile_id
+ profile_sequence witness
+ profile_record_fingerprint witness
+ persistent OrganizationPosition
+ capability
+ context scope
```

A same-level I.1 supersession creates a new I.4 policy/evaluation scope even when autonomy level and evidence-policy version remain unchanged.

The accepted writer uses the same current-profile optimistic/locking semantics proven by the I.3 profile-precondition hardening. A new policy must not report success for a profile that becomes historical during the transaction.

## 6. Durable evaluation policy

I.4 adds one append-only Board-authored policy model:

```text
CapabilityAutonomyEvidenceEvaluationPolicy
```

The policy records:

```text
exact I.1 profile identity/fingerprint
policy sequence
qualification contract
maximum observation age
maximum canonical source age
maximum candidate observations per evaluation
policy reason
Board decision Activity identity/fingerprint
append-only supersession
idempotency key
semantic fingerprint
```

The policy does **not** contain quality-pass thresholds already owned by I.3.

The two age bounds are distinct and required:

```text
observation age = evaluation_as_of - I.2 observation.created_at
source age      = evaluation_as_of - canonical source Activity.occurred_at
```

Both must be within policy bounds. Recording a new I.2 observation today cannot refresh an old canonical execution into recent promotion evidence.

## 7. Evaluation time contract

The internal evaluation service accepts an explicit timezone-aware `evaluation_as_of` for deterministic testing/replay. Board HTTP transparency uses server time; request parameters cannot move evaluation time backward or forward to manufacture eligibility.

The accepted snapshot records:

```text
evaluation_as_of
observation cutoff
source cutoff
policy identity/sequence
exact profile identity
qualification contract
candidate count
qualified count
excluded stale-observation count
excluded stale-source count
excluded unqualified-source count
missing-derivation fields
promotion_grade_ready
```

No evaluation result is persisted as a second mutable score truth in I.4.

## 8. Derived facts for governed eligibility v1

For each source-qualified canonical eligibility effect, I.4 derives only what the accepted lineage actually proves.

### 8.1 Qualifying execution

A fully validated canonical eligibility effect counts as one qualifying execution.

The source Activity and canonical revision/effect fingerprint must remain intact. Any lineage/fingerprint failure fails closed.

### 8.2 Evidence grounding

Grounding is derived from canonical governed lineage, not copied from `CapabilityAutonomyEvidenceObservation.evidence_grounded`.

The canonical eligibility assessment must carry non-empty governed Evidence basis and rule basis whose lineage passed the existing G.1/G.2/G.3 validator. If durable lineage does not prove the basis, grounding is unavailable rather than assumed.

### 8.3 Verifier contradiction

A committed governed eligibility effect necessarily carries accepted G.1 `disposition = agrees` under the canonical lineage contract. For that qualified effect, verifier contradiction is deterministically `false`.

A disagreeing/insufficient G.1 outcome cannot be laundered into a qualified canonical effect.

### 8.4 Policy compliance

A qualified canonical effect carries accepted G.2 floor satisfaction and G.3 canonical `AUTO_EXECUTE` authorization lineage. For that effect, policy compliance is deterministically `true`.

This does not mean a future autonomy policy is satisfied; it means the underlying governed execution passed its own canonical policy/authority floor.

### 8.5 Human review outcome

Human outcome is derived only from authenticated immutable `OrganizationHumanAction` records explicitly bound to the exact canonical `eligibility_assessment` and revision version.

Accepted explicit mapping:

```text
approved           → accepted
requested_changes  → modified
rejected           → rejected
no qualifying action by evaluation_as_of → not_reviewed
```

Generic `reviewed`, attested, acknowledged, assigned or resolved actions do not imply acceptance.

When multiple explicit review outcomes exist for the same exact assessment revision, the latest outcome at or before `evaluation_as_of` is authoritative only if ordering is deterministic. Ambiguous equal-time conflicting terminal outcomes fail closed.

### 8.6 Facts not derivable in I.4 v1

Unless an exact typed canonical linkage is separately proven, I.4 v1 marks these promotion-grade dimensions unavailable rather than copying I.2 inputs:

```text
source-freshness quality separate from execution/source age
critical-error outcome for the exact execution
recovery applicability/result for the exact execution
SLA-met outcome for the exact execution
incident count attributable to the exact execution
```

Eligibility-aggregate immune incidents are useful safety truth, but aggregate-level incidents are not assigned to one execution without a deterministic causal/identity contract.

Therefore `promotion_grade_ready` may remain false until configured I.3 criteria can be evaluated exclusively from qualified/derived facts.

## 9. Temporal inclusion

An observation participates only when all are true:

```text
observation belongs to the exact current I.1 profile
observation semantic/source fingerprints remain valid
observation.created_at <= evaluation_as_of
source Activity.occurred_at <= evaluation_as_of
observation.created_at >= observation cutoff
source Activity.occurred_at >= source cutoff
source passes the capability qualification adapter
```

Future-dated evidence fails integrity validation rather than being silently ignored.

Historical exact I.2 replay remains available through I.2. I.4 only determines whether evidence is admissible for current promotion-grade evaluation.

## 10. Bounded evaluation and transparency

I.4 does not return the unbounded I.2 observation tuple inside its promotion-grade snapshot.

The accepted Board summary endpoint is:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/evidence-evaluation?context_scope=...
```

Detailed provenance is a separate paginated read:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/evidence-evaluation/provenance?context_scope=...&limit=...&cursor=...
```

Accepted requirements:

- explicit maximum page size;
- stable newest-first ordering by `created_at` plus unique-ID tie-breaker;
- stable cursor semantics;
- no raw Activity payload JSON;
- no HTTP write route;
- summary response does not nest an unbounded lifetime observation list.

The evaluation policy carries a maximum candidate-observation bound. Exceeding it fails closed with an operationally bounded evaluation error rather than silently truncating metrics.

## 11. Query/index doctrine

I.4 adds no index changes merely because low-cardinality indexes look undesirable.

The accepted evaluation access shape is centered on:

```text
tenant + exact profile + created_at
```

Source qualification resolves by canonical source Activity identity. Pagination uses profile/time/id ordering.

Future I.2 index removal/replacement requires measured query-plan/workload evidence and schema-parity proof.

## 12. Relationship to I.2 and I.3

I.2 remains the canonical immutable shadow-observation history and is not rewritten.

I.3 remains the canonical Board criteria/eligibility foundation and its historical `ELIGIBLE` projection remains non-authorizing.

I.4 creates the stricter evidence input required before a future autonomy-changing layer can consume an eligibility decision.

I.4 does not silently redefine I.2 historical metrics. Where I.4 derives a stricter metric, it is explicitly promotion-grade qualified/temporal truth.

A future mutation stage must consume I.4 promotion-grade readiness, not raw lifetime I.2 attestations or I.3 eligibility alone.

## 13. Migration shape — accepted

I.4 adds exactly one application table through the existing linear Alembic lineage:

```text
0080_capability_autonomy_promotion_policy_foundation
→ 0081_capability_autonomy_evidence_evaluation_policy
```

Accepted registered application-table count:

```text
124
```

Accepted physical-table count:

```text
125 including alembic_version
```

No second migration head is introduced. No durable per-evaluation aggregate table is added in I.4 v1.

## 14. Acceptance tests — satisfied

The exact accepted candidate proves:

- Board-only evaluation-policy establishment;
- exact-profile optimistic precondition and PostgreSQL serialization with I.1 supersession;
- exact idempotent replay/divergent conflict;
- append-only policy supersession/stale sequence rejection;
- age/window/count policy validation;
- unsupported capability/qualification adapter fail-closed behavior;
- arbitrary same-tenant Activity exclusion from promotion-grade evidence;
- canonical eligibility semantic Activity qualification with valid G.1/G.2/G.3 lineage;
- torn/corrupted canonical eligibility lineage fail-closed behavior;
- I.2 observation/source fingerprint drift fail-closed behavior;
- new observation over an old canonical source not refreshing source age;
- stale observation exclusion;
- stale source exclusion;
- future-dated observation/source failure;
- deterministic human `approved / requested_changes / rejected / not_reviewed` derivation;
- generic non-terminal review not implying acceptance;
- ambiguous conflicting human review ordering fail-closed behavior;
- unavailable dimensions remaining unavailable rather than inheriting I.2 attestations;
- bounded summary projection;
- stable and capped provenance pagination;
- no I.4 HTTP write route;
- no I.1 autonomy/Board ceiling/authority mutation;
- migration/schema `0081` / 124-app-table proof on SQLite and PostgreSQL;
- real PostgreSQL policy-writer concurrency proof;
- full four-lane V12 Production Proof.

Exact proof:

```text
technical candidate                  46727cd130923f4ede825965cea3a011537a930b
V12 Production Proof                 32560318311 — 4/4 jobs PASS
Standalone Repository Policy         32560318310 — PASS
SQLite regression                    1172 passed / 19 skipped / 1 warning / 0 failed
PostgreSQL governed/autonomy suite   102 passed / 1 warning / 0 failed
Alembic                               0001 → 0081 PASS
registered application tables        124
physical tables                      125 including alembic_version
frontend                              PASS
repository/release/deps/diff          PASS
```

## 15. Explicit non-claims

I.4 does not claim or implement:

- automatic promotion;
- automatic downgrade;
- an autonomy-change command;
- a Dynamic Autonomy Manager;
- completion of all quality derivations for every capability;
- generic promotion-grade evidence adapters for arbitrary Activity types;
- source-freshness derivation where canonical source metadata does not prove it;
- execution-attributed critical-error/recovery/SLA/incident semantics without typed linkage;
- replacement of I.2 historical measurement truth;
- replacement of I.3 Board thresholds;
- agent self-promotion;
- provider/model-specific autonomy grants;
- weakening of Board/Human/legal/professional floors;
- final query-optimized I.2 index layout;
- production-scale operational readiness.

## 16. Acceptance boundary — sealed

I.4 is accepted only for the exact implementation and proof recorded above.

```text
I.1 SEALED
I.2 SEALED
I.3 SEALED
I.3 profile-precondition hardening SEALED
I.4 SEALED
actual autonomy mutation NOT STARTED
Dynamic Autonomy Manager NOT STARTED
```

A later autonomy-changing increment requires its own bounded contract, exact current-profile concurrency semantics, explicit Board authority, append-only change lineage, recovery/Human override rules and separate Production Proof. I.4 acceptance does not pre-authorize that increment.

# V1.3-I.4 — Qualified + Temporal Autonomy Evidence Evaluation Acceptance

**Date:** 2026-08-22
**Status:** COMPLETE / PASS / SEALED
**Technical candidate:** `46727cd130923f4ede825965cea3a011537a930b`
**V12 Production Proof:** `32560318311` — 4/4 jobs PASS
**Standalone Repository Policy:** `32560318310` — PASS
**Migration head:** `0081_capability_autonomy_evidence_evaluation_policy`
**Registered SQLModel application tables:** 124
**Physical tables:** 125 including `alembic_version`

## 1. Acceptance decision

V1.3-I.4 is accepted and sealed as the qualified + temporal autonomy evidence evaluation foundation.

The accepted boundary is deliberately non-authorizing:

```text
I.1 canonical autonomy truth
→ I.2 immutable shadow observations
→ I.3 Board-authored promotion eligibility criteria
→ I.4 qualified + time-bounded promotion-grade evidence evaluation
→ future autonomy mutation — NOT PART OF I.4
```

The permanent rule remains:

> **qualified evidence evaluation ≠ promotion approval ≠ autonomy mutation ≠ authority grant**

I.4 therefore closes the evidence-provenance, time-boundary and bounded-read prerequisite that had to exist before any future capability-specific autonomy mutation could be designed. It does not itself change autonomy.

## 2. Exact proof

The exact accepted technical candidate is:

```text
46727cd130923f4ede825965cea3a011537a930b
```

The exact V12 Production Proof is:

```text
32560318311 — 4/4 jobs PASS
```

The standalone Repository Policy run is:

```text
32560318310 — PASS
```

Accepted backend proof:

```text
Python                                             3.12.14
Alembic                                            PASS — 0001 → 0081
Registered SQLModel application tables             124
Fresh SQLite physical tables                       125 including alembic_version
Backend SQLite regression                         1172 passed / 19 skipped / 1 warning / 0 failed
Fresh PostgreSQL 16 migration/schema               PASS
PostgreSQL governed/autonomy suite                  102 passed / 1 warning / 0 failed
```

Accepted frontend proof:

```text
npm ci                                             PASS
npm audit --audit-level=high                       PASS
frontend design foundation                         PASS
frontend request/auth                              PASS
TypeScript --noEmit                                PASS
Next.js production build                           PASS
compiled-auth verification                         PASS
```

Accepted repository proof:

```text
repository policy                                  PASS
release consistency                                PASS — 0081
Python direct-dependency constraints               PASS
diff hygiene                                       PASS
```

The known Pydantic `model_metadata_json` protected-namespace warning remains historical and non-blocking.

## 3. Accepted durable policy truth

I.4 accepts one append-only Board-authored policy model:

```text
CapabilityAutonomyEvidenceEvaluationPolicy
```

The policy is frozen to one exact immutable I.1 profile revision using profile identity plus sequence/fingerprint witnesses. New writes use the current-profile precondition and serialization semantics inherited from the sealed I.3 profile-precondition hardening, so policy establishment cannot report success for a profile that became historical during the transaction.

The accepted policy carries separate limits for:

```text
maximum observation age
maximum canonical source age
maximum candidate observations per evaluation
qualification contract
policy sequence / append-only supersession
Board Activity identity/fingerprint
idempotency / semantic fingerprint
```

I.3 continues to own promotion-quality thresholds. I.4 does not duplicate those thresholds into a second policy truth.

## 4. Accepted qualification boundary

The first accepted promotion-grade qualification adapter is intentionally capability-specific:

```text
capability = eligibility.proposal
qualification_contract = governed-eligibility-canonical-effect.v1
```

A candidate I.2 observation qualifies only when its source resolves to the canonical semantic eligibility effect:

```text
organization.eligibility.assessment_committed.v1
```

and the existing canonical eligibility-lineage validator proves the durable chain:

```text
E.2 governed proposal
→ F.1 Decision Readiness
→ G.1 blind independent verification
→ G.2 verification floor
→ G.3 canonical authorization
→ canonical EligibilityAssessmentRevision
→ semantic eligibility effect
```

Arbitrary same-tenant Activities are not promotion-grade merely because a trusted I.2 writer referenced them. Unsupported capabilities fail closed; I.4 does not introduce a generic Activity whitelist.

## 5. Accepted derived evidence semantics

For the supported governed-eligibility adapter, I.4 derives only facts proven by canonical domain truth.

Accepted derivations include:

- one valid canonical eligibility effect = one qualifying execution;
- evidence grounding from the accepted governed Evidence/rule lineage rather than the raw I.2 `evidence_grounded` flag;
- verifier contradiction deterministically false only where the accepted G.1 lineage proves `agrees`;
- policy compliance deterministically true only where G.2 floor satisfaction and G.3 canonical `AUTO_EXECUTE` authorization are proven;
- human review outcome only from immutable exact-assessment/revision `OrganizationHumanAction` records.

Accepted terminal human mapping:

```text
approved           → accepted
requested_changes  → modified
rejected           → rejected
no qualifying terminal action by evaluation_as_of → not_reviewed
```

Generic `reviewed`, attested, acknowledged, assigned or resolved actions do not imply acceptance. Ambiguous equal-time conflicting terminal outcomes fail closed.

Dimensions not yet supported by an exact typed canonical linkage remain unavailable rather than copied from I.2 attestations. This includes the still-unsupported execution-level derivation of source-freshness quality, critical errors, recovery, SLA and incidents.

## 6. Accepted temporal contract

I.4 accepts explicit timezone-aware `evaluation_as_of` for deterministic internal evaluation and server-time evaluation for Board HTTP transparency.

Observation age and canonical source age are separate:

```text
observation age = evaluation_as_of - observation.created_at
source age      = evaluation_as_of - source Activity.occurred_at
```

Both must satisfy the accepted policy. Writing a new observation over an old source cannot refresh that source into recent evidence.

Future-dated observation/source evidence fails integrity validation. Stale observations and stale sources are separately excluded and reported.

The final accepted SQLite repair normalizes ORM-loaded SQLite review timestamps inside the test boundary before constructing explicit `evaluation_as_of` values; the production evaluator continues to require timezone-aware timestamps and was not weakened.

## 7. Accepted bounded evaluation and transparency

I.4 accepts a bounded summary read and a separate cursor-paged provenance read:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/evidence-evaluation?context_scope=...

GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/evidence-evaluation/provenance?context_scope=...&limit=...&cursor=...
```

The summary does not nest unbounded lifetime observation history. Provenance paging is capped and stably ordered. Raw Activity payload JSON is not exposed by this contract.

The evaluation policy also bounds candidate observations. Candidate overflow fails closed instead of silently truncating metrics.

There is no I.4 HTTP mutation route.

## 8. Adversarial and concurrency proof accepted

The accepted proof includes coverage for:

- Board-only evaluation-policy establishment;
- exact-profile precondition and I.1 supersession serialization;
- idempotent replay and divergent idempotency conflict;
- append-only supersession and stale sequence rejection;
- invalid age/window/count policy rejection;
- unsupported qualification adapters failing closed;
- arbitrary same-tenant Activity exclusion;
- valid canonical eligibility qualification;
- torn/corrupted canonical eligibility lineage rejection;
- observation/source fingerprint drift rejection;
- stale observation and stale source behavior;
- new-observation/old-source non-refresh behavior;
- future-dated evidence failure;
- explicit terminal human-review derivation;
- generic non-terminal review non-acceptance;
- ambiguous review ordering fail-closed behavior;
- unavailable dimensions remaining unavailable;
- bounded summary and stable/capped provenance pagination;
- no HTTP write path;
- no I.1 autonomy/Board ceiling/authority mutation;
- PostgreSQL competing initial policy writer race;
- PostgreSQL stale policy supersession race;
- PostgreSQL profile-supersession-wins stale-policy rejection.

## 9. Migration acceptance

I.4 advances the single linear Alembic lineage:

```text
0080_capability_autonomy_promotion_policy_foundation
→ 0081_capability_autonomy_evidence_evaluation_policy
```

Accepted schema:

```text
registered application tables = 124
physical tables                = 125 including alembic_version
fresh SQLite                   = PASS
fresh PostgreSQL 16            = PASS
```

No second migration head and no durable per-evaluation aggregate table were introduced.

## 10. Parent checkpoint integrity

The following remain sealed parents and are not rewritten by I.4:

```text
I.1 capability-specific autonomy profile + evidence
I.2 shadow autonomy evidence profile
I.3 promotion eligibility policy
I.3 profile-precondition hardening
```

I.2 remains immutable measurement history. I.3 remains the Board criteria/eligibility layer. I.4 creates the stricter qualified/temporal evidence input required before any later mutation layer may act.

`ELIGIBLE` remains evidence satisfaction, not permission.

## 11. Explicit nonclaims after acceptance

I.4 does **not** implement or authorize:

- automatic promotion;
- automatic demotion/downgrade;
- any autonomy-change command;
- a Dynamic Autonomy Manager;
- autonomy-change lineage after an actual level change;
- recovery-based automatic autonomy restoration;
- agent self-promotion;
- provider/model-specific autonomy grants;
- confidence or score as permission;
- Board-ceiling or Command-Gateway bypass;
- generic promotion-grade adapters for arbitrary capabilities;
- typed deterministic derivation of every historical I.2 measurement dimension;
- execution-attributed critical-error/recovery/SLA/incident semantics without typed linkage;
- final query-optimized I.2 index layout;
- production-scale operational readiness.

## 12. Next gate

With I.4 sealed, the next Earned Autonomy problem may now be designed, but it is **not pre-authorized by this acceptance**.

The next bounded design must preserve Human Owner / Board supremacy and must not introduce automatic self-promotion. Any future capability-specific promotion/demotion command must, at minimum, consume exact current I.1 profile truth, applicable I.3 Board policy semantics and I.4 promotion-grade qualified/temporal evidence; obey Board ceilings; serialize with profile supersession; create append-only autonomy-change lineage; and define explicit Human override/recovery behavior before acceptance.

Until that separate design and proof exist:

```text
I.1 SEALED
I.2 SEALED
I.3 SEALED
I.3 profile-precondition hardening SEALED
I.4 SEALED
actual autonomy mutation NOT STARTED
Dynamic Autonomy Manager NOT STARTED
```

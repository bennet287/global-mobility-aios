# Global Mobility AIOS — V1.3-I.2 Shadow Autonomy Evidence Profile Foundation

**Date:** 2026-08-22  
**Stage:** V1.3-I.2 — Shadow Autonomy Evidence Profile Foundation  
**Status:** IMPLEMENTATION CONTRACT / NOT ACCEPTED  
**Parent checkpoint:** V1.3-I.1 — COMPLETE / PASS / SEALED on technical candidate `581df5d99b65f0a7a49ace228ee707b881d508fa`  
**Parent Production Proof:** GitHub Actions run `32529241957`  
**Parent migration head:** `0078_capability_autonomy_profile_foundation`

## 1. Purpose

I.1 established canonical capability-specific and context-specific autonomy truth. I.2 adds the measurement foundation required before any later earned-autonomy policy may be designed.

I.2 is deliberately **shadow / measurement only**.

It answers:

> For one persistent OrganizationPosition, one capability, one context scope and one explicit I.1 autonomy profile, what qualifying canonical execution evidence has accumulated and what does that evidence objectively show?

It does **not** answer:

> Should the agent be promoted or downgraded?

That policy remains a later bounded I-stage increment.

Permanent doctrine remains:

```text
Memory ≠ Truth
Capability ≠ Authority ≠ Autonomy ≠ Risk
Human Owner / Board remains supreme authority
Agents cannot self-promote
Scores and confidence do not create permission
Immune System may restrict; it does not grant authority
```

## 2. Architecture source

The V1.3 architecture requires earned autonomy to develop through demonstrated performance, beginning in shadow mode, and calls for an `AutonomyEvidenceProfile` that can account for evidence such as:

```text
qualifying execution volume
evidence grounding
human acceptance / modification / rejection
verifier contradiction or disagreement
policy compliance
freshness compliance
critical errors
recovery performance
SLA performance
incident history
```

I.2 implements the **durable evidence + deterministic read-model foundation** for those measurements. It intentionally does not implement the Dynamic Autonomy Manager or promotion/downgrade thresholds.

## 3. Canonical scope

Every I.2 observation is frozen to an exact I.1 profile and therefore to:

```text
tenant
+ persistent OrganizationPosition
+ capability
+ context scope
+ I.1 profile revision
+ evidence-policy version
```

No organization-wide autonomy score exists.

No evidence from another capability, context, tenant, position or profile revision may be silently pooled into the measurement scope.

## 4. Canonical observation record

I.2 introduces one append-only companion record:

```text
CapabilityAutonomyEvidenceObservation
```

Each observation represents exactly one qualifying execution/evaluation unit backed by a canonical `OrganizationActivity`.

Required durable identity and provenance:

```text
id
tenant_key
profile_id
position_id
capability_key
context_scope
profile_sequence
evidence_policy_version
source_activity_id
source_activity_fingerprint
idempotency_key
record_fingerprint
created_by_actor_type
created_by_actor_key
created_at
```

Required measurement facts:

```text
human_review_outcome
  = accepted | modified | rejected | not_reviewed

evidence_grounded
verifier_contradiction
policy_compliant
freshness_compliant
critical_error
recovery_outcome
  = succeeded | failed | not_applicable
sla_met
incident_count
```

The source Activity fingerprint captured at observation time must continue to match the canonical Activity on later reads. Direct database drift must therefore fail closed rather than silently changing measurement truth.

## 5. Trusted writer boundary

There is no I.2 HTTP write route.

Canonical observation establishment is an internal command only.

Allowed trusted actor classes:

```text
HUMAN   authenticated admin / Board governance context
SYSTEM  trusted server-side measurement context
```

Disallowed:

```text
AGENT
WORKER
EXTERNAL_HUMAN
```

An agent cannot record its own success, quality, compliance, acceptance, recovery or incident score as permission evidence.

A SYSTEM observation is server-owned measurement provenance; it is not provider/model self-report and does not imply authority.

## 6. Source-Evidence rules

A qualifying observation must reference one canonical `OrganizationActivity` that:

1. exists;
2. belongs to the same tenant;
3. has a stable canonical fingerprint;
4. is not already counted for the same I.1 profile;
5. is durably frozen into the observation fingerprint.

The observation must also reference an existing canonical I.1 profile whose tenant, position, capability, context, profile sequence and evidence-policy version match the observation scope.

Request-body or caller-provided identity may not substitute for canonical I.1 scope resolution.

## 7. Append-only, replay and concurrency contract

Observations are immutable after commit.

Required database protections:

```text
unique tenant + idempotency_key
unique tenant + profile_id + source_activity_id
composite tenant/profile foreign key
composite tenant/source-activity foreign key
```

Exact idempotent replay returns the existing canonical observation.

Divergent reuse of an idempotency key fails closed.

The same source Activity cannot be double-counted for one I.1 profile even under concurrent PostgreSQL writers.

I.2 deliberately avoids a mutable aggregate counter table. Aggregate measurement is derived from immutable observations, preventing last-write-wins score mutation.

## 8. Deterministic `AutonomyEvidenceProfile` read model

`AutonomyEvidenceProfile` is a **computed read projection**, not a second mutable authority record.

For one exact I.1 profile, the read model exposes deterministic counts and rates such as:

```text
qualifying_execution_volume

evidence_grounded_count
evidence_grounding_rate

human_accepted_count
human_modified_count
human_rejected_count
human_not_reviewed_count
human_acceptance_rate
human_modification_rate
human_rejection_rate

verifier_contradiction_count
verifier_contradiction_rate

policy_compliant_count
policy_compliance_rate

freshness_compliant_count
freshness_compliance_rate

critical_error_count
critical_error_rate

recovery_applicable_count
recovery_succeeded_count
recovery_failed_count
recovery_success_rate

sla_met_count
sla_met_rate

incident_count
```

Rate denominators are explicit:

- general rates use qualifying execution volume;
- human acceptance/modification/rejection rates use only human-reviewed observations (`accepted + modified + rejected`), excluding `not_reviewed`;
- recovery success rate uses only recovery-applicable observations (`succeeded + failed`).

When a denominator is zero, the rate is `null`, not fabricated as zero or one.

Rates are derived server-side from canonical counts. Persisted caller-supplied percentages are prohibited.

## 9. Board / Cockpit transparency

I.2 extends the existing Board-only transparency facade with a GET-only evidence-profile surface under the current autonomy namespace.

Target route:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/evidence?context_scope=...
```

The response includes:

- exact current I.1 profile identity and sequence;
- current autonomy level and Board ceiling for context only;
- evidence-policy version;
- deterministic measurement counts/rates;
- append-only observation history with source Activity IDs/fingerprints;
- no raw Activity payload JSON.

The route remains Board/admin-only and read-only.

## 10. Integrity requirements

Before returning a snapshot, I.2 must verify:

```text
current I.1 profile integrity through the I.1 read contract
observation tenant/profile/scope continuity
profile sequence and evidence-policy continuity
source Activity existence and tenant continuity
source Activity fingerprint continuity
observation semantic record fingerprint integrity
unique source Activity counting within the exact profile
```

Any integrity failure returns a fail-closed conflict rather than a partial or misleading measurement profile.

## 11. Autonomy non-effect

I.2 measurement is never an autonomy mutation.

Establishing or reading an observation must not change:

```text
CapabilityAutonomyProfile.autonomy_level
CapabilityAutonomyProfile.board_ceiling_level
CapabilityAutonomyProfile.authority_requirement
CapabilityAutonomyProfile.risk_ceiling
CapabilityAuthority
Command Gateway decisions
Human / Board / legal / professional review floors
```

A perfect evidence profile grants nothing by itself.

A poor evidence profile changes nothing automatically in I.2.

Later promotion/downgrade policy must receive its own explicit contract, thresholds, anti-gaming controls, recovery behavior and Production Proof.

## 12. Required tests before acceptance

I.2 acceptance requires contract coverage for at least:

1. trusted Human Board observation establishment;
2. trusted SYSTEM observation establishment;
3. AGENT self-grading refusal;
4. foreign-tenant source Activity refusal;
5. profile/scope mismatch refusal;
6. exact idempotent replay;
7. divergent idempotency failure;
8. duplicate source Activity cannot double-count;
9. deterministic counts and denominator-aware rates;
10. context/profile-revision separation;
11. source Activity fingerprint drift fails closed;
12. observation fingerprint drift fails closed;
13. Board-only read route;
14. absence of an I.2 HTTP write route;
15. observations do not mutate I.1 autonomy truth;
16. real PostgreSQL concurrent same-source writers yield exactly one canonical observation;
17. fresh SQLite and PostgreSQL migration/schema proof at the new single Alembic head;
18. full backend, frontend and repository Production Proof remains green.

## 13. Migration doctrine

I.2 should add exactly one bounded observation table through the existing linear Alembic lineage.

Target migration:

```text
0079_capability_autonomy_evidence_profile_foundation
```

Expected registered application-table count after implementation:

```text
122
```

No independent migration head is permitted.

## 14. Explicit non-claims

I.2 does **not** claim:

- automatic autonomy promotion;
- automatic autonomy downgrade;
- a Dynamic Autonomy Manager;
- promotion eligibility or promotion recommendation;
- agent self-grading or self-promotion;
- provider/model self-reported quality as canonical evidence;
- provider/model-specific autonomy grants;
- a single organization-wide autonomy score;
- confidence or score as permission;
- replacement of the I.1 Board ceiling;
- replacement of the Command Gateway;
- weakening of Human/Board/legal/professional review floors;
- completion of the wider Earned Autonomy stage;
- completion of the future Organizational Immune System.

## 15. Acceptance gate

I.2 may move to **COMPLETE / PASS / SEALED** only when:

```text
implementation contract satisfied
+ exact-candidate repository policy/constraints/diff hygiene PASS
+ full SQLite backend regression PASS
+ fresh migration/schema proof PASS at 0079
+ frontend proof PASS
+ real PostgreSQL governed contracts PASS
+ concurrent same-source observation proof PASS
+ acceptance record reconciled to the exact tested candidate
```

Until then, any implementation remains **IMPLEMENTED / ACCEPTANCE PENDING**.

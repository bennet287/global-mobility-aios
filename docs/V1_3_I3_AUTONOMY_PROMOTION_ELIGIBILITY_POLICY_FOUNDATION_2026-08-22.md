# V1.3-I.3 — Autonomy Promotion Eligibility Policy Foundation

**Date:** 2026-08-22
**Status:** IMPLEMENTATION CONTRACT / ACCEPTANCE NOT YET CLAIMED
**Parent checkpoints:** V1.3-I.1 and V1.3-I.2 — COMPLETE / PASS / SEALED

## 1. Purpose

I.3 implements the next bounded Earned Autonomy step after accepted I.2 shadow measurement:

```text
I.1 canonical autonomy truth
→ I.2 immutable shadow evidence + deterministic metrics
→ I.3 versioned promotion criteria + deterministic eligibility evaluation
```

I.3 answers one question only:

> Given the current validated I.1 profile, the current exact-profile I.2 evidence profile and a Human Board-established promotion policy, does the evidence satisfy the criteria for a **proposed one-step autonomy promotion**?

Eligibility is not authority and is not an autonomy mutation.

```text
promotion eligibility ≠ promotion approval ≠ autonomy change ≠ authority grant
```

## 2. Constitutional boundary

I.3 must preserve:

```text
Capability ≠ Authority ≠ Autonomy ≠ Risk
Board ceiling remains supreme
Command Gateway remains authoritative for governed execution
Human/legal/professional floors remain unchanged
agents cannot self-promote
provider/model identity cannot grant autonomy
scores or confidence cannot become permission
Immune System remains restrict-only
```

I.3 may identify that evidence satisfies Board-authored criteria. It may not update `CapabilityAutonomyProfile`, mint `CapabilityAuthority`, change a Board ceiling, or execute an external action.

## 3. Canonical policy scope

Promotion criteria are not universal. One policy is scoped to:

```text
tenant
+ persistent OrganizationPosition
+ capability
+ context scope
+ current autonomy level
+ next autonomy level
+ exact I.1 evidence-policy version
```

The target must be exactly one A-level above the current level and must remain at or below the current I.1 Board ceiling.

A policy cannot pre-authorize an A-level that the current Board ceiling forbids.

## 4. Durable policy truth

I.3 adds one append-only canonical model:

```text
CapabilityAutonomyPromotionPolicy
```

The policy records:

```text
scope
policy sequence
from autonomy level
target autonomy level
evidence-policy version
minimum qualifying execution volume
minimum reviewed-human sample
minimum evidence-grounding rate
minimum human acceptance rate
maximum human modification rate
maximum human rejection rate
maximum verifier-contradiction rate
minimum policy-compliance rate
minimum freshness-compliance rate
maximum critical-error count
optional minimum recovery sample + recovery-success rate
minimum SLA-met rate
maximum incident count
Board decision Activity identity + captured fingerprint
append-only supersession
idempotency key
semantic fingerprint
policy reason
```

No aggregate permission score is stored.

## 5. Board-authored criteria

The canonical policy writer is internal and HTTP-independent.

It requires:

```text
authenticated HUMAN
+ admin role
+ persistent Board position
+ active target OrganizationPosition
+ current validated I.1 profile
+ from level == current I.1 autonomy level
+ target level == exactly one level above current
+ target <= current Board ceiling
+ policy evidence version == current I.1 evidence-policy version
```

AGENT, WORKER, SYSTEM and EXTERNAL_HUMAN actors do not establish promotion criteria in I.3.

There is deliberately no I.3 HTTP policy-write route.

## 6. Append-only policy lineage

Policy revisions are immutable.

For one exact policy scope:

```text
v1 → v2 → v3
```

Each new revision explicitly supersedes the current revision. One predecessor cannot fork into multiple successors.

Required protections:

```text
unique tenant + idempotency key
unique exact scope + policy sequence
unique tenant + supersedes policy id
expected_policy_sequence for supersession
PostgreSQL current-policy locking where available
semantic policy fingerprint
Board decision Activity fingerprint continuity
```

Exact idempotent replay resolves the original immutable policy. Divergent reuse fails closed.

## 7. Deterministic eligibility projection

I.3 computes an `AutonomyPromotionEligibilitySnapshot`; it does not persist a second mutable recommendation truth.

The evaluator must first validate:

1. I.1 canonical profile integrity;
2. I.2 exact-profile evidence integrity;
3. current promotion-policy lineage/integrity;
4. current autonomy level matches the policy `from` level;
5. policy evidence version matches the current I.1/I.2 evidence version;
6. target is still within the current Board ceiling.

The evaluator exposes every criterion with:

```text
criterion key
comparison
required value
observed value
sample/evaluable state
pass/fail state
```

No hidden weighted score is used.

## 8. Eligibility states

The bounded deterministic result is:

```text
ELIGIBLE
INSUFFICIENT_EVIDENCE
HOLD
```

Meaning:

- `ELIGIBLE` — all minimum sample requirements and all quality criteria pass;
- `INSUFFICIENT_EVIDENCE` — no known quality blocker fails, but required evidence/review/recovery sample volume is not yet sufficient;
- `HOLD` — at least one evaluable quality/safety criterion fails.

A known quality/safety failure dominates an insufficient sample and therefore returns `HOLD`.

`ELIGIBLE` means only that the current evidence satisfies the current Board-authored criteria. It does not change autonomy.

## 9. Criteria semantics

Sample sufficiency:

```text
qualifying execution volume >= policy minimum
reviewed-human sample >= policy minimum
recovery-applicable sample >= policy minimum, when recovery criteria are configured
```

Quality criteria:

```text
evidence grounding rate >= minimum
human acceptance rate >= minimum
human modification rate <= maximum
human rejection rate <= maximum
verifier contradiction rate <= maximum
policy compliance rate >= minimum
freshness compliance rate >= minimum
critical error count <= maximum
recovery success rate >= minimum, when configured
SLA-met rate >= minimum
incident count <= maximum
```

I.2 denominator semantics remain canonical. I.3 must not recalculate rates from a different denominator contract.

## 10. Transparency

Board/Cockpit receives a read-only view under the existing autonomy transparency namespace:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/promotion-eligibility?context_scope=...
```

The view should expose:

```text
current I.1 profile identity/sequence/autonomy/Board ceiling
current I.2 evidence profile identity and metrics
current I.3 policy identity/sequence/from/target/version
eligibility state
criterion-by-criterion evidence
```

It must not expose raw Activity payload JSON or provide a mutation route.

## 11. Migration shape

I.3 adds exactly one application table through the existing linear Alembic lineage:

```text
0079_capability_autonomy_evidence_profile_foundation
→ 0080_capability_autonomy_promotion_policy_foundation
```

Expected registered application-table count after I.3:

```text
123
```

No second migration head is permitted.

## 12. Required tests

Acceptance requires, at minimum:

- Board-only policy establishment;
- non-Board writer refusal;
- exact one-step promotion requirement;
- target-above-Board-ceiling refusal;
- evidence-policy-version match;
- threshold/range validation;
- exact idempotent replay;
- divergent idempotency conflict;
- append-only policy supersession;
- stale expected policy sequence rejection;
- deterministic `ELIGIBLE` result at exact boundaries;
- deterministic `INSUFFICIENT_EVIDENCE` result for sample deficits;
- deterministic `HOLD` when any evaluable quality/safety criterion fails;
- zero-denominator behavior inherited from I.2 without invented rates;
- current I.1 profile supersession makes the old promotion policy non-current for eligibility;
- policy Activity fingerprint drift fails closed;
- policy semantic fingerprint drift fails closed;
- I.2 evidence drift still fails closed through I.3;
- Board-only read API;
- no policy/autonomy HTTP write route;
- proof that evaluation does not mutate I.1 autonomy truth;
- fresh migration head `0080` and 123-table schema;
- real PostgreSQL concurrent policy-writer/stale-supersession protection.

## 13. Explicit non-claims

I.3 does not claim or implement:

- automatic promotion;
- automatic downgrade/demotion;
- autonomy mutation;
- an autonomy-change command;
- a Dynamic Autonomy Manager;
- recovery-based automatic restoration;
- autonomy-change lineage after an actual level change;
- Human override execution semantics;
- provider/model-specific autonomy grants;
- agent self-promotion;
- a universal organization-wide promotion threshold;
- a single aggregate promotion score;
- replacement of Board ceilings;
- replacement of the Command Gateway;
- weakening of legal/professional/Human review floors.

Those remain later bounded Earned Autonomy increments and require separate contracts and proof.

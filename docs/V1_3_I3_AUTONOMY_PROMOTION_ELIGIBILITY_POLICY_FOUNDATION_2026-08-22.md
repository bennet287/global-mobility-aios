# V1.3-I.3 — Autonomy Promotion Eligibility Policy Foundation

**Date:** 2026-08-22
**Status:** ACCEPTED / COMPLETE / PASS / SEALED
**Accepted technical candidate:** `77b2e9adb30d69419158930b31c0bc10515cb6a7`
**Accepted Production Proof:** GitHub Actions run `32536826352`
**Parent checkpoints:** V1.3-I.1 and V1.3-I.2 — COMPLETE / PASS / SEALED

## 1. Purpose

I.3 is the bounded Earned Autonomy policy/evaluation layer after accepted I.2 shadow measurement:

```text
I.1 canonical autonomy truth
→ I.2 immutable shadow evidence + deterministic metrics
→ I.3 exact-profile Board criteria + deterministic promotion eligibility
```

I.3 answers one question only:

> Given the current validated I.1 profile, its current exact-profile I.2 evidence profile and a Human Board-established policy frozen to that exact I.1 profile revision, does the evidence satisfy the criteria for a proposed one-step autonomy promotion?

Eligibility is not authority and is not an autonomy mutation.

```text
promotion eligibility ≠ promotion approval ≠ autonomy change ≠ authority grant
```

## 2. Constitutional boundary

I.3 preserves:

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

I.3 may identify that evidence satisfies Board-authored criteria. It may not update `CapabilityAutonomyProfile`, mint `CapabilityAuthority`, change a Board ceiling, execute an external action or authorize a future promotion command by itself.

## 3. Canonical policy scope — exact I.1 profile revision

Promotion criteria are not universal and are not reusable merely because autonomy level/version strings happen to match.

The durable policy is frozen to:

```text
tenant
+ exact I.1 profile_id
+ captured I.1 profile_sequence
+ captured I.1 profile_record_fingerprint
+ persistent OrganizationPosition
+ capability
+ context scope
+ current autonomy level
+ exactly-next autonomy level
+ I.1 evidence-policy version
```

`profile_id` is the canonical profile-scope key. Profile sequence and profile fingerprint are integrity witnesses.

The target must be exactly one A-level above the current profile level and must remain at or below the profile's current Board ceiling.

A later I.1 supersession creates a new exact profile scope. The old I.3 policy remains historical for the old immutable profile but cannot become the new profile's current eligibility policy, even when autonomy level and evidence-policy version remain unchanged.

## 4. Durable policy truth

I.3 adds one append-only canonical model:

```text
CapabilityAutonomyPromotionPolicy
```

The policy records:

```text
exact I.1 profile identity / sequence / fingerprint
position / capability / context
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

Rate thresholds must be finite values in `[0,1]`. `NaN`, positive infinity and negative infinity are invalid.

There is deliberately no I.3 HTTP policy-write route.

## 6. Board Activity classification

I.3 follows the repository's existing physical/constitutional Activity separation.

Accepted representation:

```text
OrganizationActivity.activity_class = decision
payload.constitutional_activity_class = AUTHORITY
```

The Activity payload freezes:

```text
contract version
governance source = human_board
exact profile id / sequence / fingerprint
policy sequence
from/target autonomy levels
evidence-policy version
criteria
policy reason
autonomy_mutated = false
```

The read validator checks both the physical `decision` class and constitutional `AUTHORITY` marker, plus exact source/profile/policy identities and Activity fingerprint/supersession continuity.

## 7. Append-only policy lineage

Policy revisions are immutable.

For one exact I.1 profile:

```text
v1 → v2 → v3
```

Each new revision explicitly supersedes the current revision. One predecessor cannot fork into multiple successors.

Required protections:

```text
unique tenant + idempotency key
unique tenant + exact profile + policy sequence
unique tenant + supersedes policy id
composite tenant/profile foreign key
composite tenant/decision-Activity foreign key
expected_policy_sequence for supersession
PostgreSQL current-policy locking where available
semantic policy fingerprint
captured profile fingerprint
Board decision Activity fingerprint continuity
```

Exact idempotent replay resolves the original immutable policy. Divergent reuse fails closed.

## 8. Deterministic eligibility projection

I.3 computes an `AutonomyPromotionEligibilitySnapshot`; it does not persist a second mutable recommendation truth.

The evaluator validates:

1. I.1 canonical profile integrity;
2. I.2 exact-profile evidence integrity;
3. current exact-profile I.3 policy lineage/integrity;
4. policy profile ID/sequence/fingerprint exactly match current I.1 profile;
5. current autonomy matches policy `from` level;
6. policy evidence version matches current I.1/I.2 evidence version;
7. target remains within the current Board ceiling.

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

## 9. Eligibility states

The bounded deterministic result is:

```text
ELIGIBLE
INSUFFICIENT_EVIDENCE
HOLD
```

Meaning:

- `ELIGIBLE` — all minimum sample requirements and all quality criteria pass;
- `INSUFFICIENT_EVIDENCE` — no known quality blocker fails, but required evidence/review/recovery sample volume or defined-rate evidence is not yet sufficient;
- `HOLD` — at least one evaluable quality/safety criterion fails.

A known quality/safety failure dominates an insufficient sample and therefore returns `HOLD`.

`ELIGIBLE` means only that current validated I.2 evidence satisfies current exact-profile Board criteria. It does not change autonomy.

## 10. Criteria semantics

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
target autonomy rank <= current Board-ceiling rank
```

I.2 denominator semantics remain canonical. I.3 does not recalculate rates from a different denominator contract.

## 11. Transparency

Board/Cockpit receives a read-only view under the existing autonomy transparency namespace:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/promotion-eligibility?context_scope=...
```

The view exposes:

```text
current I.1 profile identity/sequence/autonomy/Board ceiling
current I.2 evidence profile and metrics
current I.3 policy identity/sequence/from/target/version
eligibility state
criterion-by-criterion evidence
```

It does not expose raw policy Activity payload JSON and provides no policy/autonomy mutation route.

## 12. Migration shape

I.3 adds exactly one application table through the existing linear Alembic lineage:

```text
0079_capability_autonomy_evidence_profile_foundation
→ 0080_capability_autonomy_promotion_policy_foundation
```

Accepted registered application-table count:

```text
123
```

No second migration head is permitted.

Migration `0080` was corrected in place before acceptance because its earlier shape had never been accepted or integrated as a production baseline.

## 13. Accepted tests and proof

Acceptance includes:

- Board-only policy establishment;
- non-Board/non-human writer refusal;
- exact one-step promotion requirement;
- target-above-Board-ceiling refusal;
- evidence-policy-version match;
- finite threshold/range validation including `NaN` and infinities;
- exact idempotent replay;
- divergent idempotency conflict;
- append-only policy supersession;
- stale expected policy sequence rejection;
- physical `decision` + constitutional `AUTHORITY` Activity classification;
- constitutional Activity payload drift failure;
- exact-boundary `ELIGIBLE` behavior;
- `INSUFFICIENT_EVIDENCE` behavior for sample/undefined-rate deficits;
- deterministic `HOLD` for quality/safety failure;
- quality failure dominating sample deficit;
- exact recovery-success boundary behavior;
- same-level I.1 supersession invalidating old policy applicability;
- Board-ceiling reduction after supersession requiring a new compatible policy;
- policy Activity fingerprint drift fails closed;
- policy semantic fingerprint drift fails closed;
- I.2 evidence drift fails closed through I.3;
- Board-only read API;
- no policy/autonomy HTTP write route;
- evaluation does not mutate I.1 autonomy truth;
- fresh migration head `0080` and 123-table schema;
- real PostgreSQL competing initial policy and stale-supersession protection;
- full exact-candidate V12 Production Proof.

Accepted technical candidate:

```text
77b2e9adb30d69419158930b31c0bc10515cb6a7
```

Accepted GitHub Production Proof:

```text
32536826352 — 4 / 4 jobs PASS
```

Backend SQLite result:

```text
1158 passed / 15 skipped / 1 warning / 0 failed
```

PostgreSQL governed/autonomy result:

```text
98 passed / 1 warning / 0 failed
```

## 14. Deferred prerequisites before executable autonomy mutation

I.3 is accepted as a **non-authorizing** eligibility foundation. It deliberately does not claim that current I.2 evidence is sufficient for automatic/executable autonomy promotion.

Before any autonomy-changing increment may consume `ELIGIBLE`, a later bounded foundation must address at least:

```text
typed / source-qualified performance evidence
canonical derivation or explicit authoritative attestation provenance
temporal evaluation boundary / evidence aging semantics
minimum recent evidence contract
bounded/paginated operational transparency projection
```

Current limitations retained explicitly:

- I.2 trusted writers attest measurement facts rather than deterministically deriving every field from typed domain records;
- `freshness_compliant` is frozen per observation and there is no accepted rolling-window or maximum-age policy;
- current-profile evidence is materialized into the read projection and I.3 nests that projection;
- I.2 observation indexes are not yet query-driven/operational-scale tuned.

These do not grant authority and therefore do not invalidate I.3 eligibility-policy correctness. They do block skipping directly to an executable autonomy-change mechanism.

## 15. Explicit non-claims

I.3 does not claim or implement:

- automatic promotion;
- automatic downgrade/demotion;
- autonomy mutation;
- an autonomy-change command;
- a Dynamic Autonomy Manager;
- recovery-based automatic restoration;
- autonomy-change lineage after an actual level change;
- Human override execution semantics;
- typed deterministic derivation of every I.2 observation field;
- accepted rolling-window / maximum-age promotion evidence policy;
- accepted minimum-recent-execution policy;
- operational-scale paginated evidence transparency;
- final optimized I.2 index layout;
- provider/model-specific autonomy grants;
- agent self-promotion;
- a universal organization-wide promotion threshold;
- a single aggregate promotion score;
- replacement of Board ceilings;
- replacement of the Command Gateway;
- weakening of legal/professional/Human review floors.

Those remain later bounded Earned Autonomy increments and require separate contracts and proof.

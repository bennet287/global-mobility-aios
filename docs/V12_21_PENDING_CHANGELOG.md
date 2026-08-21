# V12.21 Acceptance Changelog — V1.3-I.2 Shadow Autonomy Evidence Profile Foundation

**Date:** 2026-08-22
**Branch:** `roadmap/global-mobility-aios-v12`
**Status:** ACCEPTED / COMPLETE / PASS / SEALED
**Accepted technical candidate:** `c23e64a95770b1736ac9921486f8d017d17f930b`
**Accepted Production Proof:** GitHub Actions run `32533230630`
**Acceptance record:** `docs/V1_3_I2_SHADOW_AUTONOMY_EVIDENCE_PROFILE_ACCEPTANCE_2026-08-22.md`

This file retains its historical `PENDING_CHANGELOG` filename for continuity, but the I.2 delivery recorded here is now closed and accepted. The full code/runtime proof applies to the exact technical candidate above; later acceptance-documentation commits reconcile repository truth without pretending the full code suite reran on those docs-only SHAs.

## Implementation lineage

```text
dd6e9a93d37c24ebb637aa3b41bbb9c4914da9ce  docs: define I.2 shadow autonomy evidence profile foundation
8b851899b3d7ca3656fe4bf7ebb95c965a5ae2ea  feat: add I.2 shadow autonomy evidence profile foundation
c54fd100c9392248e6290ea56069b49dad908f82  feat: register I.2 autonomy evidence observations
32e5a26a7e45ca3ed06edae3555d8b3ee30293d5  feat: expose Board I.2 autonomy evidence profile read
8962290b8a60e68772b6781e09e74b6af230f727  test: fix I.2 canonical activity timestamps
cc509a9d9c2aaf6734f29569d8ad9f2274337476  test: advance fresh migration head to I.2
dc828bd5c5e4d54e95ad792308f40ea7a6d9b97a  test: advance organization migration boundary to I.2
9de51be193f023e887ecc59f1a425003fd19be37  test: add I.2 PostgreSQL observation race contract
12a2c2288a0291ae108638381c82fe5251bd2836  docs: mark I.2 shadow evidence implementation acceptance pending
7f15bb8c13098694e6b2c194261c09377e8016ee  docs: fix V12.21 changelog diff hygiene
c23e64a95770b1736ac9921486f8d017d17f930b  fix: bound I.2 PostgreSQL index identifiers
50a11765c5029ed00ddc3a10e65a0f7b3f5c4d23  docs: seal V1.3 I.2 shadow autonomy evidence profile foundation
```

## Canonical I.2 scope

I.2 is a **shadow / measurement-only foundation**. It implements the architecture requirement that earned autonomy begin with demonstrated performance evidence before any promotion/downgrade policy exists.

The canonical measurement scope is frozen to:

```text
tenant
+ persistent OrganizationPosition
+ capability
+ context scope
+ exact I.1 profile revision
+ evidence-policy version
```

No organization-wide autonomy score is introduced.

## Durable observation model

I.2 adds exactly one bounded append-only model:

```text
CapabilityAutonomyEvidenceObservation
```

Each row records one qualifying execution/evaluation unit and freezes:

```text
exact I.1 profile identity/scope
canonical OrganizationActivity identity
source Activity fingerprint
human review outcome
evidence-grounded flag
verifier-contradiction flag
policy-compliance flag
freshness-compliance flag
critical-error flag
recovery outcome
SLA outcome
incident count
trusted writer actor type/key
idempotency key
semantic record fingerprint
```

The observation table is immutable after commit. There is no mutable aggregate score/counter table.

## Trusted writer boundary

The canonical observation command is HTTP-independent and accepts only:

```text
HUMAN   authenticated admin + persistent Board position
SYSTEM  trusted server-side system identity with admin/operator role
```

It rejects AGENT, WORKER and EXTERNAL_HUMAN self-grading.

The SYSTEM path is trusted AIOS measurement provenance, not provider/model self-report and not an authority grant.

There is deliberately no I.2 POST/PUT/PATCH/DELETE HTTP route.

## Replay / integrity / concurrency

The accepted implementation protects:

```text
unique tenant + idempotency_key
unique tenant + exact profile + source Activity
composite tenant/profile foreign key
composite tenant/source-Activity foreign key
captured source Activity fingerprint
semantic observation fingerprint
```

Exact idempotent replay returns the already-durable observation, including after the I.1 profile later becomes historical.

New observations require the target I.1 profile to remain the validated current profile. Historical exact replay remains available, but new historical-profile backfill is rejected.

The Board read model fails closed on:

```text
I.1 profile integrity failure
profile/scope drift
position identity drift
source Activity disappearance/tenant mismatch
source Activity fingerprint drift
observation record-fingerprint drift
duplicate source counting
```

## Deterministic `AutonomyEvidenceProfile` projection

The evidence profile is computed from immutable observations, not persisted as a second authority record.

It derives:

```text
qualifying execution volume
evidence grounding count/rate
human accepted/modified/rejected/not-reviewed counts
human acceptance/modification/rejection rates
verifier contradiction count/rate
policy compliance count/rate
freshness compliance count/rate
critical error count/rate
recovery applicable/succeeded/failed counts
recovery success rate
SLA met count/rate
incident count
```

Rate denominators are explicit:

- general rates → qualifying execution volume;
- human outcome rates → accepted + modified + rejected only;
- recovery success rate → succeeded + failed only;
- zero denominator → `null`.

No caller-supplied percentage or permission score is persisted.

## Board / Cockpit transparency

The existing Board-only transparency facade now includes:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/evidence?context_scope=...
```

The response exposes current I.1 profile context, deterministic measurement counts/rates and append-only observation provenance without raw Activity payload JSON.

The route is read-only and does not create an autonomy mutation path.

## Migration / schema

The controlled Alembic lineage advances:

```text
0078_capability_autonomy_profile_foundation
→ 0079_capability_autonomy_evidence_profile_foundation
```

I.2 adds exactly one registered application table:

```text
capability_autonomy_evidence_observations
```

Accepted application-table count:

```text
122
```

Fresh SQLite and PostgreSQL migration/physical-schema proof both verified `0079_capability_autonomy_evidence_profile_foundation`, 122 registered application tables and matching physical schema.

### PostgreSQL identifier-length diagnostic and repair

The first exact I.2 PostgreSQL migration attempt reached `0079` but failed before schema verification because an explicitly constructed index name exceeded PostgreSQL's 63-character identifier limit. SQLite accepted the same identifier, so this was a real cross-dialect migration defect rather than an I.2 measurement-policy issue.

The repair in `c23e64a95770b1736ac9921486f8d017d17f930b` replaces the seven overlength automatic-style index names with bounded explicit names in both SQLModel metadata and migration `0079`. No columns, constraints, uniqueness, foreign keys, measurement semantics, authority boundaries or autonomy behavior changed.

The repaired exact candidate then migrated a fresh PostgreSQL 16 database through `0079` and passed physical-schema verification before the governed PostgreSQL contract suite executed.

## Accepted Production Proof

The exact technical candidate `c23e64a95770b1736ac9921486f8d017d17f930b` passed GitHub Actions run `32533230630` across all four required lanes:

```text
Repository policy and constraints        PASS
Backend regression (SQLite)              PASS
Frontend tests, types and build          PASS
PostgreSQL governance contracts          PASS
```

All jobs explicitly checked out the exact accepted candidate SHA.

Accepted backend evidence:

```text
Python                                    3.12.14
full SQLite regression                    1147 passed / 13 skipped / 1 warning / 0 failed
Alembic SQLite                            0001 -> 0079 PASS
migration head                            0079_capability_autonomy_evidence_profile_foundation
registered SQLModel tables                122
physical schema                           PASS
local schema contract                     PASS — 122 actual application tables / 123 physical including alembic_version
```

Accepted PostgreSQL evidence:

```text
PostgreSQL                                16
Alembic PostgreSQL                        0001 -> 0079 PASS
migration head                            0079_capability_autonomy_evidence_profile_foundation
registered SQLModel tables                122
physical schema                           PASS
governed eligibility/autonomy suite       96 passed / 1 warning / 0 failed
concurrent same-profile/same-source race  PASS
```

Accepted frontend/repository evidence:

```text
Node                                      24
npm install/audit                         PASS — 0 vulnerabilities
design foundation                         PASS — 28/28
request/auth                              PASS — 4/4
TypeScript                                PASS
Next.js 16.3.1 production build           PASS
compiled auth                             PASS
repository policy                         PASS
release consistency                       PASS — 0079
Python dependency constraints             PASS
diff hygiene                              PASS
```

The known Pydantic `model_metadata_json` protected-namespace warning remains visible and non-blocking.

The duplicate-key message visible in the PostgreSQL service log during the adversarial race is expected rejected-writer behavior exercised by the concurrency contract; the governed pytest lane itself passed 96/96 tests.

## Accepted test surface

Acceptance includes contract coverage for:

- Human Board observation establishment;
- trusted SYSTEM observation establishment;
- AGENT self-grading refusal;
- foreign-tenant source refusal;
- exact idempotent replay;
- divergent idempotency failure;
- duplicate source exclusion;
- deterministic denominator-aware counts/rates;
- profile-revision separation;
- current-profile-only new observation rule;
- historical exact replay;
- source Activity fingerprint drift;
- observation semantic fingerprint drift;
- Board-only evidence-profile read;
- absence of an HTTP evidence write route;
- no mutation of I.1 autonomy/Board-ceiling truth;
- fresh migration head `0079`;
- organization architecture ceiling `0079`;
- real PostgreSQL concurrent same-profile/same-source observation exclusion.

## Explicit non-claims

I.2 does not claim:

- automatic autonomy promotion;
- automatic autonomy downgrade;
- promotion eligibility or recommendation;
- promotion or downgrade thresholds;
- a Dynamic Autonomy Manager;
- agent self-grading or self-promotion as permission;
- provider/model-specific autonomy grants;
- provider/model self-report as canonical performance evidence;
- a single organization-wide autonomy score;
- confidence or score as permission;
- replacement of the I.1 Board ceiling;
- replacement of the Command Gateway;
- weakening of Human/Board/legal/professional review floors;
- completion of the wider Earned Autonomy stage;
- completion of the future Organizational Immune System.

The accepted V1.3 baseline is now I.2. The acceptance record is `docs/V1_3_I2_SHADOW_AUTONOMY_EVIDENCE_PROFILE_ACCEPTANCE_2026-08-22.md`, anchored to exact technical candidate `c23e64a95770b1736ac9921486f8d017d17f930b` and Production Proof run `32533230630`.

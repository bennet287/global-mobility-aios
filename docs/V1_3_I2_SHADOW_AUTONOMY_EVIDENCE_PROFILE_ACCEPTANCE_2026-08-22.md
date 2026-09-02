# Global Mobility AIOS — V1.3 I.2 Acceptance Record — 2026-08-22

**Stage:** V1.3-I.2 — Shadow Autonomy Evidence Profile Foundation
**Status:** ACCEPTED / COMPLETE / PASS / SEALED
**Accepted technical candidate:** `c23e64a95770b1736ac9921486f8d017d17f930b`
**Accepted Production Proof:** GitHub Actions run `32533230630`
**Parent accepted checkpoint:** V1.3-I.1 — `581df5d99b65f0a7a49ace228ee707b881d508fa`
**Parent Production Proof:** run `32529241957`
**Accepted migration head:** `0079_capability_autonomy_evidence_profile_foundation`
**Accepted registered application tables:** 122

## 1. Acceptance decision

V1.3-I.2 is accepted and sealed on technical candidate `c23e64a95770b1736ac9921486f8d017d17f930b`.

I.2 establishes the canonical **shadow / measurement-only** evidence foundation required before any later earned-autonomy promotion or downgrade policy may be designed.

Permanent doctrine remains:

```text
Memory ≠ Truth
Capability ≠ Authority ≠ Autonomy ≠ Risk
Human Owner / Board remains supreme authority
Agents cannot self-promote
Scores and confidence do not create permission
Immune System may restrict; it does not grant authority
```

I.2 measures demonstrated performance. It does not convert measurement into permission.

## 2. Accepted canonical observation model

I.2 adds exactly one bounded append-only model:

```text
CapabilityAutonomyEvidenceObservation
```

Every accepted observation is frozen to one exact I.1 autonomy profile and therefore to:

```text
tenant
+ persistent OrganizationPosition
+ capability
+ context scope
+ profile sequence
+ evidence-policy version
```

Each observation durably records:

```text
canonical I.1 profile identity
canonical OrganizationActivity source identity
captured source Activity fingerprint
human review outcome
evidence-grounded result
verifier contradiction result
policy-compliance result
freshness-compliance result
critical-error result
recovery outcome
SLA outcome
incident count
trusted writer actor type/key
idempotency key
semantic record fingerprint
```

The observation is immutable after commit. I.2 introduces no mutable aggregate score table and no organization-wide autonomy score.

## 3. Accepted trusted-writer boundary

The canonical observation writer is internal and HTTP-independent.

Accepted writer classes are:

```text
HUMAN   authenticated admin + persistent Board position
SYSTEM  trusted server-side AIOS measurement identity with admin/operator role
```

The following actor classes cannot establish canonical I.2 evidence:

```text
AGENT
WORKER
EXTERNAL_HUMAN
```

An agent therefore cannot self-grade success, quality, compliance, acceptance, recovery or incident history into permission evidence.

The SYSTEM path is trusted AIOS measurement provenance. It is not provider/model self-report and does not create authority.

## 4. Accepted replay, integrity and concurrency contract

I.2 accepts the following durable protections:

```text
unique tenant + idempotency_key
unique tenant + exact profile + source Activity
composite tenant/profile foreign key
composite tenant/source-Activity foreign key
captured source Activity fingerprint
semantic observation fingerprint
```

Exact idempotent replay returns the already-durable canonical observation.

Divergent reuse of an idempotency key fails closed.

A source Activity cannot be counted twice for one exact I.1 profile.

New observations may attach only to the validated current I.1 profile. Already-durable historical observations remain exactly replayable after later I.1 supersession, but new historical-profile backfill is rejected.

The real PostgreSQL concurrency contract proves that two cross-session writers racing to count the same source Activity for the same profile produce exactly one canonical observation; the competing write is rejected without duplicate measurement truth.

## 5. Accepted deterministic `AutonomyEvidenceProfile` projection

`AutonomyEvidenceProfile` is accepted as a computed read projection over immutable observations, not as a second authority or mutable score record.

The projection derives:

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

Accepted denominator rules are explicit:

- general rates use qualifying execution volume;
- human acceptance/modification/rejection rates use only `accepted + modified + rejected`;
- `not_reviewed` is excluded from human-outcome rate denominators;
- recovery success rate uses only `succeeded + failed`;
- a zero denominator produces `null`, never a fabricated zero or one.

No caller-supplied percentage or permission score is persisted.

## 6. Accepted Board / Cockpit transparency

The accepted Board-only read surface is:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/evidence?context_scope=...
```

The response exposes:

- the exact current I.1 profile context;
- current autonomy level and Board ceiling for context only;
- evidence-policy version;
- deterministic measurement counts/rates;
- append-only observation provenance with source Activity IDs/fingerprints.

Raw Activity payload JSON is not exposed.

There is no I.2 POST/PUT/PATCH/DELETE HTTP route.

## 7. Accepted integrity behavior

Before returning a measurement profile, I.2 validates:

```text
I.1 current-profile integrity
observation tenant/profile/scope continuity
profile sequence continuity
evidence-policy continuity
position identity continuity
source Activity existence and tenant continuity
source Activity fingerprint continuity
observation semantic record fingerprint integrity
duplicate-source exclusion
```

Any mismatch fails closed rather than returning a partial or silently altered measurement profile.

## 8. Accepted autonomy non-effect

I.2 observation establishment and evidence-profile reads do not mutate:

```text
CapabilityAutonomyProfile.autonomy_level
CapabilityAutonomyProfile.board_ceiling_level
CapabilityAutonomyProfile.authority_requirement
CapabilityAutonomyProfile.risk_ceiling
CapabilityAuthority
Command Gateway decisions
Human / Board / legal / professional review floors
```

A perfect I.2 evidence profile grants nothing automatically.

A poor I.2 evidence profile changes nothing automatically.

Promotion and downgrade policy remain outside I.2.

## 9. Migration and schema acceptance

The accepted controlled Alembic lineage is:

```text
0078_capability_autonomy_profile_foundation
→ 0079_capability_autonomy_evidence_profile_foundation
```

I.2 adds exactly one registered application table:

```text
capability_autonomy_evidence_observations
```

Accepted schema evidence on exact candidate `c23e64a95770b1736ac9921486f8d017d17f930b`:

```text
SQLite migration head                         0079_capability_autonomy_evidence_profile_foundation
SQLite registered application tables          122
SQLite actual application tables              122
SQLite physical tables                        123 including alembic_version
SQLite physical schema                        PASS

PostgreSQL 16 migration head                  0079_capability_autonomy_evidence_profile_foundation
PostgreSQL registered application tables      122
PostgreSQL physical schema                    PASS
```

No independent Alembic head was introduced.

## 10. PostgreSQL identifier-length diagnostic and repair

The first I.2 exact-candidate PostgreSQL attempt reached migration `0079` but failed before schema verification because an explicitly constructed observation index name exceeded PostgreSQL's 63-character identifier limit.

SQLite accepted the same identifier, so this exposed a genuine cross-dialect DDL portability defect.

The accepted technical candidate includes commit:

```text
c23e64a95770b1736ac9921486f8d017d17f930b  fix: bound I.2 PostgreSQL index identifiers
```

The repair replaces the seven overlength automatic-style names with bounded explicit names in both SQLModel metadata and migration `0079`.

No columns, constraints, uniqueness, foreign keys, measurement semantics, authority boundaries or autonomy behavior changed.

The exact repaired candidate subsequently migrated a fresh PostgreSQL 16 database through `0079` and passed physical-schema verification.

## 11. Exact-candidate Production Proof

GitHub Actions run `32533230630` checked out exact technical candidate:

```text
c23e64a95770b1736ac9921486f8d017d17f930b
```

The accepted proof ran on Python 3.12.14 for backend/PostgreSQL lanes and Node 24.19.0 for the frontend lane.

Accepted results:

```text
Repository policy and constraints             PASS
Release consistency                           PASS — 0079
Python dependency constraints                 PASS
Diff hygiene                                  PASS

Backend regression (SQLite)                   1147 passed / 13 skipped / 1 warning / 0 failed
SQLite migration consistency                  PASS — 0079
SQLite registered tables                      122
SQLite physical schema                        PASS
SQLite local schema contract                  PASS

Frontend npm ci                               PASS
Frontend high-severity audit                  PASS — 0 vulnerabilities
Frontend design foundation                    28 / 28 PASS
Frontend request/auth                         4 / 4 PASS
Frontend TypeScript                           PASS
Frontend Next.js 16.3.1 production build      PASS
Frontend compiled-auth verification           PASS

PostgreSQL 16 Alembic                         PASS — 0001 → 0079
PostgreSQL migration/schema contract           PASS
PostgreSQL registered tables                  122
PostgreSQL governed suite                     96 passed / 1 warning / 0 failed
I.2 concurrent same-source exclusion          PASS

V12 Production Proof run 32533230630          4 / 4 jobs PASS
```

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

## 12. Acceptance invariants proven

I.2 acceptance establishes that:

1. Human Board/admin context can establish canonical observations;
2. trusted server SYSTEM measurement context can establish canonical observations;
3. agents cannot self-grade canonical autonomy evidence;
4. foreign-tenant source Activities fail closed;
5. observations remain frozen to one exact I.1 profile scope;
6. exact replay is deterministic;
7. divergent idempotency reuse fails closed;
8. one source Activity cannot be double-counted for one profile;
9. deterministic counts and denominator-aware rates are derived server-side;
10. different I.1 profile revisions do not silently pool measurement evidence;
11. historical exact replay remains available without permitting new historical backfill;
12. source Activity fingerprint drift fails closed;
13. observation semantic fingerprint drift fails closed;
14. Board transparency is read-only and raw payload JSON remains hidden;
15. observation establishment does not mutate I.1 autonomy truth;
16. real PostgreSQL concurrency yields exactly one canonical same-source observation;
17. fresh SQLite and PostgreSQL schema proof is green at `0079` / 122 registered tables;
18. full backend, frontend, repository and PostgreSQL Production Proof is green.

## 13. Explicit non-claims

I.2 acceptance does **not** claim:

- automatic autonomy promotion;
- automatic autonomy downgrade;
- promotion eligibility or promotion recommendation;
- promotion thresholds;
- downgrade thresholds driven by I.2 measurement alone;
- a Dynamic Autonomy Manager;
- agent self-grading or self-promotion as permission;
- provider/model self-report as canonical performance evidence;
- provider/model-specific autonomy grants;
- a single organization-wide autonomy score;
- confidence or score as permission;
- replacement of the I.1 Board ceiling;
- replacement of the Command Gateway;
- weakening of Human/Board/legal/professional review floors;
- completion of the wider Earned Autonomy stage;
- completion of the future Organizational Immune System;
- production-scale operational readiness.

## 14. Seal

V1.3-I.2 is **COMPLETE / PASS / SEALED** on technical candidate `c23e64a95770b1736ac9921486f8d017d17f930b`, proven by GitHub Actions run `32533230630`.

The next I-stage increment, if pursued, must define its own bounded policy contract and proof. I.2 evidence is a prerequisite for later earned-autonomy policy; it is not that policy itself.

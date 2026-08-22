# V12.22 Acceptance Changelog — V1.3-I.3 Autonomy Promotion Eligibility Policy Foundation

**Date:** 2026-08-22
**Branch:** `roadmap/global-mobility-aios-v12`
**Status:** ACCEPTED / COMPLETE / PASS / SEALED
**Accepted technical candidate:** `77b2e9adb30d69419158930b31c0bc10515cb6a7`
**Accepted Production Proof:** GitHub Actions run `32536826352`
**Post-acceptance profile-precondition hardening:** ACCEPTED / PASS / SEALED on `108231d75b4c7413c1759c003e121fdcca206d7c`, run `32539026789`
**Parent accepted checkpoint:** I.2 — `c23e64a95770b1736ac9921486f8d017d17f930b`, run `32533230630`

This historical filename remains `V12_22_PENDING_CHANGELOG.md`, matching prior V12 convention, but its contents are now closed as the V12.22 I.3 acceptance changelog.

## Accepted scope

I.3 adds Board-authored, append-only, exact-profile promotion criteria and a deterministic non-authorizing eligibility projection over accepted I.1 + I.2 truth.

Canonical separation remains:

```text
promotion eligibility ≠ promotion approval ≠ autonomy mutation ≠ authority grant
```

## Implementation accepted

I.3 adds:

- `CapabilityAutonomyPromotionPolicy` as one append-only policy table;
- exact binding to immutable I.1 `profile_id`, captured `profile_sequence` and `profile_record_fingerprint`;
- composite tenant/profile foreign-key integrity;
- denormalized position/capability/context/from-level/evidence-version continuity checks against the bound profile;
- Board-only internal policy establishment;
- exactly-one-level promotion target constrained by the I.1 Board ceiling;
- exact idempotent replay and divergent-idempotency rejection;
- expected policy-sequence supersession protection;
- PostgreSQL current-policy locking plus database uniqueness backstops;
- physical `OrganizationActivity.activity_class = decision` with constitutional `AUTHORITY` classification in the immutable payload;
- Board decision Activity identity/fingerprint and supersession validation;
- finite rate-threshold validation rejecting `NaN` and infinities;
- deterministic `ELIGIBLE`, `INSUFFICIENT_EVIDENCE`, `HOLD` evaluation;
- explicit criterion-by-criterion required/observed/evaluable/pass state;
- no weighted aggregate permission score;
- read-only Board transparency at `/api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/promotion-eligibility?context_scope=...`;
- no I.3 HTTP policy-write or autonomy-write route;
- no mutation of I.1 autonomy truth during eligibility evaluation.

## Critical diagnostic defects and repair

The pre-acceptance candidate `07260260a442418589f76e3df154a35bb2557e96` was correctly left unaccepted.

Exact GitHub backend regression on that candidate produced:

```text
7 failed / 1146 passed / 15 skipped / 1 warning
```

Three real defects were identified:

1. the I.3 writer attempted physical `activity_class="authority"`, but `OrganizationActivityClass` has no such enum member;
2. policy scope used autonomy level/evidence-policy strings rather than the exact I.1 profile revision, allowing stale policy reuse after same-level profile supersession;
3. the platform-hardening router registry count remained 66 after I.3 registered the 67th router feature.

Repair commit:

```text
77b2e9adb30d69419158930b31c0bc10515cb6a7  fix: bind I.3 policy to exact autonomy profile
```

The accepted physical/constitutional Activity pattern is now:

```text
activity_class = decision
payload.constitutional_activity_class = AUTHORITY
```

A same-level I.1 supersession creates a new policy scope. The old policy remains historically inspectable for its original profile but is not reused for the new current profile.

Migration `0080` was corrected in place because no prior `0080` shape had been accepted/sealed.

## Criteria represented

The accepted Board policy can define:

```text
minimum qualifying execution volume
minimum human-reviewed sample
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
```

I.2 denominator semantics remain canonical. I.3 does not invent alternate denominators.

## Accepted adversarial proof surface

Focused proof now includes:

- Board-only establishment and non-human refusal;
- exact one-step promotion and Board-ceiling protection;
- evidence-policy version matching;
- finite-rate/range validation including `NaN` and positive/negative infinity;
- idempotent replay/divergent conflict;
- append-only supersession/stale sequence rejection;
- physical `decision` + constitutional `AUTHORITY` Activity validation;
- constitutional Activity payload drift failure;
- policy Activity fingerprint drift failure;
- policy semantic-fingerprint drift failure;
- `INSUFFICIENT_EVIDENCE`, exact-boundary `ELIGIBLE`, and quality-failure `HOLD`;
- quality failure dominating sample deficit;
- exact recovery-success boundary behavior;
- no I.1 autonomy mutation;
- same-level I.1 supersession invalidating old policy applicability;
- same-level Board-ceiling reduction requiring a new compatible policy;
- I.2 observation drift detected through I.3;
- Board-only GET and no HTTP mutation route;
- platform router registry 67-feature hardening.

The original governed PostgreSQL I.3 lane proves:

- competing initial policy writers do not fork exact-profile canonical policy truth;
- stale cross-session policy supersession is rejected.

## Post-acceptance profile-precondition hardening

A later adversarial review identified a narrower command-success race that did not permit stale policy reuse but could allow a Board command to report success for a profile that became historical during the transaction.

The accepted hardening candidate is:

```text
108231d75b4c7413c1759c003e121fdcca206d7c
```

It adds:

- optional caller `expected_profile_id` optimistic precondition;
- exact current I.1 profile row locking with PostgreSQL `FOR UPDATE` for every new policy write;
- canonical current-profile snapshot revalidation after the profile lock is acquired;
- autonomy/evidence-version/Board-ceiling revalidation under the same profile lock;
- final locked current-profile recheck before atomic policy/audit commit;
- a fast same-level v1 → v2 stale-profile-precondition regression;
- a deterministic PostgreSQL supersession-wins race proving the I.3 writer actually waits on the I.1 profile row lock and rejects stale after v2 becomes current.

The real PostgreSQL race contract proves:

```text
I.1 supersession owns v1 FOR UPDATE lock
→ I.3 writer for expected v1 blocks on that exact row
→ I.1 commits v2
→ I.3 resumes and revalidates
→ stale v1 command is rejected
→ zero policy rows persist for the stale attempt
```

The inverse ordering is also safe by construction: if I.3 owns the current-profile row lock first, I.1 supersession waits until the I.3 transaction completes, so the Board policy was established against a genuinely current profile at the serialization point.

This refinement adds no migration, table, HTTP write route, authority grant, Board-ceiling change or autonomy mutation.

## Migration / schema acceptance

Accepted linear migration:

```text
0079_capability_autonomy_evidence_profile_foundation
→ 0080_capability_autonomy_promotion_policy_foundation
```

Accepted registered application-table count:

```text
123
```

Exact-candidate schema proof passed on fresh SQLite and PostgreSQL 16. The post-acceptance profile-precondition hardening does not change schema.

## Exact Production Proof

Original accepted I.3 technical candidate:

```text
77b2e9adb30d69419158930b31c0bc10515cb6a7
```

Original accepted run:

```text
GitHub Actions V12 Production Proof 32536826352
```

Original accepted results:

```text
Repository policy and constraints             PASS
Release consistency                           PASS — 0080
Python dependency constraints                 PASS
Diff hygiene                                  PASS

Backend regression (SQLite)                   1158 passed / 15 skipped / 1 warning / 0 failed
SQLite migration/schema                       PASS
SQLite registered application tables          123

Frontend tests/types/build                    PASS

PostgreSQL 16 migration/schema                PASS — 0001 → 0080
PostgreSQL registered application tables      123
PostgreSQL governed/autonomy suite            98 passed / 1 warning / 0 failed

V12 Production Proof                          4 / 4 jobs PASS
Standalone Repository Policy run 32536826350  PASS
```

Post-acceptance hardening exact candidate and proof:

```text
candidate                                      108231d75b4c7413c1759c003e121fdcca206d7c
run                                            32539026789
Repository policy and constraints              PASS
Release consistency                            PASS — 0080
Python dependency constraints                  PASS
Diff hygiene                                   PASS
Backend regression (SQLite)                    1159 passed / 16 skipped / 1 warning / 0 failed
SQLite registered/actual application tables    123 / 123
SQLite physical schema                         PASS
Frontend tests/types/build                     PASS
PostgreSQL 16 migration/schema                 PASS — 0001 → 0080
PostgreSQL registered application tables       123
PostgreSQL governed/autonomy suite             99 passed / 1 warning / 0 failed
I.3 profile-supersession lock race              PASS
V12 Production Proof                           4 / 4 jobs PASS
Standalone Repository Policy run 32539026838   PASS
```

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains non-blocking and pre-existing.

## Deferred hardening / next-stage prerequisites

The following review concerns were assessed as valid but are **not I.3 correctness blockers** because I.3 does not authorize or mutate autonomy:

1. I.2 measurement facts are trusted Human Board/SYSTEM attestation inputs rather than deterministically derived from typed review/verification/incident/execution records;
2. `freshness_compliant` is frozen per observation and no rolling-window/maximum-age/minimum-recent-execution policy is accepted;
3. I.2 transparency currently materializes all current-profile observations and I.3 nests that projection rather than using bounded aggregate/paginated provenance reads;
4. I.2 has several single-column/low-cardinality indexes that should later be tuned from real query patterns.

These concerns are now explicit sequencing constraints: **the project must not jump directly from I.3 eligibility to executable autonomy mutation.**

Before an actual promotion/demotion command or Dynamic Autonomy Manager is designed, a bounded successor should establish typed/source-qualified evidence and temporal evaluation semantics, plus an operationally bounded Board projection.

Working roadmap boundary:

```text
I.4 — Qualified + Temporal Autonomy Evidence Evaluation Foundation
```

This is future direction, not an accepted implementation.

## Explicit non-claims

I.3 acceptance and its profile-precondition hardening do not claim or implement:

- automatic promotion;
- automatic downgrade/demotion;
- an autonomy-change command;
- a Dynamic Autonomy Manager;
- recovery-based automatic restoration;
- typed deterministic derivation of all I.2 evidence facts;
- accepted rolling-window / maximum-age promotion policy;
- accepted minimum-recent-execution contract;
- operational-scale paginated evidence transparency;
- optimized final I.2 index layout;
- durable autonomy-change lineage after an actual level change;
- Human override execution semantics;
- agent self-promotion;
- provider/model-specific autonomy grants;
- a universal organization-wide promotion threshold;
- a single aggregate promotion score;
- replacement of Board ceilings;
- replacement of the Command Gateway;
- weakening of legal/professional/Human review floors.

## Closure

V1.3-I.3 remains **COMPLETE / PASS / SEALED** on its original technical foundation candidate `77b2e9adb30d69419158930b31c0bc10515cb6a7`, Production Proof run `32536826352`.

The later profile-precondition/concurrency refinement is separately **ACCEPTED / PASS / SEALED** on technical candidate `108231d75b4c7413c1759c003e121fdcca206d7c`, Production Proof run `32539026789`.

The accepted output remains a Board-authored deterministic eligibility signal only. Future autonomy mutation remains NOT STARTED and is gated behind separate evidence-qualification and temporal-evaluation proof.

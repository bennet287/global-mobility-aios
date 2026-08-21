# Global Mobility AIOS — V1.3 I.3 Acceptance Record — 2026-08-22

**Stage:** V1.3-I.3 — Autonomy Promotion Eligibility Policy Foundation
**Status:** ACCEPTED / COMPLETE / PASS / SEALED
**Accepted technical candidate:** `77b2e9adb30d69419158930b31c0bc10515cb6a7`
**Accepted Production Proof:** GitHub Actions run `32536826352`
**Parent accepted checkpoint:** V1.3-I.2 — `c23e64a95770b1736ac9921486f8d017d17f930b`
**Parent Production Proof:** run `32533230630`
**Accepted migration head:** `0080_capability_autonomy_promotion_policy_foundation`
**Accepted registered application tables:** 123

## 1. Acceptance decision

V1.3-I.3 is accepted and sealed on exact technical candidate `77b2e9adb30d69419158930b31c0bc10515cb6a7`.

I.3 establishes a bounded, **non-authorizing** policy/evaluation layer between accepted I.2 measurement and any future autonomy-changing mechanism:

```text
I.1 canonical autonomy truth
→ I.2 immutable shadow evidence profile
→ I.3 Board-authored promotion criteria + deterministic eligibility
→ future evidence-qualification / temporal-evaluation boundary
→ only then may an actual autonomy-change increment be designed
```

Permanent doctrine remains:

```text
Memory ≠ Truth
Capability ≠ Authority ≠ Autonomy ≠ Risk
promotion eligibility ≠ promotion approval ≠ autonomy mutation ≠ authority grant
Human Owner / Board remains supreme authority
agents cannot self-promote
scores and confidence do not create permission
Immune System may restrict; it does not grant authority
```

`ELIGIBLE` means only that current validated evidence satisfies the current exact-profile Board criteria. It grants no permission and changes no autonomy.

## 2. Accepted exact-profile policy scope

The accepted canonical policy is frozen to one exact immutable I.1 profile revision through:

```text
tenant_key
profile_id
profile_sequence
profile_record_fingerprint
position_key
capability_key
context_scope
from_autonomy_level
target_autonomy_level
evidence_policy_version
```

`profile_id` is the canonical durable scope key. `profile_sequence` and `profile_record_fingerprint` are captured integrity witnesses.

A same-level I.1 supersession therefore invalidates the old policy for current eligibility even when the new profile retains the same autonomy level and evidence-policy version. Changes to authority requirement, risk ceiling, Board ceiling or any other profile semantics cannot silently inherit policy from the superseded profile.

Historical policy lineage for the older immutable profile remains inspectable; it is not reused as current policy.

## 3. Accepted Board-authored policy truth

I.3 adds one append-only canonical model:

```text
CapabilityAutonomyPromotionPolicy
```

The internal writer requires:

```text
authenticated HUMAN
+ admin role
+ persistent Board position
+ active target OrganizationPosition
+ validated current I.1 profile
+ from level == current profile autonomy
+ target == exactly one A-level above current
+ target <= current Board ceiling
+ evidence-policy version == current profile evidence-policy version
```

AGENT, WORKER, SYSTEM and EXTERNAL_HUMAN actors cannot establish I.3 promotion criteria.

The policy persists explicit thresholds, not a hidden permission score:

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

All rate thresholds must be finite values in `[0,1]`; `NaN`, positive infinity and negative infinity fail before persistence.

## 4. Accepted Activity classification and constitutional provenance

The first diagnostic I.3 candidate incorrectly attempted to stage:

```text
activity_class = authority
```

`OrganizationActivityClass` has no physical `authority` enum member, so the writer could not create a policy.

The accepted candidate uses the repository's established separation:

```text
physical OrganizationActivity.activity_class = decision
payload.constitutional_activity_class = AUTHORITY
```

The accepted Activity payload additionally freezes:

```text
contract version
governance source = human_board
exact profile id / sequence / fingerprint
policy sequence
autonomy from / target
evidence-policy version
criteria
policy reason
autonomy_mutated = false
```

The read validator fails closed if the physical class, constitutional class, Activity identity, source identity, profile witnesses, policy sequence, supersession link or captured Activity fingerprint drifts.

## 5. Accepted append-only policy lineage

For one exact I.1 profile revision:

```text
policy v1 → policy v2 → policy v3
```

Accepted protections include:

```text
unique tenant + idempotency key
unique tenant + exact profile + policy sequence
unique tenant + supersedes policy id
composite tenant/profile foreign key
composite tenant/decision-Activity foreign key
expected_policy_sequence for supersession
PostgreSQL row locking where applicable
database uniqueness as race backstop
semantic policy fingerprint
captured I.1 profile fingerprint
captured Board decision Activity fingerprint
```

Exact idempotent replay returns the existing immutable policy. Divergent idempotency reuse fails closed. A predecessor cannot fork into two accepted successors.

## 6. Accepted deterministic eligibility projection

I.3 computes `AutonomyPromotionEligibilitySnapshot` rather than persisting a second mutable recommendation truth.

The evaluator validates, in order:

1. current I.1 profile integrity;
2. current I.2 exact-profile evidence integrity;
3. current policy integrity;
4. exact policy profile ID/sequence/fingerprint equals the current I.1 profile;
5. policy `from` autonomy equals current autonomy;
6. evidence-policy versions match;
7. one-step target remains within the current Board ceiling.

It emits every criterion with required value, observed value, comparison, sample/evaluable state and pass/fail result.

Accepted result states are:

```text
ELIGIBLE
INSUFFICIENT_EVIDENCE
HOLD
```

- `ELIGIBLE`: all required sample and quality criteria pass;
- `INSUFFICIENT_EVIDENCE`: no known quality blocker fails but required sample/defined-rate evidence is insufficient;
- `HOLD`: at least one evaluable quality/safety criterion fails.

A quality/safety failure dominates an insufficient sample. Undefined I.2 rates remain unevaluable rather than becoming fabricated zero/one values.

Exact recovery-success boundaries are inclusive according to the declared `>=` policy comparison and are covered by regression proof.

## 7. Accepted Board / Cockpit transparency

The accepted Board-only read surface is:

```text
GET /api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/promotion-eligibility?context_scope=...
```

It exposes current I.1 identity/context, I.2 metrics/evidence profile, current I.3 policy and criterion-by-criterion eligibility.

There is no I.3 POST/PUT/PATCH/DELETE route for policy creation or autonomy mutation.

Raw policy decision Activity payload JSON is not exposed by the transparency response.

## 8. Accepted autonomy non-effect

Policy establishment and eligibility evaluation do not mutate:

```text
CapabilityAutonomyProfile.autonomy_level
CapabilityAutonomyProfile.board_ceiling
CapabilityAutonomyProfile.authority_requirement
CapabilityAutonomyProfile.risk_ceiling
CapabilityAuthority
Command Gateway decisions
Human / Board / legal / professional review floors
```

A perfect I.3 eligibility result grants nothing automatically.

No automatic promotion, downgrade, recovery or autonomy-change command exists in I.3.

## 9. Adversarial defects found before acceptance

The unaccepted pre-repair candidate `07260260a442418589f76e3df154a35bb2557e96` exposed real defects and is retained only as diagnostic history.

Exact GitHub-hosted backend regression on that candidate reported:

```text
7 failed / 1146 passed / 15 skipped / 1 warning
```

The defects were:

1. invalid physical `OrganizationActivityClass('authority')`, breaking all six then-current I.3 tests;
2. policy scope not bound to exact I.1 profile, allowing stale policy reuse after same-level I.1 supersession;
3. router-registry hardening expected 66 routes after I.3 correctly registered route 67.

The accepted repair commit:

```text
77b2e9adb30d69419158930b31c0bc10515cb6a7  fix: bind I.3 policy to exact autonomy profile
```

repairs all three without adding an autonomy mutation path.

Migration `0080` was never accepted in its earlier shape, so it was corrected in place rather than creating an `0081` whose only purpose would be to preserve an unaccepted broken schema.

## 10. Accepted adversarial regression surface

The accepted candidate proves at least:

1. Board-only policy establishment;
2. agent/non-human writer refusal;
3. exact one-step promotion requirement;
4. target-above-Board-ceiling refusal;
5. evidence-policy version match;
6. finite threshold/range validation including `NaN` and infinities;
7. exact idempotent replay and divergent conflict;
8. append-only policy supersession and stale expected sequence rejection;
9. physical `decision` + constitutional `AUTHORITY` Activity classification;
10. constitutional Activity payload drift fails closed;
11. policy decision Activity fingerprint drift fails closed;
12. policy semantic fingerprint drift fails closed;
13. deterministic `ELIGIBLE`, `INSUFFICIENT_EVIDENCE` and `HOLD`;
14. quality failure dominates sample deficit;
15. exact recovery-success boundary behavior;
16. same-level I.1 supersession invalidates old policy applicability;
17. same-level Board-ceiling reduction does not inherit an old A2→A3 policy;
18. I.2 observation semantic drift still fails closed through the I.3 evaluator;
19. Board-only GET transparency and no HTTP mutation route;
20. evaluation does not mutate I.1 autonomy truth;
21. real PostgreSQL competing initial policy writers cannot fork canonical policy truth;
22. real PostgreSQL stale cross-session supersession is rejected.

## 11. Migration and schema acceptance

Accepted linear Alembic lineage:

```text
0079_capability_autonomy_evidence_profile_foundation
→ 0080_capability_autonomy_promotion_policy_foundation
```

I.3 adds exactly one application table:

```text
capability_autonomy_promotion_policies
```

Accepted exact-candidate schema evidence:

```text
SQLite migration head                         0080_capability_autonomy_promotion_policy_foundation
SQLite registered application tables          123
SQLite actual application tables              123
SQLite physical tables                        124 including alembic_version
SQLite physical schema                        PASS

PostgreSQL 16 migration head                  0080_capability_autonomy_promotion_policy_foundation
PostgreSQL registered application tables      123
PostgreSQL physical schema                    PASS
```

No second Alembic head was introduced.

## 12. Exact-candidate Production Proof

GitHub Actions run `32536826352` checked out exact technical candidate:

```text
77b2e9adb30d69419158930b31c0bc10515cb6a7
```

Backend/PostgreSQL used Python 3.12.14.

Accepted results:

```text
Repository policy and constraints             PASS
Release consistency                           PASS — 0080
Python dependency constraints                 PASS
Diff hygiene                                  PASS

Backend regression (SQLite)                   1158 passed / 15 skipped / 1 warning / 0 failed
SQLite migration consistency                  PASS — 0080
SQLite registered tables                      123
SQLite physical schema                        PASS
SQLite local schema contract                  PASS

Frontend npm ci                               PASS
Frontend high-severity audit                  PASS
Frontend design foundation                    PASS
Frontend request/auth                         PASS
Frontend TypeScript                           PASS
Frontend production build                     PASS
Frontend compiled-auth verification           PASS

PostgreSQL 16 Alembic                         PASS — 0001 → 0080
PostgreSQL migration/schema contract           PASS
PostgreSQL registered tables                  123
PostgreSQL governed/autonomy suite            98 passed / 1 warning / 0 failed
I.3 competing initial policy race             PASS
I.3 stale cross-session supersession          PASS

V12 Production Proof run 32536826352          4 / 4 jobs PASS
Standalone Repository Policy run 32536826350  PASS
```

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

## 13. Deferred concerns deliberately not misrepresented as solved

I.3 acceptance does not erase or weaken the following real limitations in the currently accepted I.2/I.3 foundation:

### 13.1 Evidence source qualification

I.2 is a trusted attestation/measurement foundation. Its trusted Human Board or server SYSTEM writer supplies measurement facts against a same-tenant source Activity. The service does not yet derive every measurement field deterministically from typed canonical review, verification, incident and execution records.

This is acceptable for sealed measurement truth and non-authorizing I.3 eligibility. It is **not sufficient for a future automatic or executable autonomy-change mechanism**.

### 13.2 Temporal evidence boundaries

`freshness_compliant` is frozen on each I.2 observation and I.3 currently evaluates the full current-profile evidence set. There is no accepted rolling window, maximum observation age, `evaluation_as_of` policy or minimum-recent-execution threshold.

A future autonomy-changing design must define temporal evidence semantics before consuming I.3 eligibility as an input.

### 13.3 Operational-scale read shape

I.2 currently materializes the current-profile observations for its deterministic projection, and I.3 transparency nests that evidence profile. Database aggregate projection, pagination and bounded provenance response design remain future operational-scale work.

### 13.4 Index tuning

The accepted I.2 observation table retains several individual indexes, including low-cardinality fields. Query-driven composite/index simplification remains a performance-tuning task and was not required to prove I.3 correctness.

These limitations do not grant authority and therefore do not invalidate the bounded I.3 eligibility-policy acceptance. They **do block skipping directly from I.3 to executable autonomy mutation**.

## 14. Next-stage sequencing constraint

Before any actual promotion/demotion command or Dynamic Autonomy Manager is designed, the next bounded I-stage increment must establish at least:

```text
typed / source-qualified performance evidence
canonical derivation or explicit authoritative attestation provenance
temporal evaluation boundary / evidence aging semantics
minimum recent evidence contract
bounded Board/Cockpit evidence projection for operational scale
```

A suitable working boundary is:

```text
I.4 — Qualified + Temporal Autonomy Evidence Evaluation Foundation
```

That name is a roadmap direction, not an accepted implementation.

Only after that layer is separately implemented and proven should the project consider capability-specific promotion/demotion mutation semantics.

## 15. Explicit non-claims

I.3 acceptance does **not** claim:

- automatic autonomy promotion;
- automatic downgrade/demotion;
- any autonomy-change command;
- a Dynamic Autonomy Manager;
- recovery-based automatic autonomy restoration;
- typed deterministic derivation of every I.2 measurement from source-domain records;
- accepted rolling-window / maximum-age evidence policy;
- accepted minimum-recent-execution policy;
- operational-scale paginated autonomy evidence transparency;
- optimized final I.2 index layout;
- provider/model-specific autonomy grants;
- agent self-promotion;
- a universal organization-wide promotion threshold;
- a single aggregate promotion score;
- replacement of Board ceilings;
- replacement of the Command Gateway;
- weakening of legal/professional/Human review floors;
- completion of the wider Earned Autonomy stage;
- production-scale operational readiness.

## 16. Seal

V1.3-I.3 is **COMPLETE / PASS / SEALED** on exact technical candidate `77b2e9adb30d69419158930b31c0bc10515cb6a7`, proven by GitHub Actions run `32536826352`.

The sealed output is a deterministic, exact-profile, Board-authored **eligibility signal only**. It is not permission. Future autonomy-changing work is gated behind a separate qualified/temporal evidence foundation and its own proof.

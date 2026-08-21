# V12.22 Pending Changelog — V1.3-I.3 Autonomy Promotion Eligibility Policy Foundation

**Date:** 2026-08-22
**Branch:** `roadmap/global-mobility-aios-v12`
**Status:** IMPLEMENTED / ACCEPTANCE PENDING
**Last accepted V1.3 checkpoint:** I.2 — technical candidate `c23e64a95770b1736ac9921486f8d017d17f930b`, Production Proof run `32533230630`

This record captures the bounded I.3 implementation state without claiming COMPLETE / PASS / SEALED before an exact I.3 candidate passes the full V12 Production Proof gate.

## Scope

I.3 adds Board-authored, append-only promotion criteria and a deterministic eligibility projection over the accepted I.1 + I.2 truth layers.

Canonical separation remains:

```text
promotion eligibility ≠ promotion approval ≠ autonomy mutation ≠ authority grant
```

## Implementation

I.3 adds:

- `CapabilityAutonomyPromotionPolicy` as one append-only policy table;
- exact scope by tenant + persistent position + capability + context + current autonomy + exactly-next autonomy + evidence-policy version;
- Board-only internal policy establishment;
- exact idempotent replay and divergent-idempotency rejection;
- expected policy-sequence supersession protection;
- bounded PostgreSQL-safe index identifiers from the first `0080` migration;
- Board decision `OrganizationActivity` identity/fingerprint lineage;
- deterministic `ELIGIBLE`, `INSUFFICIENT_EVIDENCE`, `HOLD` evaluation;
- explicit criterion-by-criterion required/observed/pass state;
- no weighted aggregate permission score;
- read-only Board transparency at `/api/v1/organization/transparency/autonomy/profiles/{position_key}/{capability_key}/promotion-eligibility?context_scope=...`;
- no I.3 HTTP policy-write or autonomy-write route;
- no mutation of I.1 autonomy truth during eligibility evaluation.

## Criteria represented

The Board policy can define:

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

## Migration / schema

The implementation advances the single controlled Alembic lineage:

```text
0079_capability_autonomy_evidence_profile_foundation
→ 0080_capability_autonomy_promotion_policy_foundation
```

Expected registered application-table count:

```text
123
```

Fresh SQLite and PostgreSQL migration/schema proof is required before acceptance.

## Test / proof surface

The implementation includes focused SQLite contracts for:

- Board-only establishment;
- exact one-step promotion;
- Board-ceiling protection;
- evidence-policy version matching;
- threshold/range validation;
- idempotent replay/divergent conflict;
- append-only supersession/stale sequence rejection;
- `INSUFFICIENT_EVIDENCE`, exact-boundary `ELIGIBLE`, and safety-failure `HOLD`;
- quality failure dominating sample deficit;
- explicit recovery sample behavior;
- no I.1 autonomy mutation;
- current-profile supersession invalidating old policy applicability;
- decision-Activity fingerprint integrity;
- Board-only GET and no HTTP mutation route.

The governed PostgreSQL lane now includes dedicated I.3 contracts for:

- competing initial policy writers not forking canonical policy truth;
- stale cross-session policy supersession rejection.

## Current proof state

The first diagnostic I.3 runs intentionally began while ROADMAP still declared accepted I.2 migration `0079`; repository release-consistency therefore failed by design. Those runs are diagnostic only and cannot be acceptance evidence.

I.3 acceptance requires a later exact candidate containing:

- migration-boundary reconciliation to `0080`;
- ROADMAP V12.22 pending truth;
- this pending changelog;
- focused I.3 tests;
- full SQLite regression;
- fresh PostgreSQL migration/schema + governed concurrency contracts;
- frontend production proof;
- repository policy/release/dependency/diff-hygiene proof.

## Explicit non-claims

I.3 does not claim or implement:

- automatic promotion;
- automatic downgrade/demotion;
- an autonomy-change command;
- a Dynamic Autonomy Manager;
- recovery-based automatic restoration;
- durable autonomy-change lineage after an actual level change;
- Human override execution semantics;
- agent self-promotion;
- provider/model-specific autonomy grants;
- a universal organization-wide promotion threshold;
- a single aggregate promotion score;
- replacement of Board ceilings;
- replacement of the Command Gateway;
- weakening of legal/professional/Human review floors.

The accepted V1.3 baseline remains I.2 until exact-candidate V12 Production Proof is green and I.3 acceptance is explicitly recorded.

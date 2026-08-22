# V12.23 Acceptance Changelog — V1.3-I.4 Qualified + Temporal Autonomy Evidence Evaluation

**Date:** 2026-08-22
**Status:** COMPLETE / PASS / SEALED
**Historical filename:** `V12_23_PENDING_CHANGELOG.md`
**Technical candidate:** `46727cd130923f4ede825965cea3a011537a930b`
**V12 Production Proof:** `32560318311` — 4/4 jobs PASS
**Standalone Repository Policy:** `32560318310` — PASS

## Scope

V12.23 accepts the bounded V1.3-I.4 prerequisite between sealed I.2/I.3 evidence eligibility and any future autonomy-changing design.

Principle:

> **qualified evidence evaluation ≠ promotion approval ≠ autonomy mutation ≠ authority grant**

## Accepted implementation

- `CapabilityAutonomyEvidenceEvaluationPolicy` append-only Board policy truth.
- Exact immutable I.1 profile binding with profile sequence/fingerprint witnesses.
- Human Board/admin-only policy authoring.
- I.3-hardened current-profile precondition and PostgreSQL serialization with I.1 supersession.
- Explicit observation age, source age and candidate-count bounds.
- Migration `0081_capability_autonomy_evidence_evaluation_policy`.
- 124 registered SQLModel application tables and 125 physical tables including `alembic_version`.
- Qualification adapter v1 for `eligibility.proposal` only.
- Canonical source qualification through the existing E.2 → F.1 → G.1 → G.2 → G.3 eligibility-lineage validator.
- Typed metric derivation instead of trusting raw I.2 quality flags for promotion-grade truth.
- Human review outcomes only from immutable exact-revision `OrganizationHumanAction` records.
- Terminal mapping `approved → accepted`, `requested_changes → modified`, `rejected → rejected`, with no terminal action by `evaluation_as_of` represented as `not_reviewed`.
- Generic `reviewed` and other non-terminal actions do not imply acceptance.
- Explicit unavailable derivations for source-freshness quality, critical errors, recovery, SLA and incidents until later canonical adapters exist.
- Timezone-aware `evaluation_as_of` with deterministic observation/source cutoffs.
- Candidate overflow fails closed; no silent truncation.
- Bounded summary read and stable cursor-paged provenance read.
- Board-only GET transparency for aggregate evaluation and paged provenance.
- No I.4 HTTP mutation route.
- Focused adversarial tests for raw-I.2 disagreement, torn canonical lineage, source-fingerprint drift, ambiguous human review, temporal bounds, candidate overflow, pagination and exact-profile supersession.
- PostgreSQL concurrency contracts for competing initial policy writers, stale policy supersession and I.1 profile-supersession-wins locking.

## Acceptance proof

Exact accepted candidate:

```text
46727cd130923f4ede825965cea3a011537a930b
```

Exact accepted proof:

```text
V12 Production Proof                  32560318311 — 4/4 jobs PASS
Standalone Repository Policy          32560318310 — PASS
SQLite backend regression             1172 passed / 19 skipped / 1 warning / 0 failed
PostgreSQL governed/autonomy suite    102 passed / 1 warning / 0 failed
Alembic                                0001 → 0081 PASS
Registered application tables         124
Physical tables                       125 including alembic_version
Frontend tests/types/build            PASS
Repository policy                     PASS
Release consistency                   PASS — 0081
Python dependency constraints         PASS
Diff hygiene                          PASS
```

The final SQLite repair was test-boundary normalization of ORM-loaded naive timestamps before constructing explicit `evaluation_as_of` values. Production I.4 evaluator semantics remain strict: explicit evaluation timestamps must be timezone-aware.

Canonical acceptance record:

```text
docs/V1_3_I4_QUALIFIED_TEMPORAL_AUTONOMY_EVIDENCE_EVALUATION_ACCEPTANCE_2026-08-22.md
```

## Nonclaims

V12.23 does not implement or authorize:

- automatic promotion;
- automatic demotion/downgrade;
- any autonomy-change command;
- Dynamic Autonomy Manager behavior;
- autonomy-change lineage after a real level change;
- automatic recovery-based autonomy restoration;
- agent self-promotion;
- provider/model-specific autonomy grants;
- confidence/score as permission;
- Board-ceiling or Command-Gateway bypass;
- generic evidence adapters for arbitrary capabilities;
- full typed derivation of every historical I.2 measurement field;
- execution-attributed critical-error/recovery/SLA/incident semantics without typed linkage;
- final query-optimized I.2 index layout;
- production-scale query optimization without measured workload evidence.

## Next gate

V1.3-I.4 is now the latest accepted Earned Autonomy checkpoint.

Actual capability-specific promotion/demotion mutation remains **NOT STARTED**. A future mutation design must separately prove Board-only authority, exact-current-profile serialization, consumption of I.3 policy plus I.4 promotion-grade evidence, Board-ceiling enforcement, append-only autonomy-change lineage, Human override/recovery semantics and no automatic self-promotion.

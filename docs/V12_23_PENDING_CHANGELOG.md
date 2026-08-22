# V12.23 Pending Changelog — V1.3-I.4 Qualified + Temporal Autonomy Evidence Evaluation

**Date:** 2026-08-22  
**Status:** IMPLEMENTED / ACCEPTANCE PENDING

## Scope

V12.23 implements the bounded V1.3-I.4 prerequisite between accepted I.2/I.3 evidence eligibility and any future autonomy-changing design.

Principle:

> **qualified evidence evaluation ≠ promotion approval ≠ autonomy mutation ≠ authority grant**

## Implemented

- `CapabilityAutonomyEvidenceEvaluationPolicy` append-only Board policy truth.
- Exact immutable I.1 profile binding with profile sequence/fingerprint witnesses.
- Human Board/admin-only policy authoring.
- Explicit observation age, source age and candidate-count bounds.
- Migration `0081_capability_autonomy_evidence_evaluation_policy`.
- 124 registered SQLModel application tables expected at the current implementation head.
- Qualification adapter v1 for `eligibility.proposal` only.
- Canonical source qualification through the existing E.2 → F.1 → G.1 → G.2 → G.3 eligibility-lineage validator.
- Typed metric derivation instead of trusting raw I.2 quality flags for promotion-grade truth.
- Human review outcomes only from immutable exact-revision `OrganizationHumanAction` records.
- Explicit unavailable derivations for freshness, critical errors, recovery, SLA and incidents until later canonical adapters exist.
- Timezone-aware `evaluation_as_of` with deterministic observation/source cutoffs.
- Candidate overflow fails closed; no silent truncation.
- Bounded summary provenance and stable cursor-paged provenance.
- Board-only GET transparency for aggregate evaluation and paged provenance.
- No I.4 HTTP mutation route.
- Focused adversarial tests for raw-I.2 disagreement, torn canonical lineage, source-fingerprint drift, ambiguous human review, temporal bounds, candidate overflow, pagination and exact-profile supersession.
- PostgreSQL concurrency contracts for competing initial policy writers, stale policy supersession and I.1 profile-supersession-wins locking.

## Acceptance gate

I.4 is **not accepted or sealed by this file**. Acceptance requires one exact technical candidate with the complete four-lane V12 Production Proof green, including the new I.4 SQLite/API/adversarial tests and PostgreSQL policy-race contracts.

The acceptance record must capture the exact candidate SHA, run ID, backend counts, PostgreSQL counts, migration/schema proof, frontend proof and repository-policy proof.

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
- full typed derivation of every historical I.2 measurement field;
- production-scale query optimization without measured workload evidence.

The last accepted Earned Autonomy checkpoint remains V1.3-I.3 plus its separately sealed profile-precondition hardening until I.4 satisfies its own acceptance gate.

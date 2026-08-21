# Global Mobility AIOS — V1.3-H.1 Eligibility Immune Circuit Foundation

**Date:** 2026-08-20  
**Accepted:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** ACCEPTED / SEALED  
**Production Proof Gate:** ACCEPTED / GREEN  
**Acceptance record:** `docs/V1_3_H1_ACCEPTANCE_2026-08-21.md`  
**H.2:** BLOCKED pending required-check enforcement verification

## Purpose

H.1 begins the Organizational Immune System from a real governed vertical rather than from a generic monitoring framework.

The first bounded target is the canonical eligibility aggregate introduced by G.3/G.5:

```text
eligibility:<tenant_key>:<lead_id>:<pathway_id>
```

H.1 adds durable incident signals, aggregate-scoped structural integrity audit and a restrictive circuit state for that aggregate using the already-canonical `OrganizationActivity` stream model.

Permanent rule:

> **The Immune System may reduce or stop execution, but it may never create authority, autonomy or permission that the normal governance path did not already grant.**

## Why H.1 is aggregate-scoped

A tenant-wide kill switch would have unnecessarily large blast radius.

A WorkItem-scoped breaker could be bypassed by creating a different WorkItem for the same canonical eligibility truth.

Therefore the first breaker is scoped to the stable canonical eligibility aggregate:

```text
tenant + Lead + stable pathway
```

This matches the G.3/G.5 truth boundary and keeps unrelated cases/pathways operational.

## Durable representation

H.1 introduces no new table or migration.

It uses append-only `OrganizationActivity` records on:

```text
stream_key = immune:eligibility:<aggregate_key>
source_object_type = eligibility_aggregate
source_object_id = <aggregate_key>
```

Activity types:

```text
organization.immune.eligibility_incident.v1
organization.immune.eligibility_circuit_opened.v1
organization.immune.eligibility_circuit_closed.v1
```

The latest circuit-control Activity determines current state. No Activity history is rewritten in place.

## Incident classes

First-slice typed signals:

```text
CANONICAL_AGGREGATE_INTEGRITY
DURABLE_LINEAGE_INTEGRITY
RUNTIME_HEALTH_FAILURE
REVISION_CONFLICT
VERIFIER_DISAGREEMENT
REASSESSMENT_ROLLBACK
```

### Critical / automatic circuit-open

```text
CANONICAL_AGGREGATE_INTEGRITY
DURABLE_LINEAGE_INTEGRITY
```

These mean AIOS can no longer safely identify one coherent canonical eligibility truth/lineage. Continuing material execution would risk silent corruption, so the circuit opens immediately.

### Warning / observable but non-opening

```text
RUNTIME_HEALTH_FAILURE
REVISION_CONFLICT
VERIFIER_DISAGREEMENT
REASSESSMENT_ROLLBACK
```

These are not automatically treated as organizational corruption. A normal optimistic conflict, one runtime outage or legitimate verifier disagreement does not by itself prove systemic corruption.

Later H slices may add rate/recurrence policy only after operational evidence justifies it.

## Atomic critical transition

For a new critical incident:

```text
incident Activity
+ circuit-open Activity
→ one transaction
```

A critical incident must never become durable while its required restrictive circuit action is lost. Synthetic failure of the second staged Activity must roll the whole unit back.

## Circuit guard and G.4 preflight

Public guard:

```text
require_eligibility_circuit_closed(...)
```

Current semantics:

```text
CLOSED + coherent canonical lineage → execution may continue to normal governance
OPEN                               → raise EligibilityCircuitOpen
CLOSED + structural defect         → append CRITICAL incident + OPEN + raise EligibilityCircuitOpen
```

G.4 resolves any exact durable committed-effect replay first. Fresh execution then resolves the canonical aggregate from the trusted proposal WorkItem and runs this guard **before E.2 or either model/provider is called**.

This preserves two distinct truths:

- exact historical replay remains read-only/history-preserving and performs no new provider execution;
- fresh work cannot cross a known or newly detected aggregate circuit boundary.

The guard does not authorize any action when CLOSED. Normal E.2/F.1/G.1/G.2/G.3/G.4/G.5 authority, risk, verification, revision and Gateway checks remain mandatory.

## One canonical eligibility-lineage contract

The H.1 audit originally evolved separately from the G.3/G.4 replay validators. That created an unacceptable invariant-drift risk: a durable row could be present, same-tenant and causally connected while no longer representing the expected eligibility Activity type.

The canonical contract is now centralized in:

```text
apps/api/app/services/organization_eligibility_lineage.py
```

Public domain-specific validators:

```text
validate_canonical_eligibility_lineage(...)
canonical_eligibility_lineage_for_governance(...)
validate_canonical_eligibility_aggregate_lineage(...)
```

G.3 replay, G.4 replay and H.1 preflight consume this same contract.

Permanent rule:

> **Canonical eligibility lineage has one domain contract. Replay, orchestration and the Immune System may not redefine it independently.**

For each committed canonical revision the validator proves, as applicable:

1. tenant identity;
2. stable Lead + pathway-derived aggregate identity;
3. valid revision version/lifecycle;
4. predecessor and supersession identity;
5. assessment ↔ revision identity;
6. pathway-version ↔ stable pathway identity;
7. exact G.1 Activity type: `verification.eligibility.independent.v1`;
8. exact G.2 Activity type: `governance.eligibility.verification_floor.v1`;
9. canonical governance record kind: `eligibility_canonical_effect_authorization`;
10. exact semantic Activity type: `organization.eligibility.assessment_committed.v1`;
11. MATERIAL constitutional lineage classification;
12. source object type/id/version identity;
13. action, intent, readiness, verification, verification-floor and effect fingerprints;
14. expected previous revision identity/version;
15. semantic assessment/revision/effect identity;
16. E.2 → G.1 → G.2 → G.3 → semantic causation.

For the complete aggregate it additionally proves:

```text
versions are contiguous from v1
exactly one ACTIVE revision exists
latest revision is ACTIVE
all earlier revisions are SUPERSEDED
supersedes_revision_id forms one ordered chain
```

A structural defect receives a deterministic problem fingerprint. If a human closes the circuit without repairing the durable defect, the next fresh preflight detects the defect again and opens a new restrictive control state.

## Adversarial identity-corruption proof

H.1 was not accepted merely because valid fixtures pass.

The focused regression deliberately mutates already-committed durable lineage, including:

```text
verification Activity type
verification-floor Activity type
governance record kind
semantic Activity type
assessment/revision identity
semantic source revision identity
missing semantic lineage
invalid aggregate lifecycle
```

For fresh execution after structural corruption the required result is:

```text
canonical validator rejects lineage
→ CRITICAL immune incident
→ exact aggregate circuit OPEN
→ producer provider calls = 0
→ verifier provider calls = 0
```

Historical G.3/G.4 replay also uses the same validator and fails closed on the same identity corruption.

## Current automatic signal wiring

H.1 is wired to these concrete G.4 signals:

```text
open aggregate circuit
→ fresh G.4 stops before provider egress

canonical lifecycle / durable lineage defect
→ CRITICAL incident + aggregate circuit OPEN

producer runtime failure
→ RUNTIME_HEALTH_FAILURE warning

verifier runtime failure
→ RUNTIME_HEALTH_FAILURE warning

verifier DISAGREES
→ VERIFIER_DISAGREEMENT warning
```

`INSUFFICIENT_BASIS` remains a governed verification outcome and is not mislabeled as verifier disagreement.

Warnings remain observable and non-opening in H.1. They are not promoted to a circuit event without a future bounded recurrence/anomaly policy.

## Opening authority

Automatic opening uses the infrastructure actor:

```text
actor_type = system
actor_id   = organization-immune-system
role       = operator
```

This actor may append observable incident state and restrict execution only. It owns no `CapabilityAuthority` and does not become an `OrganizationPosition` employee identity.

## Recovery authority

H.1 deliberately has no automatic circuit recovery.

Closing a circuit restores only the ability to *attempt* governed execution and requires:

```text
authenticated human
+ admin role
```

Recovery appends a `circuit_closed` Activity that supersedes the current open control Activity.

Recovery payload records:

```text
restores_execution_attempts_only = true
grants_authority = false
```

Closing the breaker does not grant autonomy or material-action authority.

## Historical replay semantics

Incident keys and recovery keys are idempotent.

```text
incident A → OPEN
recovery A → CLOSED
incident B → OPEN
replay recovery A
→ remains OPEN
```

Historical idempotency may recover old records; it may not override newer control state.

An exact replay of an already committed G.4 canonical effect is also historical. It resolves before fresh-execution circuit preflight and must not call either model again, but it must still satisfy the canonical durable-lineage validator.

## Isolation

Circuit state remains tenant- and aggregate-scoped.

An open circuit for:

```text
tenant-a / aggregate-A
```

must not block:

```text
tenant-a / aggregate-B
tenant-b / aggregate-A-like identifier
```

## Production proof gate — accepted

H.1 acceptance depends on:

```text
docs/V1_3_H1_PRODUCTION_PROOF_GATE.md
docs/V1_3_H1_ACCEPTANCE_2026-08-21.md
```

and CI implementation:

```text
.github/workflows/v12-production-proof.yml
```

The accepted proof surface includes:

- full backend pytest regression on SQLite;
- repository policy and release-consistency checks;
- direct Python dependency constraint enforcement;
- migration and local schema checks;
- frontend reproducible install and high-severity security audit;
- frontend Node tests;
- TypeScript checking;
- Next.js production build;
- compiled frontend auth verification;
- a real PostgreSQL 16 lane;
- Alembic upgrade on PostgreSQL;
- focused G.3/G.4/G.5/H.1 PostgreSQL tests;
- cross-session stale reassessment proof;
- cross-session circuit recovery/reopen proof.

Final GitHub-hosted acceptance run:

```text
candidate = 0b19d61a417de2d372e101d4e132a6a0a6c2a84f
run       = 32463849415

Repository policy and constraints   PASS
Backend regression (SQLite)         PASS
Frontend tests, types and build     PASS
PostgreSQL governance contracts     PASS
```

Normal pytest remains SQLite by default. Setting `GMAI_TEST_DATABASE_URL` routes the same shared fixtures through an explicitly isolated PostgreSQL database.

The workflow existing and passing is not the same as proving repository branch protection requires it. Required-check enforcement is not claimed as verified and remains a repository-settings prerequisite before H.2 begins.

## Repository/dependency hygiene accepted with this checkpoint

The accidental tracked shell-redirection artifact:

```text
apps/api/=5.4
```

has been removed.

`check_repo_policy.py` rejects suspicious redirection-like filenames before extension filtering while preserving the existing content scan coverage.

Direct backend dependency reproducibility uses:

```text
apps/api/requirements.txt
+ apps/api/constraints.txt
```

with constrained install:

```text
python -m pip install -r apps/api/requirements.txt -c apps/api/constraints.txt
```

The API Dockerfile uses the same constraint baseline.

Current claim boundary: this is an exact **direct-dependency** constraint baseline, not a complete transitive lock.

Frontend dependency security is accepted on the bounded Next 16 baseline after a reproducible `npm ci` and zero-vulnerability high-severity audit.

Cross-platform receipt integrity was also repaired by replacing exactly two stale Windows-checkout SHA receipts with hashes of the canonical Git blob bytes. Evidence JSON and SHA validation semantics were not changed.

## Deliberate non-claims after H.1 acceptance

H.1 does not claim:

- branch-protection/ruleset enforcement of the Production Proof workflow;
- automatic wiring from **every** E.2–G.5 exception into incident creation;
- automatic `REVISION_CONFLICT` emission from every G.5 conflict path;
- automatic `REASSESSMENT_ROLLBACK` emission from every contained rollback path;
- tenant-wide or capability-wide circuit breaking;
- automatic recovery;
- recurrence thresholds or rolling-window anomaly policy;
- provider-wide/runtime-wide health scoring;
- incident aggregation/root-cause clustering across aggregates;
- earned-autonomy changes;
- generic incident-management infrastructure;
- Munder circuit-breaker adoption;
- new H.1 database schema;
- Playwright/browser E2E coverage;
- completed large-module decomposition.

Those remain future bounded work and may not be inferred from the H.1 seal.

## Accepted test/proof surface

Focused eligibility/H.1 suites include:

```text
apps/api/tests/test_organization_eligibility_effect.py
apps/api/tests/test_organization_eligibility_orchestration.py
apps/api/tests/test_organization_eligibility_lineage_contract.py
apps/api/tests/test_organization_eligibility_immune_system.py
apps/api/tests/test_organization_eligibility_immune_orchestration.py
apps/api/tests/test_organization_eligibility_immune_lineage.py
apps/api/tests/test_organization_eligibility_postgres_contract.py
```

Accepted evidence includes:

```text
full deterministic constrained backend
1105 passed / 7 skipped / 1 warning / 0 failed

fresh PostgreSQL 16 governed H.1
57 passed / 1 warning / 0 failed

local frontend
npm audit high = 0 vulnerabilities
28/28 design tests
4/4 request/auth tests
TypeScript PASS
Next.js production build PASS
compiled auth PASS

GitHub Actions run 32463849415
all four Production Proof jobs PASS
```

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

## Acceptance truth

H.1 is **ACCEPTED / SEALED** as of 2026-08-21.

The Production Proof Gate is **ACCEPTED / GREEN** on candidate `0b19d61a417de2d372e101d4e132a6a0a6c2a84f`, GitHub Actions run `32463849415`.

Required GitHub check enforcement is **NOT VERIFIED** and is explicitly recorded as the remaining repository-settings action.

H.2 remains **BLOCKED** until that enforcement is verified. No H.2 implementation is authorized by the H.1 acceptance alone.

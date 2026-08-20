# Global Mobility AIOS — V12.18 Pending Changelog

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** IMPLEMENTED / ACCEPTANCE PENDING  
**Accepted changelog remains:** `docs/CHANGELOG.md` at V1.3-G.5

This record exists so acceptance-pending repository changes are visible without falsely promoting them into the accepted changelog.

When the H.1 Production Proof Gate is accepted, the verified result should be reconciled into `docs/CHANGELOG.md` together with the actual test/CI evidence and accepted implementation head.

## H.1 canonical lineage consolidation

Added one domain-specific canonical eligibility-lineage validator:

```text
apps/api/app/services/organization_eligibility_lineage.py
```

G.3 replay, G.4 replay and H.1 preflight now consume the same durable lineage contract.

The contract validates stable aggregate/revision identity, exact eligibility Activity identity/record kind, source identity, fingerprints and causation instead of allowing those invariants to drift between callers.

## H.1 adversarial regression

Expanded H.1 tests to corrupt committed durable lineage deliberately:

```text
verification Activity type
verification-floor Activity type
governance record kind
semantic Activity type
assessment/revision identity
semantic source revision identity
missing semantic lineage
invalid lifecycle state
```

Fresh corrupted execution is expected to open a CRITICAL aggregate circuit before either producer or verifier provider egress.

G.3/G.4 historical replay is also expected to reject corrupted canonical lineage.

## PostgreSQL proof contracts

`apps/api/tests/conftest.py` now supports an explicitly isolated real database via:

```text
GMAI_TEST_DATABASE_URL
```

SQLite remains the default broad regression environment.

Added PostgreSQL-only cross-session contracts for:

- stale reassessment after another session commits the next revision;
- zero-provider-call stale rejection;
- circuit OPEN visibility;
- authorized recovery;
- later critical reopen;
- old recovery replay being unable to close the newer circuit.

## Database migration proof

`scripts/check_database_migrations.py` now validates for the configured database:

```text
exactly one Alembic head
physical SQLModel table/column schema
alembic_version == declared head
```

This applies to real PostgreSQL as well as SQLite.

## Production Proof CI

Added:

```text
.github/workflows/v12-production-proof.yml
```

Current lanes:

1. repository policy + release consistency + dependency constraints;
2. isolated SQLite migration + full backend pytest + schema proof;
3. frontend Node tests + TypeScript + Next.js production build;
4. PostgreSQL 16 migration/schema + focused governed eligibility/H.1 contracts.

The workflow is configured for `main`, `roadmap/**` pushes and pull requests.

No PASS is claimed yet.

A repository workflow existing is also not equivalent to branch protection requiring the checks. Required-check enforcement remains to be verified separately.

## Dependency reproducibility

Added:

```text
apps/api/constraints.txt
scripts/check_python_dependency_constraints.py
```

The API Dockerfile and CI use:

```text
pip install -r requirements.txt -c constraints.txt
```

Current claim is exact direct-dependency constraints only, not a full transitive lock.

## Repository hygiene

Removed accidental shell-redirection artifact:

```text
apps/api/=5.4
```

Repository policy now rejects suspicious redirection-like tracked filenames while retaining the prior file-content scan coverage.

## Roadmap correction

`docs/ROADMAP.md` now records:

```text
last accepted checkpoint = G.5
H.1 = IMPLEMENTED / ACCEPTANCE PENDING
H.1 seal = PAUSED
Production Proof Gate = IMPLEMENTED / ACCEPTANCE PENDING
H.2 = BLOCKED until proof is green
```

Large backend/frontend decomposition is sequenced after production proof rather than started in parallel with this repair.

## Acceptance boundary

This pending record must not be merged into the accepted changelog as PASS until real evidence exists for:

```text
focused canonical-lineage tests
adversarial H.1 tests
full backend regression
migration/schema checks
frontend tests/types/build
PostgreSQL migration/schema
focused PostgreSQL governance contracts
repository policy
dependency constraints
branch/head/docs synchronization
```

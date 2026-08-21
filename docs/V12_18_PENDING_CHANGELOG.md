# Global Mobility AIOS — V12.18 Acceptance Changelog

**Opened:** 2026-08-20  
**Accepted:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** ACCEPTED / CLOSED  
**H.1:** ACCEPTED / SEALED  
**Production Proof Gate:** ACCEPTED / GREEN  
**Acceptance candidate:** `0b19d61a417de2d372e101d4e132a6a0a6c2a84f`  
**GitHub Actions run:** `32463849415`  
**H.2:** BLOCKED pending required-check enforcement verification

This record began as the V12.18 acceptance-pending changelog so implementation work remained visible without being falsely promoted before production proof existed. The production-proof correction is now accepted. Detailed acceptance evidence is preserved in `docs/V1_3_H1_ACCEPTANCE_2026-08-21.md`.

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

Fresh corrupted execution opens a CRITICAL aggregate circuit before either producer or verifier provider egress.

G.3/G.4 historical replay also rejects corrupted canonical lineage.

## PostgreSQL proof contracts

`apps/api/tests/conftest.py` supports an explicitly isolated real database via:

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

Fresh PostgreSQL 16 proof passed from an empty database through Alembic head `0077_canonical_eligibility_assessment_revision`, physical-schema verification and the governed H.1 suite.

Accepted PostgreSQL result:

```text
Alembic 0001 → 0077              PASS
registered_tables                 119
physical_schema                   PASS
database_revision                 0077_canonical_eligibility_assessment_revision
governed H.1 suite                57 passed / 1 warning / 0 failed
```

## Database migration proof

`scripts/check_database_migrations.py` validates for the configured database:

```text
exactly one Alembic head
physical SQLModel table/column schema
alembic_version == declared head
```

This applies to real PostgreSQL as well as SQLite.

Migration `0077` also received explicit PostgreSQL-safe names for the verification-floor indexes after fresh-database proof exposed generated identifiers longer than PostgreSQL's 63-byte limit.

## Production Proof CI

Added:

```text
.github/workflows/v12-production-proof.yml
```

Current lanes:

1. repository policy + release consistency + dependency constraints + diff hygiene;
2. isolated SQLite migration + full backend pytest + schema proof;
3. frontend install + security audit + Node tests + TypeScript + Next.js production build + compiled auth;
4. PostgreSQL 16 migration/schema + focused governed eligibility/H.1 contracts.

The workflow is configured for `main`, `roadmap/**` pushes and pull requests.

Final accepted GitHub-hosted run:

```text
candidate = 0b19d61a417de2d372e101d4e132a6a0a6c2a84f
run       = 32463849415

Repository policy and constraints   PASS
Backend regression (SQLite)         PASS
Frontend tests, types and build     PASS
PostgreSQL governance contracts     PASS
```

The repository-policy lane was repaired to fetch the parent commit before running `git diff --check HEAD^`.

The frontend lane was aligned to Node 24 after the previous Node 20.20.2 run rejected the request/auth test's `--experimental-strip-types` flag. The final Node 24 run passed every frontend step.

A repository workflow existing and passing is not equivalent to branch protection requiring the checks. Required-check enforcement remains a separately recorded repository-settings action and is not claimed as verified.

## Frontend security repair

The old frontend baseline was not accepted because npm audit evidence showed high/critical vulnerabilities.

An intermediate Next 15.5.21 candidate still carried high-severity findings through transitive `nanoid`, `postcss` and `sharp` dependencies.

The accepted bounded baseline is:

```text
next=16.3.1
react=19.0.8
react-dom=19.0.8
postcss=8.5.23
sharp=0.35.3
nanoid=3.3.18
```

Accepted frontend proof:

```text
npm ci                         PASS
npm audit --audit-level=high   PASS — 0 vulnerabilities
design foundation              PASS — 28/28
request/auth                   PASS — 4/4
TypeScript                     PASS
Next.js production build       PASS
compiled auth                  PASS
```

Next 16-generated TypeScript/route-type configuration was accepted. The obsolete `next lint` package script was removed rather than leaving a knowingly invalid command.

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

Current claim is exact direct-dependency constraints, not a full transitive lock.

The deterministic constrained backend environment passed:

```text
Python dependency constraints       PASS — 25 direct dependencies
pip check                           PASS
full backend                        1105 passed / 7 skipped / 1 warning / 0 failed
```

Compatibility corrections retained in the accepted baseline include PyYAML `6.0.3`, clamd `1.0.2`, psycopg/psycopg-binary `3.2.2`, and an explicit bodyless FastAPI HTTP 204 checklist DELETE response.

## Repository hygiene and evidence portability

Removed accidental shell-redirection artifact:

```text
apps/api/=5.4
```

Repository policy rejects suspicious redirection-like tracked filenames while retaining the prior file-content scan coverage.

The expanded policy scan explicitly treats the existing `vendor/munder-difflin/v0.4.4` snapshot as declared reference-only vendor material rather than product source, while suspicious filename checks remain repository-wide.

A canonical Git-blob receipt audit checked 20 evidence receipts and found exactly two stale Windows-checkout hashes. Only those receipt files were corrected:

```text
v10_22_2_africa_tranche_1A_ready_9.json
SHA-256 = e7527b1ea84fca60c0afde49d5b6f0c48a22e6d9207305cd2c1fcecebc970db4

v10_22_3_botswana_supplemental_source.json
SHA-256 = 546343546f7112e8d6b2c59abda1f7a06563ae3a14e7da4863d884098d0c31a2
```

The evidence JSON was not modified and SHA validation was not weakened. The subsequent GitHub-hosted Linux backend lane passed.

## Accepted proof boundary

The V12.18 production-proof correction is accepted on evidence for:

```text
focused canonical-lineage tests                 PASS
adversarial H.1 tests                            PASS
full constrained backend regression              PASS
migration/schema checks                          PASS
frontend tests/types/build                       PASS
frontend high-severity audit                      PASS — 0 vulnerabilities
fresh PostgreSQL migration/schema                PASS
focused PostgreSQL governance contracts          PASS
repository policy                                PASS
dependency constraints                           PASS
final GitHub-hosted four-lane workflow           PASS
```

The known Pydantic 2.8 `model_metadata_json` protected-namespace warning remains visible and non-blocking.

## Acceptance boundary and next step

Current accepted state:

```text
H.1 = ACCEPTED / SEALED
Production Proof Gate = ACCEPTED / GREEN
Required-check enforcement = NOT VERIFIED
H.2 = BLOCKED
```

The H.1 gate explicitly permits required-check enforcement to be recorded as a remaining repository-settings action at acceptance. The roadmap retains a stricter H.2 entry sequence: required GitHub check enforcement must be verified before H.2 production transition guardrails begin.

No H.2 implementation is authorized by this changelog entry alone.

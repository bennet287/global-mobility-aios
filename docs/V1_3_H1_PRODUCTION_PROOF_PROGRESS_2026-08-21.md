# Global Mobility AIOS — V1.3-H.1 Production Proof Progress

**Evidence date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted baseline remains:** V1.3-G.5  
**Latest fully tested constrained-backend head:** `c4d958c6b6d16f3fbd2dd06d3968049f192ee9f0`  
**Latest fresh PostgreSQL 16 proof head:** `76f0a7b7abe9312a25571f11624126b5d00a22b4`  
**Status:** PARTIAL PROOF RECORDED / BACKEND + FRESH POSTGRESQL H.1 PROOF PASS / FRONTEND SECURITY + CURRENT FRONTEND PROOF REQUIRED / H.1 ACCEPTANCE STILL PENDING

This record captures real Human Owner local verification for the V12.18 H.1/Production Proof candidate. Failed proof attempts are intentionally preserved as evidence. It does not seal H.1 and does not authorize H.2.

## 1. Backend / SQLite evidence

### Original H.1 backend candidate

The original H.1 proof candidate passed the full backend suite on:

```text
44744ca5d550c94dfd6809345a0f1052cb99dcf3
```

Result:

```text
1095 passed
5 skipped
1 warning
0 failed
duration = 417.39s
```

### Canonical-lineage repair candidate

After the PostgreSQL behavioral defects were repaired, the focused SQLite regression on:

```text
5eccb70a5b5cf15a37944511292831f058a70e0c
```

passed:

```text
55 passed
1 warning
0 failed
duration = 33.29s
```

The full backend suite on the same head then passed:

```text
1105 passed
7 skipped
1 warning
0 failed
duration = 511.09s
```

### Backend source revalidation before deterministic dependency downgrade

The full backend suite was run again on:

```text
ddac84b054c92c872f6df668e8c6f7a2a76e270c
```

Runtime:

```text
Python 3.13.12
```

Result:

```text
1105 passed
7 skipped
1 warning
0 failed
duration = 513.70s
```

This was valid source-tree evidence, but it occurred before the proof environment was downgraded to the deterministic direct-dependency candidates.

### Full deterministic constrained backend — PASS

After the direct-dependency compatibility candidates were successfully installed and the FastAPI HTTP-204 contract repair was applied, the complete backend suite was run on:

```text
c4d958c6b6d16f3fbd2dd06d3968049f192ee9f0
```

Runtime:

```text
Python 3.13.12
fastapi=0.115.0
starlette=0.38.6
pydantic=2.8.0
sqlmodel=0.0.22
alembic=1.13.0
PyYAML=6.0.3
clamd=1.0.2
psycopg=3.2.2
psycopg-binary=3.2.2
pytest=8.3.0
```

Pre-test dependency checks:

```text
Python dependency constraints passed for 25 direct dependencies.
pip check → No broken requirements found.
```

Full backend result:

```text
1105 passed
7 skipped
1 warning
0 failed
duration = 536.28s (0:08:56)
```

Post-test repository/release evidence:

```text
Repository policy check passed.
Release consistency check passed. Alembic head: 0077_canonical_eligibility_assessment_revision
git diff --check = clean
roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
```

This closes the deterministic Python backend runtime sub-gate for the current candidate set.

The only warning in the constrained full suite is:

```text
UserWarning: Field "model_metadata_json" has conflict with protected namespace "model_".
```

This is a Pydantic 2.8 compatibility warning. It did not affect application import, collection, route registration, persistence tests, or any of the 1105 passing tests. It remains visible as a follow-up compatibility item and is not expanded into the H.1 correction unless later proof demonstrates behavioral impact.

## 2. SQLite migration / physical schema evidence

Earlier local SQLite proof passed with:

```text
Database migration check passed.
database_url = sqlite:///./gmai.db
migration_heads = 0077_canonical_eligibility_assessment_revision
registered_tables = 119
physical_schema = ok
database_revision = 0077_canonical_eligibility_assessment_revision
```

Local schema proof passed with:

```text
registered_tables = 119
actual_tables = 119
physical_tables = 120
infrastructure_tables = ["alembic_version"]
```

Migration head remains:

```text
0077_canonical_eligibility_assessment_revision
```

## 3. PostgreSQL governed eligibility / H.1 behavior

### First real PostgreSQL behavioral attempt — FAILED

The first real PostgreSQL 16 governed eligibility/H.1 suite ran on:

```text
ad07f1e1416b7d524a880f3ca0596e8004ba5250
```

Result:

```text
49 passed
8 failed
1 warning
duration = 908.01s
```

The failure was retained rather than hidden.

### Behavioral repairs

Three bounded repairs followed:

```text
78d310d6fa8c4dd5ba0eeea35ef726b24e4bd548
fix: align canonical governance outcome with persisted contract

ad2bd9a339601d6fb14d7b0404b9ab8129d32223
test: make H.1 lineage corruption PostgreSQL-valid

a192fafd9290013a7f99e946bb1f43c929760297
test: assert canonical replay cardinality failure code
```

The first aligned the shared canonical validator with the sealed governance projection's persisted `AUTO_EXECUTE` representation. The second changed adversarial corruption from a random foreign-key-breaking activity ID to a real same-tenant cross-link so PostgreSQL could preserve referential integrity while H.1 evaluated higher-order lineage integrity. The third asserted the stable `governance_revision_cardinality` failure code rather than obsolete caller-era prose.

### PostgreSQL behavioral retest — PASS

The governed eligibility/H.1 suite was rerun on:

```text
5eccb70a5b5cf15a37944511292831f058a70e0c
```

Result:

```text
57 passed
1 warning
0 failed
duration = 589.67s
```

This established real PostgreSQL behavioral evidence for the shared G.3/G.4/H.1 lineage repair, but it did not yet establish a fresh-database migration proof.

## 4. Fresh PostgreSQL 16 migration / schema / H.1 proof — PASS

### Prior migration failure

A fresh PostgreSQL 16 Alembic upgrade through `0077` previously failed because a generated index identifier exceeded PostgreSQL's 63-character limit:

```text
ix_eligibility_assessment_revisions_verification_floor_activity_id
```

The failure was:

```text
sqlalchemy.exc.IdentifierError:
Identifier 'ix_eligibility_assessment_revisions_verification_floor_activity_id'
exceeds maximum length of 63 characters
```

Because Alembic aborted transactionally, the subsequent incomplete-schema output was not treated as an independent model-drift defect.

`0077_canonical_eligibility_assessment_revision.py` was repaired to use explicit PostgreSQL-safe index names:

```text
ix_eligibility_revisions_verification_floor_activity
ix_eligibility_revisions_verification_floor_fp
```

### Current fresh-database proof

On:

```text
76f0a7b7abe9312a25571f11624126b5d00a22b4
```

the Human Owner started a fresh `postgres:16` container with an empty `global_mobility_aios_test` database and pointed both `DATABASE_URL` and `GMAI_TEST_DATABASE_URL` at that isolated database.

Pre-proof environment integrity:

```text
Python 3.13.12
pip check → No broken requirements found.
```

Alembic then successfully executed the complete controlled migration sequence:

```text
0001_mvp1_baseline
→ ...
→ 0076_organization_position_active_identity
→ 0077_canonical_eligibility_assessment_revision
```

No PostgreSQL identifier failure recurred.

The physical schema/head checker then passed:

```text
Database migration check passed.
database_url=postgresql+psycopg://postgres:***@127.0.0.1:55432/global_mobility_aios_test
migration_heads=0077_canonical_eligibility_assessment_revision
registered_tables=119
physical_schema=ok
database_revision=0077_canonical_eligibility_assessment_revision
```

On the same fresh PostgreSQL database and same candidate head, the governed eligibility/H.1 suite passed:

```text
57 passed
1 warning
0 failed
duration = 973.50s (0:16:13)
```

Final repository truth remained:

```text
76f0a7b7abe9312a25571f11624126b5d00a22b4
roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
git diff --check = clean
```

This closes the fresh PostgreSQL migration/schema/H.1 backend production-proof sub-gate. The recurring warning is the same non-blocking Pydantic 2.8 `model_metadata_json` protected-namespace warning already recorded in the constrained backend proof.

## 5. Repository policy / release consistency

Repeated local proof has established:

```text
Repository policy check passed.
Release consistency check passed. Alembic head: 0077_canonical_eligibility_assessment_revision
Python dependency constraints passed for 25 direct dependencies.
git diff --check = clean
```

The current constrained full-backend and fresh PostgreSQL proofs both completed on synchronized V12 branch heads with clean repository state.

## 6. Deterministic Python dependency-install proof — PASS

The constraints file is a direct-dependency compatibility candidate, not yet a complete transitive lock. The current candidate has proven installability and backend runtime compatibility on the Human Owner's CPython 3.13 Windows proof environment.

### Constraint syntax defect — repaired

The first constraint form incorrectly included extras such as:

```text
uvicorn[standard]==...
psycopg[binary]==...
```

Modern pip rejects extras in constraint entries. Extras remain in `requirements.txt`; constraints use normalized distribution names.

### PyYAML minimum candidate — failed, repaired

On Python 3.13.12, `pyyaml==6.0.0` fell back to an old source-build path and failed with:

```text
AttributeError: 'build_ext' object has no attribute 'cython_sources'
```

The exact candidate moved to:

```text
pyyaml==6.0.3
```

### clamd minimum candidate — failed, repaired

The earlier `clamd==1.0.0` candidate failed during package metadata generation because that release uses an obsolete `d2to1` / old setuptools build path. The repair preserved the `clamd.ClamdNetworkSocket` API while moving the candidate to:

```text
requirements.txt: clamd>=1.0.2
constraints.txt:  clamd==1.0.2
```

### Psycopg binary minimum candidate — failed, repaired

The earlier `psycopg==3.2.0` constraint resolved the `binary` extra to unavailable `psycopg-binary==3.2.0.dev1` on CPython 3.13 Windows. The repaired contract is:

```text
requirements.txt: psycopg[binary]>=3.2.2
constraints.txt:  psycopg==3.2.2
```

The successful constrained install proved:

```text
PyYAML=6.0.3
clamd=1.0.2
psycopg=3.2.2
psycopg-binary=3.2.2
pip check → No broken requirements found.
```

The same deterministic environment subsequently passed the focused compatibility test and complete 1105-test backend suite.

## 7. Constrained runtime compatibility repair

FastAPI 0.115 exposed an invalid API contract during application import:

```text
DELETE /api/v1/application-authority-checklist-items/{item_id}
status_code = 204
handler return = None using default response machinery
```

FastAPI correctly rejected the route because HTTP 204 must not have a response body. The route was repaired on:

```text
78ad35efa68973e4e28f135195fabce4c9cd49fb
```

It now uses an explicit empty `Response` for HTTP 204 and disables response-model generation for that endpoint.

Focused proof:

```text
12 passed
1 warning
0 failed
duration = 0.91s
```

The subsequent full constrained backend suite passed all 1105 runnable tests, establishing compatibility across the backend surface.

## 8. Frontend production-proof evidence and remaining blocker

Earlier frontend evidence established:

```text
design-foundation tests: 28 passed / 0 failed
request-auth tests:       4 passed / 0 failed
TypeScript/build path:    Next.js production build completed successfully
```

The compiled-auth verifier previously failed because it asserted local API port `8002` while the canonical repository client configuration/default uses port `8000`. The proof harness has since been corrected to canonical configuration and the workflow supplies deterministic public build-time auth configuration. That correction still requires a current-head frontend rerun.

The current frontend dependency baseline remains:

```text
next=15.2.4
react=19.0.0
react-dom=19.0.0
```

Earlier `npm ci`/audit evidence reported:

```text
4 vulnerabilities
3 high
1 critical
```

The security signal is not waived. Upstream security verification performed during the 2026-08-21 proof shows that the old React2Shell-only patch targets are no longer sufficient because later 2026 advisories affect earlier patched lines as well. The bounded current repair target is therefore at least:

```text
Next.js 15.x security floor: 15.5.21
React 19.0.x security floor: 19.0.8
React DOM 19.0.x:            19.0.8
```

The frontend package and lockfile must be regenerated together and then proven with a fresh install, audit, existing design/request-auth tests, TypeScript, production build, and compiled-client-auth verification. The lockfile will not be hand-edited.

## 9. Current evidence matrix

```text
Focused SQLite H.1 / lineage regression         PASS (55 passed)
Full backend regression, pre-constraint env      PASS (1105 passed / 7 skipped)
SQLite migration consistency                    PASS
SQLite physical schema                          PASS
Repository policy                               PASS
Release consistency                             PASS
Direct dependency constraint structure          PASS (25 dependencies)
Constrained dependency installation             PASS
Constrained exact dependency versions           PASS
Constrained pip integrity                       PASS
Constrained application import                  PASS
HTTP 204 checklist contract                     PASS
ClamAV adapter compatibility                    PASS
Focused constrained runtime regression          PASS (12 passed)
Full backend on constrained environment          PASS (1105 passed / 7 skipped / 1 warning)
PostgreSQL governed H.1 behavior                PASS (57 passed on earlier repaired head)
Fresh PostgreSQL Alembic upgrade                PASS (empty PostgreSQL 16 DB → 0077)
Fresh PostgreSQL physical schema/head           PASS (119 registered tables / physical_schema=ok / revision=0077)
Current-head PostgreSQL governed H.1 suite      PASS (57 passed / 1 warning)
Frontend design/request-auth                    PASS on earlier candidate; current rerun required
Frontend TypeScript/build                       PASS on earlier candidate; current rerun required
Compiled frontend auth                          REPAIRED / RETEST REQUIRED
Frontend dependency security                    BLOCKED until patched package+lock candidate is proven
GitHub Actions current-head execution           NOT YET PROVEN
Required-check/branch-protection enforcement    NOT YET VERIFIED
```

## 10. Acceptance state

H.1 remains:

```text
IMPLEMENTED / ACCEPTANCE PENDING
```

The Production Proof Gate remains:

```text
IMPLEMENTED / BACKEND + POSTGRESQL PROVEN / FRONTEND + CI EVIDENCE PENDING / NOT SEALED
```

H.2 remains:

```text
BLOCKED
```

Permanent sequencing now is:

```text
frontend security repair + current frontend production proof
→ CI/settings evidence where available
→ reconcile ROADMAP / CHANGELOG / H.1 acceptance records
→ seal H.1 only if all required evidence is green
→ only then begin H.2
```

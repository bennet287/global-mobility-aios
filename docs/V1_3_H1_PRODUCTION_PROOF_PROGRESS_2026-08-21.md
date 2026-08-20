# Global Mobility AIOS — V1.3-H.1 Production Proof Progress

**Evidence date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted baseline remains:** V1.3-G.5  
**Latest fully tested constrained-backend head:** `c4d958c6b6d16f3fbd2dd06d3968049f192ee9f0`  
**Status:** PARTIAL PROOF RECORDED / BACKEND CONSTRAINED RUNTIME PASS / FRESH POSTGRESQL MIGRATION PROOF + FRONTEND SECURITY PROOF REQUIRED / H.1 ACCEPTANCE STILL PENDING

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

### Behavioral repair 1 — canonical governance outcome representation

The shared canonical lineage validator expected lowercase:

```text
outcome = auto_execute
```

while the sealed governance projection persists:

```text
outcome = AUTO_EXECUTE
```

Repair:

```text
78d310d6fa8c4dd5ba0eeea35ef726b24e4bd548
fix: align canonical governance outcome with persisted contract
```

### Behavioral repair 2 — PostgreSQL-valid adversarial lineage corruption

Two H.1 tests previously used a random `semantic_activity_id`. Real PostgreSQL correctly rejected that mutation through the composite foreign key before H.1 could evaluate higher-order lineage integrity.

Repair:

```text
ad2bd9a339601d6fb14d7b0404b9ab8129d32223
test: make H.1 lineage corruption PostgreSQL-valid
```

The corruption now cross-links to an existing same-tenant Activity, preserving referential integrity while violating canonical semantic lineage.

### Behavioral repair 3 — stable replay failure code

Repair:

```text
a192fafd9290013a7f99e946bb1f43c929760297
test: assert canonical replay cardinality failure code
```

The replay test now asserts:

```text
governance_revision_cardinality
```

rather than obsolete caller-era prose.

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

This establishes real PostgreSQL behavioral evidence for the shared G.3/G.4/H.1 lineage repair. It does **not** by itself establish the fresh-database PostgreSQL migration gate.

## 4. Fresh PostgreSQL migration proof — prior failure repaired, current-head retest required

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

Because Alembic aborted transactionally, the subsequent physical-schema check correctly reported the database as incomplete. That output is not treated as a separate model-drift defect.

`0077_canonical_eligibility_assessment_revision.py` has since been repaired to use explicit PostgreSQL-safe index names:

```text
ix_eligibility_revisions_verification_floor_activity
ix_eligibility_revisions_verification_floor_fp
```

Required proof still outstanding:

```text
fresh PostgreSQL 16 database
→ alembic upgrade head succeeds from empty DB
→ database revision == 0077_canonical_eligibility_assessment_revision
→ registered/physical schema check passes
→ governed eligibility/H.1 PostgreSQL suite passes on the same current candidate
```

Until that sequence is observed on the current repaired head, the PostgreSQL Production Proof lane is not marked PASS.

## 5. Repository policy / release consistency

Repeated local proof has established:

```text
Repository policy check passed.
Release consistency check passed. Alembic head: 0077_canonical_eligibility_assessment_revision
Python dependency constraints passed for 25 direct dependencies.
git diff --check = clean
```

The current constrained full-backend proof on `c4d958c6b6d16f3fbd2dd06d3968049f192ee9f0` again passed these checks and completed with the local branch synchronized with `origin/roadmap/global-mobility-aios-v12`.

## 6. Deterministic Python dependency-install proof

The constraints file is a direct-dependency compatibility candidate, not yet a complete transitive lock. The current candidate has now proven installability and backend runtime compatibility on the Human Owner's CPython 3.13 Windows proof environment.

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

The exact candidate was moved to:

```text
pyyaml==6.0.3
```

### clamd minimum candidate — failed, repaired

The earlier `clamd==1.0.0` candidate failed during package metadata generation because that release uses an obsolete `d2to1` / old setuptools build path:

```text
ImportError: cannot import name '_get_unpatched' from 'setuptools.dist'
```

The application adapter uses `clamd.ClamdNetworkSocket`. The repair preserved the package/API and moved the declared minimum/candidate to:

```text
requirements.txt: clamd>=1.0.2
constraints.txt:  clamd==1.0.2
```

### Psycopg binary minimum candidate — failed, repaired

The constrained install on `2808dd4fe91e18bb382c9d95e1f2502cb9461ab6` failed because:

```text
psycopg==3.2.0
```

resolved its `binary` extra to:

```text
psycopg-binary==3.2.0.dev1
```

which has no matching distribution for the CPython 3.13 Windows proof environment.

Repairs:

```text
291a2ec9f56e79cb5c33fa90ef822e19ba215305
fix: raise psycopg binary floor for Python 3.13

4a09646ea9d93b96071e312b73510f5b9aace634
fix: pin psycopg binary-compatible candidate
```

Current contract:

```text
requirements.txt: psycopg[binary]>=3.2.2
constraints.txt:  psycopg==3.2.2
```

### Successful constrained installation — PASS

On:

```text
59cdcb3af3a5661660e3d5b9e8575983014263ee
```

the constraint checker passed for all 25 declared direct dependencies and the constrained installation completed successfully.

Installed critical candidates:

```text
PyYAML=6.0.3
clamd=1.0.2
psycopg=3.2.2
psycopg-binary=3.2.2
```

Integrity:

```text
pip check → No broken requirements found.
```

The same deterministic environment subsequently passed the focused compatibility test and the complete backend suite recorded above.

## 7. Constrained runtime compatibility repair

### FastAPI 0.115 exposed an invalid 204 response contract

After the successful constrained install, the targeted malware test initially failed during application import before any malware-scanning assertion ran.

FastAPI 0.115 rejected:

```text
DELETE /api/v1/application-authority-checklist-items/{item_id}
status_code = 204
handler return = None using default response machinery
```

with:

```text
AssertionError: Status code 204 must not have a response body
```

This was treated as a real API contract defect rather than hidden by raising the FastAPI floor.

Repair:

```text
78ad35efa68973e4e28f135195fabce4c9cd49fb
```

The route now uses an explicit empty `Response` for HTTP 204 and disables response-model generation for that endpoint.

Focused constrained-environment runtime proof then passed:

```text
12 passed
1 warning
0 failed
duration = 0.91s
```

The full constrained backend suite subsequently passed 1105 tests, establishing that the repair is compatible across the complete backend surface.

## 8. Frontend production-proof evidence and blockers

Earlier frontend evidence established:

```text
design-foundation tests: 28 passed / 0 failed
request-auth tests:       4 passed / 0 failed
TypeScript/build path:    Next.js production build completed successfully
```

The compiled-auth verifier then failed because it asserted local API port `8002` while the canonical repository client configuration/default uses port `8000`. The proof harness has since been corrected to canonical configuration and the workflow now supplies deterministic public build-time auth configuration.

That correction still requires a current-head frontend rerun.

Separately, `npm ci` reported:

```text
4 vulnerabilities
3 high
1 critical
```

and specifically warned that pinned Next.js `15.2.4` has a security vulnerability. This security signal is **not waived**. A bounded patched Next.js dependency update and current frontend/audit/type/build/compiled-auth proof are required before the Production Proof Gate can be sealed.

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
Fresh PostgreSQL Alembic upgrade                RETEST REQUIRED after identifier repair
Fresh PostgreSQL physical schema/head           RETEST REQUIRED
Current-head PostgreSQL governed H.1 suite      RETEST REQUIRED on same fresh DB
Frontend design/request-auth                    PASS on earlier candidate; current rerun required
Frontend TypeScript/build                       PASS on earlier candidate; current rerun required
Compiled frontend auth                          REPAIRED / RETEST REQUIRED
Frontend dependency security                    BLOCKED by known high/critical audit findings
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
IMPLEMENTED / PARTIALLY PROVEN / NOT SEALED
```

H.2 remains:

```text
BLOCKED
```

Permanent sequencing now is:

```text
fresh PostgreSQL migration/schema/H.1 proof
→ frontend security repair + current frontend production proof
→ CI/settings evidence where available
→ reconcile ROADMAP / CHANGELOG / H.1 acceptance records
→ seal H.1 only if all required evidence is green
→ only then begin H.2
```

# Global Mobility AIOS — V1.3-H.1 Production Proof Progress

**Evidence date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Accepted baseline remains:** V1.3-G.5  
**Latest fully tested backend source/dependency-candidate head:** `ddac84b054c92c872f6df668e8c6f7a2a76e270c`  
**Latest dependency-proof attempt head:** `2808dd4fe91e18bb382c9d95e1f2502cb9461ab6`  
**Current dependency-repair candidate head:** `4a09646ea9d93b96071e312b73510f5b9aace634`  
**Status:** PARTIAL PROOF RECORDED / DEPENDENCY INSTALL RETEST + FRESH POSTGRESQL MIGRATION PROOF + FRONTEND SECURITY PROOF REQUIRED / H.1 ACCEPTANCE STILL PENDING

This record captures real Human Owner local verification for the V12.18 H.1/Production Proof candidate. It deliberately preserves failed proof attempts as evidence. It does not seal H.1 and does not authorize H.2.

## 1. Backend / SQLite evidence

### Original backend candidate

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

After the PostgreSQL behavioral defects described below were repaired, the focused SQLite regression on:

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

### Current backend source tree under the dependency-proof candidate

After the production-proof infrastructure repairs and the PyYAML candidate-pin correction, the full backend suite was run again on:

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

Worktree evidence at completion:

```text
git diff --check = clean
roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
```

The single recurring warning is:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

The later dependency-repair commits change only declared dependency minimum/exact candidates and proof documentation; they do not change application source. Therefore the 1105-test backend result remains source-tree evidence, while each changed dependency candidate still requires deterministic install/runtime proof before acceptance.

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

### First real PostgreSQL behavioral attempt — failed

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

### PostgreSQL behavioral retest — passed

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

This establishes real PostgreSQL behavioral evidence for the shared G.3/G.4/H.1 lineage repair.

It does **not** by itself establish the fresh-database PostgreSQL migration gate, because the same production-proof sequence exposed the independent migration defect below.

## 4. Fresh PostgreSQL migration proof — prior failure and repair pending retest

A fresh PostgreSQL 16 Alembic upgrade through `0077` failed because a generated index identifier exceeded PostgreSQL's 63-character limit:

```text
ix_eligibility_assessment_revisions_verification_floor_activity_id
```

The failure was:

```text
sqlalchemy.exc.IdentifierError:
Identifier 'ix_eligibility_assessment_revisions_verification_floor_activity_id'
exceeds maximum length of 63 characters
```

Because Alembic aborted transactionally, the subsequent physical-schema check correctly reported the database as incomplete. That missing-schema output is not treated as an independent model drift defect.

`0077_canonical_eligibility_assessment_revision.py` has since been repaired to use bounded explicit index names for identifiers that exceed the PostgreSQL limit.

Required proof still outstanding:

```text
fresh PostgreSQL 16 database
→ alembic upgrade head succeeds
→ database revision == 0077_canonical_eligibility_assessment_revision
→ registered/physical schema check passes
→ governed eligibility/H.1 PostgreSQL suite passes on the same current candidate
```

Until that sequence is observed on the current repaired head, the PostgreSQL Production Proof lane is not marked PASS.

## 5. Repository policy / release consistency / dependency contract

Earlier local proof established:

```text
Repository policy check passed.
Release consistency check passed. Alembic head: 0077_canonical_eligibility_assessment_revision
Python dependency constraints passed for 25 direct dependencies.
git diff --check = clean
```

On dependency-proof attempt head `2808dd4fe91e18bb382c9d95e1f2502cb9461ab6`, the Human Owner reran the relevant checks and observed:

```text
Python dependency constraints passed for 25 direct dependencies.
Repository policy check passed.
Release consistency check passed. Alembic head: 0077_canonical_eligibility_assessment_revision
git diff --check = clean
```

The branch/worktree was synchronized at the beginning and end of that attempt.

## 6. Deterministic Python dependency-install proof

The constraints file is a direct-dependency compatibility candidate, not yet a complete transitive lock. Acceptance requires the candidate to install in the supported proof environment and then pass runtime tests.

### Constraint syntax defect — repaired

The first constraint form incorrectly included extras such as:

```text
uvicorn[standard]==...
psycopg[binary]==...
```

Modern pip rejects extras in constraint entries. Extras remain in `requirements.txt`; constraints now use normalized distribution names.

### PyYAML minimum candidate — failed, repaired

On Python 3.13.12, the `pyyaml==6.0.0` candidate fell back to an old source-build path and failed with:

```text
AttributeError: 'build_ext' object has no attribute 'cython_sources'
```

The exact candidate was moved to:

```text
pyyaml==6.0.3
```

and later install attempts successfully resolved the wheel-backed PyYAML 6.0.3 candidate.

### clamd minimum candidate — failed, repaired and adapter-proven

An earlier constrained-install attempt reached:

```text
clamd==1.0.0
```

and failed during package metadata generation because that release uses the obsolete `d2to1` / old setuptools build path:

```text
ImportError: cannot import name '_get_unpatched' from 'setuptools.dist'
```

The application adapter uses the `clamd.ClamdNetworkSocket` client API. The bounded repair preserved that package/API and moved only the declared minimum/candidate to:

```text
requirements.txt: clamd>=1.0.2
constraints.txt:  clamd==1.0.2
```

On `2808dd4fe91e18bb382c9d95e1f2502cb9461ab6`, the environment confirmed:

```text
PyYAML=6.0.3
clamd=1.0.2
pip check: No broken requirements found.
```

The targeted malware adapter contract then passed:

```text
11 passed
1 warning
0 failed
duration = 0.13s
```

This establishes the ClamAV adapter compatibility itself. It does **not** mark the overall constrained install PASS because pip failed later in the same install attempt on the Psycopg candidate below.

### Psycopg binary minimum candidate — failed, repaired, retest pending

The constrained install on:

```text
2808dd4fe91e18bb382c9d95e1f2502cb9461ab6
```

failed while resolving:

```text
psycopg[binary]>=3.2
constraints.txt: psycopg==3.2.0
```

Psycopg 3.2.0's `binary` extra resolves to:

```text
psycopg-binary==3.2.0.dev1
```

which has no matching distribution for the Human Owner's CPython 3.13 Windows production-proof environment. The observed terminal failure was:

```text
ERROR: Could not find a version that satisfies the requirement
psycopg-binary==3.2.0.dev1
ERROR: No matching distribution found for psycopg-binary==3.2.0.dev1
```

This is treated as another invalid minimum compatibility candidate, not as an application or database behavior failure.

The bounded repair moves the floor/exact direct candidate to the first 3.2-series release with a published CPython 3.13 Windows binary wheel:

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

Required dependency proof now outstanding:

```text
constraint checker PASS on current repair head
constrained pip install PASS on current repair head
installed psycopg / psycopg-binary versions confirmed
pip check PASS after successful constrained install
```

The existing PyYAML/clamd version output, `pip check`, and 11-test malware adapter result are retained as real evidence from the failed-install attempt, but they do not substitute for a complete successful constrained install.

## 7. Frontend production-proof evidence and blockers

Earlier frontend evidence established:

```text
design-foundation tests: 28 passed / 0 failed
request-auth tests:       4 passed / 0 failed
TypeScript/build path:    Next.js production build completed successfully
```

The compiled-auth verifier then failed because it asserted local API port `8002` while the canonical repository client configuration/default uses port `8000`. The proof harness has since been corrected to the canonical configuration and the workflow now supplies deterministic public build-time auth configuration.

That correction still requires a current-head frontend rerun.

Separately, `npm ci` reported:

```text
4 vulnerabilities
3 high
1 critical
```

and specifically warned that the pinned Next.js `15.2.4` release has a security vulnerability. This security signal is **not waived**. A bounded patched Next.js dependency update and current frontend/audit/type/build/compiled-auth proof are required before the Production Proof Gate can be sealed.

## 8. Current evidence matrix

```text
Focused SQLite H.1 / lineage regression         PASS (55 passed)
Full backend regression                         PASS (1105 passed / 7 skipped)
Backend source revalidation on Python 3.13.12   PASS (1105 passed / 7 skipped)
SQLite migration consistency                    PASS
SQLite physical schema                          PASS
Repository policy                               PASS
Release consistency                             PASS
Direct dependency constraint structure          PASS (25 dependencies on 2808dd4...)
PostgreSQL governed H.1 behavior                PASS (57 passed)
Fresh PostgreSQL Alembic upgrade                RETEST REQUIRED after identifier repair
Fresh PostgreSQL physical schema/head           RETEST REQUIRED
ClamAV adapter compatibility                    PASS (11 passed on clamd 1.0.2)
Constrained dependency installation             FAILED on psycopg 3.2.0 candidate; RETEST REQUIRED after 3.2.2 repair
Frontend design/request-auth                    PASS on earlier candidate; current rerun required
Frontend TypeScript/build                       PASS on earlier candidate; current rerun required
Compiled frontend auth                          REPAIRED / RETEST REQUIRED
Frontend dependency security                    BLOCKED by known high/critical audit findings
GitHub Actions current-head execution           NOT YET PROVEN
Required-check/branch-protection enforcement    NOT YET VERIFIED
```

## 9. Acceptance state

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

Permanent sequencing remains:

```text
constrained dependency proof
→ fresh PostgreSQL migration/schema/H.1 proof
→ frontend security repair + frontend production proof
→ CI/settings evidence where available
→ reconcile ROADMAP / CHANGELOG / H.1 acceptance records
→ seal H.1 only if all required evidence is green
→ only then begin H.2
```

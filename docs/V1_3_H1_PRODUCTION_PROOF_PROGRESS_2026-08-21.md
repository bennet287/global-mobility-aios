# Global Mobility AIOS — V1.3-H.1 Production Proof Progress

**Evidence date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Original SQLite/backend candidate head tested:** `44744ca5d550c94dfd6809345a0f1052cb99dcf3`  
**PostgreSQL failure head tested:** `ad07f1e1416b7d524a880f3ca0596e8004ba5250`  
**Current repair candidate head:** `a192fafd9290013a7f99e946bb1f43c929760297`  
**Status:** PARTIAL PROOF RECORDED / POSTGRESQL RETEST REQUIRED / H.1 ACCEPTANCE STILL PENDING  
**Accepted baseline remains:** V1.3-G.5

This record captures real Human Owner local verification for the V12.18 H.1/Production Proof candidate. It does not seal H.1 and does not authorize H.2.

## Verified local evidence

### Full backend regression

Command:

```text
.\.venv\Scripts\python.exe -m pytest apps/api/tests -q
```

Result:

```text
1095 passed
5 skipped
1 warning
0 failed
duration = 417.39s
```

The single warning is the existing Starlette/httpx test-client deprecation warning:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

The full SQLite backend suite includes the canonical eligibility-lineage, G.3/G.4 replay, H.1 immune-system and adversarial lineage tests present in the original candidate. PostgreSQL-only contracts remain skipped unless `GMAI_TEST_DATABASE_URL` is set to a PostgreSQL database.

### Migration consistency

Command:

```text
.\.venv\Scripts\python.exe scripts/check_database_migrations.py
```

Result:

```text
Database migration check passed.
database_url = sqlite:///./gmai.db
migration_heads = 0077_canonical_eligibility_assessment_revision
registered_tables = 119
physical_schema = ok
database_revision = 0077_canonical_eligibility_assessment_revision
```

### Local physical schema

Command:

```text
.\.venv\Scripts\python.exe scripts/check_local_db_schema.py --database-url "sqlite:///D:/global-mobility-aios/gmai.db"
```

Result:

```text
Local DB schema check passed.
registered_tables = 119
actual_tables = 119
physical_tables = 120
infrastructure_tables = ["alembic_version"]
```

### Repository policy

Command:

```text
.\.venv\Scripts\python.exe scripts/check_repo_policy.py --root .
```

Result:

```text
Repository policy check passed.
```

This verifies the repository-policy lane after removal of the accidental `apps/api/=5.4` artifact and after adding suspicious redirection-artifact filename enforcement.

### Diff and branch hygiene

Commands:

```text
git diff --check
git status -sb
```

Result at the original evidence point:

```text
git diff --check = clean
roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
```

The connected GitHub repository independently resolved the same V12 branch head as:

```text
44744ca5d550c94dfd6809345a0f1052cb99dcf3
```

at the time the SQLite/backend evidence was recorded.

## PostgreSQL production-proof attempt — FAILED, REPAIRED, RETEST PENDING

The real PostgreSQL 16 governed eligibility/H.1 lane was then run on:

```text
ad07f1e1416b7d524a880f3ca0596e8004ba5250
```

Observed result:

```text
49 passed
8 failed
1 warning
duration = 908.01s
```

This is a real failed production-proof run and is intentionally retained in the acceptance trail.

### Failure class 1 — canonical governance outcome representation drift

The canonical lineage validator expected:

```text
outcome = auto_execute
```

while the sealed governance-kernel projection persists the enum value:

```text
outcome = AUTO_EXECUTE
```

That mismatch caused valid committed G.3/G.4/H.1 replay and cross-session reassessment paths to fail with:

```text
governance_payload_mismatch
```

Repair:

```text
78d310d6fa8c4dd5ba0eeea35ef726b24e4bd548
fix: align canonical governance outcome with persisted contract
```

The canonical validator now validates the persisted `AUTO_EXECUTE` contract rather than inventing a lowercase representation.

### Failure class 2 — adversarial test corruption violated PostgreSQL FK before H.1 could inspect it

Two H.1 tests replaced `semantic_activity_id` with a random UUID. SQLite permitted that synthetic tear, but real PostgreSQL correctly rejected it through:

```text
fk_eligibility_revision_semantic_activity_tenant
```

That meant the database constraint, rather than H.1, stopped the mutation.

Repair:

```text
ad2bd9a339601d6fb14d7b0404b9ab8129d32223
test: make H.1 lineage corruption PostgreSQL-valid
```

The adversarial mutation now cross-links the semantic slot to an existing same-tenant governance Activity. The row remains valid under the real composite FK, while the canonical lineage is semantically invalid. This preserves the intended proof boundary:

```text
PostgreSQL accepts referential identity
→ H.1 detects higher-order canonical lineage corruption
→ CRITICAL restrictive circuit opens
→ provider egress remains zero
```

### Failure class 3 — replay assertion targeted obsolete wording

The G.3 torn-governance replay test still matched the pre-consolidation prose `exactly one`, while shared canonical validation now exposes the stable failure code:

```text
governance_revision_cardinality
```

Repair:

```text
a192fafd9290013a7f99e946bb1f43c929760297
test: assert canonical replay cardinality failure code
```

The test now asserts the stable canonical lineage failure code instead of caller-era wording.

### Current repair state

The repair branch is three commits ahead of the failed PostgreSQL evidence head with only these bounded changes:

```text
apps/api/app/services/organization_eligibility_lineage.py
apps/api/tests/test_organization_eligibility_effect.py
apps/api/tests/test_organization_eligibility_immune_lineage.py
```

No migration, schema, authority model, orchestration architecture or broad refactor was introduced.

The current repair candidate must be retested before any PASS claim is made.

## What the evidence currently clears

The following H.1 Production Proof Gate items have real local evidence from the original candidate:

```text
full backend regression                         PASS on 44744ca5...
canonical-lineage/adversarial tests in suite    PASS on SQLite candidate
G.3/G.4 shared-lineage replay tests in suite    PASS on SQLite candidate
SQLite migration consistency                    PASS
local SQLite physical schema                    PASS
repository policy                               PASS
diff whitespace hygiene                         PASS
local/remote V12 branch synchronization         PASS at evidence point
```

The PostgreSQL lane is **not PASS**. It is:

```text
FAILED on ad07f1e...
→ targeted repairs pushed
→ RETEST REQUIRED on current repair head
```

No separate focused-count claim is invented beyond the command outputs actually supplied.

## Remaining acceptance proof

H.1 remains **IMPLEMENTED / ACCEPTANCE PENDING**. The remaining production-proof items are:

```text
PostgreSQL focused governed eligibility/H.1 retest on current repair head
SQLite focused regression for the three repaired files/contracts
release consistency check
Python direct-dependency constraint check
constrained dependency-install proof
frontend Node tests
TypeScript --noEmit
Next.js production build
compiled frontend auth tests
real PostgreSQL Alembic upgrade confirmation on retest database
real PostgreSQL physical schema/head verification on retest database
GitHub workflow execution evidence, where available
required-check / branch-protection enforcement verification or explicit repository-settings limitation record
```

Permanent sequencing remains:

```text
remaining Production Proof Gate
→ reconcile verified evidence
→ seal H.1 only if green
→ only then begin H.2
```

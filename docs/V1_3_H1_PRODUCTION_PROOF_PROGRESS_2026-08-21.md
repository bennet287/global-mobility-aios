# Global Mobility AIOS — V1.3-H.1 Production Proof Progress

**Evidence date:** 2026-08-21  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Candidate head tested:** `44744ca5d550c94dfd6809345a0f1052cb99dcf3`  
**Status:** PARTIAL PROOF RECORDED / H.1 ACCEPTANCE STILL PENDING  
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

The full SQLite backend suite includes the canonical eligibility-lineage, G.3/G.4 replay, H.1 immune-system and adversarial lineage tests present in the candidate. PostgreSQL-only contracts remain skipped unless `GMAI_TEST_DATABASE_URL` is set to a PostgreSQL database.

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

Result:

```text
git diff --check = clean
roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
```

The connected GitHub repository independently resolved the same V12 branch head as:

```text
44744ca5d550c94dfd6809345a0f1052cb99dcf3
```

at the time this evidence was recorded.

## What this evidence clears

The following H.1 Production Proof Gate items now have real local evidence:

```text
full backend regression                         PASS
canonical-lineage/adversarial tests in suite    PASS
G.3/G.4 shared-lineage replay tests in suite    PASS
SQLite migration consistency                    PASS
local SQLite physical schema                    PASS
repository policy                               PASS
diff whitespace hygiene                         PASS
local/remote V12 branch synchronization         PASS
```

No separate focused-count claim is invented because the user ran the complete backend suite rather than a separate focused command. The relevant focused tests are included in the 1095-pass full-suite result.

## Remaining acceptance proof

H.1 remains **IMPLEMENTED / ACCEPTANCE PENDING**. The remaining production-proof items are:

```text
release consistency check
Python direct-dependency constraint check
constrained dependency-install proof
frontend Node tests
TypeScript --noEmit
Next.js production build
compiled frontend auth tests
real PostgreSQL Alembic upgrade
real PostgreSQL physical schema/head verification
focused PostgreSQL governed eligibility/H.1 contracts
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

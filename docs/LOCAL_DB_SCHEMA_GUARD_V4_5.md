# Local DB Schema Guard v4.5

## Purpose

v4.5 adds a local database schema guard for SQLite demo/dev databases.

This fixes the operator experience around stale local databases. If a local `gmai.db` was created before newer columns were added, scripts can fail with errors such as:

```text
sqlite3.OperationalError: no such column: documents.storage_provider
```

The new checker reports schema drift clearly before a demo.

## New Script

```powershell
python scripts/check_local_db_schema.py
```

Machine-readable output:

```powershell
python scripts/check_local_db_schema.py --json
```

Inspect another DB:

```powershell
python scripts/check_local_db_schema.py --database-url "sqlite:///./apps/api/gmai.db"
```

## Healthy Output

```text
Local DB schema check passed.
```

## Drift Output

When the local SQLite file is stale, the script reports:

- missing tables
- missing columns
- masked database URL
- local demo recovery hint

Example:

```text
missing_columns={"documents": ["storage_provider", "file_hash", "..."]}
suggested_fix=Back up and remove the stale local SQLite database, then run `python scripts/seed_demo_data.py --reset-all --yes`.
```

## Recommended Demo Check

Before demo:

```powershell
python scripts/check_local_db_schema.py
python scripts/seed_demo_data.py --reset-all --yes
python scripts/check_demo_readiness.py
```

Expected:

```text
Local DB schema check passed.
"status": "ready"
```

## Safety

The checker is read-only. It does not alter tables, delete data, or run migrations.

For disposable local demo databases, rebuild the SQLite file. For production/PostgreSQL, use Alembic migrations instead.

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py scripts/check_demo_readiness.py scripts/check_local_db_schema.py scripts/check_database_migrations.py scripts/check_docker_profile.py
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py

$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

Expected test count increases by two.

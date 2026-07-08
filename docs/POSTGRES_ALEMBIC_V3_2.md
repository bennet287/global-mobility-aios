# PostgreSQL and Alembic v3.2

This milestone prepares the project for PostgreSQL while preserving the current SQLite-first local workflow.

## What Changed

- Added a database URL utility for:
  - `postgres://` to `postgresql+psycopg://` normalization.
  - SQLite detection.
  - safe database URL masking.
  - auto-create-table behavior.
- Added `DATABASE_AUTO_CREATE_TABLES`.
- Added `DATABASE_ECHO`.
- Added `alembic` to API requirements.
- Hardened Alembic `env.py` with:
  - normalized app database URL.
  - model registration before migration.
  - type/default comparison.
  - SQLite batch rendering support.
- Added `scripts/check_database_migrations.py`.
- Added regression tests for database URL and auto-create behavior.

## Important Behavior

SQLite remains simple for local development:

```text
DATABASE_URL=sqlite:///./gmai.db
DATABASE_AUTO_CREATE_TABLES unset
```

Result:

```text
The app auto-creates tables on startup.
```

PostgreSQL uses Alembic by default:

```text
DATABASE_URL=postgresql+psycopg://gmai:gmai_password@localhost:5432/gmai
DATABASE_AUTO_CREATE_TABLES unset or false
```

Result:

```text
The app does not auto-create tables.
Run Alembic migrations before starting the API.
```

## Local PostgreSQL Check

Start only Postgres:

```powershell
docker compose up -d postgres
```

Set the local database URL:

```powershell
$env:DATABASE_URL="postgresql+psycopg://gmai:gmai_password@localhost:5432/gmai"
$env:DATABASE_AUTO_CREATE_TABLES="false"
```

Run migrations from the repository root:

```powershell
python scripts/check_database_migrations.py
python -m alembic -c alembic.ini upgrade head
```

Seed demo data into PostgreSQL:

```powershell
python scripts/seed_demo_data.py --reset-all --yes
```

Run tests on SQLite as the default regression path:

```powershell
$env:DATABASE_URL="sqlite:///./gmai.db"
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py scripts/check_database_migrations.py
python scripts/check_repo_policy.py --root .
$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

## Production Rule

Do not use `SQLModel.metadata.create_all()` as the production PostgreSQL schema mechanism.

For PostgreSQL:

```text
Alembic owns schema creation and schema changes.
```

For local SQLite:

```text
Auto-create stays available for fast development and tests.
```

# FastAPI Lifespan Cleanup v4.8

## Status

Implemented as the final project-owned test warning cleanup after v4.7.

## Goal

Replace the deprecated FastAPI startup event decorator with a lifespan handler.

## Problem

FastAPI now warns when applications use:

```python
@app.on_event("startup")
```

The project used this hook to create local database tables during application startup.

## Change

`apps/api/app/main.py` now uses an `asynccontextmanager` lifespan handler:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
```

The app is configured with:

```python
app = FastAPI(..., lifespan=lifespan)
```

This preserves startup behavior while removing the deprecated FastAPI API.

## Regression Coverage

Added:

```text
apps/api/tests/test_fastapi_lifespan.py
```

The test verifies that the app has a lifespan context and that `main.py` no longer uses `@app.on_event`.

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/check_local_db_schema.py scripts/check_demo_readiness.py scripts/seed_demo_data.py scripts/check_database_migrations.py scripts/check_docker_profile.py
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py
python scripts/check_local_db_schema.py

$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

Expected:

```text
42 passed
```

The only remaining warning should be the external Starlette/TestClient `httpx` compatibility warning from the installed dependency stack.

# UTC Timestamp Cleanup v4.7

## Status

Implemented as a narrow warning-reduction and compatibility milestone after v4.6.

## Goal

Remove remaining project-owned `datetime.utcnow()` deprecation warnings from workflow tests without changing the stored database timestamp shape.

## Problem

Python now warns that `datetime.datetime.utcnow()` is deprecated. The project used it in workflow routers and the demo seed script for audit, update, review, and follow-up timestamps.

## Change

Each touched module now uses a local helper:

```python
def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

This keeps timestamps in UTC while preserving the existing naive `datetime` shape expected by the current SQLite/Alembic model layer.

Updated files:

- `apps/api/app/routers/truth_resolution.py`
- `apps/api/app/routers/application_draft_control.py`
- `apps/api/app/routers/application_engine.py`
- `apps/api/app/routers/authority_decision.py`
- `apps/api/app/routers/post_approval_onboarding.py`
- `apps/api/app/routers/document_verification.py`
- `apps/api/app/routers/client_communications.py`
- `scripts/seed_demo_data.py`

## Regression Coverage

Added:

```text
apps/api/tests/test_utc_timestamp_compat.py
```

The test verifies the timestamp helpers return `datetime` objects and preserve the current naive database timestamp shape.

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
40 passed
```

Remaining warnings should be limited mostly to FastAPI/TestClient lifecycle compatibility unless new third-party warnings are introduced.

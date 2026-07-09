# Pydantic Compatibility Cleanup v4.6

## Status

Implemented as a narrow compatibility hardening milestone after the local DB schema guard.

## Goal

Reduce noisy Pydantic v2 deprecation warnings in the regression suite without changing workflow behavior.

## Problem

Several router helpers used this pattern:

```python
getattr(model, "model_fields", getattr(model, "__fields__", {}))
```

Python evaluates function arguments before calling `getattr`, so the fallback expression touched `__fields__` even when `model_fields` existed. Under Pydantic v2 this produced repeated deprecation warnings during normal workflow tests.

## Change

The helpers now read `model_fields` first and only fall back to `__fields__` when needed:

```python
fields = getattr(model, "model_fields", None)
if fields is None:
    fields = getattr(model, "__fields__", {})
return set(fields.keys())
```

Updated modules:

- `apps/api/app/routers/truth_resolution.py`
- `apps/api/app/routers/application_lifecycle.py`
- `apps/api/app/routers/application_draft_control.py`
- `apps/api/app/routers/admin_ui_sync.py`
- `apps/api/app/routers/document_verification.py`
- `apps/api/app/routers/client_communications.py`
- `apps/api/app/routers/application_engine.py`
- `apps/api/app/routers/authority_decision.py`
- `apps/api/app/routers/post_approval_onboarding.py`

## Regression Coverage

Added:

```text
apps/api/tests/test_pydantic_compat.py
```

The test calls each compatibility helper against a SQLModel model and fails if the deprecated `__fields__` path is touched when `model_fields` is available.

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
39 passed
```

The remaining warnings are expected to come from timestamp and FastAPI lifespan deprecations, which should be handled separately.

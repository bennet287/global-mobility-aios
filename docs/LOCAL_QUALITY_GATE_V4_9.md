# Local Quality Gate v4.9

## Status

Implemented as a developer workflow hardening milestone after the warning cleanup work.

## Goal

Replace the repeated manual verification block with one project-owned command.

## New Script

```text
scripts/check_local_quality.py
```

The script runs:

1. `compileall`
2. repository policy check
3. database migration check
4. Docker production profile check
5. local DB schema check
6. pytest regression suite

## Usage

Run the complete gate:

```powershell
python scripts/check_local_quality.py
```

List the command plan without running it:

```powershell
python scripts/check_local_quality.py --list --json
```

Run static/local checks without pytest:

```powershell
python scripts/check_local_quality.py --skip-pytest
```

## Regression Coverage

Added:

```text
apps/api/tests/test_local_quality_gate.py
```

The tests verify:

- the quality gate includes all expected checks
- pytest runs with `PYTHONPATH=apps/api`
- `--skip-pytest` keeps the static checks and omits pytest

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/check_local_db_schema.py scripts/check_demo_readiness.py scripts/seed_demo_data.py scripts/check_database_migrations.py scripts/check_docker_profile.py scripts/check_local_quality.py
python scripts/check_repo_policy.py --root .
python scripts/check_local_quality.py --list --json
python scripts/check_local_quality.py
```

Expected:

```text
Local quality gate passed.
45 passed
```

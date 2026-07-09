# Demo Release v5.5

## Goal

v5.5 creates a named local demo release checkpoint for the Global Mobility AIOS MVP.

This milestone does not add new workflow behavior. It consolidates the demo-ready stack into a release check that operators can run before presenting.

## Added

- `scripts/check_demo_release.py`
- `apps/api/tests/test_demo_release.py`
- `docs/DEMO_RELEASE_V5_5.md`
- `docs/CHANGELOG.md`
- `scripts/check_local_quality.py` now syntax-checks `scripts/check_demo_release.py`.

## Release Check

Run the standard demo release check:

```powershell
python scripts/check_demo_release.py
```

Run with full pytest quality gate:

```powershell
python scripts/check_demo_release.py --full-quality
```

Run JSON output:

```powershell
python scripts/check_demo_release.py --json
```

## What It Verifies

- Required demo scripts exist.
- Required demo docs exist.
- Local quality commands pass.
- Demo readiness is `ready`.
- Demo snapshot status is `ready`.
- Demo runbook includes required routes.
- Safety rules remain explicit:
  - human review required
  - no automatic email
  - no WhatsApp auto-send
  - no application submission
  - no lead conversion

## Demo Stack Included

- v5.1 demo release runbook.
- v5.2 demo snapshot export.
- v5.3 demo command center.
- v5.4 readiness banner.
- v5.5 release checkpoint.

## Expected Verification

```text
57 passed, 1 warning
Local quality gate passed.
```

The remaining warning is the existing external Starlette `TestClient` warning.

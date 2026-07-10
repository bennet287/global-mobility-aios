# Demo Release Status Sync v5.9

## Goal

v5.9 updates the local demo release checker so it validates the current v5.8 demo release package.

This milestone does not add new workflow behavior. It keeps the release gate aligned with the demo stack after the duplicate-output guard, UX polish, and clean snapshot export work.

## Changes

- Updates `scripts/check_demo_release.py` to report `release_version` as `v5.8`.
- Requires the v5.6, v5.7, and v5.8 milestone docs in the release check.
- Verifies demo snapshot exports default to the ignored `demo_exports/` folder.
- Verifies local export and production env files stay ignored:
  - `.env.production`
  - `demo_exports/`
  - `demo-snapshot-*.md`
  - `demo-snapshot-*.json`
- Extends `apps/api/tests/test_demo_release.py`.
- Updates `docs/CHANGELOG.md`.

## Commands

Run the release checkpoint:

```powershell
python scripts/check_demo_release.py
```

Run the full local quality gate:

```powershell
python scripts/check_local_quality.py
```

Print release JSON:

```powershell
python scripts/check_demo_release.py --json
```

## Expected Verification

```text
Demo release v5.8: ready
quality_status=passed
demo_readiness=ready
snapshot_status=ready
runbook_status=ready
export_cleanup=ready
```

The standard local quality gate should continue to pass with only the existing external Starlette `TestClient` warning.

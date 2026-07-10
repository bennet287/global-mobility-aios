# MVP Release Hardening v6.0

## Goal

v6.0 adds one local release-hardening check for the Global Mobility AIOS MVP.

This milestone does not add new product behavior. It answers whether the local demo release is ready to present, hand over, or package.

## Added

- `scripts/check_mvp_release.py`
- `apps/api/tests/test_mvp_release.py`
- `docs/MVP_RELEASE_HARDENING_V6_0.md`
- `docs/CHANGELOG.md` update
- `scripts/check_local_quality.py` compile coverage for the MVP release checker

## What It Checks

- Required release files exist.
- The local git working tree is clean.
- Required demo release tags exist:
  - `demo-release-v5.6`
  - `demo-release-v5.7`
  - `demo-release-v5.8`
  - `demo-release-v5.9`
- Demo release status is ready.
- Demo readiness, snapshot, runbook, and export cleanup are ready.
- Safety state remains explicit:
  - no automatic sending
  - human review required
  - no automatic application submission
  - no automatic lead conversion

## Commands

Run the standard hardening check:

```powershell
python scripts/check_mvp_release.py
```

Run without local quality commands:

```powershell
python scripts/check_mvp_release.py --skip-quality
```

Run full local quality, including pytest:

```powershell
python scripts/check_mvp_release.py --full-quality
```

Print JSON:

```powershell
python scripts/check_mvp_release.py --json
```

## Expected Verification

After committing v6.0, run:

```powershell
python scripts/check_local_quality.py
python scripts/check_mvp_release.py
git status
```

Expected:

```text
Local quality gate passed.
MVP release v6.0: ready
nothing to commit, working tree clean
```

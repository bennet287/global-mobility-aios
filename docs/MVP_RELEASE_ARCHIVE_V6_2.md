# MVP Release Archive v6.2

## Goal

v6.2 adds a local archive exporter for packaging the MVP release handoff into one ignored zip file.

The archive is intended for local sharing, backup, or supervisor/demo handoff. It excludes local databases, `.env` files, caches, and runtime storage by design.

## Added

- `scripts/export_mvp_release_archive.py`
- `apps/api/tests/test_mvp_release_archive.py`
- `docs/MVP_RELEASE_ARCHIVE_V6_2.md`
- `.gitignore` safety for root-level `mvp-release-archive-*.zip`
- Compile coverage through `scripts/check_local_quality.py`

## Archive Contents

The default archive contains:

```text
release/mvp-release-bundle-v6.1.md
release/mvp-release-bundle-v6.1.json
metadata/manifest.json
project/docs/CHANGELOG.md
project/docs/DEMO_RELEASE_RUNBOOK_V5_1.md
project/docs/DEMO_SNAPSHOT_EXPORT_V5_2.md
project/docs/DEMO_READINESS_BANNER_V5_4.md
project/docs/DEMO_RELEASE_STATUS_V5_9.md
project/docs/AGENT_DUPLICATE_OUTPUT_GUARD_V5_6.md
project/docs/DEMO_UX_POLISH_V5_7.md
project/docs/DEMO_EXPORT_CLEANUP_V5_8.md
project/docs/MVP_RELEASE_HARDENING_V6_0.md
project/docs/MVP_RELEASE_BUNDLE_EXPORT_V6_1.md
project/docs/MVP_RELEASE_ARCHIVE_V6_2.md
```

## Commands

Create the default archive:

```powershell
python scripts/export_mvp_release_archive.py
```

Create and print manifest JSON:

```powershell
python scripts/export_mvp_release_archive.py --json
```

Use a custom filename routed into `release_exports/`:

```powershell
python scripts/export_mvp_release_archive.py --output supervisor-handoff.zip
```

## Output Path

Default output:

```text
release_exports/mvp-release-archive-v6.2.zip
```

The `release_exports/` directory is ignored, so archive generation should not dirty Git.

## Verification

Run after committing v6.2:

```powershell
python scripts/check_local_quality.py
python scripts/export_mvp_release_archive.py --json
git status
```

Expected:

```text
Local quality gate passed.
"status": "ready"
nothing to commit, working tree clean
```

## Safety

The archive exporter is read-only. It does not send messages, submit applications, convert leads, mutate documents, or modify workflow state.

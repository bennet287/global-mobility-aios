# GitHub Release Prep v6.3

## Goal

v6.3 adds a GitHub release readiness check for the sealed MVP release archive.

It verifies that the repository is clean, required release tags exist, release notes are present, and the v6.2 archive is available and internally valid.

## Added

- `scripts/check_github_release_ready.py`
- `apps/api/tests/test_github_release_ready.py`
- `docs/GITHUB_RELEASE_PREP_V6_3.md`
- `docs/RELEASE_NOTES_MVP_V6_2.md`
- Compile coverage through `scripts/check_local_quality.py`

## Readiness Check

Run after committing v6.3 and after generating the v6.2 archive:

```powershell
python scripts/check_github_release_ready.py
```

JSON mode:

```powershell
python scripts/check_github_release_ready.py --json
```

Expected state:

```text
GitHub release prep v6.3: ready
missing_tags=none
missing_docs=none
archive_status=ready
```

## Required Tags

```text
demo-release-v5.6
demo-release-v5.7
demo-release-v5.8
demo-release-v5.9
mvp-release-v6.0
mvp-release-v6.1
mvp-release-v6.2
```

## Required Local Archive

```text
release_exports/mvp-release-archive-v6.2.zip
```

The archive must contain:

```text
release/mvp-release-bundle-v6.1.md
release/mvp-release-bundle-v6.1.json
metadata/manifest.json
```

The manifest must report:

```text
status: ready
archive_version: v6.2
```

## Suggested Push Flow

```powershell
git status
python scripts/check_local_quality.py
python scripts/check_github_release_ready.py

git push -u origin feature/github-release-prep-v6.3
git push origin demo-release-v5.6 demo-release-v5.7 demo-release-v5.8 demo-release-v5.9 mvp-release-v6.0 mvp-release-v6.1 mvp-release-v6.2
```

Then create a GitHub release from tag:

```text
mvp-release-v6.2
```

Use:

```text
docs/RELEASE_NOTES_MVP_V6_2.md
```

as the release notes, and attach:

```text
release_exports/mvp-release-archive-v6.2.zip
```

## Safety

The readiness checker is read-only. It does not push, publish, send messages, submit applications, convert leads, or modify workflow state.

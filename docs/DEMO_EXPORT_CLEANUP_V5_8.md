# Demo Export Cleanup v5.8

## Goal

Keep the git working tree clean after local demo snapshot exports.

## Changes

- Adds ignored `demo_exports/` storage for generated demo artifacts.
- Ignores root-level `demo-snapshot-*.md` and `demo-snapshot-*.json` files as an extra safety net.
- Makes `scripts/export_demo_snapshot.py` write to `demo_exports/` by default.
- Routes bare output filenames such as `demo-snapshot-local.md` into `demo_exports/`.
- Adds `--stdout` for operators who want to print the snapshot instead of writing a file.
- Updates demo runbook and snapshot docs to use the clean export path.

## Commands

Export Markdown:

```powershell
python scripts/export_demo_snapshot.py --format markdown
```

Export JSON:

```powershell
python scripts/export_demo_snapshot.py --format json
```

Print instead of writing:

```powershell
python scripts/export_demo_snapshot.py --format markdown --stdout
```

## Verification

Run:

```powershell
python scripts/check_local_quality.py
python scripts/export_demo_snapshot.py --format markdown
git status
```

Expected:

```text
Local quality gate passed.
nothing to commit, working tree clean
```


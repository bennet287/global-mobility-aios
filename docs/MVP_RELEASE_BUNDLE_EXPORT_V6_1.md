# MVP Release Bundle Export v6.1

## Goal

v6.1 adds a local MVP release bundle exporter for handoff and demo records.

The exporter creates a concise Markdown or JSON bundle with release status, demo counts, audit highlights, key URLs, runbook flow, required tags, and safety rules.

## Added

- `scripts/export_mvp_release_bundle.py`
- `apps/api/tests/test_mvp_release_bundle.py`
- `docs/MVP_RELEASE_BUNDLE_EXPORT_V6_1.md`
- Ignored `release_exports/` storage for generated release bundles
- Root-level ignore safety net for:
  - `mvp-release-bundle-*.md`
  - `mvp-release-bundle-*.json`

## Commands

Export Markdown:

```powershell
python scripts/export_mvp_release_bundle.py --format markdown
```

Export JSON:

```powershell
python scripts/export_mvp_release_bundle.py --format json
```

Print without writing:

```powershell
python scripts/export_mvp_release_bundle.py --format markdown --stdout
```

Use a different local base URL:

```powershell
python scripts/export_mvp_release_bundle.py --base-url http://localhost:9000 --format markdown
```

## Output Paths

By default, exports are written under ignored `release_exports/` paths:

```text
release_exports/mvp-release-bundle-v6.1.md
release_exports/mvp-release-bundle-v6.1.json
```

Bare filenames passed through `--output` are also routed into `release_exports/`.

## Verification

Run:

```powershell
python scripts/check_local_quality.py
python scripts/export_mvp_release_bundle.py --format markdown
git status
```

Expected:

```text
Local quality gate passed.
MVP release bundle written to ...\release_exports\mvp-release-bundle-v6.1.md
nothing to commit, working tree clean
```

The bundle exporter does not send messages, submit applications, convert leads, or mutate workflow state.

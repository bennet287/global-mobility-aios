# Official-Source Truth Engine v3.4

This milestone upgrades the Truth Engine from source-aware verification to persistent official-source verification scaffolding.

## Scope

Added models:

| Model | Purpose |
|---|---|
| `OfficialSource` | Persistent official or trusted source inventory. |
| `SourceSnapshot` | Evidence record for a referenced or captured source state. |
| `SourceCheckRun` | Per-claim source verification run. |
| `VerifiedRule` | Future durable country/domain rule statements. |
| `CountryPolicy` | Country/domain verification policy metadata. |

Added routes:

```text
POST /api/v1/official-sources/seed
GET  /api/v1/official-sources
GET  /api/v1/official-sources/check-runs
GET  /api/v1/official-sources/policies
GET  /admin/official-sources
GET  /debug/official-sources
```

## Behavior

The existing truth endpoint still works:

```text
POST /api/v1/truth/verify
```

Now each verification also:

1. Seeds known official sources from `knowledge/official_sources/sources.yaml`.
2. Stores or reuses matching `OfficialSource` records.
3. Records a `SourceCheckRun`.
4. Records `SourceSnapshot` rows with `referenced` status.
5. Preserves the existing `TruthClaim`, `VerificationAudit`, and `SourceReference` behavior.

## Initial Countries

The v3.4 source inventory starts with:

```text
Germany
Austria
Canada
United Kingdom
Australia
```

This is intentionally small. Do not add broad country coverage until the verification workflow is stable.

## What This Is Not Yet

v3.4 does not fetch web pages, scrape official sites, run RAG, or compare full page text against claims.

Those come later. This milestone creates the durable records and operator surface needed before live retrieval is safe.

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py scripts/check_database_migrations.py scripts/check_docker_profile.py
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py
$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

Expected:

```text
Repository policy check passed.
Database migration check passed.
Docker production profile check passed.
All tests pass.
```

## Alembic

Migration added:

```text
apps/api/alembic/versions/0002_official_source_truth_engine.py
```

For PostgreSQL:

```powershell
python -m alembic -c alembic.ini upgrade head
```

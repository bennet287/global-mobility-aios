# PostgreSQL Backup + Isolated Restore v1

**Classification:** L SUPPORTING PARALLEL production foundation  
**Status:** IMPLEMENTED / REAL DOCKER RECOVERY PROOF PENDING  
**Acceptance effect:** does not seal L and does not replace the remaining professional-review, live-provider, provider-failure, or guarded fresh-retrieval evidence gates.

## Purpose

The production Docker profile stores canonical transactional state in PostgreSQL. A Docker volume is not a backup, and a successful `pg_dump` is not sufficient recovery proof by itself.

This capability therefore separates two operations:

1. create a portable PostgreSQL custom-format backup plus integrity manifest;
2. prove that exact manifested dump can be restored into a fresh, disposable, network-isolated PostgreSQL 16 container without touching the source database.

## Safety boundary

- The utility never runs `DROP DATABASE`, `DROP SCHEMA`, or `docker compose down -v` against the source stack.
- Restore verification targets only a newly created container named `gmai-restore-verify-*`.
- The restore container is created with Docker `--network none` and exposes no host port.
- The restore container is explicitly removed after verification; a success receipt is not written if cleanup fails.
- Backup artifacts and verification receipts are written beneath `backups/` by default; that directory is ignored by Git.
- The integrity manifest contains database/user/schema metadata but never the PostgreSQL password.
- The disposable restore password is generated per run and is not written to the receipt.
- Restore verification requires the companion manifest. An unmanifested dump is not accepted as recovery proof.

## Prerequisites

The production PostgreSQL service must already be running for backup creation:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d postgres
```

Docker must also be able to run the configured restore image. The default matches the production major:

```text
postgres:16-alpine
```

## Create a backup

```powershell
python scripts/postgres_backup_restore.py backup
```

Default outputs:

```text
backups/postgres/gmai-postgres-<UTC_TIMESTAMP>-<ID>.dump
backups/postgres/gmai-postgres-<UTC_TIMESTAMP>-<ID>.manifest.json
```

Before and after `pg_dump`, the utility reads the source `alembic_version` and public-table count. If either changes while the backup is being created, the dump is rejected and removed rather than being represented as a stable schema snapshot.

The companion manifest records:

- schema version and UTC creation time;
- backup filename, format, SHA-256 digest, and byte size;
- source Compose service, database, and PostgreSQL user;
- source `alembic_version`;
- source public-table count.

Alternative locations can be supplied explicitly:

```powershell
python scripts/postgres_backup_restore.py backup `
  --compose-file docker-compose.prod.yml `
  --env-file .env.production `
  --output-dir D:\gmai-backups\postgres
```

## Verify an isolated restore

Use the exact dump produced above:

```powershell
python scripts/postgres_backup_restore.py verify-restore `
  --backup D:\gmai-backups\postgres\gmai-postgres-<UTC_TIMESTAMP>-<ID>.dump
```

Verification performs this bounded sequence:

```text
verify backup exists and is non-empty
→ require and validate companion manifest
→ recompute SHA-256 and verify byte size/format
→ create fresh postgres:16-alpine container with --network none
→ wait for PostgreSQL readiness through docker exec
→ copy exact dump into disposable container
→ pg_restore --exit-on-error
→ compare restored public-table count to source manifest
→ compare restored alembic_version to source manifest
→ remove disposable container
→ only then write restore-verification receipt
```

Each successful verification writes an immutable receipt next to the dump:

```text
<backup-stem>.restore-verification-<VERIFICATION_ID>.json
```

A new receipt is created for each successful verification rather than overwriting prior recovery evidence. A successful receipt records the verification ID and time, backup creation time and digest, configured restore image plus the concrete Docker image ID, network mode, source/restored public-table counts, source/restored Alembic versions, manifest verification, isolation assertion, and `restore_verified=true`.

## Failure semantics

The utility fails closed when:

- the production Compose or env file is missing;
- the source PostgreSQL container does not expose the expected database/user variables;
- source schema metadata is missing or changes while the dump is being created;
- `pg_dump` fails or creates an empty dump;
- the companion manifest is absent, malformed, or mismatches filename, format, size, or SHA-256;
- the disposable PostgreSQL container does not become ready;
- `pg_restore --exit-on-error` fails;
- restored public-table count differs from the source manifest;
- restored `alembic_version` differs from the source manifest;
- the concrete restore-container image ID cannot be read;
- cleanup of an otherwise-successful disposable restore container fails.

A failed `pg_dump` or unstable-schema backup removes its partial `.dump`. A failed restore does not produce a success receipt.

## Verification during development

Unit coverage lives in:

```text
apps/api/tests/test_postgres_backup_restore_script.py
```

The tests cover backup/manifest creation, partial cleanup, post-dump metadata failure cleanup, schema-change rejection, mandatory-manifest behavior, digest tamper detection, required source metadata, network-isolated restore flow, source/restored schema-metadata parity, immutable receipt metadata, failure cleanup, and receipt suppression when cleanup fails.

A real recovery proof still requires executing the utility against Docker with a representative PostgreSQL backup. Unit/static tests alone are not a recovery claim.

## Roadmap relationship

This closes an implementation gap in the L supporting production foundation. It does **not** advance the project to M and does **not** change the L acceptance boundary. L remains `IMPLEMENTED / ACCEPTANCE PENDING` until its external evidence requirements are satisfied.

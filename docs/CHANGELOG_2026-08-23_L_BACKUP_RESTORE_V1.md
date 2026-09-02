# 2026-08-23 — L Supporting Production Foundation: PostgreSQL Backup + Isolated Restore v1

## Status

**IMPLEMENTED / REAL DOCKER RECOVERY PROOF PENDING**

This tranche advances the L supporting production foundation without changing the L acceptance boundary or authorizing milestone M.

## Added

- `scripts/postgres_backup_restore.py`
  - creates PostgreSQL custom-format backups from the production Compose `postgres` service;
  - records SHA-256, byte size, source `alembic_version`, and source public-table count in a mandatory integrity manifest;
  - rejects a backup if source schema metadata changes across the dump window;
  - restores only into a fresh disposable PostgreSQL 16 container with `--network none`;
  - requires restored table count and `alembic_version` to match the source manifest exactly;
  - records the concrete Docker restore image ID;
  - writes a new immutable restore-verification receipt only after successful container cleanup.
- `apps/api/tests/test_postgres_backup_restore_script.py`
  - backup/manifest creation and partial-backup cleanup;
  - source-schema drift rejection;
  - mandatory-manifest and digest-tamper rejection;
  - source metadata validation;
  - network-isolated restore and exact schema-metadata parity;
  - post-dump metadata failure cleanup;
  - failure cleanup and success-receipt suppression if cleanup fails.
- `docs/POSTGRES_BACKUP_RESTORE_V1.md`
  - safety boundary, commands, failure semantics, and proof distinction.
- `scripts/check_docker_profile.py`
  - production-profile gate requires the backup/restore capability, mandatory-manifest behavior, network isolation, and schema-parity proof markers.
- `infrastructure/deployment/README.md`
  - deployment target requires backup plus isolated restore verification rather than treating a volume or dump alone as recovery proof.

## Non-claims

This implementation does not claim:

- a real representative production backup has already been restored;
- a recovery-time or recovery-point objective has been measured;
- off-host retention, encryption-at-rest, rotation, or managed backup storage is implemented;
- L is sealed;
- M has started.

A real Docker recovery exercise remains required before this supporting capability can be called operationally proven.

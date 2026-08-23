# Deployment

Initial deployment target:

- Single VPS or local workstation
- Docker Compose
- Daily PostgreSQL backups with isolated restore verification
- Manual human approval for sensitive workflows

PostgreSQL backup/recovery operations are defined in:

```text
docs/POSTGRES_BACKUP_RESTORE_V1.md
scripts/postgres_backup_restore.py
```

A production volume is not treated as a backup. Recovery confidence requires a manifested portable dump plus a successful restore into a fresh disposable PostgreSQL container with no network access and source/restored schema-metadata parity.

Later:

- Kubernetes
- CI/CD
- Multi-tenant architecture
- Secrets manager
- Managed Postgres/Object storage

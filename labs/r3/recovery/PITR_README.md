# R3 Native PostgreSQL WAL-PITR

This experiment upgrades the recovery lane from logical restore plus event-log replay to a real PostgreSQL WAL point-in-time recovery fixture.

It uses PostgreSQL 16 with `wal_level=replica`, `archive_mode=on`, a local synthetic WAL archive, `pg_basebackup`, `recovery.signal`, `restore_command`, and `recovery_target_time`.

The synthetic case records a Human Review Required state, captures the exact database timestamp, then writes a later unauthorized synthetic mutation. Recovery must stop at the earlier timestamp and prove that the later mutation is absent while the retained-authority state is intact.

```powershell
python -m labs.r3.recovery.pitr_lab `
  --run-id recovery-wal-pitr-20260831-001 `
  --output labs/r3/recovery/results/recovery-wal-pitr-20260831-001.json

python -m labs.r3.common.verify_results labs/r3/recovery/results/*.json
```

This is still disposable R3 evidence. It does not prove production backup retention, object-storage durability, cross-region recovery, encryption/key recovery, or operational RPO/RTO.

# Native PostgreSQL WAL PITR

This is distinct from the logical `pg_dump/pg_restore` lab and from
`PITR_STYLE_EVENT_REPLAY`.

The executable experiment uses real PostgreSQL 16 continuous archiving:

```text
source cluster
  archive_mode=on
  archive_command → wal_archive/
       │
       ├─ pg_basebackup
       │
       ├─ commit HUMAN_REVIEW_REQUIRED
       │      ↓ target timestamp
       │
       └─ later destructive corruption
              status = CORRUPTED_SYNTHETIC
              rule.threshold = 999

base backup + archived WAL
       ↓
recovery.signal
restore_command
recovery_target_time
       ↓
new PostgreSQL instance
       ↓
exact target fingerprint
```

The recovered target must contain the Human Review state and rule 55 while
excluding the later corruption transaction. Authority remains RETAINED.

```powershell
python -m labs.r3.recovery.wal_pitr_lab `
  --run-id postgres-pitr-20260831-001 `
  --output labs/r3/recovery/results/postgres-pitr-20260831-001.json
```

The lab creates fresh Docker volumes and removes all containers/volumes at the
end. It contains only synthetic data. Cross-region/object-storage restore is a
separate operational exercise.

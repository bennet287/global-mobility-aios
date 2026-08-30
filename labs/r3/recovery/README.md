# R3 Recovery Lane

This lane separates actual PostgreSQL recovery proof from event-log
point-in-time reconstruction.

Run the disposable PostgreSQL service:

```powershell
docker compose -f labs/r3/infrastructure-compose.yml up -d postgres

python -m pytest labs/r3/recovery/tests -q

python -m labs.r3.recovery.recovery_lab `
  --run-id recovery-postgres-20260830-001 `
  --output labs/r3/recovery/results/recovery-postgres-20260830-001.json

python -m labs.r3.common.verify_results labs/r3/recovery/results/*.json
```

The executable lab uses real PostgreSQL 16 `pg_dump -Fc` and `pg_restore`,
then compares canonical row fingerprints, foreign-key relationship counts,
Activity ordering and VerifiedRule→Evidence lineage. It performs a destructive
source mutation after backup and proves the restored database remains identical
to the original snapshot.

The same fixture reconstructs aggregate state at exact timestamps from a durable
event log. That evidence is named `PITR_STYLE_EVENT_REPLAY`; it is **not**
native PostgreSQL WAL-PITR. Native WAL archive/restore and cross-service recovery
remain explicit gaps.

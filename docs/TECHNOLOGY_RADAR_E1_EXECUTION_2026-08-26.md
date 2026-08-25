# Track C — Technology Radar E1 execution

Date: 2026-08-26  
Base source head: `d861c5e2cdd34120e88c0e47f4bf3eab2c2a90fb`  
Status: **BOUNDED IMPLEMENTATION CANDIDATE / EXTERNAL PROOF PENDING**

## Purpose and boundary

E1 advances three production-foundation gaps that support L without changing the
product milestone:

```text
L execution correlation
+ recoverability readiness
+ secret lifecycle boundary
!= L acceptance
```

This work does not authorize an external action, move canonical truth into a vendor,
or start M. Technology availability remains distinct from AIOS authority.

## 1. OpenTelemetry correlation

The existing optional FastAPI/OTLP pilot now has an AIOS-owned correlation contract
for two fixed operations:

- `organization.mobility.live_provider_cycle`
- `organization.mobility.specialist.execute`

The allowlist is limited to root WorkItem, specialist WorkItem, execution attempt,
AgentRun and ActionOutput identifiers; position key; latency and retry counts;
fresh-snapshot count; bounded outcome; and full-L-candidate boolean. It has no API
for arbitrary payload attributes.

Telemetry startup, writes, and span shutdown fail open. They cannot replace or mask
the domain result. Tenant identifiers, prompts, provider responses, Evidence content,
secrets and personal case data are excluded.

Current evidence: focused unit and L runtime tests pass locally. An OTLP collector was
not configured and an exported end-to-end trace has not been sampled for leakage.

Advancement evidence still required:

1. export one guarded L cycle through an operator-managed OTLP endpoint;
2. verify root → specialists correlation and latency/retry fields;
3. sample the exported trace for protected-content absence;
4. demonstrate that disabling/replacing the backend leaves domain behavior unchanged.

## 2. PostgreSQL backup, PITR and restore

The existing utility retains its safer logical path:

```text
manifested custom pg_dump
→ disposable postgres:16-alpine
→ --network none
→ schema/Alembic parity
→ immutable verification receipt
```

E1 adds `pitr-preflight`, a read-only server configuration inspection. It checks the
PostgreSQL major and WAL/archive settings while withholding archive-command text. The
report deliberately marks base-backup, WAL-continuity and point-in-time-restore proof
false.

Current evidence: unit contract tests pass locally. A real Docker logical restore was
not rerun for this source state, and no PITR recovery was performed.

Advancement evidence still required:

1. select and pin pgBackRest or WAL-G-class tooling from measured deployment needs;
2. define RPO/RTO and off-host encrypted retention;
3. produce a representative base backup and prove continuous WAL archiving;
4. restore to an explicit time/transaction in an isolated target;
5. verify canonical data, schema and migration lineage, then retain a receipt;
6. define MinIO/object recovery separately—PostgreSQL recovery does not recover blobs.

## 3. SecretsPort / OpenBao pilot

E1 introduces a narrow AIOS-owned `SecretsPort` and a minimal OpenBao KV-v2 adapter.
The adapter:

- accepts references rather than repository-stored values;
- restricts the pilot to explicit non-production environments;
- requires HTTPS except for loopback development;
- uses KV-v2 versions and check-and-set rotation;
- supports soft deletion and undelete recovery;
- redacts material and token representations;
- omits response bodies from errors;
- grants no organizational authority.

The operator command is intentionally gated:

```powershell
python scripts/pilot_openbao_secrets.py --check-config
python scripts/pilot_openbao_secrets.py --run-lifecycle --confirm-nonproduction
```

Only generated sentinel values are used. A successful run verifies retrieval, CAS
rotation, soft delete, undelete recovery and metadata cleanup, and prints no secret.

Current evidence: adapter/lifecycle contracts pass against an in-process HTTP
transport. `--check-config` was run with the unconfigured defaults and correctly
reported `pilot_ready=false`. No live OpenBao server was contacted.

Advancement evidence still required:

1. run the lifecycle against an isolated non-production OpenBao instance;
2. retain server-side audit evidence without secret values;
3. prove token revocation and operator recovery, not only secret undelete;
4. define workload identity/short-lived authentication before production consideration;
5. migrate exactly one non-production credential path before considering broader use.

## 4. Other active radar pilots

E1 reviewed the active portfolio and did not manufacture work without a measured gap:

| Capability | Current state | E1 disposition |
|---|---|---|
| ClamAV | pilot complete / trial-eligible | keep bounded upload control; no state change |
| Promptfoo | pilot complete / trial-eligible | retain evaluation role; no state change |
| Docling | pilot in progress | continue independently |
| Presidio | queued pilot | do not pull ahead of the current privacy-processing need |
| urlwatch | queued pilot | keep behind governed source-monitor requirements |
| Langfuse | research / pilot candidate | only behind OpenTelemetry; no canonical truth |
| pgvector vs Qdrant | benchmark | no E1 storage migration |
| LLMLingua-2 | selected primary pilot | demand/integrity benchmark gated |
| Temporal / OpenFGA | deferred pilots | remain gap-triggered |
| DeepSeek Harness | donor candidate / assess | no L dependency or adoption |

## Verification recorded for this working tree

Observed local proof:

```text
30 focused telemetry / SecretsPort / backup-PITR / presence tests PASS
22 focused Austria objective / live-provider / fresh-retrieval tests PASS
targeted Python compilation PASS
OpenBao --check-config safe negative result PASS (pilot_ready=false)
backup utility CLI exposes pitr-preflight PASS
```

This is local working-tree proof, not Woodpecker proof and not exact-head acceptance.
The implementation remains uncommitted at the time this record is written.

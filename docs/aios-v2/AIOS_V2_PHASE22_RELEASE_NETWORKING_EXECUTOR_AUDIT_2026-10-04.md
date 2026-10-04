# AIOS V2 — Phase 22 Release/Networking Executor Audit

**Programme:** Phase 22 real production deployment acceptance / GRSI.E canary evidence
**Slice:** target-host `release_networking` satisfied-capable executor preflight
**Audit date:** 2026-10-04
**Exact audited integration head:** `7af2a44332e814f428ae01dd0f5f67c7d5147955`
**Current migration head:** `0100_phase22_release_networking_contract`
**Nature of this slice:** read-only ownership and execution-contract audit. No deployment, receipt write, migration, rollback, production-ready claim, or external action is performed.

---

## 1. Decision

Do not create another canary/deployment/receipt store.

The canonical durable path already exists:

```text
ProductionDeploymentAcceptanceRun
  -> ProductionDeploymentAcceptanceCheckReceipt
```

The existing receipt schema already supports:

```text
status = satisfied | failed | blocked | unknown
```

and already enforces one immutable receipt per tenant/run/gate.

The current foundation executor is intentionally unable to record `satisfied`. The missing component is therefore one stronger, narrowly-scoped **target-host release/networking executor contract**, not another persistence layer.

The first stronger executor may write only:

```text
gate_key = release_networking
```

It must not write the other five Phase 22 gates.

---

## 2. Existing owners to reuse

| Concern | Canonical owner | Rule |
| --- | --- | --- |
| Prepared candidate/rollback identity | `ProductionDeploymentAcceptanceRun` | Never reinterpret or mutate prepared identity. |
| Public networking contract | Phase 22 networking fields added by migration 0100 | Exact web/API hostnames, public IPv4, TCP allowlist and verifier key fingerprint remain authoritative. |
| External observations | protected GitHub-hosted Phase 22 verifier + signed manifest | Portable evidence only; no receipt authority. |
| Signature/identity/freshness interpretation | `verify_external_network_manifest()` | Reuse exactly; do not implement a second verifier in the target-host executor. |
| Release image identity | OCI labels + `production_release_identity.py` | Candidate and rollback image identity must match prepared SHA/config fingerprints. |
| Current target-host identity | `phase22_target_host_acceptance.py` host fingerprint | Must equal prepared target environment fingerprint. |
| Gate receipt | `ProductionDeploymentAcceptanceCheckReceipt` | Reuse immutable existing table. |
| Overall canary state | `project_deployment_acceptance_run()` | One satisfied release/networking gate does not make all Phase 22 gates satisfied. |

---

## 3. The existing foundation executor remains correct and must not be widened

Foundation v1 owns:

```text
actor    = phase22-target-host-foundation
contract = phase22.target-host-foundation.v1
statuses = blocked | failed | unknown
```

It verifies target-host identity and current candidate release labels, then records fail-closed evidence for all six gates.

It explicitly rejects `satisfied`.

Do not change that invariant. A stronger release/networking executor needs its own actor/contract identity and a separate internal receipt writer restricted to the one supported gate.

---

## 4. Immutable release tags already provide the switching primitive

Production application images are tagged by exact prepared identity:

```text
global-mobility-aios-api:<commit>-<configuration-fingerprint>
global-mobility-aios-web:<commit>-<configuration-fingerprint>
```

API, migration, worker and beat share the API image. Web uses the web image.

Each production image also contains immutable OCI labels:

```text
org.opencontainers.image.revision
com.global-mobility-aios.release-configuration-fingerprint
com.global-mobility-aios.release-identity-contract=phase22.release-identity.v1
```

This is sufficient to preflight both candidate and rollback images without rebuilding either release.

**Permanent rule:** the canary executor must use already-built immutable tags with `--no-build`. Rebuilding from current source during rollback would destroy the evidence chain.

---

## 5. Database schema rollback is not a valid primitive

Production startup normally executes:

```text
postgres healthy
  -> api-migrate: alembic upgrade head
  -> application services
```

That normal startup path must **not** be reused for application rollback.

Recent governed migrations explicitly refuse destructive downgrade when governed rows exist, including the GRSI, Phase 20, Phase 22 and networking owners. Examples include migrations 0091–0100.

Therefore:

> **The Phase 22 release/networking rollback contract must not run `alembic downgrade`, and must not run the rollback image's `api-migrate` service.**

An older rollback image may not even know the database's current Alembic revision. Running its `upgrade head` is not a rollback compatibility proof.

---

## 6. v1 rollback strategy: application rollback over retained forward schema

The first satisfied-capable release/networking executor should use:

```text
rollback_schema_strategy = forward_schema_retained
schema_downgrade_attempted = false
rollback_api_migrate_run = false
```

The database remains at the candidate/current forward schema throughout the drill.

The rollback release must prove that it can actually start and read the retained schema. If it cannot, the gate is not satisfied.

This is intentionally stricter than assuming migrations are backward compatible.

It also preserves the existing separation of concerns:

- `release_networking` proves exact release switching, restart, basic database-read compatibility and public networking;
- `core_journey` later proves the real synthetic application journey;
- `failure_recovery` later proves backup/restore and broader recovery;
- no one release/networking receipt claims full write-path compatibility or complete disaster recovery.

---

## 7. Rollback compatibility probe must execute inside the rollback API image

`/health` is insufficient because it is a shallow process endpoint and does not touch PostgreSQL.

The target-host executor should inject a bounded read-only Python probe into the **rollback API image itself**. That probe may use the rollback image's own:

- `app.core.db`;
- model registration;
- SQLModel metadata;
- SQLAlchemy inspector.

Minimum proof:

1. connect through the rollback image's production database configuration;
2. execute a read-only database connectivity query;
3. register the rollback image's own models;
4. confirm every table and column required by the rollback image exists in the live forward schema;
5. detect extra live columns on rollback-known tables that are non-null and have neither server default nor generated/identity semantics, because old inserts could be structurally impossible;
6. emit only redacted schema names/status, never row data or credentials.

This is a **read compatibility / structural insert-shape** check. It is not a claim that every old application write remains valid. Deeper behavior belongs to the other Phase 22 gates.

The probe should be supplied by the current trusted host executor as bounded stdin to `python -`; it must execute against modules installed in the rollback image. That avoids requiring historical rollback images to contain a newly introduced probe module and avoids mounting candidate application code over the rollback image.

---

## 8. Exact rollback configuration must be proven, not approximated

Using rollback image tags under only the candidate's current Compose file is not enough when the prepared rollback configuration fingerprint differs.

The executor must resolve the exact prepared rollback commit locally and verify:

```text
compute_release_configuration_fingerprint(rollback checkout)
  == prepared rollback_configuration_fingerprint
```

The rollback Compose model must come from that exact rollback revision.

A temporary detached Git worktree is acceptable because it is local release material, not external authority.

Before mutation:

- the rollback commit must already exist locally;
- the worktree must be detached and clean;
- its computed configuration fingerprint must match the prepared run;
- rollback API/web image tags must already exist locally;
- their OCI release labels must match the prepared rollback identity;
- no `docker build` or image pull may occur during the drill.

---

## 9. Preserve the current Compose project/network identity

Running Compose from a temporary rollback worktree can otherwise create a second project/network.

The executor must derive the current production Compose project identity from the running candidate containers' Docker Compose labels and require all governed application containers to agree.

Every rollback/restoration command must explicitly reuse that exact project identity.

The executor must not create parallel PostgreSQL/Redis volumes or a second production network.

---

## 10. Services switched by the release/networking drill

The rollback drill may switch only the application/networking services required by this gate:

```text
api
web
worker
beat
ingress
```

The drill must leave:

```text
postgres
redis
```

running on the existing project/volumes.

The executor must use `--no-deps` and `--no-build` so the rollback operation cannot:

- invoke `api-migrate`;
- rebuild candidate or rollback images;
- recreate PostgreSQL/Redis;
- silently pull a different application release.

Service order must be explicit and health-checked.

---

## 11. Candidate restart proof

Before rollback, the executor must prove the current running candidate identity exactly matches the prepared run.

It must then perform an actual candidate service restart/recreation without changing image identity and re-verify:

- API exact release/configuration OCI labels;
- web exact release/configuration OCI labels;
- worker and beat API-image labels;
- API local health;
- web local health;
- ingress still routes the candidate locally.

A no-op `docker inspect` is not restart evidence.

---

## 12. Actual rollback proof

The executor must then switch the bounded services to the exact prepared rollback release/configuration without running migrations.

After switch it must prove:

- rollback API/web/worker/beat exact labels;
- rollback Compose configuration fingerprint;
- rollback API and web become healthy;
- rollback read-only forward-schema compatibility probe passes;
- local ingress routes to the rollback web/API.

If any requirement fails, the gate cannot be satisfied.

---

## 13. Candidate restoration is mandatory and must be attempted in `finally`

The executor must restore the exact prepared candidate images/configuration even when the rollback validation raises an error.

Candidate restoration must verify:

- exact candidate release/configuration labels;
- API and web health;
- worker/beat running identity;
- current ingress configuration;
- local HTTPS/SNI routing for web and API.

A rollback drill that leaves the host on the rollback release can never create a satisfied receipt.

If restoration cannot be proven, fail the command and require operator intervention. Do not fabricate a receipt merely to record the failure.

---

## 14. Fresh external evidence must be post-restoration

The strongest evidence order is:

```text
candidate restart
  -> rollback
  -> rollback compatibility proof
  -> candidate restoration
  -> fresh protected external-network verifier
  -> target-host manifest verification
  -> immutable release_networking receipt
```

A manifest captured before rollback does not prove the final restored public state.

The target-host executor must therefore require the accepted external manifest's:

```text
observed_started_at >= candidate_restored_at
```

in addition to the existing API validator's signature, identity and freshness checks.

---

## 15. Do not put GitHub credentials on the VPS

The target host must not trigger or download the protected external verifier using a GitHub token.

Instead, the executor may use a bounded **wait-for-artifact** workflow:

1. perform candidate restart, rollback and candidate restoration;
2. record the in-process `candidate_restored_at` instant;
3. wait for a new envelope file at a caller-supplied path, with a bounded timeout;
4. operator/automation dispatches the protected main-branch workflow separately;
5. only the signed public evidence artifact is transferred to the target host;
6. executor validates the new artifact and requires its observation to begin after restoration.

The executor must reject an envelope file that existed before the drill or whose digest/timestamps do not satisfy the fresh post-restoration contract.

This keeps the private verifier key in GitHub and keeps GitHub credentials off the VPS.

---

## 16. Satisfied receipt writer boundary

The stronger internal writer should have a distinct identity, for example:

```text
actor    = phase22-target-host-release-networking
contract = phase22.target-host-release-networking.v1
gate     = release_networking only
```

It may accept `satisfied` only when a typed, internally-derived evidence object proves every v1 requirement.

It must reject:

- other gate keys;
- caller-supplied generic success booleans;
- candidate/host identity mismatch;
- missing rollback identity;
- any migration/downgrade attempt;
- rebuild/pull evidence;
- rollback compatibility failure;
- candidate restoration failure;
- external network failure;
- external manifest observed before candidate restoration;
- verifier signature/trust-root/provenance failure.

No public receipt write endpoint is added.

---

## 17. Receipt evidence should remain redacted but specific

A satisfied `release_networking` receipt should be able to carry bounded redacted evidence such as:

- executor contract/version;
- target environment fingerprint;
- candidate release/configuration identity;
- candidate image IDs;
- Compose project identity fingerprint;
- candidate restart timestamps/result;
- rollback release/configuration identity;
- rollback image IDs;
- forward-schema strategy and read-only probe result;
- `schema_downgrade_attempted=false`;
- `rollback_api_migrate_run=false`;
- candidate restoration timestamp/result;
- signed manifest SHA-256;
- verifier public-key fingerprint;
- verifier workflow/ref/commit/run ID/attempt;
- external observation timestamps;
- `network_contract_satisfied=true`;
- `secret_values_recorded=false`.

Never persist:

- passwords;
- private keys;
- tokens;
- database rows;
- full environment values.

---

## 18. Receipt satisfaction does not equal production readiness

Even a valid `release_networking=satisfied` receipt leaves five Phase 22 gates unresolved:

- identity/boundaries;
- core journey;
- documents/integrations;
- failure/recovery;
- operations.

The existing projection remains authoritative:

```text
all six gates satisfied -> canary_evidence_satisfied = true
```

Even then, the current Phase 22 projection still does not itself grant promotion or general production authority.

---

## 19. Migration decision

No migration is justified for this slice.

Existing `ProductionDeploymentAcceptanceCheckReceipt` already has the required durable fields and permits `satisfied`.

Migration head remains:

```text
0100_phase22_release_networking_contract
```

---

## 20. Next bounded implementation

**Phase 22 target-host release/networking executor v1**

Implementation order:

1. add typed release/networking evidence contract;
2. add a restricted internal `release_networking` receipt writer with its own actor/contract;
3. extend the existing target-host script with a separate satisfied-capable command;
4. implement exact candidate/rollback image and Compose-project preflight;
5. implement candidate restart;
6. implement rollback through exact rollback worktree/immutable images with no migration;
7. implement read-only forward-schema compatibility probe inside rollback API image;
8. restore candidate in a `finally` path;
9. wait for a new post-restoration signed verifier envelope;
10. reuse `verify_external_network_manifest()`;
11. require external observation start after restoration;
12. write one immutable `release_networking` receipt only if all checks pass.

Do not implement any other Phase 22 gate in this slice.

This audit does **not** claim that a live canary has been executed or that the product is production ready.

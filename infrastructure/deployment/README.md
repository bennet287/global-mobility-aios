# Deployment

Initial deployment target:

- Single VPS or local workstation
- Docker Compose
- Daily PostgreSQL backups with isolated restore verification
- Manual human approval for sensitive workflows

## Whole-product production acceptance

**Status: NOT YET VERIFIED ON A PRODUCTION HOST.** The workflow named `V12 Production Proof` is repository CI evidence: it checks code, isolated database contracts, builds and browser journeys, some of which use fixture API responses. It does not deploy the complete product to a VPS. A passing workflow must never be described as proof that AIOS is operating in production.

The intended first target is a single VPS running Docker Compose. Acceptance is tied to the exact deployed commit, concrete host and dated evidence. Run the following gates against the actual deployed services with synthetic cases and documents before admitting real client data or enabling consequential automation:

| Gate | Required evidence on the target VPS |
| --- | --- |
| Release and networking | Reproducible image/build identities and migrations at the deployed commit; HTTPS browser access to the web UI and API through the intended ingress; only intended ports externally reachable; startup, restart and rollback demonstrated. |
| Identity and boundaries | Real browser sign-in, session expiry, role denial, CORS and secure cookie behavior; disabled header-role bypass; no default credentials or secret values in client assets, logs or broadly shared container environments. |
| Core journey | A synthetic user/case follows the actual web → API → PostgreSQL → worker/beat → web path; durable state and audit evidence survive restart; an authorized and a denied action behave as governed. Test each promoted product capability through its real dependencies, recording unsupported or disabled capabilities explicitly. |
| Documents and integrations | Upload, configured scan policy, private encrypted object write, controlled read, expiry/revocation and deletion/retention against the real configured object store; verify official-source and provider integrations with actual endpoints and credentials where those capabilities are enabled. A consumer chat subscription is not an API credential. |
| Failure and recovery | Prove PostgreSQL backup and isolated restore from a real deployment backup, plus object-store backup and recovery for documents; exercise database, Redis, object-store, worker and external-provider outages, then confirm bounded failure behavior and recovery without silent loss or duplicate consequential action. |
| Operations | Observe real service health, logs, metrics/alerts, capacity and costs; test incident response, credential rotation/revocation, restore ownership and a dated recovery drill. Preserve human approval and authority gates; keep paid autonomous execution off until the monetary ceiling is genuinely enforceable. |

Record a pass/fail/blocked result and redacted evidence for each gate. A capability with missing external access, unavailable vendor billing evidence, or an unexercised recovery path stays **unverified/disabled**, even if its unit and CI tests pass. A failed gate blocks the production-ready claim; do not convert a fixture, static check, or local simulation into a live-host receipt.

### Current repository blockers (inspection at 2026-09-28, integration branch)

- The production profile now includes a Caddy ingress configuration for separate web/API hostnames, but no public certificate, HTTPS browser journey, DNS, host firewall or target-host networking proof exists. Direct web/API host ports are loopback diagnostics.
- API production startup requires a configured MinIO/S3-compatible document backend with TLS, non-default credentials, a preprovisioned private bucket and server-side encryption. Compose does not start that dependency. The example requires an external endpoint and leaves backup/recovery declarations empty; the synthetic probe in `docs/DOCKER_PRODUCTION_PROFILE_V3_3.md` must be run on the target host, followed by separate privacy, backup/restore and document-journey proof.
- The existing `SecretsPort` now backs one bounded production runtime-secret mount at `/run/secrets/aios`. Production Compose passes references rather than values for the database password, JWT signing, automation connector encryption and webhook authentication, MinIO access/secret keys, document-access token signing, and DeepSeek/Moonshot/Gemini provider keys. PostgreSQL reads the same database-password file via `POSTGRES_PASSWORD_FILE`; PostgreSQL, migration, API and worker mount the host directory read-only with host-path auto-creation disabled. Configured application references are authoritative and missing, empty, oversized, non-UTF-8, out-of-scope and symlink-escape files fail closed. API startup and a fail-closed worker-container preflight verify all seven mandatory shared refs before traffic or task execution. The canonical `Settings` access path re-resolves governed refs rather than caching or falling back to plaintext. JWT-file replacement invalidates sessions signed with the prior key; document-token replacement invalidates outstanding tokens; webhook verification observes replacement on the next request. Newly-created MinIO clients observe current credential files, while an already-created client retains its original credentials. LLM provider keys resolve through the same `SecretsPort` when provider clients are constructed. These rotation/revocation semantics still need target-host proof.
- Automation connector encryption has active and optional previous-key file references plus a production PostgreSQL maintenance command to check, atomically re-encrypt and verify every connector row under the active key. `docs/DOCKER_PRODUCTION_PROFILE_V3_3.md` owns its backup, service-quiescence and target-host procedure. No target-host rotation has been performed here; retain both keys until that proof passes. The API bootstrap admin password resolves from a bounded file reference on each login; the worker does not receive it. The database password is no longer in Compose environment metadata, but replacing its file does not rotate an existing PostgreSQL role; a coordinated host rotation/reconnection procedure and proof are still required. A general secrets-manager/workload-identity authority is also open. OpenBao remains a non-production pilot rather than a production authority.
- The existing PostgreSQL backup utility describes a real isolated restore, but its unit tests and the current workspace do not establish a dated restore on the target VPS. Object-store backup/recovery needs its own proof.
- No production VPS, production configuration, or Docker engine is available in the current execution workspace. The host-level gates above cannot be marked passed here.

Resolve the deployment topology and these blockers in bounded implementation slices; then deploy a release candidate on the actual VPS and run the whole-product gate. Do not treat the eventual presence of an OpenBao server or a green CI run as a substitute for live end-to-end evidence.

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

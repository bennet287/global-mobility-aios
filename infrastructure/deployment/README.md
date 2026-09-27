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

### Current repository blockers (inspection at 2026-09-27, after PR #231)

- The production profile now includes a Caddy ingress configuration for separate web/API hostnames, but no public certificate, HTTPS browser journey, DNS, host firewall or target-host networking proof exists. Direct web/API host ports are loopback diagnostics.
- API production startup requires a configured MinIO/S3-compatible document backend with TLS, non-default credentials, a preprovisioned private bucket and server-side encryption. Compose does not start that dependency. The example now requires an external endpoint and leaves backup/recovery declarations empty; the synthetic probe in `docs/DOCKER_PRODUCTION_PROFILE_V3_3.md` must be run on the target host, followed by separate privacy, backup/restore and document-journey proof.
- The production example still injects one `.env.production` into several containers. Per-service credential scope, production secret loading and rotation need implementation and live verification.
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

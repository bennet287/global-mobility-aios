# Deployment

Initial deployment target:

- Single VPS or local workstation
- Docker Compose
- Daily PostgreSQL backups with isolated restore verification
- Manual human approval for sensitive workflows

## Exact release identity before target-host acceptance

Production application images must be built from a clean Git checkout through the canonical helper:

```bash
python scripts/production_release_identity.py show --json
python scripts/production_release_identity.py build --env-file .env.production
```

The helper derives the exact 40-character Git commit and a deterministic SHA-256 fingerprint over the tracked production build/deployment inputs, then injects both into the API and web-derived images as OCI/custom image labels. Production Compose also tags those application images with the full commit plus configuration fingerprint, so a previously accepted release remains addressable as a concrete rollback image instead of being represented only by a mutable service tag. The all-zero values in `.env.production.example` exist only so static Compose validation can resolve the example file; they are not valid deployment evidence.

This release identity is necessary but not sufficient for canary or production acceptance. A target-host acceptance executor must still inspect the **running** container/image labels and compare them with the prepared deployment-acceptance run, observe migration/health/networking behavior, and record immutable receipts. A successful image build or matching label alone is not a deployment, rollback or production-readiness claim.

### Phase 22 target-host foundation executor

The first target-host executor contract is deliberately fail-closed. It can establish a deterministic host fingerprint, verify that the four long-running application containers are running the exact prepared release/configuration identity, and persist immutable evidence for the six existing Phase 22 gates. **Foundation v1 cannot record a satisfied gate.** Every receipt it writes is `blocked`, `failed`, or `unknown`; there is no public receipt-write endpoint.

Before preparing the deployment-acceptance run on the same VPS, derive the host fingerprint:

```bash
python scripts/phase22_target_host_acceptance.py fingerprint --json
```

After the prepared run exists and the exact candidate images are running:

```bash
python scripts/phase22_target_host_acceptance.py record-foundation \
  --run-id <deployment-run-uuid> \
  --tenant-key default \
  --json
```

The command independently recomputes the host fingerprint and inspects the running API, web, worker and beat image labels. If either host identity or release identity differs from the prepared run, it exits without creating receipts. On an exact match it records six **blocked** receipts describing which gate-specific probes are still absent. The host fingerprint is a deterministic operational identity hash, not cryptographic remote attestation; the host operator remains inside the trust boundary. Because receipts are immutable per run/gate, a foundation run that records blocked receipts is not later upgraded in place to a passing canary; prepare a new run after satisfied-capable gate executors have been implemented.

### Phase 22 release/networking executor v2

After the signed external-network verifier workflow is operational on protected `main`, a **fresh** prepared deployment-acceptance run may exercise the satisfied-capable release/networking drill.

The executor must itself run from a clean trusted `main` management checkout. Keep two persistent, clean release checkouts on the target host:

- the exact candidate commit/configuration named by the prepared run;
- the exact rollback commit/configuration named by the prepared run.

Do not place `.env.production` inside either release checkout; pass its protected host path explicitly.

Before executing, both exact candidate and rollback API/web image tags must already exist locally with the canonical release labels. The executor does not build or pull a different release during the drill.

Run:

```bash
python scripts/phase22_target_host_acceptance.py record-release-networking \
  --run-id <fresh-deployment-run-uuid> \
  --tenant-key default \
  --external-network-envelope /secure/evidence/envelope.json \
  --env-file /secure/config/.env.production \
  --candidate-root /srv/aios/releases/<candidate-sha> \
  --rollback-root /srv/aios/releases/<rollback-sha> \
  --json
```

The v2 executor:

1. verifies its clean `main` management checkout;
2. verifies both release checkouts and deterministic configuration fingerprints;
3. validates the signed external-network manifest through the existing Phase 22 validator and requires the protected `refs/heads/main` verifier provenance;
4. verifies target-host identity, candidate running identity, and exact candidate/rollback image labels;
5. restarts the candidate application/ingress and re-proves health/identity;
6. records a read-only database compatibility baseline;
7. retains the candidate's forward schema; never runs rollback `api-migrate` or schema downgrade;
8. switches API/web/worker/beat/ingress to the exact rollback release using the same observed Compose project, without rebuilding images or recreating PostgreSQL/Redis;
9. requires rollback health, exact labels, unchanged Alembic revision, model/schema compatibility, and unchanged stable lead-row count;
10. restores the exact candidate application/ingress without running migrations;
11. re-proves candidate health/identity/schema/data compatibility;
12. waits for a newly transferred signed envelope whose observation started after restoration, then verifies the final public network;
13. writes exactly one immutable existing `release_networking` receipt.

A failed rollback is recorded as failed evidence after candidate restoration is proven. Unverified restoration stops without writing a receipt and requires operator intervention. The database retains the already applied forward schema throughout the drill. Both application switches disable builds, pulls and dependency recreation.

The initial envelope is preflight evidence only. After the executor reports the restoration timestamp on stderr, dispatch the protected verifier separately and atomically replace the envelope at the supplied path. Its signed observation must begin after that timestamp. The executor waits for at most `--timeout-seconds` (30–900 seconds) and fails closed on missing, stale or failed evidence. GitHub credentials and the signing private key remain off the target host.

A foundation-v1 `release_networking=blocked` receipt cannot be upgraded. Use a fresh prepared run because Phase 22 receipts are immutable per run/gate.

Even a satisfied `release_networking` receipt is **not** production authorization or GRSI promotion. The other five Phase 22 gates remain separately required.

### Phase 22 identity-boundaries executor

The identity executor uses the existing prepared run and immutable receipt owner. Run it from a clean trusted `main` management checkout on the target VPS, with the exact candidate checkout and running release, a fresh `identity_boundaries` gate, controlled bootstrap credentials and the intended HTTPS web/API origins. A previous foundation or failed identity receipt cannot be upgraded; prepare a fresh run for a retry.

The management process needs the existing API Python dependencies and a governed connection to the canonical deployment-acceptance database, plus read access to the configured host secret scopes and Docker. Keep connection credentials and configuration outside the clean release/management checkouts. Bootstrap material is resolved privately from the deployed file reference; do not put passwords or cookies in command arguments.

Install the repository's `apps/web/e2e` Node dependencies and its Playwright Chromium runtime as a separate management-tooling step. The probe does not install tooling, disable certificate validation, provision credentials, rotate secrets, change the deployed session TTL or alter the server clock. The browser uses actual ingress responses without fixture routing. Missing tooling or incompatible SameSite/CORS topology prevents satisfaction.

```bash
python scripts/phase22_identity_boundaries.py \
  --run-id <fresh-deployment-run-uuid> \
  --tenant-key default \
  --candidate-root /srv/aios/releases/<candidate-sha> \
  --secrets-root /etc/global-mobility-aios/runtime-secrets \
  --max-wait-seconds 28920
```

Choose an explicit wait budget that covers the unchanged deployed session TTL and probe overhead. The default session lifetime is eight hours; expiry proof genuinely waits for the issued session to expire. Keep the candidate and credentials stable for that observation. No partial receipt is upgraded after waiting.

The executor checks exact prepared run, host, checkout and running release identities before probing, then exercises real form login and the cockpit's compiled organization-activities request. It pairs authenticated access with anonymous, forged-header and signed restricted-role denials; checks cookie scope, flags and lifetime, approved/denied CORS, and default/invalid login rejection; observes real expiry and replays the original expired token alongside a fresh successful login. It also checks bounded deployed mount, read-denial, reference, environment, client-asset, rendered-page and interval-log surfaces. Final identity and configuration checks must still succeed before a satisfied receipt is written.

Credentials, signing material and cookies stay in private bounded execution memory, including browser-helper stdin. The probe exports no screenshots, traces, HAR or storage state. Persistent evidence contains fixed proof fields, surface-contract identifiers, counts, observation times and bounded failure identifiers. Finite literal scans do not establish universal secret absence: transformed values, unobserved logs and other surfaces remain outside the contract. The host operator and trusted management checkout remain inside the trust boundary; this is operational evidence, not remote attestation.

A nonzero exit indicates incomplete or failed proof. Read the canonical receipt status; an identity mismatch may stop without writing a receipt. Even a satisfied identity receipt proves neither independent per-user role assignment nor credential rotation, whole-product readiness, six-gate acceptance, canary qualification or GRSI promotion. The bootstrap holder currently selects a signed role. Paid autonomous execution remains off.


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
- API production startup requires external document storage: either a TLS MinIO/S3-compatible backend with non-default credentials, private bucket and SSE-S3, or the native OCI instance-principal backend with a private Standard bucket. Compose does not start that dependency. The example defaults to S3 and leaves backup/recovery declarations empty; the synthetic probe in `docs/DOCKER_PRODUCTION_PROFILE_V3_3.md` must be run on the target host, followed by separate privacy, backup/restore and document-journey proof.
- An optional OCI native Object Storage pilot path now uses instance-principal identity with a preprovisioned private Standard bucket, bypassing the unsupported S3 SSE-S3 and `GetBucketPolicy` calls. Its repository tests are code-level only. Target-host identity, bucket access, anonymous-read denial, encryption configuration, backup/recovery and document-journey proof remain blocked without an OCI instance; see the canonical production profile for the procedure.
- The existing `SecretsPort` resolves scoped production credential-directory mounts below `/run/secrets/aios`. Production Compose passes references rather than values for the database password, JWT signing, automation connector encryption and webhook authentication, optional MinIO access/secret keys, document-access token signing, and DeepSeek/Moonshot/Gemini provider keys. PostgreSQL reads the same database-password file via `POSTGRES_PASSWORD_FILE`; PostgreSQL and migration mount only `database`; API and worker mount their currently required shared scopes, and only API mounts `bootstrap`. Beat, web, ingress and Redis receive no AIOS credential-directory mount. Scope directories are read-only with host-path auto-creation disabled. Configured application references are authoritative and missing, empty, oversized, non-UTF-8, out-of-scope and symlink-escape files fail closed. API startup and a fail-closed worker-container preflight verify five mandatory shared refs plus both MinIO refs when that backend is selected. The canonical `Settings` access path re-resolves governed refs rather than caching or falling back to plaintext. JWT-file replacement invalidates sessions signed with the prior key; document-token replacement invalidates outstanding tokens; webhook verification observes replacement on the next request. Newly-created MinIO clients observe current credential files, while an already-created client retains its original credentials. LLM provider keys resolve through the same `SecretsPort` when provider clients are constructed. These rotation/revocation semantics still need target-host proof.
- Automation connector encryption has active and optional previous-key file references plus a production PostgreSQL maintenance command to check, atomically re-encrypt and verify every connector row under the active key. `docs/DOCKER_PRODUCTION_PROFILE_V3_3.md` owns its backup, service-quiescence and target-host procedure. No target-host rotation has been performed here; retain both keys until that proof passes. The API bootstrap admin password resolves from `bootstrap/admin_password` on each login; the worker receives no bootstrap mount or admin-password environment reference. Existing hosts must move the previous `auth/admin_password` file and update its reference without leaving a copy in shared `auth`, as specified in the production profile. Actual workload read denial still requires target-host proof. The database password is no longer in Compose environment metadata. A production connection probe and coordinated PostgreSQL role-password procedure now cover staged file verification, role change, client restart and old-password rejection, but neither has been performed on the target VPS. A general secrets-manager/workload-identity authority is also open. OpenBao remains a non-production pilot rather than a production authority.
- The existing PostgreSQL backup utility describes a real isolated restore, but its unit tests and the current workspace do not establish a dated restore on the target VPS. Object-store backup/recovery now has a provider-neutral verification contract in `docs/DOCUMENT_STORAGE_BACKUP_RECOVERY_V1.md`; it still needs a real provider backup restored to a separate target and a dated target-host evidence bundle.
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

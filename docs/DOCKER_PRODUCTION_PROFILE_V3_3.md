# Docker Production Profile — Current Baseline

This file remains the canonical Docker production-profile owner. The filename is retained from the original v3.3 API/PostgreSQL milestone so the repository does not grow a parallel deployment document for every later service addition.

## Current Scope

Included in `docker-compose.prod.yml`:

- PostgreSQL 16 with persistent production volume and healthcheck;
- PostgreSQL without a published host port; the backup utility operates through `docker compose exec`;
- one-shot Alembic migration gate (`api-migrate`) before API/worker startup;
- Redis with persistent append-only storage;
- FastAPI service with production healthcheck;
- Celery worker and beat services;
- Next.js web service built from the explicit `production` Docker target;
- browser-public API origin supplied at image build time through `NEXT_PUBLIC_API_BASE_URL`;
- web-to-API startup dependency on the API health gate;
- API and web host ports bound to IPv4 loopback for local diagnostics;
- Caddy ingress for separate web and API hostnames, with public HTTP/HTTPS ports and persisted certificate storage;
- no `.env.production` injection into the web container, keeping database, signing, storage, and provider secrets out of the frontend runtime;
- PostgreSQL receives its database identity and a password-file path; the migration container receives a passwordless database URL plus a reference to the same password file. Compose still uses `.env.production` for interpolation;
- Celery beat receives only the production flag, Redis broker URL and scheduler-only switch; it does not import task modules or receive database credentials. The worker handles database and external actions with its own runtime configuration;
- one bounded read-only AIOS runtime-secret mount at `/run/secrets/aios` for PostgreSQL, migration, API and worker, with host-path auto-creation disabled;
- JWT signing, API bootstrap admin login, automation connector encryption, automation webhook authentication, optional MinIO access/secret keys, document-access signing, and remote-provider credentials supplied to application code through `*_REF` references rather than their secret values in Compose environment metadata;
- the worker receives an explicit database/broker, document, provider and automation allowlist from Compose interpolation, excluding API login credentials and browser/ingress configuration; optional settings absent from the host env keep application defaults;
- the API uses the same shared runtime allowlist plus login, CORS, telemetry and upload-scan settings; it no longer loads every value in `.env.production` into its container;
- static production-profile validation through `scripts/check_docker_profile.py`.

The same `apps/web/Dockerfile` retains a separate `development` target. `docker-compose.yml` explicitly selects that target, so local hot-reload behavior is not coupled to the production image.

Not included in the production Compose yet:

- MinIO document-storage service;
- Qdrant;
- n8n;
- Ollama/local-model runtime;
- live DNS, certificate issuance, ingress routing and TLS verification on the target VPS;
- a general production secrets manager/workload-identity authority beyond the bounded host-file secret mount and the OCI pilot's storage-specific instance principal;
- target-host evidence for the database-wide connector credential rotation procedure;
- Kubernetes or another production orchestrator;
- a real hosted deployment target and live post-deployment acceptance evidence.

Those are separate production-acceptance slices. A passing Docker/CI profile proves deployability of this bounded container contract; it does **not** by itself prove a live production deployment.

Only ingress publishes public ports 80 and 443; web and API retain loopback diagnostic ports, and PostgreSQL has no host port. Do not publish ports 3000, 8000 or 5432 through firewall or alternate Docker overrides. Caddy reaches the web and API by Compose service names. Binding internal services to loopback is one network boundary, not a substitute for target-host firewall or live TLS verification.

## Production Web Configuration

`NEXT_PUBLIC_API_BASE_URL` is browser-visible and is compiled into the Next.js client bundle during the image build. It must therefore be the API origin that an end-user browser can reach.

Examples:

```text
NEXT_PUBLIC_API_BASE_URL=https://api.example.com
CORS_ALLOWED_ORIGINS=https://app.example.com
```

Do not use Docker-internal names such as `http://api:8000` for `NEXT_PUBLIC_API_BASE_URL`; a remote browser cannot resolve the Compose service name.

The production web service intentionally does not load `.env.production`. Only public frontend values are passed to it. Server-only credentials remain on the API/worker side.

## First Run

Create the production env file:

```powershell
Copy-Item .env.production.example .env.production
```

Replace every relevant `change-this-*` placeholder before starting. At minimum configure the database/admin/browser settings plus the runtime-secret directory and required references:

```text
POSTGRES_USER
POSTGRES_DB
DATABASE_URL
DATABASE_PASSWORD_REF
AUTH_ADMIN_PASSWORD_REF
CORS_ALLOWED_ORIGINS
NEXT_PUBLIC_API_BASE_URL
WEB_DOMAIN
API_DOMAIN
AIOS_SECRETS_DIR
JWT_SECRET_REF
AUTOMATION_ENCRYPTION_KEY_REF
AUTOMATION_WEBHOOK_SECRET_REF
DOCUMENT_ACCESS_TOKEN_SECRET_REF
```

The MinIO/S3 backend additionally requires `MINIO_ACCESS_KEY_REF` and `MINIO_SECRET_KEY_REF`. The OCI backend instead requires `OCI_REGION`, `OCI_NAMESPACE`, and `OCI_BUCKET_DOCUMENTS` plus instance-principal access on the target host.

Provision `AIOS_SECRETS_DIR` on the target host before Compose starts. Keep the directory private (for example mode `0700`) and each active secret file readable only by the intended host operator/container path (for example mode `0600`). The example uses this layout:

```text
runtime-secrets/
  database/postgres_password
  auth/jwt_secret
  auth/admin_password
  automation/encryption_key
  automation/webhook_secret
  storage/minio_access_key
  storage/minio_secret_key
  documents/access_token_secret
  llm/deepseek_api_key
  llm/moonshot_api_key
  llm/gemini_api_key
```

Only provision provider files for providers that are actually enabled. The application accepts only bounded absolute `file:///run/secrets/aios/...` references under the mounted root; missing, empty, oversized, non-UTF-8, out-of-scope and symlink-escape references fail closed. API startup resolves its admin-password reference plus five shared database-password, JWT, automation encryption, webhook and document-access refs before serving; the two MinIO key refs are additionally required when `DOCUMENT_STORAGE_BACKEND=minio`. The worker uses the same shared backend-dependent rule. Alembic builds its database connection from the passwordless `DATABASE_URL` and `DATABASE_PASSWORD_REF`.

PostgreSQL reads the same raw password file through `POSTGRES_PASSWORD_FILE` when initializing a new data directory. On an existing database, replacing this file does **not** change the stored role password. Use a maintenance window for a role-password rotation on the target host:

1. Record the deployed commit and image identities. Create a PostgreSQL backup with `scripts/postgres_backup_restore.py backup` and prove its isolated restore with `verify-restore`. Copy the old active password file to private mode-`0600` `AIOS_SECRETS_DIR/database/postgres_password_previous` for the rollback window. Prepare a distinct new UTF-8 password of at least 12 characters in a mode-`0600` file at `AIOS_SECRETS_DIR/database/postgres_password_next` on the same filesystem as the active file. Do not put either password in shell arguments, environment values, SQL text, tickets or logs.
2. Check the existing remote application login using `docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps api python -m app.core.database_password_probe`. It requires the configured role/database over TCP and an explicit PostgreSQL invalid-password rejection for a separate random attempt. The output contains only a success flag, role and database. A failed probe blocks rotation.
3. Stop `ingress`, `web`, `api`, `worker` and `beat` with `docker compose --env-file .env.production -f docker-compose.prod.yml stop ingress web api worker beat`; leave `postgres` running. Open an interactive `psql` session in the PostgreSQL container with `docker compose --env-file .env.production -f docker-compose.prod.yml exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>`. Confirm `SELECT current_user, current_database();` matches the passwordless `DATABASE_URL`, then run `\password` at the `psql` prompt and enter the exact staged new value twice. PostgreSQL's interactive command avoids placing the cleartext password in SQL history or the server's SQL text. Exit `psql`.
4. Before replacing the active file, prove a new application connection with the staged file: `docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps -e DATABASE_PASSWORD_REF=file:///run/secrets/aios/database/postgres_password_next api python -m app.core.database_password_probe`. If this fails, keep all application services stopped; correct the role password with `\password` or restore the old role password and verify the old file. Do not proceed based on `pg_isready`, which does not prove the application's password.
5. After the staged probe passes, rename the staged file over the active password file on the same host filesystem, preserving private permissions. Restart `api`, `worker` and `beat` with the same deployed image/configuration, then `web` and `ingress`. Run the default probe again and verify API health, worker/beat operation, migration connectivity on the next deployment, and a synthetic web → API → PostgreSQL → worker journey. The previous password file must fail the probe when selected with `-e DATABASE_PASSWORD_REF=file:///run/secrets/aios/database/postgres_password_previous`; keep it only through the controlled rollback window. A role-password change affects new connections, so stopping and restarting application clients is part of this gate.

Capture redacted command exit states, backup/restore receipt, service restart and actual host connection evidence. Keep production readiness **unverified** until this procedure is executed on the intended VPS; repository CI only checks the probe against an isolated PostgreSQL role. The optional OpenBao pilot does not take over this production credential authority.

The migrated values are re-read through the existing `SecretsPort` rather than cached as a second secret system. Replacing the admin-password file applies to the next login; replacing the JWT secret invalidates sessions signed with the previous key; replacing the document-access signing secret invalidates outstanding document tokens signed with the previous key; webhook replacement applies to the next verification; and newly-created MinIO clients observe the current files. Exercise those exact consequences on the target host before claiming rotation support.

`AUTOMATION_ENCRYPTION_KEY_REF` points to the active file. An optional `AUTOMATION_ENCRYPTION_PREVIOUS_KEY_REF` supports decrypting ciphertext written under the prior key while new writes use the active key; the two resolved values must differ. Rotate stored connector credentials on the target host as a maintenance operation:

1. Record the exact release and take a PostgreSQL backup; prove its isolated restore before modifying the key. Stop API, worker and beat to prevent connector writes and delivery during the migration. Preserve the old active key in a separate private file under `/run/secrets/aios/automation/` and set `AUTOMATION_ENCRYPTION_PREVIOUS_KEY_REF` to that file. Install a distinct new active key file at the configured active reference, using an atomic host file replacement. Never log or paste either value.
2. With PostgreSQL running, use the deployed API image and the same production Compose configuration for `docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps api python -m app.services.connector_key_rotation --check`. It reports only total, already-active and previous-key row counts. Any unreadable row fails the command; investigate against the preserved backup and both keys before proceeding.
3. Run the same command with `--apply`, then with `--verify`. Apply locks the connector table, re-encrypts only prior-key rows in one transaction, records redacted audit entries and verifies every row with the active key before commit. Failure rolls the transaction back. Verify requires every row to decrypt with only the active key; keep the previous key until this passes. The command never emits credential values.
4. Remove the previous reference from the Compose env, recreate API/worker/beat, rerun `--verify` without the previous reference, and exercise a synthetic connector read and authorized delivery through the live services. Record row counts, backup/restore evidence, service restart, audit entries and connector behavior against the deployed commit. Delete the old file only after that proof and the rollback window close. An application or database failure after a committed apply must be handled with both keys retained while diagnosing; do not simply revert the active file.

The command is deliberately PostgreSQL and production-only. Repository tests of its transaction and rollback are not target-host rotation evidence. Until this procedure is performed and recorded on the intended VPS, credential rotation remains unverified there.

Set two distinct public DNS hostnames. For example, `WEB_DOMAIN=app.example.com` and `API_DOMAIN=api.example.com` require `CORS_ALLOWED_ORIGINS=https://app.example.com` and `NEXT_PUBLIC_API_BASE_URL=https://api.example.com`. The API URL is compiled into the web image, so changing it requires a rebuild. Replace the example values before a hosted launch. Ensure both DNS records point to the VPS, public 80/443 reach ingress, and the Caddy `/data` volume persists across restarts. Record the exact image digest and certificate/routing evidence during target-host acceptance; a successful Caddy configuration check does not issue a public certificate.

The ingress startup guard rejects missing, malformed, duplicate and reserved example hostnames before Caddy starts. It does not verify DNS ownership or the relationship between the browser API URL and CORS settings; prove those on the deployed host.

The example leaves `LLM_PROVIDER` empty because a ChatGPT/Kimi consumer subscription is not an API credential. If a remote LLM provider is enabled, provision only that provider's real API credential in the runtime-secret directory and point its `*_API_KEY_REF` at the corresponding `/run/secrets/aios/llm/...` file. Never expose provider credentials through `NEXT_PUBLIC_*` variables.

Provision the document bucket on a TLS S3-compatible endpoint outside this Compose profile. Set `MINIO_ENDPOINT` to its real `host:port`, provision scoped non-default access/secret keys through `MINIO_ACCESS_KEY_REF` and `MINIO_SECRET_KEY_REF`, keep `MINIO_SECURE=true`, `MINIO_AUTO_CREATE_BUCKET=false`, and `MINIO_SERVER_SIDE_ENCRYPTION=true`. The example deliberately leaves `DOCUMENT_STORAGE_BACKUP_STRATEGY` and `DOCUMENT_STORAGE_RECOVERY_TESTED_AT` empty. Fill them only after the real backup/isolated recovery procedure is defined and exercised; those strings are declarations, not restore evidence.

After building the API image, run the isolated synthetic object probe from the target host before enabling document journeys:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml build api
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps api python -m app.services.document_storage_preflight
```

The probe checks the configured bucket and policy through the production adapter, writes one random synthetic object with SSE-S3, reads its bytes and encryption response header, and removes it with a missing-object check. It returns a redacted result and a synthetic key for manual cleanup if necessary. A passing probe does not prove public-read denial from outside the host, object-store backup/restore, retention, credential rotation, upload malware scanning, or the complete browser document journey. Capture those separately in the whole-product acceptance gate.

### OCI Always Free storage pilot (synthetic data only)

`DOCUMENT_STORAGE_BACKEND=oci` selects the OCI native Object Storage SDK and instance-principal identity. Set `OCI_REGION`, `OCI_NAMESPACE`, and `OCI_BUCKET_DOCUMENTS` to a preprovisioned **Standard**, `NoPublicAccess` bucket in the compute instance's home region; the adapter rejects a region mismatch. Clear the unused `MINIO_ACCESS_KEY_REF` and `MINIO_SECRET_KEY_REF`; the other runtime-secret file references remain mandatory. Create a dynamic group containing only the pilot compute instance and grant it bucket metadata read and object create/read/delete rights scoped to this one bucket. Do not grant bucket update, public access, pre-authenticated-request creation, or tenancy-wide object management. The container must be able to obtain OCI instance-principal identity and reach the regional Object Storage HTTPS API; prove both on the target host.

The OCI adapter checks `NoPublicAccess` and Standard tier before every document write/read. OCI encrypts stored objects by default; the native API does not return the S3 `AES256` evidence used by the MinIO/S3 adapter. Its synthetic preflight proves current-key write/read/deletion only and explicitly reports `object_encryption_independently_verified=false`. Bucket versioning can retain older object versions after a current-key delete. Separately inspect pre-authenticated requests, test anonymous denial from outside the host, and record bucket encryption configuration, retention, versioning and an independent document backup/recovery drill. Do not populate the recovery declarations or admit real client documents from this code-level/CI proof alone. This pilot does not create an Oracle account or any resources and makes no cost or production-readiness claim.

Validate the resolved Compose model before launch:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps ingress caddy validate --config /etc/caddy/Caddyfile
```

Build and start:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up --build
```

The important startup gates are:

```text
postgres healthy
  -> api-migrate completes successfully
  -> api starts and becomes healthy
  -> web starts after API health

redis starts
  -> worker / beat may start after migrations
```

Check the API:

```powershell
curl http://localhost:8000/health
```

Expected shape:

```json
{"status":"ok","service":"global-mobility-aios-api","environment":"production"}
```

Check the web container:

```powershell
curl -I http://localhost:3000/
```

For a hosted deployment, verify both external HTTPS origins, HTTP-to-HTTPS redirects, CORS, secure cookies and the externally reachable port set. The direct HTTP checks above are local diagnostics only.

## Operational Commands

Start in background:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

View application logs:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f api web worker beat
```

Run migrations manually:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm api-migrate
```

Stop services:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

Stop and delete production database/Redis volumes:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml down -v
```

Do not use `down -v` against production data unless destructive removal is explicitly intended and independently recoverable from validated backups.

## Verification

Repository/static gates:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py scripts/check_database_migrations.py scripts/check_docker_profile.py
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py
docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
```

Web production-image proof:

```powershell
docker build --target production --build-arg NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 --build-arg NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE=false -t gmai-web-production-proof apps/web
docker run --rm -p 3000:3000 gmai-web-production-proof
```

Then verify `http://127.0.0.1:3000/` responds from the production container. `V12 Production Proof` performs this bounded production-image build/smoke contract on pull requests and on its configured push branches.

Backend regression remains:

```powershell
$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

A complete real-world production acceptance still requires a real deployment environment, the provisioned runtime-secret directory and remaining production secret-management decisions, real storage infrastructure, live migrations/backups/recovery evidence, live browser-to-API behavior, and operational observability. Those claims must not be inferred from local Docker or fixture-only browser tests.

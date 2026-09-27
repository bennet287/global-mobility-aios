# Docker Production Profile — Current Baseline

This file remains the canonical Docker production-profile owner. The filename is retained from the original v3.3 API/PostgreSQL milestone so the repository does not grow a parallel deployment document for every later service addition.

## Current Scope

Included in `docker-compose.prod.yml`:

- PostgreSQL 16 with persistent production volume and healthcheck;
- one-shot Alembic migration gate (`api-migrate`) before API/worker startup;
- Redis with persistent append-only storage;
- FastAPI service with production healthcheck;
- Celery worker and beat services;
- Next.js web service built from the explicit `production` Docker target;
- browser-public API origin supplied at image build time through `NEXT_PUBLIC_API_BASE_URL`;
- web-to-API startup dependency on the API health gate;
- no `.env.production` injection into the web container, keeping database, JWT, storage, and provider secrets out of the frontend runtime;
- static production-profile validation through `scripts/check_docker_profile.py`.

The same `apps/web/Dockerfile` retains a separate `development` target. `docker-compose.yml` explicitly selects that target, so local hot-reload behavior is not coupled to the production image.

Not included in the production Compose yet:

- MinIO document-storage service;
- Qdrant;
- n8n;
- Ollama/local-model runtime;
- reverse proxy / ingress / TLS termination;
- managed workload identity or external secret injection;
- Kubernetes or another production orchestrator;
- a real hosted deployment target and live post-deployment acceptance evidence.

Those are separate production-acceptance slices. A passing Docker/CI profile proves deployability of this bounded container contract; it does **not** by itself prove a live production deployment.

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

Replace every relevant `change-this-*` placeholder before starting. At minimum configure:

```text
POSTGRES_PASSWORD
DATABASE_URL
JWT_SECRET
AUTH_ADMIN_PASSWORD
CORS_ALLOWED_ORIGINS
NEXT_PUBLIC_API_BASE_URL
```

If a remote LLM provider is enabled, configure only the selected provider's real credential on the server side. Never expose provider credentials through `NEXT_PUBLIC_*` variables.

Validate the resolved Compose model before launch:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml config
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

For a hosted deployment, use the externally routed HTTPS origins instead of localhost.

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
docker compose --env-file .env.production -f docker-compose.prod.yml config
```

Web production-image proof:

```powershell
docker build --target production --build-arg NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 --build-arg NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE=false -t gmai-web-production-proof apps/web
docker run --rm -p 3000:3000 gmai-web-production-proof
```

Then verify `http://127.0.0.1:3000/` responds from the production container. `V12 Production Proof` now performs this bounded production-image build/smoke contract on each pull request.

Backend regression remains:

```powershell
$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

A complete real-world production acceptance still requires a real deployment environment, real secret/storage infrastructure, live migrations/backups/recovery evidence, live browser-to-API behavior, and operational observability. Those claims must not be inferred from local Docker or fixture-only browser tests.

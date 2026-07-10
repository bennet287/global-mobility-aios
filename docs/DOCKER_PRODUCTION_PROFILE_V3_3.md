# Docker Production Profile v3.3

This milestone adds a narrow production Docker profile for the API and PostgreSQL only.

## Scope

Included:

- `docker-compose.prod.yml`
- `api`
- `api-migrate`
- `postgres`
- PostgreSQL healthcheck
- API healthcheck
- Alembic migration gate before API startup
- `.env.production.example`
- API `.dockerignore`
- static Docker profile check script

Not included yet:

- Redis
- Qdrant
- MinIO
- n8n
- web frontend production build
- Kubernetes

Those should come later, one service at a time.

## First Run

Create the production env file:

```powershell
Copy-Item .env.production.example .env.production
```

Edit these values before starting:

```text
POSTGRES_PASSWORD
DATABASE_URL
JWT_SECRET
AUTH_ADMIN_PASSWORD
```

Build and start:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up --build
```

The startup order is:

```text
postgres healthy
api-migrate runs alembic upgrade head
api starts after migrations complete
```

Check the API:

```powershell
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok","service":"global-mobility-aios-api","environment":"production"}
```

## Operational Commands

Start in background:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

View logs:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f api
```

Run migrations manually:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm api-migrate
```

Stop services:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

Stop and delete the production database volume:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml down -v
```

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py scripts/check_database_migrations.py scripts/check_docker_profile.py
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py
$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

Expected:

```text
Repository policy check passed.
Database migration check passed.
Docker production profile check passed.
All tests pass.
```

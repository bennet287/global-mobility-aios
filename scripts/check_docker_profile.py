from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEV_COMPOSE = ROOT / "docker-compose.yml"
PROD_COMPOSE = ROOT / "docker-compose.prod.yml"
PROD_ENV_EXAMPLE = ROOT / ".env.production.example"
INGRESS_CADDYFILE = ROOT / "infrastructure" / "deployment" / "Caddyfile"
API_DOCKERFILE = ROOT / "apps" / "api" / "Dockerfile"
API_DOCKERIGNORE = ROOT / "apps" / "api" / ".dockerignore"
WEB_DOCKERFILE = ROOT / "apps" / "web" / "Dockerfile"
WEB_DOCKERIGNORE = ROOT / "apps" / "web" / ".dockerignore"
WEB_NEXT_CONFIG = ROOT / "apps" / "web" / "next.config.js"
BACKUP_RESTORE_SCRIPT = ROOT / "scripts" / "postgres_backup_restore.py"
BACKUP_RESTORE_DOC = ROOT / "docs" / "POSTGRES_BACKUP_RESTORE_V1.md"


def _require_file(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"Missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _require(text: str, needle: str, source: Path) -> None:
    if needle not in text:
        raise AssertionError(f"Missing {needle!r} in {source.relative_to(ROOT)}")


def _require_absent(text: str, needle: str, source: Path) -> None:
    if needle in text:
        raise AssertionError(f"Unexpected {needle!r} in {source.relative_to(ROOT)}")


def _service_block(compose: str, service: str, source: Path) -> str:
    lines = compose.splitlines()
    header = f"  {service}:"
    try:
        start = lines.index(header)
    except ValueError as exc:
        raise AssertionError(f"Missing service {service!r} in {source.relative_to(ROOT)}") from exc

    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            end = index
            break
    return "\n".join(lines[start:end])


def main() -> int:
    try:
        dev_compose = _require_file(DEV_COMPOSE)
        compose = _require_file(PROD_COMPOSE)
        env_example = _require_file(PROD_ENV_EXAMPLE)
        caddyfile = _require_file(INGRESS_CADDYFILE)
        api_dockerfile = _require_file(API_DOCKERFILE)
        api_dockerignore = _require_file(API_DOCKERIGNORE)
        web_dockerfile = _require_file(WEB_DOCKERFILE)
        web_dockerignore = _require_file(WEB_DOCKERIGNORE)
        web_next_config = _require_file(WEB_NEXT_CONFIG)
        backup_restore_script = _require_file(BACKUP_RESTORE_SCRIPT)
        backup_restore_doc = _require_file(BACKUP_RESTORE_DOC)

        for service in ("postgres", "api-migrate", "redis", "api", "web", "ingress", "worker", "beat"):
            _service_block(compose, service, PROD_COMPOSE)

        postgres_block = _service_block(compose, "postgres", PROD_COMPOSE)
        api_block = _service_block(compose, "api", PROD_COMPOSE)
        web_block = _service_block(compose, "web", PROD_COMPOSE)
        ingress_block = _service_block(compose, "ingress", PROD_COMPOSE)
        dev_web_block = _service_block(dev_compose, "web", DEV_COMPOSE)

        _require(compose, "condition: service_healthy", PROD_COMPOSE)
        _require(compose, "condition: service_completed_successfully", PROD_COMPOSE)
        _require(compose, "alembic -c alembic.ini upgrade head", PROD_COMPOSE)
        _require(compose, 'DATABASE_AUTO_CREATE_TABLES: "false"', PROD_COMPOSE)
        _require(compose, "change-this-postgres-password", PROD_COMPOSE)
        _require(compose, ".env.production", PROD_COMPOSE)
        _require(compose, "postgres_prod_data:", PROD_COMPOSE)
        _require(compose, "redis_prod_data:", PROD_COMPOSE)

        _require(api_block, "condition: service_completed_successfully", PROD_COMPOSE)
        _require_absent(postgres_block, "ports:", PROD_COMPOSE)
        _require(api_block, '127.0.0.1:${API_PORT:-8000}:8000', PROD_COMPOSE)
        _require(web_block, "target: production", PROD_COMPOSE)
        _require(web_block, "NEXT_PUBLIC_API_BASE_URL", PROD_COMPOSE)
        _require(web_block, 'NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE: "false"', PROD_COMPOSE)
        _require(web_block, '127.0.0.1:${WEB_PORT:-3000}:3000', PROD_COMPOSE)
        _require(web_block, "condition: service_healthy", PROD_COMPOSE)
        _require_absent(web_block, "env_file:", PROD_COMPOSE)
        for needle in (
            "caddy:2.11.4-alpine",
            "WEB_DOMAIN: ${WEB_DOMAIN:?",
            "API_DOMAIN: ${API_DOMAIN:?",
            '"80:80"',
            '"443:443"',
            "./infrastructure/deployment/Caddyfile:/etc/caddy/Caddyfile:ro",
            "ingress_data:/data",
            "ingress_config:/config",
        ):
            _require(ingress_block, needle, PROD_COMPOSE)
        _require_absent(ingress_block, "env_file:", PROD_COMPOSE)
        _require(caddyfile, "https://{$WEB_DOMAIN} {\n    reverse_proxy web:3000", INGRESS_CADDYFILE)
        _require(caddyfile, "https://{$API_DOMAIN} {\n    reverse_proxy api:8000", INGRESS_CADDYFILE)
        _require(compose, "ingress_data:", PROD_COMPOSE)
        _require(dev_web_block, "target: development", DEV_COMPOSE)

        _require(env_example, "APP_ENV=production", PROD_ENV_EXAMPLE)
        _require(env_example, "AUTH_ALLOW_HEADER_ROLE=false", PROD_ENV_EXAMPLE)
        _require(env_example, "DATABASE_AUTO_CREATE_TABLES=false", PROD_ENV_EXAMPLE)
        _require(env_example, "postgresql+psycopg://", PROD_ENV_EXAMPLE)
        _require(env_example, "WEB_PORT=3000", PROD_ENV_EXAMPLE)
        _require(env_example, "NEXT_PUBLIC_API_BASE_URL=", PROD_ENV_EXAMPLE)
        _require(env_example, "WEB_DOMAIN=", PROD_ENV_EXAMPLE)
        _require(env_example, "API_DOMAIN=", PROD_ENV_EXAMPLE)

        _require(api_dockerfile, "HEALTHCHECK", API_DOCKERFILE)
        _require(api_dockerignore, "gmai.db", API_DOCKERIGNORE)
        _require(api_dockerignore, "tests/", API_DOCKERIGNORE)

        for needle in (
            "AS development",
            "AS builder",
            "AS production",
            "npm ci",
            "npm run build",
            "NEXT_PUBLIC_API_BASE_URL",
            "COPY --from=builder --chown=node:node /app/public ./public",
            "USER node",
            "HEALTHCHECK",
            'CMD ["node", "server.js"]',
        ):
            _require(web_dockerfile, needle, WEB_DOCKERFILE)
        _require_absent(_service_block(compose, "web", PROD_COMPOSE), "npm run dev", PROD_COMPOSE)
        _require(web_dockerignore, "node_modules", WEB_DOCKERIGNORE)
        _require(web_dockerignore, ".next", WEB_DOCKERIGNORE)
        _require(web_dockerignore, "e2e", WEB_DOCKERIGNORE)
        _require(web_next_config, 'output: "standalone"', WEB_NEXT_CONFIG)

        for needle in (
            "pg_dump",
            "pg_restore",
            "--exit-on-error",
            "Backup manifest not found",
            "source_public_table_count",
            "source_alembic_version",
            '"network_mode": "none"',
            "restore_image_id",
            "verification_id",
            "gmai-restore-verify-",
        ):
            _require(backup_restore_script, needle, BACKUP_RESTORE_SCRIPT)
        _require(backup_restore_doc, "network-isolated", BACKUP_RESTORE_DOC)
        _require(backup_restore_doc, "source/restored schema-metadata parity", BACKUP_RESTORE_DOC)
        _require(backup_restore_doc, "backups/postgres", BACKUP_RESTORE_DOC)
    except AssertionError as exc:
        print(f"Docker profile check failed: {exc}", file=sys.stderr)
        return 1

    print("Docker production profile check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

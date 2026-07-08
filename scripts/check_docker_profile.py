from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROD_COMPOSE = ROOT / "docker-compose.prod.yml"
PROD_ENV_EXAMPLE = ROOT / ".env.production.example"
API_DOCKERFILE = ROOT / "apps" / "api" / "Dockerfile"
API_DOCKERIGNORE = ROOT / "apps" / "api" / ".dockerignore"


def _require_file(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"Missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _require(text: str, needle: str, source: Path) -> None:
    if needle not in text:
        raise AssertionError(f"Missing {needle!r} in {source.relative_to(ROOT)}")


def main() -> int:
    try:
        compose = _require_file(PROD_COMPOSE)
        env_example = _require_file(PROD_ENV_EXAMPLE)
        dockerfile = _require_file(API_DOCKERFILE)
        dockerignore = _require_file(API_DOCKERIGNORE)

        for service in ("postgres:", "api-migrate:", "api:"):
            _require(compose, service, PROD_COMPOSE)
        _require(compose, "condition: service_healthy", PROD_COMPOSE)
        _require(compose, "condition: service_completed_successfully", PROD_COMPOSE)
        _require(compose, "alembic -c alembic.ini upgrade head", PROD_COMPOSE)
        _require(compose, "DATABASE_AUTO_CREATE_TABLES: \"false\"", PROD_COMPOSE)
        _require(compose, "change-this-postgres-password", PROD_COMPOSE)
        _require(compose, ".env.production", PROD_COMPOSE)
        _require(compose, "postgres_prod_data:", PROD_COMPOSE)

        _require(env_example, "APP_ENV=production", PROD_ENV_EXAMPLE)
        _require(env_example, "AUTH_ALLOW_HEADER_ROLE=false", PROD_ENV_EXAMPLE)
        _require(env_example, "DATABASE_AUTO_CREATE_TABLES=false", PROD_ENV_EXAMPLE)
        _require(env_example, "postgresql+psycopg://", PROD_ENV_EXAMPLE)

        _require(dockerfile, "HEALTHCHECK", API_DOCKERFILE)
        _require(dockerignore, "gmai.db", API_DOCKERIGNORE)
        _require(dockerignore, "tests/", API_DOCKERIGNORE)
    except AssertionError as exc:
        print(f"Docker profile check failed: {exc}", file=sys.stderr)
        return 1

    print("Docker production profile check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

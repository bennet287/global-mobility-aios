from __future__ import annotations

from typing import Optional

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


def normalize_database_url(database_url: str) -> str:
    value = str(database_url or "").strip()
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def configured_database_url() -> str:
    """Add the production password from the canonical bounded secret resolver."""
    from app.core.config import settings

    base = normalize_database_url(settings.database_url)
    if not settings.is_production():
        return base
    if not settings.database_password_ref.strip():
        raise RuntimeError("DATABASE_PASSWORD_REF must be configured in production")
    try:
        url = make_url(base)
    except (ArgumentError, ValueError, TypeError) as exc:
        raise RuntimeError("Production DATABASE_URL must be a passwordless PostgreSQL URL") from exc
    if (
        url.drivername != "postgresql+psycopg"
        or not url.username
        or not url.host
        or not url.database
        or url.password is not None
        or url.query
    ):
        raise RuntimeError("Production DATABASE_URL must be a passwordless PostgreSQL URL")
    password = settings.database_password
    if len(password) < 12 or password.lower().startswith("change-this"):
        raise RuntimeError("Production database password must be a non-default value of at least 12 characters")
    return url.set(password=password).render_as_string(hide_password=False)


def is_sqlite_url(database_url: str) -> bool:
    return normalize_database_url(database_url).startswith("sqlite")


def should_auto_create_tables(database_url: str, explicit_setting: Optional[bool]) -> bool:
    if explicit_setting is not None:
        return bool(explicit_setting)
    return is_sqlite_url(database_url)


def mask_database_url(database_url: str) -> str:
    value = normalize_database_url(database_url)
    if "://" not in value or "@" not in value:
        return value
    scheme, rest = value.split("://", 1)
    credentials, host = rest.split("@", 1)
    username = credentials.split(":", 1)[0]
    return f"{scheme}://{username}:***@{host}"

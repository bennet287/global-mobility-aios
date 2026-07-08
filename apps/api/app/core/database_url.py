from __future__ import annotations

from typing import Optional


def normalize_database_url(database_url: str) -> str:
    value = str(database_url or "").strip()
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


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

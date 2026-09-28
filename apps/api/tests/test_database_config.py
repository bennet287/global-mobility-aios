from __future__ import annotations

import pytest

from app.core.config import settings
from app.core.database_url import (
    configured_database_url,
    is_sqlite_url,
    mask_database_url,
    normalize_database_url,
    should_auto_create_tables,
)


def test_postgres_url_is_normalized_for_psycopg_driver() -> None:
    assert normalize_database_url("postgres://user:pass@localhost:5432/gmai") == (
        "postgresql+psycopg://user:pass@localhost:5432/gmai"
    )
    assert normalize_database_url("postgresql://user:pass@localhost:5432/gmai") == (
        "postgresql+psycopg://user:pass@localhost:5432/gmai"
    )


def test_sqlite_remains_the_default_auto_create_database() -> None:
    assert is_sqlite_url("sqlite:///./gmai.db")
    assert should_auto_create_tables("sqlite:///./gmai.db", None) is True
    assert should_auto_create_tables("sqlite:///./gmai.db", False) is False


def test_postgres_uses_alembic_by_default() -> None:
    url = "postgresql+psycopg://gmai:gmai_password@localhost:5432/gmai"
    assert not is_sqlite_url(url)
    assert should_auto_create_tables(url, None) is False
    assert should_auto_create_tables(url, True) is True


def test_database_url_masking_hides_passwords() -> None:
    masked = mask_database_url("postgresql+psycopg://gmai:gmai_password@localhost:5432/gmai")
    assert masked == "postgresql+psycopg://gmai:***@localhost:5432/gmai"


def test_production_database_password_comes_from_bounded_file(monkeypatch, tmp_path) -> None:
    root = tmp_path / "aios"
    root.mkdir()
    secret = root / "database_password"
    secret.write_text("special:pass@word%strong\n", encoding="utf-8")
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "database_url", "postgresql+psycopg://gmai@postgres:5432/gmai")
    monkeypatch.setattr(settings, "database_password_ref", f"file://{secret}")

    from sqlalchemy.engine import make_url

    configured = configured_database_url()
    assert make_url(configured).password == "special:pass@word%strong"
    assert "special:pass@word%strong" not in configured
    from alembic.config import Config

    migration_config = Config()
    migration_config.set_main_option("sqlalchemy.url", configured.replace("%", "%%"))
    assert make_url(migration_config.get_main_option("sqlalchemy.url")).password == "special:pass@word%strong"

    secret.write_text("replacement-password\n", encoding="utf-8")
    assert make_url(configured_database_url()).password == "replacement-password"


def test_production_database_url_rejects_inline_password_and_missing_ref(monkeypatch, tmp_path) -> None:
    root = tmp_path / "aios"
    root.mkdir()
    secret = root / "database_password"
    secret.write_text("strong-database-password", encoding="utf-8")
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "database_url", "postgresql+psycopg://gmai@postgres:5432/gmai")
    monkeypatch.setattr(settings, "database_password_ref", "")
    with pytest.raises(RuntimeError, match="DATABASE_PASSWORD_REF must be configured"):
        configured_database_url()

    monkeypatch.setattr(settings, "database_password_ref", f"file://{secret}")
    monkeypatch.setattr(settings, "database_url", "postgresql+psycopg://gmai:embedded@postgres:5432/gmai")
    with pytest.raises(RuntimeError, match="passwordless PostgreSQL URL"):
        configured_database_url()

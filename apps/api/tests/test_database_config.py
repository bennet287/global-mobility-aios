from __future__ import annotations

from app.core.database_url import (
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

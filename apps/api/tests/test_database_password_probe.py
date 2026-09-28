from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from sqlalchemy.engine import URL, make_url

from app.core.config import settings
from app.core import database_password_probe as probe


def test_probe_rejects_passwordless_trust_authentication(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(
        probe, "configured_database_url", lambda: "postgresql+psycopg://gmai:strong-secret@postgres/gmai"
    )
    monkeypatch.setattr(probe, "_connect_and_identify", lambda url: ("gmai", "gmai", True))

    with pytest.raises(probe.DatabasePasswordProbeError, match="accepted an incorrect password"):
        probe.probe_database_password()


def test_probe_authenticates_file_password_against_postgresql(monkeypatch, tmp_path):
    database_url = os.environ.get("GMAI_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Isolated PostgreSQL CI lane only")

    admin_url = make_url(database_url)
    role = f"rotation_probe_{uuid4().hex[:12]}"
    password = "strong-test-database-password"
    root = tmp_path / "aios"
    root.mkdir()
    secret = root / "postgres_password"
    secret.write_text(password, encoding="utf-8")
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    monkeypatch.setattr(settings, "app_env", "production")
    passwordless_url = URL.create(
        admin_url.drivername,
        username=role,
        host=admin_url.host,
        port=admin_url.port,
        database=admin_url.database,
    )
    assert passwordless_url.password is None
    monkeypatch.setattr(settings, "database_url", passwordless_url.render_as_string())
    monkeypatch.setattr(settings, "database_password_ref", f"file://{secret}")

    admin_dsn = admin_url.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(
            sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(role), sql.Literal(password))
        )
        try:
            result = probe.probe_database_password()
            assert result == {
                "authenticated": True,
                "incorrect_password_rejected": True,
                "role": role,
                "database": admin_url.database,
            }
            secret.write_text("a-different-strong-password", encoding="utf-8")
            with pytest.raises(probe.DatabasePasswordProbeError, match="configured connection"):
                probe.probe_database_password()
        finally:
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

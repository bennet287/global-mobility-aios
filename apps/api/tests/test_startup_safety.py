import pytest

from app.core.config import settings
from app.core.startup_safety import (
    validate_production_settings,
    validate_production_worker_settings,
)


_SECRET_FIELDS = {
    "database_password": "database_password_ref",
    "jwt_secret": "jwt_secret_ref",
    "auth_admin_password": "auth_admin_password_ref",
    "automation_encryption_key": "automation_encryption_key_ref",
    "automation_webhook_secret": "automation_webhook_secret_ref",
    "minio_access_key": "minio_access_key_ref",
    "minio_secret_key": "minio_secret_key_ref",
    "document_access_token_secret": "document_access_token_secret_ref",
}


def _production_baseline(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "database_url", "postgresql+psycopg://gmai@postgres:5432/gmai")
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_allow_header_role", False)
    for field_name, ref_field_name in _SECRET_FIELDS.items():
        monkeypatch.setattr(settings, ref_field_name, "")
        monkeypatch.setattr(settings, field_name, f"direct-{field_name}-fallback")


def _write_secret(root, relative_path: str, value: str) -> str:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value + "\n", encoding="utf-8")
    return f"file://{target}"


def _valid_refs(root) -> tuple[dict[str, str], dict[str, str]]:
    resolved = {
        "database_password": "strong-database-password",
        "jwt_secret": "j" * 48,
        "auth_admin_password": "strong-production-admin-password",
        "automation_encryption_key": "a" * 48,
        "automation_webhook_secret": "w" * 48,
        "minio_access_key": "access-key-v1",
        "minio_secret_key": "secret-key-v1",
        "document_access_token_secret": "d" * 48,
    }
    refs = {
        "database_password_ref": _write_secret(
            root, "database/postgres_password", resolved["database_password"]
        ),
        "jwt_secret_ref": _write_secret(root, "auth/jwt_secret", resolved["jwt_secret"]),
        "auth_admin_password_ref": _write_secret(
            root, "auth/admin_password", resolved["auth_admin_password"]
        ),
        "automation_encryption_key_ref": _write_secret(
            root, "automation/encryption_key", resolved["automation_encryption_key"]
        ),
        "automation_webhook_secret_ref": _write_secret(
            root, "automation/webhook_secret", resolved["automation_webhook_secret"]
        ),
        "minio_access_key_ref": _write_secret(
            root, "storage/minio_access_key", resolved["minio_access_key"]
        ),
        "minio_secret_key_ref": _write_secret(
            root, "storage/minio_secret_key", resolved["minio_secret_key"]
        ),
        "document_access_token_secret_ref": _write_secret(
            root, "documents/access_token_secret", resolved["document_access_token_secret"]
        ),
    }
    return refs, resolved


def _configure_valid_refs(monkeypatch, root) -> dict[str, str]:
    refs, resolved = _valid_refs(root)
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)
    return resolved


def test_production_startup_accepts_governed_runtime_secret_refs(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    resolved = _configure_valid_refs(monkeypatch, root)

    validate_production_settings()

    for field_name, expected in resolved.items():
        assert getattr(settings, field_name) == expected
        assert getattr(settings, field_name) != f"direct-{field_name}-fallback"


def test_oci_startup_does_not_require_unused_minio_keys(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    refs, _ = _valid_refs(root)
    for field_name, value in refs.items():
        if not field_name.startswith("minio_"):
            monkeypatch.setattr(settings, field_name, value)
    monkeypatch.setattr(settings, "document_storage_backend", "oci")
    validate_production_settings()


def test_runtime_secret_file_replacement_is_observed_on_next_access(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    _configure_valid_refs(monkeypatch, root)

    validate_production_settings()
    assert settings.jwt_secret == "j" * 48

    (root / "auth/jwt_secret").write_text("k" * 48 + "\n", encoding="utf-8")

    assert settings.jwt_secret == "k" * 48
    (root / "auth/admin_password").write_text("replacement-admin-password\n", encoding="utf-8")
    assert settings.auth_admin_password == "replacement-admin-password"


def test_production_startup_rejects_missing_required_runtime_secret_ref(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs, _ = _valid_refs(root)
    refs.pop("jwt_secret_ref")
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    with pytest.raises(RuntimeError, match="JWT_SECRET_REF must be configured"):
        validate_production_settings()


def test_production_startup_rejects_missing_database_password_ref(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    refs, _ = _valid_refs(root)
    refs.pop("database_password_ref")
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)
    monkeypatch.setattr(settings, "database_password", "strong-direct-password")

    with pytest.raises(RuntimeError, match="DATABASE_PASSWORD_REF must be configured"):
        validate_production_settings()


def test_production_startup_rejects_missing_automation_encryption_key_ref(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs, _ = _valid_refs(root)
    refs.pop("automation_encryption_key_ref")
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    with pytest.raises(RuntimeError, match="AUTOMATION_ENCRYPTION_KEY_REF must be configured"):
        validate_production_settings()


def test_production_startup_rejects_unavailable_configured_runtime_secret(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs, _ = _valid_refs(root)
    refs["jwt_secret_ref"] = f"file://{root / 'auth/missing-jwt'}"
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    with pytest.raises(RuntimeError, match="JWT_SECRET_REF must resolve"):
        validate_production_settings()


def test_production_startup_rejects_non_file_runtime_secret_refs(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs, _ = _valid_refs(root)
    refs["jwt_secret_ref"] = "env://JWT_SECRET_FROM_ENV"
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    with pytest.raises(RuntimeError, match="JWT_SECRET_REF must resolve"):
        validate_production_settings()


def test_api_production_startup_still_rejects_default_admin_password(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    _configure_valid_refs(monkeypatch, root)
    (root / "auth/admin_password").write_text("admin\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="AUTH_ADMIN_PASSWORD must be set"):
        validate_production_settings()


def test_api_production_startup_requires_admin_password_ref_even_with_direct_value(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    _configure_valid_refs(monkeypatch, root)
    monkeypatch.setattr(settings, "auth_admin_password_ref", "")
    monkeypatch.setattr(settings, "auth_admin_password", "strong-direct-password")

    with pytest.raises(RuntimeError, match="AUTH_ADMIN_PASSWORD_REF must be configured"):
        validate_production_settings()


def test_api_production_startup_rejects_unavailable_admin_password_file(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    _configure_valid_refs(monkeypatch, root)
    (root / "auth/admin_password").unlink()

    with pytest.raises(RuntimeError, match="AUTH_ADMIN_PASSWORD_REF must resolve"):
        validate_production_settings()


def test_worker_preflight_excludes_api_login_secret_and_runs_storage_gate(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)
    _configure_valid_refs(monkeypatch, root)
    monkeypatch.setattr(settings, "auth_admin_password", "admin")
    monkeypatch.setattr(settings, "auth_admin_password_ref", f"file://{root / 'auth/missing-admin'}")

    calls: list[str] = []
    monkeypatch.setattr(
        "app.services.document_storage.validate_document_storage_configuration",
        lambda: calls.append("document-storage"),
    )

    validate_production_worker_settings()

    assert calls == ["document-storage"]

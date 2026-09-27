import pytest

from app.core.config import settings
from app.core.startup_safety import validate_production_settings


_SECRET_FIELDS = {
    "jwt_secret": "jwt_secret_ref",
    "automation_webhook_secret": "automation_webhook_secret_ref",
    "minio_access_key": "minio_access_key_ref",
    "minio_secret_key": "minio_secret_key_ref",
    "document_access_token_secret": "document_access_token_secret_ref",
}


def _production_baseline(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_allow_header_role", False)
    monkeypatch.setattr(settings, "auth_admin_password", "strong-production-admin-password")
    for field_name, ref_field_name in _SECRET_FIELDS.items():
        monkeypatch.setattr(settings, ref_field_name, "")
        monkeypatch.setattr(settings, field_name, f"direct-{field_name}-fallback")


def _write_secret(root, relative_path: str, value: str) -> str:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value + "\n", encoding="utf-8")
    return f"file://{target}"


def test_production_startup_accepts_available_governed_runtime_secret_refs(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs = {
        "jwt_secret_ref": _write_secret(root, "auth/jwt_secret", "j" * 48),
        "automation_webhook_secret_ref": _write_secret(
            root, "automation/webhook_secret", "w" * 48
        ),
        "minio_access_key_ref": _write_secret(root, "storage/minio_access_key", "access-key-v1"),
        "minio_secret_key_ref": _write_secret(root, "storage/minio_secret_key", "secret-key-v1"),
        "document_access_token_secret_ref": _write_secret(
            root, "documents/access_token_secret", "d" * 48
        ),
    }
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    validate_production_settings()


def test_production_startup_rejects_missing_required_runtime_secret_ref(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    for ref_field_name, relative_path, value in (
        ("automation_webhook_secret_ref", "automation/webhook_secret", "w" * 48),
        ("minio_access_key_ref", "storage/minio_access_key", "access-key-v1"),
        ("minio_secret_key_ref", "storage/minio_secret_key", "secret-key-v1"),
        ("document_access_token_secret_ref", "documents/access_token_secret", "d" * 48),
    ):
        monkeypatch.setattr(settings, ref_field_name, _write_secret(root, relative_path, value))

    with pytest.raises(RuntimeError, match="JWT_SECRET_REF must be configured"):
        validate_production_settings()


def test_production_startup_rejects_unavailable_configured_runtime_secret(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs = {
        "jwt_secret_ref": f"file://{root / 'auth/missing-jwt'}",
        "automation_webhook_secret_ref": _write_secret(
            root, "automation/webhook_secret", "w" * 48
        ),
        "minio_access_key_ref": _write_secret(root, "storage/minio_access_key", "access-key-v1"),
        "minio_secret_key_ref": _write_secret(root, "storage/minio_secret_key", "secret-key-v1"),
        "document_access_token_secret_ref": _write_secret(
            root, "documents/access_token_secret", "d" * 48
        ),
    }
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    with pytest.raises(RuntimeError, match="JWT_SECRET_REF must resolve"):
        validate_production_settings()

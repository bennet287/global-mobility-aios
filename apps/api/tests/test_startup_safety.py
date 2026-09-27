import pytest

from app.core.config import settings
from app.core.startup_safety import (
    validate_production_settings,
    validate_production_worker_settings,
)


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


def _valid_refs(root) -> tuple[dict[str, str], dict[str, str]]:
    resolved = {
        "jwt_secret": "j" * 48,
        "automation_webhook_secret": "w" * 48,
        "minio_access_key": "access-key-v1",
        "minio_secret_key": "secret-key-v1",
        "document_access_token_secret": "d" * 48,
    }
    refs = {
        "jwt_secret_ref": _write_secret(root, "auth/jwt_secret", resolved["jwt_secret"]),
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


def test_production_startup_accepts_and_materializes_governed_runtime_secret_refs(
    monkeypatch, tmp_path
):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs, resolved = _valid_refs(root)
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    validate_production_settings()

    for field_name, expected in resolved.items():
        assert getattr(settings, field_name) == expected
        assert getattr(settings, field_name) != f"direct-{field_name}-fallback"


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


def test_production_startup_rejects_unavailable_ref_without_materializing_fallbacks(
    monkeypatch, tmp_path
):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs, _ = _valid_refs(root)
    refs["jwt_secret_ref"] = f"file://{root / 'auth/missing-jwt'}"
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    before = {
        field_name: getattr(settings, field_name)
        for field_name in _SECRET_FIELDS
    }
    with pytest.raises(RuntimeError, match="JWT_SECRET_REF must resolve"):
        validate_production_settings()

    for field_name, original in before.items():
        assert getattr(settings, field_name) == original


def test_production_startup_rejects_non_file_runtime_secret_refs(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs, _ = _valid_refs(root)
    refs["jwt_secret_ref"] = "env://JWT_SECRET_FROM_ENV"
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    with pytest.raises(RuntimeError, match=r"JWT_SECRET_REF must use a file:// reference"):
        validate_production_settings()


def test_production_startup_rejects_invalid_runtime_secret_ref(monkeypatch, tmp_path):
    _production_baseline(monkeypatch)
    root = tmp_path / "aios"
    root.mkdir()
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", root)

    refs, _ = _valid_refs(root)
    refs["jwt_secret_ref"] = "not-a-secret-reference"
    for field_name, value in refs.items():
        monkeypatch.setattr(settings, field_name, value)

    with pytest.raises(RuntimeError, match="JWT_SECRET_REF must be a valid production secret reference"):
        validate_production_settings()


def test_worker_preflight_runs_runtime_and_document_storage_gates(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        "app.core.startup_safety.validate_production_settings",
        lambda: calls.append("runtime-secrets"),
    )
    monkeypatch.setattr(
        "app.services.document_storage.validate_document_storage_configuration",
        lambda: calls.append("document-storage"),
    )

    validate_production_worker_settings()

    assert calls == ["runtime-secrets", "document-storage"]

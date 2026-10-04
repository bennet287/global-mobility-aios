from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from app.core.config import Settings
from app.core.secrets import SecretResolutionError, resolve_runtime_secret


ROOT = Path(__file__).resolve().parents[3]
SHARED = {"database", "auth", "automation", "documents", "storage", "llm"}


def test_production_workloads_receive_only_intended_credential_directories() -> None:
    services = yaml.safe_load((ROOT / "docker-compose.prod.yml").read_text())["services"]
    expected = {
        "postgres": {"database"}, "api-migrate": {"database"},
        "api": SHARED | {"bootstrap"}, "worker": SHARED,
        "beat": set(), "web": set(), "ingress": set(), "redis": set(),
    }
    for name, scopes in expected.items():
        volumes = services[name].get("volumes", [])
        secret_mounts = [item for item in volumes if isinstance(item, dict)
                         and item.get("target", "").startswith("/run/secrets/aios")]
        assert {item["target"] for item in secret_mounts} == {
            f"/run/secrets/aios/{scope}" for scope in scopes
        }
        assert len(secret_mounts) == len(scopes)
        for item in secret_mounts:
            scope = item["target"].rsplit("/", 1)[1]
            assert item["type"] == "bind"
            assert item["read_only"] is True
            assert item["bind"]["create_host_path"] is False
            assert item["source"].endswith(f"}}/{scope}")


@pytest.mark.parametrize(("field", "relative"), [
    ("database_password", "database/postgres_password"),
    ("jwt_secret", "auth/jwt_secret"),
    ("auth_admin_password", "bootstrap/admin_password"),
    ("automation_encryption_key", "automation/encryption_key"),
    ("automation_encryption_previous_key", "automation/encryption_key_previous"),
    ("automation_webhook_secret", "automation/webhook_secret"),
    ("document_access_token_secret", "documents/access_token_secret"),
    ("minio_access_key", "storage/minio_access_key"),
    ("minio_secret_key", "storage/minio_secret_key"),
])
def test_settings_observe_atomic_file_replacement_inside_stable_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, relative: str,
) -> None:
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", tmp_path)
    active = tmp_path / relative
    active.parent.mkdir(parents=True)
    active.write_text("synthetic-before\n")
    settings = Settings(_env_file=None, **{field: "unused-fallback", f"{field}_ref": f"file://{active}"})
    assert getattr(settings, field) == "synthetic-before"
    replacement = active.with_name(active.name + ".next")
    replacement.write_text("synthetic-after\n")
    os.replace(replacement, active)
    assert getattr(settings, field) == "synthetic-after"


def test_bootstrap_transition_and_absent_scope_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", tmp_path)
    bootstrap = tmp_path / "bootstrap" / "admin_password"
    bootstrap.parent.mkdir()
    bootstrap.write_text("synthetic-bootstrap\n")
    settings = Settings(_env_file=None, auth_admin_password="unused-fallback",
                        auth_admin_password_ref=f"file://{bootstrap}")
    assert settings.auth_admin_password == "synthetic-bootstrap"
    settings.auth_admin_password_ref = f"file://{tmp_path / 'auth' / 'admin_password'}"
    with pytest.raises(SecretResolutionError, match="unavailable"):
        _ = settings.auth_admin_password
    settings.auth_admin_password_ref = f"file://{bootstrap}"
    bootstrap.unlink()
    with pytest.raises(SecretResolutionError, match="unavailable"):
        _ = settings.auth_admin_password


@pytest.mark.parametrize("relative", [
    "database/postgres_password", "database/postgres_password_next",
    "database/postgres_password_previous", "automation/encryption_key",
    "automation/encryption_key_previous",
])
def test_rotation_window_references_remain_in_mounted_scopes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str,
) -> None:
    monkeypatch.setattr("app.core.secrets._FILE_SECRET_ROOT", tmp_path)
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text("synthetic-rotation-value\n")
    assert resolve_runtime_secret(reference=f"file://{path}", fallback="unused") == "synthetic-rotation-value"

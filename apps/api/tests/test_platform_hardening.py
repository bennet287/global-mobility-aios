from __future__ import annotations

import pytest

from app.core.auth_policy import required_roles
from app.core.config import settings
from app.core.pagination import MAX_QUERY_LIMIT, clamp_query_limit
from app.core.router_registry import ROUTER_SPECS
from app.core.startup_safety import validate_production_settings
from app.services.department_runtime import department_runtime_spec
from app.services.document_storage import LocalDocumentStorage, document_storage_posture
from app.services.organization_governance import department_runtime_available


def test_production_auth_configuration_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_allow_header_role", True)
    monkeypatch.setattr(settings, "jwt_secret", "change-this-in-production")
    monkeypatch.setattr(settings, "auth_admin_password", "admin")

    with pytest.raises(RuntimeError, match="Production startup blocked"):
        validate_production_settings()


def test_production_auth_configuration_accepts_explicit_secure_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_allow_header_role", False)
    monkeypatch.setattr(settings, "jwt_secret", "x" * 48)
    monkeypatch.setattr(settings, "auth_admin_password", "correct-horse-battery-staple")

    validate_production_settings()


def test_production_document_storage_requires_encrypted_minio(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "document_storage_production_strict", False)
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    posture = document_storage_posture()
    assert "production_requires_minio" in posture["failures"]
    with pytest.raises(RuntimeError, match="Local document storage is prohibited"):
        LocalDocumentStorage(str(tmp_path))

    monkeypatch.setattr(settings, "document_storage_backend", "minio")
    monkeypatch.setattr(settings, "minio_secure", True)
    monkeypatch.setattr(settings, "minio_access_key", "production-access-key")
    monkeypatch.setattr(settings, "minio_secret_key", "production-secret-key")
    monkeypatch.setattr(settings, "minio_auto_create_bucket", False)
    monkeypatch.setattr(settings, "minio_server_side_encryption", False)
    posture = document_storage_posture()
    assert "minio_server_side_encryption_required" in posture["failures"]


def test_auth_policy_registry_preserves_sensitive_role_boundaries() -> None:
    assert required_roles("POST", "/api/v1/truth/claims/example/resolve") == {"admin", "reviewer"}
    assert required_roles("POST", "/api/v1/applications/example/approve") == {"admin", "reviewer"}
    assert required_roles("POST", "/api/v1/sales/leads") == {"admin", "operator", "sales"}
    assert required_roles("GET", "/api/v1/profiles") == {
        "admin",
        "operator",
        "reviewer",
        "sales",
        "read_only",
    }
    assert required_roles("POST", "/api/v1/external-validation/runs/example/reviews") == {
        "admin",
        "operator",
        "reviewer",
    }
    assert required_roles(
        "POST",
        "/api/v1/external-validation/findings/example/board-acceptance",
    ) == {"admin"}


def test_router_registry_contains_compatibility_and_security_critical_routes() -> None:
    features = [spec.feature for spec in ROUTER_SPECS]
    assert len(features) == 63
    assert "auth" in features
    assert "organization-governance" in features
    assert "external-validation" in features
    assert "document-access" in features
    assert "audit-logs" in features
    assert features.count("dashboard-api") == 1
    assert features.count("dashboard-compat") == 1


def test_pagination_policy_clamps_untrusted_limits() -> None:
    assert clamp_query_limit(None) <= MAX_QUERY_LIMIT
    assert clamp_query_limit(0) == 1
    assert clamp_query_limit(25) == 25
    assert clamp_query_limit(50_000) == MAX_QUERY_LIMIT


def test_department_runtime_registry_keeps_active_and_held_departments_explicit() -> None:
    technology = department_runtime_spec("Technology")
    marketing = department_runtime_spec("Marketing")
    operations = department_runtime_spec("Operations")
    finance = department_runtime_spec("Finance")
    communications = department_runtime_spec("Communications")
    people = department_runtime_spec("People")

    assert technology is not None and technology.allowed_actions == frozenset({"internal.analysis"})
    assert technology.executive_position == "cto"
    assert marketing is not None and marketing.allowed_actions == frozenset({"internal.analysis"})
    assert marketing.executive_position == "cmo"
    assert operations is not None and operations.allowed_actions is None
    assert finance is not None and finance.allowed_actions == frozenset({"internal.analysis"})
    assert finance.executive_position == "cfo"
    assert communications is not None and communications.allowed_actions == frozenset({"internal.analysis"})
    assert communications.executive_position == "cco"
    assert people is not None and people.allowed_actions == frozenset({"internal.analysis"})
    assert people.executive_position == "chro"


def test_capability_boundary_denies_prohibited_department_actions() -> None:
    assert department_runtime_available("Security", "internal.analysis") is True
    assert department_runtime_available("Security", "secrets.access") is False
    assert department_runtime_available("Security Operations", "position.suspend") is False
    assert department_runtime_available("Technology", "deployment.production") is False
    assert department_runtime_available("Product", "policy.publish") is False
    assert department_runtime_available("Marketing", "internal.analysis") is True
    assert department_runtime_available("Marketing", "client.external_send") is False
    assert department_runtime_available("Finance", "internal.analysis") is True
    assert department_runtime_available("Finance", "client.external_send") is False
    assert department_runtime_available("Finance", "payment.initiate") is False
    assert department_runtime_available("Communications", "internal.analysis") is True
    assert department_runtime_available("Communications", "client.external_send") is False
    assert department_runtime_available("Communications", "policy.publish") is False
    assert department_runtime_available("People", "internal.analysis") is True
    assert department_runtime_available("People", "hiring.decision") is False
    assert department_runtime_available("People", "compensation.change") is False
    assert department_runtime_available("People", "termination.action") is False

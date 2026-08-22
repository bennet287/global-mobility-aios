from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from app.core.access import required_roles
from app.core.pagination import MAX_QUERY_LIMIT, clamp_query_limit
from app.core.router_registry import ROUTER_SPECS
from app.core.runtime_registry import department_runtime_spec


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_core_security_modules_import_without_router_side_effects() -> None:
    modules = (
        "app.core.access",
        "app.core.auth",
        "app.core.db",
        "app.core.pagination",
        "app.core.request_limits",
        "app.core.router_registry",
        "app.core.runtime_registry",
        "app.core.security",
    )
    for module in modules:
        importlib.import_module(module)


def test_legacy_wildcard_imports_are_not_reintroduced() -> None:
    forbidden = (
        "from app.models.domain import *",
        "from app.schemas import *",
        "from app.routers import *",
    )
    for path in (REPO_ROOT / "apps" / "api" / "app").rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        for statement in forbidden:
            assert statement not in content, f"{path} reintroduced forbidden wildcard import {statement!r}"


def test_model_compatibility_contract_keeps_expected_names_explicit() -> None:
    domain = importlib.import_module("app.models.domain")
    package = importlib.import_module("app.models")
    expected = (
        "Lead",
        "Profile",
        "Application",
        "Document",
        "DocumentExtraction",
        "OrganizationPosition",
        "OrganizationActivity",
        "OrganizationAuthorityGrant",
    )
    for name in expected:
        assert getattr(package, name) is getattr(domain, name)


def test_schema_compatibility_contract_keeps_expected_names_explicit() -> None:
    schemas = importlib.import_module("app.schemas")
    expected = (
        "LeadCreate",
        "LeadRead",
        "ProfileCreate",
        "ProfileRead",
        "ApplicationCreate",
        "ApplicationRead",
        "DocumentRead",
    )
    for name in expected:
        assert hasattr(schemas, name)


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
    assert len(features) == 68
    assert "auth" in features
    assert "organization-governance" in features
    assert "organization-records" in features
    assert "organization-transparency" in features
    assert "organization-autonomy-promotion-transparency" in features
    assert "organization-autonomy-evidence-evaluation-transparency" in features
    assert "organization-governed-eligibility" in features
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

    assert technology.active is True
    assert marketing.active is True
    assert operations.active is True
    assert finance.active is False
    assert communications.active is False
    assert "CTO" in technology.positions
    assert "CMO" in marketing.positions
    assert "Head of Mobility Operations" in operations.positions

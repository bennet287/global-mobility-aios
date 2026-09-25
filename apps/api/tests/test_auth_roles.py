from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

import app.core.auth as auth_module
from app.core.auth import create_session_token, is_public_path, parse_session_token
from app.core.config import settings


def test_public_client_routes_do_not_require_operator_auth(raw_client: TestClient) -> None:
    response = raw_client.post("/api/v1/public/lookup", json={})
    assert response.status_code == 400


def test_public_prefix_does_not_match_similarly_named_private_path() -> None:
    assert is_public_path("/api/v1/public/intake") is True
    assert is_public_path("/api/v1/publicity") is False
    assert is_public_path("/api/partner/v1/intake") is True
    assert is_public_path("/debug/controlled-agents") is False


def test_debug_routes_require_admin_without_exposing_configuration(raw_client: TestClient) -> None:
    # These routes include provider/model and storage configuration in their payloads.
    for path in ("/debug/controlled-agents", "/debug/document-uploads"):
        unauthenticated = raw_client.get(path)
        assert unauthenticated.status_code == 401

        raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "viewer"})
        forbidden = raw_client.get(path)
        assert forbidden.status_code == 403
        assert forbidden.json()["allowed_roles"] == ["admin"]
        raw_client.headers.clear()

    raw_client.headers.update({"X-GMAI-Role": "admin", "X-GMAI-User": "operator"})
    assert raw_client.get("/debug/controlled-agents").status_code == 200
    assert raw_client.get("/debug/document-uploads").status_code == 200


def test_connector_credentials_and_health_checks_require_admin(raw_client: TestClient) -> None:
    config_id = uuid.uuid4()
    raw_client.headers.update({"X-GMAI-Role": "operator", "X-GMAI-User": "operator"})
    for path in (
        "/api/v1/automation/connectors",
        f"/api/v1/automation/connectors/{config_id}/status",
        f"/api/v1/automation/connectors/{config_id}/health-check",
    ):
        blocked = raw_client.post(path, json={})
        assert blocked.status_code == 403
        assert blocked.json()["allowed_roles"] == ["admin"]

    # Operators still dispatch an already-governed delivery through its existing gate.
    assert raw_client.post(f"/api/v1/automation/deliveries/{uuid.uuid4()}/dispatch").status_code == 404

    raw_client.headers.update({"X-GMAI-Role": "admin", "X-GMAI-User": "admin"})
    assert raw_client.post("/api/v1/automation/connectors", json={}).status_code == 422


def test_admin_page_redirects_to_login_without_auth(raw_client: TestClient) -> None:
    response = raw_client.get("/admin/v2", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"


def test_read_only_can_view_but_not_mutate(raw_client: TestClient) -> None:
    raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "viewer"})

    view_response = raw_client.get("/admin/v2")
    assert view_response.status_code == 200

    mutate_response = raw_client.post(
        f"/api/v1/document-verification/leads/{uuid.uuid4()}/bulk-verify",
        json={"note": "Should be blocked before route execution."},
    )
    assert mutate_response.status_code == 403
    assert mutate_response.json()["role"] == "read_only"


def test_reviewer_role_can_reach_reviewer_actions(raw_client: TestClient) -> None:
    raw_client.headers.update({"X-GMAI-Role": "reviewer", "X-GMAI-User": "reviewer"})

    response = raw_client.post(
        f"/api/v1/truth/claims/{uuid.uuid4()}/resolve",
        json={"resolution_note": "Allowed through auth; fake id should fail in route."},
    )
    assert response.status_code in {400, 404}


def test_sales_role_cannot_approve_application(raw_client: TestClient) -> None:
    raw_client.headers.update({"X-GMAI-Role": "sales", "X-GMAI-User": "sales"})

    response = raw_client.post(
        f"/api/v1/applications/{uuid.uuid4()}/approve",
        json={"note": "Sales should not approve applications."},
    )
    assert response.status_code == 403
    assert response.json()["allowed_roles"] == ["admin", "reviewer"]


def test_read_only_cannot_access_extracted_document_data(raw_client: TestClient) -> None:
    raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "viewer"})

    response = raw_client.get("/api/v1/document-intelligence/extractions")

    assert response.status_code == 403
    assert response.json()["allowed_roles"] == ["admin", "operator", "reviewer"]


def test_only_admin_or_reviewer_can_mutate_jurisdiction_assessments(raw_client: TestClient) -> None:
    payload = {
        "rule_relationship": "independent",
        "evidence_url": "https://government.example/immigration",
        "evidence_title": "Official immigration framework",
        "rationale": "Official evidence requires an independent human review decision.",
    }
    raw_client.headers.update({"X-GMAI-Role": "operator", "X-GMAI-User": "operator"})
    blocked = raw_client.post(
        f"/api/v1/global-intelligence/registry/{uuid.uuid4()}/immigration-assessments",
        json=payload,
    )
    assert blocked.status_code == 403
    assert blocked.json()["allowed_roles"] == ["admin", "reviewer"]

    raw_client.headers.update({"X-GMAI-Role": "reviewer", "X-GMAI-User": "reviewer"})
    allowed = raw_client.post(
        f"/api/v1/global-intelligence/registry/{uuid.uuid4()}/immigration-assessments",
        json=payload,
    )
    assert allowed.status_code == 400


def test_session_token_expires_at_configured_ttl(monkeypatch) -> None:
    issued_at = 1_000_000
    monkeypatch.setattr(auth_module.time, "time", lambda: float(issued_at))

    token = create_session_token(username="admin", role="operator")
    context = parse_session_token(token)
    assert context is not None
    assert context.username == "admin"
    assert context.role == "operator"

    monkeypatch.setattr(
        auth_module.time,
        "time",
        lambda: float(issued_at + settings.auth_session_ttl_seconds - 1),
    )
    assert parse_session_token(token) is not None

    monkeypatch.setattr(
        auth_module.time,
        "time",
        lambda: float(issued_at + settings.auth_session_ttl_seconds),
    )
    assert parse_session_token(token) is None


def test_local_login_sets_session_cookie(raw_client: TestClient) -> None:
    response = raw_client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin", "role": "operator"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/v2"
    set_cookie = response.headers.get("set-cookie", "")
    assert "gmai_session=" in set_cookie
    assert f"Max-Age={settings.auth_session_ttl_seconds}" in set_cookie


def test_source_authority_reassignment_is_admin_or_reviewer_only(
    raw_client: TestClient,
) -> None:
    source_id = uuid.uuid4()
    payload = {
        "target_regulatory_authority_id": str(uuid.uuid4()),
        "reason": "Authorization boundary regression test for controlled source remediation.",
    }

    raw_client.headers.update({
        "X-GMAI-Role": "operator",
        "X-GMAI-User": "operator",
    })
    blocked = raw_client.post(
        f"/api/v1/regulatory-intelligence/official-sources/{source_id}/reassign-authority",
        json=payload,
    )
    assert blocked.status_code == 403
    assert blocked.json()["allowed_roles"] == ["admin", "reviewer"]

    raw_client.headers.update({
        "X-GMAI-Role": "admin",
        "X-GMAI-User": "admin",
    })
    allowed = raw_client.post(
        f"/api/v1/regulatory-intelligence/official-sources/{source_id}/reassign-authority",
        json=payload,
    )
    assert allowed.status_code == 400
    assert "Active official source not found" in allowed.json()["detail"]


def test_coverage_batch_linkage_reconciliation_is_admin_or_reviewer_only(
    raw_client: TestClient,
) -> None:
    batch_id = uuid.uuid4()

    raw_client.headers.update({
        "X-GMAI-Role": "operator",
        "X-GMAI-User": "operator",
    })

    blocked = raw_client.post(
        f"/api/v1/global-intelligence/registry/"
        f"coverage-batches/{batch_id}/"
        "reconcile-existing-source-linkage"
    )

    assert blocked.status_code == 403
    assert blocked.json()["allowed_roles"] == [
        "admin",
        "reviewer",
    ]

    raw_client.headers.update({
        "X-GMAI-Role": "admin",
        "X-GMAI-User": "admin",
    })

    allowed = raw_client.post(
        f"/api/v1/global-intelligence/registry/"
        f"coverage-batches/{batch_id}/"
        "reconcile-existing-source-linkage"
    )

    assert allowed.status_code == 400
    assert (
        "Coverage evidence batch not found"
        in allowed.json()["detail"]
    )


def test_agent_run_cancellation_requires_admin_role(raw_client: TestClient) -> None:
    run_id = uuid.uuid4()
    payload = {"reason": "Authorization regression test for runtime cancellation."}

    raw_client.headers.update({
        "X-GMAI-Role": "operator",
        "X-GMAI-User": "operator",
    })
    blocked = raw_client.post(
        f"/api/v1/agent-runs/{run_id}/cancel",
        json=payload,
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "AgentRun cancellation requires the admin role"

    raw_client.headers.update({
        "X-GMAI-Role": "admin",
        "X-GMAI-User": "admin",
    })
    allowed = raw_client.post(
        f"/api/v1/agent-runs/{run_id}/cancel",
        json=payload,
    )
    assert allowed.status_code == 404
    assert allowed.json()["detail"] == "Agent run not found"

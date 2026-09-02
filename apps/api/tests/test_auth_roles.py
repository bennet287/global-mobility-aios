from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.auth import is_public_path


def test_public_client_routes_do_not_require_operator_auth(raw_client: TestClient) -> None:
    response = raw_client.post("/api/v1/public/lookup", json={})
    assert response.status_code == 400


def test_public_prefix_does_not_match_similarly_named_private_path() -> None:
    assert is_public_path("/api/v1/public/intake") is True
    assert is_public_path("/api/v1/publicity") is False


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


def test_local_login_sets_session_cookie(raw_client: TestClient) -> None:
    response = raw_client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin", "role": "operator"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/v2"
    assert "gmai_session=" in response.headers.get("set-cookie", "")

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

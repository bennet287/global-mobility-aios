from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


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


def test_local_login_sets_session_cookie(raw_client: TestClient) -> None:
    response = raw_client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin", "role": "operator"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/v2"
    assert "gmai_session=" in response.headers.get("set-cookie", "")


from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


LOCAL_ORIGIN = "http://127.0.0.1:3000"
UNAPPROVED_ORIGIN = "https://unapproved.example"
REQUESTED_HEADERS = "content-type,x-gmai-role,x-gmai-user"


@pytest.mark.parametrize(
    ("path", "method"),
    [
        (f"/api/v1/eligibility/{uuid.uuid4()}/latest", "GET"),
        ("/api/v1/eligibility/evaluate", "POST"),
    ],
)
def test_local_eligibility_preflight_permits_authenticated_operator_headers(
    raw_client: TestClient,
    path: str,
    method: str,
) -> None:
    response = raw_client.options(
        path,
        headers={
            "Origin": LOCAL_ORIGIN,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": REQUESTED_HEADERS,
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == LOCAL_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    allowed_headers = {
        header.strip().lower()
        for header in response.headers["access-control-allow-headers"].split(",")
    }
    assert {"content-type", "x-gmai-role", "x-gmai-user"} <= allowed_headers


def test_authenticated_eligibility_requests_reach_routes_with_cors(
    raw_client: TestClient,
) -> None:
    headers = {
        "Origin": LOCAL_ORIGIN,
        "X-GMAI-Role": "admin",
        "X-GMAI-User": "frontend-operator",
    }
    lead_id = uuid.uuid4()

    get_response = raw_client.get(
        f"/api/v1/eligibility/{lead_id}/latest",
        headers=headers,
    )
    post_response = raw_client.post(
        "/api/v1/eligibility/evaluate",
        headers=headers,
        json={"lead_id": str(lead_id), "profile": {}},
    )

    assert get_response.status_code == 404
    assert post_response.status_code == 404
    for response in (get_response, post_response):
        assert response.headers["access-control-allow-origin"] == LOCAL_ORIGIN
        assert response.headers["access-control-allow-credentials"] == "true"


@pytest.mark.parametrize("method", ["get", "post"])
def test_unauthorized_eligibility_requests_remain_unauthorized_and_cors_visible(
    raw_client: TestClient,
    method: str,
) -> None:
    lead_id = uuid.uuid4()
    if method == "get":
        response = raw_client.get(
            f"/api/v1/eligibility/{lead_id}/latest",
            headers={"Origin": LOCAL_ORIGIN},
        )
    else:
        response = raw_client.post(
            "/api/v1/eligibility/evaluate",
            headers={"Origin": LOCAL_ORIGIN},
            json={"lead_id": str(lead_id), "profile": {}},
        )

    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == LOCAL_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


def test_unapproved_origin_preflight_is_denied(raw_client: TestClient) -> None:
    response = raw_client.options(
        "/api/v1/eligibility/evaluate",
        headers={
            "Origin": UNAPPROVED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": REQUESTED_HEADERS,
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.test_organization_autonomy_evidence_evaluation import (
    _foundation,
    _observation,
    _ordinary_source,
)
from tests.test_organization_autonomy_promotion_policy import (
    CAPABILITY_KEY,
    CONTEXT_SCOPE,
    POSITION_KEY,
)


BASE = "/api/v1/organization/transparency/autonomy/profiles"


def _summary_path(context_scope: str = CONTEXT_SCOPE) -> str:
    return (
        f"{BASE}/{POSITION_KEY}/{CAPABILITY_KEY}/evidence-evaluation"
        f"?context_scope={context_scope.replace(':', '%3A')}"
    )


def _provenance_path(context_scope: str = CONTEXT_SCOPE, *, limit: int = 50) -> str:
    return (
        f"{BASE}/{POSITION_KEY}/{CAPABILITY_KEY}/evidence-evaluation/provenance"
        f"?context_scope={context_scope.replace(':', '%3A')}&limit={limit}"
    )


def test_i4_board_summary_and_provenance_are_bounded_get_only(
    client: TestClient,
    raw_client: TestClient,
    db_session,
) -> None:
    profile, policy = _foundation(db_session)
    source = _ordinary_source(db_session, key="api-unqualified")
    observation = _observation(db_session, profile, source, key="api-unqualified")

    summary = client.get(_summary_path())
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["profile_id"] == str(profile.id)
    assert body["evaluation_policy_id"] == str(policy.id)
    assert body["candidate_count"] == 1
    assert body["qualified_count"] == 0
    assert body["excluded_unqualified_source_count"] == 1
    assert len(body["recent_provenance"]) <= 10
    assert body["recent_provenance"][0]["observation_id"] == str(observation.id)
    assert "payload_json" not in summary.text
    assert "assessment_json" not in summary.text

    provenance = client.get(_provenance_path(limit=1))
    assert provenance.status_code == 200, provenance.text
    page = provenance.json()
    assert page["profile_id"] == str(profile.id)
    assert page["evaluation_policy_id"] == str(policy.id)
    assert page["page_limit"] == 1
    assert len(page["items"]) == 1
    assert "payload_json" not in provenance.text
    assert "assessment_json" not in provenance.text

    denied_headers = {"X-GMAI-Role": "operator", "X-GMAI-User": "operator-user"}
    assert raw_client.get(_summary_path(), headers=denied_headers).status_code == 403
    assert raw_client.get(_provenance_path(), headers=denied_headers).status_code == 403

    admin_headers = {"X-GMAI-Role": "admin", "X-GMAI-User": "board-human"}
    for path in (_summary_path(), _provenance_path()):
        assert raw_client.post(path, headers=admin_headers, json={}).status_code == 405
        assert raw_client.put(path, headers=admin_headers, json={}).status_code == 405
        assert raw_client.patch(path, headers=admin_headers, json={}).status_code == 405
        assert raw_client.delete(path, headers=admin_headers).status_code == 405

    assert client.get(_provenance_path(limit=101)).status_code == 422


def test_i4_read_surface_returns_404_without_current_exact_profile_policy(
    client: TestClient,
) -> None:
    missing_context = "austria:i4-missing-policy"
    assert client.get(_summary_path(missing_context)).status_code == 404
    assert client.get(_provenance_path(missing_context)).status_code == 404


def test_i4_openapi_exposes_only_server_time_get_contract() -> None:
    schema = app.openapi()
    summary_path = f"{BASE}/{{position_key}}/{{capability_key}}/evidence-evaluation"
    provenance_path = (
        f"{BASE}/{{position_key}}/{{capability_key}}/evidence-evaluation/provenance"
    )
    http_methods = {"get", "post", "put", "patch", "delete"}

    assert summary_path in schema["paths"]
    assert provenance_path in schema["paths"]
    assert {method for method in schema["paths"][summary_path] if method in http_methods} == {"get"}
    assert {method for method in schema["paths"][provenance_path] if method in http_methods} == {"get"}

    summary_parameters = {
        parameter["name"] for parameter in schema["paths"][summary_path]["get"].get("parameters", [])
    }
    provenance_parameters = {
        parameter["name"]
        for parameter in schema["paths"][provenance_path]["get"].get("parameters", [])
    }
    assert "context_scope" in summary_parameters
    assert "evaluation_as_of" not in summary_parameters
    assert {"context_scope", "limit", "cursor"}.issubset(provenance_parameters)
    assert "evaluation_as_of" not in provenance_parameters

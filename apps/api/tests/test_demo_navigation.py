from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from scripts.seed_demo_data import seed_demo_data


def test_demo_hub_lists_operator_flow(client: TestClient, db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    response = client.get("/admin/demo")

    assert response.status_code == 200
    assert "Demo Command Center v5.3" in response.text
    assert "/admin/controlled-agents" in response.text
    assert "/admin/agent-output-reviews" in response.text
    assert "/admin/client-communications/drafts" in response.text
    assert "/admin/audit-logs" in response.text
    assert "python scripts/check_local_quality.py" in response.text
    assert "No automatic email" in response.text


def test_demo_navigation_json_reports_seeded_counts(client: TestClient, db_session: Session) -> None:
    seed_demo_data(db_session, reset_demo=True)

    response = client.get("/api/v1/admin-demo/navigation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v5.3"
    assert payload["demo_leads"] == 4
    assert payload["demo_agent_runs"] == 4
    assert payload["demo_client_drafts"] >= 5
    assert {item["path"] for item in payload["primary_flow"]} >= {
        "/admin/v2",
        "/admin/controlled-agents",
        "/admin/agent-output-reviews",
        "/admin/client-communications/drafts",
        "/admin/audit-logs",
    }

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.conftest import create_lead


def test_agent_chat_endpoint_returns_decision(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session, name="Chat Lead")
    response = client.post(
        "/api/v1/agent-chat",
        json={
            "message": f"create a sales summary for {lead.full_name}",
            "conversation_history": [],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "reply" in data
    assert data["decision"]["decision"] == "propose_action"
    assert data["decision"]["agent_name"] == "sales_summary_agent"
    assert data["decision"]["lead_id"] == str(lead.id)


def test_agent_chat_uses_lead_hint(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session, name="Hint Chat Lead")
    response = client.post(
        "/api/v1/agent-chat",
        json={
            "message": "draft an update",
            "lead_hint": str(lead.id),
            "conversation_history": [],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["decision"]["decision"] == "propose_action"
    assert data["decision"]["agent_name"] == "client_drafting_agent"
    assert data["decision"]["lead_id"] == str(lead.id)


def test_agent_chat_requires_auth(client: TestClient) -> None:
    # Clear auth header to verify middleware rejects unauthenticated request.
    client.headers.pop("X-GMAI-Role", None)
    response = client.post(
        "/api/v1/agent-chat",
        json={"message": "hello"},
    )
    assert response.status_code == 401

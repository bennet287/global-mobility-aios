from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.conftest import create_lead


def _create_target_run(client: TestClient, lead_id: str) -> None:
    payload = {
        "agent_name": "application_readiness_agent",
        "task": "Explain readiness",
        "lead_id": lead_id,
        "context": {"truth_clear": True, "documents_verified": False},
        "actor": "pytest",
    }
    response = client.post("/api/v1/controlled-agents/run", json=payload)
    assert response.status_code == 200


def test_run_eligibility_coach(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session, name="Coach Lead", target_country="Germany")
    _create_target_run(client, str(lead.id))

    response = client.post(f"/api/v1/coaching/eligibility/{lead.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["coach_agent_name"] == "eligibility_coach"
    assert data["target_agent_name"] == "application_readiness_agent"
    assert "conclusion_valid" in data
    assert data["status"] == "pending"


def test_list_coach_reviews(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session, name="Coach Lead 2", target_country="Germany")
    _create_target_run(client, str(lead.id))
    client.post(f"/api/v1/coaching/eligibility/{lead.id}")

    response = client.get(f"/api/v1/coaching/eligibility/{lead.id}/reviews")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_submit_coach_feedback(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session, name="Coach Lead 3", target_country="Germany")
    _create_target_run(client, str(lead.id))
    review_response = client.post(f"/api/v1/coaching/eligibility/{lead.id}")
    review_id = review_response.json()["id"]

    response = client.post(
        f"/api/v1/coaching/reviews/{review_id}/feedback",
        json={"operator_feedback": "Looks good after source added.", "override_decision": "approved"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert "Looks good" in data["operator_feedback"]

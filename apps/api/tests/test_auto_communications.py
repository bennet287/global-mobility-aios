from __future__ import annotations

from sqlmodel import Session

from app.models.domain import Lead, LeadIntent, LeadStatus
from app.services.auto_communications import list_auto_communications


def _create_lead(session: Session, **kwargs) -> Lead:
    lead = Lead(
        full_name=kwargs.get("full_name", "Test Lead"),
        email=kwargs.get("email"),
        target_country=kwargs.get("target_country", "Germany"),
        intent=kwargs.get("intent", LeadIntent.overseas_job),
        status=LeadStatus.new,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def test_get_templates(client) -> None:
    response = client.get("/api/v1/auto-communications/templates")
    assert response.status_code == 200
    data = response.json()
    assert "intake_welcome" in data["templates"]


def test_create_auto_communication(client, db_session: Session) -> None:
    lead = _create_lead(db_session, full_name="Auto Client")

    response = client.post(
        f"/api/v1/auto-communications/leads/{lead.id}?trigger=intake_submitted",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["created_count"] == 1
    assert data["communications"][0]["trigger"] == "intake_welcome"
    assert "subject" in data["communications"][0]


def test_list_auto_communications(client, db_session: Session) -> None:
    lead = _create_lead(db_session, full_name="List Auto Client")
    client.post(
        f"/api/v1/auto-communications/leads/{lead.id}?trigger=eligibility_ready",
        json={"score": "75", "status": "likely_eligible"},
    )

    response = client.get(f"/api/v1/auto-communications/leads/{lead.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(c["trigger"] == "eligibility_update" for c in data["communications"])


def test_intake_creates_welcome_communication(client, db_session: Session) -> None:
    response = client.post(
        "/api/v1/public/intake",
        json={
            "full_name": "Intake Auto Client",
            "email": "autoclient@example.com",
            "goal": "Work in Germany as a nurse",
            "nationality": "India",
            "profession": "Registered Nurse",
            "target_country": "Germany",
        },
    )
    assert response.status_code == 200
    lead_id = response.json()["lead_id"]

    follow_ups = list_auto_communications(db_session, lead_id)
    assert len(follow_ups) >= 1
    assert "intake_welcome" in follow_ups[0].message

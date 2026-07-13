from __future__ import annotations

from sqlmodel import Session

from app.models.domain import IntakeSession, Lead, LeadIntent, LeadStatus


def _create_lead(session: Session, **kwargs) -> Lead:
    lead = Lead(
        full_name=kwargs.get("full_name", "Test Lead"),
        email=kwargs.get("email"),
        phone=kwargs.get("phone"),
        target_country=kwargs.get("target_country", "Germany"),
        intent=kwargs.get("intent", LeadIntent.overseas_job),
        status=LeadStatus.new,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def test_lookup_by_email(client, db_session: Session) -> None:
    lead = _create_lead(db_session, full_name="Return Client", email="return@example.com")

    response = client.post("/api/v1/public/lookup", json={"email": "return@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["lead_id"] == str(lead.id)
    assert data[0]["full_name"] == "Return Client"


def test_lookup_by_session_token(client, db_session: Session) -> None:
    lead = _create_lead(db_session, full_name="Token Client")
    session = IntakeSession(
        lead_id=lead.id,
        session_token="test-token-123",
        status="completed",
        source="public_intake",
    )
    db_session.add(session)
    db_session.commit()

    response = client.post("/api/v1/public/lookup", json={"session_token": "test-token-123"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["lead_id"] == str(lead.id)


def test_return_dashboard(client, db_session: Session) -> None:
    lead = _create_lead(db_session, full_name="Dashboard Client", target_country="Canada", intent=LeadIntent.study_abroad)

    response = client.get(f"/api/v1/public/return/{lead.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == str(lead.id)
    assert data["full_name"] == "Dashboard Client"
    assert len(data["checklist"]) > 0
    assert data["next_action"]


def test_return_dashboard_not_found(client) -> None:
    import uuid

    response = client.get(f"/api/v1/public/return/{uuid.uuid4()}")
    assert response.status_code == 404

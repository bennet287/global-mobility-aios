from __future__ import annotations

from sqlmodel import Session

from app.models.domain import Lead, LeadIntent, LeadStatus
from app.services.client_portal import issue_client_portal_grant


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
    _create_lead(db_session, full_name="Return Client", email="return@example.com")

    response = client.post("/api/v1/public/lookup", json={"email": "return@example.com"})
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()


def test_lookup_by_session_token(client, db_session: Session) -> None:
    lead = _create_lead(db_session, full_name="Token Client")
    _, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )

    response = client.post("/api/v1/public/lookup", json={"session_token": token})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["lead_id"] == str(lead.id)


def test_return_dashboard(client, db_session: Session) -> None:
    lead = _create_lead(db_session, full_name="Dashboard Client", target_country="Canada", intent=LeadIntent.study_abroad)
    _, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )

    response = client.get(
        f"/api/v1/public/return/{lead.id}",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == str(lead.id)
    assert data["full_name"] == "Dashboard Client"
    assert len(data["checklist"]) > 0
    assert data["next_action"]


def test_return_dashboard_not_found(client, db_session: Session) -> None:
    import uuid

    lead = _create_lead(db_session, full_name="Scoped Client")
    _, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    response = client.get(
        f"/api/v1/public/return/{uuid.uuid4()}",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert response.status_code == 404

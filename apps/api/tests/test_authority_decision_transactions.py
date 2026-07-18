from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import ApplicationRecord, AuditLog, FollowUp
from app.routers import authority_decision

from .conftest import create_application, create_lead, enum_value


def test_authority_transition_commits_state_follow_up_and_audit_together(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead, status="submitted")

    response = client.post(
        f"/api/v1/authority-decision/applications/{application.id}/approve",
        json={
            "note": "Approval received.",
            "reference_number": "AUTH-2026-001",
            "decision_date": "2026-07-18",
            "create_follow_up": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "approved_by_authority"
    assert payload["follow_up"] is not None

    db_session.refresh(application)
    db_session.refresh(lead)
    assert application.status == "approved_by_authority"
    assert enum_value(lead.status) == "converted"
    assert "reference=AUTH-2026-001" in (lead.notes or "")
    assert "decision_date=2026-07-18" in (lead.notes or "")
    assert "note=Approval received." in (lead.notes or "")

    follow_ups = db_session.exec(select(FollowUp).where(FollowUp.lead_id == lead.id)).all()
    audits = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "application",
            AuditLog.entity_id == str(application.id),
            AuditLog.action == "authority_decision_recorded",
        )
    ).all()
    assert len(follow_ups) == 1
    assert len(audits) == 1


def test_authority_transition_rolls_back_every_change_when_audit_fails(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead, status="submitted")
    original_lead_status = enum_value(lead.status)
    original_notes = lead.notes

    def fail_audit(*args, **kwargs):
        raise RuntimeError("simulated audit failure")

    monkeypatch.setattr(authority_decision, "record_audit", fail_audit)

    response = client.post(
        f"/api/v1/authority-decision/applications/{application.id}/approve",
        json={"note": "This must roll back.", "create_follow_up": True},
    )

    assert response.status_code == 500
    assert response.json()["detail"]["message"] == "Could not update authority decision status."

    persisted_application = db_session.get(ApplicationRecord, application.id)
    db_session.refresh(lead)
    assert persisted_application is not None
    db_session.refresh(persisted_application)
    assert persisted_application.status == "submitted"
    assert enum_value(lead.status) == original_lead_status
    assert lead.notes == original_notes
    assert db_session.exec(select(FollowUp).where(FollowUp.lead_id == lead.id)).all() == []
    assert db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "application",
            AuditLog.entity_id == str(application.id),
            AuditLog.action == "authority_decision_recorded",
        )
    ).all() == []

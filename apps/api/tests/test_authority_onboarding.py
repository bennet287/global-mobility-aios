from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog, FollowUp

from .conftest import create_application, create_lead, enum_value


def test_authority_approval_converts_lead_and_onboarding_is_audited(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    app_record = create_application(db_session, lead, status="submitted")

    approval = client.post(
        f"/api/v1/authority-decision/applications/{app_record.id}/approve",
        json={"note": "Authority approved.", "create_follow_up": False},
    )
    assert approval.status_code == 200
    assert approval.json()["status"] == "approved_by_authority"

    db_session.refresh(lead)
    assert enum_value(lead.status) == "converted"

    generated = client.post(
        f"/api/v1/post-approval-onboarding/leads/{lead.id}/generate",
        json={"note": "Generate onboarding checklist."},
    )
    assert generated.status_code == 200
    assert generated.json()["created_count"] > 0

    task = db_session.exec(select(FollowUp).where(FollowUp.lead_id == lead.id)).first()
    assert task is not None
    completed = client.post(
        f"/api/v1/post-approval-onboarding/follow-ups/{task.id}/complete",
        json={"note": "Task checked."},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    actions = {log.action for log in db_session.exec(select(AuditLog)).all()}
    assert {"authority_decision_recorded", "onboarding_generated", "onboarding_task_completed"}.issubset(actions)

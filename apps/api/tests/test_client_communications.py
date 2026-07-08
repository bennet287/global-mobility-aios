from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog, FollowUp

from .conftest import create_application, create_lead, enum_value


def test_client_communication_stores_enum_safe_status_and_displays_public_state(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session)
    create_application(db_session, lead, status="approved_by_authority")

    created = client.post(f"/api/v1/client-communications/leads/{lead.id}/drafts/approval_confirmation", json={})
    assert created.status_code == 200
    draft = created.json()["draft"]
    draft_id = draft["draft"]["id"]
    assert draft["communication"]["status"] == "draft"

    follow_up = db_session.get(FollowUp, uuid.UUID(draft_id))
    assert follow_up is not None
    assert enum_value(follow_up.status) == "pending"

    reviewed = client.post(
        f"/api/v1/client-communications/drafts/{draft_id}/mark-reviewed",
        json={"note": "Reviewed manually."},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["draft"]["communication"]["status"] == "reviewed"

    db_session.refresh(follow_up)
    assert enum_value(follow_up.status) == "completed"

    actions = {log.action for log in db_session.exec(select(AuditLog)).all()}
    assert {"client_draft_generated", "client_draft_reviewed"}.issubset(actions)


def test_unreviewed_client_draft_send_is_blocked(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    create_application(db_session, lead, status="approved_by_authority")
    created = client.post(f"/api/v1/client-communications/leads/{lead.id}/drafts/travel_checklist", json={})
    draft_id = created.json()["draft"]["draft"]["id"]

    response = client.post(f"/api/v1/client-communications/drafts/{draft_id}/send-blocked")

    assert response.status_code == 409
    assert response.json()["blocker"] == "human_review_required"

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import ApplicationRecord, AuditLog

from .conftest import create_document, create_lead, create_truth_claim


def test_rejected_truth_claim_blocks_controlled_draft(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    create_truth_claim(db_session, lead, verdict="rejected")
    create_document(db_session, lead, status="verified")

    response = client.post(f"/api/v1/applications/leads/{lead.id}/controlled-draft", json={})

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["blocker"] == "readiness_not_clear"
    assert "truth_claim_rejected" in detail["blockers"]


def test_ready_lead_can_draft_approve_submit_and_audit(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    create_document(db_session, lead, status="verified")

    draft_response = client.post(f"/api/v1/applications/leads/{lead.id}/controlled-draft", json={})
    assert draft_response.status_code == 200
    app_id = draft_response.json()["application"]["id"]

    approve_response = client.post(f"/api/v1/applications/{app_id}/approve", json={"note": "Human approved."})
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    submit_response = client.post(f"/api/v1/applications/{app_id}/submit", json={"note": "Submitted after approval."})
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "submitted"

    app_record = db_session.get(ApplicationRecord, uuid.UUID(app_id))
    assert app_record is not None
    assert app_record.status == "submitted"

    actions = {log.action for log in db_session.exec(select(AuditLog)).all()}
    assert {"application_drafted", "application_approved", "application_submitted"}.issubset(actions)

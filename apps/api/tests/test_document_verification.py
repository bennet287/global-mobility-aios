from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog

from .conftest import create_document, create_lead


def test_bulk_verify_documents_updates_readiness_and_audit(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    create_document(db_session, lead, status="missing", document_type="passport")
    create_document(db_session, lead, status="received", document_type="admission_letter")

    response = client.post(
        f"/api/v1/document-verification/leads/{lead.id}/bulk-verify",
        json={"note": "All documents checked."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "verified"
    assert payload["updated_count"] == 2
    assert payload["summary"]["all_verified"] is True

    audit = db_session.exec(select(AuditLog).where(AuditLog.action == "documents_bulk_verified")).first()
    assert audit is not None
    assert audit.entity_id == str(lead.id)

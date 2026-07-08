from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog, SourceReference

from .conftest import create_lead, create_truth_claim, enum_value


def test_truth_resolution_unblocks_rejected_claim_and_writes_audit(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    claim = create_truth_claim(db_session, lead, verdict="rejected", requires_review=True)
    db_session.add(
        SourceReference(
            truth_claim_id=claim.id,
            source_url="https://www.auswaertiges-amt.de/",
            source_type="official",
            title="Official source",
            country="Germany",
        )
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/truth/claims/{claim.id}/resolve",
        json={
            "resolution_note": "Resolved against official source.",
            "resolution_status": "resolved",
            "require_sources": True,
            "create_follow_up": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["truth_resolution"]["can_progress"] is True

    db_session.refresh(claim)
    assert enum_value(claim.verdict).lower() in {"verified", "verificationstatus.verified"}
    assert claim.requires_human_review is False

    audit = db_session.exec(select(AuditLog).where(AuditLog.action == "truth_claim_resolved")).first()
    assert audit is not None
    assert audit.entity_id == str(claim.id)

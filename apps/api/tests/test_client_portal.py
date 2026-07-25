from __future__ import annotations

import hashlib
from datetime import timedelta
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    AuditLog,
    ClientPortalAccessGrant,
    DocumentRecord,
    now_utc,
)
from app.services.client_portal import issue_client_portal_grant
from tests.conftest import create_lead


def test_portal_grant_is_hashed_scoped_and_audited(client, raw_client, db_session: Session) -> None:
    lead = create_lead(db_session, name="Portal Client", target_country="Austria")
    document = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport.pdf",
        status="verified",
    )
    application = ApplicationRecord(
        lead_id=lead.id,
        domain="visa",
        target_country="Austria",
        status="preparation",
    )
    db_session.add(document)
    db_session.add(application)
    db_session.commit()

    issued = client.post(
        "/api/v1/client-portal/grants",
        json={
            "lead_id": str(lead.id),
            "label": "Primary client access",
            "expires_in_days": 14,
        },
    )
    assert issued.status_code == 201, issued.text
    payload = issued.json()
    token = payload["token"]
    assert token.startswith("gmai_portal_")
    assert payload["portal_path"] == f"/portal?token={token}"

    grant = db_session.get(ClientPortalAccessGrant, UUID(payload["grant"]["id"]))
    assert grant is not None
    assert grant.token_hash == hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert token not in grant.token_hash

    dashboard = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()
    assert data["client_name"] == "Portal Client"
    assert data["target_country"] == "Austria"
    assert data["application_stage"] == "preparation"
    assert data["documents"][0]["filename"] == "passport.pdf"
    assert "email" not in data
    assert "eligibility" not in data
    assert "follow_ups" not in data

    db_session.refresh(grant)
    assert grant.access_count == 1
    assert grant.last_accessed_at is not None
    actions = {
        row.action
        for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_id == str(grant.id))
        ).all()
    }
    assert {"client_portal_grant_created", "client_portal_accessed"} <= actions


def test_portal_token_cannot_cross_lead_scope_and_revocation_is_immediate(
    client,
    raw_client,
    db_session: Session,
) -> None:
    first = create_lead(db_session, name="First Portal Client")
    second = create_lead(db_session, name="Second Portal Client")
    grant, token = issue_client_portal_grant(
        db_session,
        first.id,
        actor="pytest-operator",
    )

    cross_scope = raw_client.get(
        f"/api/v1/public/return/{second.id}",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert cross_scope.status_code == 404

    revoked = client.post(
        f"/api/v1/client-portal/grants/{grant.id}/revoke",
        json={"reason": "Client requested access closure."},
    )
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["status"] == "revoked"

    denied = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert denied.status_code == 404


def test_expired_portal_grant_is_denied(client, raw_client, db_session: Session) -> None:
    lead = create_lead(db_session, name="Expired Portal Client")
    grant, token = issue_client_portal_grant(
        db_session,
        lead.id,
        actor="pytest-operator",
    )
    grant.expires_at = now_utc() - timedelta(minutes=1)
    db_session.add(grant)
    db_session.commit()

    denied = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert denied.status_code == 404
    db_session.refresh(grant)
    assert grant.status == "expired"


def test_portal_grant_issuance_requires_operator_auth(raw_client, db_session: Session) -> None:
    lead = create_lead(db_session, name="Protected Portal Client")
    response = raw_client.post(
        "/api/v1/client-portal/grants",
        json={"lead_id": str(lead.id), "expires_in_days": 30},
    )
    assert response.status_code == 401

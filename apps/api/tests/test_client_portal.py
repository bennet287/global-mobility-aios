from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AgencySubmission,
    ApplicationAuthorityChecklistItem,
    ApplicationRecord,
    AuditLog,
    AuthorityAppointment,
    ClientPortalAccessGrant,
    DocumentRecord,
    ExternalAgency,
    ExternalAgencyAssignment,
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


def test_portal_dashboard_exposes_agency_workflows(
    client, raw_client, db_session: Session
) -> None:
    lead = create_lead(db_session, name="Agency Workflow Client", target_country="Germany")
    application = ApplicationRecord(
        lead_id=lead.id,
        domain="visa",
        target_country="Germany",
        status="preparation",
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)

    agency = ExternalAgency(
        name="Partner Agency",
        status="active",
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add(agency)
    db_session.commit()
    db_session.refresh(agency)

    scheduled_at = datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc)
    submitted_at = datetime(2026, 8, 10, 14, 0, 0, tzinfo=timezone.utc)

    appointment = AuthorityAppointment(
        application_id=application.id,
        appointment_type="interview",
        authority_name="German Consulate Mumbai",
        location="Mumbai",
        scheduled_at=scheduled_at,
        timezone="Asia/Kolkata",
        status="scheduled",
        reference_number="APT-001",
        created_by="pytest",
        updated_by="pytest",
    )
    submission = AgencySubmission(
        application_id=application.id,
        authority_name="German Consulate Mumbai",
        submission_channel="online",
        submitted_at=submitted_at,
        status="submitted",
        reference_number="SUB-001",
        created_by="pytest",
        updated_by="pytest",
    )
    assignment = ExternalAgencyAssignment(
        application_id=application.id,
        external_agency_id=agency.id,
        status="assigned",
        sla_due_at=datetime.now(timezone.utc) + timedelta(days=3),
        sla_status="on_track",
        created_by="pytest",
        updated_by="pytest",
    )
    checklist_item = ApplicationAuthorityChecklistItem(
        application_id=application.id,
        authority_name="German Consulate Mumbai",
        item_key="passport_copy",
        item_label="Copy of passport",
        category="document",
        is_required=True,
        status="pending",
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add_all([appointment, submission, assignment, checklist_item])
    db_session.commit()

    grant, token = issue_client_portal_grant(
        db_session, lead.id, actor="pytest-operator"
    )
    dashboard = raw_client.get(
        "/api/v1/public/client-portal/dashboard",
        headers={"X-GMAI-Portal-Token": token},
    )
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()

    assert len(data["appointments"]) == 1
    assert data["appointments"][0]["authority_name"] == "German Consulate Mumbai"
    assert data["appointments"][0]["appointment_type"] == "interview"
    assert data["appointments"][0]["reference_number"] == "APT-001"

    assert len(data["submissions"]) == 1
    assert data["submissions"][0]["status"] == "submitted"
    assert data["submissions"][0]["reference_number"] == "SUB-001"

    assert len(data["external_agency_assignments"]) == 1
    assert data["external_agency_assignments"][0]["agency_name"] == "Partner Agency"
    assert data["external_agency_assignments"][0]["status"] == "assigned"
    assert data["external_agency_assignments"][0]["sla_status"] == "on_track"
    assert data["external_agency_assignments"][0]["sla_due_at"] is not None

    assert len(data["authority_checklist"]) == 1
    assert data["authority_checklist"][0]["item_label"] == "Copy of passport"
    assert data["authority_checklist"][0]["is_required"] is True

    # Internal-only fields are never exposed to the portal.
    for section in ("appointments", "submissions", "external_agency_assignments", "authority_checklist"):
        assert data[section][0]
        assert "notes" not in data[section][0]
        assert "created_by" not in data[section][0]
        assert "updated_by" not in data[section][0]

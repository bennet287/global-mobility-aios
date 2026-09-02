from __future__ import annotations

import hashlib
from datetime import timedelta
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    CorporateAccount,
    CorporateComplianceEvent,
    CorporateMobilityCase,
    CorporateRelocationTask,
    EcosystemPortalAccessGrant,
    now_utc,
)
from app.services.ecosystem_portal import issue_ecosystem_portal_grant
from tests.conftest import create_lead


def _account(session: Session, name: str, actor: str = "pytest-admin") -> CorporateAccount:
    account = CorporateAccount(
        legal_name=f"{name} Legal GmbH",
        display_name=name,
        primary_country="Austria",
        account_status="active",
        created_by=actor,
        updated_by=actor,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def _case(
    session: Session,
    account: CorporateAccount,
    reference: str,
    employee_name: str,
) -> CorporateMobilityCase:
    lead = create_lead(session, name=employee_name, target_country="Germany")
    case = CorporateMobilityCase(
        corporate_account_id=account.id,
        employee_lead_id=lead.id,
        case_reference=reference,
        case_type="employee_relocation",
        status="active",
        origin_country="Austria",
        destination_country="Germany",
        compliance_due_date=now_utc() + timedelta(days=10),
        human_review_required=True,
        created_by="pytest-admin",
        updated_by="pytest-admin",
    )
    session.add(case)
    session.commit()
    session.refresh(case)
    return case


def test_ecosystem_grant_is_hash_only_account_scoped_and_audited(
    client,
    raw_client,
    db_session: Session,
) -> None:
    account = _account(db_session, "Northstar Employer")
    case = _case(db_session, account, "NS-2026-001", "Northstar Employee")
    db_session.add(CorporateComplianceEvent(
        corporate_mobility_case_id=case.id,
        event_type="registration",
        title="City registration",
        due_at=now_utc() + timedelta(days=4),
        status="open",
        evidence_required=True,
        created_by="pytest-admin",
        updated_by="pytest-admin",
    ))
    db_session.add(CorporateRelocationTask(
        corporate_mobility_case_id=case.id,
        title="Prepare registration pack",
        category="relocation",
        status="ready",
        owner_role="mobility_operator",
        created_by="pytest-admin",
        updated_by="pytest-admin",
    ))
    db_session.commit()

    response = client.post(
        "/api/v1/ecosystem-portal/grants",
        json={
            "corporate_account_id": str(account.id),
            "audience_type": "employer",
            "label": "Northstar mobility team",
            "expires_in_days": 14,
        },
    )
    assert response.status_code == 201, response.text
    issued = response.json()
    token = issued["token"]
    assert token.startswith("gmai_ecosystem_")
    assert issued["portal_path"] == f"/partner-portal?token={token}"

    grant = db_session.get(EcosystemPortalAccessGrant, UUID(issued["grant"]["id"]))
    assert grant is not None
    assert grant.token_hash == hashlib.sha256(token.encode("utf-8")).hexdigest()
    assert token not in grant.token_hash

    dashboard = raw_client.get(
        "/api/v1/public/ecosystem-portal/dashboard",
        headers={"X-GMAI-Ecosystem-Token": token},
    )
    assert dashboard.status_code == 200, dashboard.text
    data = dashboard.json()
    assert data["account_name"] == "Northstar Employer"
    assert data["audience_type"] == "employer"
    assert data["cases"][0]["case_reference"] == "NS-2026-001"
    assert data["cases"][0]["employee_name"] == "Northstar Employee"
    assert data["cases"][0]["open_compliance_items"] == 1
    assert data["cases"][0]["open_tasks"] == 1
    assert data["upcoming_compliance"][0]["title"] == "City registration"
    assert "contact_email" not in data
    assert "notes" not in data["cases"][0]
    assert "employee_lead_id" not in data["cases"][0]

    actions = set(db_session.exec(
        select(AuditLog.action).where(
            AuditLog.entity_type == "ecosystem_portal_access_grant"
        )
    ).all())
    assert {"ecosystem_portal_grant_created", "ecosystem_portal_accessed"} <= actions


def test_ecosystem_token_cannot_cross_tenant_boundary(
    raw_client,
    db_session: Session,
) -> None:
    account_a = _account(db_session, "Tenant A")
    account_b = _account(db_session, "Tenant B")
    _case(db_session, account_a, "A-ONLY-001", "Employee A")
    _case(db_session, account_b, "B-SECRET-001", "Employee B")
    _, token_a = issue_ecosystem_portal_grant(
        db_session,
        account_a.id,
        actor="tenant-test",
        audience_type="partner",
        label="Tenant A partner",
        expires_in_days=7,
    )

    dashboard = raw_client.get(
        "/api/v1/public/ecosystem-portal/dashboard",
        headers={"X-GMAI-Ecosystem-Token": token_a},
    )
    assert dashboard.status_code == 200
    serialized = dashboard.text
    assert "A-ONLY-001" in serialized
    assert "Employee A" in serialized
    assert "B-SECRET-001" not in serialized
    assert "Employee B" not in serialized
    assert str(account_b.id) not in serialized


def test_ecosystem_grant_revocation_and_expiry_fail_closed(
    client,
    raw_client,
    db_session: Session,
) -> None:
    account = _account(db_session, "Revocation Tenant")
    grant, token = issue_ecosystem_portal_grant(
        db_session,
        account.id,
        actor="issuer",
        audience_type="employer",
        label="Temporary access",
        expires_in_days=1,
    )
    revoked = client.post(
        f"/api/v1/ecosystem-portal/grants/{grant.id}/revoke",
        json={"reason": "Access recipient changed"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert raw_client.get(
        "/api/v1/public/ecosystem-portal/dashboard",
        headers={"X-GMAI-Ecosystem-Token": token},
    ).status_code == 404

    expiring, expired_token = issue_ecosystem_portal_grant(
        db_session,
        account.id,
        actor="issuer",
        audience_type="partner",
        label="Expired access",
        expires_in_days=1,
    )
    expiring.expires_at = now_utc() - timedelta(minutes=1)
    db_session.add(expiring)
    db_session.commit()
    assert raw_client.get(
        "/api/v1/public/ecosystem-portal/dashboard",
        headers={"X-GMAI-Ecosystem-Token": expired_token},
    ).status_code == 404
    db_session.refresh(expiring)
    assert expiring.status == "expired"


def test_ecosystem_grant_management_requires_internal_auth(
    raw_client,
    db_session: Session,
) -> None:
    account = _account(db_session, "Protected Tenant")
    response = raw_client.post(
        "/api/v1/ecosystem-portal/grants",
        json={
            "corporate_account_id": str(account.id),
            "audience_type": "employer",
            "label": "Unauthorized attempt",
            "expires_in_days": 7,
        },
    )
    assert response.status_code == 401
    assert db_session.exec(select(EcosystemPortalAccessGrant)).first() is None

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
    PartnerApiCredential,
    now_utc,
)
from app.services.partner_api import issue_partner_api_credential
from tests.conftest import create_lead


def _account(session: Session, name: str) -> CorporateAccount:
    account = CorporateAccount(
        legal_name=f"{name} Holdings GmbH",
        display_name=name,
        primary_country="Austria",
        account_status="active",
        created_by="pytest-admin",
        updated_by="pytest-admin",
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
    *,
    status: str = "active",
) -> CorporateMobilityCase:
    lead = create_lead(session, name=employee_name, target_country="Germany")
    case = CorporateMobilityCase(
        corporate_account_id=account.id,
        employee_lead_id=lead.id,
        case_reference=reference,
        case_type="employee_relocation",
        status=status,
        origin_country="Austria",
        destination_country="Germany",
        compliance_due_date=now_utc() + timedelta(days=12),
        human_review_required=True,
        created_by="pytest-admin",
        updated_by="pytest-admin",
    )
    session.add(case)
    session.commit()
    session.refresh(case)
    return case


def test_public_v1_contract_is_unauthenticated_versioned_and_data_free(raw_client) -> None:
    root = raw_client.get("/api/public/v1")
    assert root.status_code == 200
    assert root.headers["X-GMAI-API-Version"] == "1.0"
    assert root.headers["Deprecation"] == "false"
    assert root.json()["version"] == "1.0"
    assert "corporate_account_id" not in root.text
    assert "client_name" not in root.text

    capabilities = raw_client.get("/api/public/v1/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.headers["X-GMAI-API-Version"] == "1.0"
    assert capabilities.json()["authentication"]["tenant_scope"] == "derived_from_credential"


def test_partner_key_is_hash_only_and_contract_is_account_scoped(
    client,
    raw_client,
    db_session: Session,
) -> None:
    account_a = _account(db_session, "API Tenant A")
    account_b = _account(db_session, "API Tenant B")
    case_a = _case(db_session, account_a, "API-A-001", "API Employee A")
    case_b = _case(db_session, account_b, "API-B-SECRET", "API Employee B")
    db_session.add(CorporateComplianceEvent(
        corporate_mobility_case_id=case_a.id,
        event_type="permit_renewal",
        title="Tenant A renewal",
        due_at=now_utc() + timedelta(days=6),
        status="open",
        evidence_required=True,
        created_by="pytest-admin",
        updated_by="pytest-admin",
    ))
    db_session.add(CorporateComplianceEvent(
        corporate_mobility_case_id=case_b.id,
        event_type="payroll",
        title="Tenant B confidential payroll",
        due_at=now_utc() + timedelta(days=8),
        status="open",
        evidence_required=True,
        created_by="pytest-admin",
        updated_by="pytest-admin",
    ))
    db_session.commit()

    issued = client.post(
        "/api/v1/partner-api/credentials",
        json={
            "corporate_account_id": str(account_a.id),
            "label": "Tenant A integration",
            "scopes": ["account:read", "cases:read", "compliance:read"],
            "expires_in_days": 90,
        },
    )
    assert issued.status_code == 201, issued.text
    payload = issued.json()
    api_key = payload["api_key"]
    assert api_key.startswith("gmai_partner_live_")
    credential = db_session.get(
        PartnerApiCredential,
        UUID(payload["credential"]["id"]),
    )
    assert credential is not None
    assert credential.key_hash == hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    assert api_key not in credential.key_hash
    assert payload["credential"]["key_prefix"] == api_key[:24]

    headers = {"X-GMAI-Partner-Key": api_key}
    account = raw_client.get("/api/partner/v1/account", headers=headers)
    assert account.status_code == 200
    assert account.headers["X-GMAI-API-Version"] == "1.0"
    assert account.headers["Cache-Control"] == "private, no-store"
    assert account.json()["name"] == "API Tenant A"

    cases = raw_client.get("/api/partner/v1/cases", headers=headers)
    assert cases.status_code == 200, cases.text
    assert cases.json()["meta"] == {
        "page": 1,
        "page_size": 25,
        "total": 1,
        "total_pages": 1,
    }
    assert "API-A-001" in cases.text
    assert "API Employee A" in cases.text
    assert "API-B-SECRET" not in cases.text
    assert "API Employee B" not in cases.text
    assert str(account_b.id) not in cases.text
    assert "employee_lead_id" not in cases.text
    assert "notes" not in cases.text

    compliance = raw_client.get("/api/partner/v1/compliance", headers=headers)
    assert compliance.status_code == 200
    assert "Tenant A renewal" in compliance.text
    assert "Tenant B confidential payroll" not in compliance.text

    audit_actions = set(db_session.exec(
        select(AuditLog.action).where(AuditLog.entity_type == "partner_api_credential")
    ).all())
    assert {"partner_api_credential_created", "partner_api_accessed"} <= audit_actions


def test_partner_api_enforces_scopes_and_pagination(
    raw_client,
    db_session: Session,
) -> None:
    account = _account(db_session, "Scoped API Tenant")
    for index in range(3):
        _case(
            db_session,
            account,
            f"SCOPE-{index + 1}",
            f"Scoped Employee {index + 1}",
        )
    _, api_key = issue_partner_api_credential(
        db_session,
        account.id,
        actor="issuer",
        label="Cases only",
        scopes=["cases:read"],
        expires_in_days=30,
    )
    headers = {"X-GMAI-Partner-Key": api_key}

    page = raw_client.get(
        "/api/partner/v1/cases?page=2&page_size=2",
        headers=headers,
    )
    assert page.status_code == 200
    assert len(page.json()["data"]) == 1
    assert page.json()["meta"] == {
        "page": 2,
        "page_size": 2,
        "total": 3,
        "total_pages": 2,
    }
    assert raw_client.get("/api/partner/v1/account", headers=headers).status_code == 403
    assert raw_client.get("/api/partner/v1/compliance", headers=headers).status_code == 403


def test_partner_api_revocation_expiry_and_account_suspension_fail_closed(
    client,
    raw_client,
    db_session: Session,
) -> None:
    account = _account(db_session, "Lifecycle API Tenant")
    credential, api_key = issue_partner_api_credential(
        db_session,
        account.id,
        actor="issuer",
        label="Lifecycle",
        scopes=["account:read"],
        expires_in_days=30,
    )
    revoked = client.post(
        f"/api/v1/partner-api/credentials/{credential.id}/revoke",
        json={"reason": "Integration retired"},
    )
    assert revoked.status_code == 200
    assert raw_client.get(
        "/api/partner/v1/account",
        headers={"X-GMAI-Partner-Key": api_key},
    ).status_code == 401

    expiring, expired_key = issue_partner_api_credential(
        db_session,
        account.id,
        actor="issuer",
        label="Expired",
        scopes=["account:read"],
        expires_in_days=1,
    )
    expiring.expires_at = now_utc() - timedelta(minutes=1)
    db_session.add(expiring)
    db_session.commit()
    assert raw_client.get(
        "/api/partner/v1/account",
        headers={"X-GMAI-Partner-Key": expired_key},
    ).status_code == 401
    db_session.refresh(expiring)
    assert expiring.status == "expired"

    active, suspended_key = issue_partner_api_credential(
        db_session,
        account.id,
        actor="issuer",
        label="Suspended tenant",
        scopes=["account:read"],
        expires_in_days=30,
    )
    account.account_status = "suspended"
    db_session.add(account)
    db_session.commit()
    assert raw_client.get(
        "/api/partner/v1/account",
        headers={"X-GMAI-Partner-Key": suspended_key},
    ).status_code == 401
    assert active.status == "active"


def test_partner_credential_management_requires_internal_auth(
    raw_client,
    db_session: Session,
) -> None:
    account = _account(db_session, "Protected API Tenant")
    response = raw_client.post(
        "/api/v1/partner-api/credentials",
        json={
            "corporate_account_id": str(account.id),
            "label": "Unauthorized",
            "scopes": ["cases:read"],
            "expires_in_days": 30,
        },
    )
    assert response.status_code == 401
    assert db_session.exec(select(PartnerApiCredential)).first() is None

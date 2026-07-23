from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Session, select

from app.models.domain import CorporateAccount, CorporateMobilityCase, Lead
from app.schemas_corporate_mobility import (
    CorporateAccountCreate,
    CorporateAccountUpdate,
    CorporateMobilityCaseCreate,
    CorporateMobilityCaseUpdate,
)
from app.services.audit_log import record_audit, to_audit_dict


ACCOUNT_TRANSITIONS = {
    "active": {"active", "suspended", "closed"},
    "suspended": {"active", "suspended", "closed"},
    "closed": {"closed"},
}

CASE_TRANSITIONS = {
    "draft": {"draft", "active", "closed"},
    "active": {"active", "on_hold", "completed", "closed"},
    "on_hold": {"on_hold", "active", "closed"},
    "completed": {"completed", "closed"},
    "closed": {"closed"},
}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _case_reference() -> str:
    return f"CORP-{datetime.now(timezone.utc).strftime('%Y%m')}-{uuid4().hex[:8].upper()}"


def _utc_naive(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def create_account(
    session: Session,
    payload: CorporateAccountCreate,
    *,
    actor: str,
) -> CorporateAccount:
    account = CorporateAccount(
        legal_name=payload.legal_name.strip(),
        display_name=_clean(payload.display_name),
        primary_country=payload.primary_country.strip(),
        registration_number=_clean(payload.registration_number),
        contact_name=_clean(payload.contact_name),
        contact_email=str(payload.contact_email) if payload.contact_email else None,
        compliance_owner=_clean(payload.compliance_owner),
        notes=_clean(payload.notes),
        created_by=actor,
        updated_by=actor,
    )
    session.add(account)
    session.flush()
    record_audit(
        session,
        action="corporate_account_created",
        entity_type="corporate_account",
        entity_id=account.id,
        after_state=account,
        actor=actor,
        source="corporate_mobility_v11_0",
    )
    session.commit()
    session.refresh(account)
    return account


def update_account(
    session: Session,
    account: CorporateAccount,
    payload: CorporateAccountUpdate,
    *,
    actor: str,
) -> CorporateAccount:
    before = to_audit_dict(account)
    changes = payload.model_dump(exclude_unset=True)
    if account.account_status == "closed" and changes:
        raise ValueError("Closed corporate accounts are immutable")
    requested_status = changes.get("account_status")
    if requested_status and requested_status not in ACCOUNT_TRANSITIONS.get(account.account_status, set()):
        raise ValueError(f"Corporate account cannot transition from {account.account_status} to {requested_status}")
    for field, value in changes.items():
        if field == "contact_email" and value is not None:
            value = str(value)
        elif isinstance(value, str):
            value = _clean(value)
        setattr(account, field, value)
    account.updated_by = actor
    account.updated_at = datetime.now(timezone.utc)
    session.add(account)
    record_audit(
        session,
        action="corporate_account_updated",
        entity_type="corporate_account",
        entity_id=account.id,
        before_state=before,
        after_state=account,
        actor=actor,
        source="corporate_mobility_v11_0",
    )
    session.commit()
    session.refresh(account)
    return account


def create_case(
    session: Session,
    account: CorporateAccount,
    payload: CorporateMobilityCaseCreate,
    *,
    actor: str,
) -> CorporateMobilityCase:
    if account.account_status != "active":
        raise ValueError("Corporate mobility cases can only be created for active accounts")
    if payload.employee_lead_id is not None and session.get(Lead, payload.employee_lead_id) is None:
        raise ValueError("Employee lead not found")
    reference = _clean(payload.case_reference) or _case_reference()
    existing = session.exec(
        select(CorporateMobilityCase).where(CorporateMobilityCase.case_reference == reference)
    ).first()
    if existing is not None:
        raise ValueError("Corporate mobility case reference already exists")
    case = CorporateMobilityCase(
        corporate_account_id=account.id,
        employee_lead_id=payload.employee_lead_id,
        case_reference=reference,
        case_type=payload.case_type,
        origin_country=_clean(payload.origin_country),
        destination_country=payload.destination_country.strip(),
        sponsor_name=_clean(payload.sponsor_name),
        target_start_date=payload.target_start_date,
        compliance_due_date=payload.compliance_due_date,
        human_review_required=True,
        notes=_clean(payload.notes),
        created_by=actor,
        updated_by=actor,
    )
    session.add(case)
    session.flush()
    record_audit(
        session,
        action="corporate_mobility_case_created",
        entity_type="corporate_mobility_case",
        entity_id=case.id,
        after_state=case,
        actor=actor,
        source="corporate_mobility_v11_0",
    )
    session.commit()
    session.refresh(case)
    return case


def update_case(
    session: Session,
    case: CorporateMobilityCase,
    payload: CorporateMobilityCaseUpdate,
    *,
    actor: str,
) -> CorporateMobilityCase:
    before = to_audit_dict(case)
    changes = payload.model_dump(exclude_unset=True)
    if case.status == "closed" and changes:
        raise ValueError("Closed corporate mobility cases are immutable")
    requested_status = changes.get("status")
    if requested_status and requested_status not in CASE_TRANSITIONS.get(case.status, set()):
        raise ValueError(f"Corporate mobility case cannot transition from {case.status} to {requested_status}")
    employee_lead_id = changes.get("employee_lead_id")
    if employee_lead_id is not None and session.get(Lead, employee_lead_id) is None:
        raise ValueError("Employee lead not found")
    target_start = changes.get("target_start_date", case.target_start_date)
    compliance_due = changes.get("compliance_due_date", case.compliance_due_date)
    if (
        target_start is not None
        and compliance_due is not None
        and _utc_naive(compliance_due) > _utc_naive(target_start)
    ):
        raise ValueError("Compliance due date cannot be later than the target start date")
    for field, value in changes.items():
        if isinstance(value, str):
            value = _clean(value)
        setattr(case, field, value)
    case.human_review_required = True
    case.updated_by = actor
    case.updated_at = datetime.now(timezone.utc)
    session.add(case)
    record_audit(
        session,
        action="corporate_mobility_case_updated",
        entity_type="corporate_mobility_case",
        entity_id=case.id,
        before_state=before,
        after_state=case,
        actor=actor,
        source="corporate_mobility_v11_0",
    )
    session.commit()
    session.refresh(case)
    return case

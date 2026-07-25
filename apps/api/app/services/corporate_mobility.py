from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Session, select

from app.models.domain import (
    CorporateAccount,
    CorporateCaseDependant,
    CorporateCaseSponsorAssignment,
    CorporateComplianceEvent,
    CorporateMobilityCase,
    CorporateRelocationTask,
    CorporateRelocationTaskDecision,
    CorporateSponsorEntity,
    DocumentRecord,
    EntrepreneurVentureProfile,
    Lead,
    VentureEvidenceItem,
    VentureReviewDecision,
)
from app.schemas_corporate_mobility import (
    CorporateAccountCreate,
    CorporateAccountUpdate,
    CorporateMobilityCaseCreate,
    CorporateMobilityCaseUpdate,
    CorporateCaseDependantCreate,
    CorporateComplianceEventCreate,
    CorporateComplianceEventUpdate,
    CorporateSponsorEntityCreate,
    CorporateSponsorEntityUpdate,
    CorporateRelocationTaskCreate,
    CorporateRelocationTaskDecisionCreate,
    CorporateRelocationTaskTransition,
    EntrepreneurVentureProfileCreate,
    VentureEvidenceItemCreate,
    VentureReviewDecisionCreate,
    VentureReviewSubmission,
)
from app.services.audit_log import record_audit, to_audit_dict
from app.services.automation import capture_event


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

TASK_TRANSITIONS = {
    "planned": {"ready", "cancelled"},
    "ready": {"in_progress", "cancelled"},
    "in_progress": {"blocked", "completed", "cancelled"},
    "blocked": {"in_progress", "cancelled"},
    "awaiting_approval": set(),
    "completed": set(),
    "cancelled": set(),
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
    capture_event(
        session,
        idempotency_key=f"corporate-case:{case.id}:created",
        corporate_account_id=account.id,
        case_id=case.id,
        event_type="case.created",
        entity_type="corporate_mobility_case",
        entity_id=case.id,
        payload={
            "case_reference": case.case_reference,
            "status": case.status,
            "destination_country": case.destination_country,
            "case_type": case.case_type,
        },
        actor=actor,
        source="corporate_mobility_v12_3",
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
    previous_status = case.status
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
    if case.status != previous_status:
        capture_event(
            session,
            idempotency_key=(
                f"corporate-case:{case.id}:status:{previous_status}:{case.status}:"
                f"{case.updated_at.isoformat()}"
            ),
            corporate_account_id=case.corporate_account_id,
            case_id=case.id,
            event_type="case.status_changed",
            entity_type="corporate_mobility_case",
            entity_id=case.id,
            payload={
                "case_reference": case.case_reference,
                "previous_status": previous_status,
                "status": case.status,
                "destination_country": case.destination_country,
            },
            actor=actor,
            source="corporate_mobility_v12_3",
            occurred_at=case.updated_at,
        )
    session.commit()
    session.refresh(case)
    return case


def _assert_case_mutable(case: CorporateMobilityCase) -> None:
    if case.status == "closed":
        raise ValueError("Closed corporate mobility cases are immutable")


def create_sponsor_entity(
    session: Session, account: CorporateAccount, payload: CorporateSponsorEntityCreate, *, actor: str
) -> CorporateSponsorEntity:
    if account.account_status == "closed":
        raise ValueError("Closed corporate accounts are immutable")
    sponsor = CorporateSponsorEntity(
        corporate_account_id=account.id,
        legal_name=payload.legal_name.strip(),
        sponsor_type=payload.sponsor_type,
        country=payload.country.strip(),
        registration_number=_clean(payload.registration_number),
        contact_name=_clean(payload.contact_name),
        contact_email=str(payload.contact_email) if payload.contact_email else None,
        created_by=actor,
        updated_by=actor,
    )
    session.add(sponsor)
    session.flush()
    record_audit(session, action="corporate_sponsor_entity_created", entity_type="corporate_sponsor_entity",
                 entity_id=sponsor.id, after_state=sponsor, actor=actor, source="corporate_mobility_v11_1")
    session.commit()
    session.refresh(sponsor)
    return sponsor


def update_sponsor_entity(
    session: Session, sponsor: CorporateSponsorEntity, payload: CorporateSponsorEntityUpdate, *, actor: str
) -> CorporateSponsorEntity:
    changes = payload.model_dump(exclude_unset=True)
    if sponsor.status == "retired" and changes:
        raise ValueError("Retired corporate sponsor entities are immutable")
    before = to_audit_dict(sponsor)
    for field, value in changes.items():
        if field == "contact_email" and value is not None:
            value = str(value)
        elif isinstance(value, str):
            value = _clean(value)
        setattr(sponsor, field, value)
    sponsor.updated_by = actor
    sponsor.updated_at = datetime.now(timezone.utc)
    session.add(sponsor)
    record_audit(session, action="corporate_sponsor_entity_updated", entity_type="corporate_sponsor_entity",
                 entity_id=sponsor.id, before_state=before, after_state=sponsor, actor=actor,
                 source="corporate_mobility_v11_1")
    session.commit()
    session.refresh(sponsor)
    return sponsor


def assign_sponsor(
    session: Session, case: CorporateMobilityCase, sponsor: CorporateSponsorEntity, *, actor: str
) -> CorporateCaseSponsorAssignment:
    _assert_case_mutable(case)
    if sponsor.corporate_account_id != case.corporate_account_id:
        raise ValueError("Sponsor entity must belong to the case corporate account")
    if sponsor.status != "active":
        raise ValueError("Only active sponsor entities can be assigned")
    existing = session.exec(select(CorporateCaseSponsorAssignment).where(
        CorporateCaseSponsorAssignment.corporate_mobility_case_id == case.id,
        CorporateCaseSponsorAssignment.status == "active",
    )).first()
    if existing:
        raise ValueError("Corporate mobility case already has an active sponsor assignment")
    assignment = CorporateCaseSponsorAssignment(
        corporate_mobility_case_id=case.id, sponsor_entity_id=sponsor.id,
        created_by=actor, updated_by=actor,
    )
    session.add(assignment)
    session.flush()
    record_audit(session, action="corporate_case_sponsor_assigned", entity_type="corporate_case_sponsor_assignment",
                 entity_id=assignment.id, after_state=assignment, actor=actor, source="corporate_mobility_v11_1")
    session.commit()
    session.refresh(assignment)
    return assignment


def remove_sponsor_assignment(
    session: Session, assignment: CorporateCaseSponsorAssignment, case: CorporateMobilityCase, *, actor: str
) -> CorporateCaseSponsorAssignment:
    _assert_case_mutable(case)
    if assignment.status == "removed":
        raise ValueError("Removed sponsor assignments are immutable")
    before = to_audit_dict(assignment)
    assignment.status = "removed"
    assignment.updated_by = actor
    assignment.updated_at = datetime.now(timezone.utc)
    session.add(assignment)
    record_audit(session, action="corporate_case_sponsor_removed", entity_type="corporate_case_sponsor_assignment",
                 entity_id=assignment.id, before_state=before, after_state=assignment, actor=actor,
                 source="corporate_mobility_v11_1")
    session.commit()
    session.refresh(assignment)
    return assignment


def add_dependant(
    session: Session, case: CorporateMobilityCase, payload: CorporateCaseDependantCreate, *, actor: str
) -> CorporateCaseDependant:
    _assert_case_mutable(case)
    if session.get(Lead, payload.dependant_lead_id) is None:
        raise ValueError("Dependant lead not found")
    if case.employee_lead_id == payload.dependant_lead_id:
        raise ValueError("Employee lead cannot also be a dependant")
    existing = session.exec(select(CorporateCaseDependant).where(
        CorporateCaseDependant.corporate_mobility_case_id == case.id,
        CorporateCaseDependant.dependant_lead_id == payload.dependant_lead_id,
        CorporateCaseDependant.status == "active",
    )).first()
    if existing:
        raise ValueError("Dependant is already linked to this corporate mobility case")
    dependant = CorporateCaseDependant(
        corporate_mobility_case_id=case.id, dependant_lead_id=payload.dependant_lead_id,
        relationship_to_employee=payload.relationship_to_employee,
        sponsorship_required=payload.sponsorship_required, created_by=actor, updated_by=actor,
    )
    session.add(dependant)
    session.flush()
    record_audit(session, action="corporate_case_dependant_added", entity_type="corporate_case_dependant",
                 entity_id=dependant.id, after_state=dependant, actor=actor, source="corporate_mobility_v11_1")
    session.commit()
    session.refresh(dependant)
    return dependant


def remove_dependant(
    session: Session, dependant: CorporateCaseDependant, case: CorporateMobilityCase, *, actor: str
) -> CorporateCaseDependant:
    _assert_case_mutable(case)
    if dependant.status == "removed":
        raise ValueError("Removed dependant links are immutable")
    before = to_audit_dict(dependant)
    dependant.status = "removed"
    dependant.updated_by = actor
    dependant.updated_at = datetime.now(timezone.utc)
    session.add(dependant)
    record_audit(session, action="corporate_case_dependant_removed", entity_type="corporate_case_dependant",
                 entity_id=dependant.id, before_state=before, after_state=dependant, actor=actor,
                 source="corporate_mobility_v11_1")
    session.commit()
    session.refresh(dependant)
    return dependant


def create_compliance_event(
    session: Session, case: CorporateMobilityCase, payload: CorporateComplianceEventCreate, *, actor: str
) -> CorporateComplianceEvent:
    _assert_case_mutable(case)
    event = CorporateComplianceEvent(
        corporate_mobility_case_id=case.id, event_type=payload.event_type,
        title=payload.title.strip(), due_at=payload.due_at,
        evidence_required=payload.evidence_required, human_review_required=True,
        created_by=actor, updated_by=actor,
    )
    session.add(event)
    session.flush()
    record_audit(session, action="corporate_compliance_event_created", entity_type="corporate_compliance_event",
                 entity_id=event.id, after_state=event, actor=actor, source="corporate_mobility_v11_1")
    capture_event(
        session,
        idempotency_key=f"corporate-compliance:{event.id}:created",
        corporate_account_id=case.corporate_account_id,
        case_id=case.id,
        event_type="compliance.created",
        entity_type="corporate_compliance_event",
        entity_id=event.id,
        payload={
            "case_reference": case.case_reference,
            "event_type": event.event_type,
            "title": event.title,
            "due_at": event.due_at,
            "status": event.status,
            "evidence_required": event.evidence_required,
        },
        actor=actor,
        source="corporate_mobility_v12_3",
    )
    session.commit()
    session.refresh(event)
    return event


def update_compliance_event(
    session: Session, event: CorporateComplianceEvent, payload: CorporateComplianceEventUpdate, *, actor: str
) -> CorporateComplianceEvent:
    if event.status in {"completed", "waived"}:
        raise ValueError("Completed or waived compliance events are immutable")
    if payload.status == "open":
        raise ValueError("Open compliance events require no status transition")
    notes = _clean(payload.completion_notes)
    if payload.status == "waived" and not notes:
        raise ValueError("Waived compliance events require completion notes")
    before = to_audit_dict(event)
    previous_status = event.status
    event.status = payload.status
    event.completion_notes = notes
    event.completed_by = actor
    event.completed_at = datetime.now(timezone.utc)
    event.updated_by = actor
    event.updated_at = datetime.now(timezone.utc)
    session.add(event)
    record_audit(session, action="corporate_compliance_event_resolved", entity_type="corporate_compliance_event",
                 entity_id=event.id, before_state=before, after_state=event, actor=actor,
                 source="corporate_mobility_v11_1")
    case = session.get(CorporateMobilityCase, event.corporate_mobility_case_id)
    if case is None:
        raise ValueError("Corporate mobility case not found")
    capture_event(
        session,
        idempotency_key=(
            f"corporate-compliance:{event.id}:status:{previous_status}:{event.status}:"
            f"{event.updated_at.isoformat()}"
        ),
        corporate_account_id=case.corporate_account_id,
        case_id=case.id,
        event_type="compliance.status_changed",
        entity_type="corporate_compliance_event",
        entity_id=event.id,
        payload={
            "case_reference": case.case_reference,
            "event_type": event.event_type,
            "previous_status": previous_status,
            "status": event.status,
            "due_at": event.due_at,
        },
        actor=actor,
        source="corporate_mobility_v12_3",
        occurred_at=event.updated_at,
    )
    session.commit()
    session.refresh(event)
    return event


def create_relocation_task(
    session: Session, case: CorporateMobilityCase, payload: CorporateRelocationTaskCreate, *, actor: str
) -> CorporateRelocationTask:
    _assert_case_mutable(case)
    dependency = None
    if payload.depends_on_task_id is not None:
        dependency = session.get(CorporateRelocationTask, payload.depends_on_task_id)
        if dependency is None:
            raise ValueError("Relocation task dependency not found")
        if dependency.corporate_mobility_case_id != case.id:
            raise ValueError("Relocation task dependency must belong to the same corporate mobility case")
    task = CorporateRelocationTask(
        corporate_mobility_case_id=case.id,
        depends_on_task_id=dependency.id if dependency else None,
        title=payload.title.strip(),
        category=payload.category,
        owner_role=payload.owner_role.strip(),
        due_at=payload.due_at,
        requires_human_approval=payload.requires_human_approval,
        approval_status="pending" if payload.requires_human_approval else "not_required",
        created_by=actor,
        updated_by=actor,
    )
    session.add(task)
    session.flush()
    record_audit(session, action="corporate_relocation_task_created", entity_type="corporate_relocation_task",
                 entity_id=task.id, after_state=task, actor=actor, source="corporate_mobility_v11_2")
    session.commit()
    session.refresh(task)
    return task


def transition_relocation_task(
    session: Session,
    task: CorporateRelocationTask,
    case: CorporateMobilityCase,
    payload: CorporateRelocationTaskTransition,
    *,
    actor: str,
) -> CorporateRelocationTask:
    _assert_case_mutable(case)
    requested = payload.status
    if requested not in TASK_TRANSITIONS.get(task.status, set()):
        raise ValueError(f"Relocation task cannot transition from {task.status} to {requested}")
    notes = _clean(payload.work_notes)
    if requested in {"blocked", "cancelled"} and not notes:
        raise ValueError(f"Relocation task {requested} transition requires work notes")
    if requested == "ready" and task.depends_on_task_id is not None:
        dependency = session.get(CorporateRelocationTask, task.depends_on_task_id)
        if dependency is None or dependency.status != "completed":
            raise ValueError("Relocation task dependency must be completed before this task becomes ready")

    before = to_audit_dict(task)
    previous_status = task.status
    now = datetime.now(timezone.utc)
    task.work_notes = notes if notes is not None else task.work_notes
    if requested == "completed" and task.requires_human_approval:
        task.status = "awaiting_approval"
        task.approval_status = "pending"
        task.submitted_by = actor
        task.submitted_at = now
    elif requested == "completed":
        task.status = "completed"
        task.completed_by = actor
        task.completed_at = now
    else:
        task.status = requested
        if requested == "in_progress" and task.approval_status == "rejected":
            task.approval_status = "pending"
    task.updated_by = actor
    task.updated_at = now
    session.add(task)
    record_audit(session, action="corporate_relocation_task_transitioned", entity_type="corporate_relocation_task",
                 entity_id=task.id, before_state=before, after_state=task, actor=actor,
                 source="corporate_mobility_v11_2")
    capture_event(
        session,
        idempotency_key=(
            f"corporate-task:{task.id}:status:{previous_status}:{task.status}:"
            f"{task.updated_at.isoformat()}"
        ),
        corporate_account_id=case.corporate_account_id,
        case_id=case.id,
        event_type="task.status_changed",
        entity_type="corporate_relocation_task",
        entity_id=task.id,
        payload={
            "case_reference": case.case_reference,
            "task_title": task.title,
            "category": task.category,
            "previous_status": previous_status,
            "status": task.status,
            "due_at": task.due_at,
        },
        actor=actor,
        source="corporate_mobility_v12_3",
        occurred_at=task.updated_at,
    )
    session.commit()
    session.refresh(task)
    return task


def decide_relocation_task(
    session: Session,
    task: CorporateRelocationTask,
    case: CorporateMobilityCase,
    payload: CorporateRelocationTaskDecisionCreate,
    *,
    actor: str,
) -> CorporateRelocationTaskDecision:
    _assert_case_mutable(case)
    if task.status != "awaiting_approval":
        raise ValueError("Relocation task is not awaiting approval")
    if task.submitted_by == actor:
        raise ValueError("Relocation task completion requires a different reviewer")
    before = to_audit_dict(task)
    now = datetime.now(timezone.utc)
    decision = CorporateRelocationTaskDecision(
        corporate_relocation_task_id=task.id,
        decision=payload.decision,
        reason=payload.reason.strip(),
        reviewer=actor,
    )
    session.add(decision)
    if payload.decision == "approved":
        task.status = "completed"
        task.approval_status = "approved"
        task.completed_by = task.submitted_by
        task.completed_at = now
    else:
        task.status = "in_progress"
        task.approval_status = "rejected"
    task.updated_by = actor
    task.updated_at = now
    session.add(task)
    session.flush()
    record_audit(session, action="corporate_relocation_task_reviewed", entity_type="corporate_relocation_task",
                 entity_id=task.id, before_state=before, after_state=task, reason=payload.reason.strip(),
                 actor=actor, source="corporate_mobility_v11_2")
    session.commit()
    session.refresh(decision)
    return decision


def create_venture_profile(
    session: Session,
    case: CorporateMobilityCase,
    payload: EntrepreneurVentureProfileCreate,
    *,
    actor: str,
) -> EntrepreneurVentureProfile:
    _assert_case_mutable(case)
    if case.case_type != "entrepreneur_startup":
        raise ValueError("Venture profiles require an entrepreneur/startup corporate mobility case")
    if session.get(Lead, payload.founder_lead_id) is None:
        raise ValueError("Founder lead not found")
    if case.employee_lead_id is not None and case.employee_lead_id != payload.founder_lead_id:
        raise ValueError("Venture founder must match the lead linked to the corporate mobility case")
    if payload.target_country.strip() != case.destination_country:
        raise ValueError("Venture target country must match the corporate mobility case destination")
    existing = session.exec(select(EntrepreneurVentureProfile).where(
        EntrepreneurVentureProfile.corporate_mobility_case_id == case.id
    )).first()
    if existing is not None:
        raise ValueError("Corporate mobility case already has a venture profile")
    profile = EntrepreneurVentureProfile(
        corporate_mobility_case_id=case.id,
        founder_lead_id=payload.founder_lead_id,
        venture_name=payload.venture_name.strip(),
        venture_stage=payload.venture_stage,
        sector=payload.sector.strip(),
        target_country=payload.target_country.strip(),
        incorporation_country=_clean(payload.incorporation_country),
        founder_role=payload.founder_role.strip(),
        business_model_summary=payload.business_model_summary.strip(),
        human_review_required=True,
        created_by=actor,
        updated_by=actor,
    )
    session.add(profile)
    session.flush()
    record_audit(session, action="entrepreneur_venture_profile_created", entity_type="entrepreneur_venture_profile",
                 entity_id=profile.id, after_state=profile, actor=actor, source="corporate_mobility_v11_3")
    session.commit()
    session.refresh(profile)
    return profile


def add_venture_evidence(
    session: Session,
    profile: EntrepreneurVentureProfile,
    case: CorporateMobilityCase,
    payload: VentureEvidenceItemCreate,
    *,
    actor: str,
) -> VentureEvidenceItem:
    _assert_case_mutable(case)
    if profile.status not in {"draft", "evidence_pending"}:
        raise ValueError("Venture evidence can only be added before review submission")
    document = None
    if payload.document_record_id is not None:
        document = session.get(DocumentRecord, payload.document_record_id)
        if document is None:
            raise ValueError("Venture evidence document not found")
        if document.lead_id != profile.founder_lead_id:
            raise ValueError("Venture evidence document must belong to the founder lead")
    evidence = VentureEvidenceItem(
        venture_profile_id=profile.id,
        evidence_type=payload.evidence_type,
        title=payload.title.strip(),
        declared_amount_minor=payload.declared_amount_minor,
        currency=payload.currency.upper() if payload.currency else None,
        document_record_id=document.id if document else None,
        notes=_clean(payload.notes),
        created_by=actor,
    )
    before = to_audit_dict(profile)
    profile.status = "evidence_pending"
    profile.updated_by = actor
    profile.updated_at = datetime.now(timezone.utc)
    session.add(evidence)
    session.add(profile)
    session.flush()
    record_audit(session, action="venture_evidence_item_added", entity_type="venture_evidence_item",
                 entity_id=evidence.id, after_state=evidence, actor=actor, source="corporate_mobility_v11_3")
    record_audit(session, action="entrepreneur_venture_profile_updated", entity_type="entrepreneur_venture_profile",
                 entity_id=profile.id, before_state=before, after_state=profile, actor=actor,
                 source="corporate_mobility_v11_3")
    session.commit()
    session.refresh(evidence)
    return evidence


def submit_venture_review(
    session: Session,
    profile: EntrepreneurVentureProfile,
    case: CorporateMobilityCase,
    payload: VentureReviewSubmission,
    *,
    actor: str,
) -> EntrepreneurVentureProfile:
    _assert_case_mutable(case)
    if profile.status not in {"draft", "evidence_pending"}:
        raise ValueError("Venture profile cannot be submitted from its current status")
    if not payload.evidence_complete_attestation:
        raise ValueError("Evidence completeness attestation is required")
    evidence = list(session.exec(select(VentureEvidenceItem).where(
        VentureEvidenceItem.venture_profile_id == profile.id
    )).all())
    if not evidence:
        raise ValueError("Venture profile requires evidence before review submission")
    if not any(item.document_record_id is not None for item in evidence):
        raise ValueError("Venture profile requires at least one controlled document before review submission")
    before = to_audit_dict(profile)
    profile.status = "review_ready"
    profile.submitted_by = actor
    profile.submitted_at = datetime.now(timezone.utc)
    profile.updated_by = actor
    profile.updated_at = datetime.now(timezone.utc)
    session.add(profile)
    record_audit(session, action="entrepreneur_venture_profile_submitted", entity_type="entrepreneur_venture_profile",
                 entity_id=profile.id, before_state=before, after_state=profile, actor=actor,
                 source="corporate_mobility_v11_3")
    session.commit()
    session.refresh(profile)
    return profile


def decide_venture_review(
    session: Session,
    profile: EntrepreneurVentureProfile,
    case: CorporateMobilityCase,
    payload: VentureReviewDecisionCreate,
    *,
    actor: str,
) -> VentureReviewDecision:
    _assert_case_mutable(case)
    if profile.status != "review_ready":
        raise ValueError("Venture profile is not ready for review")
    if profile.submitted_by == actor:
        raise ValueError("Venture profile requires a different reviewer")
    before = to_audit_dict(profile)
    decision = VentureReviewDecision(
        venture_profile_id=profile.id,
        decision=payload.decision,
        reason=payload.reason.strip(),
        reviewer=actor,
    )
    now = datetime.now(timezone.utc)
    profile.status = "reviewed" if payload.decision == "approved" else "evidence_pending"
    profile.reviewed_by = actor
    profile.reviewed_at = now
    profile.review_notes = payload.reason.strip()
    profile.updated_by = actor
    profile.updated_at = now
    session.add(decision)
    session.add(profile)
    session.flush()
    record_audit(session, action="entrepreneur_venture_profile_reviewed", entity_type="entrepreneur_venture_profile",
                 entity_id=profile.id, before_state=before, after_state=profile, reason=payload.reason.strip(),
                 actor=actor, source="corporate_mobility_v11_3")
    session.commit()
    session.refresh(decision)
    return decision

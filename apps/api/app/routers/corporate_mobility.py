from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    CorporateAccount, CorporateCaseDependant, CorporateCaseSponsorAssignment,
    CorporateComplianceEvent, CorporateMobilityCase, CorporateSponsorEntity,
    CorporateRelocationTask, CorporateRelocationTaskDecision,
    EntrepreneurVentureProfile, VentureEvidenceItem, VentureReviewDecision,
)
from app.schemas_corporate_mobility import (
    CorporateAccountCreate,
    CorporateAccountDetail,
    CorporateAccountRead,
    CorporateAccountUpdate,
    CorporateMobilityCaseCreate,
    CorporateMobilityCaseRead,
    CorporateMobilityCaseUpdate,
    CorporateCaseDependantCreate, CorporateCaseDependantRead, CorporateCaseDependantUpdate,
    CorporateCaseSponsorAssignmentCreate, CorporateCaseSponsorAssignmentRead,
    CorporateCaseSponsorAssignmentUpdate, CorporateComplianceEventCreate,
    CorporateComplianceEventRead, CorporateComplianceEventUpdate,
    CorporateSponsorEntityCreate, CorporateSponsorEntityRead, CorporateSponsorEntityUpdate,
    CorporateRelocationTaskCreate, CorporateRelocationTaskDecisionCreate,
    CorporateRelocationTaskDecisionRead, CorporateRelocationTaskRead,
    CorporateRelocationTaskTransition,
    EntrepreneurVentureProfileCreate, EntrepreneurVentureProfileRead,
    VentureEvidenceItemCreate, VentureEvidenceItemRead,
    VentureReviewDecisionCreate, VentureReviewDecisionRead, VentureReviewSubmission,
)
from app.services.corporate_mobility import (
    add_dependant, assign_sponsor, create_account, create_case, create_compliance_event,
    create_sponsor_entity, remove_dependant, remove_sponsor_assignment, update_account,
    update_case, update_compliance_event, update_sponsor_entity,
    create_relocation_task, decide_relocation_task, transition_relocation_task,
    add_venture_evidence, create_venture_profile, decide_venture_review, submit_venture_review,
)


router = APIRouter(prefix="/api/v1/corporate-mobility", tags=["corporate-mobility-v11.1"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    status = 404 if message in {
        "Corporate account not found",
        "Corporate mobility case not found",
        "Employee lead not found",
        "Dependant lead not found",
        "Corporate sponsor entity not found",
        "Corporate sponsor assignment not found",
        "Corporate dependant link not found",
        "Corporate compliance event not found",
        "Corporate relocation task not found",
        "Relocation task dependency not found",
        "Founder lead not found",
        "Venture evidence document not found",
        "Entrepreneur venture profile not found",
    } else 400
    return HTTPException(status_code=status, detail=message)


@router.post("/accounts", response_model=CorporateAccountRead, status_code=201)
def api_create_account(
    payload: CorporateAccountCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> CorporateAccount:
    return create_account(session, payload, actor=_actor(request))


@router.get("/accounts", response_model=list[CorporateAccountRead])
def api_list_accounts(
    status: str | None = None,
    country: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[CorporateAccount]:
    statement = select(CorporateAccount).order_by(CorporateAccount.updated_at.desc())
    if status:
        statement = statement.where(CorporateAccount.account_status == status.strip().lower())
    if country:
        statement = statement.where(CorporateAccount.primary_country == country.strip())
    return list(session.exec(statement.limit(limit)).all())


@router.get("/accounts/{account_id}", response_model=CorporateAccountDetail)
def api_get_account(
    account_id: UUID,
    session: Session = Depends(get_session),
) -> CorporateAccountDetail:
    account = session.get(CorporateAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Corporate account not found")
    cases = session.exec(
        select(CorporateMobilityCase)
        .where(CorporateMobilityCase.corporate_account_id == account.id)
        .order_by(CorporateMobilityCase.updated_at.desc())
    ).all()
    return CorporateAccountDetail(**CorporateAccountRead.model_validate(account).model_dump(), cases=cases)


@router.patch("/accounts/{account_id}", response_model=CorporateAccountRead)
def api_update_account(
    account_id: UUID,
    payload: CorporateAccountUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> CorporateAccount:
    account = session.get(CorporateAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Corporate account not found")
    try:
        return update_account(session, account, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/accounts/{account_id}/cases", response_model=CorporateMobilityCaseRead, status_code=201)
def api_create_case(
    account_id: UUID,
    payload: CorporateMobilityCaseCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> CorporateMobilityCase:
    account = session.get(CorporateAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Corporate account not found")
    try:
        return create_case(session, account, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/cases", response_model=list[CorporateMobilityCaseRead])
def api_list_cases(
    account_id: UUID | None = None,
    employee_lead_id: UUID | None = None,
    status: str | None = None,
    destination_country: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[CorporateMobilityCase]:
    statement = select(CorporateMobilityCase).order_by(CorporateMobilityCase.updated_at.desc())
    if account_id:
        statement = statement.where(CorporateMobilityCase.corporate_account_id == account_id)
    if employee_lead_id:
        statement = statement.where(CorporateMobilityCase.employee_lead_id == employee_lead_id)
    if status:
        statement = statement.where(CorporateMobilityCase.status == status.strip().lower())
    if destination_country:
        statement = statement.where(CorporateMobilityCase.destination_country == destination_country.strip())
    return list(session.exec(statement.limit(limit)).all())


@router.get("/cases/{case_id}", response_model=CorporateMobilityCaseRead)
def api_get_case(
    case_id: UUID,
    session: Session = Depends(get_session),
) -> CorporateMobilityCase:
    case = session.get(CorporateMobilityCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    return case


@router.patch("/cases/{case_id}", response_model=CorporateMobilityCaseRead)
def api_update_case(
    case_id: UUID,
    payload: CorporateMobilityCaseUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> CorporateMobilityCase:
    case = session.get(CorporateMobilityCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    try:
        return update_case(session, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/accounts/{account_id}/sponsors", response_model=CorporateSponsorEntityRead, status_code=201)
def api_create_sponsor(account_id: UUID, payload: CorporateSponsorEntityCreate, request: Request,
                       session: Session = Depends(get_session)) -> CorporateSponsorEntity:
    account = session.get(CorporateAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Corporate account not found")
    try:
        return create_sponsor_entity(session, account, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/accounts/{account_id}/sponsors", response_model=list[CorporateSponsorEntityRead])
def api_list_sponsors(account_id: UUID, session: Session = Depends(get_session)) -> list[CorporateSponsorEntity]:
    if session.get(CorporateAccount, account_id) is None:
        raise HTTPException(status_code=404, detail="Corporate account not found")
    return list(session.exec(select(CorporateSponsorEntity).where(
        CorporateSponsorEntity.corporate_account_id == account_id
    ).order_by(CorporateSponsorEntity.updated_at.desc())).all())


@router.patch("/sponsors/{sponsor_id}", response_model=CorporateSponsorEntityRead)
def api_update_sponsor(sponsor_id: UUID, payload: CorporateSponsorEntityUpdate, request: Request,
                       session: Session = Depends(get_session)) -> CorporateSponsorEntity:
    sponsor = session.get(CorporateSponsorEntity, sponsor_id)
    if sponsor is None:
        raise HTTPException(status_code=404, detail="Corporate sponsor entity not found")
    try:
        return update_sponsor_entity(session, sponsor, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/cases/{case_id}/sponsors", response_model=CorporateCaseSponsorAssignmentRead, status_code=201)
def api_assign_sponsor(case_id: UUID, payload: CorporateCaseSponsorAssignmentCreate, request: Request,
                       session: Session = Depends(get_session)) -> CorporateCaseSponsorAssignment:
    case = session.get(CorporateMobilityCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    sponsor = session.get(CorporateSponsorEntity, payload.sponsor_entity_id)
    if sponsor is None:
        raise HTTPException(status_code=404, detail="Corporate sponsor entity not found")
    try:
        return assign_sponsor(session, case, sponsor, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/cases/{case_id}/sponsors", response_model=list[CorporateCaseSponsorAssignmentRead])
def api_list_case_sponsors(case_id: UUID, session: Session = Depends(get_session)) -> list[CorporateCaseSponsorAssignment]:
    if session.get(CorporateMobilityCase, case_id) is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    return list(session.exec(select(CorporateCaseSponsorAssignment).where(
        CorporateCaseSponsorAssignment.corporate_mobility_case_id == case_id
    ).order_by(CorporateCaseSponsorAssignment.created_at.desc())).all())


@router.patch("/sponsor-assignments/{assignment_id}", response_model=CorporateCaseSponsorAssignmentRead)
def api_remove_sponsor(assignment_id: UUID, payload: CorporateCaseSponsorAssignmentUpdate, request: Request,
                       session: Session = Depends(get_session)) -> CorporateCaseSponsorAssignment:
    assignment = session.get(CorporateCaseSponsorAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Corporate sponsor assignment not found")
    case = session.get(CorporateMobilityCase, assignment.corporate_mobility_case_id)
    try:
        return remove_sponsor_assignment(session, assignment, case, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/cases/{case_id}/dependants", response_model=CorporateCaseDependantRead, status_code=201)
def api_add_dependant(case_id: UUID, payload: CorporateCaseDependantCreate, request: Request,
                      session: Session = Depends(get_session)) -> CorporateCaseDependant:
    case = session.get(CorporateMobilityCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    try:
        return add_dependant(session, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/cases/{case_id}/dependants", response_model=list[CorporateCaseDependantRead])
def api_list_dependants(case_id: UUID, session: Session = Depends(get_session)) -> list[CorporateCaseDependant]:
    if session.get(CorporateMobilityCase, case_id) is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    return list(session.exec(select(CorporateCaseDependant).where(
        CorporateCaseDependant.corporate_mobility_case_id == case_id
    ).order_by(CorporateCaseDependant.created_at.desc())).all())


@router.patch("/dependants/{dependant_id}", response_model=CorporateCaseDependantRead)
def api_remove_dependant(dependant_id: UUID, payload: CorporateCaseDependantUpdate, request: Request,
                         session: Session = Depends(get_session)) -> CorporateCaseDependant:
    dependant = session.get(CorporateCaseDependant, dependant_id)
    if dependant is None:
        raise HTTPException(status_code=404, detail="Corporate dependant link not found")
    case = session.get(CorporateMobilityCase, dependant.corporate_mobility_case_id)
    try:
        return remove_dependant(session, dependant, case, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/cases/{case_id}/compliance-events", response_model=CorporateComplianceEventRead, status_code=201)
def api_create_event(case_id: UUID, payload: CorporateComplianceEventCreate, request: Request,
                     session: Session = Depends(get_session)) -> CorporateComplianceEvent:
    case = session.get(CorporateMobilityCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    try:
        return create_compliance_event(session, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/cases/{case_id}/compliance-events", response_model=list[CorporateComplianceEventRead])
def api_list_events(case_id: UUID, session: Session = Depends(get_session)) -> list[CorporateComplianceEvent]:
    if session.get(CorporateMobilityCase, case_id) is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    return list(session.exec(select(CorporateComplianceEvent).where(
        CorporateComplianceEvent.corporate_mobility_case_id == case_id
    ).order_by(CorporateComplianceEvent.due_at)).all())


@router.patch("/compliance-events/{event_id}", response_model=CorporateComplianceEventRead)
def api_update_event(event_id: UUID, payload: CorporateComplianceEventUpdate, request: Request,
                     session: Session = Depends(get_session)) -> CorporateComplianceEvent:
    event = session.get(CorporateComplianceEvent, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Corporate compliance event not found")
    try:
        return update_compliance_event(session, event, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/cases/{case_id}/relocation-tasks", response_model=CorporateRelocationTaskRead, status_code=201)
def api_create_relocation_task(
    case_id: UUID, payload: CorporateRelocationTaskCreate, request: Request,
    session: Session = Depends(get_session),
) -> CorporateRelocationTask:
    case = session.get(CorporateMobilityCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    try:
        return create_relocation_task(session, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/cases/{case_id}/relocation-tasks", response_model=list[CorporateRelocationTaskRead])
def api_list_relocation_tasks(
    case_id: UUID, status: str | None = None, session: Session = Depends(get_session),
) -> list[CorporateRelocationTask]:
    if session.get(CorporateMobilityCase, case_id) is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    statement = select(CorporateRelocationTask).where(
        CorporateRelocationTask.corporate_mobility_case_id == case_id
    ).order_by(CorporateRelocationTask.created_at)
    if status:
        statement = statement.where(CorporateRelocationTask.status == status.strip().lower())
    return list(session.exec(statement).all())


@router.patch("/relocation-tasks/{task_id}", response_model=CorporateRelocationTaskRead)
def api_transition_relocation_task(
    task_id: UUID, payload: CorporateRelocationTaskTransition, request: Request,
    session: Session = Depends(get_session),
) -> CorporateRelocationTask:
    task = session.get(CorporateRelocationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Corporate relocation task not found")
    case = session.get(CorporateMobilityCase, task.corporate_mobility_case_id)
    try:
        return transition_relocation_task(session, task, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post(
    "/relocation-tasks/{task_id}/decisions",
    response_model=CorporateRelocationTaskDecisionRead,
    status_code=201,
)
def api_decide_relocation_task(
    task_id: UUID, payload: CorporateRelocationTaskDecisionCreate, request: Request,
    session: Session = Depends(get_session),
) -> CorporateRelocationTaskDecision:
    task = session.get(CorporateRelocationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Corporate relocation task not found")
    case = session.get(CorporateMobilityCase, task.corporate_mobility_case_id)
    try:
        return decide_relocation_task(session, task, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get(
    "/relocation-tasks/{task_id}/decisions",
    response_model=list[CorporateRelocationTaskDecisionRead],
)
def api_list_relocation_task_decisions(
    task_id: UUID, session: Session = Depends(get_session),
) -> list[CorporateRelocationTaskDecision]:
    if session.get(CorporateRelocationTask, task_id) is None:
        raise HTTPException(status_code=404, detail="Corporate relocation task not found")
    return list(session.exec(select(CorporateRelocationTaskDecision).where(
        CorporateRelocationTaskDecision.corporate_relocation_task_id == task_id
    ).order_by(CorporateRelocationTaskDecision.created_at)).all())


@router.post("/cases/{case_id}/venture-profile", response_model=EntrepreneurVentureProfileRead, status_code=201)
def api_create_venture_profile(
    case_id: UUID, payload: EntrepreneurVentureProfileCreate, request: Request,
    session: Session = Depends(get_session),
) -> EntrepreneurVentureProfile:
    case = session.get(CorporateMobilityCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    try:
        return create_venture_profile(session, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/cases/{case_id}/venture-profile", response_model=EntrepreneurVentureProfileRead)
def api_get_venture_profile(
    case_id: UUID, session: Session = Depends(get_session),
) -> EntrepreneurVentureProfile:
    if session.get(CorporateMobilityCase, case_id) is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    profile = session.exec(select(EntrepreneurVentureProfile).where(
        EntrepreneurVentureProfile.corporate_mobility_case_id == case_id
    )).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Entrepreneur venture profile not found")
    return profile


@router.post("/venture-profiles/{profile_id}/evidence", response_model=VentureEvidenceItemRead, status_code=201)
def api_add_venture_evidence(
    profile_id: UUID, payload: VentureEvidenceItemCreate, request: Request,
    session: Session = Depends(get_session),
) -> VentureEvidenceItem:
    profile = session.get(EntrepreneurVentureProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Entrepreneur venture profile not found")
    case = session.get(CorporateMobilityCase, profile.corporate_mobility_case_id)
    try:
        return add_venture_evidence(session, profile, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/venture-profiles/{profile_id}/evidence", response_model=list[VentureEvidenceItemRead])
def api_list_venture_evidence(
    profile_id: UUID, session: Session = Depends(get_session),
) -> list[VentureEvidenceItem]:
    if session.get(EntrepreneurVentureProfile, profile_id) is None:
        raise HTTPException(status_code=404, detail="Entrepreneur venture profile not found")
    return list(session.exec(select(VentureEvidenceItem).where(
        VentureEvidenceItem.venture_profile_id == profile_id
    ).order_by(VentureEvidenceItem.created_at)).all())


@router.post("/venture-profiles/{profile_id}/submit", response_model=EntrepreneurVentureProfileRead)
def api_submit_venture_profile(
    profile_id: UUID, payload: VentureReviewSubmission, request: Request,
    session: Session = Depends(get_session),
) -> EntrepreneurVentureProfile:
    profile = session.get(EntrepreneurVentureProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Entrepreneur venture profile not found")
    case = session.get(CorporateMobilityCase, profile.corporate_mobility_case_id)
    try:
        return submit_venture_review(session, profile, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/venture-profiles/{profile_id}/decisions", response_model=VentureReviewDecisionRead, status_code=201)
def api_decide_venture_profile(
    profile_id: UUID, payload: VentureReviewDecisionCreate, request: Request,
    session: Session = Depends(get_session),
) -> VentureReviewDecision:
    profile = session.get(EntrepreneurVentureProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Entrepreneur venture profile not found")
    case = session.get(CorporateMobilityCase, profile.corporate_mobility_case_id)
    try:
        return decide_venture_review(session, profile, case, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/venture-profiles/{profile_id}/decisions", response_model=list[VentureReviewDecisionRead])
def api_list_venture_decisions(
    profile_id: UUID, session: Session = Depends(get_session),
) -> list[VentureReviewDecision]:
    if session.get(EntrepreneurVentureProfile, profile_id) is None:
        raise HTTPException(status_code=404, detail="Entrepreneur venture profile not found")
    return list(session.exec(select(VentureReviewDecision).where(
        VentureReviewDecision.venture_profile_id == profile_id
    ).order_by(VentureReviewDecision.created_at)).all())

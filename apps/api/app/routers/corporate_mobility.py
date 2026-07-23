from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import CorporateAccount, CorporateMobilityCase
from app.schemas_corporate_mobility import (
    CorporateAccountCreate,
    CorporateAccountDetail,
    CorporateAccountRead,
    CorporateAccountUpdate,
    CorporateMobilityCaseCreate,
    CorporateMobilityCaseRead,
    CorporateMobilityCaseUpdate,
)
from app.services.corporate_mobility import create_account, create_case, update_account, update_case


router = APIRouter(prefix="/api/v1/corporate-mobility", tags=["corporate-mobility-v11.0"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    status = 404 if message in {
        "Corporate account not found",
        "Corporate mobility case not found",
        "Employee lead not found",
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


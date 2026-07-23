from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import InvestmentMobilityProgram
from app.schemas_investment_mobility import (
    InvestmentProgramCreate,
    InvestmentProgramPublish,
    InvestmentProgramRead,
    InvestmentProgramVersionInput,
    InvestmentProgramVersionRead,
)
from app.services.investment_mobility import (
    create_investment_program,
    create_investment_program_version,
    investment_program_read,
    investment_version_read,
    publish_investment_program_version,
)


router = APIRouter(prefix="/api/v1/investment-mobility", tags=["investment-mobility-v11.5"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    not_found = {"Investment program not found", "Investment program version not found", "Mobility pathway not found"}
    return HTTPException(status_code=404 if str(exc) in not_found else 400, detail=str(exc))


@router.post("/programs", response_model=InvestmentProgramRead, status_code=201)
def api_create_program(payload: InvestmentProgramCreate, request: Request, session: Session = Depends(get_session)):
    try:
        return investment_program_read(session, create_investment_program(session, payload, actor=_actor(request)))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/programs", response_model=list[InvestmentProgramRead])
def api_list_programs(
    country: str | None = None,
    program_type: str | None = None,
    catalogue_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    statement = select(InvestmentMobilityProgram).order_by(InvestmentMobilityProgram.updated_at.desc())
    if country:
        statement = statement.where(InvestmentMobilityProgram.country == country.strip().lower())
    if program_type:
        statement = statement.where(InvestmentMobilityProgram.program_type == program_type.strip().lower())
    if catalogue_status:
        statement = statement.where(InvestmentMobilityProgram.catalogue_status == catalogue_status.strip().lower())
    return [investment_program_read(session, row) for row in session.exec(statement.limit(limit)).all()]


@router.get("/programs/{program_id}", response_model=InvestmentProgramRead)
def api_get_program(program_id: UUID, session: Session = Depends(get_session)):
    row = session.get(InvestmentMobilityProgram, program_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Investment program not found")
    return investment_program_read(session, row)


@router.post("/programs/{program_id}/versions", response_model=InvestmentProgramVersionRead, status_code=201)
def api_create_version(
    program_id: UUID, payload: InvestmentProgramVersionInput, request: Request, session: Session = Depends(get_session),
):
    try:
        return investment_version_read(create_investment_program_version(session, program_id, payload, actor=_actor(request)))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/versions/{version_id}/publish", response_model=InvestmentProgramRead)
def api_publish_version(
    version_id: UUID, payload: InvestmentProgramPublish, request: Request, session: Session = Depends(get_session),
):
    try:
        row = publish_investment_program_version(
            session, version_id, actor=_actor(request), review_notes=payload.review_notes,
        )
        return investment_program_read(session, row)
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc

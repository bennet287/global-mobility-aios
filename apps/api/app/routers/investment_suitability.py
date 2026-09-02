from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import InvestmentMobilitySuitabilityAssessment, InvestmentMobilitySuitabilityReview
from app.schemas_investment_suitability import (
    InvestmentSuitabilityCreate, InvestmentSuitabilityRead,
    InvestmentSuitabilityReviewCreate, InvestmentSuitabilityReviewRead,
)
from app.services.investment_suitability import create_suitability_assessment, review_suitability_assessment, suitability_read


router = APIRouter(prefix="/api/v1/investment-mobility/suitability", tags=["investment-suitability-v11.6"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    missing = {"Lead not found", "Business mobility advisory not found", "Suitability evidence document not found", "Investment mobility suitability assessment not found"}
    return HTTPException(status_code=404 if str(exc) in missing else 400, detail=str(exc))


@router.post("/assessments", response_model=InvestmentSuitabilityRead, status_code=201)
def create(payload: InvestmentSuitabilityCreate, request: Request, session: Session = Depends(get_session)):
    try:
        return suitability_read(create_suitability_assessment(session, payload, actor=_actor(request)))
    except ValueError as exc:
        session.rollback(); raise _error(exc) from exc


@router.get("/assessments", response_model=list[InvestmentSuitabilityRead])
def list_assessments(
    lead_id: UUID | None = None, status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500), session: Session = Depends(get_session),
):
    statement = select(InvestmentMobilitySuitabilityAssessment).order_by(InvestmentMobilitySuitabilityAssessment.created_at.desc())
    if lead_id: statement = statement.where(InvestmentMobilitySuitabilityAssessment.lead_id == lead_id)
    if status: statement = statement.where(InvestmentMobilitySuitabilityAssessment.status == status.strip().lower())
    return [suitability_read(row) for row in session.exec(statement.limit(limit)).all()]


@router.get("/assessments/{assessment_id}", response_model=InvestmentSuitabilityRead)
def get_assessment(assessment_id: UUID, session: Session = Depends(get_session)):
    row = session.get(InvestmentMobilitySuitabilityAssessment, assessment_id)
    if row is None: raise HTTPException(status_code=404, detail="Investment mobility suitability assessment not found")
    return suitability_read(row)


@router.post("/assessments/{assessment_id}/reviews", response_model=InvestmentSuitabilityReviewRead, status_code=201)
def review(assessment_id: UUID, payload: InvestmentSuitabilityReviewCreate, request: Request, session: Session = Depends(get_session)):
    row = session.get(InvestmentMobilitySuitabilityAssessment, assessment_id)
    if row is None: raise HTTPException(status_code=404, detail="Investment mobility suitability assessment not found")
    try:
        return review_suitability_assessment(session, row, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback(); raise _error(exc) from exc


@router.get("/assessments/{assessment_id}/reviews", response_model=list[InvestmentSuitabilityReviewRead])
def reviews(assessment_id: UUID, session: Session = Depends(get_session)):
    if session.get(InvestmentMobilitySuitabilityAssessment, assessment_id) is None:
        raise HTTPException(status_code=404, detail="Investment mobility suitability assessment not found")
    return list(session.exec(select(InvestmentMobilitySuitabilityReview).where(
        InvestmentMobilitySuitabilityReview.assessment_id == assessment_id
    ).order_by(InvestmentMobilitySuitabilityReview.created_at)).all())

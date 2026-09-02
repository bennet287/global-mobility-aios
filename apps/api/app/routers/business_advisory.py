from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import BusinessMobilityAdvisoryAssessment, BusinessMobilityAdvisoryReview
from app.schemas_business_advisory import (
    BusinessAdvisoryCreate,
    BusinessAdvisoryRead,
    BusinessAdvisoryReviewCreate,
    BusinessAdvisoryReviewRead,
    BusinessAdvisorySituationRequest,
    BusinessAdvisorySolutionResponse,
)
from app.services.business_advisory import (
    advise_on_business_mobility_situation,
    advisory_read,
    create_advisory_assessment,
    review_advisory_assessment,
)


router = APIRouter(prefix="/api/v1/business-mobility-advisory", tags=["business-mobility-advisory-v11.4"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    missing = {
        "Lead not found", "Corporate mobility case not found", "Advisory document not found",
        "Business mobility advisory not found",
    }
    return HTTPException(status_code=404 if str(exc) in missing else 400, detail=str(exc))


@router.post("/assessments", response_model=BusinessAdvisoryRead, status_code=201)
def api_create_assessment(
    payload: BusinessAdvisoryCreate, request: Request, session: Session = Depends(get_session),
) -> BusinessAdvisoryRead:
    try:
        return advisory_read(create_advisory_assessment(session, payload, actor=_actor(request)))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/advise", response_model=BusinessAdvisorySolutionResponse, status_code=200)
def api_advise_on_situation(
    payload: BusinessAdvisorySituationRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> BusinessAdvisorySolutionResponse:
    try:
        return advise_on_business_mobility_situation(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/assessments", response_model=list[BusinessAdvisoryRead])
def api_list_assessments(
    lead_id: UUID | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[BusinessAdvisoryRead]:
    statement = select(BusinessMobilityAdvisoryAssessment).order_by(
        BusinessMobilityAdvisoryAssessment.created_at.desc()
    )
    if lead_id:
        statement = statement.where(BusinessMobilityAdvisoryAssessment.lead_id == lead_id)
    if status:
        statement = statement.where(BusinessMobilityAdvisoryAssessment.status == status.strip().lower())
    return [advisory_read(row) for row in session.exec(statement.limit(limit)).all()]


@router.get("/assessments/{assessment_id}", response_model=BusinessAdvisoryRead)
def api_get_assessment(
    assessment_id: UUID, session: Session = Depends(get_session),
) -> BusinessAdvisoryRead:
    row = session.get(BusinessMobilityAdvisoryAssessment, assessment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Business mobility advisory not found")
    return advisory_read(row)


@router.post(
    "/assessments/{assessment_id}/reviews",
    response_model=BusinessAdvisoryReviewRead,
    status_code=201,
)
def api_review_assessment(
    assessment_id: UUID,
    payload: BusinessAdvisoryReviewCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> BusinessMobilityAdvisoryReview:
    row = session.get(BusinessMobilityAdvisoryAssessment, assessment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Business mobility advisory not found")
    try:
        return review_advisory_assessment(session, row, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get(
    "/assessments/{assessment_id}/reviews",
    response_model=list[BusinessAdvisoryReviewRead],
)
def api_list_reviews(
    assessment_id: UUID, session: Session = Depends(get_session),
) -> list[BusinessMobilityAdvisoryReview]:
    if session.get(BusinessMobilityAdvisoryAssessment, assessment_id) is None:
        raise HTTPException(status_code=404, detail="Business mobility advisory not found")
    return list(session.exec(select(BusinessMobilityAdvisoryReview).where(
        BusinessMobilityAdvisoryReview.assessment_id == assessment_id
    ).order_by(BusinessMobilityAdvisoryReview.created_at)).all())

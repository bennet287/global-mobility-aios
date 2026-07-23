from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import FamilyOfficeMobilityAssessment, FamilyOfficeMobilityReview
from app.schemas_family_office_mobility import (
    FamilyOfficeAssessmentCreate,
    FamilyOfficeAssessmentRead,
    FamilyOfficeReviewCreate,
    FamilyOfficeReviewRead,
)
from app.services.family_office_mobility import (
    create_family_office_assessment,
    family_office_read,
    review_family_office_assessment,
)


router = APIRouter(
    prefix="/api/v1/family-office-mobility",
    tags=["family-office-mobility-v11.10"],
)


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    missing = {
        "Lead not found",
        "Business mobility advisory not found",
        "Family-office evidence document not found",
        "Family-office mobility assessment not found",
    }
    return HTTPException(
        status_code=404 if str(exc) in missing else 400,
        detail=str(exc),
    )


@router.post("/assessments", response_model=FamilyOfficeAssessmentRead, status_code=201)
def create(
    payload: FamilyOfficeAssessmentCreate,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        return family_office_read(
            create_family_office_assessment(session, payload, actor=_actor(request))
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/assessments", response_model=list[FamilyOfficeAssessmentRead])
def list_assessments(
    lead_id: UUID | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    statement = select(FamilyOfficeMobilityAssessment).order_by(
        FamilyOfficeMobilityAssessment.created_at.desc()
    )
    if lead_id:
        statement = statement.where(FamilyOfficeMobilityAssessment.lead_id == lead_id)
    if status:
        statement = statement.where(
            FamilyOfficeMobilityAssessment.status == status.strip().lower()
        )
    return [
        family_office_read(row)
        for row in session.exec(statement.limit(limit)).all()
    ]


@router.get("/assessments/{assessment_id}", response_model=FamilyOfficeAssessmentRead)
def get_assessment(
    assessment_id: UUID,
    session: Session = Depends(get_session),
):
    row = session.get(FamilyOfficeMobilityAssessment, assessment_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Family-office mobility assessment not found",
        )
    return family_office_read(row)


@router.post(
    "/assessments/{assessment_id}/reviews",
    response_model=FamilyOfficeReviewRead,
    status_code=201,
)
def review(
    assessment_id: UUID,
    payload: FamilyOfficeReviewCreate,
    request: Request,
    session: Session = Depends(get_session),
):
    row = session.get(FamilyOfficeMobilityAssessment, assessment_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Family-office mobility assessment not found",
        )
    try:
        return review_family_office_assessment(
            session, row, payload, actor=_actor(request)
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get(
    "/assessments/{assessment_id}/reviews",
    response_model=list[FamilyOfficeReviewRead],
)
def reviews(
    assessment_id: UUID,
    session: Session = Depends(get_session),
):
    if session.get(FamilyOfficeMobilityAssessment, assessment_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Family-office mobility assessment not found",
        )
    return list(session.exec(select(FamilyOfficeMobilityReview).where(
        FamilyOfficeMobilityReview.assessment_id == assessment_id
    ).order_by(FamilyOfficeMobilityReview.created_at)).all())

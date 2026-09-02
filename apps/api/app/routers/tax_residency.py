from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    TaxResidencyAssessment,
    TaxResidencyAssessmentReview,
    TaxTreatyEvidence,
    TaxTreatyEvidenceDecision,
)
from app.schemas_tax_residency import (
    TaxResidencyAssessmentCreate,
    TaxResidencyAssessmentRead,
    TaxResidencyReviewCreate,
    TaxResidencyReviewRead,
    TaxTreatyEvidenceCreate,
    TaxTreatyEvidenceDecisionCreate,
    TaxTreatyEvidenceDecisionRead,
    TaxTreatyEvidenceRead,
)
from app.services.tax_residency import (
    assessment_read,
    create_tax_residency_assessment,
    create_treaty_evidence,
    decide_treaty_evidence,
    review_tax_residency_assessment,
    treaty_evidence_read,
)


router = APIRouter(
    prefix="/api/v1/tax-residency",
    tags=["tax-residency-treaty-v11.11"],
)


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    missing = {
        "Lead not found", "Family-office mobility assessment not found",
        "Business mobility advisory not found", "Tax-residency evidence document not found",
        "Tax treaty evidence not found", "Official source not found",
        "Tax-residency assessment not found",
    }
    return HTTPException(status_code=404 if str(exc) in missing else 400, detail=str(exc))


@router.post("/treaty-evidence", response_model=TaxTreatyEvidenceRead, status_code=201)
def create_evidence(
    payload: TaxTreatyEvidenceCreate,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        return treaty_evidence_read(
            session,
            create_treaty_evidence(session, payload, actor=_actor(request)),
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/treaty-evidence", response_model=list[TaxTreatyEvidenceRead])
def list_evidence(
    status: str | None = None,
    jurisdiction: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    statement = select(TaxTreatyEvidence).order_by(TaxTreatyEvidence.created_at.desc())
    if status:
        statement = statement.where(TaxTreatyEvidence.status == status.strip().lower())
    rows = list(session.exec(statement.limit(limit)).all())
    if jurisdiction:
        normalized = jurisdiction.strip().lower()
        rows = [
            row for row in rows
            if normalized in {row.jurisdiction_a.lower(), row.jurisdiction_b.lower()}
        ]
    return [treaty_evidence_read(session, row) for row in rows]


@router.post(
    "/treaty-evidence/{evidence_id}/decisions",
    response_model=TaxTreatyEvidenceRead,
)
def decide_evidence(
    evidence_id: UUID,
    payload: TaxTreatyEvidenceDecisionCreate,
    request: Request,
    session: Session = Depends(get_session),
):
    row = session.get(TaxTreatyEvidence, evidence_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tax treaty evidence not found")
    try:
        decide_treaty_evidence(session, row, payload, actor=_actor(request))
        session.refresh(row)
        return treaty_evidence_read(session, row)
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get(
    "/treaty-evidence/{evidence_id}/decisions",
    response_model=list[TaxTreatyEvidenceDecisionRead],
)
def evidence_decisions(
    evidence_id: UUID,
    session: Session = Depends(get_session),
):
    if session.get(TaxTreatyEvidence, evidence_id) is None:
        raise HTTPException(status_code=404, detail="Tax treaty evidence not found")
    return list(session.exec(select(TaxTreatyEvidenceDecision).where(
        TaxTreatyEvidenceDecision.tax_treaty_evidence_id == evidence_id
    ).order_by(TaxTreatyEvidenceDecision.created_at)).all())


@router.post("/assessments", response_model=TaxResidencyAssessmentRead, status_code=201)
def create_assessment(
    payload: TaxResidencyAssessmentCreate,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        return assessment_read(
            create_tax_residency_assessment(session, payload, actor=_actor(request))
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/assessments", response_model=list[TaxResidencyAssessmentRead])
def list_assessments(
    lead_id: UUID | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    statement = select(TaxResidencyAssessment).order_by(
        TaxResidencyAssessment.created_at.desc()
    )
    if lead_id:
        statement = statement.where(TaxResidencyAssessment.lead_id == lead_id)
    if status:
        statement = statement.where(
            TaxResidencyAssessment.status == status.strip().lower()
        )
    return [
        assessment_read(row)
        for row in session.exec(statement.limit(limit)).all()
    ]


@router.get("/assessments/{assessment_id}", response_model=TaxResidencyAssessmentRead)
def get_assessment(
    assessment_id: UUID,
    session: Session = Depends(get_session),
):
    row = session.get(TaxResidencyAssessment, assessment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tax-residency assessment not found")
    return assessment_read(row)


@router.post(
    "/assessments/{assessment_id}/reviews",
    response_model=TaxResidencyReviewRead,
    status_code=201,
)
def review_assessment(
    assessment_id: UUID,
    payload: TaxResidencyReviewCreate,
    request: Request,
    session: Session = Depends(get_session),
):
    row = session.get(TaxResidencyAssessment, assessment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tax-residency assessment not found")
    try:
        return review_tax_residency_assessment(
            session, row, payload, actor=_actor(request)
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get(
    "/assessments/{assessment_id}/reviews",
    response_model=list[TaxResidencyReviewRead],
)
def assessment_reviews(
    assessment_id: UUID,
    session: Session = Depends(get_session),
):
    if session.get(TaxResidencyAssessment, assessment_id) is None:
        raise HTTPException(status_code=404, detail="Tax-residency assessment not found")
    return list(session.exec(select(TaxResidencyAssessmentReview).where(
        TaxResidencyAssessmentReview.assessment_id == assessment_id
    ).order_by(TaxResidencyAssessmentReview.created_at)).all())

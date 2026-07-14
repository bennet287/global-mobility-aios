from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select
from uuid import UUID

from app.core.db import get_session
from app.models.domain import JurisdictionImmigrationAssessment, JurisdictionSourceCertification
from app.schemas import (
    JurisdictionImmigrationAssessmentProposal,
    JurisdictionImmigrationAssessmentReview,
    JurisdictionSourceCertificationProposal,
    JurisdictionSourceCertificationReview,
)
from app.services.jurisdiction_registry import (
    immigration_assessment_payload,
    import_un_m49_registry,
    jurisdiction_registry_coverage,
    propose_immigration_assessment,
    propose_source_certification,
    review_immigration_assessment,
    review_source_certification,
    source_certification_payload,
)
from app.services.live_intelligence import global_intelligence_dashboard

router = APIRouter(prefix="/api/v1/global-intelligence", tags=["global-live-intelligence-v10.0"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


@router.get("/dashboard")
def api_global_intelligence_dashboard(
    window_days: int = Query(default=90, ge=1, le=730),
    session: Session = Depends(get_session),
):
    return global_intelligence_dashboard(session, window_days=window_days)


@router.get("/registry")
def api_global_jurisdiction_registry(session: Session = Depends(get_session)):
    return jurisdiction_registry_coverage(session)


@router.post("/registry/import-un-m49", status_code=201)
def api_import_global_jurisdiction_registry(
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        release, created = import_un_m49_registry(session, actor=_actor(request))
    except (ValueError, RuntimeError) as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "created": created,
        "release_id": release.id,
        "version": release.version,
        "source_sha256": release.source_sha256,
        "imported_entries": release.imported_entries,
        "status": release.status,
    }


@router.get("/registry/immigration-assessments")
def api_list_immigration_assessments(
    status: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(JurisdictionImmigrationAssessment)
    if status:
        statement = statement.where(JurisdictionImmigrationAssessment.status == status)
    rows = session.exec(
        statement.order_by(JurisdictionImmigrationAssessment.created_at.desc())
    ).all()
    return {"total": len(rows), "assessments": [immigration_assessment_payload(row) for row in rows]}


@router.post("/registry/{jurisdiction_id}/immigration-assessments", status_code=201)
def api_propose_immigration_assessment(
    jurisdiction_id: UUID,
    payload: JurisdictionImmigrationAssessmentProposal,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        assessment = propose_immigration_assessment(
            session,
            jurisdiction_id=jurisdiction_id,
            actor=_actor(request),
            **payload.model_dump(),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return immigration_assessment_payload(assessment)


@router.post("/registry/immigration-assessments/{assessment_id}/review")
def api_review_immigration_assessment(
    assessment_id: UUID,
    payload: JurisdictionImmigrationAssessmentReview,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        assessment = review_immigration_assessment(
            session,
            assessment_id=assessment_id,
            decision=payload.decision,
            notes=payload.notes,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return immigration_assessment_payload(assessment)


@router.get("/registry/source-certifications")
def api_list_source_certifications(
    status: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(JurisdictionSourceCertification)
    if status:
        statement = statement.where(JurisdictionSourceCertification.status == status)
    rows = session.exec(
        statement.order_by(JurisdictionSourceCertification.created_at.desc())
    ).all()
    return {"total": len(rows), "certifications": [source_certification_payload(row) for row in rows]}


@router.post("/registry/{jurisdiction_id}/source-certifications", status_code=201)
def api_propose_source_certification(
    jurisdiction_id: UUID,
    payload: JurisdictionSourceCertificationProposal,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        certification = propose_source_certification(
            session,
            jurisdiction_id=jurisdiction_id,
            actor=_actor(request),
            **payload.model_dump(),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return source_certification_payload(certification)


@router.post("/registry/source-certifications/{certification_id}/review")
def api_review_source_certification(
    certification_id: UUID,
    payload: JurisdictionSourceCertificationReview,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        certification = review_source_certification(
            session,
            certification_id=certification_id,
            decision=payload.decision,
            notes=payload.notes,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return source_certification_payload(certification)

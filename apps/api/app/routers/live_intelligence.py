from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select
from uuid import UUID

from app.core.db import get_session
from app.models.domain import InitialRuleAssertion, JurisdictionImmigrationAssessment, JurisdictionSourceCertification
from app.schemas import (
    InitialRuleAssertionCreateRequest,
    InitialRuleAssertionPublishRequest,
    InitialRuleAssertionReviewRequest,
    CoverageTrancheAssistantPrepareRequest,
    JurisdictionCoverageEvidenceBatchCreate,
    JurisdictionImmigrationAssessmentProposal,
    JurisdictionImmigrationAssessmentReview,
    JurisdictionSourceCertificationProposal,
    JurisdictionSourceCertificationReview,
)
from app.services.coverage_evidence_batches import (
    coverage_batch_payload,
    create_coverage_evidence_batch,
    jurisdiction_coverage_worklist,
    list_coverage_evidence_batches,
    reconcile_coverage_batch_existing_source_linkage,
)
from app.services.coverage_baseline_capture import (
    coverage_batch_baseline_status,
    queue_coverage_batch_baselines,
)
from app.services.coverage_tranche_assistant import (
    coverage_tranche_assistant_config,
    prepare_coverage_tranche,
)
from app.services.initial_rule_assertions import (
    initial_rule_assertion_payload,
    list_initial_rule_assertions,
    propose_initial_rule_assertion,
    publish_initial_rule_assertion,
    review_initial_rule_assertion,
)
from app.services.jurisdiction_registry import (
    immigration_assessment_payload,
    import_un_m49_registry,
    jurisdiction_coverage_receipt,
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
    freshness: str = Query(default="all"),
    coverage: str = Query(default="all"),
    authority_id: UUID | None = Query(default=None),
    confidence: str = Query(default="all"),
    materiality: str = Query(default="all"),
    review_state: str = Query(default="all"),
    session: Session = Depends(get_session),
):
    try:
        return global_intelligence_dashboard(
            session,
            window_days=window_days,
            freshness=freshness,
            coverage=coverage,
            authority_id=authority_id,
            confidence=confidence,
            materiality=materiality,
            review_state=review_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/registry")
def api_global_jurisdiction_registry(session: Session = Depends(get_session)):
    return jurisdiction_registry_coverage(session)


@router.get("/registry/jurisdictions/{jurisdiction_id}/coverage-receipt")
def api_jurisdiction_coverage_receipt(
    jurisdiction_id: UUID,
    session: Session = Depends(get_session),
):
    try:
        return jurisdiction_coverage_receipt(session, jurisdiction_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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

@router.get("/registry/coverage-worklist")
def api_global_coverage_worklist(
    gap: str = Query(default="all"),
    region: str = Query(default="all"),
    limit: int = Query(default=249, ge=1, le=249),
    session: Session = Depends(get_session),
):
    return jurisdiction_coverage_worklist(
        session,
        gap=gap,
        region=region,
        limit=limit,
    )




@router.get("/registry/coverage-tranche-assistant/config")
def api_coverage_tranche_assistant_config():
    return coverage_tranche_assistant_config()


@router.post("/registry/coverage-batches/{batch_id}/assistant/prepare")
def api_prepare_coverage_tranche(
    batch_id: UUID,
    payload: CoverageTrancheAssistantPrepareRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        return prepare_coverage_tranche(
            session,
            batch_id=batch_id,
            payload=payload,
            actor=_actor(request),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/registry/coverage-batches")
def api_list_global_coverage_batches(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    rows = list_coverage_evidence_batches(session, limit=limit)
    return {
        "total": len(rows),
        "batches": [coverage_batch_payload(session, row, include_items=False) for row in rows],
    }


@router.get("/registry/coverage-batches/{batch_id}")
def api_get_global_coverage_batch(
    batch_id: UUID,
    session: Session = Depends(get_session),
):
    from app.models.domain import JurisdictionCoverageEvidenceBatch

    batch = session.get(JurisdictionCoverageEvidenceBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Coverage evidence batch not found")
    return coverage_batch_payload(session, batch)


@router.post("/registry/coverage-batches", status_code=201)
def api_create_global_coverage_batch(
    payload: JurisdictionCoverageEvidenceBatchCreate,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        batch, created = create_coverage_evidence_batch(
            session,
            name=payload.name,
            notes=payload.notes,
            items=[item.model_dump() for item in payload.items],
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = coverage_batch_payload(session, batch)
    result["created"] = created
    return result


@router.post(
    "/registry/coverage-batches/{batch_id}/reconcile-existing-source-linkage"
)
def api_reconcile_coverage_batch_existing_source_linkage(
    batch_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        return reconcile_coverage_batch_existing_source_linkage(
            session,
            batch_id,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/registry/coverage-batches/{batch_id}/baseline-status")
def api_get_coverage_batch_baseline_status(
    batch_id: UUID,
    session: Session = Depends(get_session),
):
    try:
        return coverage_batch_baseline_status(session, batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/registry/coverage-batches/{batch_id}/capture-baselines", status_code=202)
def api_queue_coverage_batch_baselines(
    batch_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        return queue_coverage_batch_baselines(
            session,
            batch_id=batch_id,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/registry/coverage-batches/{batch_id}/initial-rule-assertions")
def api_list_initial_rule_assertions(
    batch_id: UUID,
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    session: Session = Depends(get_session),
):
    from app.models.domain import JurisdictionCoverageEvidenceBatch

    if session.get(JurisdictionCoverageEvidenceBatch, batch_id) is None:
        raise HTTPException(status_code=404, detail="Coverage evidence batch not found")
    rows = list_initial_rule_assertions(
        session,
        batch_id=batch_id,
        status=status,
        limit=limit,
    )
    return {
        "total": len(rows),
        "assertions": [initial_rule_assertion_payload(session, row) for row in rows],
        "safety": {
            "source_change_claimed": False,
            "human_review_required": True,
            "publishes_automatically": False,
        },
    }


@router.post("/registry/coverage-batches/{batch_id}/initial-rule-assertions", status_code=201)
def api_propose_initial_rule_assertion(
    batch_id: UUID,
    payload: InitialRuleAssertionCreateRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        assertion, created = propose_initial_rule_assertion(
            session,
            batch_id=batch_id,
            payload=payload,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = initial_rule_assertion_payload(session, assertion)
    result["created"] = created
    return result


@router.post("/registry/initial-rule-assertions/{assertion_id}/review")
def api_review_initial_rule_assertion(
    assertion_id: UUID,
    payload: InitialRuleAssertionReviewRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        assertion = review_initial_rule_assertion(
            session,
            assertion_id,
            payload,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return initial_rule_assertion_payload(session, assertion)


@router.post("/registry/initial-rule-assertions/{assertion_id}/publish")
def api_publish_initial_rule_assertion(
    assertion_id: UUID,
    payload: InitialRuleAssertionPublishRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        rule, coverage_receipt = publish_initial_rule_assertion(
            session,
            assertion_id,
            payload,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    assertion = session.get(InitialRuleAssertion, assertion_id)
    return {
        "initial_rule_assertion": initial_rule_assertion_payload(session, assertion),
        "verified_rule": rule,
        "coverage_receipt": coverage_receipt,
    }

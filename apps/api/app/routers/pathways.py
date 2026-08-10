from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import MobilityPathway, MobilityPathwayVersion, PathwayComparisonAssessment
from app.schemas import (
    CountryRankingCreate,
    CountryRankingRead,
    PathwayCreate,
    PathwayComparisonRead,
    PathwayDetail,
    PathwayMatchResponse,
    PathwayPublishRequest,
    PathwayRead,
    PathwayRegulatoryImpactList,
    PathwayRegulatoryImpactRead,
    PathwayRegulatoryImpactReviewRequest,
    PathwayRetireRequest,
    PathwayVersionInput,
    PathwayVersionRead,
    ReassessmentAcceptanceCreate,
    ReassessmentAcceptanceRead,
    ReassessmentCandidateRead,
)
from app.services.country_ranking import (
    country_ranking_history,
    generate_country_ranking,
    latest_country_ranking,
)
from app.services.pathway_catalogue import (
    create_pathway,
    create_pathway_version,
    generate_pathway_comparison,
    match_pathways_for_lead,
    pathway_read,
    pathway_comparison_read,
    pathway_version_read,
    publish_pathway_version,
    retire_pathway,
)
from app.services.pathway_regulatory_impacts import (
    list_pathway_regulatory_impacts,
    pathway_regulatory_impact_read,
    review_pathway_regulatory_impact,
)
from app.services.reassessment_acceptance import (
    create_reassessment_acceptance,
    ensure_direct_comparison_allowed,
    execute_reassessment_acceptance,
    get_reassessment_candidate,
    list_reassessment_acceptances,
    reassessment_acceptance_read,
)

router = APIRouter(prefix="/api/v1/pathways", tags=["mobility-planning-v10.13"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _bad_request(exc: ValueError) -> HTTPException:
    message = str(exc)
    status = 404 if message in {
        "Pathway not found",
        "Pathway version not found",
        "Lead not found",
        "Pathway regulatory impact not found",
        "Reassessment acceptance not found",
        "No country ranking found for this lead",
    } else 400
    return HTTPException(status_code=status, detail=message)


@router.post("", response_model=PathwayRead, status_code=201)
def api_create_pathway(
    payload: PathwayCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> PathwayRead:
    try:
        pathway, _ = create_pathway(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc
    return pathway_read(session, pathway)


@router.get("", response_model=list[PathwayRead])
def api_list_pathways(
    country: str | None = None,
    domain: str | None = None,
    catalogue_status: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[PathwayRead]:
    statement = select(MobilityPathway).order_by(MobilityPathway.updated_at.desc())
    if country:
        statement = statement.where(MobilityPathway.country == country.strip().lower())
    if domain:
        statement = statement.where(MobilityPathway.domain == domain.strip().lower())
    if catalogue_status:
        statement = statement.where(MobilityPathway.catalogue_status == catalogue_status.strip().lower())
    rows = session.exec(statement.limit(max(1, min(limit, 500)))).all()
    return [pathway_read(session, row) for row in rows]


@router.get("/regulatory-impacts", response_model=PathwayRegulatoryImpactList)
def api_list_pathway_regulatory_impacts(
    status: str | None = None,
    pathway_id: UUID | None = None,
    pathway_version_id: UUID | None = None,
    verified_rule_id: UUID | None = None,
    impact_type: str | None = None,
    limit: int = 200,
    session: Session = Depends(get_session),
) -> PathwayRegulatoryImpactList:
    return PathwayRegulatoryImpactList(**list_pathway_regulatory_impacts(
        session,
        status=status,
        pathway_id=pathway_id,
        pathway_version_id=pathway_version_id,
        verified_rule_id=verified_rule_id,
        impact_type=impact_type,
        limit=limit,
    ))


@router.post(
    "/regulatory-impacts/{impact_id}/review",
    response_model=PathwayRegulatoryImpactRead,
)
def api_review_pathway_regulatory_impact(
    impact_id: UUID,
    payload: PathwayRegulatoryImpactReviewRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> PathwayRegulatoryImpactRead:
    try:
        impact = review_pathway_regulatory_impact(
            session,
            impact_id,
            payload,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc
    return pathway_regulatory_impact_read(session, impact)


@router.post("/country-rankings/{lead_id}", response_model=CountryRankingRead, status_code=201)
def api_generate_country_ranking(
    lead_id: UUID,
    payload: CountryRankingCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> CountryRankingRead:
    try:
        ensure_direct_comparison_allowed(session, lead_id)
        return generate_country_ranking(session, lead_id, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.get("/country-rankings/{lead_id}/latest", response_model=CountryRankingRead)
def api_latest_country_ranking(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> CountryRankingRead:
    try:
        return latest_country_ranking(session, lead_id)
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.get("/country-rankings/{lead_id}", response_model=list[CountryRankingRead])
def api_country_ranking_history(
    lead_id: UUID,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> list[CountryRankingRead]:
    return country_ranking_history(session, lead_id, limit=limit)


@router.post("/match/{lead_id}", response_model=PathwayMatchResponse)
def api_match_pathways(
    lead_id: UUID,
    limit: int = 10,
    session: Session = Depends(get_session),
) -> PathwayMatchResponse:
    try:
        return PathwayMatchResponse(**match_pathways_for_lead(session, lead_id, limit=limit))
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.post("/compare/{lead_id}", response_model=PathwayComparisonRead)
def api_compare_pathways(
    lead_id: UUID,
    request: Request,
    limit: int = 5,
    session: Session = Depends(get_session),
) -> PathwayComparisonRead:
    try:
        ensure_direct_comparison_allowed(session, lead_id)
        return generate_pathway_comparison(
            session,
            lead_id,
            actor=_actor(request),
            limit=max(1, min(limit, 20)),
        )
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.get("/comparisons/{lead_id}/reassessment", response_model=ReassessmentCandidateRead)
def api_reassessment_candidate(lead_id: UUID, session: Session = Depends(get_session)) -> ReassessmentCandidateRead:
    try:
        return get_reassessment_candidate(session, lead_id)
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.get("/comparisons/{lead_id}/reassessment-acceptances", response_model=list[ReassessmentAcceptanceRead])
def api_list_reassessment_acceptances(
    lead_id: UUID,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[ReassessmentAcceptanceRead]:
    return list_reassessment_acceptances(session, lead_id, limit=limit)


@router.post(
    "/comparisons/{lead_id}/reassessment-acceptances",
    response_model=ReassessmentAcceptanceRead,
    status_code=201,
)
def api_create_reassessment_acceptance(
    lead_id: UUID,
    payload: ReassessmentAcceptanceCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ReassessmentAcceptanceRead:
    try:
        row = create_reassessment_acceptance(session, lead_id, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc
    return reassessment_acceptance_read(row)


@router.post("/reassessment-acceptances/{acceptance_id}/execute", response_model=PathwayComparisonRead)
def api_execute_reassessment_acceptance(
    acceptance_id: UUID,
    request: Request,
    limit: int = 5,
    session: Session = Depends(get_session),
) -> PathwayComparisonRead:
    try:
        return execute_reassessment_acceptance(
            session,
            acceptance_id,
            actor=_actor(request),
            limit=max(1, min(limit, 20)),
        )
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc


@router.get("/comparisons/{lead_id}/latest", response_model=PathwayComparisonRead)
def api_latest_pathway_comparison(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> PathwayComparisonRead:
    assessment = session.exec(
        select(PathwayComparisonAssessment)
        .where(PathwayComparisonAssessment.lead_id == lead_id)
        .order_by(PathwayComparisonAssessment.created_at.desc())
    ).first()
    if assessment is None:
        raise HTTPException(status_code=404, detail="No pathway comparison found for this lead")
    return pathway_comparison_read(assessment)


@router.get("/comparisons/{lead_id}", response_model=list[PathwayComparisonRead])
def api_pathway_comparison_history(
    lead_id: UUID,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> list[PathwayComparisonRead]:
    rows = session.exec(
        select(PathwayComparisonAssessment)
        .where(PathwayComparisonAssessment.lead_id == lead_id)
        .order_by(PathwayComparisonAssessment.created_at.desc())
        .limit(max(1, min(limit, 200)))
    ).all()
    return [pathway_comparison_read(row) for row in rows]


@router.post("/versions/{version_id}/publish", response_model=PathwayRead)
def api_publish_pathway_version(
    version_id: UUID,
    payload: PathwayPublishRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> PathwayRead:
    try:
        pathway, _ = publish_pathway_version(
            session,
            version_id,
            actor=_actor(request),
            review_notes=payload.review_notes,
        )
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc
    return pathway_read(session, pathway, published_only=True)


@router.post("/{pathway_id}/versions", response_model=PathwayVersionRead, status_code=201)
def api_create_pathway_version(
    pathway_id: UUID,
    payload: PathwayVersionInput,
    request: Request,
    session: Session = Depends(get_session),
) -> PathwayVersionRead:
    try:
        version = create_pathway_version(session, pathway_id, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc
    return pathway_version_read(session, version)


@router.post("/{pathway_id}/retire", response_model=PathwayRead)
def api_retire_pathway(
    pathway_id: UUID,
    payload: PathwayRetireRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> PathwayRead:
    try:
        pathway = retire_pathway(
            session,
            pathway_id,
            actor=_actor(request),
            reason=payload.reason,
        )
    except ValueError as exc:
        session.rollback()
        raise _bad_request(exc) from exc
    return pathway_read(session, pathway)


@router.get("/{pathway_id}", response_model=PathwayDetail)
def api_get_pathway(
    pathway_id: UUID,
    session: Session = Depends(get_session),
) -> PathwayDetail:
    pathway = session.get(MobilityPathway, pathway_id)
    if pathway is None:
        raise HTTPException(status_code=404, detail="Pathway not found")
    versions = session.exec(
        select(MobilityPathwayVersion)
        .where(MobilityPathwayVersion.pathway_id == pathway_id)
        .order_by(MobilityPathwayVersion.version_number.desc())
    ).all()
    return PathwayDetail(
        **pathway_read(session, pathway).model_dump(),
        versions=[pathway_version_read(session, version) for version in versions],
    )

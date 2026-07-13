from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import Lead, Opportunity
from app.schemas import (
    OpportunityCreate,
    OpportunityMatchResponse,
    OpportunityMatchResult,
    OpportunityRead,
)
from app.services.opportunity_matcher import match_opportunities_for_lead, seed_default_opportunities

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])


def _model_to_read(opp: Opportunity) -> OpportunityRead:
    return OpportunityRead.from_model(opp)


@router.post("/seed", response_model=dict[str, Any])
def seed_opportunities(session: Session = Depends(get_session)) -> dict[str, Any]:
    count = seed_default_opportunities(session)
    return {"status": "ok", "seeded": count}


@router.post("", response_model=OpportunityRead)
def create_opportunity(
    payload: OpportunityCreate,
    session: Session = Depends(get_session),
) -> Opportunity:
    import json

    opp = Opportunity(
        title=payload.title,
        organization=payload.organization,
        country=payload.country.lower().strip(),
        domain=payload.domain.lower().strip(),
        profession_tags_json=json.dumps([t.lower().strip() for t in payload.profession_tags]),
        field_tags_json=json.dumps([t.lower().strip() for t in payload.field_tags]),
        required_years_experience=payload.required_years_experience,
        language_requirement=payload.language_requirement,
        salary_eur=payload.salary_eur,
        budget_eur=payload.budget_eur,
        description=payload.description,
        source=payload.source,
        active=payload.active,
    )
    session.add(opp)
    session.commit()
    session.refresh(opp)
    return opp


@router.get("", response_model=list[OpportunityRead])
def list_opportunities(
    country: str | None = None,
    domain: str | None = None,
    active: bool | None = None,
    session: Session = Depends(get_session),
) -> list[Opportunity]:
    query = select(Opportunity).order_by(Opportunity.created_at.desc())
    if country:
        query = query.where(Opportunity.country == country.lower().strip())
    if domain:
        query = query.where(Opportunity.domain == domain.lower().strip())
    if active is not None:
        query = query.where(Opportunity.active == active)
    rows = session.exec(query).all()
    return list(rows)


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(
    opportunity_id: UUID,
    session: Session = Depends(get_session),
) -> Opportunity:
    opp = session.get(Opportunity, opportunity_id)
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.post("/match/{lead_id}", response_model=OpportunityMatchResponse)
def match_opportunities(
    lead_id: UUID,
    limit: int = 10,
    session: Session = Depends(get_session),
) -> OpportunityMatchResponse:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = match_opportunities_for_lead(session, lead_id, limit=limit)
    matches = [
        OpportunityMatchResult(
            opportunity=_model_to_read(m["opportunity"]),
            match_score=m["match_score"],
            confidence=m["confidence"],
            reasons=m["reasons"],
            risks=m["risks"],
        )
        for m in result["matches"]
    ]
    return OpportunityMatchResponse(
        lead_id=lead_id,
        matches=matches,
        top_opportunity_id=result.get("top_opportunity_id"),
        summary=result["summary"],
    )

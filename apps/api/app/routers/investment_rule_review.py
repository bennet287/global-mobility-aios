from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import InvestmentMobilityRuleProposal
from app.schemas_investment_rule_review import (
    InvestmentRuleProposalCreate,
    InvestmentRuleProposalRead,
    InvestmentRuleProposalReview,
)
from app.services.investment_rule_review import (
    create_investment_rule_proposal,
    investment_rule_proposal_read,
    review_investment_rule_proposal,
)


router = APIRouter(
    prefix="/api/v1/investment-mobility/rule-proposals",
    tags=["investment-rule-review-v11.9"],
)


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    missing = {"Pathway version not found", "Investment rule proposal not found"}
    return HTTPException(status_code=404 if str(exc) in missing else 400, detail=str(exc))


@router.post("", response_model=InvestmentRuleProposalRead, status_code=201)
def api_create_rule_proposal(
    payload: InvestmentRuleProposalCreate,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        row = create_investment_rule_proposal(session, payload, actor=_actor(request))
        return investment_rule_proposal_read(session, row)
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("", response_model=list[InvestmentRuleProposalRead])
def api_list_rule_proposals(
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    statement = select(InvestmentMobilityRuleProposal).order_by(
        InvestmentMobilityRuleProposal.created_at.desc()
    )
    if status:
        statement = statement.where(
            InvestmentMobilityRuleProposal.status == status.strip().lower()
        )
    return [
        investment_rule_proposal_read(session, row)
        for row in session.exec(statement.limit(limit)).all()
    ]


@router.post("/{proposal_id}/review", response_model=InvestmentRuleProposalRead)
def api_review_rule_proposal(
    proposal_id: UUID,
    payload: InvestmentRuleProposalReview,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        row = review_investment_rule_proposal(
            session, proposal_id, payload, actor=_actor(request)
        )
        return investment_rule_proposal_read(session, row)
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc

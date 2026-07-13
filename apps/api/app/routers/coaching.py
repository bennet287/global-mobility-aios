from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import AgentRun, CoachReview, CoachReviewStatus, Lead
from app.schemas import CoachReviewFeedback, CoachReviewRead, ControlledAgentRunRequest
from app.services.controlled_agents import run_controlled_agent
from app.services.eligibility_coach import run_eligibility_coach_review

router = APIRouter(prefix="/api/v1", tags=["coaching"])


def _latest_target_run(session: Session, lead_id: UUID) -> AgentRun | None:
    target_agents = ["application_readiness_agent", "sales_summary_agent", "truth_explanation_agent"]
    rows = session.exec(
        select(AgentRun)
        .where(AgentRun.lead_id == lead_id)
        .where(AgentRun.agent_name.in_(target_agents))
        .order_by(AgentRun.created_at.desc())
    ).all()
    return rows[0] if rows else None


def _json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {"value": data}
    except Exception:
        return {"raw": value}


@router.post("/coaching/eligibility/{lead_id}", response_model=CoachReviewRead)
def run_eligibility_coach(
    lead_id: UUID,
    target_agent_name: str | None = None,
    session: Session = Depends(get_session),
) -> CoachReview:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Run via controlled agent infrastructure for audit trail.
    target_run = _latest_target_run(session, lead_id)
    target_output = _json_loads(target_run.output_json) if target_run else {}
    lead_data = {
        "id": str(lead.id),
        "full_name": lead.full_name,
        "target_country": lead.target_country,
        "intent": getattr(lead.intent, "value", lead.intent),
    }
    payload = ControlledAgentRunRequest(
        agent_name="eligibility_coach",
        task=f"Audit eligibility/pathway conclusions for {lead.full_name}",
        lead_id=lead_id,
        context={
            "lead": lead_data,
            "target_agent": target_agent_name or (target_run.agent_name if target_run else "unknown"),
            "target_output": target_output,
        },
        actor="system",
    )
    agent_response = run_controlled_agent(session, payload)

    # Persist structured coach review.
    output = agent_response.output
    review = CoachReview(
        lead_id=lead_id,
        agent_run_id=target_run.id if target_run else None,
        coach_agent_name="eligibility_coach",
        target_agent_name=target_agent_name or (target_run.agent_name if target_run else "unknown"),
        conclusion_valid=bool(output.get("conclusion_valid", False)),
        missing_facts_json=json.dumps(output.get("missing_facts", [])),
        source_issues_json=json.dumps(output.get("source_issues", [])),
        corrected_summary=output.get("corrected_summary"),
        confidence=output.get("confidence", "medium"),
        status=CoachReviewStatus.pending,
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return review


@router.get("/coaching/eligibility/{lead_id}/reviews", response_model=list[CoachReviewRead])
def list_eligibility_reviews(lead_id: UUID, session: Session = Depends(get_session)) -> list[CoachReview]:
    rows = session.exec(
        select(CoachReview).where(CoachReview.lead_id == lead_id).order_by(CoachReview.created_at.desc())
    ).all()
    return list(rows)


@router.post("/coaching/reviews/{review_id}/feedback", response_model=CoachReviewRead)
def submit_coach_feedback(
    review_id: UUID,
    feedback: CoachReviewFeedback,
    session: Session = Depends(get_session),
) -> CoachReview:
    review = session.get(CoachReview, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Coach review not found")
    review.operator_feedback = feedback.operator_feedback
    if feedback.override_decision:
        review.status = feedback.override_decision
    session.add(review)
    session.commit()
    session.refresh(review)
    return review

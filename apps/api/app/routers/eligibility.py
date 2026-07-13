from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import EligibilityAssessment, Lead
from app.schemas import EligibilityAssessmentRead, EligibilityEvaluateRequest
from app.services.controlled_agents import run_controlled_agent
from app.services.eligibility_engine import evaluate_lead_eligibility, persist_eligibility_assessment

router = APIRouter(prefix="/api/v1", tags=["eligibility"])


@router.post("/eligibility/evaluate", response_model=EligibilityAssessmentRead)
def evaluate_eligibility(
    payload: EligibilityEvaluateRequest,
    session: Session = Depends(get_session),
) -> EligibilityAssessment:
    lead = session.get(Lead, payload.lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    assessment_result = evaluate_lead_eligibility(
        session,
        payload.lead_id,
        profile_data=payload.profile,
    )

    agent_payload = {
        "agent_name": "eligibility_agent",
        "task": f"Assess eligibility for {lead.full_name}",
        "lead_id": payload.lead_id,
        "context": {
            "profile": payload.profile,
            "assessment": assessment_result,
            "actor": payload.actor,
        },
        "actor": payload.actor,
    }
    from app.schemas import ControlledAgentRunRequest

    agent_response = run_controlled_agent(
        session,
        ControlledAgentRunRequest(**agent_payload),
    )

    assessment = persist_eligibility_assessment(
        session,
        payload.lead_id,
        agent_run_id=agent_response.run_id,
        result=assessment_result,
    )
    return EligibilityAssessmentRead.from_model(assessment)


@router.get("/eligibility/{lead_id}/assessments", response_model=list[EligibilityAssessmentRead])
def list_eligibility_assessments(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> list[EligibilityAssessment]:
    rows = session.exec(
        select(EligibilityAssessment)
        .where(EligibilityAssessment.lead_id == lead_id)
        .order_by(EligibilityAssessment.created_at.desc())
    ).all()
    return list(rows)


@router.get("/eligibility/{lead_id}/latest", response_model=EligibilityAssessmentRead)
def get_latest_eligibility_assessment(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> EligibilityAssessment:
    row = session.exec(
        select(EligibilityAssessment)
        .where(EligibilityAssessment.lead_id == lead_id)
        .order_by(EligibilityAssessment.created_at.desc())
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="No eligibility assessment found for this lead")
    return EligibilityAssessmentRead.from_model(row)

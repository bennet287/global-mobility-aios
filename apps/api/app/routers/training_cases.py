from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import CoachReview, CoachReviewStatus, TrainingCase
from app.schemas import CoachReviewRead, TrainingCaseGenerateRequest, TrainingCaseRead
from app.services.eligibility_coach import evaluate_eligibility_output
from app.services.training_case_generator import generate_training_cases

router = APIRouter(prefix="/api/v1", tags=["training-cases"])


def _json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {"value": data}
    except Exception:
        return {"raw": value}


@router.post("/training-cases/generate", response_model=list[TrainingCaseRead])
def create_training_cases(
    request: TrainingCaseGenerateRequest,
    session: Session = Depends(get_session),
) -> list[TrainingCase]:
    cases = generate_training_cases(
        session,
        count=request.count,
        country=request.country,
        profession=request.profession,
    )
    return cases


@router.get("/training-cases", response_model=list[TrainingCaseRead])
def list_training_cases(
    country: str | None = None,
    profession: str | None = None,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> list[TrainingCase]:
    query = select(TrainingCase).order_by(TrainingCase.created_at.desc())
    if country:
        query = query.where(TrainingCase.country == country)
    if profession:
        query = query.where(TrainingCase.profession == profession)
    rows = session.exec(query.limit(limit)).all()
    return list(rows)


@router.post("/training-cases/{case_id}/run", response_model=CoachReviewRead)
def run_training_case(
    case_id: UUID,
    session: Session = Depends(get_session),
) -> CoachReview:
    case = session.get(TrainingCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Training case not found")

    scenario = _json_loads(case.scenario_json)
    expected = _json_loads(case.expected_outcome_json)

    # Simulate an operational agent output from the scenario.
    simulated_agent_output = {
        "summary": f"Based on the profile, likely pathways include: {', '.join(expected.get('eligible_pathways', []))}.",
        "eligible_pathways": expected.get("eligible_pathways", []),
        "missing_requirements": expected.get("missing_requirements", []),
        "confidence": expected.get("confidence", "medium"),
    }

    lead_data = {
        "target_country": scenario.get("target_country"),
        "intent": scenario.get("goal", "unknown"),
    }
    evaluation = evaluate_eligibility_output(simulated_agent_output, lead_data)

    review = CoachReview(
        lead_id=None,
        agent_run_id=None,
        coach_agent_name="eligibility_coach",
        target_agent_name="training_simulated_agent",
        conclusion_valid=evaluation["conclusion_valid"],
        missing_facts_json=json.dumps(evaluation["missing_facts"]),
        source_issues_json=json.dumps(evaluation["source_issues"]),
        corrected_summary=evaluation["corrected_summary"],
        confidence=evaluation["confidence"],
        status=CoachReviewStatus.pending,
    )
    case.times_run += 1
    session.add(review)
    session.add(case)
    session.commit()
    session.refresh(review)
    return review

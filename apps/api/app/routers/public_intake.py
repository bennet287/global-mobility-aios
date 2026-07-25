from __future__ import annotations

import json
import secrets
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import IntakeSession, IntakeSessionStatus, Lead, LeadIntent, LeadStatus
from app.schemas import PublicIntakeCreate, PublicIntakeResponse
from app.services.auto_communications import generate_auto_communications_for_lead
from app.services.client_portal import issue_client_portal_grant, resolve_client_portal_grant

router = APIRouter(prefix="/api/v1", tags=["public-intake"])


def _intent_from_goal(goal: str) -> LeadIntent:
    lower = goal.lower()
    if any(word in lower for word in {"study", "university", "college", "education", "student"}):
        return LeadIntent.study_abroad
    if any(word in lower for word in {"job", "work", "employment", "nurse", "engineer", "salary"}):
        return LeadIntent.overseas_job
    if any(word in lower for word in {"visa", "permanent", "residency", "immigration"}):
        return LeadIntent.visa
    return LeadIntent.unknown


def _checklist(intent: LeadIntent, target_country: str | None) -> list[str]:
    items = ["Upload passport"]
    if intent == LeadIntent.study_abroad:
        items.extend(["Upload academic transcripts", "Upload language test results", "Confirm target institution"])
    elif intent == LeadIntent.overseas_job:
        items.extend(["Upload CV / resume", "Upload degree / professional certificate", "Confirm language level"])
    elif intent == LeadIntent.visa:
        items.extend(["Upload supporting financial documents", "State purpose of travel"])
    if target_country:
        items.append(f"Review {target_country} eligibility rules")
    items.append("Wait for consultant review")
    return items


@router.post("/public/intake", response_model=PublicIntakeResponse)
def create_public_intake(payload: PublicIntakeCreate, session: Session = Depends(get_session)) -> dict[str, Any]:
    intent = _intent_from_goal(payload.goal)
    notes = f"Goal: {payload.goal}. Nationality: {payload.nationality}. Profession: {payload.profession}."
    if payload.notes:
        notes += f" Notes: {payload.notes}"

    lead = Lead(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        source="public_intake",
        intent=intent,
        target_country=payload.target_country,
        notes=notes,
        status=LeadStatus.new,
    )
    session.add(lead)
    session.flush()

    answers = {
        "goal": payload.goal,
        "nationality": payload.nationality,
        "profession": payload.profession,
        "years_experience": payload.years_experience,
        "target_country": payload.target_country,
    }
    intake_session = IntakeSession(
        lead_id=lead.id,
        session_token=secrets.token_urlsafe(32),
        status=IntakeSessionStatus.completed,
        source="public_intake",
        answers_json=json.dumps(answers, default=str, sort_keys=True),
    )
    session.add(intake_session)
    session.commit()
    session.refresh(lead)
    session.refresh(intake_session)

    _, portal_token = issue_client_portal_grant(
        session,
        lead.id,
        actor="public-intake",
        label="Initial client portal access",
        expires_in_days=30,
    )
    generate_auto_communications_for_lead(
        session,
        lead.id,
        trigger="intake_submitted",
        context={"return_link": f"/portal?token={portal_token}"},
    )

    return {
        "session_token": portal_token,
        "lead_id": lead.id,
        "status": lead.status,
        "checklist": _checklist(intent, payload.target_country),
        "message": "Your case has been received. A consultant will review it shortly.",
    }


@router.get("/public/intake/{session_token}", response_model=PublicIntakeResponse)
def get_public_intake(session_token: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    try:
        portal_grant = resolve_client_portal_grant(session, session_token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Intake session not found") from exc
    lead = session.get(Lead, portal_grant.lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {
        "session_token": session_token,
        "lead_id": lead.id,
        "status": lead.status,
        "checklist": _checklist(lead.intent, lead.target_country),
        "message": "Your case is being reviewed.",
    }

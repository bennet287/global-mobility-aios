from __future__ import annotations

import json
import secrets
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    IntakeSession,
    IntakeSessionStatus,
    Jurisdiction,
    Lead,
    LeadIntent,
    LeadStatus,
)
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


COUNTRY_CODE_ALIASES: dict[str, str] = {
    "austria": "AT",
}

COUNTRY_NAMES: dict[str, str] = {
    "AT": "Austria",
}


def _normalized_target_country(target_country: str) -> str:
    cleaned = target_country.strip()
    code = COUNTRY_CODE_ALIASES.get(cleaned.lower())
    return COUNTRY_NAMES.get(code, cleaned)


def _ensure_target_jurisdiction(session: Session, target_country: str | None) -> None:
    """Ensure a canonical jurisdiction row exists for supported intake destinations."""
    if not target_country:
        return
    normalized = target_country.strip().lower()
    code = COUNTRY_CODE_ALIASES.get(normalized)
    if code is None:
        return
    existing = session.exec(
        select(Jurisdiction).where(Jurisdiction.code == code)
    ).first()
    if existing is None:
        session.add(
            Jurisdiction(
                code=code,
                name=target_country.strip(),
                jurisdiction_type="country",
                region="Europe" if code == "AT" else None,
                active=True,
            )
        )
        session.flush()


def _submission_fingerprint(payload: PublicIntakeCreate) -> str:
    canonical = payload.model_dump(mode="json", exclude={"submission_key"})
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _case_reference(lead: Lead) -> str:
    country = COUNTRY_CODE_ALIASES.get((lead.target_country or "").strip().lower(), "CASE")
    return f"{country}-{str(lead.id).split('-')[0].upper()}"


def _existing_intake(
    session: Session,
    submission_key: str,
) -> IntakeSession | None:
    return session.exec(
        select(IntakeSession).where(IntakeSession.submission_key == submission_key)
    ).first()


def _intake_response(
    session: Session,
    intake_session: IntakeSession,
    *,
    fingerprint: str,
    replay: bool,
) -> dict[str, Any]:
    if intake_session.submission_fingerprint and intake_session.submission_fingerprint != fingerprint:
        raise HTTPException(
            status_code=409,
            detail="This intake submission key is already associated with different case details.",
        )
    if intake_session.lead_id is None:
        raise HTTPException(status_code=503, detail="Your case could not be created. Please try again.")
    lead = session.get(Lead, intake_session.lead_id)
    if lead is None:
        raise HTTPException(status_code=503, detail="Your case could not be loaded. Please try again.")

    _, portal_token = issue_client_portal_grant(
        session,
        lead.id,
        actor="public-intake",
        label="Initial client portal access" if not replay else "Replacement client portal access",
        expires_in_days=30,
    )
    if not replay:
        generate_auto_communications_for_lead(
            session,
            lead.id,
            trigger="intake_submitted",
            context={"return_link": f"/portal?token={portal_token}"},
        )

    is_austria = (lead.target_country or "").strip().lower() == "austria"
    return {
        "session_token": portal_token,
        "lead_id": lead.id,
        "status": lead.status,
        "checklist": _checklist(lead.intent, lead.target_country),
        "message": (
            "Your Austria skilled-employment case has been received. The next step is an evidence-backed pathway review. "
            "You will receive a draft recommendation for your review before any external action is taken."
            if is_austria
            else "Your case has been received. A consultant will review it shortly."
        ),
        "case_reference": _case_reference(lead),
        "idempotent_replay": replay,
    }


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
    if target_country and target_country.strip().lower() == "austria":
        items.append("Confirm Austria occupation and job-offer status")
        items.append("Confirm qualification recognition status for Austria")
    items.append("Wait for consultant review")
    return items


@router.post("/public/intake", response_model=PublicIntakeResponse, status_code=201)
def create_public_intake(payload: PublicIntakeCreate, session: Session = Depends(get_session)) -> dict[str, Any]:
    submission_key = payload.submission_key or f"server-{uuid4()}"
    fingerprint = _submission_fingerprint(payload)
    existing = _existing_intake(session, submission_key)
    if existing is not None:
        return _intake_response(session, existing, fingerprint=fingerprint, replay=True)

    intent = _intent_from_goal(payload.goal)
    target_country = _normalized_target_country(payload.target_country)
    _ensure_target_jurisdiction(session, target_country)

    structured_notes = {
        "goal": payload.goal,
        "nationality": payload.nationality,
        "profession": payload.profession,
        "years_experience": payload.years_experience,
        "target_country": target_country,
        "current_country": payload.current_country,
        "job_offer_status": payload.job_offer_status,
        "qualification_recognition": payload.qualification_recognition,
        "language_level": payload.language_level,
    }
    notes = f"Intake: {json.dumps(structured_notes, default=str, sort_keys=True)}"
    if payload.notes:
        notes += f" Additional notes: {payload.notes}"

    lead = Lead(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        source="public_intake",
        intent=intent,
        target_country=target_country,
        nationality=payload.nationality,
        current_country=payload.current_country,
        occupation_title=payload.profession,
        years_experience=payload.years_experience,
        job_offer_status=payload.job_offer_status,
        qualification_recognition=payload.qualification_recognition,
        german_level=payload.language_level,
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
        "target_country": target_country,
        "current_country": payload.current_country,
        "job_offer_status": payload.job_offer_status,
        "qualification_recognition": payload.qualification_recognition,
        "language_level": payload.language_level,
    }
    intake_session = IntakeSession(
        lead_id=lead.id,
        session_token=secrets.token_urlsafe(32),
        submission_key=submission_key,
        submission_fingerprint=fingerprint,
        status=IntakeSessionStatus.completed,
        source="public_intake",
        answers_json=json.dumps(answers, default=str, sort_keys=True),
    )
    session.add(intake_session)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        existing = _existing_intake(session, submission_key)
        if existing is not None:
            return _intake_response(session, existing, fingerprint=fingerprint, replay=True)
        raise HTTPException(
            status_code=503,
            detail="Your case could not be created. Please try again.",
        ) from exc
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=503,
            detail="Your case could not be created. Please try again.",
        ) from exc
    session.refresh(lead)
    session.refresh(intake_session)
    return _intake_response(session, intake_session, fingerprint=fingerprint, replay=False)


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
        "case_reference": _case_reference(lead),
        "idempotent_replay": False,
    }

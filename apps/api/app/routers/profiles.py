from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import Lead, Profile
from app.schemas import (
    ProfileCreate,
    ProfileRead,
    UniversalMobilityProfileRead,
    UniversalMobilityProfileUpsert,
)
from app.services.mobility_profiles import (
    create_mobility_profile_version,
    current_mobility_profile,
    mobility_profile_read,
)

router = APIRouter()

@router.post("/profiles", response_model=ProfileRead)
def create_profile(payload: ProfileCreate, session: Session = Depends(get_session)) -> Profile:
    lead = session.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    profile = Profile(**payload.model_dump())
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

@router.get("/profiles", response_model=List[ProfileRead])
def list_profiles(session: Session = Depends(get_session), limit: int = 50) -> list[Profile]:
    return list(session.exec(select(Profile).order_by(Profile.created_at.desc()).limit(limit)).all())


@router.put("/profiles/leads/{lead_id}/current", response_model=UniversalMobilityProfileRead)
def replace_current_mobility_profile(
    lead_id: UUID,
    payload: UniversalMobilityProfileUpsert,
    request: Request,
    session: Session = Depends(get_session),
) -> UniversalMobilityProfileRead:
    context = getattr(request.state, "auth", None)
    actor = getattr(context, "username", "api-operator")
    try:
        profile = create_mobility_profile_version(session, lead_id, payload, actor=actor)
    except ValueError as exc:
        session.rollback()
        message = str(exc)
        status = 404 if message == "Lead not found" else 400
        raise HTTPException(status_code=status, detail=message) from exc
    return mobility_profile_read(profile)


@router.get("/profiles/leads/{lead_id}/current", response_model=UniversalMobilityProfileRead)
def get_current_mobility_profile(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> UniversalMobilityProfileRead:
    if session.get(Lead, lead_id) is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    profile = current_mobility_profile(session, lead_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="No mobility profile found for this lead")
    return mobility_profile_read(profile)


@router.get("/profiles/leads/{lead_id}/history", response_model=List[UniversalMobilityProfileRead])
def get_mobility_profile_history(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> list[UniversalMobilityProfileRead]:
    if session.get(Lead, lead_id) is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    rows = session.exec(
        select(Profile)
        .where(Profile.lead_id == lead_id)
        .order_by(Profile.profile_version.desc(), Profile.updated_at.desc())
    ).all()
    return [mobility_profile_read(row) for row in rows]

@router.get("/profiles/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: UUID, session: Session = Depends(get_session)) -> Profile:
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

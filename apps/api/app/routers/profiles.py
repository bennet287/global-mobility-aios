from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import Lead, Profile
from app.schemas import ProfileCreate, ProfileRead

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

@router.get("/profiles/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: UUID, session: Session = Depends(get_session)) -> Profile:
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

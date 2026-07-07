from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import FollowUp, now_utc
from app.schemas import FollowUpRead, FollowUpUpdate

router = APIRouter()

@router.get("/follow-ups", response_model=List[FollowUpRead])
def list_follow_ups(
    session: Session = Depends(get_session),
    status: str | None = None,
    limit: int = 50,
) -> list[FollowUp]:
    statement = select(FollowUp).order_by(FollowUp.created_at.desc()).limit(limit)

    if status:
        statement = (
            select(FollowUp)
            .where(FollowUp.status == status)
            .order_by(FollowUp.created_at.desc())
            .limit(limit)
        )

    return list(session.exec(statement).all())

@router.get("/follow-ups/{follow_up_id}", response_model=FollowUpRead)
def get_follow_up(follow_up_id: UUID, session: Session = Depends(get_session)) -> FollowUp:
    follow_up = session.get(FollowUp, follow_up_id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return follow_up

@router.patch("/follow-ups/{follow_up_id}", response_model=FollowUpRead)
def update_follow_up(
    follow_up_id: UUID,
    payload: FollowUpUpdate,
    session: Session = Depends(get_session),
) -> FollowUp:
    follow_up = session.get(FollowUp, follow_up_id)
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(follow_up, field, value)

    follow_up.updated_at = now_utc()
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return follow_up

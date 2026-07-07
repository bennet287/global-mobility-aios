from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import HumanReview, now_utc
from app.schemas import HumanReviewRead, HumanReviewUpdate

router = APIRouter()

@router.get("/reviews", response_model=List[HumanReviewRead])
def list_reviews(
    session: Session = Depends(get_session),
    status: str | None = "pending",
    limit: int = 50,
) -> list[HumanReview]:
    statement = select(HumanReview).order_by(HumanReview.created_at.desc()).limit(limit)

    if status:
        statement = (
            select(HumanReview)
            .where(HumanReview.status == status)
            .order_by(HumanReview.created_at.desc())
            .limit(limit)
        )

    return list(session.exec(statement).all())

@router.get("/reviews/{review_id}", response_model=HumanReviewRead)
def get_review(review_id: UUID, session: Session = Depends(get_session)) -> HumanReview:
    review = session.get(HumanReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Human review not found")
    return review

@router.patch("/reviews/{review_id}", response_model=HumanReviewRead)
def update_review(
    review_id: UUID,
    payload: HumanReviewUpdate,
    session: Session = Depends(get_session),
) -> HumanReview:
    review = session.get(HumanReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Human review not found")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(review, field, value)

    review.updated_at = now_utc()
    session.add(review)
    session.commit()
    session.refresh(review)
    return review

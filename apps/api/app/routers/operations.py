from datetime import timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    FollowUp,
    FollowUpStatus,
    HumanReview,
    Lead,
    LeadStatus,
    ReviewStatus,
    WorkflowRun,
    WorkflowStatus,
    now_utc,
)

router = APIRouter()


class ReviewActionRequest(BaseModel):
    reviewer_notes: Optional[str] = None


def _get_review(session: Session, review_id: UUID) -> HumanReview:
    review = session.get(HumanReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Human review not found")
    return review


def _maybe_create_follow_up(
    session: Session,
    review: HumanReview,
    message: str,
) -> FollowUp | None:
    if not review.lead_id:
        return None

    existing = session.exec(
        select(FollowUp)
        .where(FollowUp.lead_id == review.lead_id)
        .where(FollowUp.workflow_run_id == review.workflow_run_id)
    ).first()

    if existing:
        return existing

    follow_up = FollowUp(
        lead_id=review.lead_id,
        workflow_run_id=review.workflow_run_id,
        channel="email",
        status=FollowUpStatus.pending,
        due_at=now_utc() + timedelta(hours=24),
        message=message,
    )
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return follow_up


def _complete_workflow_if_present(session: Session, review: HumanReview) -> None:
    if not review.workflow_run_id:
        return

    workflow = session.get(WorkflowRun, review.workflow_run_id)
    if workflow:
        workflow.status = WorkflowStatus.completed
        workflow.completed_at = now_utc()
        session.add(workflow)


def _update_lead_status(session: Session, review: HumanReview, status: LeadStatus) -> None:
    if not review.lead_id:
        return

    lead = session.get(Lead, review.lead_id)
    if lead:
        lead.status = status
        lead.updated_at = now_utc()
        session.add(lead)


@router.post("/operations/reviews/{review_id}/approve")
def approve_review(
    review_id: UUID,
    payload: ReviewActionRequest,
    session: Session = Depends(get_session),
) -> dict:
    review = _get_review(session, review_id)

    review.status = ReviewStatus.approved
    review.reviewer_notes = payload.reviewer_notes or "AI truth-check decision approved by human reviewer."
    review.updated_at = now_utc()

    _update_lead_status(session, review, LeadStatus.qualified)
    _complete_workflow_if_present(session, review)

    follow_up = _maybe_create_follow_up(
        session,
        review,
        "Human review approved. Send a corrected, source-grounded explanation to the lead and request missing documents.",
    )

    session.add(review)
    session.commit()
    session.refresh(review)

    return jsonable_encoder(
        {
            "status": "approved",
            "review": review,
            "follow_up": follow_up,
        }
    )


@router.post("/operations/reviews/{review_id}/reject")
def reject_review(
    review_id: UUID,
    payload: ReviewActionRequest,
    session: Session = Depends(get_session),
) -> dict:
    review = _get_review(session, review_id)

    review.status = ReviewStatus.rejected
    review.reviewer_notes = payload.reviewer_notes or "AI truth-check decision rejected by human reviewer. Re-investigation required."
    review.updated_at = now_utc()

    _update_lead_status(session, review, LeadStatus.human_review)

    session.add(review)
    session.commit()
    session.refresh(review)

    return jsonable_encoder(
        {
            "status": "rejected",
            "review": review,
            "next_action": "Re-check official sources and update the truth claim manually.",
        }
    )


@router.post("/operations/reviews/{review_id}/resolve")
def resolve_review(
    review_id: UUID,
    payload: ReviewActionRequest,
    session: Session = Depends(get_session),
) -> dict:
    review = _get_review(session, review_id)

    review.status = ReviewStatus.resolved
    review.reviewer_notes = payload.reviewer_notes or "Human review resolved."
    review.updated_at = now_utc()

    _update_lead_status(session, review, LeadStatus.qualified)
    _complete_workflow_if_present(session, review)

    session.add(review)
    session.commit()
    session.refresh(review)

    return jsonable_encoder(
        {
            "status": "resolved",
            "review": review,
        }
    )


@router.post("/operations/follow-ups/{follow_up_id}/complete")
def complete_follow_up(
    follow_up_id: UUID,
    session: Session = Depends(get_session),
) -> dict:
    follow_up = session.get(FollowUp, follow_up_id)

    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    follow_up.status = FollowUpStatus.completed
    follow_up.updated_at = now_utc()

    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)

    return jsonable_encoder(
        {
            "status": "completed",
            "follow_up": follow_up,
        }
    )

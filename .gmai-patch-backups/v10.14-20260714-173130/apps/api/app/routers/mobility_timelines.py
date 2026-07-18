from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import MobilityTimeline
from app.schemas import (
    MobilityTimelineGenerateRequest,
    MobilityTimelineRead,
    MobilityTimelineTransitionRequest,
)
from app.services.mobility_timelines import (
    activate_timeline,
    generate_timeline,
    timeline_read,
    transition_milestone,
)

router = APIRouter(prefix="/api/v1/mobility-timelines", tags=["mobility-timelines-v8.3"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    status = 404 if "not found" in message.lower() else 400
    return HTTPException(status_code=status, detail=message)


@router.post("/from-comparison/{assessment_id}", response_model=MobilityTimelineRead, status_code=201)
def api_generate_timeline(
    assessment_id: UUID,
    request: Request,
    payload: MobilityTimelineGenerateRequest = MobilityTimelineGenerateRequest(),
    session: Session = Depends(get_session),
) -> MobilityTimelineRead:
    try:
        return generate_timeline(
            session,
            assessment_id,
            actor=_actor(request),
            target_date=payload.target_date,
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("", response_model=list[MobilityTimelineRead])
def api_list_timelines(
    lead_id: UUID | None = None,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> list[MobilityTimelineRead]:
    statement = select(MobilityTimeline).order_by(MobilityTimeline.created_at.desc())
    if lead_id:
        statement = statement.where(MobilityTimeline.lead_id == lead_id)
    rows = session.exec(statement.limit(max(1, min(limit, 200)))).all()
    return [timeline_read(session, row) for row in rows]


@router.get("/{timeline_id}", response_model=MobilityTimelineRead)
def api_get_timeline(
    timeline_id: UUID,
    session: Session = Depends(get_session),
) -> MobilityTimelineRead:
    timeline = session.get(MobilityTimeline, timeline_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Mobility timeline not found")
    return timeline_read(session, timeline)


@router.post("/{timeline_id}/activate", response_model=MobilityTimelineRead)
def api_activate_timeline(
    timeline_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> MobilityTimelineRead:
    try:
        return activate_timeline(session, timeline_id, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/{timeline_id}/milestones/{milestone_id}/transition", response_model=MobilityTimelineRead)
def api_transition_milestone(
    timeline_id: UUID,
    milestone_id: UUID,
    payload: MobilityTimelineTransitionRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> MobilityTimelineRead:
    try:
        return transition_milestone(
            session,
            timeline_id,
            milestone_id,
            action=payload.action,
            note=payload.note,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc

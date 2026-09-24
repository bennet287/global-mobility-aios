from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import AgentRun
from app.schemas import AgentRunRead
from app.services.agent_run_cancellation import (
    AgentRunCancellationConflict,
    AgentRunCancellationNotFound,
    request_agent_run_cancellation,
    request_agent_run_transport_revoke,
)

router = APIRouter()


class AgentRunCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _require_admin(request: Request) -> None:
    context = getattr(request.state, "auth", None)
    if str(getattr(context, "role", "read_only")) != "admin":
        raise HTTPException(
            status_code=403,
            detail="AgentRun cancellation requires the admin role",
        )


@router.get("/agent-runs", response_model=List[AgentRunRead])
def list_agent_runs(session: Session = Depends(get_session), limit: int = 50) -> list[AgentRun]:
    return list(session.exec(select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)).all())


@router.get("/agent-runs/{agent_run_id}", response_model=AgentRunRead)
def get_agent_run(agent_run_id: UUID, session: Session = Depends(get_session)) -> AgentRun:
    run = session.get(AgentRun, agent_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@router.post("/agent-runs/{agent_run_id}/cancel")
def cancel_agent_run(
    agent_run_id: UUID,
    payload: AgentRunCancelRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    _require_admin(request)
    actor = _actor(request)
    try:
        run = request_agent_run_cancellation(
            session,
            run_id=agent_run_id,
            actor=actor,
            reason=payload.reason,
        )
        session.commit()
        session.refresh(run)
    except AgentRunCancellationNotFound as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail="Agent run not found") from exc
    except AgentRunCancellationConflict as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        session.rollback()
        raise

    revoke_requested, revoke_error = request_agent_run_transport_revoke(
        session,
        run=run,
        actor=actor,
    )
    return {
        "run_id": str(run.id),
        "status": run.status,
        "transport_task_id": str(run.id),
        "transport_identity": "agent_run_id",
        "transport_revoke_requested": revoke_requested,
        "transport_revoke_error": revoke_error,
        "worker_termination_requested": False,
        "rollback_claimed": False,
    }

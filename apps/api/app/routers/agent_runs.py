from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import AgentRun
from app.schemas import AgentRunRead

router = APIRouter()

@router.get("/agent-runs", response_model=List[AgentRunRead])
def list_agent_runs(session: Session = Depends(get_session), limit: int = 50) -> list[AgentRun]:
    return list(session.exec(select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)).all())

@router.get("/agent-runs/{agent_run_id}", response_model=AgentRunRead)
def get_agent_run(agent_run_id: UUID, session: Session = Depends(get_session)) -> AgentRun:
    run = session.get(AgentRun, agent_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run

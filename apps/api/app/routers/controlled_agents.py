from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.db import get_session
from app.schemas import ControlledAgentRunRequest, ControlledAgentRunResponse
from app.services.controlled_agents import list_controlled_agents, run_controlled_agent

router = APIRouter()


@router.get("/api/v1/controlled-agents")
def get_controlled_agents() -> dict:
    return {
        "version": "v4.0",
        "mode": "workflow_assistant_only",
        "automatic_actions_enabled": False,
        "agents": list_controlled_agents(),
    }


@router.post("/api/v1/controlled-agents/run", response_model=ControlledAgentRunResponse)
def run_controlled_agent_endpoint(
    payload: ControlledAgentRunRequest,
    session: Session = Depends(get_session),
) -> ControlledAgentRunResponse:
    try:
        return run_controlled_agent(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/debug/controlled-agents")
def debug_controlled_agents() -> dict:
    return {
        "module": "controlled_ai_agents",
        "version": "v4.0",
        "send_actions_enabled": False,
        "external_llm_required": False,
        "agent_count": len(list_controlled_agents()),
    }

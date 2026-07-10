from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.agents.registry import AGENT_REGISTRY, CONTROLLED_AGENT_REGISTRY
from app.core.db import get_session
from app.schemas import AgentRunRequest, AgentRunResponse, ControlledAgentRunRequest
from app.services.controlled_agents import run_controlled_agent

router = APIRouter()


@router.get("/agents")
def list_agents() -> dict:
    return {
        "version": "v4.0",
        "mode": "controlled_workflow_assistants",
        "agents": AGENT_REGISTRY,
        "controlled_agents": CONTROLLED_AGENT_REGISTRY,
    }


@router.post("/agents/run", response_model=AgentRunResponse)
def run_agent(
    payload: AgentRunRequest,
    session: Session = Depends(get_session),
) -> AgentRunResponse:
    if payload.agent_name not in AGENT_REGISTRY:
        return AgentRunResponse(
            agent_name=payload.agent_name,
            status="unknown_agent",
            output={"error": "Agent is not registered."},
            message="Agent is not registered.",
        )

    controlled_response = run_controlled_agent(
        session,
        ControlledAgentRunRequest(
            agent_name=payload.agent_name,
            task=payload.task,
            context=payload.context,
        ),
    )
    return AgentRunResponse(
        agent_name=controlled_response.agent_name,
        status=controlled_response.status,
        output={
            **controlled_response.output,
            "run_id": str(controlled_response.run_id),
            "guardrails": controlled_response.guardrails,
            "requires_human_review": controlled_response.requires_human_review,
        },
        message="Legacy agent endpoint routed through controlled v4.0 agent service.",
        created_at=controlled_response.created_at,
    )

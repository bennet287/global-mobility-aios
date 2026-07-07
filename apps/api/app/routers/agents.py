from fastapi import APIRouter

from app.schemas import AgentRunRequest, AgentRunResponse
from app.agents.registry import AGENT_REGISTRY

router = APIRouter()


@router.get("/agents")
def list_agents() -> dict:
    return {"agents": AGENT_REGISTRY}


@router.post("/agents/run", response_model=AgentRunResponse)
def run_agent(payload: AgentRunRequest) -> AgentRunResponse:
    if payload.agent_name not in AGENT_REGISTRY:
        return AgentRunResponse(
            agent_name=payload.agent_name,
            status="unknown_agent",
            output={"error": "Agent is not registered."},
        )

    # This is intentionally deterministic. Replace with CrewAI execution after approval guardrails are in place.
    agent = AGENT_REGISTRY[payload.agent_name]
    return AgentRunResponse(
        agent_name=payload.agent_name,
        status="simulated",
        output={
            "role": agent["role"],
            "task_received": payload.task,
            "guardrail": agent["guardrail"],
            "next_step": "Route through LangGraph workflow and Truth Engine before client-facing output.",
        },
    )

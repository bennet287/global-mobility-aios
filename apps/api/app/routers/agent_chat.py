from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.schemas import AgentChatRequest, AgentChatResponse
from app.services.inhouse_consultant import consult

router = APIRouter(tags=["agent-chat-v1"])


@router.post("/api/v1/agent-chat", response_model=AgentChatResponse)
def agent_chat(payload: AgentChatRequest, session: Session = Depends(get_session)) -> AgentChatResponse:
    """Chat with the in-house consultant agent.

    The consultant parses the operator's natural-language request, identifies the
    relevant lead and agent, and returns a routing decision. It does NOT execute
    any agent itself; the frontend must confirm a `propose_action` decision and
    call the controlled-agent run/run-batch endpoints separately.
    """
    result = consult(
        session=session,
        message=payload.message,
        conversation_history=payload.conversation_history,
        lead_hint=payload.lead_hint,
    )
    return AgentChatResponse(decision=result["decision"], reply=result["reply"])

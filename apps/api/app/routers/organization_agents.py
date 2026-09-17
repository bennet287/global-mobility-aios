from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.models.agent_lifecycle import OrganizationAgent
from app.services.organization_agent_lifecycle import transition_organization_agent
from app.services.organization_command import InvalidTransition, NotFound


router = APIRouter(
    prefix="/api/v1/organization/agents",
    tags=["ai-organization-agent-lifecycle-v15"],
)


class OrganizationAgentTransitionRequest(BaseModel):
    target_status: str = Field(min_length=1, max_length=32)
    reason: str = Field(min_length=1, max_length=1000)


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _require_admin(request: Request) -> None:
    context = getattr(request.state, "auth", None)
    if str(getattr(context, "role", "read_only")) != "admin":
        raise HTTPException(
            status_code=403,
            detail="Organization agent lifecycle mutation requires the admin role",
        )


def _transition_response(agent: OrganizationAgent) -> dict:
    return {
        "id": agent.id,
        "agent_key": agent.agent_key,
        "registry_key": agent.registry_key,
        "registry_version": agent.registry_version,
        "status": agent.status,
        "lifecycle_reason": agent.lifecycle_reason,
        "updated_at": agent.updated_at,
        "activated_at": agent.activated_at,
        "suspended_at": agent.suspended_at,
        "retired_at": agent.retired_at,
        "authority_granted": False,
        "permissions_granted": False,
        "credentials_granted": False,
        "autonomy_granted": False,
        "tool_access_granted": False,
        "work_assignment_granted": False,
        "execution_granted": False,
    }


@router.post("/{agent_id}/transitions")
def transition_agent_lifecycle(
    agent_id: UUID,
    payload: OrganizationAgentTransitionRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    _require_admin(request)
    try:
        agent = transition_organization_agent(
            session,
            agent_id=agent_id,
            target_status=payload.target_status,
            reason=payload.reason,
            actor=_actor(request),
        )
        session.commit()
        session.refresh(agent)
    except NotFound as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidTransition as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        session.rollback()
        raise
    return _transition_response(agent)

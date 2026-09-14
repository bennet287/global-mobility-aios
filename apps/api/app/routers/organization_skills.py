from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import OrganizationPosition
from app.models.skill_registry import OrganizationSkill
from app.services.organization_skill_registry import (
    bind_skill_to_position,
    evaluate_skill_applicability,
    list_active_skills,
)


router = APIRouter(prefix="/api/v1/organization/skills", tags=["ai-organization-skills-v14"])


class SkillBindingRequest(BaseModel):
    position_id: UUID
    assignment_reason: str = Field(min_length=1, max_length=1000)


class SkillApplicabilityRequest(BaseModel):
    position_id: UUID
    available_tools: list[str] = Field(default_factory=list)
    available_permissions: list[str] = Field(default_factory=list)


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _require_admin(request: Request) -> None:
    context = getattr(request.state, "auth", None)
    if str(getattr(context, "role", "read_only")) != "admin":
        raise HTTPException(status_code=403, detail="Skill registry mutation requires the admin role")


@router.get("")
def get_active_skills(session: Session = Depends(get_session)) -> list[OrganizationSkill]:
    return list_active_skills(session)


@router.post("/{skill_id}/bindings", status_code=201)
def create_skill_binding(
    skill_id: UUID,
    payload: SkillBindingRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    _require_admin(request)
    try:
        binding = bind_skill_to_position(
            session,
            position_id=payload.position_id,
            skill_id=skill_id,
            assignment_reason=payload.assignment_reason,
            actor=_actor(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.commit()
    session.refresh(binding)
    return {
        "id": binding.id,
        "organization_position_id": binding.organization_position_id,
        "organization_skill_id": binding.organization_skill_id,
        "status": binding.status,
        "assignment_reason": binding.assignment_reason,
        "assigned_by": binding.assigned_by,
    }


@router.post("/{skill_id}/applicability")
def check_skill_applicability(
    skill_id: UUID,
    payload: SkillApplicabilityRequest,
    session: Session = Depends(get_session),
) -> dict:
    skill = session.get(OrganizationSkill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Organization skill not found")
    position = session.get(OrganizationPosition, payload.position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="Organization position not found")
    try:
        result = evaluate_skill_applicability(
            skill=skill,
            position=position,
            available_tools=payload.available_tools,
            available_permissions=payload.available_permissions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "skill_id": result.skill_id,
        "skill_key": result.skill_key,
        "version": result.version,
        "applicable": result.applicable,
        "reasons": list(result.reasons),
        "missing_tools": list(result.missing_tools),
        "missing_permissions": list(result.missing_permissions),
        "authority_granted": False,
        "credentials_granted": False,
    }

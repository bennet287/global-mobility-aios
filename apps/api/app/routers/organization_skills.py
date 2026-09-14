from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import OrganizationPosition
from app.models.skill_registry import OrganizationSkill
from app.services.organization_skill_audit import (
    binding_audit_state,
    record_skill_mutation,
    skill_audit_state,
)
from app.services.organization_skill_lifecycle import (
    NativeSkillDefinition,
    create_native_skill,
    create_native_skill_version,
    deprecate_native_skill,
)
from app.services.organization_skill_registry import (
    bind_skill_to_position,
    evaluate_skill_applicability,
    list_active_skills,
    validate_native_skill_contract,
)


router = APIRouter(prefix="/api/v1/organization/skills", tags=["ai-organization-skills-v14"])


class SkillBindingRequest(BaseModel):
    position_id: UUID
    assignment_reason: str = Field(min_length=1, max_length=1000)


class SkillApplicabilityRequest(BaseModel):
    position_id: UUID
    available_tools: list[str] = Field(default_factory=list)
    available_permissions: list[str] = Field(default_factory=list)


class NativeSkillDefinitionRequest(BaseModel):
    skill_key: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    capability_family: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=4000)
    compatible_departments: list[str] = Field(default_factory=list)
    compatible_position_keys: list[str] = Field(default_factory=list)
    tool_requirements: list[str] = Field(default_factory=list)
    permission_requirements: list[str] = Field(default_factory=list)
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    evidence_expectations: list[str] = Field(default_factory=list)

    def to_definition(self) -> NativeSkillDefinition:
        return NativeSkillDefinition(
            skill_key=self.skill_key,
            name=self.name,
            capability_family=self.capability_family,
            description=self.description,
            compatible_departments=tuple(self.compatible_departments),
            compatible_position_keys=tuple(self.compatible_position_keys),
            tool_requirements=tuple(self.tool_requirements),
            permission_requirements=tuple(self.permission_requirements),
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            evidence_expectations=tuple(self.evidence_expectations),
        )


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _require_admin(request: Request) -> None:
    context = getattr(request.state, "auth", None)
    if str(getattr(context, "role", "read_only")) != "admin":
        raise HTTPException(status_code=403, detail="Skill registry mutation requires the admin role")


def _skill_response(skill: OrganizationSkill) -> dict:
    return {
        "id": skill.id,
        "skill_key": skill.skill_key,
        "version": skill.version,
        "origin": skill.origin,
        "status": skill.status,
        "validation_status": skill.validation_status,
        "content_sha256": skill.content_sha256,
        "supersedes_skill_id": skill.supersedes_skill_id,
        "authority_granted": False,
        "permissions_granted": False,
        "credentials_granted": False,
        "autonomy_granted": False,
    }


@router.get("")
def get_active_skills(session: Session = Depends(get_session)) -> list[OrganizationSkill]:
    return list_active_skills(session)


@router.post("/native", status_code=201)
def create_native_skill_definition(
    payload: NativeSkillDefinitionRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    _require_admin(request)
    actor = _actor(request)
    try:
        skill = create_native_skill(session, definition=payload.to_definition(), actor=actor)
        record_skill_mutation(
            session,
            action="organization_skill.created",
            actor=actor,
            entity_type="organization_skill",
            entity_id=skill.id,
            after_state=skill_audit_state(skill),
            reason="native skill created through governed registry API",
        )
        session.commit()
        session.refresh(skill)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _skill_response(skill)


@router.post("/{skill_id}/versions", status_code=201)
def create_native_skill_successor(
    skill_id: UUID,
    payload: NativeSkillDefinitionRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    _require_admin(request)
    actor = _actor(request)
    before_state = skill_audit_state(session.get(OrganizationSkill, skill_id))
    try:
        skill = create_native_skill_version(
            session,
            skill_id=skill_id,
            definition=payload.to_definition(),
            actor=actor,
        )
        record_skill_mutation(
            session,
            action="organization_skill.versioned",
            actor=actor,
            entity_type="organization_skill",
            entity_id=skill.id,
            before_state=before_state,
            after_state=skill_audit_state(skill),
            reason="native skill successor created through governed registry API",
        )
        session.commit()
        session.refresh(skill)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _skill_response(skill)


@router.post("/{skill_id}/deprecate")
def deprecate_native_skill_definition(
    skill_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    _require_admin(request)
    actor = _actor(request)
    before_state = skill_audit_state(session.get(OrganizationSkill, skill_id))
    try:
        skill = deprecate_native_skill(session, skill_id=skill_id)
        record_skill_mutation(
            session,
            action="organization_skill.deprecated",
            actor=actor,
            entity_type="organization_skill",
            entity_id=skill.id,
            before_state=before_state,
            after_state=skill_audit_state(skill),
            reason="native skill deprecated through governed registry API",
        )
        session.commit()
        session.refresh(skill)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _skill_response(skill)


@router.post("/{skill_id}/validate")
def validate_native_skill(
    skill_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    _require_admin(request)
    actor = _actor(request)
    before_state = skill_audit_state(session.get(OrganizationSkill, skill_id))
    try:
        result = validate_native_skill_contract(session, skill_id=skill_id)
        skill = session.get(OrganizationSkill, skill_id)
        record_skill_mutation(
            session,
            action="organization_skill.validated",
            actor=actor,
            entity_type="organization_skill",
            entity_id=result.skill_id,
            before_state=before_state,
            after_state=skill_audit_state(skill),
            reason=f"{result.validator}:{'passed' if result.passed else 'failed'}",
        )
        session.commit()
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "skill_id": result.skill_id,
        "skill_key": result.skill_key,
        "version": result.version,
        "validation_status": "passed" if result.passed else "failed",
        "validator": result.validator,
        "checks": list(result.checks),
        "failures": list(result.failures),
        "content_sha256": result.content_sha256,
        "authority_granted": False,
        "permissions_granted": False,
        "credentials_granted": False,
        "autonomy_granted": False,
    }


@router.post("/{skill_id}/bindings", status_code=201)
def create_skill_binding(
    skill_id: UUID,
    payload: SkillBindingRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    _require_admin(request)
    actor = _actor(request)
    try:
        binding = bind_skill_to_position(
            session,
            position_id=payload.position_id,
            skill_id=skill_id,
            assignment_reason=payload.assignment_reason,
            actor=actor,
        )
        record_skill_mutation(
            session,
            action="organization_skill.binding_upserted",
            actor=actor,
            entity_type="organization_position_skill",
            entity_id=binding.id,
            after_state=binding_audit_state(binding),
            reason="position skill binding created or reaffirmed through governed registry API",
        )
        session.commit()
        session.refresh(binding)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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

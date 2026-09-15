from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationPosition, OrganizationalWorkItem
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill


@dataclass(frozen=True)
class SkillWorkCandidate:
    position_id: UUID
    position_key: str
    skill_id: UUID
    skill_key: str
    skill_version: int


@dataclass(frozen=True)
class SkillWorkCandidateSet:
    work_item_id: UUID
    capability_family: str
    candidates: tuple[SkillWorkCandidate, ...]
    diagnostic_only: bool = True
    prerequisites_resolved: bool = False
    authority_granted: bool = False
    permissions_granted: bool = False
    credentials_granted: bool = False
    autonomy_granted: bool = False
    assignment_granted: bool = False
    execution_granted: bool = False


def _string_list_or_none(raw: str) -> tuple[str, ...] | None:
    """Parse a registry string-list contract, returning None when malformed."""
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        return None
    return tuple(value)


def _is_candidate_compatible(skill: OrganizationSkill, position: OrganizationPosition) -> bool:
    departments = _string_list_or_none(skill.compatible_departments_json)
    position_keys = _string_list_or_none(skill.compatible_position_keys_json)
    required_tools = _string_list_or_none(skill.tool_requirements_json)
    required_permissions = _string_list_or_none(skill.permission_requirements_json)
    if None in (departments, position_keys, required_tools, required_permissions):
        return False
    if departments and position.department not in departments:
        return False
    if position_keys and position.position_key not in position_keys:
        return False
    # Until canonical server-side entitlement truth exists, any declared tool or
    # permission prerequisite makes this skill ineligible for operational matching.
    return not required_tools and not required_permissions


def find_skill_work_candidates(
    session: Session,
    *,
    work_item: OrganizationalWorkItem,
    capability_family: str,
) -> SkillWorkCandidateSet:
    """Return capability candidates without authorizing assignment or execution.

    Phase 14.6 matches canonical active, unsuspended positions to eligible exact
    bindings and active validated skill versions. Compatibility contracts are
    enforced fail-closed. Skills declaring tool or permission requirements are
    excluded because canonical server-side per-position entitlement truth does not
    yet exist. The result is diagnostic candidate discovery only and must never be
    consumed as authorization, assignment, routing, credential, or execution truth.
    """
    family = capability_family.strip()
    if not family:
        raise ValueError("capability_family is required")

    rows = session.exec(
        select(OrganizationPositionSkill, OrganizationSkill, OrganizationPosition)
        .join(
            OrganizationSkill,
            OrganizationPositionSkill.organization_skill_id == OrganizationSkill.id,
        )
        .join(
            OrganizationPosition,
            OrganizationPositionSkill.organization_position_id == OrganizationPosition.id,
        )
        .where(
            OrganizationPositionSkill.status == "eligible",
            OrganizationSkill.status == "active",
            OrganizationSkill.validation_status == "passed",
            OrganizationSkill.capability_family == family,
            OrganizationPosition.status == "active",
            OrganizationPosition.suspended_at.is_(None),
            OrganizationPosition.department == work_item.department,
        )
    ).all()

    candidates = tuple(
        sorted(
            (
                SkillWorkCandidate(
                    position_id=position.id,
                    position_key=position.position_key,
                    skill_id=skill.id,
                    skill_key=skill.skill_key,
                    skill_version=skill.version,
                )
                for _binding, skill, position in rows
                if _is_candidate_compatible(skill, position)
            ),
            key=lambda candidate: (
                candidate.position_key,
                candidate.skill_key,
                candidate.skill_version,
                str(candidate.skill_id),
            ),
        )
    )
    return SkillWorkCandidateSet(
        work_item_id=work_item.id,
        capability_family=family,
        candidates=candidates,
        prerequisites_resolved=True,
    )

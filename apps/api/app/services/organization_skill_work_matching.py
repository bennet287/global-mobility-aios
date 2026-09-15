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


def _has_no_requirements(raw: str) -> bool:
    """Accept only a valid empty JSON string-list contract.

    Malformed, non-list, or non-string requirement contracts fail closed instead of
    being treated as prerequisite-free capability.
    """
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(value, list) and not value


def find_skill_work_candidates(
    session: Session,
    *,
    work_item: OrganizationalWorkItem,
    capability_family: str,
) -> SkillWorkCandidateSet:
    """Return capability candidates without authorizing assignment or execution.

    Phase 14.6 deliberately matches only canonical active positions, eligible exact
    position/skill bindings, and active validated skill versions. Skills declaring
    tool or permission requirements are excluded because the repository does not
    yet expose canonical server-side per-position entitlement truth. Consequently
    this result is diagnostic candidate discovery only and must not be consumed as
    an authorization, assignment, routing, credential, or execution decision.
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
                if _has_no_requirements(skill.tool_requirements_json)
                and _has_no_requirements(skill.permission_requirements_json)
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

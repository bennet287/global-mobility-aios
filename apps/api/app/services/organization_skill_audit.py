from __future__ import annotations

from typing import Any

from sqlmodel import Session

from app.models.domain import AuditLog
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill
from app.services.audit_log import record_audit


SKILL_AUDIT_SOURCE = "organization_skill_registry"


def skill_audit_state(skill: OrganizationSkill | None) -> dict[str, Any] | None:
    """Return bounded skill metadata suitable for durable audit evidence.

    Skill bodies, schemas, tool/permission requirement payloads and descriptions are
    intentionally excluded. Audit evidence should identify the governed transition
    without duplicating potentially sensitive or high-volume registry content.
    """
    if skill is None:
        return None
    return {
        "id": str(skill.id),
        "skill_key": skill.skill_key,
        "version": skill.version,
        "origin": skill.origin,
        "status": skill.status,
        "validation_status": skill.validation_status,
        "content_sha256": skill.content_sha256,
        "supersedes_skill_id": str(skill.supersedes_skill_id) if skill.supersedes_skill_id else None,
    }


def binding_audit_state(binding: OrganizationPositionSkill | None) -> dict[str, Any] | None:
    if binding is None:
        return None
    return {
        "id": str(binding.id),
        "organization_position_id": str(binding.organization_position_id),
        "organization_skill_id": str(binding.organization_skill_id),
        "status": binding.status,
        "assignment_reason": binding.assignment_reason,
        "assigned_by": binding.assigned_by,
    }


def record_skill_mutation(
    session: Session,
    *,
    action: str,
    actor: str,
    entity_type: str,
    entity_id: object,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    reason: str | None = None,
) -> AuditLog:
    """Stage a skill-registry audit record in the caller's transaction."""
    return record_audit(
        session,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        after_state=after_state,
        reason=reason,
        actor=actor,
        source=SKILL_AUDIT_SOURCE,
        commit=False,
    )

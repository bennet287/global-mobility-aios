from __future__ import annotations

import hashlib

import pytest

from app.models.domain import OrganizationPosition
from app.models.skill_registry import OrganizationSkill
from app.services.organization_skill_registry import (
    bind_skill_to_position,
    evaluate_skill_applicability,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _position() -> OrganizationPosition:
    return OrganizationPosition(
        position_key="regulatory.reviewer",
        title="Regulatory Reviewer",
        department="regulatory",
        authority_level="A3",
        created_by="pytest",
    )


def _skill() -> OrganizationSkill:
    return OrganizationSkill(
        skill_key="regulatory.source.review",
        name="Regulatory Source Review",
        capability_family="regulatory_evidence",
        description="Review certified regulatory evidence.",
        content_sha256=_sha("regulatory-source-review-v1"),
        compatible_departments_json='["regulatory"]',
        compatible_position_keys_json='["regulatory.reviewer"]',
        tool_requirements_json='["official_source_reader"]',
        permission_requirements_json='["regulatory.source.read"]',
        validation_status="passed",
        created_by="pytest",
    )


def test_applicability_requires_declared_tools_and_permissions_without_granting_them() -> None:
    position = _position()
    skill = _skill()

    missing = evaluate_skill_applicability(skill=skill, position=position)
    assert missing.applicable is False
    assert missing.missing_tools == ("official_source_reader",)
    assert missing.missing_permissions == ("regulatory.source.read",)
    assert "missing_tool_requirements" in missing.reasons
    assert "missing_permission_requirements" in missing.reasons
    assert position.authority_level == "A3"

    ready = evaluate_skill_applicability(
        skill=skill,
        position=position,
        available_tools=["official_source_reader"],
        available_permissions=["regulatory.source.read"],
    )
    assert ready.applicable is True
    assert ready.reasons == ()
    assert position.authority_level == "A3"


def test_applicability_is_fail_closed_for_unvalidated_incompatible_or_malformed_skill() -> None:
    position = _position()
    skill = _skill()
    skill.validation_status = "unvalidated"
    skill.compatible_departments_json = '["technical"]'

    result = evaluate_skill_applicability(
        skill=skill,
        position=position,
        available_tools=["official_source_reader"],
        available_permissions=["regulatory.source.read"],
    )
    assert result.applicable is False
    assert "skill_not_validated" in result.reasons
    assert "department_not_compatible" in result.reasons

    skill.compatible_departments_json = "not-json"
    with pytest.raises(ValueError, match="compatible_departments_json"):
        evaluate_skill_applicability(skill=skill, position=position)


def test_binding_service_is_idempotent_and_preserves_position_authority(db_session) -> None:
    position = _position()
    skill = _skill()
    db_session.add(position)
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(position)
    db_session.refresh(skill)

    first = bind_skill_to_position(
        db_session,
        position_id=position.id,
        skill_id=skill.id,
        assignment_reason="Required regulatory evidence capability.",
        actor="pytest",
    )
    db_session.commit()
    first_id = first.id

    second = bind_skill_to_position(
        db_session,
        position_id=position.id,
        skill_id=skill.id,
        assignment_reason="Repeated request must not duplicate the binding.",
        actor="pytest",
    )
    db_session.commit()

    assert second.id == first_id
    db_session.refresh(position)
    assert position.authority_level == "A3"

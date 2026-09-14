from __future__ import annotations

from sqlmodel import select

from app.models.domain import OrganizationPosition
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill
from app.services.organization_skill_lifecycle import (
    NativeSkillDefinition,
    create_native_skill,
    create_native_skill_version,
    deprecate_native_skill,
)
from app.services.organization_skill_registry import bind_skill_to_position


def _definition(*, description: str = "Review official regulatory evidence.") -> NativeSkillDefinition:
    return NativeSkillDefinition(
        skill_key="regulatory.source.review",
        name="Regulatory Source Review",
        capability_family="regulatory_evidence",
        description=description,
        compatible_departments=("regulatory",),
        compatible_position_keys=("regulatory.reviewer",),
        tool_requirements=("official_source_reader",),
        permission_requirements=("regulatory.source.read",),
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        evidence_expectations=("source_snapshot_id",),
    )


def test_native_skill_creation_is_deterministic_and_unvalidated(db_session) -> None:
    first = create_native_skill(db_session, definition=_definition(), actor="admin")
    db_session.commit()
    db_session.refresh(first)

    assert first.origin == "native"
    assert first.version == 1
    assert first.status == "active"
    assert first.validation_status == "unvalidated"
    assert len(first.content_sha256) == 64

    duplicate = _definition()
    try:
        create_native_skill(db_session, definition=duplicate, actor="admin")
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate skill_key must fail closed")


def test_new_version_supersedes_exact_active_version_without_inheriting_validation(db_session) -> None:
    first = create_native_skill(db_session, definition=_definition(), actor="admin")
    db_session.commit()
    db_session.refresh(first)
    first.validation_status = "passed"
    db_session.add(first)
    db_session.commit()

    successor = create_native_skill_version(
        db_session,
        skill_id=first.id,
        definition=_definition(description="Review official regulatory evidence with a revised contract."),
        actor="admin",
    )
    db_session.commit()
    db_session.refresh(first)
    db_session.refresh(successor)

    assert first.status == "superseded"
    assert successor.version == 2
    assert successor.supersedes_skill_id == first.id
    assert successor.status == "active"
    assert successor.validation_status == "unvalidated"
    assert successor.content_sha256 != first.content_sha256


def test_deprecation_disables_bindings_but_never_changes_position_authority(db_session) -> None:
    position = OrganizationPosition(
        position_key="regulatory.reviewer",
        title="Regulatory Reviewer",
        department="regulatory",
        authority_level="A3",
        created_by="pytest",
    )
    skill = create_native_skill(db_session, definition=_definition(), actor="admin")
    db_session.add(position)
    db_session.commit()
    db_session.refresh(position)
    db_session.refresh(skill)

    binding = bind_skill_to_position(
        db_session,
        position_id=position.id,
        skill_id=skill.id,
        assignment_reason="Role capability",
        actor="admin",
    )
    db_session.commit()
    db_session.refresh(binding)

    deprecated = deprecate_native_skill(db_session, skill_id=skill.id)
    db_session.commit()
    db_session.refresh(position)
    db_session.refresh(binding)

    assert deprecated.status == "deprecated"
    assert binding.status == "disabled"
    assert position.authority_level == "A3"
    assert len(db_session.exec(select(OrganizationPositionSkill)).all()) == 1


def test_versioning_rejects_skill_key_change(db_session) -> None:
    first = create_native_skill(db_session, definition=_definition(), actor="admin")
    db_session.commit()
    db_session.refresh(first)

    changed = NativeSkillDefinition(
        skill_key="regulatory.other",
        name="Regulatory Source Review",
        capability_family="regulatory_evidence",
        description="Changed key must fail.",
    )
    try:
        create_native_skill_version(db_session, skill_id=first.id, definition=changed, actor="admin")
    except ValueError as exc:
        assert "immutable" in str(exc)
    else:
        raise AssertionError("skill_key mutation must fail closed")

    db_session.refresh(first)
    assert first.status == "active"
    assert db_session.exec(select(OrganizationSkill)).all() == [first]

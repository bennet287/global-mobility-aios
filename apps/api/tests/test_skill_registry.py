from __future__ import annotations

import hashlib

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models.domain import OrganizationPosition
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_native_skill_registry_versions_capability_without_granting_authority(db_session) -> None:
    position = OrganizationPosition(
        position_key="regulatory.reviewer",
        title="Regulatory Reviewer",
        department="regulatory",
        authority_level="A3",
        contract_json='{"authority_source":"organization_position"}',
        created_by="pytest",
    )
    db_session.add(position)
    db_session.commit()
    db_session.refresh(position)

    skill_v1 = OrganizationSkill(
        skill_key="regulatory.official_source_review",
        name="Official Source Review",
        capability_family="regulatory_evidence",
        description="Review official-source evidence and produce a grounded evidence packet.",
        origin="native",
        version=1,
        content_sha256=_sha("official-source-review-v1"),
        compatible_departments_json='["regulatory"]',
        compatible_position_keys_json='["regulatory.reviewer"]',
        tool_requirements_json='["official_source_reader"]',
        permission_requirements_json='["regulatory.source.read"]',
        input_schema_json='{"type":"object"}',
        output_schema_json='{"type":"object"}',
        evidence_expectations_json='["source_snapshot_id"]',
        validation_status="passed",
        validation_summary_json='{"contract_tests":true}',
        created_by="pytest",
    )
    db_session.add(skill_v1)
    db_session.commit()
    db_session.refresh(skill_v1)

    binding = OrganizationPositionSkill(
        organization_position_id=position.id,
        organization_skill_id=skill_v1.id,
        assignment_reason="Native capability required by the regulatory reviewer position.",
        assigned_by="pytest",
    )
    db_session.add(binding)
    db_session.commit()

    db_session.refresh(position)
    assert position.authority_level == "A3"
    assert "authority" not in OrganizationPositionSkill.model_fields
    assert "permission" not in OrganizationPositionSkill.model_fields
    assert "credential" not in OrganizationPositionSkill.model_fields
    assert skill_v1.permission_requirements_json == '["regulatory.source.read"]'

    duplicate_active = OrganizationSkill(
        skill_key=skill_v1.skill_key,
        name=skill_v1.name,
        capability_family=skill_v1.capability_family,
        description="Second active version must fail until the previous version is superseded.",
        origin="native",
        version=2,
        content_sha256=_sha("official-source-review-v2-premature"),
        created_by="pytest",
    )
    db_session.add(duplicate_active)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    persisted_v1 = db_session.get(OrganizationSkill, skill_v1.id)
    persisted_v1.status = "superseded"
    db_session.add(persisted_v1)
    db_session.commit()

    skill_v2 = OrganizationSkill(
        skill_key=skill_v1.skill_key,
        name=skill_v1.name,
        capability_family=skill_v1.capability_family,
        description="Versioned improvement that preserves the v1 provenance chain.",
        origin="native",
        version=2,
        content_sha256=_sha("official-source-review-v2"),
        supersedes_skill_id=skill_v1.id,
        validation_status="passed",
        created_by="pytest",
    )
    db_session.add(skill_v2)
    db_session.commit()
    db_session.refresh(skill_v2)

    active = db_session.exec(
        select(OrganizationSkill).where(
            OrganizationSkill.skill_key == skill_v1.skill_key,
            OrganizationSkill.status == "active",
        )
    ).all()
    assert [item.id for item in active] == [skill_v2.id]
    assert skill_v2.supersedes_skill_id == skill_v1.id
    assert binding.organization_skill_id == skill_v1.id


def test_position_skill_binding_is_exact_version_and_unique(db_session) -> None:
    position = OrganizationPosition(
        position_key="technical.backend",
        title="Backend Engineer",
        department="technical",
        authority_level="A2",
        created_by="pytest",
    )
    skill = OrganizationSkill(
        skill_key="technical.backend.testing",
        name="Backend Contract Testing",
        capability_family="software_testing",
        description="Run backend contract tests with explicit validation evidence.",
        origin="native",
        version=1,
        content_sha256=_sha("backend-contract-testing-v1"),
        created_by="pytest",
    )
    db_session.add(position)
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(position)
    db_session.refresh(skill)

    first = OrganizationPositionSkill(
        organization_position_id=position.id,
        organization_skill_id=skill.id,
        assignment_reason="Position capability baseline.",
        assigned_by="pytest",
    )
    db_session.add(first)
    db_session.commit()

    duplicate = OrganizationPositionSkill(
        organization_position_id=position.id,
        organization_skill_id=skill.id,
        assignment_reason="Duplicate binding must be rejected.",
        assigned_by="pytest",
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    rows = db_session.exec(select(OrganizationPositionSkill)).all()
    assert len(rows) == 1
    assert rows[0].organization_position_id == position.id
    assert rows[0].organization_skill_id == skill.id

from __future__ import annotations

import hashlib
import json

import pytest
from sqlmodel import select

from app.models.domain import OrganizationPosition
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill
from app.services.organization_skill_registry import (
    NATIVE_SKILL_VALIDATOR,
    validate_native_skill_contract,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _native_skill() -> OrganizationSkill:
    return OrganizationSkill(
        skill_key="regulatory.source.validation",
        name="Regulatory Source Validation",
        capability_family="regulatory_evidence",
        description="Validate structured regulatory source evidence.",
        origin="native",
        content_sha256=_sha("regulatory-source-validation-v1"),
        compatible_departments_json='["regulatory"]',
        compatible_position_keys_json='["regulatory.reviewer"]',
        tool_requirements_json='["official_source_reader"]',
        permission_requirements_json='["regulatory.source.read"]',
        input_schema_json='{"type":"object"}',
        output_schema_json='{"type":"object"}',
        evidence_expectations_json='["source_snapshot_id"]',
        validation_status="unvalidated",
        created_by="pytest",
    )


def test_native_skill_validation_persists_deterministic_contract_summary(db_session) -> None:
    skill = _native_skill()
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)

    first = validate_native_skill_contract(db_session, skill_id=skill.id)
    db_session.commit()
    db_session.refresh(skill)

    summary = json.loads(skill.validation_summary_json)
    assert first.passed is True
    assert first.validator == NATIVE_SKILL_VALIDATOR
    assert first.failures == ()
    assert skill.validation_status == "passed"
    assert summary["validator"] == NATIVE_SKILL_VALIDATOR
    assert summary["content_sha256"] == skill.content_sha256
    assert summary["failures"] == []
    assert "content_sha256:valid" in summary["checks"]
    first_summary = skill.validation_summary_json

    second = validate_native_skill_contract(db_session, skill_id=skill.id)
    db_session.commit()
    db_session.refresh(skill)

    assert second.passed is True
    assert skill.validation_summary_json == first_summary


def test_native_skill_validation_fails_closed_for_malformed_contract(db_session) -> None:
    skill = _native_skill()
    skill.content_sha256 = "z" * 64
    skill.tool_requirements_json = "not-json"
    skill.input_schema_json = "[]"
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)

    result = validate_native_skill_contract(db_session, skill_id=skill.id)
    db_session.commit()
    db_session.refresh(skill)

    assert result.passed is False
    assert skill.validation_status == "failed"
    assert "content_sha256:not_hex" in result.failures
    assert "tool_requirements_json:invalid" in result.failures
    assert "input_schema_json:invalid" in result.failures
    summary = json.loads(skill.validation_summary_json)
    assert summary["failures"] == sorted(result.failures)


@pytest.mark.parametrize("origin", ["imported", "learned"])
def test_phase_14_3_rejects_non_native_skill_validation(db_session, origin: str) -> None:
    skill = _native_skill()
    skill.skill_key = f"regulatory.{origin}.candidate"
    skill.origin = origin
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)

    with pytest.raises(ValueError, match="native skills only"):
        validate_native_skill_contract(db_session, skill_id=skill.id)

    db_session.refresh(skill)
    assert skill.validation_status == "unvalidated"


def test_validation_never_changes_authority_or_creates_binding(db_session) -> None:
    position = OrganizationPosition(
        position_key="regulatory.reviewer",
        title="Regulatory Reviewer",
        department="regulatory",
        authority_level="A3",
        created_by="pytest",
    )
    skill = _native_skill()
    db_session.add(position)
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(position)
    db_session.refresh(skill)

    result = validate_native_skill_contract(db_session, skill_id=skill.id)
    db_session.commit()
    db_session.refresh(position)

    assert result.passed is True
    assert position.authority_level == "A3"
    bindings = db_session.exec(select(OrganizationPositionSkill)).all()
    assert bindings == []

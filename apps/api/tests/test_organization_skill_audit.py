from __future__ import annotations

import json

from sqlmodel import select

from app.models.domain import AuditLog
from app.models.skill_registry import OrganizationSkill
from app.services.organization_skill_audit import (
    SKILL_AUDIT_SOURCE,
    record_skill_mutation,
    skill_audit_state,
)


def _skill() -> OrganizationSkill:
    return OrganizationSkill(
        skill_key="regulatory.source.review",
        name="Regulatory Source Review",
        capability_family="regulatory_evidence",
        description="Sensitive implementation detail that must not be copied to audit evidence.",
        origin="native",
        version=1,
        content_sha256="a" * 64,
        tool_requirements_json='["official_source_reader"]',
        permission_requirements_json='["regulatory.source.read"]',
        status="active",
        validation_status="unvalidated",
        created_by="admin",
    )


def test_skill_audit_state_is_bounded_and_excludes_contract_payloads() -> None:
    skill = _skill()
    state = skill_audit_state(skill)

    assert state is not None
    assert state["skill_key"] == "regulatory.source.review"
    assert state["content_sha256"] == "a" * 64
    assert "description" not in state
    assert "tool_requirements_json" not in state
    assert "permission_requirements_json" not in state
    assert "input_schema_json" not in state
    assert "output_schema_json" not in state


def test_skill_mutation_audit_commits_with_canonical_actor_and_source(db_session) -> None:
    skill = _skill()
    db_session.add(skill)
    record_skill_mutation(
        db_session,
        action="organization_skill.created",
        actor="registry-admin",
        entity_type="organization_skill",
        entity_id=skill.id,
        after_state=skill_audit_state(skill),
        reason="pytest governed mutation",
    )
    db_session.commit()

    audit = db_session.exec(select(AuditLog)).one()
    assert audit.actor == "registry-admin"
    assert audit.action == "organization_skill.created"
    assert audit.entity_type == "organization_skill"
    assert audit.entity_id == str(skill.id)
    assert audit.source == SKILL_AUDIT_SOURCE
    assert audit.reason == "pytest governed mutation"

    state = json.loads(audit.after_state_json or "{}")
    assert state["skill_key"] == skill.skill_key
    assert state["version"] == 1
    assert "description" not in state


def test_skill_mutation_audit_rolls_back_with_governed_transaction(db_session) -> None:
    skill = _skill()
    db_session.add(skill)
    record_skill_mutation(
        db_session,
        action="organization_skill.created",
        actor="registry-admin",
        entity_type="organization_skill",
        entity_id=skill.id,
        after_state=skill_audit_state(skill),
    )
    db_session.rollback()

    assert db_session.exec(select(AuditLog)).all() == []
    assert db_session.exec(select(OrganizationSkill)).all() == []

from __future__ import annotations

import hashlib

import pytest

from app.models.domain import OrganizationPosition, OrganizationalWorkItem
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill
from app.services.organization_command import AuthorityDenied, OrganizationCommandContext
from app.services.organization_skill_assignment import (
    SkillAssignmentDenied,
    assign_skill_candidate_to_work,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _context(*, actor_type: str = "human", role: str = "admin") -> OrganizationCommandContext:
    actor_id = "pytest-admin" if actor_type == "human" else "regulatory_reviewer"
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id=actor_id,
        actor_type=actor_type,
        authenticated_user_id="pytest-admin" if actor_type == "human" else "system",
        role=role,
    )


def _work() -> OrganizationalWorkItem:
    return OrganizationalWorkItem(
        idempotency_key="phase-14-7-work",
        idempotency_fingerprint=_sha("phase-14-7-work"),
        tenant_key="default",
        title="Review regulatory evidence",
        objective="Assign a human-approved capable position.",
        department="regulatory",
        authority_level="L2",
        assigned_position_key="unassigned",
        requested_by_type="human",
        requested_by_id="pytest-admin",
        created_by="pytest-admin",
    )


def _position(key: str) -> OrganizationPosition:
    return OrganizationPosition(
        position_key=key,
        title="Regulatory Reviewer",
        department="regulatory",
        authority_level="A3",
        created_by="pytest",
    )


def _skill(*, requirements: str = "[]") -> OrganizationSkill:
    return OrganizationSkill(
        skill_key="regulatory.source.review",
        name="Regulatory source review",
        capability_family="regulatory_evidence",
        description="Review official-source evidence.",
        content_sha256=_sha("regulatory.source.review"),
        validation_status="passed",
        status="active",
        tool_requirements_json=requirements,
        created_by="pytest",
    )


def _seed_candidate(db_session, *, requirements: str = "[]"):
    work = _work()
    position = _position("regulatory_reviewer")
    skill = _skill(requirements=requirements)
    db_session.add_all([work, position, skill])
    db_session.flush()
    db_session.add(
        OrganizationPositionSkill(
            organization_position_id=position.id,
            organization_skill_id=skill.id,
            status="eligible",
            assignment_reason="validated capability",
            assigned_by="pytest",
        )
    )
    db_session.commit()
    return work, position


def test_human_admin_can_assign_exact_validated_skill_candidate(db_session) -> None:
    work, position = _seed_candidate(db_session)

    assigned = assign_skill_candidate_to_work(
        db_session,
        _context(),
        work_item_id=work.id,
        assigned_position_key=position.position_key,
        capability_family="regulatory_evidence",
        reason="Human administrator approved the capability match.",
    )

    assert assigned.assigned_position_key == position.position_key
    assert assigned.authority_level == "L2"
    db_session.refresh(position)
    assert position.authority_level == "A3"


def test_agent_cannot_promote_skill_match_into_assignment(db_session) -> None:
    work, position = _seed_candidate(db_session)

    with pytest.raises(AuthorityDenied):
        assign_skill_candidate_to_work(
            db_session,
            _context(actor_type="agent", role="operator"),
            work_item_id=work.id,
            assigned_position_key=position.position_key,
            capability_family="regulatory_evidence",
            reason="Agent selected itself.",
        )

    db_session.refresh(work)
    assert work.assigned_position_key == "unassigned"


def test_non_candidate_position_fails_closed_without_mutation(db_session) -> None:
    work, _position_row = _seed_candidate(db_session)

    with pytest.raises(SkillAssignmentDenied, match="not an eligible validated skill candidate"):
        assign_skill_candidate_to_work(
            db_session,
            _context(),
            work_item_id=work.id,
            assigned_position_key="another_position",
            capability_family="regulatory_evidence",
            reason="Attempted assignment.",
        )

    db_session.refresh(work)
    assert work.assigned_position_key == "unassigned"


def test_unresolved_skill_prerequisites_cannot_be_human_overridden_by_this_gate(db_session) -> None:
    work, position = _seed_candidate(db_session, requirements='["official_source_browser"]')

    with pytest.raises(SkillAssignmentDenied):
        assign_skill_candidate_to_work(
            db_session,
            _context(),
            work_item_id=work.id,
            assigned_position_key=position.position_key,
            capability_family="regulatory_evidence",
            reason="Human approval cannot fabricate tool entitlement.",
        )

    db_session.refresh(work)
    assert work.assigned_position_key == "unassigned"


def test_assignment_requires_nonblank_reason(db_session) -> None:
    work, position = _seed_candidate(db_session)

    with pytest.raises(SkillAssignmentDenied, match="assignment reason is required"):
        assign_skill_candidate_to_work(
            db_session,
            _context(),
            work_item_id=work.id,
            assigned_position_key=position.position_key,
            capability_family="regulatory_evidence",
            reason="   ",
        )

    db_session.refresh(work)
    assert work.assigned_position_key == "unassigned"

from __future__ import annotations

import hashlib

from app.models.domain import OrganizationPosition, OrganizationalWorkItem
from app.models.skill_registry import OrganizationPositionSkill, OrganizationSkill
from app.services.organization_skill_work_matching import find_skill_work_candidates


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _position(*, key: str, department: str = "regulatory") -> OrganizationPosition:
    return OrganizationPosition(
        position_key=key,
        title=key.replace("_", " ").title(),
        department=department,
        authority_level="A3",
        created_by="pytest",
    )


def _skill(*, key: str, family: str, status: str = "active", validation: str = "passed") -> OrganizationSkill:
    return OrganizationSkill(
        skill_key=key,
        name=key,
        capability_family=family,
        description="Diagnostic candidate capability.",
        content_sha256=_sha(key),
        validation_status=validation,
        status=status,
        created_by="pytest",
    )


def _work() -> OrganizationalWorkItem:
    return OrganizationalWorkItem(
        idempotency_key="phase-14-6-work",
        idempotency_fingerprint=_sha("phase-14-6-work"),
        tenant_key="default",
        title="Review regulatory source evidence",
        objective="Identify positions with the required capability.",
        department="regulatory",
        authority_level="L2",
        assigned_position_key="unassigned",
        requested_by_type="human",
        requested_by_id="pytest",
        created_by="pytest",
    )


def test_matching_returns_only_active_validated_eligible_same_department_candidates(db_session) -> None:
    work = _work()
    eligible_position = _position(key="regulatory_reviewer")
    wrong_department = _position(key="technical_reviewer", department="technology")
    eligible_skill = _skill(key="regulatory.source.review", family="regulatory_evidence")
    unvalidated_skill = _skill(
        key="regulatory.source.draft",
        family="regulatory_evidence",
        validation="unvalidated",
    )
    db_session.add_all([work, eligible_position, wrong_department, eligible_skill, unvalidated_skill])
    db_session.flush()
    db_session.add_all(
        [
            OrganizationPositionSkill(
                organization_position_id=eligible_position.id,
                organization_skill_id=eligible_skill.id,
                status="eligible",
                assignment_reason="validated capability",
                assigned_by="pytest",
            ),
            OrganizationPositionSkill(
                organization_position_id=wrong_department.id,
                organization_skill_id=eligible_skill.id,
                status="eligible",
                assignment_reason="wrong department",
                assigned_by="pytest",
            ),
            OrganizationPositionSkill(
                organization_position_id=eligible_position.id,
                organization_skill_id=unvalidated_skill.id,
                status="eligible",
                assignment_reason="unvalidated capability",
                assigned_by="pytest",
            ),
        ]
    )
    db_session.commit()

    result = find_skill_work_candidates(
        db_session,
        work_item=work,
        capability_family="regulatory_evidence",
    )

    assert [(candidate.position_key, candidate.skill_key) for candidate in result.candidates] == [
        ("regulatory_reviewer", "regulatory.source.review")
    ]
    assert result.diagnostic_only is True
    assert result.authority_granted is False
    assert result.permissions_granted is False
    assert result.credentials_granted is False
    assert result.autonomy_granted is False
    assert result.assignment_granted is False
    assert result.execution_granted is False


def test_matching_does_not_mutate_work_assignment_or_position_authority(db_session) -> None:
    work = _work()
    position = _position(key="regulatory_reviewer")
    skill = _skill(key="regulatory.source.review", family="regulatory_evidence")
    db_session.add_all([work, position, skill])
    db_session.flush()
    db_session.add(
        OrganizationPositionSkill(
            organization_position_id=position.id,
            organization_skill_id=skill.id,
            status="eligible",
            assignment_reason="candidate only",
            assigned_by="pytest",
        )
    )
    db_session.commit()

    original_assignment = work.assigned_position_key
    original_authority = position.authority_level
    result = find_skill_work_candidates(
        db_session,
        work_item=work,
        capability_family="regulatory_evidence",
    )

    assert len(result.candidates) == 1
    db_session.refresh(work)
    db_session.refresh(position)
    assert work.assigned_position_key == original_assignment
    assert position.authority_level == original_authority


def test_matching_requires_explicit_capability_family(db_session) -> None:
    work = _work()
    db_session.add(work)
    db_session.commit()

    try:
        find_skill_work_candidates(db_session, work_item=work, capability_family="  ")
    except ValueError as exc:
        assert str(exc) == "capability_family is required"
    else:
        raise AssertionError("blank capability family must fail closed")

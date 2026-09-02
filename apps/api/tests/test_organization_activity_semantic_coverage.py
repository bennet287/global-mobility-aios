from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func
from sqlmodel import Session, create_engine, select

from app.models.domain import (
    AuditLog,
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationHumanAction,
    OrganizationHumanActionType,
    OrganizationWorkItemDependency,
    OrganizationalWorkItem,
)
from app.services.organization_activity import stage_activity
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_contribution import (
    append_contribution_correction,
    create_contribution,
    validate_authoritative_outcome,
)
from app.services.organization_decision import (
    create_executive_decision,
    record_executive_decision_outcome,
)
from app.services.organization_human_action import (
    acknowledge_human_action_request,
    assign_human_action_request,
    complete_human_action_request,
    create_human_action_request,
    decline_human_action_request,
    start_human_action_request,
)
from app.services.organization_work import (
    complete_work_item,
    create_dependency,
    create_work_item,
    open_blocker,
    resolve_blocker,
    start_work_item,
    waive_dependency,
)


NOW = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)


def _context(
    *,
    tenant: str = "default",
    actor: str = "semantic-owner",
    department: str = "operations",
) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant,
        actor_id=actor,
        actor_type="human",
        authenticated_user_id=actor,
        role="admin",
        department=department,
        position_key="board",
        authority_level="L4",
        correlation_key="e2-semantic-coverage",
    )


def _work(
    session: Session,
    context: OrganizationCommandContext,
    key: str,
    *,
    department: str = "operations",
) -> OrganizationalWorkItem:
    return create_work_item(
        session,
        context,
        idempotency_key=key,
        title=key,
        objective="Exercise E2 semantic Activity coverage",
        department=department,
        authority_level="L2",
        assigned_position_key="coo",
    )


def _approved_decision(
    session: Session,
    context: OrganizationCommandContext,
    key: str,
):
    decision = create_executive_decision(
        session,
        context,
        decision_key=key,
        decision_type="operational",
        authority_level="L3",
        requested_by_position="coo",
        decision_owner_position="ceo",
        title="Bounded governed decision",
        question="Approve this bounded decision?",
        recommendation="Approve",
    )
    return record_executive_decision_outcome(
        session,
        context,
        decision_id=decision.id,
        outcome="approved",
        reason="Authenticated authority approved the bounded decision.",
    )


def _source_activities(
    session: Session,
    source_type: str,
    source_id: object,
) -> list[OrganizationActivity]:
    return list(
        session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.source_object_type == source_type,
                OrganizationActivity.source_object_id == str(source_id),
            )
            .order_by(OrganizationActivity.stream_sequence)
        ).all()
    )


def test_stage_activity_is_caller_owned_and_rollback_safe(db_session: Session) -> None:
    context = _context()
    activities_before = db_session.exec(select(func.count()).select_from(OrganizationActivity)).one()
    audits_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()

    staged = stage_activity(
        db_session,
        context,
        activity_key="e2-staged-only",
        stream_key="e2-stage-contract",
        activity_class="operational",
        activity_type="organization.e2.stage.contract.v1",
        title="E2 staged activity",
        summary="This row must remain caller-owned until the surrounding transaction commits.",
        source_object_type="e2_contract",
        source_object_id="staged-only",
        occurred_at=NOW,
    )
    assert staged.id is not None
    assert db_session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before + 1
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before + 1

    db_session.rollback()
    assert db_session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before


def test_work_lifecycle_emits_ordered_semantic_activity_without_contribution(db_session: Session) -> None:
    context = _context()
    work = _work(db_session, context, "e2-work-lifecycle")
    start_work_item(db_session, context, work_item_id=work.id, reason="Begin governed work")
    count_after_start = len(_source_activities(db_session, "organizational_work_item", work.id))
    start_work_item(db_session, context, work_item_id=work.id, reason="Replay begin")
    assert len(_source_activities(db_session, "organizational_work_item", work.id)) == count_after_start
    complete_work_item(db_session, context, work_item_id=work.id, reason="Governed work completed")

    activities = _source_activities(db_session, "organizational_work_item", work.id)
    assert [row.activity_type for row in activities] == [
        "organization.work.created.v1",
        "organization.work.status.running.v1",
        "organization.work.status.completed.v1",
    ]
    assert [row.stream_sequence for row in activities] == [1, 2, 3]
    assert len({row.source_object_version for row in activities}) == 3
    assert all(row.activity_class is OrganizationActivityClass.work for row in activities)
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0


def test_activity_adapter_failure_rolls_back_work_transition_and_source_audit(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    work = _work(db_session, context, "e2-work-rollback")
    activities_before = db_session.exec(select(func.count()).select_from(OrganizationActivity)).one()
    audits_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()

    def fail_activity(*_args, **_kwargs):
        raise RuntimeError("simulated semantic Activity failure")

    monkeypatch.setattr(
        "app.services.organization_work.stage_work_item_status_activity",
        fail_activity,
    )
    with pytest.raises(RuntimeError, match="semantic Activity failure"):
        start_work_item(db_session, context, work_item_id=work.id, reason="Must roll back")

    db_session.refresh(work)
    assert work.status == "queued"
    assert db_session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before


def test_activity_audit_failure_rolls_back_source_transition_and_staged_rows(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context()
    work = _work(db_session, context, "e2-activity-audit-rollback")
    activities_before = db_session.exec(select(func.count()).select_from(OrganizationActivity)).one()
    audits_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()

    from app.services import organization_command

    original_record_audit = organization_command.record_audit

    def fail_activity_audit(*args, **kwargs):  # type: ignore[no-untyped-def]
        if kwargs.get("action") == "organization.activity.append":
            raise RuntimeError("simulated Activity audit storage failure")
        return original_record_audit(*args, **kwargs)

    monkeypatch.setattr(organization_command, "record_audit", fail_activity_audit)
    with pytest.raises(RuntimeError, match="Activity audit storage"):
        start_work_item(db_session, context, work_item_id=work.id, reason="Must roll back")

    db_session.refresh(work)
    assert work.status == "queued"
    assert db_session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before


def test_blocker_lifecycle_activity_uses_linked_work_department(db_session: Session) -> None:
    context = _context(department="executive")
    work = _work(db_session, context, "e2-blocker-work", department="compliance")
    blocker = open_blocker(
        db_session,
        context,
        blocker_key="e2-blocker",
        blocker_type="evidence",
        severity="high",
        title="Evidence blocker",
        description="A governed blocker fixture.",
        work_item_id=work.id,
    )
    resolve_blocker(db_session, context, blocker_id=blocker.id, reason="Evidence verified")

    activities = _source_activities(db_session, "organization_blocker", blocker.id)
    assert [row.activity_type for row in activities] == [
        "organization.blocker.opened.v1",
        "organization.blocker.status.resolved.v1",
    ]
    assert [row.stream_sequence for row in activities] == [1, 2]
    assert all(row.department == "compliance" for row in activities)


def test_decision_lifecycle_emits_activity_but_not_automatic_contribution(db_session: Session) -> None:
    context = _context()
    decision = _approved_decision(db_session, context, "e2-decision")
    activities = _source_activities(db_session, "executive_decision", decision.id)
    assert [row.activity_type for row in activities] == [
        "organization.decision.created.v1",
        "organization.decision.status.approved.v1",
    ]
    assert [row.stream_sequence for row in activities] == [1, 2]
    assert all(row.activity_class is OrganizationActivityClass.decision for row in activities)
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0


def test_human_request_completion_orders_action_then_request_completion(db_session: Session) -> None:
    context = _context()
    work = _work(db_session, context, "e2-human-work")
    request = create_human_action_request(
        db_session,
        context,
        request_key="e2-human-request",
        request_type="review",
        title="Review governed work",
        instructions="Review the bounded fixture.",
        required_role="admin",
        assigned_human_id=context.actor_id,
        work_item_id=work.id,
    )
    acknowledge_human_action_request(db_session, context, request_id=request.id)
    start_human_action_request(db_session, context, request_id=request.id)
    completed, action = complete_human_action_request(
        db_session,
        context,
        request_id=request.id,
        action_key="e2-human-action",
        action_type=OrganizationHumanActionType.reviewed,
        outcome="Reviewed",
        occurred_at=NOW,
        reason="Authenticated review",
    )
    assert completed.status.value == "completed"

    request_activity = _source_activities(
        db_session,
        "organization_human_action_request",
        request.id,
    )
    action_activity = _source_activities(
        db_session,
        "organization_human_action",
        action.id,
    )
    assert [row.activity_type for row in request_activity] == [
        "organization.human_request.created.v1",
        "organization.human_request.status.acknowledged.v1",
        "organization.human_request.status.in_progress.v1",
        "organization.human_request.status.completed.v1",
    ]
    assert len(action_activity) == 1
    assert action_activity[0].activity_type == "organization.human_action.reviewed.v1"
    assert action_activity[0].activity_stream_id == request_activity[-1].activity_stream_id
    assert action_activity[0].stream_sequence == 4
    assert request_activity[-1].stream_sequence == 5
    assert request_activity[-1].causation_activity_id == action_activity[0].id
    assert db_session.exec(select(func.count()).select_from(OrganizationHumanAction)).one() == 1
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0


def test_human_request_assignment_and_decline_are_semantic_activity(db_session: Session) -> None:
    context = _context()
    work = _work(db_session, context, "e2-human-decline-work")
    request = create_human_action_request(
        db_session,
        context,
        request_key="e2-human-decline",
        request_type="approval",
        title="Approval required",
        instructions="Review and decide.",
        required_role="admin",
        work_item_id=work.id,
    )
    assign_human_action_request(
        db_session,
        context,
        request_id=request.id,
        assigned_human_id=context.actor_id,
        reason="Assign owner",
    )
    decline_human_action_request(
        db_session,
        context,
        request_id=request.id,
        outcome="Declined after review",
    )
    activities = _source_activities(
        db_session,
        "organization_human_action_request",
        request.id,
    )
    assert [row.activity_type for row in activities] == [
        "organization.human_request.created.v1",
        "organization.human_request.assigned.v1",
        "organization.human_request.status.declined.v1",
    ]
    assert [row.stream_sequence for row in activities] == [1, 2, 3]


def test_dependency_lifecycle_has_curated_work_activity(db_session: Session) -> None:
    context = _context()
    first = _work(db_session, context, "e2-dependency-first")
    second = _work(db_session, context, "e2-dependency-second")
    dependency = create_dependency(
        db_session,
        context,
        dependency_key="e2-dependency",
        work_item_id=first.id,
        depends_on_work_item_id=second.id,
        dependency_type="requires",
    )
    waive_dependency(
        db_session,
        context,
        dependency_id=dependency.id,
        reason="Board-authorized bounded waiver",
    )
    activities = _source_activities(
        db_session,
        "organization_work_item_dependency",
        dependency.id,
    )
    assert [row.activity_type for row in activities] == [
        "organization.dependency.created.v1",
        "organization.dependency.status.waived.v1",
    ]
    assert all(row.activity_class is OrganizationActivityClass.work for row in activities)
    db_session.refresh(dependency)
    assert dependency.status.value == "waived"


def test_contribution_outcome_and_correction_append_activity_without_changing_outcome_policy(
    db_session: Session,
) -> None:
    context = _context()
    decision = _approved_decision(db_session, context, "e2-contribution-decision")
    descriptor = validate_authoritative_outcome(
        db_session,
        context,
        source_type="executive_decision",
        source_id=decision.id,
        source_version=decision.record_fingerprint,
        outcome_type="governed_approval",
        verification_basis="Authenticated Board decision",
    )
    original = create_contribution(
        db_session,
        context,
        contribution_key="e2-contribution",
        descriptor=descriptor,
        contribution_type="governed_outcome",
        title="Governed outcome",
        outcome_summary="A bounded organizational outcome was recorded.",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind=OrganizationContributionImpactKind.state_change,
        effective_at=NOW,
    )
    correction = append_contribution_correction(
        db_session,
        context,
        contribution_key="e2-contribution-retraction",
        original_contribution_id=original.id,
        descriptor=descriptor,
        record_kind=OrganizationContributionRecordKind.retraction,
        title="Retracted outcome",
        outcome_summary="The prior bounded outcome is no longer active.",
        effective_at=NOW,
        retraction_reason="Board-authorized correction",
    )

    original_activity = _source_activities(
        db_session,
        "organization_contribution",
        original.id,
    )
    correction_activity = _source_activities(
        db_session,
        "organization_contribution",
        correction.id,
    )
    assert len(original_activity) == len(correction_activity) == 1
    assert original_activity[0].activity_type == "organization.contribution.outcome.v1"
    assert correction_activity[0].activity_type == "organization.contribution.retraction.v1"
    assert original_activity[0].activity_stream_id == correction_activity[0].activity_stream_id
    assert original_activity[0].stream_sequence == 1
    assert correction_activity[0].stream_sequence == 2
    assert correction.supersedes_contribution_id == original.id
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 2


def test_postgresql_work_semantic_activity_transaction_contract() -> None:
    database_url = os.getenv("ORGANIZATION_POSTGRES_TEST_URL")
    if not database_url:
        pytest.skip("ORGANIZATION_POSTGRES_TEST_URL is not configured")
    engine = create_engine(database_url)
    connection = engine.connect()
    outer = connection.begin()
    try:
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            context = _context(actor="e2-pg-owner")
            suffix = uuid4().hex
            work = _work(session, context, f"e2-pg-work-{suffix}")
            start_work_item(session, context, work_item_id=work.id, reason="Start")
            complete_work_item(session, context, work_item_id=work.id, reason="Complete")
            activities = _source_activities(session, "organizational_work_item", work.id)
            assert [row.activity_type for row in activities] == [
                "organization.work.created.v1",
                "organization.work.status.running.v1",
                "organization.work.status.completed.v1",
            ]
            assert [row.stream_sequence for row in activities] == [1, 2, 3]
            assert session.exec(
                select(func.count()).select_from(OrganizationContribution).where(
                    OrganizationContribution.work_item_id == work.id
                )
            ).one() == 0
    finally:
        outer.rollback()
        connection.close()
        engine.dispose()

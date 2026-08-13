from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import event, func
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.core.db import register_models
from app.models.domain import (
    AgentRun,
    AuditLog,
    ExecutiveDecision,
    Lead,
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationActorType,
    OrganizationBlocker,
    OrganizationBlockerStatus,
    OrganizationBlockerType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationDependencyStatus,
    OrganizationDependencyType,
    OrganizationHumanAction,
    OrganizationHumanActionRequestStatus,
    OrganizationHumanActionRequestType,
    OrganizationHumanActionType,
    OrganizationRecordReference,
    OrganizationReferenceRole,
    OrganizationReferenceTargetType,
    OrganizationWorkItemDependency,
    OrganizationalWorkItem,
)
from app.services import organization_command
from app.services.organization_activity import append_activity
from app.services.organization_command import (
    AuthorityDenied,
    ContributionSourceRejected,
    DependencyConflict,
    IdempotencyConflict,
    InvalidHumanActor,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    TenantMismatch,
    canonical_fingerprint,
)
from app.services.organization_contribution import (
    append_contribution_correction,
    create_contribution,
    validate_authoritative_outcome,
)
from app.services.organization_decision import (
    create_executive_decision,
    record_executive_decision_outcome,
    supersede_executive_decision,
)
from app.services.organization_human_action import (
    acknowledge_human_action_request,
    complete_human_action_request,
    create_human_action_request,
    start_human_action_request,
)
from app.services.organization_reference import create_record_reference
from app.services.organization_work import (
    block_work_item,
    complete_work_item,
    create_dependency,
    create_work_item,
    open_blocker,
    mitigate_blocker,
    resolve_blocker,
    satisfy_dependency,
    start_work_item,
    waive_blocker,
    waive_dependency,
)


NOW = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)


@pytest.fixture()
def organization_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    register_models()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="human-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="human-owner",
        role="admin",
        department="operations",
        position_key="board",
        authority_level="L4",
        correlation_key="corr-13161b",
    )


@pytest.fixture()
def agent_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="coo-agent",
        actor_type=OrganizationActorType.agent,
        authenticated_user_id="service-account",
        role="operator",
        department="operations",
        position_key="coo",
        authority_level="L2",
    )


def _work(session: Session, context: OrganizationCommandContext, key: str, **changes) -> OrganizationalWorkItem:
    values = {
        "idempotency_key": key,
        "title": key,
        "objective": "Exercise the durable command layer",
        "department": "operations",
        "authority_level": "L2",
        "assigned_position_key": "coo",
    }
    values.update(changes)
    return create_work_item(session, context, **values)


def _approved_decision(
    session: Session,
    context: OrganizationCommandContext,
    key: str = "decision-source",
) -> ExecutiveDecision:
    decision = create_executive_decision(
        session,
        context,
        decision_key=key,
        decision_type="operational",
        authority_level="L3",
        requested_by_position="coo",
        decision_owner_position="ceo",
        title="Governed outcome",
        question="Approve the bounded outcome?",
        recommendation="Approve",
    )
    return record_executive_decision_outcome(
        session,
        context,
        decision_id=decision.id,
        outcome="approved",
        reason="Human owner approved the governed outcome.",
    )


def _contribution(
    session: Session,
    context: OrganizationCommandContext,
    key: str = "contribution-1",
) -> OrganizationContribution:
    decision = _approved_decision(session, context, f"{key}-decision")
    descriptor = validate_authoritative_outcome(
        session,
        context,
        source_type="executive_decision",
        source_id=decision.id,
        source_version=decision.record_fingerprint,
        outcome_type="governed_approval",
        verification_basis="Authenticated Board decision",
    )
    return create_contribution(
        session,
        context,
        contribution_key=key,
        descriptor=descriptor,
        contribution_type="governed_outcome",
        title="Approved governed outcome",
        outcome_summary="A human-authorized organizational outcome was recorded.",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind=OrganizationContributionImpactKind.state_change,
        effective_at=NOW,
    )


def test_canonical_fingerprint_is_deterministic_and_excludes_runtime_time() -> None:
    left = canonical_fingerprint({"b": [2, 1], "a": {"x": "yes"}})
    right = canonical_fingerprint({"a": {"x": "yes"}, "b": [2, 1]})
    assert left == right
    assert len(left) == 64


def test_activity_create_replay_conflict_and_monotonic_sequence(
    organization_session: Session,
    agent_context: OrganizationCommandContext,
) -> None:
    first = append_activity(
        organization_session,
        agent_context,
        activity_key="run-1-completed",
        stream_key="operations",
        activity_class=OrganizationActivityClass.operational,
        activity_type="agent.execution.completed.v1",
        title="Execution completed",
        summary="Telemetry was recorded without impact inference.",
        source_object_type="agent_run",
        source_object_id="run-1",
        occurred_at=NOW,
        payload={"result": "success"},
    )
    replay = append_activity(
        organization_session,
        agent_context,
        activity_key="run-1-completed",
        stream_key="operations",
        activity_class="operational",
        activity_type="agent.execution.completed.v1",
        title="Execution completed",
        summary="Telemetry was recorded without impact inference.",
        source_object_type="agent_run",
        source_object_id="run-1",
        occurred_at=NOW,
        payload={"result": "success"},
    )
    assert replay.id == first.id
    second = append_activity(
        organization_session,
        agent_context,
        activity_key="run-2-completed",
        stream_key="operations",
        activity_class="operational",
        activity_type="agent.execution.completed.v1",
        title="Second execution completed",
        summary="Another semantic activity.",
        source_object_type="agent_run",
        source_object_id="run-2",
        occurred_at=NOW,
    )
    assert (first.stream_sequence, second.stream_sequence) == (1, 2)
    assert first.activity_stream_id == second.activity_stream_id
    with pytest.raises(IdempotencyConflict):
        append_activity(
            organization_session,
            agent_context,
            activity_key="run-1-completed",
            stream_key="operations",
            activity_class="operational",
            activity_type="agent.execution.failed.v1",
            title="Conflicting retry",
            summary="Different command under the same key.",
            source_object_type="agent_run",
            source_object_id="run-1",
            occurred_at=NOW,
        )


def test_activity_cross_tenant_work_item_is_rejected(
    organization_session: Session,
    agent_context: OrganizationCommandContext,
    human_context: OrganizationCommandContext,
) -> None:
    other = OrganizationCommandContext("tenant-b", "human-b", "human", "human-b", "admin")
    foreign_work = _work(organization_session, other, "tenant-b-work")
    with pytest.raises(TenantMismatch):
        append_activity(
            organization_session,
            agent_context,
            activity_key="cross-tenant-activity",
            stream_key="operations",
            activity_class="work",
            activity_type="work.observed.v1",
            title="Invalid cross tenant",
            summary="Must fail before append.",
            source_object_type="organizational_work_item",
            source_object_id=str(foreign_work.id),
            work_item_id=foreign_work.id,
            occurred_at=NOW,
        )


@pytest.mark.parametrize("source_type", ["agent_run", "workflow_run", "tool_call", "llm_request", "audit_log"])
def test_execution_telemetry_is_rejected_as_contribution_authority(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    source_type: str,
) -> None:
    with pytest.raises(ContributionSourceRejected):
        validate_authoritative_outcome(
            organization_session,
            human_context,
            source_type=source_type,
            source_id="00000000-0000-0000-0000-000000000001",
            source_version="1",
            outcome_type="not-authoritative",
            verification_basis="Telemetry alone",
        )


def test_contribution_valid_source_replay_conflict_and_correction(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    decision = _approved_decision(organization_session, human_context)
    descriptor = validate_authoritative_outcome(
        organization_session,
        human_context,
        source_type="executive_decision",
        source_id=decision.id,
        source_version=decision.record_fingerprint,
        outcome_type="governed_approval",
        verification_basis="Authenticated Board decision",
    )
    command = dict(
        contribution_key="governed-contribution",
        descriptor=descriptor,
        contribution_type="governed_outcome",
        title="Outcome",
        outcome_summary="Approved outcome",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind="state_change",
        effective_at=NOW,
    )
    original = create_contribution(organization_session, human_context, **command)
    assert create_contribution(organization_session, human_context, **command).id == original.id
    with pytest.raises(IdempotencyConflict):
        create_contribution(organization_session, human_context, **{**command, "outcome_summary": "conflict"})
    correction = append_contribution_correction(
        organization_session,
        human_context,
        contribution_key="governed-contribution-retraction",
        original_contribution_id=original.id,
        descriptor=descriptor,
        record_kind=OrganizationContributionRecordKind.retraction,
        title="Retracted outcome",
        outcome_summary="The previous outcome is no longer active.",
        effective_at=NOW,
        retraction_reason="Board-authorized correction",
    )
    assert correction.id != original.id
    assert correction.supersedes_contribution_id == original.id
    assert correction.record_kind is OrganizationContributionRecordKind.retraction
    organization_session.refresh(original)
    assert original.record_kind is OrganizationContributionRecordKind.outcome
    assert original.supersedes_contribution_id is None


def test_contribution_tenant_and_actor_authority_are_enforced(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
) -> None:
    decision = _approved_decision(organization_session, human_context, "tenant-source")
    other = OrganizationCommandContext("tenant-b", "human-b", "human", "human-b", "admin")
    with pytest.raises(TenantMismatch):
        validate_authoritative_outcome(
            organization_session,
            other,
            source_type="executive_decision",
            source_id=decision.id,
            source_version=decision.record_fingerprint,
            outcome_type="wrong-tenant",
            verification_basis="Must not cross tenants",
        )
    descriptor = validate_authoritative_outcome(
        organization_session,
        human_context,
        source_type="executive_decision",
        source_id=decision.id,
        source_version=decision.record_fingerprint,
        outcome_type="governed_approval",
        verification_basis="Authenticated Board decision",
    )
    with pytest.raises(AuthorityDenied):
        create_contribution(
            organization_session,
            agent_context,
            contribution_key="agent-cannot-contribute",
            descriptor=descriptor,
            contribution_type="invalid",
            title="Invalid",
            outcome_summary="Agent execution is not contribution.",
            department="operations",
            accountable_position_key="coo",
            authority_level="L2",
            impact_kind="delivery",
            effective_at=NOW,
        )


def test_work_item_lifecycle_parent_boundary_and_no_automatic_contribution(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "work-lifecycle")
    assert _work(organization_session, human_context, "work-lifecycle").id == work.id
    start_work_item(organization_session, human_context, work_item_id=work.id, reason="Begin")
    complete_work_item(organization_session, human_context, work_item_id=work.id, reason="Done")
    assert work.status == "completed"
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0
    with pytest.raises(InvalidTransition):
        start_work_item(organization_session, human_context, work_item_id=work.id, reason="No implicit reopen")
    other = OrganizationCommandContext("tenant-b", "human-b", "human", "human-b", "admin")
    foreign_parent = _work(organization_session, other, "foreign-parent")
    with pytest.raises(TenantMismatch):
        _work(organization_session, human_context, "bad-child", parent_work_item_id=foreign_parent.id)


def test_dependencies_create_replay_duplicate_self_cycle_and_cross_tenant(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    first = _work(organization_session, human_context, "dep-first")
    second = _work(organization_session, human_context, "dep-second")
    edge = create_dependency(
        organization_session,
        human_context,
        dependency_key="edge-first-second",
        work_item_id=first.id,
        depends_on_work_item_id=second.id,
        dependency_type=OrganizationDependencyType.requires,
    )
    assert create_dependency(
        organization_session,
        human_context,
        dependency_key="edge-first-second",
        work_item_id=first.id,
        depends_on_work_item_id=second.id,
        dependency_type="requires",
    ).id == edge.id
    with pytest.raises(DependencyConflict):
        create_dependency(
            organization_session,
            human_context,
            dependency_key="same-edge-new-key",
            work_item_id=first.id,
            depends_on_work_item_id=second.id,
            dependency_type="requires",
        )
    with pytest.raises(DependencyConflict):
        create_dependency(
            organization_session,
            human_context,
            dependency_key="self-edge",
            work_item_id=first.id,
            depends_on_work_item_id=first.id,
            dependency_type="blocks",
        )
    with pytest.raises(DependencyConflict):
        create_dependency(
            organization_session,
            human_context,
            dependency_key="cycle-edge",
            work_item_id=second.id,
            depends_on_work_item_id=first.id,
            dependency_type="blocks",
        )
    other = OrganizationCommandContext("tenant-b", "human-b", "human", "human-b", "admin")
    foreign = _work(organization_session, other, "foreign-dependency")
    with pytest.raises(TenantMismatch):
        create_dependency(
            organization_session,
            human_context,
            dependency_key="cross-edge",
            work_item_id=first.id,
            depends_on_work_item_id=foreign.id,
            dependency_type="requires",
        )


def test_dependency_satisfaction_and_waiver_authority(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
) -> None:
    first = _work(organization_session, human_context, "sat-first")
    second = _work(organization_session, human_context, "sat-second")
    edge = create_dependency(
        organization_session,
        human_context,
        dependency_key="sat-edge",
        work_item_id=first.id,
        depends_on_work_item_id=second.id,
        dependency_type="requires",
    )
    contribution = _contribution(organization_session, human_context, "sat-contribution")
    satisfy_dependency(
        organization_session,
        human_context,
        dependency_id=edge.id,
        contribution_id=contribution.id,
        reason="Authoritative prerequisite completed",
    )
    assert edge.status is OrganizationDependencyStatus.satisfied
    waiver_edge = create_dependency(
        organization_session,
        human_context,
        dependency_key="waiver-edge",
        work_item_id=second.id,
        depends_on_work_item_id=first.id,
        dependency_type="informs",
    )
    with pytest.raises(InvalidHumanActor):
        waive_dependency(organization_session, agent_context, dependency_id=waiver_edge.id, reason="Agent cannot waive")
    organization_session.refresh(waiver_edge)
    assert waiver_edge.status is OrganizationDependencyStatus.active


def test_blocker_lifecycle_history_and_waiver_authority(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "blocked-work")
    blocker = open_blocker(
        organization_session,
        human_context,
        blocker_key="blocker-1",
        blocker_type=OrganizationBlockerType.evidence,
        severity="high",
        title="Evidence missing",
        description="A required evidence record is absent.",
        work_item_id=work.id,
    )
    resolved = resolve_blocker(
        organization_session,
        human_context,
        blocker_id=blocker.id,
        reason="Evidence was verified.",
    )
    assert resolved.id == blocker.id
    assert resolved.status is OrganizationBlockerStatus.resolved
    assert resolved.resolved_at and resolved.resolving_actor_id == human_context.actor_id
    with pytest.raises(InvalidTransition):
        mitigate_blocker(organization_session, human_context, blocker_id=blocker.id, reason="No terminal rewrite")
    active = open_blocker(
        organization_session,
        human_context,
        blocker_key="blocker-2",
        blocker_type="authority",
        severity="medium",
        title="Authority needed",
        description="Human waiver required.",
        work_item_id=work.id,
    )
    with pytest.raises(InvalidHumanActor):
        waive_blocker(organization_session, agent_context, blocker_id=active.id, reason="Agent cannot waive")
    organization_session.refresh(active)
    assert active.status is OrganizationBlockerStatus.open


def test_human_action_request_lifecycle_completion_replay_and_no_contribution(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "human-work")
    request = create_human_action_request(
        organization_session,
        human_context,
        request_key="human-request-1",
        request_type=OrganizationHumanActionRequestType.review,
        title="Review governed work",
        instructions="Review the evidence and record an outcome.",
        required_role="admin",
        assigned_human_id=human_context.actor_id,
        work_item_id=work.id,
    )
    assert create_human_action_request(
        organization_session,
        human_context,
        request_key="human-request-1",
        request_type="review",
        title="Review governed work",
        instructions="Review the evidence and record an outcome.",
        required_role="admin",
        assigned_human_id=human_context.actor_id,
        work_item_id=work.id,
    ).id == request.id
    acknowledge_human_action_request(organization_session, human_context, request_id=request.id)
    start_human_action_request(organization_session, human_context, request_id=request.id)
    completed, action = complete_human_action_request(
        organization_session,
        human_context,
        request_id=request.id,
        action_key="human-action-1",
        action_type=OrganizationHumanActionType.reviewed,
        outcome="Evidence accepted",
        occurred_at=NOW,
        reason="Authenticated review completed",
    )
    replay_request, replay_action = complete_human_action_request(
        organization_session,
        human_context,
        request_id=request.id,
        action_key="human-action-1",
        action_type="reviewed",
        outcome="Evidence accepted",
        occurred_at=NOW,
        reason="Authenticated review completed",
    )
    assert completed.status is OrganizationHumanActionRequestStatus.completed
    assert action.actor_type is OrganizationActorType.human
    assert (replay_request.id, replay_action.id) == (completed.id, action.id)
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0
    with pytest.raises(IdempotencyConflict):
        complete_human_action_request(
            organization_session,
            human_context,
            request_id=request.id,
            action_key="human-action-1",
            action_type="reviewed",
            outcome="Conflicting retry",
            occurred_at=NOW,
        )


@pytest.mark.parametrize("actor_type", ["agent", "worker", "system", "external_human"])
def test_non_internal_human_cannot_complete_human_action(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    actor_type: str,
) -> None:
    work = _work(organization_session, human_context, f"human-reject-{actor_type}")
    request = create_human_action_request(
        organization_session,
        human_context,
        request_key=f"request-reject-{actor_type}",
        request_type="approval",
        title="Human only",
        instructions="Must be completed by an authenticated internal human.",
        required_role="admin",
        work_item_id=work.id,
    )
    invalid = OrganizationCommandContext("default", f"{actor_type}-1", actor_type, f"{actor_type}-1", "admin")
    with pytest.raises(InvalidHumanActor):
        complete_human_action_request(
            organization_session,
            invalid,
            request_id=request.id,
            action_key=f"invalid-action-{actor_type}",
            action_type="approved",
            outcome="Invalid",
            occurred_at=NOW,
        )


def test_executive_decision_authority_supersession_and_replay(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    agent_context: OrganizationCommandContext,
) -> None:
    decision = _approved_decision(organization_session, human_context, "canonical-decision")
    assert decision.__tablename__ == "executive_decisions"
    audit_count = organization_session.exec(select(func.count()).select_from(AuditLog)).one()
    replay = record_executive_decision_outcome(
        organization_session,
        human_context,
        decision_id=decision.id,
        outcome="approved",
        reason="Human owner approved the governed outcome.",
    )
    assert replay.id == decision.id
    assert organization_session.exec(select(func.count()).select_from(AuditLog)).one() == audit_count
    with pytest.raises(InvalidHumanActor):
        record_executive_decision_outcome(
            organization_session,
            agent_context,
            decision_id=decision.id,
            outcome="rejected",
            reason="Agent is not Board authority",
        )
    replacement = supersede_executive_decision(
        organization_session,
        human_context,
        original_decision_id=decision.id,
        new_decision_key="canonical-decision-v2",
        title="Revised decision",
        question="Approve the revised decision?",
        recommendation="Approve revised terms",
        reason="Material new evidence",
    )
    assert replacement.supersedes_decision_id == decision.id
    organization_session.refresh(decision)
    assert decision.status == "approved"


def test_reference_allowlist_existence_tenant_owner_and_valid_reference(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "reference-owner")
    lead = Lead(full_name="Reference Subject")
    organization_session.add(lead)
    organization_session.commit()
    with pytest.raises(InvalidReference):
        create_record_reference(
            organization_session,
            human_context,
            reference_key="bad-type",
            reference_role="evidence",
            target_type="arbitrary_table",
            target_id=lead.id,
            work_item_id=work.id,
        )
    with pytest.raises(InvalidReference):
        create_record_reference(
            organization_session,
            human_context,
            reference_key="missing-target",
            reference_role="evidence",
            target_type="lead",
            target_id="00000000-0000-0000-0000-000000000001",
            work_item_id=work.id,
        )
    other = OrganizationCommandContext("tenant-b", "human-b", "human", "human-b", "admin")
    other_work = _work(organization_session, other, "other-reference-owner")
    with pytest.raises(TenantMismatch):
        create_record_reference(
            organization_session,
            other,
            reference_key="wrong-target-tenant",
            reference_role="evidence",
            target_type="lead",
            target_id=lead.id,
            work_item_id=other_work.id,
        )
    reference = create_record_reference(
        organization_session,
        human_context,
        reference_key="valid-reference",
        reference_role=OrganizationReferenceRole.affected_subject,
        target_type=OrganizationReferenceTargetType.lead,
        target_id=lead.id,
        work_item_id=work.id,
        label="Affected lead",
    )
    assert reference.target_id == str(lead.id)
    assert create_record_reference(
        organization_session,
        human_context,
        reference_key="valid-reference",
        reference_role="affected_subject",
        target_type="lead",
        target_id=lead.id,
        work_item_id=work.id,
        label="Affected lead",
    ).id == reference.id


def test_successful_mutation_writes_audit_and_audit_failure_rolls_back_domain(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = _work(organization_session, human_context, "audited-work")
    assert organization_session.exec(
        select(func.count()).select_from(AuditLog).where(AuditLog.entity_id == str(work.id))
    ).one() == 1
    before_work = organization_session.exec(select(func.count()).select_from(OrganizationalWorkItem)).one()
    before_audit = organization_session.exec(select(func.count()).select_from(AuditLog)).one()

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("simulated audit storage failure")

    monkeypatch.setattr(organization_command, "record_audit", fail_audit)
    with pytest.raises(RuntimeError, match="audit storage"):
        _work(organization_session, human_context, "must-roll-back")
    assert organization_session.exec(select(func.count()).select_from(OrganizationalWorkItem)).one() == before_work
    assert organization_session.exec(select(func.count()).select_from(AuditLog)).one() == before_audit


def test_failed_transition_creates_no_false_success_audit(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    work = _work(organization_session, human_context, "failed-transition")
    start_work_item(organization_session, human_context, work_item_id=work.id, reason="Start")
    complete_work_item(organization_session, human_context, work_item_id=work.id, reason="Complete")
    before = organization_session.exec(select(func.count()).select_from(AuditLog)).one()
    with pytest.raises(InvalidTransition):
        block_work_item(organization_session, human_context, work_item_id=work.id, reason="Invalid late blocker")
    assert organization_session.exec(select(func.count()).select_from(AuditLog)).one() == before


def test_agent_and_workflow_success_have_no_automatic_contribution_source_boundary() -> None:
    assert "contribution_key" not in AgentRun.__table__.columns
    assert "contribution_id" not in AgentRun.__table__.columns
    assert OrganizationContribution.__tablename__ == "organization_contributions"


def test_no_organization_router_or_real_contribution_emitter_was_added() -> None:
    api_root = Path(__file__).resolve().parents[1]
    router_names = {path.name for path in (api_root / "app" / "routers").glob("*.py")}
    assert "organization_activity.py" not in router_names
    assert "organization_contribution.py" not in router_names
    contribution_import = "app.services.organization_contribution import"
    integration_roots = [api_root / "app" / "tasks", api_root / "app" / "workflows"]
    integration_files = [path for root in integration_roots for path in root.rglob("*.py")]
    assert all(contribution_import not in path.read_text(encoding="utf-8") for path in integration_files)


def test_postgresql_activity_row_lock_and_sequence_contract() -> None:
    database_url = os.getenv("ORGANIZATION_POSTGRES_TEST_URL")
    if not database_url:
        pytest.skip("ORGANIZATION_POSTGRES_TEST_URL is not configured")
    engine = create_engine(database_url)
    connection = engine.connect()
    outer = connection.begin()
    try:
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            context = OrganizationCommandContext("default", "pg-service-test", "system", "pg-service-test", "operator")
            suffix = uuid4().hex
            first = append_activity(
                session,
                context,
                activity_key=f"pg-activity-{suffix}-1",
                stream_key=f"pg-stream-{suffix}",
                activity_class="operational",
                activity_type="postgres.contract.checked.v1",
                title="PostgreSQL contract check",
                summary="Exercises row locking and sequence allocation.",
                source_object_type="verified_rule",
                source_object_id=suffix,
                occurred_at=NOW,
            )
            second = append_activity(
                session,
                context,
                activity_key=f"pg-activity-{suffix}-2",
                stream_key=f"pg-stream-{suffix}",
                activity_class="operational",
                activity_type="postgres.contract.checked.v1",
                title="Second PostgreSQL contract check",
                summary="Verifies the same locked stream remains monotonic.",
                source_object_type="verified_rule",
                source_object_id=suffix,
                occurred_at=NOW,
            )
            assert (first.stream_sequence, second.stream_sequence) == (1, 2)
            assert first.activity_stream_id == second.activity_stream_id
    finally:
        outer.rollback()
        connection.close()
        engine.dispose()

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import event, func
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.core.db import register_models
from app.models.domain import (
    AuditLog,
    ExecutiveDecision,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionRecordKind,
)
from app.services import organization_command
from app.services.organization_command import (
    AuditMutation,
    OrganizationCommandContext,
    snapshot,
    stage_mutations,
)
from app.services.organization_contribution import (
    append_contribution_correction,
    create_contribution,
    stage_contribution,
    stage_contribution_correction,
    validate_authoritative_outcome,
)
from app.services.organization_decision import create_executive_decision


NOW = datetime(2026, 8, 14, 10, 30, tzinfo=timezone.utc)


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
        correlation_key="corr-13161d1",
    )


def _pending_decision(
    session: Session,
    context: OrganizationCommandContext,
    key: str,
) -> ExecutiveDecision:
    return create_executive_decision(
        session,
        context,
        decision_key=key,
        decision_type="operational",
        authority_level="L3",
        requested_by_position="coo",
        decision_owner_position="ceo",
        title="Caller-owned source transition",
        question="Approve the bounded outcome?",
        recommendation="Approve",
    )


def _stage_decision_approval(
    session: Session,
    context: OrganizationCommandContext,
    decision: ExecutiveDecision,
) -> None:
    before = snapshot(decision)
    decision.status = "approved"
    decision.decided_by = context.actor_id
    decision.decision_reason = "Caller-owned transaction test"
    decision.effect_summary = "Source state staged before Contribution emission."
    decision.decided_at = NOW
    decision.updated_at = NOW
    session.add(decision)
    stage_mutations(
        session,
        mutations=[
            AuditMutation(
                "test.executive_decision.approved",
                "executive_decision",
                decision.id,
                before_state=before,
                after_state=decision,
                reason=decision.decision_reason,
            )
        ],
        context=context,
    )


def _descriptor(
    session: Session,
    context: OrganizationCommandContext,
    decision: ExecutiveDecision,
):
    return validate_authoritative_outcome(
        session,
        context,
        source_type="executive_decision",
        source_id=decision.id,
        source_version=decision.record_fingerprint,
        outcome_type="governed_approval",
        verification_basis="Authenticated source transition inside caller transaction",
    )


def _stage_contribution(
    session: Session,
    context: OrganizationCommandContext,
    decision: ExecutiveDecision,
    *,
    key: str,
):
    return stage_contribution(
        session,
        context,
        contribution_key=key,
        descriptor=_descriptor(session, context, decision),
        contribution_type="governed_outcome",
        title="Governed outcome staged",
        outcome_summary="The authoritative outcome is staged without an inner commit.",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind="state_change",
        effective_at=NOW,
        decision_id=decision.id,
    )


def test_stage_contribution_never_owns_commit_and_outer_rollback_is_atomic(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = _pending_decision(organization_session, human_context, "d1-atomic-rollback")
    baseline_audits = organization_session.exec(select(func.count()).select_from(AuditLog)).one()

    _stage_decision_approval(organization_session, human_context, decision)

    original_commit = organization_session.commit

    def forbidden_inner_commit() -> None:
        raise AssertionError("caller-owned staging must not commit")

    monkeypatch.setattr(organization_session, "commit", forbidden_inner_commit)
    contribution = _stage_contribution(
        organization_session,
        human_context,
        decision,
        key="d1-atomic-rollback-contribution",
    )
    assert contribution.source_state == "approved"
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 1
    assert organization_session.exec(select(func.count()).select_from(AuditLog)).one() == baseline_audits + 2

    monkeypatch.setattr(organization_session, "commit", original_commit)
    organization_session.rollback()

    restored = organization_session.get(ExecutiveDecision, decision.id)
    assert restored is not None
    assert restored.status == "pending_ceo"
    assert restored.decided_by is None
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0
    assert organization_session.exec(select(func.count()).select_from(AuditLog)).one() == baseline_audits


def test_stage_contribution_audit_failure_leaves_rollback_to_transaction_owner(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = _pending_decision(organization_session, human_context, "d1-audit-failure")
    baseline_audits = organization_session.exec(select(func.count()).select_from(AuditLog)).one()
    _stage_decision_approval(organization_session, human_context, decision)
    descriptor = _descriptor(organization_session, human_context, decision)

    original_record_audit = organization_command.record_audit

    def fail_contribution_audit(*args, **kwargs):  # type: ignore[no-untyped-def]
        if kwargs.get("action") == "organization.contribution.create":
            raise RuntimeError("simulated contribution audit storage failure")
        return original_record_audit(*args, **kwargs)

    monkeypatch.setattr(organization_command, "record_audit", fail_contribution_audit)
    with pytest.raises(RuntimeError, match="contribution audit storage"):
        stage_contribution(
            organization_session,
            human_context,
            contribution_key="d1-audit-failure-contribution",
            descriptor=descriptor,
            contribution_type="governed_outcome",
            title="Must roll back",
            outcome_summary="Audit failure cannot leave a partial authoritative outcome.",
            department="operations",
            accountable_position_key="coo",
            authority_level="L3",
            impact_kind="state_change",
            effective_at=NOW,
            decision_id=decision.id,
        )

    # The staging primitive deliberately did not hide the failure with an inner rollback;
    # the caller still owns the complete transaction and can roll it all back together.
    assert organization_session.in_transaction()
    organization_session.rollback()

    restored = organization_session.get(ExecutiveDecision, decision.id)
    assert restored is not None
    assert restored.status == "pending_ceo"
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0
    assert organization_session.exec(select(func.count()).select_from(AuditLog)).one() == baseline_audits


def test_staged_replay_commits_once_without_duplicate_contribution_audit(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    decision = _pending_decision(organization_session, human_context, "d1-replay")
    _stage_decision_approval(organization_session, human_context, decision)
    descriptor = _descriptor(organization_session, human_context, decision)
    command = dict(
        contribution_key="d1-replay-contribution",
        descriptor=descriptor,
        contribution_type="governed_outcome",
        title="Replay-safe outcome",
        outcome_summary="One source revision produces one Contribution.",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind="state_change",
        effective_at=NOW,
        decision_id=decision.id,
    )

    first = stage_contribution(organization_session, human_context, **command)
    replay = stage_contribution(organization_session, human_context, **command)
    assert replay.id == first.id
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 1
    assert organization_session.exec(
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "organization.contribution.create")
    ).one() == 1

    organization_session.commit()
    organization_session.refresh(first)
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 1
    assert organization_session.exec(
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "organization.contribution.create")
    ).one() == 1


def test_staged_correction_is_caller_owned_and_rollback_preserves_original(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    decision = _pending_decision(organization_session, human_context, "d1-correction-source")
    _stage_decision_approval(organization_session, human_context, decision)
    descriptor = _descriptor(organization_session, human_context, decision)
    original = stage_contribution(
        organization_session,
        human_context,
        contribution_key="d1-original",
        descriptor=descriptor,
        contribution_type="governed_outcome",
        title="Original outcome",
        outcome_summary="Original authoritative outcome.",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind="state_change",
        effective_at=NOW,
        decision_id=decision.id,
    )
    organization_session.commit()
    organization_session.refresh(original)

    staged = stage_contribution_correction(
        organization_session,
        human_context,
        contribution_key="d1-original-retraction",
        original_contribution_id=original.id,
        descriptor=descriptor,
        record_kind=OrganizationContributionRecordKind.retraction,
        title="Retracted outcome",
        outcome_summary="Caller-owned correction is staged only.",
        effective_at=NOW,
        retraction_reason="Transaction composability verification",
    )
    assert staged.supersedes_contribution_id == original.id
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 2

    organization_session.rollback()
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 1
    persisted = organization_session.get(OrganizationContribution, original.id)
    assert persisted is not None
    assert persisted.record_kind is OrganizationContributionRecordKind.outcome


def test_standalone_contribution_wrapper_still_commits_for_api_contract(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    decision = _pending_decision(organization_session, human_context, "d1-standalone")
    _stage_decision_approval(organization_session, human_context, decision)
    # The source transition is explicitly committed here to model the existing standalone
    # API source contract; D1 must not change create_contribution() commit-on-command behavior.
    organization_session.commit()
    descriptor = _descriptor(organization_session, human_context, decision)
    contribution = create_contribution(
        organization_session,
        human_context,
        contribution_key="d1-standalone-contribution",
        descriptor=descriptor,
        contribution_type="governed_outcome",
        title="Standalone API outcome",
        outcome_summary="Standalone Contribution command still commits atomically with its audit.",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind="state_change",
        effective_at=NOW,
        decision_id=decision.id,
    )
    organization_session.expire_all()
    assert organization_session.get(OrganizationContribution, contribution.id) is not None
    assert organization_session.exec(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "organization.contribution.create",
            AuditLog.entity_id == str(contribution.id),
        )
    ).one() == 1


def test_standalone_correction_wrapper_still_commits(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    decision = _pending_decision(organization_session, human_context, "d1-standalone-correction")
    _stage_decision_approval(organization_session, human_context, decision)
    organization_session.commit()
    descriptor = _descriptor(organization_session, human_context, decision)
    original = create_contribution(
        organization_session,
        human_context,
        contribution_key="d1-standalone-original",
        descriptor=descriptor,
        contribution_type="governed_outcome",
        title="Original",
        outcome_summary="Original standalone outcome.",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind="state_change",
        effective_at=NOW,
        decision_id=decision.id,
    )
    correction = append_contribution_correction(
        organization_session,
        human_context,
        contribution_key="d1-standalone-retraction",
        original_contribution_id=original.id,
        descriptor=descriptor,
        record_kind="retraction",
        title="Retracted",
        outcome_summary="Standalone correction remains commit-on-command.",
        effective_at=NOW,
        retraction_reason="Standalone wrapper regression check",
    )
    organization_session.expire_all()
    assert organization_session.get(OrganizationContribution, correction.id) is not None


def test_caller_commit_failure_can_roll_back_source_contribution_and_audits(
    organization_session: Session,
    human_context: OrganizationCommandContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = _pending_decision(organization_session, human_context, "d1-final-commit-failure")
    baseline_audits = organization_session.exec(select(func.count()).select_from(AuditLog)).one()
    _stage_decision_approval(organization_session, human_context, decision)
    _stage_contribution(
        organization_session,
        human_context,
        decision,
        key="d1-final-commit-failure-contribution",
    )

    original_commit = organization_session.commit

    def fail_outer_commit() -> None:
        raise RuntimeError("simulated outer commit failure")

    monkeypatch.setattr(organization_session, "commit", fail_outer_commit)
    with pytest.raises(RuntimeError, match="outer commit failure"):
        organization_session.commit()
    monkeypatch.setattr(organization_session, "commit", original_commit)
    organization_session.rollback()

    restored = organization_session.get(ExecutiveDecision, decision.id)
    assert restored is not None
    assert restored.status == "pending_ceo"
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0
    assert organization_session.exec(select(func.count()).select_from(AuditLog)).one() == baseline_audits


def test_staged_semantic_conflict_fails_closed_without_duplicate_audit(
    organization_session: Session,
    human_context: OrganizationCommandContext,
) -> None:
    from app.services.organization_command import IdempotencyConflict

    decision = _pending_decision(organization_session, human_context, "d1-semantic-conflict")
    _stage_decision_approval(organization_session, human_context, decision)
    descriptor = _descriptor(organization_session, human_context, decision)
    base = dict(
        contribution_key="d1-semantic-conflict-contribution",
        descriptor=descriptor,
        contribution_type="governed_outcome",
        title="Stable title",
        outcome_summary="Stable semantic outcome.",
        department="operations",
        accountable_position_key="coo",
        authority_level="L3",
        impact_kind="state_change",
        effective_at=NOW,
        decision_id=decision.id,
    )
    stage_contribution(organization_session, human_context, **base)
    with pytest.raises(IdempotencyConflict):
        stage_contribution(
            organization_session,
            human_context,
            **{**base, "outcome_summary": "Conflicting semantic outcome."},
        )
    assert organization_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 1
    assert organization_session.exec(
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "organization.contribution.create")
    ).one() == 1
    organization_session.rollback()

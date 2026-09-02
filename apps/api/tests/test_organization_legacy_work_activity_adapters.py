from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func
from sqlmodel import Session, create_engine, select

from app.models.domain import (
    AuditLog,
    DelegationRecord,
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationContribution,
    OrganizationPosition,
    OrganizationalWorkItem,
)
from app.services.organization_governance import (
    _mark_execution_cancelled,
    _mark_execution_failed,
    ensure_foundation_positions,
    set_work_deadline,
)


def _headers(role: str = "admin", user: str = "e3b-owner") -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _create_work(raw_client, *, key: str, **changes) -> UUID:
    payload = {
        "idempotency_key": key,
        "title": key,
        "objective": "Exercise Phase 13.16.1E3B legacy WorkItem Activity coverage.",
        "department": "Operations",
        "action": "internal.analysis",
    }
    payload.update(changes)
    response = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


def _activity_types(session: Session, work_id: UUID) -> list[str]:
    return [
        row.activity_type
        for row in session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.source_object_type == "organizational_work_item",
                OrganizationActivity.source_object_id == str(work_id),
            )
            .order_by(OrganizationActivity.stream_sequence)
        ).all()
    ]


def _technology_context() -> dict:
    return {
        "technology_review_type": "delivery_readiness",
        "facts": {
            "change_scope": "internal platform readiness review",
            "dependencies": ["API test suite", "migration validation"],
        },
        "evidence": {
            "architecture": ["architecture-decision-record:phase-13"],
            "data_handling": ["data-classification:internal"],
            "integration": ["integration-contract:organization-api"],
            "tests": ["quality-gate:e3b"],
            "reliability": ["reliability-review:bounded-runtime"],
            "security": ["external-actions:fail-closed"],
            "rollback": "Revert the internal configuration and replay the bounded review.",
            "observability": ["audit-ledger", "activity-ledger"],
            "sources": ["repository:apps/api", "repository:docs/ROADMAP.md"],
        },
    }


def test_legacy_create_deadline_escalation_and_cancel_are_semantic(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(raw_client, key="e3b-lifecycle-001")
    due = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat().replace("+00:00", "Z")

    deadline = raw_client.post(f"/api/v1/organization/work-items/{work_id}/deadline", json={"due_at": due})
    assert deadline.status_code == 200, deadline.text
    after_first_deadline = list(_activity_types(db_session, work_id))
    replay_deadline = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/deadline",
        json={"due_at": due},
    )
    assert replay_deadline.status_code == 200, replay_deadline.text
    assert _activity_types(db_session, work_id) == after_first_deadline
    escalated = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/escalate",
        json={"reason": "Escalate the bounded operating review to its parent position."},
    )
    assert escalated.status_code == 200, escalated.text
    cancelled = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/cancel",
        json={"reason": "Human owner cancels the bounded review before execution."},
    )
    assert cancelled.status_code == 200, cancelled.text

    assert _activity_types(db_session, work_id) == [
        "organization.work.created.v1",
        "organization.work.deadline.set.v1",
        "organization.work.escalated.v1",
        "organization.work.cancellation_requested.v1",
        "organization.work.status.cancelled.v1",
    ]
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0


def test_global_pause_hold_and_resume_requeue_share_source_transaction(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(raw_client, key="e3b-global-control-001")
    paused = raw_client.post(
        "/api/v1/organization/control",
        json={"status": "paused", "reason": "Board pauses bounded execution."},
    )
    assert paused.status_code == 200, paused.text

    held = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert held.status_code == 200, held.text
    assert held.json()["status"] == "held"
    pause_audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.action == "organization_work_held_global_pause",
            AuditLog.entity_id == str(work_id),
        )
    ).first()
    assert pause_audit is not None

    resumed = raw_client.post(
        "/api/v1/organization/control",
        json={"status": "active", "reason": "Board resumes bounded execution."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"
    assert _activity_types(db_session, work_id) == [
        "organization.work.created.v1",
        "organization.work.status.held.v1",
        "organization.work.status.queued.v1",
    ]


def test_position_resume_requeues_held_work_semantically(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(raw_client, key="e3b-position-resume-001")
    coo = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "coo")
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{coo.id}/suspend",
        json={"reason": "Temporarily suspend the accountable position."},
    )
    assert suspended.status_code == 200, suspended.text
    held = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert held.status_code == 200, held.text
    assert held.json()["status"] == "held"

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{coo.id}/resume",
        json={"reason": "Restore the accountable position after review."},
    )
    assert resumed.status_code == 200, resumed.text
    assert _activity_types(db_session, work_id) == [
        "organization.work.created.v1",
        "organization.work.status.held.v1",
        "organization.work.status.queued.v1",
    ]


def test_emergency_material_commits_are_semantic_and_replay_safe(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(raw_client, key="e3b-emergency-001")
    first = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Critical bounded governance exception requires Board review."},
    )
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "pending_board"
    before_replay = _activity_types(db_session, work_id)
    assert before_replay == [
        "organization.work.created.v1",
        "organization.work.emergency_marked.v1",
        "organization.work.status.held.v1",
        "organization.work.emergency_escalated.v1",
        "organization.work.emergency_escalated.v1",
        "organization.work.status.pending_board.v1",
    ]

    replay = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Critical bounded governance exception requires Board review."},
    )
    assert replay.status_code == 200, replay.text
    assert _activity_types(db_session, work_id) == before_replay


def test_retry_wait_is_telemetry_but_terminal_failure_is_semantic(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(raw_client, key="e3b-terminal-failure-001")
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None
    work.status = "running"
    work.execution_attempts = 1
    work.max_execution_attempts = 2
    db_session.add(work)
    db_session.commit()
    before = list(_activity_types(db_session, work_id))

    retriable = _mark_execution_failed(
        db_session,
        work_item_id=work_id,
        execution_token=str(uuid4()),
        error=RuntimeError("retriable execution fault"),
        actor="organization-worker",
    )
    assert retriable.status == "retry_wait"
    assert _activity_types(db_session, work_id) == before

    retriable.status = "running"
    retriable.execution_attempts = 2
    db_session.add(retriable)
    db_session.commit()
    terminal = _mark_execution_failed(
        db_session,
        work_item_id=work_id,
        execution_token=str(uuid4()),
        error=RuntimeError("terminal execution fault"),
        actor="organization-worker",
    )
    assert terminal.status == "failed"
    assert _activity_types(db_session, work_id) == before + ["organization.work.status.failed.v1"]


def test_running_cancellation_records_request_then_terminal_disposition(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(raw_client, key="e3b-running-cancel-001")
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None
    work.status = "running"
    work.execution_attempts = 1
    db_session.add(work)
    db_session.commit()

    requested = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/cancel",
        json={"reason": "Human owner requests cancellation of in-flight bounded work."},
    )
    assert requested.status_code == 200, requested.text
    assert requested.json()["status"] == "running"
    assert _activity_types(db_session, work_id)[-1] == "organization.work.cancellation_requested.v1"

    terminal = _mark_execution_cancelled(
        db_session,
        work_item_id=work_id,
        execution_token=str(uuid4()),
        actor="organization-worker",
    )
    assert terminal.status == "cancelled"
    assert _activity_types(db_session, work_id)[-1] == "organization.work.status.cancelled.v1"


def test_technology_evidence_amendment_and_release_are_both_semantic(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(
        raw_client,
        key="e3b-evidence-amend-001",
        department="Technology",
        context={"facts": {"change_scope": "unknown"}, "evidence": {}},
    )
    held = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert held.status_code == 200, held.text
    assert held.json()["status"] == "held"

    context = _technology_context()
    amended = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/technology-evidence",
        json={
            "evidence": context["evidence"],
            "facts": context["facts"],
            "reason": "Human owner supplies the missing bounded technical evidence.",
        },
    )
    assert amended.status_code == 200, amended.text
    assert amended.json()["status"] == "queued"
    assert _activity_types(db_session, work_id)[-2:] == [
        "organization.work.evidence.amended.v1",
        "organization.work.status.queued.v1",
    ]


def test_coupled_board_override_stages_only_the_linked_work_side_in_e3b(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(
        raw_client,
        key="e3b-board-override-work-001",
        risk_level="high",
    )
    decision = db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()
    response = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-override",
        json={"decision": "approved", "reason": "Board records the bounded L3 override."},
    )
    assert response.status_code == 200, response.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "held"
    assert _activity_types(db_session, work_id)[-1] == "organization.work.status.held.v1"


def test_activity_staging_failure_rolls_back_legacy_deadline_and_source_audit(
    raw_client,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(raw_client, key="e3b-rollback-001")
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.due_at is None
    activities_before = db_session.exec(select(func.count()).select_from(OrganizationActivity)).one()
    audits_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()

    def fail_activity(*_args, **_kwargs):
        raise RuntimeError("simulated legacy semantic Activity failure")

    monkeypatch.setattr(
        "app.services.organization_governance.stage_work_item_deadline_activity",
        fail_activity,
    )
    with pytest.raises(RuntimeError, match="legacy semantic Activity failure"):
        set_work_deadline(
            db_session,
            work,
            due_at=datetime.now(timezone.utc) + timedelta(hours=2),
            actor="e3b-owner",
        )

    db_session.refresh(work)
    assert work.due_at is None
    assert db_session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before


def test_bootstrap_side_effect_requeue_emits_activity_only_when_work_changes(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_work(
        raw_client,
        key="e3b-bootstrap-requeue-001",
        department="Technology",
        context=_technology_context(),
    )
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None
    delegation = db_session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == work_id,
            DelegationRecord.delegate_position_key == "lead_architect",
        )
    ).one()
    architect = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "lead_architect")
    ).one()
    work.status = "held"
    work.last_error = None
    delegation.status = "held"
    delegation.result_ref = "position:unavailable"
    db_session.add(work)
    db_session.add(delegation)
    db_session.delete(architect)
    db_session.commit()
    before = list(_activity_types(db_session, work_id))

    ensure_foundation_positions(db_session, actor="e3b-owner")
    db_session.commit()
    db_session.refresh(work)
    assert work.status == "queued"
    assert _activity_types(db_session, work_id) == before + ["organization.work.status.queued.v1"]

    before_replay = list(_activity_types(db_session, work_id))
    ensure_foundation_positions(db_session, actor="e3b-owner")
    db_session.commit()
    assert _activity_types(db_session, work_id) == before_replay


def test_postgresql_legacy_deadline_activity_is_atomic_and_outer_rollback_leaves_no_residue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.getenv("ORGANIZATION_POSTGRES_TEST_URL")
    if not database_url:
        pytest.skip("ORGANIZATION_POSTGRES_TEST_URL is not configured")

    engine = create_engine(database_url)
    connection = engine.connect()
    outer = connection.begin()
    work_id: UUID | None = None
    try:
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            suffix = uuid4().hex
            work = OrganizationalWorkItem(
                idempotency_key=f"e3b-pg-deadline-{suffix}",
                title="E3B PostgreSQL atomic deadline",
                objective="Prove legacy Work mutation and semantic Activity share the existing transaction.",
                department="Operations",
                authority_level="L1",
                assigned_position_key="coo",
                status="queued",
                created_by="e3b-pg-owner",
            )
            session.add(work)
            session.commit()
            session.refresh(work)
            work_id = work.id

            audits_before = session.exec(select(func.count()).select_from(AuditLog)).one()
            activities_before = session.exec(select(func.count()).select_from(OrganizationActivity)).one()

            def fail_activity(*_args, **_kwargs):
                raise RuntimeError("simulated PostgreSQL legacy semantic Activity failure")

            monkeypatch.setattr(
                "app.services.organization_governance.stage_work_item_deadline_activity",
                fail_activity,
            )
            with pytest.raises(RuntimeError, match="PostgreSQL legacy semantic Activity failure"):
                set_work_deadline(
                    session,
                    work,
                    due_at=datetime.now(timezone.utc) + timedelta(hours=1),
                    actor="e3b-pg-owner",
                )
            session.refresh(work)
            assert work.due_at is None
            assert session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before
            assert session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before

            monkeypatch.undo()
            due_at = datetime.now(timezone.utc) + timedelta(hours=2)
            set_work_deadline(session, work, due_at=due_at, actor="e3b-pg-owner")
            activities = _activity_types(session, work.id)
            assert activities == ["organization.work.deadline.set.v1"]
            session.refresh(work)
            assert work.due_at == due_at
    finally:
        outer.rollback()
        connection.close()

    try:
        with Session(engine) as verification:
            assert work_id is not None
            assert verification.get(OrganizationalWorkItem, work_id) is None
            assert verification.exec(
                select(func.count()).select_from(OrganizationActivity).where(
                    OrganizationActivity.source_object_type == "organizational_work_item",
                    OrganizationActivity.source_object_id == str(work_id),
                )
            ).one() == 0
    finally:
        engine.dispose()

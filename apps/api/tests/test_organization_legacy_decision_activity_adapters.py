from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func
from sqlmodel import Session, create_engine, select

from app.models.domain import (
    AuditLog,
    AutomationEvent,
    CorporateAccount,
    CorporateMobilityCase,
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationalWorkItem,
)
from app.services.organization_governance import (
    _claim_ceo_decision,
    _hold_ceo_decision,
    _promote_decision_to_board,
    route_automation_event,
    set_decision_deadline,
)


def _headers(role: str = "admin", user: str = "e3c-owner") -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _create_governed_work(raw_client, *, key: str, risk_level: str = "high") -> UUID:
    response = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": key,
            "objective": "Exercise Phase 13.16.1E3C legacy Decision/coupled Activity coverage.",
            "department": "Operations",
            "action": "internal.analysis",
            "risk_level": risk_level,
            "context": {"scope": "internal", "external_action_authorized": False},
        },
    )
    assert response.status_code == 201, response.text
    work_id = UUID(response.json()["id"])
    return work_id


def _decision_for_work(session: Session, work_id: UUID) -> ExecutiveDecision:
    return session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()


def _decision_activity_types(session: Session, decision_id: UUID) -> list[str]:
    return [
        row.activity_type
        for row in session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.source_object_type == "executive_decision",
                OrganizationActivity.source_object_id == str(decision_id),
            )
            .order_by(OrganizationActivity.stream_sequence)
        ).all()
    ]


def _work_activity_types(session: Session, work_id: UUID) -> list[str]:
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


def test_legacy_decision_create_deadline_replay_and_board_override_are_semantic(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_governed_work(raw_client, key="e3c-decision-lifecycle-001")
    decision = _decision_for_work(db_session, work_id)
    assert _decision_activity_types(db_session, decision.id) == [
        "organization.decision.created.v1"
    ]

    due = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat().replace("+00:00", "Z")
    first = raw_client.post(f"/api/v1/organization/decisions/{decision.id}/deadline", json={"due_at": due})
    assert first.status_code == 200, first.text
    after_first = list(_decision_activity_types(db_session, decision.id))
    replay = raw_client.post(f"/api/v1/organization/decisions/{decision.id}/deadline", json={"due_at": due})
    assert replay.status_code == 200, replay.text
    assert _decision_activity_types(db_session, decision.id) == after_first

    outcome = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-override",
        json={"decision": "approved", "reason": "Board records the bounded L3 override."},
    )
    assert outcome.status_code == 200, outcome.text
    assert _decision_activity_types(db_session, decision.id) == [
        "organization.decision.created.v1",
        "organization.decision.deadline.set.v1",
        "organization.decision.status.approved.v1",
    ]


def test_board_reserved_outcome_stages_decision_and_linked_work_in_one_path(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_governed_work(
        raw_client,
        key="e3c-board-outcome-001",
        risk_level="critical",
    )
    decision = _decision_for_work(db_session, work_id)
    assert decision.status == "pending_board"

    response = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-decision",
        json={"decision": "returned", "reason": "Board returns the matter for bounded revision."},
    )
    assert response.status_code == 200, response.text
    assert _decision_activity_types(db_session, decision.id)[-1] == "organization.decision.status.returned.v1"
    assert _work_activity_types(db_session, work_id)[-1] == "organization.work.status.returned.v1"


def test_emergency_promotion_records_decision_escalation_and_is_replay_safe(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_governed_work(raw_client, key="e3c-emergency-decision-001")
    decision = _decision_for_work(db_session, work_id)

    first = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Critical bounded governance exception requires Board review."},
    )
    assert first.status_code == 200, first.text
    before_replay = _decision_activity_types(db_session, decision.id)
    assert before_replay == [
        "organization.decision.created.v1",
        "organization.decision.emergency_escalated.v1",
        "organization.decision.emergency_escalated.v1",
        "organization.decision.emergency_escalated.v1",
    ]

    replay = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Critical bounded governance exception requires Board review."},
    )
    assert replay.status_code == 200, replay.text
    assert _decision_activity_types(db_session, decision.id) == before_replay


def test_ceo_hold_is_semantic_but_coordination_claim_is_not(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_governed_work(raw_client, key="e3c-ceo-hold-001")
    decision = _decision_for_work(db_session, work_id)
    before = list(_decision_activity_types(db_session, decision.id))

    claimed, coordination_token = _claim_ceo_decision(
        db_session,
        decision,
        actor="ceo-agent",
    )
    assert coordination_token is not None
    assert claimed.status == "coordinating_ceo"
    assert _decision_activity_types(db_session, decision.id) == before

    held = _hold_ceo_decision(
        db_session,
        claimed,
        coordination_token=coordination_token,
        reason="Required executive consultation is not complete.",
        actor="ceo-agent",
    )
    assert held.status == "pending_ceo"
    assert _decision_activity_types(db_session, decision.id) == before + [
        "organization.decision.held.v1"
    ]


def test_board_promotion_closes_coupled_work_side_and_decision_side(
    raw_client,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_governed_work(raw_client, key="e3c-board-promotion-001")
    work = db_session.get(OrganizationalWorkItem, work_id)
    decision = _decision_for_work(db_session, work_id)
    assert work is not None

    work.status = "pending_ceo"
    decision.status = "coordinating_ceo"
    decision.coordination_token = "e3c-promote-token"
    decision.coordination_claimed_at = datetime.now(timezone.utc)
    db_session.add(work)
    db_session.add(decision)
    db_session.commit()

    monkeypatch.setattr(
        "app.services.organization_governance.create_board_packet",
        lambda *_args, **_kwargs: {},
    )
    promoted = _promote_decision_to_board(
        db_session,
        decision,
        work,
        coordination_token="e3c-promote-token",
        reason="CEO exception requires Human Board authority.",
        actor="ceo-agent",
    )
    assert promoted.status == "pending_board"
    db_session.refresh(work)
    assert work.status == "pending_board"
    assert _decision_activity_types(db_session, decision.id)[-1] == "organization.decision.escalated.v1"
    assert _work_activity_types(db_session, work_id)[-1] == "organization.work.status.pending_board.v1"


def test_automation_route_stages_decision_creation_without_owning_commit(db_session: Session) -> None:
    suffix = uuid4().hex
    account = CorporateAccount(
        legal_name=f"E3C Automation {suffix}",
        primary_country="AT",
        created_by="e3c-owner",
        updated_by="e3c-owner",
    )
    case = CorporateMobilityCase(
        corporate_account_id=account.id,
        case_reference=f"E3C-{suffix}",
        destination_country="AT",
        created_by="e3c-owner",
        updated_by="e3c-owner",
    )
    event = AutomationEvent(
        idempotency_key=f"e3c-automation-{suffix}",
        corporate_account_id=account.id,
        corporate_mobility_case_id=case.id,
        event_type="material.internal.review",
        entity_type="corporate_mobility_case",
        entity_id=str(case.id),
        payload_json=json.dumps({"action": "internal.analysis", "risk_level": "high"}),
        created_by="automation-e3c",
    )
    db_session.add(account)
    db_session.add(case)
    db_session.add(event)
    db_session.commit()

    work, created = route_automation_event(db_session, event, case, actor="automation-e3c")
    assert created is True
    decision = _decision_for_work(db_session, work.id)
    assert _decision_activity_types(db_session, decision.id) == ["organization.decision.created.v1"]

    work_id = work.id
    decision_id = decision.id
    db_session.rollback()
    assert db_session.get(OrganizationalWorkItem, work_id) is None
    assert db_session.get(ExecutiveDecision, decision_id) is None
    assert _decision_activity_types(db_session, decision_id) == []


def test_decision_activity_failure_rolls_back_deadline_and_source_audit(
    raw_client,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_client.headers.update(_headers())
    work_id = _create_governed_work(raw_client, key="e3c-decision-rollback-001")
    decision = _decision_for_work(db_session, work_id)
    activities_before = db_session.exec(select(func.count()).select_from(OrganizationActivity)).one()
    audits_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()

    def fail_activity(*_args, **_kwargs):
        raise RuntimeError("simulated legacy Decision semantic Activity failure")

    monkeypatch.setattr(
        "app.services.organization_governance.stage_decision_deadline_activity",
        fail_activity,
    )
    with pytest.raises(RuntimeError, match="legacy Decision semantic Activity failure"):
        set_decision_deadline(
            db_session,
            decision,
            due_at=datetime.now(timezone.utc) + timedelta(hours=2),
            actor="e3c-owner",
        )

    db_session.refresh(decision)
    assert decision.due_at is None
    assert db_session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before


def test_postgresql_legacy_decision_deadline_activity_is_atomic_and_outer_rollback_leaves_no_residue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.getenv("ORGANIZATION_POSTGRES_TEST_URL")
    if not database_url:
        pytest.skip("ORGANIZATION_POSTGRES_TEST_URL is not configured")

    engine = create_engine(database_url)
    connection = engine.connect()
    outer = connection.begin()
    decision_id: UUID | None = None
    try:
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            suffix = uuid4().hex
            work = OrganizationalWorkItem(
                idempotency_key=f"e3c-pg-decision-work-{suffix}",
                title="E3C PostgreSQL Decision deadline",
                objective="Prove legacy Decision mutation and semantic Activity share the transaction.",
                department="Operations",
                authority_level="L3",
                assigned_position_key="coo",
                status="queued",
                created_by="e3c-pg-owner",
            )
            session.add(work)
            session.flush()
            decision = ExecutiveDecision(
                decision_key=f"e3c-pg-decision-{suffix}",
                work_item_id=work.id,
                authority_level="L3",
                requested_by_position="coo",
                decision_owner_position="ceo",
                title="E3C PostgreSQL Decision",
                question="Should this bounded internal matter proceed?",
                recommendation="Hold until governed review completes.",
                status="pending_ceo",
            )
            session.add(decision)
            session.commit()
            session.refresh(decision)
            decision_id = decision.id

            audits_before = session.exec(select(func.count()).select_from(AuditLog)).one()
            activities_before = session.exec(select(func.count()).select_from(OrganizationActivity)).one()

            def fail_activity(*_args, **_kwargs):
                raise RuntimeError("simulated PostgreSQL Decision semantic Activity failure")

            monkeypatch.setattr(
                "app.services.organization_governance.stage_decision_deadline_activity",
                fail_activity,
            )
            with pytest.raises(RuntimeError, match="PostgreSQL Decision semantic Activity failure"):
                set_decision_deadline(
                    session,
                    decision,
                    due_at=datetime.now(timezone.utc) + timedelta(hours=1),
                    actor="e3c-pg-owner",
                )
            session.refresh(decision)
            assert decision.due_at is None
            assert session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before
            assert session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before

            monkeypatch.undo()
            due_at = datetime.now(timezone.utc) + timedelta(hours=2)
            set_decision_deadline(session, decision, due_at=due_at, actor="e3c-pg-owner")
            assert _decision_activity_types(session, decision.id) == [
                "organization.decision.deadline.set.v1"
            ]
            session.refresh(decision)
            assert decision.due_at == due_at
    finally:
        outer.rollback()
        connection.close()

    try:
        with Session(engine) as verification:
            assert decision_id is not None
            assert verification.get(ExecutiveDecision, decision_id) is None
            assert verification.exec(
                select(func.count()).select_from(OrganizationActivity).where(
                    OrganizationActivity.source_object_type == "executive_decision",
                    OrganizationActivity.source_object_id == str(decision_id),
                )
            ).one() == 0
    finally:
        engine.dispose()

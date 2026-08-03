from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    BoardPacket,
    DelegationRecord,
    ExecutiveDecision,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationPosition,
    OrganizationalWorkItem,
    RiskEscalation,
)
from app.services import organization_governance as organization_service
from app.services.organization_governance import classify_authority
from app.tasks.organization_tasks import (
    execute_organization_work_item_task,
    scan_organization_work_task,
)


def _headers(role: str = "admin", user: str = "human-owner") -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _account(client) -> dict:
    response = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": "Phase 13 Employer", "primary_country": "Austria"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _case(client, account_id: str) -> dict:
    response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account_id}/cases",
        json={"case_reference": "ORG-CASE-001", "destination_country": "Germany"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_foundation_bootstrap_registers_executable_hierarchy(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    response = raw_client.post("/api/v1/organization/bootstrap")
    assert response.status_code == 201, response.text
    assert response.json()["positions_registered"] == 13

    positions = db_session.exec(select(OrganizationPosition)).all()
    by_key = {item.position_key: item for item in positions}
    assert by_key["ceo"].reports_to_position_key == "board"
    assert by_key["coo"].reports_to_position_key == "ceo"
    assert by_key["sales_summary"].reports_to_position_key == "coo"
    assert by_key["board"].authority_level == "L4"

    cards = Path(__file__).parents[3] / "agents" / "role_cards"
    for card in ("CEO.md", "CTO.md", "COO.md", "CMO.md", "CPO.md", "CFO.md", "CCO.md", "CHRO.md", "CLO.md"):
        assert (cards / card).is_file()


def test_authority_classifier_fails_closed_for_reserved_and_material_actions() -> None:
    assert classify_authority("internal.analysis") == ("L1", "routine")
    assert classify_authority("internal.analysis", {"risk_level": "moderate"}) == ("L2", "moderate")
    assert classify_authority("client.external_send") == ("L3", "high")
    assert classify_authority("market.entry") == ("L4", "critical")
    assert classify_authority("anything", {"requires_board_approval": True}) == ("L4", "critical")


def test_direct_reserved_work_also_creates_board_decision(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "direct-market-entry-001",
        "title": "Evaluate a new market entry",
        "objective": "Prepare the evidence and options for a human Board decision.",
        "department": "Executive",
        "action": "market.entry",
        "context": {"market": "example"},
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).one()
    assert decision.status == "pending_board"
    assert decision.decision_owner_position == "board"


def test_domain_event_routes_delegated_work_and_executes_routine_lane(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    account = _account(raw_client)
    case = _case(raw_client, account["id"])

    work = db_session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"]))
    ).first()
    assert work is not None
    assert work.authority_level == "L1"
    assert work.status == "queued"
    delegations = db_session.exec(select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)).all()
    assert {item.delegate_position_key for item in delegations} == {"sales_summary", "application_readiness"}

    executed = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    governance = output["governance"]
    assert governance["accountable_position_key"] == "coo"
    assert governance["authority_level"] == "L1"
    assert 0.0 < governance["confidence"] <= 1.0
    assert len(governance["organizational_action_output_ids"]) == 2
    assert "no external action" in governance["rollback_posture"].lower()
    assert governance["execution_attempt"] == 1
    assert governance["execution_token"]

    ledger = raw_client.get(f"/api/v1/organization/work-items/{work.id}/outputs")
    assert ledger.status_code == 200, ledger.text
    assert len(ledger.json()) == 2
    persisted = db_session.exec(
        select(OrganizationalActionOutput).where(OrganizationalActionOutput.work_item_id == work.id)
    ).all()
    assert len(persisted) == 2
    for action_output in persisted:
        assert action_output.accountable_position_key == "coo"
        assert action_output.authority_basis
        assert 0.0 < action_output.confidence <= 1.0
        assert action_output.confidence_basis
        assert json.loads(action_output.evidence_json)
        assert json.loads(action_output.impact_json)["client_facing"] is False
        assert "no external side effect" in action_output.rollback_posture.lower()

    repeated = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert repeated.status_code == 409
    db_session.expire_all()
    assert len(db_session.exec(
        select(OrganizationalActionOutput).where(OrganizationalActionOutput.work_item_id == work.id)
    ).all()) == 2
    attempts = db_session.exec(
        select(OrganizationExecutionAttempt).where(OrganizationExecutionAttempt.work_item_id == work.id)
    ).all()
    assert len(attempts) == 1
    assert attempts[0].status == "completed"


def test_board_can_cancel_queued_work_and_replay_is_blocked(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "cancel-queued-work-001",
        "title": "Prepare cancellable internal analysis",
        "objective": "Verify that the Human Board can stop queued organizational work.",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = created.json()["id"]

    raw_client.headers.update(_headers("operator", "operations-user"))
    forbidden = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/cancel",
        json={"reason": "Operator requested cancellation without Board authority."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers())
    cancelled = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/cancel",
        json={"reason": "Human owner stopped this work before execution began."},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancelled_by"] == "human-owner"
    assert cancelled.json()["cancel_requested_at"]
    assert cancelled.json()["cancelled_at"]

    replay = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert replay.status_code == 409
    attempts = raw_client.get(f"/api/v1/organization/work-items/{work_id}/attempts")
    assert attempts.status_code == 200
    assert attempts.json() == []

    audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_id == work_id,
            AuditLog.action == "organization_work_cancelled",
        )
    ).one()
    assert audit.actor == "human-owner"


def test_failed_execution_is_bounded_and_retries_without_replaying_completed_work(
    raw_client,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_client.headers.update(_headers())
    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    work = db_session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"])
        )
    ).one()
    work.max_execution_attempts = 2
    db_session.add(work)
    db_session.commit()

    original_record = organization_service._record_action_output
    calls = 0

    def fail_on_second_output(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated bounded worker failure")
        return original_record(*args, **kwargs)

    monkeypatch.setattr(organization_service, "_record_action_output", fail_on_second_output)
    with pytest.raises(RuntimeError, match="simulated bounded worker failure"):
        organization_service.execute_work_item(db_session, work, actor="test-worker")

    db_session.expire_all()
    failed = db_session.get(OrganizationalWorkItem, work.id)
    assert failed is not None
    assert failed.status == "retry_wait"
    assert failed.execution_attempts == 1
    assert failed.next_retry_at is not None
    assert "simulated bounded worker failure" in (failed.last_error or "")
    first_attempt = db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.work_item_id == work.id
        )
    ).one()
    assert first_attempt.status == "failed"

    completed_before_retry = db_session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == work.id,
            DelegationRecord.status == "completed",
        )
    ).all()
    assert len(completed_before_retry) == 1
    completed_output_id = db_session.exec(
        select(OrganizationalActionOutput.id).where(
            OrganizationalActionOutput.delegation_record_id == completed_before_retry[0].id
        )
    ).one()

    early_replay = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert early_replay.status_code == 409
    assert "not due" in early_replay.json()["detail"].lower()

    monkeypatch.setattr(organization_service, "_record_action_output", original_record)
    raw_client.headers.update(_headers("operator", "operations-user"))
    forbidden = raw_client.post(
        f"/api/v1/organization/work-items/{work.id}/retry",
        json={"reason": "Operator attempted to bypass the retry control."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers())
    retried = raw_client.post(
        f"/api/v1/organization/work-items/{work.id}/retry",
        json={"reason": "Human owner approved one bounded retry after reviewing the failure."},
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["status"] == "queued"
    assert retried.json()["execution_attempts"] == 1

    executed = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    assert executed.json()["execution_attempts"] == 2
    attempts = raw_client.get(f"/api/v1/organization/work-items/{work.id}/attempts")
    assert [item["status"] for item in attempts.json()] == ["failed", "completed"]

    db_session.expire_all()
    completed_output = db_session.get(OrganizationalActionOutput, completed_output_id)
    assert completed_output is not None
    assert json.loads(completed_output.output_json)["note"] != "Previously completed delegation reused during retry."


def test_retry_ceiling_cannot_be_reset_by_board_endpoint(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "retry-ceiling-work-001",
        "title": "Test exhausted work retry",
        "objective": "Confirm that even the Board endpoint cannot silently reset the retry budget.",
        "action": "internal.analysis",
        "max_execution_attempts": 1,
    })
    assert created.status_code == 201, created.text
    work = db_session.get(OrganizationalWorkItem, UUID(created.json()["id"]))
    assert work is not None
    work.status = "failed"
    work.execution_attempts = 1
    work.last_error = "terminal simulated failure"
    db_session.add(work)
    db_session.commit()

    response = raw_client.post(
        f"/api/v1/organization/work-items/{work.id}/retry",
        json={"reason": "Human owner inspected the exhausted retry budget."},
    )
    assert response.status_code == 409
    assert "exhausted" in response.json()["detail"].lower()


def test_work_scanner_dispatches_only_queued_and_due_retries(
    raw_client,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_client.headers.update(_headers())
    work_ids: list[UUID] = []
    for suffix in ("queued", "due", "future"):
        response = raw_client.post("/api/v1/organization/work-items", json={
            "idempotency_key": f"scanner-work-{suffix}-001",
            "title": f"Scanner work {suffix}",
            "objective": "Verify durable retry scheduling selects only eligible organizational work.",
            "action": "internal.analysis",
        })
        assert response.status_code == 201, response.text
        work_ids.append(UUID(response.json()["id"]))

    due = db_session.get(OrganizationalWorkItem, work_ids[1])
    future = db_session.get(OrganizationalWorkItem, work_ids[2])
    assert due is not None and future is not None
    due.status = "retry_wait"
    due.execution_attempts = 1
    due.next_retry_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    future.status = "retry_wait"
    future.execution_attempts = 1
    future.next_retry_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.add(due)
    db_session.add(future)
    db_session.commit()

    dispatched: list[str] = []
    monkeypatch.setattr(
        execute_organization_work_item_task,
        "delay",
        lambda work_id: dispatched.append(work_id),
    )
    result = scan_organization_work_task.run(limit=10)
    assert result["queued"] == 2
    assert set(dispatched) == {str(work_ids[0]), str(work_ids[1])}


def test_missing_work_item_output_ledger_returns_not_found(raw_client) -> None:
    raw_client.headers.update(_headers())
    response = raw_client.get(f"/api/v1/organization/work-items/{UUID(int=0)}/outputs")
    assert response.status_code == 404


def test_l4_event_reaches_human_board_and_records_decision(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    event = raw_client.post(
        "/api/v1/automation/events",
        json={
            "corporate_account_id": account["id"],
            "corporate_mobility_case_id": case["id"],
            "event_type": "case.status_changed",
            "idempotency_key": "phase13-market-entry-event",
            "payload": {"action": "market.entry", "risk_level": "critical"},
        },
    )
    assert event.status_code == 202, event.text
    work = db_session.exec(select(OrganizationalWorkItem).where(OrganizationalWorkItem.idempotency_key == f"organization:event:{event.json()['id']}")).one()
    assert work.authority_level == "L4"
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work.id)).one()
    risk = db_session.exec(select(RiskEscalation).where(RiskEscalation.work_item_id == work.id)).one()
    assert decision.status == "pending_board"
    assert risk.requires_board_attention is True

    packet = raw_client.get("/api/v1/organization/board-packet")
    assert packet.status_code == 200
    assert packet.json()["metrics"]["pending_board"] == 1

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-decision",
        json={"decision": "approved", "reason": "Operator attempted reserved approval."},
    )
    assert forbidden.status_code == 403

    executed = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_board"
    db_session.refresh(decision)
    decision_evidence = json.loads(decision.evidence_json)
    governed_output_evidence = [
        item for item in decision_evidence if item.get("type") == "organizational_action_outputs"
    ]
    assert len(governed_output_evidence) == 1
    assert len(governed_output_evidence[0]["ids"]) == 2
    assert 0.0 < governed_output_evidence[0]["aggregate_confidence"] <= 1.0

    raw_client.headers.update(_headers("admin", "human-owner"))
    approved = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-decision",
        json={"decision": "approved", "reason": "Human owner reviewed the evidence and accepts the exposure."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    assert approved.json()["decided_by"] == "human-owner"


def test_global_pause_holds_and_resume_requeues_work(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    paused = raw_client.post("/api/v1/organization/control", json={"status": "paused", "reason": "Board requested a controlled operating pause."})
    assert paused.status_code == 200, paused.text
    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    work = db_session.exec(select(OrganizationalWorkItem).where(OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"]))).one()
    assert work.status == "held"

    resumed = raw_client.post("/api/v1/organization/control", json={"status": "active", "reason": "Board completed its review and resumed execution."})
    assert resumed.status_code == 200, resumed.text
    db_session.refresh(work)
    assert work.status == "queued"


def test_board_can_override_l3_ceo_decision(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "override-l3-external-send-001",
        "title": "Send client-facing status update",
        "objective": "Communicate a routine case milestone to the client under executive oversight.",
        "department": "Communications",
        "action": "client.external_send",
        "risk_level": "high",
        "context": {"channel": "email", "milestone": "document_received"},
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).one()
    assert decision.authority_level == "L3"
    assert decision.status == "pending_ceo"
    assert decision.decision_owner_position == "ceo"

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-override",
        json={"decision": "approved", "reason": "Operator attempted Board override."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers("admin", "human-owner"))
    overridden = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-override",
        json={"decision": "approved", "reason": "Board overrides CEO lane and accepts the contractual exposure."},
    )
    assert overridden.status_code == 200, overridden.text
    assert overridden.json()["status"] == "approved"
    assert overridden.json()["decided_by"] == "human-owner"

    db_session.refresh(decision)
    audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "executive_decision",
            AuditLog.entity_id == str(decision.id),
            AuditLog.action == "executive_decision_overridden",
        )
    ).one()
    assert audit.actor == "human-owner"


def test_board_override_l4_delegates_to_normal_board_decision(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "override-l4-market-entry-001",
        "title": "Enter a new jurisdiction",
        "objective": "Board must approve market entry.",
        "department": "Executive",
        "action": "market.entry",
        "context": {"jurisdiction": "Singapore"},
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).one()
    assert decision.authority_level == "L4"
    assert decision.status == "pending_board"

    raw_client.headers.update(_headers("admin", "human-owner"))
    overridden = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-override",
        json={"decision": "approved", "reason": "Board approves market entry via override path."},
    )
    assert overridden.status_code == 200, overridden.text
    assert overridden.json()["status"] == "approved"


def test_position_suspend_and_resume(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    raw_client.post("/api/v1/organization/bootstrap")
    position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "sales_summary")
    ).one()

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/positions/{position.id}/suspend",
        json={"reason": "Operator attempted suspension."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers("admin", "human-owner"))
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{position.id}/suspend",
        json={"reason": "Sales intelligence agent paused pending data-quality review."},
    )
    assert suspended.status_code == 200, suspended.text
    assert suspended.json()["status"] == "suspended"
    assert suspended.json()["suspended_by"] == "human-owner"

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{position.id}/resume",
        json={"reason": "Data-quality review completed; agent cleared to operate."},
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["status"] == "active"
    assert resumed.json()["suspended_at"] is None


def test_suspended_position_is_not_delegated_new_work(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    raw_client.post("/api/v1/organization/bootstrap")
    position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "sales_summary")
    ).one()
    raw_client.post(
        f"/api/v1/organization/positions/{position.id}/suspend",
        json={"reason": "Suspend sales intelligence for this test."},
    )

    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    work = db_session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"]))
    ).one()
    delegations = db_session.exec(select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)).all()
    delegate_keys = {item.delegate_position_key for item in delegations}
    assert "sales_summary" not in delegate_keys
    assert "application_readiness" in delegate_keys


def test_suspended_position_holds_existing_delegation_during_execution(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    raw_client.post("/api/v1/organization/bootstrap")
    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    work = db_session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"]))
    ).one()
    delegations = db_session.exec(select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)).all()
    assert {item.delegate_position_key for item in delegations} == {"sales_summary", "application_readiness"}

    position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "sales_summary")
    ).one()
    raw_client.post(
        f"/api/v1/organization/positions/{position.id}/suspend",
        json={"reason": "Suspend sales intelligence after work was already routed."},
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    delegated_results = {result["agent"]: result for result in output["delegated_results"]}
    assert delegated_results["sales_summary_agent"]["status"] == "held"
    assert delegated_results["application_readiness_agent"]["status"] == "completed"

    db_session.refresh(work)
    held_delegation = db_session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == work.id,
            DelegationRecord.delegate_position_key == "sales_summary",
        )
    ).one()
    assert held_delegation.status == "held"
    assert held_delegation.result_ref == "position:suspended"


def test_work_item_deadline_and_decision_deadline(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "deadline-work-001",
        "title": "Deadline-bound operating review",
        "objective": "Review operating matter within a deadline.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    due = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat().replace("+00:00", "Z")

    response = raw_client.post(f"/api/v1/organization/work-items/{work_id}/deadline", json={"due_at": due})
    assert response.status_code == 200, response.text
    assert response.json()["due_at"] is not None

    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).first()
    assert decision is None


def test_escalation_moves_work_to_parent_position(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "escalate-work-001",
        "title": "Operational matter requiring CEO attention",
        "objective": "Route an operational matter up to the CEO.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work.assigned_position_key == "coo"

    response = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/escalate",
        json={"reason": "COO requests CEO guidance on operating boundary."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["assigned_position_key"] == "ceo"
    assert response.json()["escalated_at"] is not None

    risk = db_session.exec(select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)).one()
    assert risk.escalated_to_position_key == "ceo"
    assert risk.is_emergency is False


def test_emergency_escalation_reaches_board(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "emergency-work-001",
        "title": "Potential client harm scenario",
        "objective": "Emergency scenario must reach the Board immediately.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Operator attempted emergency escalation."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers("admin", "human-owner"))
    response = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Credible risk of client harm; require Board visibility."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["is_emergency"] is True
    assert response.json()["assigned_position_key"] == "board"

    risks = db_session.exec(select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)).all()
    assert any(risk.is_emergency and risk.requires_board_attention for risk in risks)

    audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "organizational_work_item",
            AuditLog.entity_id == str(work_id),
            AuditLog.action == "organization_work_emergency_escalated",
        )
    ).first()
    assert audit is not None
    assert audit.actor == "human-owner"


def test_overdue_scanner_escalates_work(raw_client, db_session: Session) -> None:
    from app.tasks.organization_tasks import scan_organization_deadlines_task

    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "overdue-work-001",
        "title": "Overdue operating task",
        "objective": "Task with a deadline in the past should be escalated by scanner.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    past_due = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    deadline = raw_client.post(f"/api/v1/organization/work-items/{work_id}/deadline", json={"due_at": past_due})
    assert deadline.status_code == 200, deadline.text

    result = scan_organization_deadlines_task(overdue_seconds=0, reminder_seconds=0)
    assert result["escalated"] >= 1

    db_session.refresh(db_session.get(OrganizationalWorkItem, work_id))
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work.assigned_position_key == "ceo"
    assert work.escalated_at is not None


def test_decision_deadline_sets_reminder_track(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "decision-deadline-001",
        "title": "CEO decision with deadline",
        "objective": "Decision requires a deadline.",
        "department": "Communications",
        "action": "client.external_send",
        "risk_level": "high",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).one()
    due = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    response = raw_client.post(f"/api/v1/organization/decisions/{decision.id}/deadline", json={"due_at": due})
    assert response.status_code == 200, response.text
    assert response.json()["due_at"] is not None


def test_board_can_create_on_demand_board_packet(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "board-packet-market-entry-001",
        "title": "Enter a new jurisdiction",
        "objective": "Board must review market entry.",
        "department": "Executive",
        "action": "market.entry",
    })
    assert created.status_code == 201, created.text

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post("/api/v1/organization/board-packets", json={"packet_type": "on_demand"})
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers("admin", "human-owner"))
    packet = raw_client.post("/api/v1/organization/board-packets", json={"packet_type": "on_demand"})
    assert packet.status_code == 201, packet.text
    assert packet.json()["packet_type"] == "on_demand"
    assert packet.json()["prepared_by_position"] == "ceo"
    assert packet.json()["status"] == "published"
    content = json.loads(packet.json()["content_json"])
    assert "ceo_recommendation" in content
    assert "approval_requested" in content
    assert "evidence_summary" in content
    assert "alternatives" in content
    assert "expected_impact" in content
    assert "dissenting_views" in content
    assert "cost_or_resource_impact" in content
    assert "urgency" in content
    assert "decisions_for_board" in content
    assert any("market.entry" in item["title"].lower() or "jurisdiction" in item["title"].lower() for item in content["decisions_for_board"])

    listed = raw_client.get("/api/v1/organization/board-packets")
    assert listed.status_code == 200
    assert any(item["id"] == packet.json()["id"] for item in listed.json())

    snapshot = raw_client.get("/api/v1/organization/board-packet")
    assert snapshot.status_code == 200
    assert snapshot.json()["metrics"]["pending_board"] >= 1


def test_emergency_creates_incident_board_packet(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "emergency-board-packet-001",
        "title": "Client harm risk",
        "objective": "Emergency must trigger incident Board Packet.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    raw_client.headers.update(_headers("admin", "human-owner"))
    response = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Credible client harm risk; escalate to Board and generate incident packet."},
    )
    assert response.status_code == 200, response.text

    packets = db_session.exec(select(BoardPacket).where(BoardPacket.packet_type == "incident")).all()
    assert len(packets) >= 1
    incident = packets[0]
    content = json.loads(incident.content_json)
    assert content["urgency"] == "immediate"
    assert any(item["work_item_id"] == str(work_id) for item in content["emergencies"])


def test_recurring_board_packet_task_publishes_packet(raw_client, db_session: Session) -> None:
    from app.tasks.organization_tasks import generate_recurring_board_packet_task

    raw_client.headers.update(_headers())
    raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "recurring-packet-001",
        "title": "Routine operating review",
        "objective": "Provide content for a recurring Board Packet.",
        "department": "Operations",
        "action": "internal.analysis",
    })

    result = generate_recurring_board_packet_task("daily")
    assert "packet_id" in result
    packet = db_session.get(BoardPacket, UUID(result["packet_id"]))
    assert packet is not None
    assert packet.packet_type == "daily"
    assert packet.status == "published"

    repeated = generate_recurring_board_packet_task("daily")
    assert repeated["packet_id"] == result["packet_id"]
    assert len(db_session.exec(select(BoardPacket).where(BoardPacket.packet_type == "daily")).all()) == 1


def test_board_packet_recurring_schedules_are_registered() -> None:
    from app.core.celery_app import celery_app

    schedule = celery_app.conf.beat_schedule
    assert schedule["generate-daily-board-packet"]["args"] == ("daily",)
    assert schedule["generate-weekly-board-packet"]["args"] == ("weekly",)

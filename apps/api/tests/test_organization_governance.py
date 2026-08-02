from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    DelegationRecord,
    ExecutiveDecision,
    OrganizationPosition,
    OrganizationalWorkItem,
    RiskEscalation,
)
from app.services.organization_governance import classify_authority


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
    repeated = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert repeated.status_code == 409


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

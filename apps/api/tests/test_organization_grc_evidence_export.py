from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog, ExecutiveDecision, OrganizationActivity, OrganizationBlocker,
    OrganizationControl, OrganizationHumanAction, OrganizationHumanActionRequest,
    OrganizationRecordReference, OrganizationalWorkItem, RiskEscalation,
)
from app.services.organization_command import NotFound
from app.services.organization_decision import create_executive_decision
from app.services.organization_grc_evidence_export import export_grc_risk_evidence
from app.services.organization_human_action import create_human_action_request, complete_human_action_request
from app.services.organization_reference import create_record_reference
from app.services.organization_work import open_blocker
from tests.test_organization_autonomy_promotion_policy import _board_context
from tests.test_organization_grc_traceability import _risk, _work


def test_grc_evidence_export_is_exact_tenant_scoped_and_read_only(client, db_session: Session) -> None:
    board = _board_context()
    work = _work(db_session, tenant_key="default", key="18d-work")
    other_work = _work(db_session, tenant_key="other", key="18d-other-work")
    risk = _risk(db_session, key="18d-risk", work_item_id=work.id)
    adjacent_risk = _risk(db_session, key="18d-adjacent-risk", work_item_id=work.id)
    other_risk = _risk(db_session, key="18d-other-risk", work_item_id=other_work.id)
    control = OrganizationControl(control_key="global", status="active", changed_by="pytest")
    global_audit = AuditLog(
        action="unrelated", entity_type="legacy", reason="private global body must not export",
    )
    db_session.add(control)
    db_session.add(global_audit)
    db_session.commit()

    decision = create_executive_decision(
        db_session, board, decision_key="18d-governance-decision", decision_type="exception",
        authority_level="L4", requested_by_position="security_grc_lead",
        decision_owner_position="board", title="Review the risk", question="What action?",
        recommendation="Hold", work_item_id=work.id,
        source_object_type="risk_escalation", source_object_id=str(risk.id),
    )
    neighbour = create_executive_decision(
        db_session, board, decision_key="18d-neighbour", decision_type="risk",
        authority_level="L4", requested_by_position="security_grc_lead",
        decision_owner_position="board", title="Other work", question="Other matter?",
        recommendation="Hold", work_item_id=work.id,
    )
    adjacent_decision = create_executive_decision(
        db_session, board, decision_key="18d-adjacent-risk-decision", decision_type="risk",
        authority_level="L4", requested_by_position="security_grc_lead",
        decision_owner_position="board", title="Another risk", question="Another response?",
        recommendation="Hold", work_item_id=work.id,
        source_object_type="risk_escalation", source_object_id=str(adjacent_risk.id),
    )
    blocker = open_blocker(
        db_session, board, blocker_key="18d-blocker", blocker_type="safety",
        severity="high", title="Response blocked", description="Review required",
        work_item_id=work.id, risk_escalation_id=risk.id, decision_id=decision.id,
    )
    request = create_human_action_request(
        db_session, board, request_key="18d-request", request_type="approval",
        title="Review", instructions="Inspect exact risk lineage", required_role="admin",
        assigned_human_id=board.actor_id, work_item_id=work.id,
        decision_id=decision.id, blocker_id=blocker.id,
    )
    _, action = complete_human_action_request(
        db_session, board, request_id=request.id, action_key="18d-action",
        action_type="approved", outcome="review accepted",
        occurred_at=datetime(2026, 9, 29, 10, tzinfo=timezone.utc),
        reason="Human review completed, decision remains pending.",
    )
    mapping = create_record_reference(
        db_session, board, reference_key="18d-control", reference_role="governance_mapping",
        target_type="organization_control", target_id=control.id,
        risk_escalation_id=risk.id, label="Control is relevant for review, not certified effective.",
    )
    withdrawn = create_record_reference(
        db_session, board, reference_key="18d-control-withdrawn", reference_role="governance_mapping",
        target_type="organization_control", target_id=control.id,
        risk_escalation_id=risk.id, label="The mapping was withdrawn.",
        supersedes_reference_id=mapping.id, metadata={"mapping_state": "withdrawn"},
    )
    evidence = create_record_reference(
        db_session, board, reference_key="18d-declared-audit", reference_role="evidence",
        target_type="audit_log", target_id=global_audit.id, blocker_id=blocker.id,
        label="Declared pointer only; no tenant proof from the global target.",
    )
    models = (
        OrganizationalWorkItem, RiskEscalation, ExecutiveDecision, OrganizationBlocker,
        OrganizationHumanActionRequest, OrganizationHumanAction, OrganizationRecordReference,
        OrganizationActivity, AuditLog,
    )
    before = {model: len(db_session.exec(select(model)).all()) for model in models}

    route = f"/api/v1/organization/grc/risks/{risk.id}/evidence-export"
    denied = client.get(route, headers={"X-GMAI-Role": "operator", "X-GMAI-User": "operator"})
    assert denied.status_code == 403
    response = client.get(route)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"].endswith(f'grc-risk-{risk.id}.json"')
    body = response.json()
    assert body == client.get(route).json()
    assert body["tenant_key"] == "default"
    assert body["risk_id"] == str(risk.id)
    assert body["evidence_validity"] == "not_assessed"
    assert body["coverage"] == "explicitly_linked_records_only"
    assert any("recorded claims" in limitation for limitation in body["limitations"])
    entries = {(entry["record_type"], entry["record_id"]): entry for entry in body["source_records"]}
    assert entries[("risk_escalation", str(risk.id))]["record_fingerprint"] is None
    assert entries[("executive_decision", str(decision.id))]["status"] == "pending_board"
    assert ("executive_decision", str(neighbour.id)) not in entries
    assert ("risk_escalation", str(adjacent_risk.id)) not in entries
    assert ("executive_decision", str(adjacent_decision.id)) not in entries
    assert entries[("organization_blocker", str(blocker.id))]["related_record_id"] == str(risk.id)
    assert entries[("organization_human_action_request", str(request.id))]["related_record_id"] == str(blocker.id)
    assert entries[("organization_human_action", str(action.id))]["related_record_id"] == str(request.id)
    assert entries[("organization_record_reference", str(mapping.id))]["supersedes_record_id"] is None
    assert entries[("organization_record_reference", str(withdrawn.id))]["status"] == "withdrawn"
    assert entries[("organization_record_reference", str(withdrawn.id))]["supersedes_record_id"] == str(mapping.id)
    assert entries[("organization_record_reference", str(evidence.id))]["target_id"] == str(global_audit.id)
    assert all(entry["record_type"] != "audit_log" for entry in body["source_records"])
    assert "private global body must not export" not in response.text
    activities = [entry for entry in body["source_records"] if entry["record_type"] == "organization_activity"]
    assert activities and all(entry["record_fingerprint"] for entry in activities)
    assert all(entry["source_object_version"] for entry in activities)
    assert all(entry["related_record_id"] != str(neighbour.id) for entry in activities)
    assert all(entry["related_record_id"] != str(adjacent_decision.id) for entry in activities)
    assert before == {model: len(db_session.exec(select(model)).all()) for model in models}

    with pytest.raises(NotFound):
        export_grc_risk_evidence(db_session, _board_context("other"), risk_id=risk.id)
    assert client.get(f"/api/v1/organization/grc/risks/{other_risk.id}/evidence-export").status_code == 404
    assert client.get("/api/v1/organization/grc/risks/00000000-0000-0000-0000-000000000000/evidence-export").status_code == 404

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, update
from sqlmodel import Session, func, select

from app.models.domain import (
    AutomationEvent,
    BoardPacket,
    CorporateMobilityCase,
    DelegationRecord,
    ExecutiveDecision,
    OrganizationControl,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
    OrganizationPosition,
    RiskEscalation,
)
from app.schemas import ControlledAgentRunRequest
from app.services.audit_log import record_audit
from app.services.controlled_agents import run_controlled_agent


SOURCE = "ai_organization_v13.0"

POSITION_SPECS = (
    ("board", "Human Board", "Board", None, "L4", None),
    ("ceo", "Chief Executive Officer Agent", "Executive", "board", "L3", "CEO.md"),
    ("cto", "Chief Technology Officer Agent", "Technology", "ceo", "L3", "CTO.md"),
    ("coo", "Chief Operating Officer Agent", "Operations", "ceo", "L3", "COO.md"),
    ("cmo", "Chief Marketing Officer Agent", "Marketing", "ceo", "L3", "CMO.md"),
    ("cpo", "Chief Product Officer Agent", "Product", "ceo", "L3", "CPO.md"),
    ("cfo", "Chief Financial Officer Agent", "Finance", "ceo", "L3", "CFO.md"),
    ("cco", "Chief Communications Officer Agent", "Communications", "ceo", "L3", "CCO.md"),
    ("chro", "Chief Human Resources Officer Agent", "People", "ceo", "L3", "CHRO.md"),
    ("clo", "Chief Legal Officer Agent", "Legal", "ceo", "L3", "CLO.md"),
    ("head_of_product", "Head of Product Agent", "Product", "cpo", "L2", "Head_of_Product.md"),
    ("sales_summary", "Sales Intelligence Agent", "Operations", "coo", "L1", "Sales_Summary_Agent.md"),
    ("application_readiness", "Application Readiness Agent", "Operations", "coo", "L1", "Application_Readiness_Agent.md"),
)

BOARD_RESERVED_ACTIONS = {
    "contract.sign",
    "executive.authority.change",
    "market.entry",
    "pricing.change",
    "production.irreversible",
    "spend.above_threshold",
}
EXECUTIVE_ACTIONS = {
    "authority.submit",
    "client.external_send",
    "deployment.production",
    "payment.initiate",
    "policy.publish",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


class WorkCancellationRequested(RuntimeError):
    """Internal cooperative stop signal for an in-flight organizational task."""


def _output_confidence(
    result: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> tuple[float, str]:
    output = result.get("output") if isinstance(result.get("output"), dict) else result
    raw = output.get("confidence") if isinstance(output, dict) else None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return (
            round(max(0.0, min(1.0, float(raw))), 4),
            "Agent supplied a bounded numeric confidence value.",
        )
    if isinstance(raw, str):
        mapped = {"high": 0.85, "medium": 0.65, "low": 0.35}.get(raw.lower())
        if mapped is not None:
            return mapped, f"Mapped the agent's qualitative '{raw.lower()}' confidence label."
    if result.get("status") == "held":
        return 0.0, "No analytical result was produced because execution was held."
    if evidence:
        return 0.5, "Conservative default: provenance exists but the result supplied no confidence."
    return 0.25, "Conservative default: neither evidence provenance nor explicit confidence was supplied."


def _output_evidence(
    work: OrganizationalWorkItem,
    *,
    result_ref: str,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    if work.automation_event_id:
        evidence.append({"type": "automation_event", "id": str(work.automation_event_id)})
    if work.corporate_mobility_case_id:
        evidence.append({"type": "corporate_mobility_case", "id": str(work.corporate_mobility_case_id)})
    if work.lead_id:
        evidence.append({"type": "lead", "id": str(work.lead_id)})
    if result_ref.startswith("agent-run:"):
        evidence.append({
            "type": "agent_run",
            "id": result_ref.removeprefix("agent-run:"),
            "review_state": "human_review_required",
        })
    return evidence


def _record_action_output(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    delegation: DelegationRecord,
    result: dict[str, Any],
    result_ref: str,
    actor: str,
) -> OrganizationalActionOutput:
    output_key = f"organization-output:{delegation.id}"
    action_output = session.exec(
        select(OrganizationalActionOutput).where(OrganizationalActionOutput.output_key == output_key)
    ).first()
    evidence = _output_evidence(work, result_ref=result_ref)
    confidence, confidence_basis = _output_confidence(result, evidence)
    result_payload = result.get("output") if isinstance(result.get("output"), dict) else result
    blocked_actions = result_payload.get("blocked_actions", []) if isinstance(result_payload, dict) else []
    impact = {
        "client_facing": False,
        "human_review_required": bool(
            result_payload.get("human_review_required", True)
            if isinstance(result_payload, dict)
            else True
        ),
        "blocked_actions": blocked_actions,
        "workflow_effect": "analysis_recorded" if delegation.status == "completed" else "execution_held",
    }
    rollback_posture = (
        "Resume the accountable position and replay this delegation; no external side effect occurred."
        if delegation.status == "held"
        else "Discard this internal output and reset the delegation to queued; no external side effect occurred."
    )
    if action_output is None:
        action_output = OrganizationalActionOutput(
            output_key=output_key,
            work_item_id=work.id,
            delegation_record_id=delegation.id,
            accountable_position_key=delegation.delegator_position_key,
            authority_basis=delegation.authority_basis,
            rollback_posture=rollback_posture,
        )
    action_output.evidence_json = _json(evidence)
    action_output.confidence = confidence
    action_output.confidence_basis = confidence_basis
    action_output.impact_json = _json(impact)
    action_output.rollback_posture = rollback_posture
    action_output.output_json = _json(result)
    action_output.status = delegation.status
    action_output.updated_at = _now()
    session.add(action_output)
    session.flush()
    record_audit(
        session,
        action="organizational_action_output_recorded",
        entity_type="organizational_action_output",
        entity_id=action_output.id,
        after_state={
            "work_item_id": str(work.id),
            "accountable_position_key": action_output.accountable_position_key,
            "confidence": confidence,
            "confidence_basis": confidence_basis,
            "status": action_output.status,
        },
        actor=actor,
        source=SOURCE,
    )
    return action_output


def ensure_foundation_positions(session: Session, *, actor: str = "system") -> list[OrganizationPosition]:
    positions: list[OrganizationPosition] = []
    for key, title, department, reports_to, authority, role_card in POSITION_SPECS:
        position = session.exec(
            select(OrganizationPosition).where(
                OrganizationPosition.position_key == key,
                OrganizationPosition.version == 1,
            )
        ).first()
        if position is None:
            position = OrganizationPosition(
                position_key=key,
                title=title,
                department=department,
                reports_to_position_key=reports_to,
                role_card_name=role_card,
                authority_level=authority,
                contract_json=_json({
                    "may_act_within": authority,
                    "must_escalate_above": authority,
                    "evidence_required": True,
                    "audit_required": True,
                }),
                created_by=actor,
            )
            session.add(position)
            session.flush()
            record_audit(
                session,
                action="organization_position_registered",
                entity_type="organization_position",
                entity_id=position.id,
                after_state={"position_key": key, "authority_level": authority},
                actor=actor,
                source=SOURCE,
            )
        positions.append(position)
    control = session.exec(
        select(OrganizationControl).where(OrganizationControl.control_key == "global")
    ).first()
    if control is None:
        session.add(OrganizationControl(control_key="global", changed_by=actor))
    return positions


def _position_by_key(session: Session, position_key: str) -> OrganizationPosition | None:
    return session.exec(
        select(OrganizationPosition).where(
            OrganizationPosition.position_key == position_key,
            OrganizationPosition.version == 1,
        )
    ).first()


def _is_suspended(position: OrganizationPosition | None) -> bool:
    return position is not None and position.status == "suspended"


def suspend_position(
    session: Session,
    position: OrganizationPosition,
    *,
    reason: str,
    actor: str,
) -> OrganizationPosition:
    if position.position_key == "board":
        raise ValueError("The human Board position cannot be suspended by the organization")
    before = position.status
    position.status = "suspended"
    position.suspended_at = _now()
    position.suspended_by = actor
    position.suspended_reason = reason.strip()
    position.updated_at = _now()
    session.add(position)
    record_audit(
        session,
        action="organization_position_suspended",
        entity_type="organization_position",
        entity_id=position.id,
        before_state={"status": before},
        after_state={
            "status": position.status,
            "suspended_by": actor,
            "suspended_reason": position.suspended_reason,
        },
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(position)
    return position


def resume_position(
    session: Session,
    position: OrganizationPosition,
    *,
    reason: str,
    actor: str,
) -> OrganizationPosition:
    if position.status != "suspended":
        raise ValueError("Position is not suspended")
    before = position.status
    position.status = "active"
    position.suspended_at = None
    position.suspended_by = None
    position.suspended_reason = None
    position.updated_at = _now()
    session.add(position)
    record_audit(
        session,
        action="organization_position_resumed",
        entity_type="organization_position",
        entity_id=position.id,
        before_state={"status": before},
        after_state={"status": position.status},
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(position)
    return position


def board_override_decision(
    session: Session,
    decision: ExecutiveDecision,
    *,
    outcome: str,
    reason: str,
    actor: str,
) -> ExecutiveDecision:
    if outcome not in {"approved", "rejected", "returned"}:
        raise ValueError("Unsupported override outcome")
    if decision.authority_level == "L4":
        # L4 is Board-reserved; an override is a normal Board decision.
        return decide_executive_decision(
            session,
            decision,
            outcome=outcome,
            reason=reason,
            actor=actor,
            board_actor=True,
        )
    if decision.authority_level != "L3":
        raise ValueError("Board override applies to L3 executive decisions only")
    before_status = decision.status
    decision.status = outcome
    decision.decided_by = actor
    decision.decision_reason = reason.strip()
    decision.decided_at = _now()
    decision.updated_at = _now()
    session.add(decision)
    work = session.get(OrganizationalWorkItem, decision.work_item_id) if decision.work_item_id else None
    if work is not None:
        work.status = "completed" if outcome == "approved" else outcome
        work.completed_at = _now()
        work.updated_at = _now()
        session.add(work)
    record_audit(
        session,
        action="executive_decision_overridden",
        entity_type="executive_decision",
        entity_id=decision.id,
        before_state={"status": before_status},
        after_state={"status": outcome, "decided_by": actor},
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(decision)
    return decision


_POSITION_PARENTS = {key: reports_to for key, _, _, reports_to, _, _ in POSITION_SPECS if reports_to is not None}


def _parent_position(position_key: str) -> str | None:
    return _POSITION_PARENTS.get(position_key)


def set_work_deadline(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    due_at: datetime,
    actor: str,
) -> OrganizationalWorkItem:
    if work.status in {"completed", "rejected", "returned"}:
        raise ValueError("Cannot set deadline on a closed work item")
    work.due_at = due_at
    work.updated_at = _now()
    session.add(work)
    record_audit(
        session,
        action="organization_work_deadline_set",
        entity_type="organizational_work_item",
        entity_id=work.id,
        after_state={"due_at": due_at.isoformat()},
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    return work


def set_decision_deadline(
    session: Session,
    decision: ExecutiveDecision,
    *,
    due_at: datetime,
    actor: str,
) -> ExecutiveDecision:
    if decision.status not in {"pending_ceo", "pending_board"}:
        raise ValueError("Cannot set deadline on a decided decision")
    decision.due_at = due_at
    decision.updated_at = _now()
    session.add(decision)
    record_audit(
        session,
        action="executive_decision_deadline_set",
        entity_type="executive_decision",
        entity_id=decision.id,
        after_state={"due_at": due_at.isoformat()},
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(decision)
    return decision


def escalate_work_item(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    reason: str,
    actor: str,
    emergency: bool = False,
) -> OrganizationalWorkItem:
    if work.status in {"completed", "rejected", "returned"}:
        raise ValueError("Cannot escalate a closed work item")
    current_owner = work.assigned_position_key
    parent = _parent_position(current_owner)
    if parent is None:
        raise ValueError(f"Position {current_owner} has no parent; cannot escalate further")
    before_owner = current_owner
    work.assigned_position_key = parent
    work.escalated_at = _now()
    work.updated_at = _now()
    if emergency:
        work.is_emergency = True
    session.add(work)

    # Update or create decision ownership if this is L3/L4 work.
    decision = session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work.id)
    ).first()
    if decision is not None and decision.status in {"pending_ceo", "pending_board"}:
        decision.decision_owner_position = parent
        decision.updated_at = _now()
        session.add(decision)

    # Open/refresh a risk escalation record.
    risk = session.exec(
        select(RiskEscalation).where(RiskEscalation.work_item_id == work.id, RiskEscalation.status == "open")
    ).first()
    if risk is None:
        risk = RiskEscalation(
            risk_key=f"risk:{work.id}:escalation",
            work_item_id=work.id,
            category="governance" if not emergency else "emergency",
            severity="critical" if emergency else work.risk_level,
            title=f"{'Emergency escalation' if emergency else 'Escalation'}: {work.title}",
            description=f"Escalated from {before_owner} to {parent}. Reason: {reason.strip()}",
            evidence_json=_json([{"from": before_owner, "to": parent, "reason": reason.strip()}]),
            containment_json=_json(["Awaiting parent position review"]),
            accountable_position_key=parent,
            escalated_to_position_key=parent,
            requires_board_attention=parent == "board" or emergency,
            is_emergency=emergency,
        )
        session.add(risk)
    else:
        risk.escalated_to_position_key = parent
        risk.requires_board_attention = parent == "board" or emergency or risk.requires_board_attention
        risk.is_emergency = risk.is_emergency or emergency
        risk.updated_at = _now()
        session.add(risk)

    record_audit(
        session,
        action="organization_work_escalated" if not emergency else "organization_work_emergency_escalated",
        entity_type="organizational_work_item",
        entity_id=work.id,
        before_state={"assigned_position_key": before_owner},
        after_state={"assigned_position_key": parent, "is_emergency": work.is_emergency},
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    return work


def mark_work_emergency(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    reason: str,
    actor: str,
) -> OrganizationalWorkItem:
    if work.is_emergency:
        return work
    work.is_emergency = True
    work.updated_at = _now()
    session.add(work)
    record_audit(
        session,
        action="organization_work_marked_emergency",
        entity_type="organizational_work_item",
        entity_id=work.id,
        after_state={"is_emergency": True},
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    # Escalate all the way to Board immediately.
    while work.assigned_position_key != "board":
        try:
            work = escalate_work_item(session, work, reason=reason, actor=actor, emergency=True)
        except ValueError:
            break
    create_board_packet(session, packet_type="incident", actor=actor, trigger_key=str(work.id))
    session.refresh(work)
    return work


def classify_authority(action: str, payload: dict[str, Any] | None = None) -> tuple[str, str]:
    data = payload or {}
    risk = str(data.get("risk_level") or data.get("severity") or "routine").lower()
    if bool(data.get("requires_board_approval")) or action in BOARD_RESERVED_ACTIONS or risk == "critical":
        return "L4", "critical"
    if action in EXECUTIVE_ACTIONS or risk in {"high", "material"}:
        return "L3", "high"
    if risk in {"medium", "moderate"} or bool(data.get("manager_review_required")):
        return "L2", "moderate"
    return "L1", "routine"


def route_automation_event(
    session: Session,
    event: AutomationEvent,
    case: CorporateMobilityCase,
    *,
    actor: str,
) -> tuple[OrganizationalWorkItem, bool]:
    key = f"organization:event:{event.id}"
    existing = session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.idempotency_key == key)
    ).first()
    if existing is not None:
        return existing, False

    ensure_foundation_positions(session, actor=actor)
    control = session.exec(
        select(OrganizationControl).where(OrganizationControl.control_key == "global")
    ).first()
    payload = _load(event.payload_json, {})
    authority, risk = classify_authority(str(payload.get("action") or event.event_type), payload)
    status = "held" if control and control.status == "paused" else "queued"
    work = OrganizationalWorkItem(
        idempotency_key=key,
        automation_event_id=event.id,
        lead_id=case.employee_lead_id,
        corporate_account_id=event.corporate_account_id,
        corporate_mobility_case_id=case.id,
        title=f"{case.case_reference}: {event.event_type}",
        objective="Assess the event, summarize commercial context, and identify readiness blockers.",
        department="Operations",
        authority_level=authority,
        status=status,
        assigned_position_key="coo",
        risk_level=risk,
        context_json=_json({
            "event_type": event.event_type,
            "case_reference": case.case_reference,
            "destination_country": case.destination_country,
            "facts": payload,
        }),
        created_by=actor,
    )
    session.add(work)
    session.flush()
    delegates = (
        ("sales_summary", "Summarize commercial and client context."),
        ("application_readiness", "Assess operational readiness and blockers."),
    )
    for delegate, task in delegates:
        position = _position_by_key(session, delegate)
        if _is_suspended(position):
            continue
        session.add(DelegationRecord(
            work_item_id=work.id,
            delegator_position_key="coo",
            delegate_position_key=delegate,
            task=task,
            authority_basis="COO L3 operating mandate; delegated analysis only.",
        ))

    if authority in {"L3", "L4"}:
        owner = "board" if authority == "L4" else "ceo"
        decision = ExecutiveDecision(
            decision_key=f"decision:{work.id}",
            work_item_id=work.id,
            authority_level=authority,
            requested_by_position="coo",
            decision_owner_position=owner,
            title=f"Decision required: {work.title}",
            question="Should the organization proceed after reviewing the evidence, alternatives, and risk?",
            recommendation="Hold execution until the accountable decision owner reviews the completed analysis.",
            alternatives_json=_json(["proceed", "revise", "reject"]),
            evidence_json=_json([{"automation_event_id": str(event.id)}]),
            impact_json=_json({"risk_level": risk, "case_reference": case.case_reference}),
            status="pending_board" if authority == "L4" else "pending_ceo",
        )
        session.add(decision)
        session.add(RiskEscalation(
            risk_key=f"risk:{work.id}",
            work_item_id=work.id,
            category="governance",
            severity=risk,
            title=f"{authority} authority boundary reached",
            description="The requested action exceeds delegated execution authority.",
            evidence_json=_json([{"event_id": str(event.id), "action": payload.get("action")}]),
            containment_json=_json(["Execution held", f"Escalated to {owner}"]),
            accountable_position_key="coo",
            escalated_to_position_key=owner,
            requires_board_attention=authority == "L4",
        ))

    record_audit(
        session,
        action="organization_work_routed",
        entity_type="organizational_work_item",
        entity_id=work.id,
        after_state={"authority_level": authority, "status": status, "assigned_to": "coo"},
        actor=actor,
        source=SOURCE,
    )
    return work, True


def _claim_work_execution(
    session: Session,
    work_item_id: UUID,
    *,
    actor: str,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt]:
    now = _now()
    token = str(uuid4())
    eligible_status = or_(
        OrganizationalWorkItem.status == "queued",
        and_(
            OrganizationalWorkItem.status == "retry_wait",
            or_(
                OrganizationalWorkItem.next_retry_at.is_(None),
                OrganizationalWorkItem.next_retry_at <= now,
            ),
        ),
    )
    statement = (
        update(OrganizationalWorkItem)
        .where(
            OrganizationalWorkItem.id == work_item_id,
            eligible_status,
            OrganizationalWorkItem.execution_attempts < OrganizationalWorkItem.max_execution_attempts,
            OrganizationalWorkItem.cancel_requested_at.is_(None),
        )
        .values(
            status="running",
            execution_attempts=OrganizationalWorkItem.execution_attempts + 1,
            execution_token=token,
            execution_started_at=now,
            next_retry_at=None,
            last_error=None,
            updated_at=now,
        )
        .execution_options(synchronize_session=False)
    )
    result = session.exec(statement)
    if result.rowcount != 1:
        session.rollback()
        current = session.get(OrganizationalWorkItem, work_item_id)
        if current is None:
            raise ValueError("Organizational work item not found")
        if current.cancel_requested_at is not None or current.status == "cancelled":
            raise ValueError("Work item has been cancelled")
        if current.execution_attempts >= current.max_execution_attempts:
            raise ValueError("Work item has exhausted its execution attempts")
        if current.status == "retry_wait":
            raise ValueError("Work item retry is not due yet")
        raise ValueError("Work item is already running or is not executable")

    session.expire_all()
    claimed = session.get(OrganizationalWorkItem, work_item_id)
    if claimed is None:
        session.rollback()
        raise ValueError("Organizational work item not found")
    attempt = OrganizationExecutionAttempt(
        attempt_key=f"organization-attempt:{claimed.id}:{claimed.execution_attempts}",
        work_item_id=claimed.id,
        attempt_number=claimed.execution_attempts,
        execution_token=token,
        actor=actor,
    )
    session.add(attempt)
    record_audit(
        session,
        action="organization_work_execution_started",
        entity_type="organizational_work_item",
        entity_id=claimed.id,
        after_state={
            "attempt": claimed.execution_attempts,
            "max_attempts": claimed.max_execution_attempts,
            "execution_token": token,
        },
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(claimed)
    session.refresh(attempt)
    return claimed, attempt


def _raise_if_cancelled(session: Session, work: OrganizationalWorkItem) -> None:
    session.refresh(work)
    if work.cancel_requested_at is not None:
        raise WorkCancellationRequested(work.cancellation_reason or "Cancellation requested")


def _mark_execution_cancelled(
    session: Session,
    *,
    work_item_id: UUID,
    execution_token: str,
    actor: str,
) -> OrganizationalWorkItem:
    session.rollback()
    work = session.get(OrganizationalWorkItem, work_item_id)
    if work is None:
        raise ValueError("Organizational work item not found")
    now = _now()
    work.status = "cancelled"
    work.cancelled_at = now
    work.completed_at = now
    work.execution_started_at = None
    work.next_retry_at = None
    work.updated_at = now
    session.add(work)
    attempt = session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.execution_token == execution_token
        )
    ).first()
    if attempt is not None:
        attempt.status = "cancelled"
        attempt.completed_at = now
        session.add(attempt)
    delegations = session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == work.id,
            DelegationRecord.status.in_(["queued", "running"]),
        )
    ).all()
    for delegation in delegations:
        delegation.status = "cancelled"
        delegation.completed_at = now
        delegation.result_ref = "work-item:cancelled"
        session.add(delegation)
    record_audit(
        session,
        action="organization_work_cancelled",
        entity_type="organizational_work_item",
        entity_id=work.id,
        after_state={"status": "cancelled", "attempt": work.execution_attempts},
        reason=work.cancellation_reason,
        actor=work.cancelled_by or actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    return work


def _mark_execution_failed(
    session: Session,
    *,
    work_item_id: UUID,
    execution_token: str,
    error: Exception,
    actor: str,
) -> OrganizationalWorkItem:
    session.rollback()
    work = session.get(OrganizationalWorkItem, work_item_id)
    if work is None:
        raise error
    now = _now()
    error_text = f"{type(error).__name__}: {error}"[:2000]
    has_attempts_remaining = work.execution_attempts < work.max_execution_attempts
    retry_delay = min(300, 15 * (2 ** max(0, work.execution_attempts - 1)))
    work.status = "retry_wait" if has_attempts_remaining else "failed"
    work.next_retry_at = now + timedelta(seconds=retry_delay) if has_attempts_remaining else None
    work.last_error = error_text
    work.execution_started_at = None
    work.updated_at = now
    session.add(work)
    attempt = session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.execution_token == execution_token
        )
    ).first()
    if attempt is not None:
        attempt.status = "failed"
        attempt.completed_at = now
        attempt.error = error_text
        session.add(attempt)
    interrupted_delegations = session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == work.id,
            DelegationRecord.status == "running",
        )
    ).all()
    for delegation in interrupted_delegations:
        delegation.status = "queued"
        delegation.completed_at = None
        delegation.result_ref = None
        session.add(delegation)
    record_audit(
        session,
        action="organization_work_execution_failed",
        entity_type="organizational_work_item",
        entity_id=work.id,
        after_state={
            "status": work.status,
            "attempt": work.execution_attempts,
            "max_attempts": work.max_execution_attempts,
            "next_retry_at": work.next_retry_at,
        },
        reason=error_text,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    return work


def execute_work_item(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    actor: str = "organization-worker",
) -> OrganizationalWorkItem:
    control = session.exec(select(OrganizationControl).where(OrganizationControl.control_key == "global")).first()
    if control and control.status == "paused":
        if work.status not in {"queued", "retry_wait"}:
            raise ValueError("Work item is not executable")
        work.status = "held"
        work.updated_at = _now()
        session.add(work)
        session.commit()
        return work

    claimed, attempt = _claim_work_execution(session, work.id, actor=actor)
    try:
        return _execute_claimed_work_item(session, claimed, attempt=attempt, actor=actor)
    except WorkCancellationRequested:
        return _mark_execution_cancelled(
            session,
            work_item_id=claimed.id,
            execution_token=attempt.execution_token,
            actor=actor,
        )
    except Exception as exc:
        session.rollback()
        current = session.get(OrganizationalWorkItem, claimed.id)
        if current is not None and current.cancel_requested_at is not None:
            return _mark_execution_cancelled(
                session,
                work_item_id=claimed.id,
                execution_token=attempt.execution_token,
                actor=actor,
            )
        _mark_execution_failed(
            session,
            work_item_id=claimed.id,
            execution_token=attempt.execution_token,
            error=exc,
            actor=actor,
        )
        raise


def _execute_claimed_work_item(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    attempt: OrganizationExecutionAttempt,
    actor: str,
) -> OrganizationalWorkItem:

    results: list[dict[str, Any]] = []
    action_outputs: list[OrganizationalActionOutput] = []
    delegations = session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
    ).all()
    for delegation in delegations:
        _raise_if_cancelled(session, work)
        if delegation.status == "completed":
            existing_output = session.exec(
                select(OrganizationalActionOutput).where(
                    OrganizationalActionOutput.delegation_record_id == delegation.id
                )
            ).first()
            if existing_output is not None:
                action_outputs.append(existing_output)
                results.append(_load(existing_output.output_json, {
                    "agent": f"{delegation.delegate_position_key}_agent",
                    "status": "completed",
                    "note": "Previously completed delegation reused during retry.",
                }))
                continue
            delegation.status = "queued"
        delegation.status = "running"
        delegation.completed_at = None
        session.add(delegation)
        session.commit()
        agent_name = f"{delegation.delegate_position_key}_agent"
        position = _position_by_key(session, delegation.delegate_position_key)
        if _is_suspended(position):
            delegation.status = "held"
            delegation.completed_at = _now()
            delegation.result_ref = "position:suspended"
            session.add(delegation)
            results.append({
                "agent": agent_name,
                "status": "held",
                "note": f"{delegation.delegate_position_key} is suspended; delegation held.",
            })
            action_outputs.append(_record_action_output(
                session,
                work=work,
                delegation=delegation,
                result=results[-1],
                result_ref=delegation.result_ref,
                actor=actor,
            ))
            session.commit()
            continue
        if work.lead_id is None:
            result = {"agent": agent_name, "status": "completed", "note": "Case has no linked lead; organizational context recorded."}
            result_ref = f"work-item:{work.id}"
        else:
            response = run_controlled_agent(session, ControlledAgentRunRequest(
                agent_name=agent_name,
                task=delegation.task,
                lead_id=work.lead_id,
                context=_load(work.context_json, {}),
                actor=actor,
            ))
            result = {
                "agent": response.agent_name,
                "run_id": str(response.run_id),
                "status": "completed",
                "output": response.output,
            }
            result_ref = f"agent-run:{response.run_id}"
        results.append(result)
        delegation.status = "completed"
        delegation.result_ref = result_ref
        delegation.completed_at = _now()
        session.add(delegation)
        action_outputs.append(_record_action_output(
            session,
            work=work,
            delegation=delegation,
            result=result,
            result_ref=result_ref,
            actor=actor,
        ))
        session.commit()

    _raise_if_cancelled(session, work)
    completed_confidences = [item.confidence for item in action_outputs if item.status == "completed"]
    aggregate_confidence = (
        round(sum(completed_confidences) / len(completed_confidences), 4)
        if completed_confidences
        else 0.0
    )
    output_ids = [str(item.id) for item in action_outputs]
    work.output_json = _json({
        "delegated_results": results,
        "governance": {
            "accountable_position_key": work.assigned_position_key,
            "authority_level": work.authority_level,
            "authority_basis": [item.authority_basis for item in action_outputs],
            "organizational_action_output_ids": output_ids,
            "confidence": aggregate_confidence,
            "confidence_basis": "Arithmetic mean of completed delegated action-output confidence values.",
            "expected_impact": "Bounded internal analysis recorded for the accountable decision owner.",
            "rollback_posture": "Discard outputs and replay delegations; no external action was authorized.",
            "execution_attempt": attempt.attempt_number,
            "execution_token": attempt.execution_token,
        },
    })
    work.status = "pending_board" if work.authority_level == "L4" else "pending_ceo" if work.authority_level == "L3" else "completed"
    work.completed_at = _now() if work.status == "completed" else None
    work.execution_started_at = None
    work.next_retry_at = None
    work.last_error = None
    work.updated_at = _now()
    session.add(work)
    attempt.status = "completed"
    attempt.completed_at = _now()
    session.add(attempt)
    decision = session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work.id)
    ).first()
    if decision is not None:
        evidence = _load(decision.evidence_json, [])
        evidence = [
            item
            for item in evidence
            if not isinstance(item, dict) or item.get("type") != "organizational_action_outputs"
        ]
        evidence.append({
            "type": "organizational_action_outputs",
            "ids": output_ids,
            "aggregate_confidence": aggregate_confidence,
        })
        decision.evidence_json = _json(evidence)
        decision.updated_at = _now()
        session.add(decision)
    record_audit(
        session,
        action="organization_work_executed",
        entity_type="organizational_work_item",
        entity_id=work.id,
        after_state={
            "status": work.status,
            "delegations": len(results),
            "action_outputs": len(action_outputs),
            "confidence": aggregate_confidence,
            "attempt": attempt.attempt_number,
            "execution_token": attempt.execution_token,
        },
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    return work


def cancel_work_item(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    reason: str,
    actor: str,
) -> OrganizationalWorkItem:
    session.refresh(work)
    if work.status in {"completed", "cancelled", "pending_ceo", "pending_board"}:
        raise ValueError("Work item can no longer be cancelled")
    now = _now()
    work.cancel_requested_at = now
    work.cancelled_by = actor
    work.cancellation_reason = reason.strip()
    work.updated_at = now
    action = "organization_work_cancellation_requested"
    if work.status != "running":
        work.status = "cancelled"
        work.cancelled_at = now
        work.completed_at = now
        work.next_retry_at = None
        action = "organization_work_cancelled"
        delegations = session.exec(
            select(DelegationRecord).where(
                DelegationRecord.work_item_id == work.id,
                DelegationRecord.status.in_(["queued", "running"]),
            )
        ).all()
        for delegation in delegations:
            delegation.status = "cancelled"
            delegation.completed_at = now
            delegation.result_ref = "work-item:cancelled"
            session.add(delegation)
    session.add(work)
    record_audit(
        session,
        action=action,
        entity_type="organizational_work_item",
        entity_id=work.id,
        after_state={"status": work.status, "cancel_requested_at": now},
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    return work


def retry_work_item(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    reason: str,
    actor: str,
) -> OrganizationalWorkItem:
    session.refresh(work)
    if work.status not in {"failed", "retry_wait"}:
        raise ValueError("Only failed or waiting work can be retried")
    if work.cancel_requested_at is not None:
        raise ValueError("Cancelled work cannot be retried")
    if work.execution_attempts >= work.max_execution_attempts:
        raise ValueError("Work item has exhausted its execution attempts")
    work.status = "queued"
    work.next_retry_at = None
    work.updated_at = _now()
    session.add(work)
    record_audit(
        session,
        action="organization_work_retry_requested",
        entity_type="organizational_work_item",
        entity_id=work.id,
        before_state={"last_error": work.last_error},
        after_state={
            "status": "queued",
            "next_attempt": work.execution_attempts + 1,
            "max_attempts": work.max_execution_attempts,
        },
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    return work


def set_global_control(session: Session, *, status: str, reason: str, actor: str) -> OrganizationControl:
    if status not in {"active", "paused"}:
        raise ValueError("Organization control status must be active or paused")
    ensure_foundation_positions(session, actor=actor)
    control = session.exec(select(OrganizationControl).where(OrganizationControl.control_key == "global")).one()
    before = control.status
    control.status = status
    control.reason = reason.strip()
    control.changed_by = actor
    control.updated_at = _now()
    session.add(control)
    if status == "active":
        held = session.exec(select(OrganizationalWorkItem).where(OrganizationalWorkItem.status == "held")).all()
        for item in held:
            item.status = "queued"
            item.updated_at = _now()
            session.add(item)
    record_audit(session, action=f"organization_{status}", entity_type="organization_control", entity_id=control.id, before_state={"status": before}, after_state={"status": status}, reason=reason, actor=actor, source=SOURCE)
    session.commit()
    session.refresh(control)
    return control


def decide_executive_decision(session: Session, decision: ExecutiveDecision, *, outcome: str, reason: str, actor: str, board_actor: bool) -> ExecutiveDecision:
    if outcome not in {"approved", "rejected", "returned"}:
        raise ValueError("Unsupported decision outcome")
    if decision.status not in {"pending_ceo", "pending_board"}:
        raise ValueError("Decision is not pending")
    if decision.status == "pending_board" and not board_actor:
        raise ValueError("This decision is reserved for the human Board")
    decision.status = outcome
    decision.decided_by = actor
    decision.decision_reason = reason.strip()
    decision.decided_at = _now()
    decision.updated_at = _now()
    session.add(decision)
    work = session.get(OrganizationalWorkItem, decision.work_item_id) if decision.work_item_id else None
    if work is not None:
        work.status = "completed" if outcome == "approved" else outcome
        work.completed_at = _now()
        work.updated_at = _now()
        session.add(work)
    record_audit(session, action=f"executive_decision_{outcome}", entity_type="executive_decision", entity_id=decision.id, after_state={"status": outcome, "decided_by": actor}, reason=reason, actor=actor, source=SOURCE)
    session.commit()
    session.refresh(decision)
    return decision


def board_packet_snapshot(session: Session) -> dict[str, Any]:
    ensure_foundation_positions(session)
    session.commit()
    positions = session.exec(select(OrganizationPosition).where(OrganizationPosition.status == "active").order_by(OrganizationPosition.department, OrganizationPosition.title)).all()
    work = session.exec(select(OrganizationalWorkItem).order_by(OrganizationalWorkItem.created_at.desc()).limit(12)).all()
    decisions = session.exec(select(ExecutiveDecision).where(ExecutiveDecision.status.in_(["pending_ceo", "pending_board"])).order_by(ExecutiveDecision.created_at.desc())).all()
    risks = session.exec(select(RiskEscalation).where(RiskEscalation.status == "open").order_by(RiskEscalation.created_at.desc())).all()
    packets = session.exec(select(BoardPacket).order_by(BoardPacket.created_at.desc()).limit(5)).all()
    control = session.exec(select(OrganizationControl).where(OrganizationControl.control_key == "global")).one()
    return {
        "generated_at": _now(),
        "control": control,
        "metrics": {
            "active_positions": len(positions),
            "queued_work": session.exec(select(func.count()).select_from(OrganizationalWorkItem).where(OrganizationalWorkItem.status == "queued")).one(),
            "pending_ceo": sum(1 for item in decisions if item.status == "pending_ceo"),
            "pending_board": sum(1 for item in decisions if item.status == "pending_board"),
            "open_risks": len(risks),
            "emergencies": sum(1 for item in risks if item.is_emergency),
        },
        "positions": positions,
        "recent_work": work,
        "pending_decisions": decisions,
        "open_risks": risks,
        "recent_packets": packets,
    }


def create_board_packet(
    session: Session,
    *,
    packet_type: str = "on_demand",
    actor: str = "ceo",
    trigger_key: str | None = None,
) -> BoardPacket:
    if packet_type not in {"on_demand", "daily", "weekly", "incident"}:
        raise ValueError("Unsupported Board Packet type")

    ensure_foundation_positions(session)
    period_end = _now()
    if packet_type == "daily":
        period_start = period_end.replace(hour=0, minute=0, second=0, microsecond=0)
        packet_key = f"packet:daily:{period_start.date().isoformat()}"
    elif packet_type == "weekly":
        period_start = (period_end - timedelta(days=period_end.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        iso_year, iso_week, _ = period_start.isocalendar()
        packet_key = f"packet:weekly:{iso_year}-W{iso_week:02d}"
    elif packet_type == "incident":
        period_start = period_end
        packet_key = f"packet:incident:{trigger_key or uuid4()}"
    else:
        period_start = period_end
        packet_key = f"packet:on_demand:{uuid4()}"

    existing = session.exec(select(BoardPacket).where(BoardPacket.packet_key == packet_key)).first()
    if existing is not None:
        return existing

    positions = session.exec(select(OrganizationPosition).where(OrganizationPosition.status == "active")).all()
    pending_decisions = session.exec(select(ExecutiveDecision).where(ExecutiveDecision.status.in_(["pending_ceo", "pending_board"])).order_by(ExecutiveDecision.created_at.desc())).all()
    open_risks = session.exec(select(RiskEscalation).where(RiskEscalation.status == "open").order_by(RiskEscalation.created_at.desc())).all()
    recent_work = session.exec(select(OrganizationalWorkItem).order_by(OrganizationalWorkItem.created_at.desc()).limit(20)).all()

    board_decisions = [item for item in pending_decisions if item.status == "pending_board"]
    ceo_decisions = [item for item in pending_decisions if item.status == "pending_ceo"]
    emergencies = [item for item in open_risks if item.is_emergency]

    summary_lines = [
        f"Active positions: {len(positions)}.",
        f"Pending Board decisions: {len(board_decisions)}.",
        f"Pending CEO decisions: {len(ceo_decisions)}.",
        f"Open risks: {len(open_risks)} ({len(emergencies)} emergency).",
    ]
    if emergencies:
        summary_lines.append(f"Emergency attention required: {', '.join(item.title for item in emergencies[:3])}.")
    if board_decisions:
        summary_lines.append("Board action is requested on the pending decisions listed below.")

    recommendation = "Review pending Board decisions, confirm emergency containment, and approve or return the proposed actions."
    if not board_decisions and not emergencies:
        recommendation = "No Board action required at this time; routine monitoring continues."

    decision_evidence = [
        {
            "decision_id": str(item.id),
            "evidence": _load(item.evidence_json, []),
            "alternatives": _load(item.alternatives_json, []),
            "expected_impact": _load(item.impact_json, {}),
        }
        for item in board_decisions[:10]
    ]
    risk_evidence = [
        {
            "risk_id": str(item.id),
            "evidence": _load(item.evidence_json, []),
            "containment": _load(item.containment_json, []),
        }
        for item in open_risks[:10]
    ]
    content = {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "executive_summary": " ".join(summary_lines),
        "ceo_recommendation": recommendation,
        "approval_requested": (
            "Decide each item in decisions_for_board and confirm emergency containment."
            if board_decisions or emergencies
            else "No approval requested; acknowledge the monitoring update."
        ),
        "evidence": {
            "active_positions": [p.position_key for p in positions],
            "pending_decisions_count": len(pending_decisions),
            "open_risks_count": len(open_risks),
            "recent_work_count": len(recent_work),
            "decision_evidence": decision_evidence,
            "risk_evidence": risk_evidence,
        },
        "evidence_summary": (
            f"Grounded in {len(pending_decisions)} pending decision records, "
            f"{len(open_risks)} open risk records, and {len(recent_work)} recent work items."
        ),
        "alternatives": ["approve", "return_for_more_evidence", "reject"],
        "expected_impact": {
            "governance": "Board oversight and decision authority exercised.",
            "operational": "Pending decisions remain held until Board action."
        },
        "cost_or_resource_impact": (
            "Not quantified in the current evidence; Board should return any "
            "item requiring a cost decision."
        ),
        "urgency": "immediate" if emergencies else "routine",
        "dissenting_views": [],
        "decisions_for_board": [{
            "id": str(item.id),
            "title": item.title,
            "question": item.question,
            "authority_level": item.authority_level,
        } for item in board_decisions[:10]],
        "emergencies": [{
            "id": str(item.id),
            "title": item.title,
            "severity": item.severity,
            "work_item_id": str(item.work_item_id) if item.work_item_id else None,
        } for item in emergencies[:10]],
    }

    packet = BoardPacket(
        packet_key=packet_key,
        packet_type=packet_type,
        period_start=period_start,
        period_end=period_end,
        ceo_summary=" ".join(summary_lines),
        content_json=_json(content),
        status="published",
        prepared_by_position="ceo",
        published_at=period_end,
    )
    session.add(packet)
    record_audit(
        session,
        action="board_packet_created",
        entity_type="board_packet",
        entity_id=packet.id,
        after_state={"packet_type": packet_type, "prepared_by": "ceo"},
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(packet)
    return packet

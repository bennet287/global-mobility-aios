from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import ExecutiveDecision, OrganizationalWorkItem, OrganizationPosition, RiskEscalation
from app.schemas_organization_governance import (
    DeadlineRequest,
    EmergencyRequest,
    EscalationRequest,
    GovernanceDecisionRequest,
    OrganizationControlUpdate,
    PositionResumeRequest,
    PositionSuspensionRequest,
    WorkItemCreate,
)
from app.services.audit_log import record_audit
from app.services.organization_governance import (
    SOURCE,
    board_packet_snapshot,
    board_override_decision,
    classify_authority,
    decide_executive_decision,
    ensure_foundation_positions,
    escalate_work_item,
    execute_work_item,
    mark_work_emergency,
    resume_position,
    set_decision_deadline,
    set_global_control,
    set_work_deadline,
    suspend_position,
)


router = APIRouter(prefix="/api/v1/organization", tags=["ai-organization-v13.0"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _role(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "role", "read_only"))


def _admin(request: Request) -> None:
    if _role(request) != "admin":
        raise HTTPException(status_code=403, detail="Human Board action requires the admin role")


@router.post("/bootstrap", status_code=201)
def bootstrap_organization(request: Request, session: Session = Depends(get_session)) -> dict:
    _admin(request)
    positions = ensure_foundation_positions(session, actor=_actor(request))
    session.commit()
    return {"status": "ready", "positions_registered": len(positions)}


@router.get("/positions")
def list_positions(session: Session = Depends(get_session)) -> list[OrganizationPosition]:
    ensure_foundation_positions(session)
    session.commit()
    return list(session.exec(select(OrganizationPosition).where(OrganizationPosition.status == "active").order_by(OrganizationPosition.department, OrganizationPosition.title)).all())


@router.get("/board-packet")
def get_board_packet(session: Session = Depends(get_session)) -> dict:
    return board_packet_snapshot(session)


@router.get("/work-items")
def list_work_items(session: Session = Depends(get_session)) -> list[OrganizationalWorkItem]:
    return list(session.exec(select(OrganizationalWorkItem).order_by(OrganizationalWorkItem.created_at.desc()).limit(100)).all())


@router.post("/work-items", status_code=201)
def create_work_item(payload: WorkItemCreate, request: Request, session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    existing = session.exec(select(OrganizationalWorkItem).where(OrganizationalWorkItem.idempotency_key == payload.idempotency_key)).first()
    if existing:
        return existing
    ensure_foundation_positions(session, actor=_actor(request))
    authority, risk = classify_authority(payload.action, {"risk_level": payload.risk_level, "requires_board_approval": payload.requires_board_approval})
    work = OrganizationalWorkItem(
        idempotency_key=payload.idempotency_key,
        title=payload.title,
        objective=payload.objective,
        department=payload.department,
        authority_level=authority,
        assigned_position_key="ceo" if payload.department == "Executive" else "coo",
        risk_level=risk,
        context_json=json.dumps({"action": payload.action, **payload.context}, sort_keys=True),
        created_by=_actor(request),
    )
    session.add(work)
    session.flush()
    if authority in {"L3", "L4"}:
        owner = "board" if authority == "L4" else "ceo"
        session.add(ExecutiveDecision(
            decision_key=f"decision:{work.id}", work_item_id=work.id,
            authority_level=authority, requested_by_position=work.assigned_position_key,
            decision_owner_position=owner, title=f"Decision required: {work.title}",
            question="Should the organization proceed with this proposed work?",
            recommendation="Hold execution until the accountable decision owner completes review.",
            alternatives_json=json.dumps(["proceed", "revise", "reject"]),
            evidence_json=json.dumps([]), impact_json=json.dumps({"risk_level": risk}),
            status="pending_board" if authority == "L4" else "pending_ceo",
        ))
        session.add(RiskEscalation(
            risk_key=f"risk:{work.id}", work_item_id=work.id,
            category="governance", severity=risk,
            title=f"{authority} authority boundary reached",
            description="The proposed work exceeds delegated execution authority.",
            evidence_json=json.dumps([]), containment_json=json.dumps(["Execution held", f"Escalated to {owner}"]),
            accountable_position_key=work.assigned_position_key,
            escalated_to_position_key=owner,
            requires_board_attention=authority == "L4",
        ))
    record_audit(session, action="organization_work_created", entity_type="organizational_work_item", entity_id=work.id, after_state={"authority_level": authority}, actor=_actor(request), source=SOURCE)
    session.commit()
    session.refresh(work)
    return work


@router.post("/work-items/{work_item_id}/execute")
def execute_work(work_item_id: UUID, request: Request, session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    work = session.get(OrganizationalWorkItem, work_item_id)
    if work is None:
        raise HTTPException(status_code=404, detail="Organizational work item not found")
    try:
        return execute_work_item(session, work, actor=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/work-items/{work_item_id}/deadline")
def set_work_item_deadline(work_item_id: UUID, payload: DeadlineRequest, request: Request, session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    _admin(request)
    work = session.get(OrganizationalWorkItem, work_item_id)
    if work is None:
        raise HTTPException(status_code=404, detail="Organizational work item not found")
    try:
        return set_work_deadline(session, work, due_at=payload.due_at, actor=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/work-items/{work_item_id}/escalate")
def escalate_work_item_endpoint(work_item_id: UUID, payload: EscalationRequest, request: Request, session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    _admin(request)
    work = session.get(OrganizationalWorkItem, work_item_id)
    if work is None:
        raise HTTPException(status_code=404, detail="Organizational work item not found")
    try:
        return escalate_work_item(session, work, reason=payload.reason, actor=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/work-items/{work_item_id}/emergency")
def mark_work_item_emergency(work_item_id: UUID, payload: EmergencyRequest, request: Request, session: Session = Depends(get_session)) -> OrganizationalWorkItem:
    _admin(request)
    work = session.get(OrganizationalWorkItem, work_item_id)
    if work is None:
        raise HTTPException(status_code=404, detail="Organizational work item not found")
    try:
        return mark_work_emergency(session, work, reason=payload.reason, actor=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/decisions/{decision_id}/deadline")
def set_decision_item_deadline(decision_id: UUID, payload: DeadlineRequest, request: Request, session: Session = Depends(get_session)) -> ExecutiveDecision:
    _admin(request)
    decision = session.get(ExecutiveDecision, decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Executive decision not found")
    try:
        return set_decision_deadline(session, decision, due_at=payload.due_at, actor=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/decisions")
def list_decisions(session: Session = Depends(get_session)) -> list[ExecutiveDecision]:
    return list(session.exec(select(ExecutiveDecision).order_by(ExecutiveDecision.created_at.desc()).limit(100)).all())


@router.post("/decisions/{decision_id}/board-decision")
def board_decision(decision_id: UUID, payload: GovernanceDecisionRequest, request: Request, session: Session = Depends(get_session)) -> ExecutiveDecision:
    _admin(request)
    decision = session.get(ExecutiveDecision, decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Executive decision not found")
    try:
        return decide_executive_decision(session, decision, outcome=payload.decision, reason=payload.reason, actor=_actor(request), board_actor=True)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/decisions/{decision_id}/board-override")
def board_override_decision_endpoint(decision_id: UUID, payload: GovernanceDecisionRequest, request: Request, session: Session = Depends(get_session)) -> ExecutiveDecision:
    _admin(request)
    decision = session.get(ExecutiveDecision, decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Executive decision not found")
    try:
        return board_override_decision(session, decision, outcome=payload.decision, reason=payload.reason, actor=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/positions/{position_id}/suspend")
def suspend_position_endpoint(position_id: UUID, payload: PositionSuspensionRequest, request: Request, session: Session = Depends(get_session)) -> OrganizationPosition:
    _admin(request)
    position = session.get(OrganizationPosition, position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")
    try:
        return suspend_position(session, position, reason=payload.reason, actor=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/positions/{position_id}/resume")
def resume_position_endpoint(position_id: UUID, payload: PositionResumeRequest, request: Request, session: Session = Depends(get_session)) -> OrganizationPosition:
    _admin(request)
    position = session.get(OrganizationPosition, position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")
    try:
        return resume_position(session, position, reason=payload.reason, actor=_actor(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/control")
def update_control(payload: OrganizationControlUpdate, request: Request, session: Session = Depends(get_session)):
    _admin(request)
    return set_global_control(session, status=payload.status, reason=payload.reason, actor=_actor(request))

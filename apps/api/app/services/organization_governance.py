from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, func, select

from app.models.domain import (
    AgentRun,
    AutomationEvent,
    BoardPacket,
    CorporateMobilityCase,
    DelegationRecord,
    ExecutiveCouncilConsultation,
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
    ("vp_engineering", "Vice President of Engineering Agent", "Technology", "cto", "L2", "VP_Engineering.md"),
    ("lead_architect", "Lead Architect Agent", "Technology", "cto", "L2", "Lead_Architect.md"),
    ("coo", "Chief Operating Officer Agent", "Operations", "ceo", "L3", "COO.md"),
    ("cmo", "Chief Marketing Officer Agent", "Marketing", "ceo", "L3", "CMO.md"),
    ("cpo", "Chief Product Officer Agent", "Product", "ceo", "L3", "CPO.md"),
    ("product_manager", "Product Manager Agent", "Product", "cpo", "L2", "Product_Manager.md"),
    ("design_agent", "Design Agent Agent", "Product", "cpo", "L2", "Design_Agent.md"),
    ("cfo", "Chief Financial Officer Agent", "Finance", "ceo", "L3", "CFO.md"),
    ("cco", "Chief Communications Officer Agent", "Communications", "ceo", "L3", "CCO.md"),
    ("chro", "Chief Human Resources Officer Agent", "People", "ceo", "L3", "CHRO.md"),
    ("clo", "Chief Legal Officer Agent", "Legal", "ceo", "L3", "CLO.md"),
    ("head_of_product", "Head of Product Agent", "Product", "cpo", "L2", "Head_of_Product.md"),
    ("sales_summary", "Sales Intelligence Agent", "Operations", "coo", "L1", "Sales_Summary_Agent.md"),
    ("operations_coordination", "Operations Coordination Agent", "Operations", "coo", "L1", "Operations_Coordination_Agent.md"),
    ("business_intelligence", "Business Intelligence Agent", "Operations", "coo", "L1", "Business_Intelligence_Agent.md"),
    ("application_readiness", "Application Readiness Agent", "Operations", "coo", "L1", "Application_Readiness_Agent.md"),
)
POSITION_SPEC_BY_KEY = {
    key: {
        "title": title,
        "department": department,
        "reports_to_position_key": reports_to,
        "authority_level": authority,
        "role_card_name": role_card,
    }
    for key, title, department, reports_to, authority, role_card in POSITION_SPECS
}
HARDENED_POSITION_KEYS = frozenset(
    {"ceo", "cto", "vp_engineering", "lead_architect", "cpo", "product_manager", "design_agent"}
)

OPERATIONS_DELEGATION_SPECS = (
    ("sales_summary", "Summarize verified commercial and client context."),
    ("operations_coordination", "Assess workflow state, dependencies, ownership, and service-level risks."),
    ("business_intelligence", "Extract evidence-backed operating signals, gaps, and decision questions."),
)
APPLICATION_READINESS_DELEGATION = (
    "application_readiness",
    "Assess application readiness, dependencies, and blockers.",
)
TECHNOLOGY_DELEGATION_SPECS = (
    (
        "vp_engineering",
        "Assess delivery readiness, test evidence, reliability, observability, dependencies, and rollback posture.",
    ),
    (
        "lead_architect",
        "Assess architecture boundaries, security, data handling, integration impact, and reversibility.",
    ),
)
TECHNOLOGY_REQUIRED_DELEGATES = frozenset(
    delegate for delegate, _ in TECHNOLOGY_DELEGATION_SPECS
)
TECHNOLOGY_REQUIRED_EVIDENCE_FIELDS = (
    "architecture",
    "data_handling",
    "dependencies",
    "integration",
    "observability",
    "reliability",
    "rollback",
    "security",
    "sources",
    "tests",
)
TECHNOLOGY_SPECIALIST_REQUIRED_OUTPUT_FIELDS = {
    "vp_engineering": frozenset(
        {
            "delivery_readiness",
            "evidence_basis",
            "evidence_gaps",
            "recommendation",
            "dissent",
            "material_risks",
            "escalation_required",
            "confidence",
        }
    ),
    "lead_architect": frozenset(
        {
            "evidence_basis",
            "evidence_gaps",
            "recommendation",
            "dissent",
            "material_risks",
            "escalation_required",
            "confidence",
        }
    ),
}

BOARD_RESERVED_ACTIONS = {
    "contract.sign",
    "executive.authority.change",
    "market.entry",
    "pricing.change",
    "production.irreversible",
    "spend.above_threshold",
    "vendor.commit",
}
EXECUTIVE_ACTIONS = {
    "authority.submit",
    "client.external_send",
    "deployment.production",
    "infrastructure.mutate",
    "payment.initiate",
    "policy.publish",
    "secrets.access",
}

DEPARTMENT_EXECUTIVE_OWNER = {
    "executive": "ceo",
    "technology": "cto",
    "operations": "coo",
    "marketing": "cmo",
    "product": "cpo",
    "finance": "cfo",
    "communications": "cco",
    "people": "chro",
    "legal": "clo",
}
EXECUTIVE_COUNCIL_POSITIONS = frozenset(DEPARTMENT_EXECUTIVE_OWNER.values()) - {"ceo"}
CEO_AUTO_RESOLVABLE_ACTIONS = frozenset({"internal.analysis"})
CEO_MINIMUM_CONFIDENCE = 0.5
CEO_COORDINATION_LEASE = timedelta(minutes=5)
EXECUTABLE_DEPARTMENT_ACTIONS: dict[str, frozenset[str] | None] = {
    "operations": None,
    "technology": frozenset({"internal.analysis"}),
    "product": frozenset({"internal.analysis"}),
}
GOVERNED_EXTERNAL_ACTIONS = frozenset(
    {
        "client.external_send",
        "authority.submit",
        "payment.initiate",
        "contract.sign",
        "deployment.production",
    }
)
TECHNOLOGY_PROHIBITED_ACTIONS = frozenset(
    GOVERNED_EXTERNAL_ACTIONS
    | {
        "infrastructure.mutate",
        "production.irreversible",
        "secrets.access",
        "vendor.commit",
    }
)
PRODUCT_DELEGATION_SPECS = (
    (
        "product_manager",
        "Assess product fit, scope, dependencies, roadmap alignment, and success metrics from supplied evidence.",
    ),
    (
        "design_agent",
        "Assess design quality, UX research, accessibility, and scope fit from supplied evidence.",
    ),
)
PRODUCT_REQUIRED_DELEGATES = frozenset(
    delegate for delegate, _ in PRODUCT_DELEGATION_SPECS
)
PRODUCT_REQUIRED_EVIDENCE_FIELDS = (
    "user_evidence",
    "market_evidence",
    "scope",
    "dependencies",
    "roadmap_alignment",
    "success_metrics",
    "design_principles",
    "ux_research",
    "accessibility",
    "sources",
    "risks",
)
PRODUCT_SPECIALIST_REQUIRED_OUTPUT_FIELDS = {
    "product_manager": frozenset(
        {
            "product_fit",
            "evidence_basis",
            "evidence_gaps",
            "recommendation",
            "dissent",
            "material_risks",
            "escalation_required",
            "confidence",
        }
    ),
    "design_agent": frozenset(
        {
            "design_assessment",
            "evidence_basis",
            "evidence_gaps",
            "recommendation",
            "dissent",
            "material_risks",
            "escalation_required",
            "confidence",
        }
    ),
}
PRODUCT_PROHIBITED_ACTIONS = frozenset(
    GOVERNED_EXTERNAL_ACTIONS
    | {
        "pricing.change",
        "policy.publish",
        "production.irreversible",
    }
)
ACTION_EXECUTIVE_CONSULTATIONS = {
    "client.external_send": ("cco",),
    "authority.submit": ("clo",),
    "payment.initiate": ("cfo",),
    "contract.sign": ("clo", "cfo"),
    "deployment.production": ("cto",),
    "policy.publish": ("cpo", "clo"),
}
POSITION_DOMAINS = {
    "cto": "technology",
    "coo": "operations",
    "cmo": "marketing",
    "cpo": "product",
    "cfo": "finance",
    "cco": "communications",
    "chro": "people",
    "clo": "legal",
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


def department_executive_owner(department: str) -> str:
    owner = DEPARTMENT_EXECUTIVE_OWNER.get(department.strip().lower())
    if owner is None:
        raise ValueError(f"Unsupported organization department: {department}")
    return owner


def department_runtime_available(department: str, action: str | None = None) -> bool:
    allowed_actions = EXECUTABLE_DEPARTMENT_ACTIONS.get(department.strip().lower())
    if allowed_actions is None:
        return department.strip().lower() == "operations"
    return bool(action) and action.strip().lower() in allowed_actions


def _runtime_unavailable_reason(department: str, action: str | None) -> str:
    normalized_department = department.strip()
    normalized_action = (action or "unspecified").strip()
    if normalized_department.lower() == "technology":
        return (
            f"The Technology runtime does not execute action '{normalized_action}'; "
            "only bounded internal.analysis is enabled."
        )
    if normalized_department.lower() == "product":
        return (
            f"The Product runtime does not execute action '{normalized_action}'; "
            "only bounded internal.analysis is enabled."
        )
    return f"The {normalized_department} runtime is registered for governance but is not yet executable."


def _position_contract(position_key: str, authority_level: str) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "may_act_within": authority_level,
        "must_escalate_above": authority_level,
        "evidence_required": True,
        "audit_required": True,
    }
    if position_key == "ceo":
        contract.update(
            {
                "capabilities": [
                    "coordinate_executive_council",
                    "resolve_evidence_complete_internal_l3",
                    "escalate_l4_emergency_and_conflict",
                ],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "self_approval_allowed": False,
                "prohibited_direct_actions": sorted(GOVERNED_EXTERNAL_ACTIONS),
            }
        )
    elif position_key == "cto":
        contract.update(
            {
                "capabilities": [
                    "delegate_bounded_technology_analysis",
                    "synthesize_evidence_complete_technology_review",
                    "escalate_production_security_and_authority_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "self_approval_allowed": False,
                "required_specialist_positions": sorted(TECHNOLOGY_REQUIRED_DELEGATES),
                "required_evidence_fields": list(TECHNOLOGY_REQUIRED_EVIDENCE_FIELDS),
                "prohibited_direct_actions": sorted(TECHNOLOGY_PROHIBITED_ACTIONS),
            }
        )
    elif position_key == "vp_engineering":
        contract.update(
            {
                "capabilities": [
                    "assess_delivery_readiness",
                    "assess_test_reliability_observability_and_rollback_evidence",
                    "raise_engineering_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "self_approval_allowed": False,
                "required_evidence_fields": [
                    "dependencies",
                    "observability",
                    "reliability",
                    "rollback",
                    "sources",
                    "tests",
                ],
                "required_output_fields": sorted(
                    TECHNOLOGY_SPECIALIST_REQUIRED_OUTPUT_FIELDS["vp_engineering"]
                ),
                "prohibited_direct_actions": sorted(TECHNOLOGY_PROHIBITED_ACTIONS),
            }
        )
    elif position_key == "lead_architect":
        contract.update(
            {
                "capabilities": [
                    "assess_architecture_security_data_and_integration_evidence",
                    "assess_reversibility",
                    "raise_architecture_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "self_approval_allowed": False,
                "required_evidence_fields": [
                    "architecture",
                    "data_handling",
                    "integration",
                    "rollback",
                    "security",
                    "sources",
                ],
                "required_output_fields": sorted(
                    TECHNOLOGY_SPECIALIST_REQUIRED_OUTPUT_FIELDS["lead_architect"]
                ),
                "prohibited_direct_actions": sorted(TECHNOLOGY_PROHIBITED_ACTIONS),
            }
        )
    elif position_key == "cpo":
        contract.update(
            {
                "capabilities": [
                    "delegate_bounded_product_analysis",
                    "synthesize_evidence_complete_product_review",
                    "escalate_pricing_policy_and_irreversible_product_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "self_approval_allowed": False,
                "required_specialist_positions": sorted(PRODUCT_REQUIRED_DELEGATES),
                "required_evidence_fields": list(PRODUCT_REQUIRED_EVIDENCE_FIELDS),
                "prohibited_direct_actions": sorted(PRODUCT_PROHIBITED_ACTIONS),
            }
        )
    elif position_key == "product_manager":
        contract.update(
            {
                "capabilities": [
                    "assess_product_fit_scope_and_roadmap_alignment",
                    "assess_dependencies_and_success_metrics",
                    "raise_product_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "self_approval_allowed": False,
                "required_evidence_fields": [
                    "user_evidence",
                    "market_evidence",
                    "scope",
                    "dependencies",
                    "roadmap_alignment",
                    "success_metrics",
                    "sources",
                    "risks",
                ],
                "required_output_fields": sorted(
                    PRODUCT_SPECIALIST_REQUIRED_OUTPUT_FIELDS["product_manager"]
                ),
                "prohibited_direct_actions": sorted(PRODUCT_PROHIBITED_ACTIONS),
            }
        )
    elif position_key == "design_agent":
        contract.update(
            {
                "capabilities": [
                    "assess_design_quality_ux_and_accessibility",
                    "assess_scope_fit_and_dependencies",
                    "raise_design_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "self_approval_allowed": False,
                "required_evidence_fields": [
                    "design_principles",
                    "ux_research",
                    "accessibility",
                    "scope",
                    "dependencies",
                    "sources",
                    "risks",
                ],
                "required_output_fields": sorted(
                    PRODUCT_SPECIALIST_REQUIRED_OUTPUT_FIELDS["design_agent"]
                ),
                "prohibited_direct_actions": sorted(PRODUCT_PROHIBITED_ACTIONS),
            }
        )
    return contract


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
    elif result_ref.startswith("work-item:"):
        evidence.append(
            {
                "type": "organizational_work_item",
                "id": result_ref.removeprefix("work-item:"),
                "review_state": "internal_context_only",
            }
        )
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
        "external_action_authorized": False,
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


def _position_matches_spec(position: OrganizationPosition, position_key: str) -> bool:
    spec = POSITION_SPEC_BY_KEY[position_key]
    return (
        position.title == spec["title"]
        and position.department == spec["department"]
        and position.reports_to_position_key == spec["reports_to_position_key"]
        and position.authority_level == spec["authority_level"]
        and position.role_card_name == spec["role_card_name"]
        and _load(position.contract_json, {})
        == _position_contract(position_key, str(spec["authority_level"]))
    )


def _requeue_position_holds(
    session: Session,
    position_key: str,
    *,
    result_refs: set[str],
) -> set[UUID]:
    requeued_work_ids: set[UUID] = set()
    held_delegations = session.exec(
        select(DelegationRecord).where(
            DelegationRecord.delegate_position_key == position_key,
            DelegationRecord.status == "held",
            DelegationRecord.result_ref.in_(sorted(result_refs)),
        )
    ).all()
    for delegation in held_delegations:
        delegation.status = "queued"
        delegation.result_ref = None
        delegation.completed_at = None
        session.add(delegation)
        work = session.get(OrganizationalWorkItem, delegation.work_item_id)
        if (
            work is not None
            and work.status == "held"
            and work.cancel_requested_at is None
            and work.execution_attempts < work.max_execution_attempts
            and department_runtime_available(work.department, _work_action(work))
        ):
            work.status = "queued"
            work.output_json = "{}"
            work.last_error = None
            work.updated_at = _now()
            session.add(work)
            requeued_work_ids.add(work.id)
    return requeued_work_ids


def ensure_foundation_positions(
    session: Session,
    *,
    actor: str = "system",
    repair_contracts: bool = False,
) -> list[OrganizationPosition]:
    positions: list[OrganizationPosition] = []
    for key, title, department, reports_to, authority, role_card in POSITION_SPECS:
        position = session.exec(
            select(OrganizationPosition).where(
                OrganizationPosition.position_key == key,
                OrganizationPosition.version == 1,
            )
        ).first()
        created = position is None
        if created:
            position = OrganizationPosition(
                position_key=key,
                title=title,
                department=department,
                reports_to_position_key=reports_to,
                role_card_name=role_card,
                authority_level=authority,
                contract_json=_json(_position_contract(key, authority)),
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
            if key in HARDENED_POSITION_KEYS:
                _requeue_position_holds(
                    session,
                    key,
                    result_refs={"position:unavailable"},
                )
        elif key in HARDENED_POSITION_KEYS and repair_contracts:
            expected_contract = _position_contract(key, authority)
            if not _position_matches_spec(position, key):
                before_state = {
                    "title": position.title,
                    "department": position.department,
                    "reports_to_position_key": position.reports_to_position_key,
                    "authority_level": position.authority_level,
                    "role_card_name": position.role_card_name,
                    "contract_json": position.contract_json,
                }
                spec = POSITION_SPEC_BY_KEY[key]
                position.title = str(spec["title"])
                position.department = str(spec["department"])
                position.reports_to_position_key = spec["reports_to_position_key"]
                position.authority_level = str(spec["authority_level"])
                position.role_card_name = spec["role_card_name"]
                position.contract_json = _json(expected_contract)
                position.updated_at = _now()
                session.add(position)
                record_audit(
                    session,
                    action="organization_position_contract_hardened",
                    entity_type="organization_position",
                    entity_id=position.id,
                    before_state=before_state,
                    after_state={
                        **spec,
                        "contract": expected_contract,
                    },
                    actor=actor,
                    source=SOURCE,
                )
                if key in TECHNOLOGY_REQUIRED_DELEGATES:
                    _requeue_position_holds(
                        session,
                        key,
                        result_refs={"position:contract_mismatch"},
                    )
                if key in PRODUCT_REQUIRED_DELEGATES:
                    _requeue_position_holds(
                        session,
                        key,
                        result_refs={"position:contract_mismatch"},
                    )
                if key == "cto":
                    contract_holds = session.exec(
                        select(OrganizationalWorkItem).where(
                            OrganizationalWorkItem.assigned_position_key == "cto",
                            OrganizationalWorkItem.status == "held",
                            OrganizationalWorkItem.last_error
                            == "The persisted CTO contract requires Human Board repair before execution.",
                        )
                    ).all()
                    for held_work in contract_holds:
                        if (
                            held_work.cancel_requested_at is None
                            and held_work.execution_attempts < held_work.max_execution_attempts
                            and department_runtime_available(
                                held_work.department,
                                _work_action(held_work),
                            )
                        ):
                            held_work.status = "queued"
                            held_work.last_error = None
                            held_work.updated_at = _now()
                            session.add(held_work)
                if key == "cpo":
                    contract_holds = session.exec(
                        select(OrganizationalWorkItem).where(
                            OrganizationalWorkItem.assigned_position_key == "cpo",
                            OrganizationalWorkItem.status == "held",
                            OrganizationalWorkItem.last_error
                            == "The persisted CPO contract requires Human Board repair before execution.",
                        )
                    ).all()
                    for held_work in contract_holds:
                        if (
                            held_work.cancel_requested_at is None
                            and held_work.execution_attempts < held_work.max_execution_attempts
                            and department_runtime_available(
                                held_work.department,
                                _work_action(held_work),
                            )
                        ):
                            held_work.status = "queued"
                            held_work.last_error = None
                            held_work.updated_at = _now()
                            session.add(held_work)
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


def delegate_operations_work(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    include_application_readiness: bool = False,
) -> list[DelegationRecord]:
    """Create the bounded COO specialist plan once for an Operations work item."""
    if work.department.strip().lower() != "operations":
        raise ValueError("Operations delegation requires an Operations work item")
    if work.assigned_position_key != "coo":
        raise ValueError("Operations delegation requires COO accountability")

    specs = list(OPERATIONS_DELEGATION_SPECS)
    if include_application_readiness:
        specs.append(APPLICATION_READINESS_DELEGATION)
    existing = {
        item.delegate_position_key: item
        for item in session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
        ).all()
    }
    delegations: list[DelegationRecord] = []
    for delegate, task in specs:
        if delegate in existing:
            delegations.append(existing[delegate])
            continue
        position = _position_by_key(session, delegate)
        if position is None or _is_suspended(position):
            continue
        delegation = DelegationRecord(
            work_item_id=work.id,
            delegator_position_key="coo",
            delegate_position_key=delegate,
            task=task,
            authority_basis="COO L3 operating mandate; delegated L1 internal analysis only.",
        )
        session.add(delegation)
        delegations.append(delegation)
    return delegations


def delegate_technology_work(
    session: Session,
    work: OrganizationalWorkItem,
) -> list[DelegationRecord]:
    """Create the complete, bounded CTO review plan once for internal analysis."""
    if work.department.strip().lower() != "technology":
        raise ValueError("Technology delegation requires a Technology work item")
    if work.assigned_position_key != "cto":
        raise ValueError("Technology delegation requires CTO accountability")
    if _work_action(work).lower() != "internal.analysis":
        raise ValueError("Technology delegation is limited to internal.analysis")

    existing = {
        item.delegate_position_key: item
        for item in session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
        ).all()
    }
    delegations: list[DelegationRecord] = []
    for delegate, task in TECHNOLOGY_DELEGATION_SPECS:
        if delegate in existing:
            delegations.append(existing[delegate])
            continue
        delegation = DelegationRecord(
            work_item_id=work.id,
            delegator_position_key="cto",
            delegate_position_key=delegate,
            task=task,
            authority_basis=(
                "CTO L3 technology mandate; delegated L2 internal analysis only; "
                "no deployment, infrastructure mutation, spend, contract, or external action authority."
            ),
        )
        session.add(delegation)
        delegations.append(delegation)
    return delegations


def delegate_product_work(
    session: Session,
    work: OrganizationalWorkItem,
) -> list[DelegationRecord]:
    """Create the complete, bounded CPO review plan once for internal analysis."""
    if work.department.strip().lower() != "product":
        raise ValueError("Product delegation requires a Product work item")
    if work.assigned_position_key != "cpo":
        raise ValueError("Product delegation requires CPO accountability")
    if _work_action(work).lower() != "internal.analysis":
        raise ValueError("Product delegation is limited to internal.analysis")

    existing = {
        item.delegate_position_key: item
        for item in session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
        ).all()
    }
    delegations: list[DelegationRecord] = []
    for delegate, task in PRODUCT_DELEGATION_SPECS:
        if delegate in existing:
            delegations.append(existing[delegate])
            continue
        delegation = DelegationRecord(
            work_item_id=work.id,
            delegator_position_key="cpo",
            delegate_position_key=delegate,
            task=task,
            authority_basis=(
                "CPO L3 product mandate; delegated L2 internal analysis only; "
                "no pricing change, policy publication, production irreversible decision, or external action authority."
            ),
        )
        session.add(delegation)
        delegations.append(delegation)
    return delegations


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
    requeued_work_ids = _requeue_position_holds(
        session,
        position.position_key,
        result_refs={"position:suspended"},
    )

    accountable_hold_reason = f"The accountable {position.position_key} position is suspended."
    accountable_work = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.assigned_position_key == position.position_key,
            OrganizationalWorkItem.status == "held",
            OrganizationalWorkItem.last_error == accountable_hold_reason,
        )
    ).all()
    for work in accountable_work:
        if (
            work.cancel_requested_at is None
            and work.execution_attempts < work.max_execution_attempts
            and department_runtime_available(work.department, _work_action(work))
        ):
            work.status = "queued"
            work.last_error = None
            work.updated_at = _now()
            session.add(work)
            requeued_work_ids.add(work.id)
    record_audit(
        session,
        action="organization_position_resumed",
        entity_type="organization_position",
        entity_id=position.id,
        before_state={"status": before},
        after_state={
            "status": position.status,
            "requeued_work_item_ids": sorted(str(item) for item in requeued_work_ids),
        },
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
            actor_position="board",
        )
    if decision.authority_level != "L3":
        raise ValueError("Board override applies to L3 executive decisions only")
    if decision.status != "pending_ceo" or decision.decision_owner_position != "ceo":
        raise ValueError("Board override requires a pending CEO-owned L3 decision")
    before_status = decision.status
    decision.status = outcome
    decision.decided_by = actor
    decision.decision_reason = reason.strip()
    decision.decided_at = _now()
    decision.updated_at = _now()
    session.add(decision)
    work = session.get(OrganizationalWorkItem, decision.work_item_id) if decision.work_item_id else None
    if work is not None:
        _apply_decision_outcome_to_work(session, work, outcome=outcome)
    record_audit(
        session,
        action="executive_decision_overridden",
        entity_type="executive_decision",
        entity_id=decision.id,
        before_state={"status": before_status},
        after_state={
            "status": outcome,
            "decided_by": actor,
            "external_action_authorized": False,
        },
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
    if decision.status not in {"pending_ceo", "coordinating_ceo", "pending_board"}:
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
        if parent == "board" or emergency:
            decision.status = "pending_board"
            decision.coordination_token = None
            decision.coordination_claimed_at = None
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
        if emergency:
            risk.category = "emergency"
            risk.severity = "critical"
        risk.escalated_to_position_key = parent
        risk.requires_board_attention = parent == "board" or emergency or risk.requires_board_attention
        risk.is_emergency = risk.is_emergency or emergency
        containment = _load(risk.containment_json, [])
        if emergency and "Execution held for Human Board review" not in containment:
            containment.append("Execution held for Human Board review")
        risk.containment_json = _json(containment)
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
    session.refresh(work)
    decision = session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work.id)
    ).first()
    risk = session.exec(
        select(RiskEscalation).where(
            RiskEscalation.work_item_id == work.id,
            RiskEscalation.status == "open",
        )
    ).first()
    packet = session.exec(
        select(BoardPacket).where(
            BoardPacket.packet_key == f"packet:incident:{work.id}"
        )
    ).first()
    invariant_complete = (
        work.is_emergency
        and work.authority_level == "L4"
        and work.assigned_position_key == "board"
        and work.status == "pending_board"
        and decision is not None
        and decision.authority_level == "L4"
        and decision.decision_owner_position == "board"
        and decision.status == "pending_board"
        and risk is not None
        and risk.is_emergency
        and risk.severity == "critical"
        and risk.requires_board_attention
        and risk.escalated_to_position_key == "board"
        and packet is not None
    )
    if invariant_complete:
        return work

    requesting_position = (
        decision.requested_by_position if decision is not None else work.assigned_position_key
    )
    was_emergency = work.is_emergency
    work.is_emergency = True
    work.authority_level = "L4"
    work.risk_level = "critical"
    work.status = "held"
    work.updated_at = _now()
    session.add(work)
    if not was_emergency:
        record_audit(
            session,
            action="organization_work_marked_emergency",
            entity_type="organizational_work_item",
            entity_id=work.id,
            after_state={"is_emergency": True, "status": "held"},
            reason=reason,
            actor=actor,
            source=SOURCE,
        )
    session.commit()
    session.refresh(work)

    # Reconcile every parent hop. A replay resumes from the last committed owner.
    while work.assigned_position_key != "board":
        try:
            work = escalate_work_item(session, work, reason=reason, actor=actor, emergency=True)
        except ValueError:
            break
    if work.assigned_position_key != "board":
        raise ValueError("Emergency escalation could not reach the Human Board")

    decision = session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work.id)
    ).first()
    if decision is None:
        decision = ExecutiveDecision(
            decision_key=f"decision:{work.id}",
            work_item_id=work.id,
            authority_level="L4",
            requested_by_position=requesting_position,
            decision_owner_position="board",
            title=f"Emergency decision required: {work.title}",
            question="What containment or disposition does the Human Board authorize?",
            recommendation="Keep execution held while the Human Board reviews the emergency evidence.",
            alternatives_json=_json(["contain", "return_for_evidence", "reject"]),
            evidence_json=_json([{"type": "emergency_escalation", "reason": reason.strip()}]),
            impact_json=_json(
                {
                    "risk_level": "critical",
                    "is_emergency": True,
                    "external_action_authorized": False,
                }
            ),
            status="pending_board",
        )
        session.add(decision)
    else:
        decision.authority_level = "L4"
        decision.decision_owner_position = "board"
        decision.status = "pending_board"
        decision.coordination_token = None
        decision.coordination_claimed_at = None
        decision.updated_at = _now()
        session.add(decision)

    risk = session.exec(
        select(RiskEscalation).where(
            RiskEscalation.work_item_id == work.id,
            RiskEscalation.status == "open",
        )
    ).first()
    if risk is None:
        risk = RiskEscalation(
            risk_key=f"risk:{work.id}:emergency",
            work_item_id=work.id,
            category="emergency",
            severity="critical",
            title=f"Emergency escalation: {work.title}",
            description=reason.strip(),
            evidence_json=_json([{"reason": reason.strip(), "work_item_id": str(work.id)}]),
            containment_json=_json(["Execution held for Human Board review"]),
            accountable_position_key="board",
            escalated_to_position_key="board",
            requires_board_attention=True,
            is_emergency=True,
        )
    else:
        risk.category = "emergency"
        risk.severity = "critical"
        risk.accountable_position_key = "board"
        risk.escalated_to_position_key = "board"
        risk.requires_board_attention = True
        risk.is_emergency = True
        containment = _load(risk.containment_json, [])
        if "Execution held for Human Board review" not in containment:
            containment.append("Execution held for Human Board review")
        risk.containment_json = _json(containment)
        risk.updated_at = _now()
    session.add(risk)
    work.status = "pending_board"
    work.updated_at = _now()
    session.add(work)
    session.commit()
    create_board_packet(session, packet_type="incident", actor=actor, trigger_key=str(work.id))
    session.refresh(work)
    return work


def classify_authority(action: str, payload: dict[str, Any] | None = None) -> tuple[str, str]:
    data = payload or {}
    normalized_action = action.strip().lower()
    risk = str(data.get("risk_level") or data.get("severity") or "routine").lower()
    if bool(data.get("requires_board_approval")) or normalized_action in BOARD_RESERVED_ACTIONS or risk == "critical":
        return "L4", "critical"
    if normalized_action in EXECUTIVE_ACTIONS or risk in {"high", "material"}:
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
    delegate_operations_work(session, work, include_application_readiness=True)

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


def _hold_work_without_claim(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    reason: str,
    action: str,
    actor: str,
    audit_action: str,
) -> OrganizationalWorkItem:
    if work.status != "held" or work.last_error != reason:
        work.status = "held"
        work.completed_at = None
        work.execution_started_at = None
        work.next_retry_at = None
        work.last_error = reason
        work.updated_at = _now()
        session.add(work)
        record_audit(
            session,
            action=audit_action,
            entity_type="organizational_work_item",
            entity_id=work.id,
            after_state={
                "status": "held",
                "department": work.department,
                "requested_action": action,
                "external_action_authorized": False,
            },
            reason=reason,
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
    action = _work_action(work)
    if not department_runtime_available(work.department, action):
        return _hold_work_without_claim(
            session,
            work,
            reason=_runtime_unavailable_reason(work.department, action),
            action=action,
            actor=actor,
            audit_action="organization_work_held_runtime_unavailable",
        )

    accountable_position = _position_by_key(session, work.assigned_position_key)
    if accountable_position is None:
        return _hold_work_without_claim(
            session,
            work,
            reason=f"The accountable {work.assigned_position_key} position is not registered.",
            action=action,
            actor=actor,
            audit_action="organization_work_held_accountability_unavailable",
        )
    if _is_suspended(accountable_position):
        return _hold_work_without_claim(
            session,
            work,
            reason=f"The accountable {work.assigned_position_key} position is suspended.",
            action=action,
            actor=actor,
            audit_action="organization_work_held_accountability_unavailable",
        )
    if (
        work.department.strip().lower() == "technology"
        and _load(accountable_position.contract_json, {}) != _position_contract("cto", "L3")
    ):
        return _hold_work_without_claim(
            session,
            work,
            reason="The persisted CTO contract requires Human Board repair before execution.",
            action=action,
            actor=actor,
            audit_action="organization_work_held_contract_mismatch",
        )
    if (
        work.department.strip().lower() == "product"
        and _load(accountable_position.contract_json, {}) != _position_contract("cpo", "L3")
    ):
        return _hold_work_without_claim(
            session,
            work,
            reason="The persisted CPO contract requires Human Board repair before execution.",
            action=action,
            actor=actor,
            audit_action="organization_work_held_contract_mismatch",
        )

    if work.department.strip().lower() == "technology":
        delegate_technology_work(session, work)
        technology_preflight_gap = _technology_preflight_gap(session, work)
        if technology_preflight_gap:
            return _hold_work_without_claim(
                session,
                work,
                reason=technology_preflight_gap,
                action=action,
                actor=actor,
                audit_action="organization_work_held_technology_preflight",
            )

    if work.department.strip().lower() == "product":
        delegate_product_work(session, work)
        product_preflight_gap = _product_preflight_gap(session, work)
        if product_preflight_gap:
            return _hold_work_without_claim(
                session,
                work,
                reason=product_preflight_gap,
                action=action,
                actor=actor,
                audit_action="organization_work_held_product_preflight",
            )

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


def _technology_evidence_context(work: OrganizationalWorkItem) -> dict[str, Any]:
    context = _load(work.context_json, {})
    context = context if isinstance(context, dict) else {}
    facts = context.get("facts")
    facts = facts if isinstance(facts, dict) else {}
    evidence = context.get("evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    return {**evidence, **facts}


def _technology_evidence_gaps(work: OrganizationalWorkItem) -> list[str]:
    evidence = _technology_evidence_context(work)
    aliases = {
        "architecture": ("architecture", "architecture_evidence"),
        "data_handling": ("data_handling", "data_classification"),
        "dependencies": ("dependencies", "delivery_dependencies"),
        "integration": ("integration", "integration_impact"),
        "observability": ("observability", "observability_evidence"),
        "reliability": ("reliability", "reliability_evidence"),
        "rollback": ("rollback", "reversibility", "rollback_plan", "rollback_evidence"),
        "security": ("security", "security_evidence"),
        "sources": ("sources", "source_provenance"),
        "tests": ("tests", "test_evidence", "test_results"),
    }
    return [
        field
        for field in TECHNOLOGY_REQUIRED_EVIDENCE_FIELDS
        if not any(evidence.get(alias) not in (None, "", [], {}) for alias in aliases[field])
    ]


def _technology_preflight_gap(
    session: Session,
    work: OrganizationalWorkItem,
) -> str | None:
    delegations = {
        item.delegate_position_key: item
        for item in session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
        ).all()
    }
    position_gaps: list[str] = []
    for position_key in sorted(TECHNOLOGY_REQUIRED_DELEGATES):
        delegation = delegations.get(position_key)
        position = _position_by_key(session, position_key)
        result_ref: str | None = None
        if position is None:
            result_ref = "position:unavailable"
            position_gaps.append(f"{position_key} is not registered")
        elif _is_suspended(position):
            result_ref = "position:suspended"
            position_gaps.append(f"{position_key} is suspended")
        elif not _position_matches_spec(position, position_key):
            result_ref = "position:contract_mismatch"
            position_gaps.append(f"{position_key} contract or reporting line requires Human Board repair")
        if delegation is not None and result_ref is not None:
            delegation.status = "held"
            delegation.result_ref = result_ref
            delegation.completed_at = _now()
            session.add(delegation)

    evidence_gaps = _technology_evidence_gaps(work)
    gaps: list[str] = []
    if position_gaps:
        gaps.append("; ".join(position_gaps))
    if evidence_gaps:
        gaps.append(f"missing evidence fields: {', '.join(evidence_gaps)}")
    if not gaps:
        return None
    return "Technology preflight incomplete; " + "; ".join(gaps) + "."


def _product_evidence_context(work: OrganizationalWorkItem) -> dict[str, Any]:
    context = _load(work.context_json, {})
    context = context if isinstance(context, dict) else {}
    facts = context.get("facts")
    facts = facts if isinstance(facts, dict) else {}
    evidence = context.get("evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    return {**evidence, **facts}


def _product_evidence_gaps(work: OrganizationalWorkItem) -> list[str]:
    evidence = _product_evidence_context(work)
    aliases = {
        "user_evidence": ("user_evidence", "user_research"),
        "market_evidence": ("market_evidence", "market_signals"),
        "scope": ("scope", "proposed_scope"),
        "dependencies": ("dependencies", "product_dependencies", "design_dependencies"),
        "roadmap_alignment": ("roadmap_alignment", "roadmap_fit"),
        "success_metrics": ("success_metrics", "metrics"),
        "design_principles": ("design_principles", "design_standards"),
        "ux_research": ("ux_research", "ux_evidence"),
        "accessibility": ("accessibility", "accessibility_evidence"),
        "sources": ("sources", "source_provenance"),
        "risks": ("risks", "known_risks"),
    }
    return [
        field
        for field in PRODUCT_REQUIRED_EVIDENCE_FIELDS
        if not any(evidence.get(alias) not in (None, "", [], {}) for alias in aliases[field])
    ]


def _product_preflight_gap(
    session: Session,
    work: OrganizationalWorkItem,
) -> str | None:
    delegations = {
        item.delegate_position_key: item
        for item in session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
        ).all()
    }
    position_gaps: list[str] = []
    for position_key in sorted(PRODUCT_REQUIRED_DELEGATES):
        delegation = delegations.get(position_key)
        position = _position_by_key(session, position_key)
        result_ref: str | None = None
        if position is None:
            result_ref = "position:unavailable"
            position_gaps.append(f"{position_key} is not registered")
        elif _is_suspended(position):
            result_ref = "position:suspended"
            position_gaps.append(f"{position_key} is suspended")
        elif not _position_matches_spec(position, position_key):
            result_ref = "position:contract_mismatch"
            position_gaps.append(f"{position_key} contract or reporting line requires Human Board repair")
        if delegation is not None and result_ref is not None:
            delegation.status = "held"
            delegation.result_ref = result_ref
            delegation.completed_at = _now()
            session.add(delegation)

    evidence_gaps = _product_evidence_gaps(work)
    gaps: list[str] = []
    if position_gaps:
        gaps.append("; ".join(position_gaps))
    if evidence_gaps:
        gaps.append(f"missing evidence fields: {', '.join(evidence_gaps)}")
    if not gaps:
        return None
    return "Product preflight incomplete; " + "; ".join(gaps) + "."


def _specialist_output_payload(action_output: OrganizationalActionOutput) -> dict[str, Any]:
    result = _load(action_output.output_json, {})
    if not isinstance(result, dict):
        return {}
    payload = result.get("output")
    return payload if isinstance(payload, dict) else {}


def _recover_completed_delegation_result(
    session: Session,
    delegation: DelegationRecord,
    work: OrganizationalWorkItem,
) -> tuple[dict[str, Any], str] | None:
    result_ref = delegation.result_ref or ""
    agent_name = f"{delegation.delegate_position_key}_agent"
    if result_ref.startswith("agent-run:"):
        try:
            run_id = UUID(result_ref.removeprefix("agent-run:"))
        except ValueError:
            return None
        run = session.get(AgentRun, run_id)
        if run is None:
            return None
        output = _load(run.output_json, {})
        output = output if isinstance(output, dict) else {}
        return (
            {
                "agent": run.agent_name,
                "run_id": str(run.id),
                "status": "completed",
                "output": output,
            },
            result_ref,
        )
    if result_ref == f"work-item:{work.id}":
        return (
            {
                "agent": agent_name,
                "status": "completed",
                "note": "Case has no linked lead; organizational context recorded.",
            },
            result_ref,
        )
    return None


def _department_completion_gap(
    work: OrganizationalWorkItem,
    delegations: list[DelegationRecord],
    action_outputs: list[OrganizationalActionOutput],
) -> str | None:
    department = work.department.strip().lower()
    if department == "technology":
        required_delegates = TECHNOLOGY_REQUIRED_DELEGATES
        specialist_output_fields = TECHNOLOGY_SPECIALIST_REQUIRED_OUTPUT_FIELDS
        evidence_gaps_fn = _technology_evidence_gaps
        proceed_recommendation = "proceed_to_cto_internal_review"
        prefix = "Technology evidence contract incomplete"
        primary_field_by_position = {"vp_engineering": "delivery_readiness"}
    elif department == "product":
        required_delegates = PRODUCT_REQUIRED_DELEGATES
        specialist_output_fields = PRODUCT_SPECIALIST_REQUIRED_OUTPUT_FIELDS
        evidence_gaps_fn = _product_evidence_gaps
        proceed_recommendation = "proceed_to_cpo_internal_review"
        prefix = "Product evidence contract incomplete"
        primary_field_by_position = {
            "product_manager": "product_fit",
            "design_agent": "design_assessment",
        }
    else:
        return None

    by_key = {item.delegate_position_key: item for item in delegations}
    missing_delegates = sorted(required_delegates - set(by_key))
    incomplete_delegates = sorted(
        key
        for key in required_delegates
        if key in by_key and by_key[key].status != "completed"
    )
    completed_output_delegation_ids = {
        item.delegation_record_id
        for item in action_outputs
        if item.status == "completed" and item.delegation_record_id is not None
    }
    output_by_delegation_id = {
        item.delegation_record_id: item
        for item in action_outputs
        if item.delegation_record_id is not None
    }
    missing_outputs = sorted(
        key
        for key in required_delegates
        if key in by_key and by_key[key].id not in completed_output_delegation_ids
    )
    evidence_gaps = evidence_gaps_fn(work)
    specialist_gaps: list[str] = []
    specialist_dissent: list[str] = []
    for position_key in sorted(required_delegates):
        delegation = by_key.get(position_key)
        action_output = (
            output_by_delegation_id.get(delegation.id)
            if delegation is not None
            else None
        )
        if action_output is None or action_output.status != "completed":
            continue
        payload = _specialist_output_payload(action_output)
        required_fields = specialist_output_fields[position_key]
        missing_fields = sorted(required_fields - set(payload))
        reported_gaps = payload.get("evidence_gaps")
        reported_gaps = reported_gaps if isinstance(reported_gaps, list) else ["invalid evidence_gaps"]
        primary_field = primary_field_by_position.get(position_key)
        if primary_field and payload.get(primary_field) != "evidence_complete_for_review":
            reported_gaps.append(primary_field)
        if payload.get("recommendation") != proceed_recommendation:
            reported_gaps.append("recommendation")
        if payload.get("escalation_required") is not False:
            reported_gaps.append("escalation_required")
        if missing_fields or reported_gaps:
            detail = sorted(set(missing_fields + [str(item) for item in reported_gaps]))
            specialist_gaps.append(f"{position_key}: {', '.join(detail)}")
        material_risks = payload.get("material_risks")
        if payload.get("dissent") is not False or material_risks not in (None, []):
            specialist_dissent.append(position_key)

    gaps: list[str] = []
    if missing_delegates:
        gaps.append(f"missing required delegates: {', '.join(missing_delegates)}")
    if incomplete_delegates:
        gaps.append(f"incomplete required delegates: {', '.join(incomplete_delegates)}")
    if missing_outputs:
        gaps.append(f"missing completed outputs: {', '.join(missing_outputs)}")
    if evidence_gaps:
        gaps.append(f"missing evidence fields: {', '.join(evidence_gaps)}")
    if specialist_gaps:
        gaps.append(f"specialist output incomplete: {'; '.join(specialist_gaps)}")
    if specialist_dissent:
        gaps.append(
            "specialist dissent or material risk: "
            + ", ".join(sorted(specialist_dissent))
        )
    if not gaps:
        return None
    return prefix + "; " + "; ".join(gaps) + "."


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
            recovered = _recover_completed_delegation_result(session, delegation, work)
            if recovered is not None:
                result, result_ref = recovered
                results.append(result)
                action_outputs.append(
                    _record_action_output(
                        session,
                        work=work,
                        delegation=delegation,
                        result=result,
                        result_ref=result_ref,
                        actor=actor,
                    )
                )
                session.commit()
                continue
            delegation.status = "queued"
        delegation.status = "running"
        delegation.completed_at = None
        session.add(delegation)
        session.commit()
        agent_name = f"{delegation.delegate_position_key}_agent"
        position = _position_by_key(session, delegation.delegate_position_key)
        if position is None or _is_suspended(position):
            delegation.status = "held"
            delegation.completed_at = _now()
            delegation.result_ref = "position:unavailable" if position is None else "position:suspended"
            session.add(delegation)
            results.append({
                "agent": agent_name,
                "status": "held",
                "note": (
                    f"{delegation.delegate_position_key} is not registered; delegation held."
                    if position is None
                    else f"{delegation.delegate_position_key} is suspended; delegation held."
                ),
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
        runs_from_internal_context = (
            work.department.strip().lower() == "technology"
            and delegation.delegate_position_key in TECHNOLOGY_REQUIRED_DELEGATES
        ) or (
            work.department.strip().lower() == "product"
            and delegation.delegate_position_key in PRODUCT_REQUIRED_DELEGATES
        )
        if work.lead_id is None and not runs_from_internal_context:
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
        session.commit()
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
    completion_gap = _department_completion_gap(work, delegations, action_outputs)
    if completion_gap or not completed_confidences:
        hold_reason = completion_gap or "No completed, provenance-bearing departmental output is available."
        work.output_json = _json(
            {
                "delegated_results": results,
                "governance": {
                    "status": "held",
                    "reason": hold_reason,
                    "external_action_authorized": False,
                    "execution_attempt": attempt.attempt_number,
                    "execution_token": attempt.execution_token,
                },
            }
        )
        work.status = "held"
        work.execution_started_at = None
        work.next_retry_at = None
        work.last_error = hold_reason
        work.updated_at = _now()
        session.add(work)
        attempt.status = "completed"
        attempt.completed_at = _now()
        session.add(attempt)
        record_audit(
            session,
            action="organization_work_held_without_output",
            entity_type="organizational_work_item",
            entity_id=work.id,
            after_state={
                "status": "held",
                "attempt": attempt.attempt_number,
                "external_action_authorized": False,
            },
            reason=work.last_error,
            actor=actor,
            source=SOURCE,
        )
        session.commit()
        session.refresh(work)
        return work
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
            "external_action_authorized": False,
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


def amend_technology_evidence(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    evidence: dict[str, Any],
    facts: dict[str, Any],
    reason: str,
    actor: str,
) -> OrganizationalWorkItem:
    session.refresh(work)
    if work.department.strip().lower() != "technology" or _work_action(work) != "internal.analysis":
        raise ValueError("Evidence amendment is limited to bounded Technology internal analysis")
    if work.status != "held" or not (work.last_error or "").startswith(
        ("Technology preflight incomplete;", "Technology evidence contract incomplete;")
    ):
        raise ValueError("Only Technology work held for incomplete evidence can be amended")
    if "specialist dissent or material risk" in (work.last_error or ""):
        raise ValueError("Specialist dissent or material risk requires a superseding Board-reviewed work item")
    if work.cancel_requested_at is not None:
        raise ValueError("Cancelled work cannot be amended")
    if not evidence and not facts:
        raise ValueError("Evidence amendment requires evidence or facts")

    context = _load(work.context_json, {})
    context = context if isinstance(context, dict) else {}
    authoritative_action = _work_action(work)
    current_evidence = context.get("evidence")
    current_evidence = current_evidence if isinstance(current_evidence, dict) else {}
    current_facts = context.get("facts")
    current_facts = current_facts if isinstance(current_facts, dict) else {}
    before_gaps = _technology_evidence_gaps(work)
    revision = int(context.get("evidence_revision") or 0) + 1
    context.update(
        {
            "action": authoritative_action,
            "evidence": {**current_evidence, **evidence},
            "facts": {**current_facts, **facts},
            "evidence_revision": revision,
        }
    )
    work.context_json = _json(context)
    after_gaps = _technology_evidence_gaps(work)

    if after_gaps:
        work.last_error = (
            "Technology preflight incomplete; missing evidence fields: "
            + ", ".join(after_gaps)
            + "."
        )
    else:
        if work.execution_attempts >= work.max_execution_attempts:
            raise ValueError("Work item has exhausted its execution attempts")
        delegations = session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
        ).all()
        for delegation in delegations:
            if delegation.delegate_position_key not in TECHNOLOGY_REQUIRED_DELEGATES:
                continue
            delegation.status = "queued"
            delegation.result_ref = None
            delegation.completed_at = None
            session.add(delegation)
        work.status = "queued"
        work.output_json = "{}"
        work.last_error = None
        work.completed_at = None
        work.next_retry_at = None
    work.updated_at = _now()
    session.add(work)
    record_audit(
        session,
        action="organization_technology_evidence_amended",
        entity_type="organizational_work_item",
        entity_id=work.id,
        before_state={
            "evidence_revision": revision - 1,
            "missing_evidence_fields": before_gaps,
        },
        after_state={
            "evidence_revision": revision,
            "evidence_keys_added": sorted(evidence),
            "fact_keys_added": sorted(facts),
            "missing_evidence_fields": after_gaps,
            "status": work.status,
            "external_action_authorized": False,
        },
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(work)
    return work


def _work_context(work: OrganizationalWorkItem) -> dict[str, Any]:
    context = _load(work.context_json, {})
    return context if isinstance(context, dict) else {}


def _work_action(work: OrganizationalWorkItem) -> str:
    context = _work_context(work)
    facts = context.get("facts") if isinstance(context.get("facts"), dict) else {}
    return str(
        context.get("action") or facts.get("action") or context.get("event_type") or ""
    ).strip().lower()


def _required_ceo_consultations(
    work: OrganizationalWorkItem,
    decision: ExecutiveDecision,
) -> list[str]:
    required: set[str] = set()
    if decision.requested_by_position in EXECUTIVE_COUNCIL_POSITIONS:
        required.add(decision.requested_by_position)
    department_owner = department_executive_owner(work.department)
    if department_owner in EXECUTIVE_COUNCIL_POSITIONS:
        required.add(department_owner)
    required.update(ACTION_EXECUTIVE_CONSULTATIONS.get(_work_action(work), ()))

    context = _work_context(work)
    facts = context.get("facts") if isinstance(context.get("facts"), dict) else {}
    explicit = context.get("required_consultations", facts.get("required_consultations", []))
    if explicit is None:
        explicit = []
    if not isinstance(explicit, list):
        raise ValueError("required_consultations must be a list of executive positions or departments")
    for value in explicit:
        normalized = str(value).strip().lower()
        position = DEPARTMENT_EXECUTIVE_OWNER.get(normalized, normalized)
        if position not in EXECUTIVE_COUNCIL_POSITIONS:
            raise ValueError(f"Unsupported executive consultation: {value}")
        required.add(position)
    return sorted(required)


def _upsert_executive_consultations(
    session: Session,
    *,
    decision: ExecutiveDecision,
    work: OrganizationalWorkItem,
    required_positions: list[str],
) -> list[ExecutiveCouncilConsultation]:
    delegations = list(
        session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
        ).all()
    )
    outputs = list(
        session.exec(
            select(OrganizationalActionOutput).where(
                OrganizationalActionOutput.work_item_id == work.id
            )
        ).all()
    )
    output_ids = [str(item.id) for item in outputs]
    all_delegations_completed = bool(delegations) and all(
        item.status == "completed" for item in delegations
    )
    all_outputs_complete = (
        bool(outputs)
        and len(outputs) == len(delegations)
        and all(item.status == "completed" for item in outputs)
    )
    aggregate_confidence = (
        round(sum(item.confidence for item in outputs) / len(outputs), 4) if outputs else 0.0
    )
    consultations: list[ExecutiveCouncilConsultation] = []
    for position_key in required_positions:
        key = f"consultation:{decision.id}:{position_key}"
        consultation = session.exec(
            select(ExecutiveCouncilConsultation).where(
                ExecutiveCouncilConsultation.consultation_key == key
            )
        ).first()
        if consultation is None:
            now = _now()
            values = {
                "id": uuid4(),
                "consultation_key": key,
                "decision_id": decision.id,
                "work_item_id": work.id,
                "requested_by_position": "ceo",
                "consulted_position": position_key,
                "domain": POSITION_DOMAINS[position_key],
                "evidence_json": "[]",
                "confidence": 0.0,
                "dissent": False,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
            table = ExecutiveCouncilConsultation.__table__
            dialect = session.get_bind().dialect.name
            if dialect == "sqlite":
                statement = sqlite_insert(table).values(**values).on_conflict_do_nothing(
                    index_elements=["consultation_key"]
                )
            elif dialect == "postgresql":
                statement = postgresql_insert(table).values(**values).on_conflict_do_nothing(
                    index_elements=["consultation_key"]
                )
            else:
                raise RuntimeError(
                    f"Executive consultation upsert is not configured for {dialect}"
                )
            session.exec(statement)
            consultation = session.exec(
                select(ExecutiveCouncilConsultation).where(
                    ExecutiveCouncilConsultation.consultation_key == key
                )
            ).one()

        position = _position_by_key(session, position_key)
        if _is_suspended(position):
            consultation.status = "held"
            consultation.recommendation = (
                f"{position_key} is suspended; the consultation cannot be treated as complete."
            )
            consultation.confidence = 0.0
            consultation.completed_at = None
        elif (
            position_key == decision.requested_by_position
            and position_key == department_executive_owner(work.department)
            and all_delegations_completed
            and all_outputs_complete
        ):
            consultation.status = "completed"
            consultation.evidence_json = _json(
                [
                    {
                        "type": "organizational_action_outputs",
                        "ids": output_ids,
                        "aggregate_confidence": aggregate_confidence,
                    }
                ]
            )
            consultation.recommendation = (
                "Accept the recorded departmental analysis for internal decision-making only; "
                "no external action is authorized."
            )
            consultation.confidence = aggregate_confidence
            consultation.completed_at = consultation.completed_at or _now()
        elif consultation.status != "completed":
            consultation.status = "pending"
            consultation.recommendation = (
                f"Awaiting evidence-backed consultation from {position_key}."
            )
            consultation.confidence = 0.0
            consultation.completed_at = None
        consultation.updated_at = _now()
        session.add(consultation)
        consultations.append(consultation)
    session.flush()
    return consultations


def _sync_consultation_evidence(
    decision: ExecutiveDecision,
    consultations: list[ExecutiveCouncilConsultation],
) -> None:
    evidence = _load(decision.evidence_json, [])
    if not isinstance(evidence, list):
        evidence = []
    evidence = [
        item
        for item in evidence
        if not isinstance(item, dict) or item.get("type") != "executive_council_consultations"
    ]
    evidence.append(
        {
            "type": "executive_council_consultations",
            "items": [
                {
                    "id": str(item.id),
                    "position": item.consulted_position,
                    "domain": item.domain,
                    "status": item.status,
                    "confidence": item.confidence,
                    "dissent": item.dissent,
                    "evidence": _load(item.evidence_json, []),
                }
                for item in consultations
            ],
        }
    )
    decision.evidence_json = _json(evidence)
    decision.updated_at = _now()


def _hold_ceo_decision(
    session: Session,
    decision: ExecutiveDecision,
    *,
    coordination_token: str,
    reason: str,
    actor: str,
) -> ExecutiveDecision:
    impact = _load(decision.impact_json, {})
    if not isinstance(impact, dict):
        impact = {}
    previous_reason = (
        impact.get("ceo_coordination", {}).get("reason")
        if isinstance(impact.get("ceo_coordination"), dict)
        else None
    )
    impact["ceo_coordination"] = {
        "status": "held",
        "reason": reason,
        "external_action_authorized": False,
    }
    recommendation = f"CEO coordination held: {reason}"
    impact_json = _json(impact)
    now = _now()
    with session.no_autoflush:
        held = session.exec(
            update(ExecutiveDecision)
            .where(
                ExecutiveDecision.id == decision.id,
                ExecutiveDecision.status == "coordinating_ceo",
                ExecutiveDecision.coordination_token == coordination_token,
            )
            .values(
                status="pending_ceo",
                coordination_token=None,
                coordination_claimed_at=None,
                recommendation=recommendation,
                evidence_json=decision.evidence_json,
                impact_json=impact_json,
                updated_at=now,
            )
            .execution_options(synchronize_session=False)
        )
    if held.rowcount != 1:
        session.rollback()
        raise ValueError("CEO coordination lease was lost before the hold was recorded")
    session.expire(decision)
    if previous_reason != reason:
        record_audit(
            session,
            action="ceo_decision_held",
            entity_type="executive_decision",
            entity_id=decision.id,
            after_state={"status": "pending_ceo", "reason": reason},
            reason=reason,
            actor=actor,
            source=SOURCE,
        )
    session.commit()
    session.refresh(decision)
    return decision


def _promote_decision_to_board(
    session: Session,
    decision: ExecutiveDecision,
    work: OrganizationalWorkItem,
    *,
    coordination_token: str,
    reason: str,
    actor: str,
) -> ExecutiveDecision:
    before = {
        "status": decision.status,
        "decision_owner_position": decision.decision_owner_position,
    }
    now = _now()
    with session.no_autoflush:
        promoted = session.exec(
            update(ExecutiveDecision)
            .where(
                ExecutiveDecision.id == decision.id,
                ExecutiveDecision.status == "coordinating_ceo",
                ExecutiveDecision.coordination_token == coordination_token,
            )
            .values(
                status="pending_board",
                coordination_token=None,
                coordination_claimed_at=None,
                decision_owner_position="board",
                recommendation=f"Escalate to the Human Board: {reason}",
                evidence_json=decision.evidence_json,
                updated_at=now,
            )
            .execution_options(synchronize_session=False)
        )
    if promoted.rowcount != 1:
        session.rollback()
        raise ValueError("CEO coordination lease was lost before Board escalation")
    session.expire(decision)
    work.status = "pending_board"
    work.escalated_at = work.escalated_at or now
    work.updated_at = now
    session.add(work)
    risk = session.exec(
        select(RiskEscalation).where(
            RiskEscalation.work_item_id == work.id,
            RiskEscalation.status == "open",
        )
    ).first()
    if risk is None:
        risk = RiskEscalation(
            risk_key=f"risk:{work.id}:ceo-exception",
            work_item_id=work.id,
            category="governance",
            severity="high",
            title=f"CEO exception: {work.title}",
            description=reason,
            evidence_json=_json([{"decision_id": str(decision.id), "reason": reason}]),
            containment_json=_json(["Execution held for Human Board review"]),
            accountable_position_key="ceo",
            escalated_to_position_key="board",
            requires_board_attention=True,
        )
    else:
        risk.escalated_to_position_key = "board"
        risk.requires_board_attention = True
        risk.updated_at = _now()
    session.add(risk)
    record_audit(
        session,
        action="ceo_decision_escalated_to_board",
        entity_type="executive_decision",
        entity_id=decision.id,
        before_state=before,
        after_state={"status": "pending_board", "decision_owner_position": "board"},
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(decision)
    create_board_packet(
        session,
        packet_type="incident",
        actor=actor,
        trigger_key=f"ceo-exception:{decision.id}",
    )
    session.refresh(decision)
    return decision


def _claim_ceo_decision(
    session: Session,
    decision: ExecutiveDecision,
    *,
    actor: str,
) -> tuple[ExecutiveDecision, str | None]:
    now = _now()
    if decision.status == "coordinating_ceo":
        stale_before = now - CEO_COORDINATION_LEASE
        recovered = session.exec(
            update(ExecutiveDecision)
            .where(
                ExecutiveDecision.id == decision.id,
                ExecutiveDecision.status == "coordinating_ceo",
                ExecutiveDecision.coordination_claimed_at <= stale_before,
            )
            .values(
                status="pending_ceo",
                coordination_token=None,
                coordination_claimed_at=None,
                updated_at=now,
            )
            .execution_options(synchronize_session=False)
        )
        if recovered.rowcount == 1:
            record_audit(
                session,
                action="ceo_coordination_stale_claim_recovered",
                entity_type="executive_decision",
                entity_id=decision.id,
                after_state={"status": "pending_ceo"},
                reason="The previous CEO coordination lease expired before a decision was recorded.",
                actor=actor,
                source=SOURCE,
            )
            session.commit()
        else:
            session.rollback()
            raise ValueError("CEO coordination is already in progress")

    coordination_token = str(uuid4())
    claimed = session.exec(
        update(ExecutiveDecision)
        .where(
            ExecutiveDecision.id == decision.id,
            ExecutiveDecision.status == "pending_ceo",
            ExecutiveDecision.authority_level == "L3",
            ExecutiveDecision.decision_owner_position == "ceo",
        )
        .values(
            status="coordinating_ceo",
            coordination_token=coordination_token,
            coordination_claimed_at=now,
            updated_at=now,
        )
        .execution_options(synchronize_session=False)
    )
    if claimed.rowcount != 1:
        session.rollback()
        session.expire_all()
        current = session.get(ExecutiveDecision, decision.id)
        if current is not None and current.status == "approved" and current.decided_by == actor:
            return current, None
        if current is not None and current.status == "coordinating_ceo":
            raise ValueError("CEO coordination is already in progress")
        raise ValueError("Only a CEO-owned pending L3 decision can enter CEO coordination")
    session.expire_all()
    current = session.get(ExecutiveDecision, decision.id)
    if current is None:
        session.rollback()
        raise ValueError("Executive decision not found")
    record_audit(
        session,
        action="ceo_coordination_claimed",
        entity_type="executive_decision",
        entity_id=current.id,
        after_state={
            "status": "coordinating_ceo",
            "lease_seconds": int(CEO_COORDINATION_LEASE.total_seconds()),
        },
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(current)
    return current, coordination_token


def _release_ceo_claim_after_error(
    session: Session,
    decision_id: UUID,
    *,
    coordination_token: str,
    actor: str,
    reason: str,
) -> None:
    session.rollback()
    released = session.exec(
        update(ExecutiveDecision)
        .where(
            ExecutiveDecision.id == decision_id,
            ExecutiveDecision.status == "coordinating_ceo",
            ExecutiveDecision.coordination_token == coordination_token,
        )
        .values(
            status="pending_ceo",
            coordination_token=None,
            coordination_claimed_at=None,
            updated_at=_now(),
        )
        .execution_options(synchronize_session=False)
    )
    if released.rowcount != 1:
        session.rollback()
        return
    record_audit(
        session,
        action="ceo_coordination_claim_released",
        entity_type="executive_decision",
        entity_id=decision_id,
        after_state={"status": "pending_ceo"},
        reason=reason[:1000],
        actor=actor,
        source=SOURCE,
    )
    session.commit()


def _coordinate_claimed_ceo_decision(
    session: Session,
    decision: ExecutiveDecision,
    *,
    coordination_token: str,
    actor: str = "ceo-agent",
) -> ExecutiveDecision:
    """Resolve only evidence-complete, internal L3 work within the CEO mandate."""
    session.refresh(decision)
    if (
        decision.status != "coordinating_ceo"
        or decision.coordination_token != coordination_token
    ):
        raise ValueError("CEO coordination requires an atomic coordination claim")
    if decision.authority_level != "L3" or decision.decision_owner_position != "ceo":
        raise ValueError("CEO coordination cannot decide a Board-owned or non-L3 matter")
    work = session.get(OrganizationalWorkItem, decision.work_item_id) if decision.work_item_id else None
    if work is None:
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason="The decision has no governed work item.",
            actor=actor,
        )
    if decision.requested_by_position == "ceo":
        return _promote_decision_to_board(
            session,
            decision,
            work,
            coordination_token=coordination_token,
            reason="CEO self-approval is prohibited.",
            actor=actor,
        )
    if work.is_emergency:
        return _promote_decision_to_board(
            session,
            decision,
            work,
            coordination_token=coordination_token,
            reason="Emergency matters are reserved for the Human Board.",
            actor=actor,
        )

    control = session.exec(
        select(OrganizationControl).where(OrganizationControl.control_key == "global")
    ).first()
    if control is None:
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason="The Board-governed organization foundation is not bootstrapped.",
            actor=actor,
        )
    if control.status != "active":
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason="The organization is globally paused.",
            actor=actor,
        )
    ceo_position = _position_by_key(session, "ceo")
    if ceo_position is None:
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason="The Board-governed CEO position is not registered.",
            actor=actor,
        )
    if _load(ceo_position.contract_json, {}) != _position_contract("ceo", "L3"):
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason="The persisted CEO contract requires Human Board repair before coordination.",
            actor=actor,
        )
    if _is_suspended(ceo_position):
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason="The CEO position is suspended.",
            actor=actor,
        )

    try:
        required_positions = _required_ceo_consultations(work, decision)
    except ValueError as exc:
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason=str(exc),
            actor=actor,
        )
    consultations = _upsert_executive_consultations(
        session,
        decision=decision,
        work=work,
        required_positions=required_positions,
    )
    _sync_consultation_evidence(decision, consultations)

    action = _work_action(work)
    if action in GOVERNED_EXTERNAL_ACTIONS:
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason=(
                f"{action} remains behind its separate human external-action gate; "
                "CEO coordination cannot authorize or execute it."
            ),
            actor=actor,
        )
    if action not in CEO_AUTO_RESOLVABLE_ACTIONS:
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason=f"{action or 'Unspecified action'} is outside the CEO auto-resolution allowlist.",
            actor=actor,
        )
    if work.status != "pending_ceo":
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason="Departmental analysis is not complete and pending CEO review.",
            actor=actor,
        )
    incomplete = [item.consulted_position for item in consultations if item.status != "completed"]
    if incomplete:
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason=f"Required executive consultations are incomplete: {', '.join(incomplete)}.",
            actor=actor,
        )
    dissenting = [item.consulted_position for item in consultations if item.dissent]
    if dissenting:
        return _promote_decision_to_board(
            session,
            decision,
            work,
            coordination_token=coordination_token,
            reason=f"Unresolved executive dissent from: {', '.join(dissenting)}.",
            actor=actor,
        )

    outputs = list(
        session.exec(
            select(OrganizationalActionOutput).where(
                OrganizationalActionOutput.work_item_id == work.id,
                OrganizationalActionOutput.status == "completed",
            )
        ).all()
    )
    if not outputs or any(not _load(item.evidence_json, []) for item in outputs):
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason="Completed, provenance-bearing organizational outputs are required.",
            actor=actor,
        )
    aggregate_confidence = round(
        sum(item.confidence for item in outputs) / len(outputs), 4
    )
    if aggregate_confidence < CEO_MINIMUM_CONFIDENCE:
        return _hold_ceo_decision(
            session,
            decision,
            coordination_token=coordination_token,
            reason=(
                f"Aggregate evidence confidence {aggregate_confidence:.2f} is below the "
                f"CEO threshold {CEO_MINIMUM_CONFIDENCE:.2f}."
            ),
            actor=actor,
        )

    evidence = _load(decision.evidence_json, [])
    if not isinstance(evidence, list):
        evidence = []
    evidence = [
        item
        for item in evidence
        if not isinstance(item, dict) or item.get("type") != "ceo_coordination_receipt"
    ]
    evidence.append(
        {
            "type": "ceo_coordination_receipt",
            "status": "eligible",
            "action": action,
            "work_item_id": str(work.id),
            "requested_by_position": decision.requested_by_position,
            "consultation_ids": [str(item.id) for item in consultations],
            "action_output_ids": [str(item.id) for item in outputs],
            "aggregate_confidence": aggregate_confidence,
            "external_action_authorized": False,
        }
    )
    decision.evidence_json = _json(evidence)
    decision.recommendation = (
        "Approve closure of the bounded internal analysis. This accepts the recorded "
        "executive position and authorizes no client communication, authority submission, "
        "payment, contract, or production deployment."
    )
    decision.alternatives_json = _json(
        [
            {"option": "return", "effect": "Request stronger or newer evidence."},
            {"option": "reject", "effect": "Do not adopt the internal recommendation."},
            {"option": "escalate", "effect": "Send only an authority conflict or exception to the Board."},
        ]
    )
    impact = _load(decision.impact_json, {})
    if not isinstance(impact, dict):
        impact = {}
    impact["ceo_coordination"] = {
        "status": "eligible",
        "aggregate_confidence": aggregate_confidence,
        "decision_effect": "close_internal_analysis_only",
        "external_action_authorized": False,
        "board_attention_required": False,
    }
    decision.impact_json = _json(impact)
    decision.updated_at = _now()
    record_audit(
        session,
        action="ceo_decision_coordinated",
        entity_type="executive_decision",
        entity_id=decision.id,
        after_state={
            "action": action,
            "consultations": [item.consulted_position for item in consultations],
            "aggregate_confidence": aggregate_confidence,
            "external_action_authorized": False,
        },
        actor=actor,
        source=SOURCE,
    )
    return decide_executive_decision(
        session,
        decision,
        outcome="approved",
        reason=(
            f"CEO accepted the evidence-complete internal {work.department} analysis within L3. "
            "No external action was authorized."
        ),
        actor=actor,
        actor_position="ceo",
        coordination_token=coordination_token,
    )


def coordinate_ceo_decision(
    session: Session,
    decision: ExecutiveDecision,
    *,
    actor: str = "ceo-agent",
) -> ExecutiveDecision:
    """Atomically coordinate one evidence-complete, internal CEO-owned L3 decision."""
    session.refresh(decision)
    if decision.status == "approved" and decision.decided_by == actor:
        return decision
    claimed, coordination_token = _claim_ceo_decision(session, decision, actor=actor)
    if claimed.status == "approved" and claimed.decided_by == actor:
        return claimed
    if coordination_token is None:
        raise ValueError("CEO coordination claim token was not issued")
    try:
        return _coordinate_claimed_ceo_decision(
            session,
            claimed,
            coordination_token=coordination_token,
            actor=actor,
        )
    except Exception as exc:
        _release_ceo_claim_after_error(
            session,
            claimed.id,
            coordination_token=coordination_token,
            actor=actor,
            reason=f"{type(exc).__name__}: {exc}",
        )
        raise


def scan_pending_ceo_decisions(
    session: Session,
    *,
    limit: int = 25,
    actor: str = "ceo-agent",
) -> dict[str, Any]:
    stale_before = _now() - CEO_COORDINATION_LEASE
    decisions = list(
        session.exec(
            select(ExecutiveDecision)
            .where(
                or_(
                    ExecutiveDecision.status == "pending_ceo",
                    and_(
                        ExecutiveDecision.status == "coordinating_ceo",
                        ExecutiveDecision.coordination_claimed_at <= stale_before,
                    ),
                )
            )
            .order_by(ExecutiveDecision.created_at)
            .limit(max(1, min(limit, 100)))
        ).all()
    )
    approved: list[str] = []
    held: list[str] = []
    escalated: list[str] = []
    errors: list[dict[str, str]] = []
    for decision in decisions:
        try:
            result = coordinate_ceo_decision(session, decision, actor=actor)
        except ValueError as exc:
            errors.append({"decision_id": str(decision.id), "reason": str(exc)})
            continue
        if result.status == "approved":
            approved.append(str(result.id))
        elif result.status == "pending_board":
            escalated.append(str(result.id))
        else:
            held.append(str(result.id))
    return {
        "examined": len(decisions),
        "approved": approved,
        "held": held,
        "escalated": escalated,
        "errors": errors,
    }


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
            if not department_runtime_available(item.department, _work_action(item)):
                continue
            if item.last_error:
                continue
            item.status = "queued"
            item.updated_at = _now()
            session.add(item)
    record_audit(session, action=f"organization_{status}", entity_type="organization_control", entity_id=control.id, before_state={"status": before}, after_state={"status": status}, reason=reason, actor=actor, source=SOURCE)
    session.commit()
    session.refresh(control)
    return control


def _resolve_work_risks(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    outcome: str,
) -> None:
    if outcome not in {"approved", "rejected"}:
        return
    now = _now()
    risks = session.exec(
        select(RiskEscalation).where(
            RiskEscalation.work_item_id == work.id,
            RiskEscalation.status == "open",
        )
    ).all()
    for risk in risks:
        if risk.category != "governance" or risk.is_emergency:
            continue
        risk.status = "resolved"
        risk.resolved_at = now
        risk.updated_at = now
        session.add(risk)


def _work_has_completed_analysis(session: Session, work: OrganizationalWorkItem) -> bool:
    delegations = session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)
    ).all()
    if not delegations or any(item.status != "completed" for item in delegations):
        return False
    outputs = session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work.id
        )
    ).all()
    return len(outputs) == len(delegations) and all(item.status == "completed" for item in outputs)


def _apply_decision_outcome_to_work(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    outcome: str,
) -> None:
    now = _now()
    if outcome == "approved":
        action = _work_action(work)
        if department_runtime_available(work.department, action) and _work_has_completed_analysis(
            session,
            work,
        ):
            work.status = "completed"
            work.completed_at = now
            work.last_error = None
            _resolve_work_risks(session, work, outcome=outcome)
        else:
            work.status = "held"
            work.completed_at = None
            work.last_error = (
                "Decision approval recorded, but execution remains held until a registered runtime "
                "produces complete governed analysis; approval is not execution."
            )
    else:
        work.status = outcome
        work.completed_at = now
        _resolve_work_risks(session, work, outcome=outcome)
    work.execution_started_at = None
    work.next_retry_at = None
    work.updated_at = now
    session.add(work)


def decide_executive_decision(
    session: Session,
    decision: ExecutiveDecision,
    *,
    outcome: str,
    reason: str,
    actor: str,
    actor_position: str,
    coordination_token: str | None = None,
) -> ExecutiveDecision:
    if outcome not in {"approved", "rejected", "returned"}:
        raise ValueError("Unsupported decision outcome")
    if decision.status not in {"pending_ceo", "coordinating_ceo", "pending_board"}:
        raise ValueError("Decision is not pending")
    if actor_position == "board":
        if decision.status != "pending_board" or decision.decision_owner_position != "board":
            raise ValueError(
                "Board decision requires a Board-owned pending decision; use the explicit Board override lane for L3"
            )
    elif actor_position == "ceo":
        if (
            decision.status != "coordinating_ceo"
            or coordination_token is None
            or decision.coordination_token != coordination_token
            or decision.decision_owner_position != "ceo"
            or decision.authority_level != "L3"
        ):
            raise ValueError("CEO may decide only CEO-owned pending L3 matters")
        if decision.requested_by_position == "ceo":
            raise ValueError("CEO self-approval is prohibited")
        evidence = _load(decision.evidence_json, [])
        receipt = next(
            (
                item
                for item in evidence
                if isinstance(item, dict)
                and item.get("type") == "ceo_coordination_receipt"
                and item.get("status") == "eligible"
                and item.get("external_action_authorized") is False
            ),
            None,
        )
        if receipt is None:
            raise ValueError("CEO decision requires an eligible coordination receipt")
        work = session.get(OrganizationalWorkItem, decision.work_item_id) if decision.work_item_id else None
        if work is None or work.status != "pending_ceo" or work.is_emergency:
            raise ValueError("CEO decision requires completed, non-emergency departmental analysis")
        if _work_action(work) not in CEO_AUTO_RESOLVABLE_ACTIONS:
            raise ValueError("CEO direct resolution is limited to allowlisted internal actions")
        consultations = session.exec(
            select(ExecutiveCouncilConsultation).where(
                ExecutiveCouncilConsultation.decision_id == decision.id
            )
        ).all()
        if not consultations or any(
            item.status != "completed" or item.dissent for item in consultations
        ):
            raise ValueError("CEO decision requires complete, non-dissenting executive consultations")
    else:
        raise ValueError("Unsupported decision actor position")
    now = _now()
    if actor_position == "ceo":
        with session.no_autoflush:
            decided = session.exec(
                update(ExecutiveDecision)
                .where(
                    ExecutiveDecision.id == decision.id,
                    ExecutiveDecision.status == "coordinating_ceo",
                    ExecutiveDecision.coordination_token == coordination_token,
                )
                .values(
                    status=outcome,
                    coordination_token=None,
                    coordination_claimed_at=None,
                    decided_by=actor,
                    decision_reason=reason.strip(),
                    decided_at=now,
                    recommendation=decision.recommendation,
                    alternatives_json=decision.alternatives_json,
                    evidence_json=decision.evidence_json,
                    impact_json=decision.impact_json,
                    updated_at=now,
                )
                .execution_options(synchronize_session=False)
            )
        if decided.rowcount != 1:
            session.rollback()
            raise ValueError("CEO coordination lease was lost before the decision was recorded")
        session.expire(decision)
    else:
        decision.status = outcome
        decision.coordination_token = None
        decision.coordination_claimed_at = None
        decision.decided_by = actor
        decision.decision_reason = reason.strip()
        decision.decided_at = now
        decision.updated_at = now
        session.add(decision)
    work = session.get(OrganizationalWorkItem, decision.work_item_id) if decision.work_item_id else None
    if work is not None:
        _apply_decision_outcome_to_work(session, work, outcome=outcome)
    record_audit(
        session,
        action=f"executive_decision_{outcome}",
        entity_type="executive_decision",
        entity_id=decision.id,
        after_state={
            "status": outcome,
            "decided_by": actor,
            "actor_position": actor_position,
            "external_action_authorized": False,
        },
        reason=reason,
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(decision)
    return decision


def board_packet_snapshot(session: Session) -> dict[str, Any]:
    ensure_foundation_positions(session)
    session.commit()
    positions = session.exec(select(OrganizationPosition).where(OrganizationPosition.status == "active").order_by(OrganizationPosition.department, OrganizationPosition.title)).all()
    work = session.exec(select(OrganizationalWorkItem).order_by(OrganizationalWorkItem.created_at.desc()).limit(12)).all()
    decisions = session.exec(select(ExecutiveDecision).where(ExecutiveDecision.status.in_(["pending_ceo", "coordinating_ceo", "pending_board"])).order_by(ExecutiveDecision.created_at.desc())).all()
    risks = session.exec(select(RiskEscalation).where(RiskEscalation.status == "open").order_by(RiskEscalation.created_at.desc())).all()
    packets = session.exec(select(BoardPacket).order_by(BoardPacket.created_at.desc()).limit(5)).all()
    control = session.exec(select(OrganizationControl).where(OrganizationControl.control_key == "global")).one()
    return {
        "generated_at": _now(),
        "control": control,
        "metrics": {
            "active_positions": len(positions),
            "queued_work": session.exec(select(func.count()).select_from(OrganizationalWorkItem).where(OrganizationalWorkItem.status == "queued")).one(),
            "pending_ceo": sum(
                1 for item in decisions if item.status in {"pending_ceo", "coordinating_ceo"}
            ),
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
    pending_decisions = session.exec(select(ExecutiveDecision).where(ExecutiveDecision.status.in_(["pending_ceo", "coordinating_ceo", "pending_board"])).order_by(ExecutiveDecision.created_at.desc())).all()
    open_risks = session.exec(select(RiskEscalation).where(RiskEscalation.status == "open").order_by(RiskEscalation.created_at.desc())).all()
    recent_work = session.exec(select(OrganizationalWorkItem).order_by(OrganizationalWorkItem.created_at.desc()).limit(20)).all()

    board_decisions = [item for item in pending_decisions if item.status == "pending_board"]
    ceo_decisions = [
        item for item in pending_decisions if item.status in {"pending_ceo", "coordinating_ceo"}
    ]
    emergencies = [item for item in open_risks if item.is_emergency]
    board_decision_ids = [item.id for item in board_decisions]
    council_consultations = (
        list(
            session.exec(
                select(ExecutiveCouncilConsultation).where(
                    ExecutiveCouncilConsultation.decision_id.in_(board_decision_ids)
                )
            ).all()
        )
        if board_decision_ids
        else []
    )
    dissenting_consultations = [item for item in council_consultations if item.dissent]

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
    if dissenting_consultations:
        summary_lines.append(
            f"Unresolved executive dissent is recorded on {len(dissenting_consultations)} consultation(s)."
        )

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
        "dissenting_views": [
            {
                "consultation_id": str(item.id),
                "decision_id": str(item.decision_id),
                "position": item.consulted_position,
                "domain": item.domain,
                "recommendation": item.recommendation,
                "confidence": item.confidence,
                "evidence": _load(item.evidence_json, []),
            }
            for item in dissenting_consultations
        ],
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

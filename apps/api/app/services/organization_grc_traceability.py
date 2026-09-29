from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision, OrganizationBlocker, OrganizationControl,
    OrganizationHumanAction, OrganizationHumanActionRequest, OrganizationRecordReference,
    OrganizationReferenceRole, OrganizationReferenceTargetType,
    OrganizationalWorkItem, RiskEscalation,
)
from app.models.autonomy_promotion_policy import CapabilityAutonomyPromotionPolicy
from app.models.autonomy_evidence_evaluation_policy import CapabilityAutonomyEvidenceEvaluationPolicy
from app.services.organization_capability_architecture import (
    CapabilityDomain,
    capability_domain_for_position,
)
from app.services.organization_transparency import (
    TransparencyActivityRecord,
    activities_for_work_item,
)


@dataclass(frozen=True, slots=True)
class GRCCapabilityRef:
    domain_key: str
    name: str
    executive_position: str


@dataclass(frozen=True, slots=True)
class GRCDecisionTrace:
    decision_id: UUID
    decision_key: str
    decision_type: str
    status: str
    decision_owner_position: str
    owner_capability: GRCCapabilityRef | None
    supersedes_decision_id: UUID | None
    activity_records: tuple[TransparencyActivityRecord, ...]


@dataclass(frozen=True, slots=True)
class GRCHumanActionTrace:
    action_id: UUID
    action_type: str
    human_actor_id: str
    outcome: str
    reason: str | None
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class GRCHumanRequestTrace:
    request_id: UUID
    request_type: str
    status: str
    required_role: str
    outcome: str | None
    completed_by_human_id: str | None
    actions: tuple[GRCHumanActionTrace, ...]


@dataclass(frozen=True, slots=True)
class GRCGovernanceDecisionTrace:
    decision_id: UUID
    decision_type: str
    status: str
    decided_by: str | None
    decision_reason: str | None
    supersedes_decision_id: UUID | None
    human_requests: tuple[GRCHumanRequestTrace, ...]


@dataclass(frozen=True, slots=True)
class GRCBlockerTrace:
    blocker_id: UUID
    blocker_type: str
    status: str
    decision_id: UUID | None
    supersedes_blocker_id: UUID | None
    resolution_summary: str | None
    resolving_actor_id: str | None
    waived_by_human_id: str | None
    waiver_reason: str | None
    human_requests: tuple[GRCHumanRequestTrace, ...]


@dataclass(frozen=True, slots=True)
class GRCRiskTrace:
    risk_id: UUID
    risk_key: str
    category: str
    severity: str
    status: str
    title: str
    requires_board_attention: bool
    is_emergency: bool
    work_item_id: UUID
    work_item_key: str
    work_item_status: str
    objective_key: str | None
    phase_key: str | None
    department: str
    accountable_position_key: str
    accountable_capability: GRCCapabilityRef | None
    linked_work_item_decisions: tuple[GRCDecisionTrace, ...]
    governance_decisions: tuple[GRCGovernanceDecisionTrace, ...] = ()
    remediation_blockers: tuple[GRCBlockerTrace, ...] = ()
    # Explicit reference identities only; no control effectiveness or risk mitigation claim.
    control_refs: tuple[str, ...] = ()


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _capability_ref(domain: CapabilityDomain | None) -> GRCCapabilityRef | None:
    if domain is None:
        return None
    return GRCCapabilityRef(
        domain_key=domain.domain_key,
        name=domain.name,
        executive_position=domain.executive_position,
    )


def _current_mapping_ref(session: Session, reference: OrganizationRecordReference, tenant_key: str) -> str | None:
    """Include only a current, exact target from the governed risk mapping allowlist."""
    if (
        reference.reference_role is not OrganizationReferenceRole.governance_mapping
        or not (reference.label or "").strip()
    ):
        return None
    try:
        mapping_metadata = json.loads(reference.metadata_json)
    except (TypeError, ValueError):
        return None
    if not isinstance(mapping_metadata, dict) or mapping_metadata.get("mapping_state", "current") != "current":
        return None
    try:
        target_id = UUID(reference.target_id)
    except ValueError:
        return None
    if reference.target_type is OrganizationReferenceTargetType.organization_control:
        if tenant_key != "default":
            return None
        control = session.get(OrganizationControl, target_id)
        if control is None or control.control_key != "global" or control.status not in {"active", "paused"}:
            return None
    elif reference.target_type in {
        OrganizationReferenceTargetType.capability_autonomy_promotion_policy,
        OrganizationReferenceTargetType.capability_autonomy_evidence_evaluation_policy,
    }:
        model = (
            CapabilityAutonomyPromotionPolicy
            if reference.target_type is OrganizationReferenceTargetType.capability_autonomy_promotion_policy
            else CapabilityAutonomyEvidenceEvaluationPolicy
        )
        policy = session.get(model, target_id)
        if (
            policy is None or policy.tenant_key != tenant_key
            or reference.target_version != policy.record_fingerprint
            or session.exec(select(model.id).where(
                model.tenant_key == tenant_key, model.supersedes_policy_id == policy.id,
            )).first() is not None
        ):
            return None
    else:
        return None
    return f"{reference.target_type.value}:{target_id}"


def project_organization_grc_traceability(
    session: Session,
    *,
    tenant_key: str,
) -> tuple[GRCRiskTrace, ...]:
    """Project current risk traceability from existing governed records, read-only.

    ``RiskEscalation`` predates tenant columns, so its linked WorkItem is the fail-closed
    tenant boundary. Orphan risks are intentionally invisible here. Decisions are factual
    WorkItem neighbours, not a claim that a decision caused or mitigated a risk. Their
    durable Activity history is delegated to the existing transparency projection and is
    narrowed by the semantic-activity source identity ``executive_decision/<uuid>``.

    Capability data is an annotation from the canonical capability architecture.
    ``control_refs`` comes only from exact, current, human-governed reference records.
    These references attest a relationship, not policy applicability, enforcement,
    control effectiveness or risk mitigation. Approval/exception and remediation
    lineage follows exact risk/blocker/decision/request IDs, not WorkItem proximity.
    """

    normalized_tenant = tenant_key.strip()
    if not normalized_tenant:
        raise ValueError("tenant_key is required")

    # A query normally autoflushes pending ORM state. Suppress that side effect so this
    # projection remains read-only even when invoked inside a wider unit of work.
    with session.no_autoflush:
        work_items = session.exec(
            select(OrganizationalWorkItem).where(
                OrganizationalWorkItem.tenant_key == normalized_tenant
            )
        ).all()
        if not work_items:
            return ()

        work_by_id = {work.id: work for work in work_items}
        work_ids = tuple(work_by_id)
        risks = session.exec(
            select(RiskEscalation).where(RiskEscalation.work_item_id.in_(work_ids))
        ).all()
        risks = [
            risk
            for risk in risks
            if risk.work_item_id is not None and risk.work_item_id in work_by_id
        ]
        if not risks:
            return ()

        risk_ids = tuple(risk.id for risk in risks)
        references = session.exec(select(OrganizationRecordReference).where(
            OrganizationRecordReference.tenant_key == normalized_tenant,
            OrganizationRecordReference.risk_escalation_id.in_(risk_ids),
            OrganizationRecordReference.reference_role == OrganizationReferenceRole.governance_mapping,
        )).all()
        superseded_refs = {ref.supersedes_reference_id for ref in references if ref.supersedes_reference_id is not None}
        refs_by_risk: dict[UUID, list[str]] = {}
        for reference in references:
            if reference.id in superseded_refs:
                continue
            mapped = _current_mapping_ref(session, reference, normalized_tenant)
            if mapped is not None and reference.risk_escalation_id is not None:
                refs_by_risk.setdefault(reference.risk_escalation_id, []).append(mapped)

        risk_work_ids = tuple({risk.work_item_id for risk in risks if risk.work_item_id is not None})
        decisions = session.exec(
            select(ExecutiveDecision).where(
                ExecutiveDecision.tenant_key == normalized_tenant,
                ExecutiveDecision.work_item_id.in_(risk_work_ids),
            )
        ).all()

        decisions_by_work: dict[UUID, list[ExecutiveDecision]] = {}
        for decision in decisions:
            if decision.work_item_id is None or decision.work_item_id not in work_by_id:
                continue
            decisions_by_work.setdefault(decision.work_item_id, []).append(decision)

        decision_by_id = {decision.id: decision for decision in decisions}
        blockers = session.exec(select(OrganizationBlocker).where(
            OrganizationBlocker.tenant_key == normalized_tenant,
            OrganizationBlocker.risk_escalation_id.in_(risk_ids),
        )).all()
        risk_by_id = {risk.id: risk for risk in risks}
        blockers_by_risk: dict[UUID, list[OrganizationBlocker]] = {}
        blocker_by_id: dict[UUID, OrganizationBlocker] = {}
        for blocker in blockers:
            risk = risk_by_id.get(blocker.risk_escalation_id)
            if risk is None or blocker.work_item_id != risk.work_item_id:
                continue
            if blocker.decision_id is not None and (
                blocker.decision_id not in decision_by_id
                or decision_by_id[blocker.decision_id].work_item_id != risk.work_item_id
                or (
                    decision_by_id[blocker.decision_id].source_object_type == "risk_escalation"
                    and decision_by_id[blocker.decision_id].source_object_id != str(risk.id)
                )
            ):
                continue
            blockers_by_risk.setdefault(risk.id, []).append(blocker)
            blocker_by_id[blocker.id] = blocker

        governance_decisions_by_risk: dict[UUID, list[ExecutiveDecision]] = {}
        for risk in risks:
            explicit_ids = {blocker.decision_id for blocker in blockers_by_risk.get(risk.id, ())}
            governance_decisions_by_risk[risk.id] = [
                decision for decision in decisions_by_work.get(risk.work_item_id, ())
                if decision.id in explicit_ids or (
                    decision.source_object_type == "risk_escalation"
                    and decision.source_object_id == str(risk.id)
                )
            ]

        blocker_ids = tuple(blocker_by_id)
        direct_decision_ids = tuple({
            decision.id for risk in risks
            for decision in governance_decisions_by_risk[risk.id]
            if decision.source_object_type == "risk_escalation"
            and decision.source_object_id == str(risk.id)
        })
        requests: dict[UUID, OrganizationHumanActionRequest] = {}
        if blocker_ids:
            for request in session.exec(select(OrganizationHumanActionRequest).where(
                OrganizationHumanActionRequest.tenant_key == normalized_tenant,
                OrganizationHumanActionRequest.blocker_id.in_(blocker_ids),
            )).all():
                requests[request.id] = request
        if direct_decision_ids:
            for request in session.exec(select(OrganizationHumanActionRequest).where(
                OrganizationHumanActionRequest.tenant_key == normalized_tenant,
                OrganizationHumanActionRequest.decision_id.in_(direct_decision_ids),
            )).all():
                requests[request.id] = request
        actions_by_request: dict[UUID, list[OrganizationHumanAction]] = {}
        if requests:
            actions = session.exec(select(OrganizationHumanAction).where(
                OrganizationHumanAction.tenant_key == normalized_tenant,
                OrganizationHumanAction.human_action_request_id.in_(tuple(requests)),
            )).all()
            for action in actions:
                request = requests[action.human_action_request_id]
                if (
                    (action.work_item_id is not None and action.work_item_id != request.work_item_id)
                    or (action.blocker_id is not None and action.blocker_id != request.blocker_id)
                    or (action.decision_id is not None and action.decision_id != request.decision_id)
                ):
                    continue
                actions_by_request.setdefault(request.id, []).append(action)

        def request_trace(request: OrganizationHumanActionRequest) -> GRCHumanRequestTrace:
            return GRCHumanRequestTrace(
                request_id=request.id,
                request_type=_enum_value(request.request_type),
                status=_enum_value(request.status),
                required_role=request.required_role,
                outcome=request.outcome,
                completed_by_human_id=request.completed_by_human_id,
                actions=tuple(
                    GRCHumanActionTrace(
                        action_id=action.id,
                        action_type=_enum_value(action.action_type),
                        human_actor_id=action.human_actor_id,
                        outcome=action.outcome,
                        reason=action.reason,
                        occurred_at=action.occurred_at,
                    )
                    for action in sorted(actions_by_request.get(request.id, ()), key=lambda item: (item.occurred_at, str(item.id)))
                ),
            )

        activities_by_work: dict[UUID, tuple[TransparencyActivityRecord, ...]] = {}
        for work_id in sorted(risk_work_ids, key=str):
            activities_by_work[work_id] = activities_for_work_item(
                session,
                tenant_key=normalized_tenant,
                work_item_id=work_id,
            )

    traces: list[GRCRiskTrace] = []
    for risk in sorted(risks, key=lambda item: (item.risk_key, str(item.id))):
        assert risk.work_item_id is not None
        work = work_by_id[risk.work_item_id]
        activity_records = activities_by_work.get(work.id, ())

        decision_traces: list[GRCDecisionTrace] = []
        for decision in sorted(
            decisions_by_work.get(work.id, ()),
            key=lambda item: (item.decision_key, str(item.id)),
        ):
            decision_activity_records = tuple(
                record
                for record in activity_records
                if record.source_object_type == "executive_decision"
                and record.source_object_id == str(decision.id)
                and record.work_item_id == work.id
            )
            decision_traces.append(
                GRCDecisionTrace(
                    decision_id=decision.id,
                    decision_key=decision.decision_key,
                    decision_type=_enum_value(decision.decision_type),
                    status=decision.status,
                    decision_owner_position=decision.decision_owner_position,
                    owner_capability=_capability_ref(
                        capability_domain_for_position(decision.decision_owner_position)
                    ),
                    supersedes_decision_id=decision.supersedes_decision_id,
                    activity_records=decision_activity_records,
                )
            )

        risk_blockers = sorted(blockers_by_risk.get(risk.id, ()), key=lambda item: (item.created_at, str(item.id)))
        blocker_traces = tuple(
            GRCBlockerTrace(
                blocker_id=blocker.id,
                blocker_type=_enum_value(blocker.blocker_type),
                status=_enum_value(blocker.status),
                decision_id=blocker.decision_id,
                supersedes_blocker_id=blocker.supersedes_blocker_id,
                resolution_summary=blocker.resolution_summary,
                resolving_actor_id=blocker.resolving_actor_id,
                waived_by_human_id=blocker.waived_by_human_id,
                waiver_reason=blocker.waiver_reason,
                human_requests=tuple(
                    request_trace(request)
                    for request in sorted(requests.values(), key=lambda item: (item.created_at, str(item.id)))
                    if request.blocker_id == blocker.id
                    and request.work_item_id in (None, work.id)
                    and request.decision_id in (None, blocker.decision_id)
                ),
            )
            for blocker in risk_blockers
        )
        governance_decisions = tuple(
            GRCGovernanceDecisionTrace(
                decision_id=decision.id,
                decision_type=_enum_value(decision.decision_type),
                status=decision.status,
                decided_by=decision.decided_by,
                decision_reason=decision.decision_reason,
                supersedes_decision_id=decision.supersedes_decision_id,
                human_requests=tuple(
                    request_trace(request)
                    for request in sorted(requests.values(), key=lambda item: (item.created_at, str(item.id)))
                    if request.blocker_id is None and request.decision_id == decision.id
                    and request.work_item_id in (None, work.id)
                    and decision.source_object_type == "risk_escalation"
                    and decision.source_object_id == str(risk.id)
                ),
            )
            for decision in sorted(governance_decisions_by_risk[risk.id], key=lambda item: (item.created_at, str(item.id)))
        )
        traces.append(
            GRCRiskTrace(
                risk_id=risk.id,
                risk_key=risk.risk_key,
                category=risk.category,
                severity=risk.severity,
                status=risk.status,
                title=risk.title,
                requires_board_attention=risk.requires_board_attention,
                is_emergency=risk.is_emergency,
                work_item_id=work.id,
                work_item_key=work.idempotency_key,
                work_item_status=work.status,
                objective_key=work.objective_key,
                phase_key=work.phase_key,
                department=work.department,
                accountable_position_key=risk.accountable_position_key,
                accountable_capability=_capability_ref(
                    capability_domain_for_position(risk.accountable_position_key)
                ),
                linked_work_item_decisions=tuple(decision_traces),
                governance_decisions=governance_decisions,
                remediation_blockers=blocker_traces,
                control_refs=tuple(sorted(set(refs_by_risk.get(risk.id, ())))),
            )
        )

    return tuple(traces)

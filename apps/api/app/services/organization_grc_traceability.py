from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import ExecutiveDecision, OrganizationalWorkItem, RiskEscalation
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
    # Phase 18A deliberately exposes no inferred risk->control relationship. A later
    # slice may populate this only from an explicit governed mapping contract.
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

    Capability data is an annotation from the canonical capability architecture. This
    projection never creates or updates risks, controls, decisions, Activities, policy,
    authority, or capability assignments. In particular it does not infer a control from
    category/name similarity; ``control_refs`` stays empty until an explicit mapping is
    governed by a later phase.
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
            )
        )

    return tuple(traces)

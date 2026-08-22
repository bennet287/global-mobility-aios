from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationPosition, OrganizationalWorkItem
from app.services.organization_agent_runtime import (
    AgentRuntimeProfile,
    EmployeeRuntimeBinding,
    bind_employee_runtime,
)
from app.services.organization_command import DependencyConflict, InvalidTransition, OrganizationCommandContext
from app.services.organization_context_broker import (
    ContextBundle,
    ContextPurpose,
    build_work_item_context_bundle,
)
from app.services.organization_work import create_work_item, start_work_item


AUSTRIA_MOBILITY_OBJECTIVE_RUNTIME_CONTRACT_VERSION = "austria-mobility-objective-runtime.v1"
AUSTRIA_MOBILITY_OBJECTIVE_ROUTE = "at-rwr-skilled-worker-shortage-occupation-2026"
AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION = "mobility_operations_lead"
AUSTRIA_MOBILITY_PATHWAY_POSITION = "pathway_operations_specialist"
AUSTRIA_MOBILITY_REGULATORY_POSITION = "regulatory_intelligence_analyst"
AUSTRIA_MOBILITY_SPECIALIST_POSITIONS = (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
)


@dataclass(frozen=True, slots=True)
class AustriaMobilityObjectivePlan:
    """One bounded J.1 objective decomposed onto existing organization primitives.

    This is not a Mission persistence model and does not grant authority. The root and
    specialist work remain canonical OrganizationalWorkItems owned by persistent
    OrganizationPositions.
    """

    root_work_item: OrganizationalWorkItem
    pathway_work_item: OrganizationalWorkItem
    regulatory_work_item: OrganizationalWorkItem


@dataclass(frozen=True, slots=True)
class AustriaSpecialistRuntimeBinding:
    position_key: str
    work_item_id: UUID
    context: ContextBundle
    runtime: EmployeeRuntimeBinding


@dataclass(frozen=True, slots=True)
class AustriaObjectiveReadiness:
    root_work_item_id: UUID
    ready_for_owner_synthesis: bool
    completed_positions: tuple[str, ...]
    pending_positions: tuple[str, ...]
    reasons: tuple[str, ...]


def _active_position(session: Session, position_key: str) -> OrganizationPosition:
    position = session.exec(
        select(OrganizationPosition).where(
            OrganizationPosition.position_key == position_key,
            OrganizationPosition.status == "active",
        )
    ).first()
    if position is None:
        raise DependencyConflict(f"required active organization position is unavailable: {position_key}")
    return position


def _objective_key(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise DependencyConflict("objective key is required")
    return normalized


def _work_key(context: OrganizationCommandContext, objective_key: str, suffix: str) -> str:
    return f"j1:austria:{context.tenant_key}:{objective_key}:{suffix}"


def create_austria_mobility_objective(
    session: Session,
    context: OrganizationCommandContext,
    *,
    objective_key: str,
) -> AustriaMobilityObjectivePlan:
    """Create the first bounded J objective using existing WorkItem primitives only.

    The root owner coordinates two persistent specialists:
    - Pathway & Eligibility Operations Specialist
    - Regulatory Intelligence Analyst

    No agent/model execution happens here. K owns execution. J.1 only establishes the
    durable organization topology and enough bounded working context for later runtime
    binding.
    """

    key = _objective_key(objective_key)
    owner = _active_position(session, AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION)
    pathway = _active_position(session, AUSTRIA_MOBILITY_PATHWAY_POSITION)
    regulatory = _active_position(session, AUSTRIA_MOBILITY_REGULATORY_POSITION)

    root = create_work_item(
        session,
        context,
        idempotency_key=_work_key(context, key, "root"),
        title="Austria mobility objective — shortage-occupation pathway",
        objective=(
            "Coordinate an evidence-bounded assessment of the 2026 Austrian Red-White-Red Card "
            "Skilled Worker in a Shortage Occupation route without producing a legal or authority decision."
        ),
        department=owner.department,
        authority_level=owner.authority_level,
        assigned_position_key=owner.position_key,
        work_type="mobility_objective",
        priority="high",
        objective_key=key,
        phase_key="J.1",
        risk_level="routine",
        context_payload={
            "contract_version": AUSTRIA_MOBILITY_OBJECTIVE_RUNTIME_CONTRACT_VERSION,
            "country": "Austria",
            "jurisdiction": "AT",
            "route_key": AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
            "claim_boundary": "internal organization-runtime proof; no legal or authority decision",
        },
    )
    # The objective owner becomes active immediately; exact replay is safe because the
    # existing transition helper is idempotent when the target state is already current.
    root = start_work_item(
        session,
        context,
        work_item_id=root.id,
        reason="Start bounded J.1 Austria organization-runtime objective.",
    )

    pathway_work = create_work_item(
        session,
        context,
        idempotency_key=_work_key(context, key, "pathway"),
        title="Assess Austria shortage-occupation pathway requirements",
        objective=(
            "Prepare bounded pathway/eligibility operations findings for the objective owner from governed context."
        ),
        department=pathway.department,
        authority_level=pathway.authority_level,
        assigned_position_key=pathway.position_key,
        work_type="mobility_specialist_work",
        priority="high",
        parent_work_item_id=root.id,
        objective_key=key,
        phase_key="J.1.pathway",
        risk_level="routine",
        context_payload={
            "contract_version": AUSTRIA_MOBILITY_OBJECTIVE_RUNTIME_CONTRACT_VERSION,
            "country": "Austria",
            "jurisdiction": "AT",
            "route_key": AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
            "collaboration_role": "pathway_requirements",
            "root_work_item_id": str(root.id),
        },
    )

    regulatory_work = create_work_item(
        session,
        context,
        idempotency_key=_work_key(context, key, "regulatory"),
        title="Verify Austria regulatory-source boundary",
        objective=(
            "Prepare bounded regulatory-intelligence findings and source-boundary questions for the objective owner."
        ),
        department=regulatory.department,
        authority_level=regulatory.authority_level,
        assigned_position_key=regulatory.position_key,
        work_type="mobility_specialist_work",
        priority="high",
        parent_work_item_id=root.id,
        objective_key=key,
        phase_key="J.1.regulatory",
        risk_level="routine",
        context_payload={
            "contract_version": AUSTRIA_MOBILITY_OBJECTIVE_RUNTIME_CONTRACT_VERSION,
            "country": "Austria",
            "jurisdiction": "AT",
            "route_key": AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
            "collaboration_role": "regulatory_source_boundary",
            "root_work_item_id": str(root.id),
        },
    )

    return AustriaMobilityObjectivePlan(
        root_work_item=root,
        pathway_work_item=pathway_work,
        regulatory_work_item=regulatory_work,
    )


def bind_austria_specialist_runtimes(
    session: Session,
    plan: AustriaMobilityObjectivePlan,
    *,
    runtime_profiles: Mapping[str, AgentRuntimeProfile],
) -> tuple[AustriaSpecialistRuntimeBinding, ...]:
    """Bind the two persistent specialists to technical runtimes without granting authority."""

    work_by_position = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: plan.pathway_work_item,
        AUSTRIA_MOBILITY_REGULATORY_POSITION: plan.regulatory_work_item,
    }
    bindings: list[AustriaSpecialistRuntimeBinding] = []
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        profile = runtime_profiles.get(position_key)
        if profile is None:
            raise DependencyConflict(f"runtime profile is required for {position_key}")
        work = work_by_position[position_key]
        if work.parent_work_item_id != plan.root_work_item.id or work.objective_key != plan.root_work_item.objective_key:
            raise InvalidTransition(f"{position_key} work is outside the supplied Austria objective")
        context = build_work_item_context_bundle(
            session,
            tenant_key=work.tenant_key,
            position_key=position_key,
            work_item_id=work.id,
            purpose=ContextPurpose.COLLABORATION,
        )
        runtime = bind_employee_runtime(
            session,
            context=context,
            profile=profile,
            required_capability="reasoning",
        )
        bindings.append(
            AustriaSpecialistRuntimeBinding(
                position_key=position_key,
                work_item_id=work.id,
                context=context,
                runtime=runtime,
            )
        )
    return tuple(bindings)


def austria_objective_readiness(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
) -> AustriaObjectiveReadiness:
    """Project whether the owner may start synthesis; never infer domain/legal correctness.

    Readiness is intentionally structural: both required specialist WorkItems must exist
    under the exact J.1 root and be completed. K/L may later add executed output and
    collaboration evidence, but J.1 does not fabricate those semantics.
    """

    root = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == root_work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first()
    if root is None:
        raise DependencyConflict("Austria mobility objective root was not found")
    if root.assigned_position_key != AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION:
        raise InvalidTransition("Austria mobility objective root is not owned by the mobility operations lead")
    if root.work_type != "mobility_objective" or root.phase_key != "J.1" or not root.objective_key:
        raise InvalidTransition("work item is not a canonical J.1 Austria mobility objective root")

    children = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.tenant_key == tenant_key,
            OrganizationalWorkItem.parent_work_item_id == root.id,
        )
    ).all()
    by_position: dict[str, list[OrganizationalWorkItem]] = {}
    for child in children:
        by_position.setdefault(child.assigned_position_key, []).append(child)

    completed: list[str] = []
    pending: list[str] = []
    reasons: list[str] = []
    if root.status != "running":
        reasons.append(f"objective owner work is {root.status}, not running")

    expected_phase = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: "J.1.pathway",
        AUSTRIA_MOBILITY_REGULATORY_POSITION: "J.1.regulatory",
    }
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        matches = by_position.get(position_key, [])
        if len(matches) != 1:
            pending.append(position_key)
            reasons.append(
                f"{position_key} requires exactly one child work item; found {len(matches)}"
            )
            continue
        child = matches[0]
        if child.objective_key != root.objective_key or child.phase_key != expected_phase[position_key]:
            pending.append(position_key)
            reasons.append(f"{position_key} work is outside the canonical J.1 objective topology")
            continue
        if child.status != "completed":
            pending.append(position_key)
            reasons.append(f"{position_key} work is {child.status}, not completed")
            continue
        completed.append(position_key)

    return AustriaObjectiveReadiness(
        root_work_item_id=root.id,
        ready_for_owner_synthesis=(not pending and root.status == "running"),
        completed_positions=tuple(sorted(completed)),
        pending_positions=tuple(sorted(pending)),
        reasons=tuple(reasons),
    )


def objective_activity_count(session: Session, *, root_work_item_id: UUID) -> int:
    """Return durable Activity lineage count across the root and its direct children."""

    child_ids = list(
        session.exec(
            select(OrganizationalWorkItem.id).where(
                OrganizationalWorkItem.parent_work_item_id == root_work_item_id
            )
        ).all()
    )
    ids = [root_work_item_id, *child_ids]
    return len(
        session.exec(
            select(OrganizationActivity).where(OrganizationActivity.work_item_id.in_(ids))
        ).all()
    )

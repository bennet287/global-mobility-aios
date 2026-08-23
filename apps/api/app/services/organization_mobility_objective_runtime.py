from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    MobilityPathway,
    MobilityPathwayVersion,
    OrganizationActivity,
    OrganizationExecutionAttempt,
    OrganizationPosition,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
)
from app.services.organization_agent_runtime import (
    AgentRuntimeProfile,
    EmployeeRuntimeBinding,
    bind_employee_runtime,
)
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
)
from app.services.organization_context_broker import (
    ContextBundle,
    ContextPurpose,
    build_work_item_context_bundle,
)
from app.services.organization_work import create_work_item, start_work_item


AUSTRIA_MOBILITY_OBJECTIVE_RUNTIME_CONTRACT_VERSION = "austria-mobility-objective-runtime.v1"
AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION = "austria-mobility-specialist-execution.v1"
AUSTRIA_MOBILITY_OBJECTIVE_ROUTE = "at-rwr-skilled-worker-shortage-occupation-2026"
AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION = "mobility_operations_lead"
AUSTRIA_MOBILITY_PATHWAY_POSITION = "pathway_operations_specialist"
AUSTRIA_MOBILITY_REGULATORY_POSITION = "regulatory_intelligence_analyst"
AUSTRIA_MOBILITY_SPECIALIST_POSITIONS = (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
)
AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES = {
    AUSTRIA_MOBILITY_PATHWAY_POSITION: "operations_coordination_agent",
    AUSTRIA_MOBILITY_REGULATORY_POSITION: "business_intelligence_agent",
}


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


def austria_specialist_output_key(work_item_id: UUID) -> str:
    """Return the stable K.1 current-work output key for one specialist WorkItem."""

    return f"k1:austria-specialist:{work_item_id}"


def austria_completed_work_fingerprint(work: OrganizationalWorkItem) -> str:
    """Fingerprint the authority-relevant completed WorkItem state used by K.1 readiness.

    Execution happens while the specialist WorkItem is running, so its execution
    ContextBundle hash is intentionally historical after the final completed transition.
    This fingerprint binds the durable output to the current completed WorkItem state;
    later topology/context/assignment/status mutation makes the evidence stale. Grounded
    source identity is included only when present so historic ungrounded K.1 fingerprints
    remain backward-compatible.
    """

    payload: dict[str, object] = {
        "id": work.id,
        "tenant_key": work.tenant_key,
        "parent_work_item_id": work.parent_work_item_id,
        "work_type": work.work_type,
        "objective_key": work.objective_key,
        "phase_key": work.phase_key,
        "assigned_position_key": work.assigned_position_key,
        "department": work.department,
        "authority_level": work.authority_level,
        "status": work.status,
        "context_json": work.context_json,
    }
    if any(
        value is not None
        for value in (
            work.source_object_type,
            work.source_object_id,
            work.source_object_version,
        )
    ):
        payload.update(
            {
                "source_object_type": work.source_object_type,
                "source_object_id": work.source_object_id,
                "source_object_version": work.source_object_version,
            }
        )
    return canonical_fingerprint(payload)


def _json_object(value: str | None, *, label: str) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError as exc:
        raise DependencyConflict(f"{label} is invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise DependencyConflict(f"{label} must be a JSON object")
    return parsed


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


def _published_austria_pathway_version_source(
    session: Session,
    pathway_version_id: UUID | None,
) -> MobilityPathwayVersion | None:
    """Resolve the optional canonical source identity before creating any J.1 topology.

    This gate intentionally validates only source identity/publication. Effectivity,
    Evidence, VerifiedRules, source snapshots and policy remain owned by Context Authority
    when K resolves the specialist ContextBundle.
    """

    if pathway_version_id is None:
        return None
    pathway_version = session.get(MobilityPathwayVersion, pathway_version_id)
    if pathway_version is None:
        raise DependencyConflict("Austria mobility pathway version source was not found")
    pathway = session.get(MobilityPathway, pathway_version.pathway_id)
    if pathway is None:
        raise DependencyConflict("Austria mobility pathway source parent was not found")
    if (
        pathway.pathway_key != AUSTRIA_MOBILITY_OBJECTIVE_ROUTE
        or pathway.country.strip().casefold() != "austria"
    ):
        raise DependencyConflict(
            "mobility pathway version does not match the canonical Austria objective route"
        )
    if pathway.catalogue_status != "published":
        raise DependencyConflict("Austria mobility pathway source is not published")
    if pathway_version.lifecycle_status != "published" or pathway_version.published_at is None:
        raise DependencyConflict("Austria mobility pathway version source is not published")
    return pathway_version


def _preflight_austria_objective_source_replay(
    session: Session,
    context: OrganizationCommandContext,
    *,
    objective_key: str,
    source_object_type: str | None,
    source_object_id: str | None,
    source_object_version: str | None,
) -> None:
    """Reject semantic source changes before generic WorkItem idempotency handling.

    The J.1 objective owns two specialist WorkItems whose canonical source binding must
    remain stable across replay. The lookup is tenant-scoped so this preflight never
    reveals another tenant's globally unique idempotency key; the generic WorkItem layer
    remains responsible for cross-tenant key conflicts and all non-source drift.
    """

    expected_binding = (
        source_object_type,
        source_object_id,
        source_object_version,
    )
    for suffix in ("pathway", "regulatory"):
        existing = session.exec(
            select(OrganizationalWorkItem).where(
                OrganizationalWorkItem.tenant_key == context.tenant_key,
                OrganizationalWorkItem.idempotency_key == _work_key(context, objective_key, suffix),
            )
        ).first()
        if existing is None:
            continue
        existing_binding = (
            existing.source_object_type,
            existing.source_object_id,
            existing.source_object_version,
        )
        if existing_binding != expected_binding:
            raise DependencyConflict(
                "canonical Austria objective already bound to a different pathway version"
            )


def create_austria_mobility_objective(
    session: Session,
    context: OrganizationCommandContext,
    *,
    objective_key: str,
    pathway_version_id: UUID | None = None,
) -> AustriaMobilityObjectivePlan:
    """Create the first bounded J objective using existing WorkItem primitives only.

    The root owner coordinates two persistent specialists:
    - Pathway & Eligibility Operations Specialist
    - Regulatory Intelligence Analyst

    No agent/model execution happens here. K owns execution. J.1 only establishes the
    durable organization topology and enough bounded working context for later runtime
    binding. When ``pathway_version_id`` is supplied, only the specialist WorkItems are
    bound to that canonical published source; Context Authority remains authoritative for
    the exact Evidence/rule/snapshot versions consumed during execution.
    """

    key = _objective_key(objective_key)
    pathway_source = _published_austria_pathway_version_source(session, pathway_version_id)
    source_object_type = "mobility_pathway_version" if pathway_source is not None else None
    source_object_id = str(pathway_source.id) if pathway_source is not None else None
    source_object_version = (
        str(pathway_source.version_number) if pathway_source is not None else None
    )
    _preflight_austria_objective_source_replay(
        session,
        context,
        objective_key=key,
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
    )
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
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
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
        source_object_type=source_object_type,
        source_object_id=source_object_id,
        source_object_version=source_object_version,
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


def austria_specialist_execution_evidence_reason(
    session: Session,
    *,
    root: OrganizationalWorkItem,
    child: OrganizationalWorkItem,
    position_key: str,
) -> str | None:
    """Return why one completed specialist lacks current K.1 execution evidence.

    ``None`` means the durable output, AgentRun and OrganizationExecutionAttempt all
    resolve to the exact current WorkItem/position lineage. The validator is public so
    later organization-runtime slices can reuse the K.1 provenance contract without
    reaching through a private service helper.
    """

    outputs = session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.output_key == austria_specialist_output_key(child.id)
        )
    ).all()
    if len(outputs) != 1:
        return f"{position_key} requires exactly one current K.1 durable output; found {len(outputs)}"
    output = outputs[0]
    if output.work_item_id != child.id or output.accountable_position_key != position_key:
        return f"{position_key} durable output is bound to the wrong WorkItem or position"
    if output.status != "completed":
        return f"{position_key} durable output is {output.status}, not completed"

    try:
        payload = _json_object(output.output_json, label=f"{position_key} K.1 output")
        impact = _json_object(output.impact_json, label=f"{position_key} K.1 impact")
    except DependencyConflict as exc:
        return str(exc)

    if payload.get("contract_version") != AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION:
        return f"{position_key} durable output has the wrong K.1 contract version"
    if payload.get("root_work_item_id") != str(root.id) or payload.get("work_item_id") != str(child.id):
        return f"{position_key} durable output has the wrong objective/WorkItem provenance"
    if payload.get("position_key") != position_key:
        return f"{position_key} durable output has the wrong employee provenance"
    if payload.get("completed_work_fingerprint") != austria_completed_work_fingerprint(child):
        return f"{position_key} durable output is stale for the current completed WorkItem"
    if payload.get("agent_name") != AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[position_key]:
        return f"{position_key} durable output used the wrong controlled-agent runtime"
    if impact.get("external_action_authorized") is not False or impact.get("client_facing") is not False:
        return f"{position_key} durable output exceeds the bounded internal execution authority"

    agent_run_id = payload.get("agent_run_id")
    execution_attempt_id = payload.get("execution_attempt_id")
    execution_token = payload.get("execution_token")
    context_hash = payload.get("context_hash")
    runtime_binding_hash = payload.get("runtime_binding_hash")
    if not all(isinstance(value, str) and value for value in (
        agent_run_id,
        execution_attempt_id,
        execution_token,
        context_hash,
        runtime_binding_hash,
    )):
        return f"{position_key} durable output lacks complete execution provenance"

    try:
        agent_run_uuid = UUID(agent_run_id)
        attempt_uuid = UUID(execution_attempt_id)
    except ValueError:
        return f"{position_key} durable output contains invalid execution identifiers"

    agent_run = session.get(AgentRun, agent_run_uuid)
    if agent_run is None or agent_run.agent_name != AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[position_key]:
        return f"{position_key} durable output does not resolve to the expected AgentRun"
    try:
        agent_input = _json_object(agent_run.input_json, label=f"{position_key} AgentRun input")
    except DependencyConflict as exc:
        return str(exc)
    run_context = agent_input.get("context")
    provenance = run_context.get("k1_provenance") if isinstance(run_context, dict) else None
    if not isinstance(provenance, dict):
        return f"{position_key} AgentRun lacks K.1 provenance"
    if (
        provenance.get("work_item_id") != str(child.id)
        or provenance.get("position_key") != position_key
        or provenance.get("context_hash") != context_hash
        or provenance.get("runtime_binding_hash") != runtime_binding_hash
    ):
        return f"{position_key} AgentRun provenance does not match the durable output"

    attempt = session.get(OrganizationExecutionAttempt, attempt_uuid)
    if (
        attempt is None
        or attempt.work_item_id != child.id
        or attempt.status != "completed"
        or attempt.execution_token != execution_token
    ):
        return f"{position_key} durable output does not resolve to a completed execution attempt"
    return None


def austria_objective_readiness(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
) -> AustriaObjectiveReadiness:
    """Project whether the owner may synthesize from current K.1 execution evidence.

    J.1 established the structural topology. K.1 strengthens the gate: WorkItem
    completion alone is not execution proof. Every required specialist must have one
    current, provenance-valid OrganizationalActionOutput linked to its controlled
    AgentRun and completed OrganizationExecutionAttempt. Provider/model identity never
    grants authority; the durable WorkItem/context provenance remains authoritative.
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
        execution_reason = austria_specialist_execution_evidence_reason(
            session,
            root=root,
            child=child,
            position_key=position_key,
        )
        if execution_reason is not None:
            pending.append(position_key)
            reasons.append(execution_reason)
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

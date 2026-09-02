from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationPosition,
    OrganizationalWorkItem,
    now_utc,
)
from app.services.organization_command import DependencyConflict
from app.services.organization_mobility_live_organization import (
    AustriaLiveOrganizationSnapshot,
    latest_austria_live_organization_snapshot,
)


LIVING_ORGANIZATION_SCENE_CONTRACT_VERSION = "living-organization-scene.v1"


@dataclass(frozen=True, slots=True)
class LivingSceneEmployee:
    position_key: str
    title: str
    department: str
    reports_to_position_key: str | None
    authority_level: str
    organization_status: str
    work_item_id: UUID | None
    work_status: str | None
    semantic_state: str
    presence_state: str
    state_reason: str


@dataclass(frozen=True, slots=True)
class LivingSceneDepartment:
    department_key: str
    label: str
    employee_count: int
    work_item_count: int
    active_blocker_count: int
    canonical_basis: str


@dataclass(frozen=True, slots=True)
class LivingSceneMission:
    mission_key: str
    objective_key: str
    root_work_item_id: UUID
    title: str
    state: str
    phase_key: str | None
    participant_position_keys: tuple[str, ...]
    work_item_ids: tuple[UUID, ...]
    blocker_count: int
    decision_count: int
    projection_only: bool
    canonical_basis: str


@dataclass(frozen=True, slots=True)
class LivingSceneConversation:
    conversation_id: str
    participant_position_keys: tuple[str, ...]
    work_item_id: UUID | None
    status: str
    summary: str


@dataclass(frozen=True, slots=True)
class LivingSceneIncident:
    incident_id: str
    title: str
    severity: str
    status: str
    work_item_id: UUID | None


@dataclass(frozen=True, slots=True)
class LivingSceneSmartObject:
    object_key: str
    object_type: str
    label: str
    state: str
    metric_label: str
    metric_value: int
    projection_only: bool
    canonical_basis: str


@dataclass(frozen=True, slots=True)
class LivingSceneCoverage:
    departments: str
    missions: str
    conversations: str
    incidents: str
    smart_objects: str
    presence: str


@dataclass(frozen=True, slots=True)
class LivingSceneWorkItem:
    work_item_id: UUID
    parent_work_item_id: UUID | None
    title: str
    objective_key: str | None
    phase_key: str | None
    status: str
    priority: str
    risk_level: str
    assigned_position_key: str
    department: str
    authority_level: str


@dataclass(frozen=True, slots=True)
class LivingSceneBlocker:
    blocker_id: UUID
    work_item_id: UUID | None
    title: str
    severity: str
    status: str
    requires_human_action: bool


@dataclass(frozen=True, slots=True)
class LivingSceneDecision:
    decision_id: UUID
    decision_key: str
    title: str
    status: str
    authority_level: str
    decision_owner_position: str
    work_item_id: UUID | None
    supersedes_decision_id: UUID | None
    superseded_by_decision_id: UUID | None
    is_current: bool
    decided_at: datetime | None


@dataclass(frozen=True, slots=True)
class LivingSceneRoom:
    room_key: str
    room_type: str
    label: str
    state: str
    metric_label: str
    metric_value: int
    projection_only: bool
    canonical_basis: str


@dataclass(frozen=True, slots=True)
class LivingSceneRelationship:
    relationship_key: str
    relationship_type: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    canonical_basis: str


@dataclass(frozen=True, slots=True)
class LivingSceneDeterministicPlane:
    canonical_projection: bool
    authoritative: bool
    departments: tuple[LivingSceneDepartment, ...]
    missions: tuple[LivingSceneMission, ...]
    employees: tuple[LivingSceneEmployee, ...]
    work_items: tuple[LivingSceneWorkItem, ...]
    conversations: tuple[LivingSceneConversation, ...]
    blockers: tuple[LivingSceneBlocker, ...]
    decisions: tuple[LivingSceneDecision, ...]
    incidents: tuple[LivingSceneIncident, ...]
    smart_objects: tuple[LivingSceneSmartObject, ...]
    rooms: tuple[LivingSceneRoom, ...]
    relationships: tuple[LivingSceneRelationship, ...]


@dataclass(frozen=True, slots=True)
class LivingSceneNonCanonicalPlane:
    enabled: bool
    canonical_projection: bool
    authoritative: bool
    status: str
    items: tuple[dict[str, object], ...]


@dataclass(frozen=True, slots=True)
class LivingSceneTruthPosture:
    canonical_authority: str
    scene_authoritative: bool
    renderer_authoritative: bool
    prediction_authoritative: bool
    environmental_authoritative: bool
    scene_mutations_allowed: bool


@dataclass(frozen=True, slots=True)
class LivingOrganizationScene:
    contract_version: str
    generated_at: datetime
    scope: str
    root_work_item_id: UUID
    objective_key: str
    coverage: LivingSceneCoverage
    deterministic: LivingSceneDeterministicPlane
    predictive: LivingSceneNonCanonicalPlane
    environmental: LivingSceneNonCanonicalPlane
    truth: LivingSceneTruthPosture


def _latest_position_rows(
    session: Session,
    *,
    position_keys: tuple[str, ...],
) -> dict[str, OrganizationPosition]:
    rows = list(
        session.exec(
            select(OrganizationPosition)
            .where(OrganizationPosition.position_key.in_(position_keys))
            .order_by(OrganizationPosition.position_key, OrganizationPosition.version.desc())
        ).all()
    )
    latest: dict[str, OrganizationPosition] = {}
    for row in rows:
        latest.setdefault(row.position_key, row)
    missing = [key for key in position_keys if key not in latest]
    if missing:
        raise DependencyConflict(
            "Living Organization scene position identity is unavailable: " + ", ".join(missing)
        )
    return latest


def _scene_work_items(
    session: Session,
    *,
    tenant_key: str,
    snapshot: AustriaLiveOrganizationSnapshot,
) -> tuple[OrganizationalWorkItem, ...]:
    ordered_ids = (
        snapshot.root_work_item_id,
        *(item.work_item_id for item in snapshot.specialist_outputs),
    )
    rows = list(
        session.exec(
            select(OrganizationalWorkItem).where(
                OrganizationalWorkItem.tenant_key == tenant_key,
                OrganizationalWorkItem.id.in_(ordered_ids),
            )
        ).all()
    )
    by_id = {row.id: row for row in rows}
    missing = [str(item_id) for item_id in ordered_ids if item_id not in by_id]
    if missing:
        raise DependencyConflict(
            "Living Organization scene WorkItem identity is unavailable: " + ", ".join(missing)
        )
    return tuple(by_id[item_id] for item_id in ordered_ids)


def _employee_state(
    *,
    work: OrganizationalWorkItem,
    blocked_work_ids: set[UUID],
    snapshot: AustriaLiveOrganizationSnapshot,
    owner: bool,
) -> tuple[str, str]:
    if work.id in blocked_work_ids:
        return "blocked", "A canonical active blocker is attached to this WorkItem."
    if owner and snapshot.ready_for_owner_synthesis and snapshot.owner_synthesis is None:
        return "awaiting_owner", "Canonical specialist readiness requires the bounded owner step."
    if work.status == "running":
        return "working", "The canonical WorkItem is running."
    if work.status == "completed":
        return "completed", "The canonical WorkItem is completed."
    if work.status in {"pending", "queued"}:
        return "queued", f"The canonical WorkItem is {work.status}."
    return "work_state", f"The canonical WorkItem state is {work.status}."


def _scene_decisions(
    session: Session,
    *,
    tenant_key: str,
    work_item_ids: tuple[UUID, ...],
) -> tuple[LivingSceneDecision, ...]:
    rows = list(
        session.exec(
            select(ExecutiveDecision)
            .where(
                ExecutiveDecision.tenant_key == tenant_key,
                ExecutiveDecision.work_item_id.in_(work_item_ids),
            )
            .order_by(ExecutiveDecision.created_at, ExecutiveDecision.id)
        ).all()
    )
    if not rows:
        return ()

    decision_ids = {row.id for row in rows}
    supersession_rows = list(
        session.exec(
            select(ExecutiveDecision.id, ExecutiveDecision.supersedes_decision_id).where(
                ExecutiveDecision.tenant_key == tenant_key,
                ExecutiveDecision.supersedes_decision_id.in_(decision_ids),
            )
        ).all()
    )
    superseded_by = {
        supersedes_id: decision_id
        for decision_id, supersedes_id in supersession_rows
        if supersedes_id is not None
    }
    return tuple(
        LivingSceneDecision(
            decision_id=row.id,
            decision_key=row.decision_key,
            title=row.title,
            status=row.status,
            authority_level=row.authority_level,
            decision_owner_position=row.decision_owner_position,
            work_item_id=row.work_item_id,
            supersedes_decision_id=row.supersedes_decision_id,
            superseded_by_decision_id=superseded_by.get(row.id),
            is_current=row.id not in superseded_by and row.status != "superseded",
            decided_at=row.decided_at,
        )
        for row in rows
    )


def austria_living_organization_scene(
    session: Session,
    *,
    tenant_key: str,
    snapshot: AustriaLiveOrganizationSnapshot,
) -> LivingOrganizationScene:
    works = _scene_work_items(session, tenant_key=tenant_key, snapshot=snapshot)
    work_by_id = {item.id: item for item in works}
    position_keys = tuple(dict.fromkeys(item.assigned_position_key for item in works))
    positions = _latest_position_rows(session, position_keys=position_keys)
    blocked_work_ids = {
        blocker.work_item_id
        for blocker in snapshot.blockers
        if blocker.work_item_id is not None
    }

    employees: list[LivingSceneEmployee] = []
    for work in works:
        position = positions[work.assigned_position_key]
        owner = work.id == snapshot.root_work_item_id
        semantic_state, state_reason = _employee_state(
            work=work,
            blocked_work_ids=blocked_work_ids,
            snapshot=snapshot,
            owner=owner,
        )
        employees.append(
            LivingSceneEmployee(
                position_key=position.position_key,
                title=position.title,
                department=position.department,
                reports_to_position_key=position.reports_to_position_key,
                authority_level=position.authority_level,
                organization_status=position.status,
                work_item_id=work.id,
                work_status=work.status,
                semantic_state=semantic_state,
                presence_state="not_asserted",
                state_reason=state_reason,
            )
        )

    work_items = tuple(
        LivingSceneWorkItem(
            work_item_id=work.id,
            parent_work_item_id=work.parent_work_item_id,
            title=work.title,
            objective_key=work.objective_key,
            phase_key=work.phase_key,
            status=work.status,
            priority=work.priority.value,
            risk_level=work.risk_level,
            assigned_position_key=work.assigned_position_key,
            department=work.department,
            authority_level=work.authority_level,
        )
        for work in works
    )

    blockers = tuple(
        LivingSceneBlocker(
            blocker_id=item.blocker_id,
            work_item_id=item.work_item_id,
            title=item.title,
            severity=item.severity,
            status=item.status,
            requires_human_action=item.requires_human_action,
        )
        for item in snapshot.blockers
    )

    work_ids = tuple(item.id for item in works)
    decisions = _scene_decisions(session, tenant_key=tenant_key, work_item_ids=work_ids)
    board_attention = sum(
        1
        for decision in decisions
        if decision.is_current
        and decision.decision_owner_position == "board"
        and decision.status in {"pending", "pending_board", "pending_ceo"}
    )
    evidence_count = len(snapshot.domain_evidence_refs) + len(snapshot.verified_rule_refs)


    department_keys = tuple(sorted({work.department for work in works}))
    departments = tuple(
        LivingSceneDepartment(
            department_key=department,
            label=department,
            employee_count=sum(1 for item in employees if item.department == department),
            work_item_count=sum(1 for item in works if item.department == department),
            active_blocker_count=sum(
                1
                for item in blockers
                if item.work_item_id is not None
                and work_by_id[item.work_item_id].department == department
            ),
            canonical_basis="OrganizationPosition.department + OrganizationalWorkItem.department",
        )
        for department in department_keys
    )

    missions = (
        LivingSceneMission(
            mission_key=f"objective:{snapshot.root_work_item_id}",
            objective_key=snapshot.objective_key,
            root_work_item_id=snapshot.root_work_item_id,
            title=work_by_id[snapshot.root_work_item_id].title,
            state=snapshot.cycle_status,
            phase_key=work_by_id[snapshot.root_work_item_id].phase_key,
            participant_position_keys=tuple(item.position_key for item in employees),
            work_item_ids=work_ids,
            blocker_count=len(blockers),
            decision_count=len(decisions),
            projection_only=True,
            canonical_basis="OrganizationalWorkItem objective_key/parent topology",
        ),
    )

    smart_objects = (
        LivingSceneSmartObject(
            object_key=f"mission-board:{snapshot.root_work_item_id}",
            object_type="mission_board",
            label="Mission Board",
            state=snapshot.cycle_status,
            metric_label="WorkItems",
            metric_value=len(work_items),
            projection_only=True,
            canonical_basis="OrganizationalWorkItem objective topology",
        ),
        LivingSceneSmartObject(
            object_key=f"evidence-console:{snapshot.root_work_item_id}",
            object_type="evidence_console",
            label="Evidence Console",
            state="grounded" if evidence_count else "empty",
            metric_label="Evidence + VerifiedRules",
            metric_value=evidence_count,
            projection_only=True,
            canonical_basis="Persisted context Evidence and VerifiedRule references",
        ),
        LivingSceneSmartObject(
            object_key=f"board-beacon:{snapshot.root_work_item_id}",
            object_type="board_beacon",
            label="Board Attention",
            state="attention" if board_attention else "quiet",
            metric_label="Board decisions",
            metric_value=board_attention,
            projection_only=True,
            canonical_basis="Current ExecutiveDecision records linked to scene WorkItems",
        ),
    )

    rooms = (
        LivingSceneRoom(
            room_key=f"mission:{snapshot.root_work_item_id}",
            room_type="mission_room",
            label=snapshot.objective_key,
            state=snapshot.cycle_status,
            metric_label="WorkItems",
            metric_value=len(work_items),
            projection_only=True,
            canonical_basis="OrganizationalWorkItem objective topology",
        ),
        LivingSceneRoom(
            room_key=f"evidence:{snapshot.root_work_item_id}",
            room_type="evidence_lab",
            label="Evidence Lab",
            state="grounded" if evidence_count else "empty",
            metric_label="Evidence + VerifiedRules",
            metric_value=evidence_count,
            projection_only=True,
            canonical_basis="Persisted context Evidence and VerifiedRule references",
        ),
        LivingSceneRoom(
            room_key=f"board:{snapshot.root_work_item_id}",
            room_type="board_room",
            label="Board Room",
            state="attention" if board_attention else "quiet",
            metric_label="Decisions requiring Board attention",
            metric_value=board_attention,
            projection_only=True,
            canonical_basis="ExecutiveDecision records linked to scene WorkItems",
        ),
    )

    relationships: list[LivingSceneRelationship] = []
    for work in works:
        relationships.append(
            LivingSceneRelationship(
                relationship_key=f"assignment:{work.id}:{work.assigned_position_key}",
                relationship_type="assigned_to",
                source_type="employee",
                source_id=work.assigned_position_key,
                target_type="work_item",
                target_id=str(work.id),
                canonical_basis="OrganizationalWorkItem.assigned_position_key",
            )
        )
        if work.parent_work_item_id is not None:
            relationships.append(
                LivingSceneRelationship(
                    relationship_key=f"parent:{work.id}:{work.parent_work_item_id}",
                    relationship_type="belongs_to",
                    source_type="work_item",
                    source_id=str(work.id),
                    target_type="work_item",
                    target_id=str(work.parent_work_item_id),
                    canonical_basis="OrganizationalWorkItem.parent_work_item_id",
                )
            )

    employee_ids = {item.position_key for item in employees}
    for employee in employees:
        if employee.reports_to_position_key in employee_ids:
            relationships.append(
                LivingSceneRelationship(
                    relationship_key=f"reports:{employee.position_key}:{employee.reports_to_position_key}",
                    relationship_type="reports_to",
                    source_type="employee",
                    source_id=employee.position_key,
                    target_type="employee",
                    target_id=str(employee.reports_to_position_key),
                    canonical_basis="OrganizationPosition.reports_to_position_key",
                )
            )

    for blocker in blockers:
        if blocker.work_item_id is not None and blocker.work_item_id in work_by_id:
            relationships.append(
                LivingSceneRelationship(
                    relationship_key=f"blocker:{blocker.blocker_id}:{blocker.work_item_id}",
                    relationship_type="blocks",
                    source_type="blocker",
                    source_id=str(blocker.blocker_id),
                    target_type="work_item",
                    target_id=str(blocker.work_item_id),
                    canonical_basis="OrganizationBlocker.work_item_id",
                )
            )

    for decision in decisions:
        if decision.work_item_id is not None:
            relationships.append(
                LivingSceneRelationship(
                    relationship_key=f"decision:{decision.decision_id}:{decision.work_item_id}",
                    relationship_type="governs",
                    source_type="decision",
                    source_id=str(decision.decision_id),
                    target_type="work_item",
                    target_id=str(decision.work_item_id),
                    canonical_basis="ExecutiveDecision.work_item_id",
                )
            )

    return LivingOrganizationScene(
        contract_version=LIVING_ORGANIZATION_SCENE_CONTRACT_VERSION,
        generated_at=now_utc(),
        scope="austria_mobility",
        root_work_item_id=snapshot.root_work_item_id,
        objective_key=snapshot.objective_key,
        coverage=LivingSceneCoverage(
            departments="projected_from_canonical_positions_and_work",
            missions="workitem_objective_topology_projection",
            conversations="not_connected_m3",
            incidents="not_connected_m3",
            smart_objects="derived_read_only_scene_metrics",
            presence="not_asserted_m3",
        ),
        deterministic=LivingSceneDeterministicPlane(
            canonical_projection=True,
            authoritative=False,
            departments=departments,
            missions=missions,
            employees=tuple(employees),
            work_items=work_items,
            conversations=(),
            blockers=blockers,
            decisions=decisions,
            incidents=(),
            smart_objects=smart_objects,
            rooms=rooms,
            relationships=tuple(relationships),
        ),
        predictive=LivingSceneNonCanonicalPlane(
            enabled=False,
            canonical_projection=False,
            authoritative=False,
            status="reserved_for_m9_phantom_futures",
            items=(),
        ),
        environmental=LivingSceneNonCanonicalPlane(
            enabled=False,
            canonical_projection=False,
            authoritative=False,
            status="reserved_for_m9_environmental_memory",
            items=(),
        ),
        truth=LivingSceneTruthPosture(
            canonical_authority="AIOS canonical records and accepted projections",
            scene_authoritative=False,
            renderer_authoritative=False,
            prediction_authoritative=False,
            environmental_authoritative=False,
            scene_mutations_allowed=False,
        ),
    )


def latest_austria_living_organization_scene(
    session: Session,
    *,
    tenant_key: str,
) -> LivingOrganizationScene | None:
    snapshot = latest_austria_live_organization_snapshot(session, tenant_key=tenant_key)
    if snapshot is None:
        return None
    return austria_living_organization_scene(
        session,
        tenant_key=tenant_key,
        snapshot=snapshot,
    )

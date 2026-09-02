from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationBlocker,
    OrganizationHumanActionRequest,
    OrganizationPosition,
    OrganizationalWorkItem,
    RiskEscalation,
    now_utc,
)
from app.services.organization_conversation import (
    CONVERSATION_CLOSED_ACTIVITY_TYPE,
    CONVERSATION_OPENED_ACTIVITY_TYPE,
    CONVERSATION_SOURCE_TYPE,
)
from app.services.organization_command import DependencyConflict
from app.services.organization_mobility_live_organization import (
    AustriaLiveOrganizationSnapshot,
    latest_austria_live_organization_snapshot,
)


LIVING_ORGANIZATION_SCENE_CONTRACT_VERSION = "living-organization-scene.v3"


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
    work_item_id: UUID
    status: str
    summary: str
    opened_activity_id: UUID
    latest_activity_id: UUID
    opened_at: datetime
    lifecycle_at: datetime
    authority_effect: str
    transcript_persisted: bool
    canonical_basis: str


@dataclass(frozen=True, slots=True)
class LivingSceneHandoff:
    activity_id: UUID
    work_item_id: UUID
    previous_position_key: str
    assigned_position_key: str
    status: str
    occurred_at: datetime
    causation_activity_id: UUID | None
    canonical_basis: str


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
    metric_value: int | None
    projection_only: bool
    canonical_basis: str


@dataclass(frozen=True, slots=True)
class LivingSceneCoverage:
    departments: str
    missions: str
    conversations: str
    handoffs: str
    blockers: str
    human_actions: str
    risk_escalations: str
    incidents: str
    smart_objects: str
    runtime_costs: str
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
    blocker_type: str
    title: str
    description: str
    severity: str
    status: str
    accountable_position_key: str | None
    decision_id: UUID | None
    risk_escalation_id: UUID | None
    requires_human_action: bool


@dataclass(frozen=True, slots=True)
class LivingSceneDecision:
    decision_id: UUID
    decision_key: str
    title: str
    question: str
    recommendation: str
    status: str
    authority_level: str
    decision_owner_position: str
    work_item_id: UUID | None
    evidence_items: tuple[object, ...]
    record_fingerprint: str | None
    source_object_type: str | None
    source_object_id: str | None
    source_object_version: str | None
    supersedes_decision_id: UUID | None
    superseded_by_decision_id: UUID | None
    is_current: bool
    required_owner_action: bool
    decided_at: datetime | None


@dataclass(frozen=True, slots=True)
class LivingSceneHumanActionRequest:
    request_id: UUID
    request_type: str
    title: str
    instructions: str
    status: str
    priority: str
    required_role: str
    assigned_human_id: str | None
    authority_level: str | None
    work_item_id: UUID | None
    decision_id: UUID | None
    blocker_id: UUID | None
    requested_at: datetime
    due_at: datetime | None
    canonical_basis: str


@dataclass(frozen=True, slots=True)
class LivingSceneRiskEscalation:
    risk_id: UUID
    risk_key: str
    category: str
    severity: str
    title: str
    description: str
    status: str
    accountable_position_key: str
    escalated_to_position_key: str
    work_item_id: UUID | None
    requires_board_attention: bool
    is_emergency: bool
    evidence_items: tuple[object, ...]
    created_at: datetime
    canonical_basis: str


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
    handoffs: tuple[LivingSceneHandoff, ...]
    blockers: tuple[LivingSceneBlocker, ...]
    decisions: tuple[LivingSceneDecision, ...]
    human_actions: tuple[LivingSceneHumanActionRequest, ...]
    risk_escalations: tuple[LivingSceneRiskEscalation, ...]
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


def _json_list(value: str, *, label: str) -> tuple[object, ...]:
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict(f"Living Organization {label} JSON is invalid") from exc
    if not isinstance(payload, list):
        raise DependencyConflict(f"Living Organization {label} JSON must be a list")
    return tuple(payload)


def _scene_blockers(
    session: Session,
    *,
    tenant_key: str,
    snapshot: AustriaLiveOrganizationSnapshot,
) -> tuple[LivingSceneBlocker, ...]:
    blocker_ids = tuple(item.blocker_id for item in snapshot.blockers)
    if not blocker_ids:
        return ()
    rows = list(session.exec(select(OrganizationBlocker).where(
        OrganizationBlocker.tenant_key == tenant_key,
        OrganizationBlocker.id.in_(blocker_ids),
    )).all())
    by_id = {row.id: row for row in rows}
    missing = [str(blocker_id) for blocker_id in blocker_ids if blocker_id not in by_id]
    if missing:
        raise DependencyConflict("Living Organization blocker identity is unavailable: " + ", ".join(missing))
    return tuple(
        LivingSceneBlocker(
            blocker_id=row.id,
            work_item_id=row.work_item_id,
            blocker_type=row.blocker_type.value,
            title=row.title,
            description=row.description,
            severity=row.severity,
            status=row.status.value,
            accountable_position_key=row.accountable_position_key,
            decision_id=row.decision_id,
            risk_escalation_id=row.risk_escalation_id,
            requires_human_action=row.requires_human_action,
        )
        for row in (by_id[blocker_id] for blocker_id in blocker_ids)
    )


def _scene_decisions(
    session: Session,
    *,
    tenant_key: str,
    work_item_ids: tuple[UUID, ...],
) -> tuple[LivingSceneDecision, ...]:
    rows = list(session.exec(
        select(ExecutiveDecision).where(
            ExecutiveDecision.tenant_key == tenant_key,
            ExecutiveDecision.work_item_id.in_(work_item_ids),
        ).order_by(ExecutiveDecision.created_at, ExecutiveDecision.id)
    ).all())
    if not rows:
        return ()
    decision_ids = {row.id for row in rows}
    supersession_rows = list(session.exec(
        select(ExecutiveDecision.id, ExecutiveDecision.supersedes_decision_id).where(
            ExecutiveDecision.tenant_key == tenant_key,
            ExecutiveDecision.supersedes_decision_id.in_(decision_ids),
        )
    ).all())
    superseded_by = {supersedes_id: decision_id for decision_id, supersedes_id in supersession_rows if supersedes_id is not None}
    projected: list[LivingSceneDecision] = []
    for row in rows:
        current = row.id not in superseded_by and row.status != "superseded"
        required_owner_action = current and row.decision_owner_position == "board" and row.status in {"pending", "pending_board", "pending_ceo"}
        projected.append(LivingSceneDecision(
            decision_id=row.id,
            decision_key=row.decision_key,
            title=row.title,
            question=row.question,
            recommendation=row.recommendation,
            status=row.status,
            authority_level=row.authority_level,
            decision_owner_position=row.decision_owner_position,
            work_item_id=row.work_item_id,
            evidence_items=_json_list(row.evidence_json, label=f"decision {row.id} evidence"),
            record_fingerprint=row.record_fingerprint,
            source_object_type=row.source_object_type,
            source_object_id=row.source_object_id,
            source_object_version=row.source_object_version,
            supersedes_decision_id=row.supersedes_decision_id,
            superseded_by_decision_id=superseded_by.get(row.id),
            is_current=current,
            required_owner_action=required_owner_action,
            decided_at=row.decided_at,
        ))
    return tuple(projected)


def _scene_human_actions(
    session: Session,
    *,
    tenant_key: str,
    work_item_ids: tuple[UUID, ...],
    decision_ids: set[UUID],
    blocker_ids: set[UUID],
) -> tuple[LivingSceneHumanActionRequest, ...]:
    rows = list(session.exec(
        select(OrganizationHumanActionRequest)
        .where(OrganizationHumanActionRequest.tenant_key == tenant_key)
        .order_by(OrganizationHumanActionRequest.requested_at, OrganizationHumanActionRequest.id)
    ).all())
    active_statuses = {"required", "acknowledged", "in_progress"}
    work_ids = set(work_item_ids)
    projected: list[LivingSceneHumanActionRequest] = []
    for row in rows:
        status = row.status.value
        if status not in active_statuses:
            continue
        if not (row.work_item_id in work_ids or row.decision_id in decision_ids or row.blocker_id in blocker_ids):
            continue
        projected.append(LivingSceneHumanActionRequest(
            request_id=row.id,
            request_type=row.request_type.value,
            title=row.title,
            instructions=row.instructions,
            status=status,
            priority=row.priority.value,
            required_role=row.required_role,
            assigned_human_id=row.assigned_human_id,
            authority_level=row.authority_level,
            work_item_id=row.work_item_id,
            decision_id=row.decision_id,
            blocker_id=row.blocker_id,
            requested_at=row.requested_at,
            due_at=row.due_at,
            canonical_basis="OrganizationHumanActionRequest canonical record",
        ))
    return tuple(projected)


def _scene_risk_escalations(session: Session, *, work_item_ids: tuple[UUID, ...]) -> tuple[LivingSceneRiskEscalation, ...]:
    rows = list(session.exec(
        select(RiskEscalation).where(RiskEscalation.work_item_id.in_(work_item_ids)).order_by(RiskEscalation.created_at, RiskEscalation.id)
    ).all())
    return tuple(
        LivingSceneRiskEscalation(
            risk_id=row.id,
            risk_key=row.risk_key,
            category=row.category,
            severity=row.severity,
            title=row.title,
            description=row.description,
            status=row.status,
            accountable_position_key=row.accountable_position_key,
            escalated_to_position_key=row.escalated_to_position_key,
            work_item_id=row.work_item_id,
            requires_board_attention=row.requires_board_attention,
            is_emergency=row.is_emergency,
            evidence_items=_json_list(row.evidence_json, label=f"risk {row.id} evidence"),
            created_at=row.created_at,
            canonical_basis="RiskEscalation canonical record linked to scene WorkItem",
        )
        for row in rows if row.status != "resolved"
    )


def _activity_payload(activity: OrganizationActivity, *, label: str) -> dict[str, object]:
    try:
        payload = json.loads(activity.payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict(f"Living Organization {label} Activity payload is invalid") from exc
    if not isinstance(payload, dict):
        raise DependencyConflict(f"Living Organization {label} Activity payload is invalid")
    return payload


def _payload_uuid(value: object, *, label: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise DependencyConflict(f"Living Organization {label} identity is invalid") from exc


def _scene_conversations(
    session: Session,
    *,
    tenant_key: str,
    work_item_ids: tuple[UUID, ...],
) -> tuple[LivingSceneConversation, ...]:
    rows = list(
        session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.tenant_key == tenant_key,
                OrganizationActivity.work_item_id.in_(work_item_ids),
                OrganizationActivity.activity_type.in_(
                    (CONVERSATION_OPENED_ACTIVITY_TYPE, CONVERSATION_CLOSED_ACTIVITY_TYPE)
                ),
            )
            .order_by(OrganizationActivity.occurred_at, OrganizationActivity.stream_sequence)
        ).all()
    )
    grouped: dict[str, dict[str, OrganizationActivity]] = {}
    for row in rows:
        conversation_id = row.source_object_id
        if (
            row.source_object_type != CONVERSATION_SOURCE_TYPE
            or row.source_object_version != "v1"
            or row.activity_class != OrganizationActivityClass.work
            or not conversation_id
            or row.activity_key
            != (
                f"organization:conversation:{conversation_id}:opened:v1"
                if row.activity_type == CONVERSATION_OPENED_ACTIVITY_TYPE
                else f"organization:conversation:{conversation_id}:closed:v1"
            )
        ):
            raise DependencyConflict("Living Organization conversation Activity identity is inconsistent")
        lifecycle = "opened" if row.activity_type == CONVERSATION_OPENED_ACTIVITY_TYPE else "closed"
        if lifecycle in grouped.setdefault(conversation_id, {}):
            raise DependencyConflict("Living Organization conversation lifecycle is ambiguous")
        grouped[conversation_id][lifecycle] = row

    result: list[LivingSceneConversation] = []
    for conversation_id, lifecycle in grouped.items():
        opened = lifecycle.get("opened")
        if opened is None or opened.work_item_id is None:
            raise DependencyConflict("Living Organization conversation opening lineage is unavailable")
        opened_payload = _activity_payload(opened, label="conversation opening")
        participant_value = opened_payload.get("participant_position_keys")
        if not isinstance(participant_value, list) or not all(
            isinstance(value, str) and value for value in participant_value
        ):
            raise DependencyConflict("Living Organization conversation participants are invalid")
        participants = tuple(dict.fromkeys(participant_value))
        payload_work_item_id = _payload_uuid(
            opened_payload.get("work_item_id"), label="conversation WorkItem"
        )
        if (
            len(participants) < 2
            or payload_work_item_id != opened.work_item_id
            or opened_payload.get("conversation_id") != conversation_id
            or opened_payload.get("lifecycle_status") != "open"
            or opened_payload.get("authority_effect") != "none"
            or opened_payload.get("transcript_persisted") is not False
        ):
            raise DependencyConflict("Living Organization conversation opening contract is inconsistent")

        closed = lifecycle.get("closed")
        latest = opened
        status = "open"
        if closed is not None:
            closed_payload = _activity_payload(closed, label="conversation closure")
            if (
                closed.work_item_id != opened.work_item_id
                or closed.occurred_at < opened.occurred_at
                or closed.causation_activity_id != opened.id
                or closed_payload.get("conversation_id") != conversation_id
                or _payload_uuid(
                    closed_payload.get("work_item_id"), label="conversation closure WorkItem"
                )
                != opened.work_item_id
                or _payload_uuid(
                    closed_payload.get("opened_activity_id"),
                    label="conversation opening Activity",
                )
                != opened.id
                or closed_payload.get("lifecycle_status") != "closed"
                or closed_payload.get("authority_effect") != "none"
                or closed_payload.get("transcript_persisted") is not False
            ):
                raise DependencyConflict("Living Organization conversation closure contract is inconsistent")
            latest = closed
            status = "closed"
        result.append(
            LivingSceneConversation(
                conversation_id=conversation_id,
                participant_position_keys=participants,
                work_item_id=opened.work_item_id,
                status=status,
                summary=latest.summary,
                opened_activity_id=opened.id,
                latest_activity_id=latest.id,
                opened_at=opened.occurred_at,
                lifecycle_at=latest.occurred_at,
                authority_effect="none",
                transcript_persisted=False,
                canonical_basis="Immutable OrganizationActivity conversation lifecycle",
            )
        )
    return tuple(sorted(result, key=lambda item: (item.opened_at, item.conversation_id)))


def _scene_handoffs(
    session: Session,
    *,
    tenant_key: str,
    work_item_ids: tuple[UUID, ...],
) -> tuple[LivingSceneHandoff, ...]:
    rows = list(
        session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.tenant_key == tenant_key,
                OrganizationActivity.work_item_id.in_(work_item_ids),
                OrganizationActivity.activity_type == "organization.work.assigned.v1",
            )
            .order_by(OrganizationActivity.occurred_at, OrganizationActivity.stream_sequence)
        ).all()
    )
    result: list[LivingSceneHandoff] = []
    for row in rows:
        if row.work_item_id is None:
            raise DependencyConflict("Living Organization handoff WorkItem lineage is unavailable")
        payload = _activity_payload(row, label="handoff")
        previous_position_key = payload.get("previous_position_key")
        assigned_position_key = payload.get("assigned_position_key")
        status = payload.get("status")
        expected_key_prefix = (
            f"semantic:organizational_work_item:{row.work_item_id}:"
            "organization.work.assigned.v1:"
        )
        if (
            row.source_object_type != "organizational_work_item"
            or row.activity_class != OrganizationActivityClass.work
            or row.source_object_id != str(row.work_item_id)
            or not row.activity_key.startswith(expected_key_prefix)
            or not row.source_object_version
            or not isinstance(previous_position_key, str)
            or not previous_position_key
            or not isinstance(assigned_position_key, str)
            or not assigned_position_key
            or previous_position_key == assigned_position_key
            or not isinstance(status, str)
            or not status
        ):
            raise DependencyConflict("Living Organization handoff Activity identity is inconsistent")
        result.append(
            LivingSceneHandoff(
                activity_id=row.id,
                work_item_id=row.work_item_id,
                previous_position_key=previous_position_key,
                assigned_position_key=assigned_position_key,
                status=status,
                occurred_at=row.occurred_at,
                causation_activity_id=row.causation_activity_id,
                canonical_basis="organization.work.assigned.v1 OrganizationActivity",
            )
        )
    return tuple(result)


def austria_living_organization_scene(
    session: Session,
    *,
    tenant_key: str,
    snapshot: AustriaLiveOrganizationSnapshot,
) -> LivingOrganizationScene:
    works = _scene_work_items(session, tenant_key=tenant_key, snapshot=snapshot)
    work_by_id = {item.id: item for item in works}
    work_ids = tuple(item.id for item in works)
    conversations = _scene_conversations(
        session,
        tenant_key=tenant_key,
        work_item_ids=work_ids,
    )
    handoffs = _scene_handoffs(
        session,
        tenant_key=tenant_key,
        work_item_ids=work_ids,
    )
    position_keys = tuple(
        dict.fromkeys(
            [item.assigned_position_key for item in works]
            + [
                position_key
                for conversation in conversations
                for position_key in conversation.participant_position_keys
            ]
            + [
                position_key
                for handoff in handoffs
                for position_key in (
                    handoff.previous_position_key,
                    handoff.assigned_position_key,
                )
            ]
        )
    )
    positions = _latest_position_rows(session, position_keys=position_keys)
    blockers = _scene_blockers(session, tenant_key=tenant_key, snapshot=snapshot)
    blocked_work_ids = {
        blocker.work_item_id
        for blocker in blockers
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

    projected_employee_keys = {employee.position_key for employee in employees}
    for position_key in position_keys:
        if position_key in projected_employee_keys:
            continue
        position = positions[position_key]
        employees.append(
            LivingSceneEmployee(
                position_key=position.position_key,
                title=position.title,
                department=position.department,
                reports_to_position_key=position.reports_to_position_key,
                authority_level=position.authority_level,
                organization_status=position.status,
                work_item_id=None,
                work_status=None,
                semantic_state="unknown",
                presence_state="not_asserted",
                state_reason=(
                    "Included by canonical conversation or handoff lineage; "
                    "no current WorkItem assignment is asserted."
                ),
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

    decisions = _scene_decisions(session, tenant_key=tenant_key, work_item_ids=work_ids)
    decision_ids = {item.decision_id for item in decisions}
    blocker_ids = {item.blocker_id for item in blockers}
    human_actions = _scene_human_actions(
        session,
        tenant_key=tenant_key,
        work_item_ids=work_ids,
        decision_ids=decision_ids,
        blocker_ids=blocker_ids,
    )
    risk_escalations = _scene_risk_escalations(session, work_item_ids=work_ids)
    decision_attention = sum(1 for decision in decisions if decision.required_owner_action)
    board_risk_attention = sum(1 for risk in risk_escalations if risk.requires_board_attention)
    board_attention = decision_attention + len(human_actions) + board_risk_attention
    source_snapshot_count = len(snapshot.source_snapshot_refs)
    evidence_count = (
        len(snapshot.domain_evidence_refs)
        + len(snapshot.verified_rule_refs)
        + source_snapshot_count
    )
    model_activity_count = sum(
        1 for specialist in snapshot.specialist_outputs if specialist.agent_run_id is not None
    )


    department_keys = tuple(
        sorted({work.department for work in works} | {employee.department for employee in employees})
    )
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
        LivingSceneSmartObject(object_key=f"mission-board:{snapshot.root_work_item_id}", object_type="mission_board", label="Mission Board", state=snapshot.cycle_status, metric_label="WorkItems", metric_value=len(work_items), projection_only=True, canonical_basis="OrganizationalWorkItem objective topology"),
        LivingSceneSmartObject(object_key=f"evidence-shelf:{snapshot.root_work_item_id}", object_type="evidence_shelf", label="Evidence Shelf", state="grounded" if evidence_count else "empty", metric_label="Evidence + Rules + SourceSnapshots", metric_value=evidence_count, projection_only=True, canonical_basis="Persisted context Evidence, VerifiedRule and SourceSnapshot references"),
        LivingSceneSmartObject(object_key=f"regulatory-monitor:{snapshot.root_work_item_id}", object_type="regulatory_monitor", label="Regulatory Monitor", state="source_provenance_recorded" if source_snapshot_count else "no_snapshot_provenance", metric_label="SourceSnapshot references", metric_value=source_snapshot_count, projection_only=True, canonical_basis="Persisted K.1 context_source_snapshot_refs; does not claim SourceRetrievalRun freshness because K.1 does not persist the retrieval-run reference"),
        LivingSceneSmartObject(object_key=f"blocker-wall:{snapshot.root_work_item_id}", object_type="blocker_wall", label="Blocker Wall", state="attention" if blockers else "clear", metric_label="Canonical blockers", metric_value=len(blockers), projection_only=True, canonical_basis="OrganizationBlocker canonical records linked to scene WorkItems"),
        LivingSceneSmartObject(object_key=f"board-desk:{snapshot.root_work_item_id}", object_type="board_desk", label="Board Desk", state="attention" if decision_attention else "quiet", metric_label="Owner decisions", metric_value=decision_attention, projection_only=True, canonical_basis="Current ExecutiveDecision records requiring Board action"),
        LivingSceneSmartObject(object_key=f"owner-inbox:{snapshot.root_work_item_id}", object_type="owner_inbox", label="Owner Inbox", state="attention" if human_actions or board_risk_attention else "clear", metric_label="Human actions + Board risks", metric_value=len(human_actions) + board_risk_attention, projection_only=True, canonical_basis="Open OrganizationHumanActionRequest records plus Board-attention RiskEscalation records"),
        LivingSceneSmartObject(object_key=f"risk-beacon:{snapshot.root_work_item_id}", object_type="risk_beacon", label="Risk Beacon", state="attention" if risk_escalations else "clear", metric_label="Open risk escalations", metric_value=len(risk_escalations), projection_only=True, canonical_basis="Open RiskEscalation records linked to scene WorkItems"),
        LivingSceneSmartObject(object_key=f"immune-center:{snapshot.root_work_item_id}", object_type="immune_center", label="Immune Center", state="unavailable", metric_label="Scene-scoped immune state unavailable", metric_value=None, projection_only=True, canonical_basis="The canonical eligibility immune circuit is aggregate-scoped and is not linked to this Austria WorkItem scene; unrelated immune state is not projected"),
        LivingSceneSmartObject(object_key=f"model-terminal:{snapshot.root_work_item_id}", object_type="model_terminal", label="Model Terminal", state="activity_recorded" if model_activity_count else "idle", metric_label="AgentRun-linked specialists", metric_value=model_activity_count, projection_only=True, canonical_basis="Persisted specialist AgentRun lineage only; provider/model identity has no organizational authority and does not authorize external action"),
        LivingSceneSmartObject(object_key=f"incident-beacon:{snapshot.root_work_item_id}", object_type="incident_beacon", label="Incident Beacon", state="unavailable", metric_label="Canonical Incident model unavailable", metric_value=None, projection_only=True, canonical_basis="No canonical Incident model is connected in M.6; beacon activity is not fabricated"),
        LivingSceneSmartObject(object_key=f"cost-display:{snapshot.root_work_item_id}", object_type="cost_display", label="Cost Display", state="unavailable", metric_label="Canonical organization cost unavailable", metric_value=None, projection_only=True, canonical_basis="Runtime telemetry may contain estimates, but no canonical organization cost ledger exists in M.6"),
    )

    rooms = (
        LivingSceneRoom(room_key=f"mission:{snapshot.root_work_item_id}", room_type="mission_room", label=snapshot.objective_key, state=snapshot.cycle_status, metric_label="WorkItems", metric_value=len(work_items), projection_only=True, canonical_basis="OrganizationalWorkItem objective topology"),
        LivingSceneRoom(room_key=f"evidence:{snapshot.root_work_item_id}", room_type="evidence_lab", label="Evidence Lab", state="grounded" if evidence_count else "empty", metric_label="Evidence + Rules + SourceSnapshots", metric_value=evidence_count, projection_only=True, canonical_basis="Persisted context Evidence, VerifiedRule and SourceSnapshot references"),
        LivingSceneRoom(room_key=f"board:{snapshot.root_work_item_id}", room_type="board_room", label="Board Room", state="attention" if board_attention else "quiet", metric_label="Board attention items", metric_value=board_attention, projection_only=True, canonical_basis="ExecutiveDecision + OrganizationHumanActionRequest + RiskEscalation projections"),
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

    for conversation in conversations:
        for position_key in conversation.participant_position_keys:
            relationships.append(
                LivingSceneRelationship(
                    relationship_key=f"conversation:{conversation.conversation_id}:{position_key}",
                    relationship_type="participates_in_conversation",
                    source_type="employee",
                    source_id=position_key,
                    target_type="conversation",
                    target_id=conversation.conversation_id,
                    canonical_basis="OrganizationActivity conversation participant_position_keys",
                )
            )
        relationships.append(
            LivingSceneRelationship(
                relationship_key=(
                    f"conversation-work:{conversation.conversation_id}:{conversation.work_item_id}"
                ),
                relationship_type="coordinates_work",
                source_type="conversation",
                source_id=conversation.conversation_id,
                target_type="work_item",
                target_id=str(conversation.work_item_id),
                canonical_basis="OrganizationActivity conversation work_item_id",
            )
        )

    for handoff in handoffs:
        relationships.append(
            LivingSceneRelationship(
                relationship_key=f"handoff:{handoff.activity_id}",
                relationship_type="governed_handoff",
                source_type="employee",
                source_id=handoff.previous_position_key,
                target_type="employee",
                target_id=handoff.assigned_position_key,
                canonical_basis="organization.work.assigned.v1 OrganizationActivity",
            )
        )

    for request in human_actions:
        for target_type, target_id in (("work_item", request.work_item_id), ("decision", request.decision_id), ("blocker", request.blocker_id)):
            if target_id is not None:
                relationships.append(LivingSceneRelationship(
                    relationship_key=f"human-action:{request.request_id}:{target_type}:{target_id}",
                    relationship_type="requires_human_action",
                    source_type="human_action_request",
                    source_id=str(request.request_id),
                    target_type=target_type,
                    target_id=str(target_id),
                    canonical_basis=request.canonical_basis,
                ))

    for risk in risk_escalations:
        if risk.work_item_id is not None:
            relationships.append(LivingSceneRelationship(
                relationship_key=f"risk-work:{risk.risk_id}:{risk.work_item_id}",
                relationship_type="escalates_risk",
                source_type="risk_escalation",
                source_id=str(risk.risk_id),
                target_type="work_item",
                target_id=str(risk.work_item_id),
                canonical_basis=risk.canonical_basis,
            ))

    return LivingOrganizationScene(
        contract_version=LIVING_ORGANIZATION_SCENE_CONTRACT_VERSION,
        generated_at=now_utc(),
        scope="austria_mobility",
        root_work_item_id=snapshot.root_work_item_id,
        objective_key=snapshot.objective_key,
        coverage=LivingSceneCoverage(
            departments="projected_from_canonical_positions_and_work",
            missions="workitem_objective_topology_projection",
            conversations="organization_activity_conversation_lifecycle_v1",
            handoffs="organization_work_assigned_activity_v1",
            blockers="organization_blocker_canonical_records",
            human_actions="organization_human_action_request_open_records",
            risk_escalations="risk_escalation_open_records",
            incidents="unavailable_no_canonical_incident_model",
            smart_objects="m6_read_only_canonical_projections",
            runtime_costs="unavailable_no_canonical_organization_cost_ledger",
            presence="not_asserted_m6",
        ),
        deterministic=LivingSceneDeterministicPlane(
            canonical_projection=True,
            authoritative=False,
            departments=departments,
            missions=missions,
            employees=tuple(employees),
            work_items=work_items,
            conversations=conversations,
            handoffs=handoffs,
            blockers=blockers,
            decisions=decisions,
            human_actions=human_actions,
            risk_escalations=risk_escalations,
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

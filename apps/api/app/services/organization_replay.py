from __future__ import annotations

from dataclasses import dataclass
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationalWorkItem, now_utc
from app.services.organization_activity import activity_coverage_epoch
from app.services.organization_command import DependencyConflict
from app.services.organization_mobility_live_organization import (
    latest_austria_live_organization_snapshot,
)


ORGANIZATION_REPLAY_CONTRACT_VERSION = "organization-replay.v1"
ORGANIZATION_REPLAY_STATE_CONTRACT_VERSION = "organization-replay-state.v1"
ORGANIZATION_REPLAY_STATE_DIFF_CONTRACT_VERSION = "organization-replay-state-diff.v1"
ORGANIZATION_REPLAY_EVENT_LIMIT = 500
ORGANIZATION_REPLAY_STATE_EVENT_LIMIT = 5000


@dataclass(frozen=True, slots=True)
class OrganizationReplayCoverage:
    activity_history_basis: str
    activity_history_established: bool
    activity_history_coverage_start: datetime | None
    pre_epoch_history: str
    evidence_history: str
    risk_escalation_history: str
    source_snapshot_history: str
    conversation_history: str


@dataclass(frozen=True, slots=True)
class OrganizationReplayEvent:
    activity_id: UUID
    event_kind: str
    coverage_state: str
    stream_sequence: int
    activity_class: str
    activity_type: str
    title: str
    summary: str
    actor_type: str
    actor_id: str
    department: str | None
    position_key: str | None
    authority_level: str | None
    work_item_id: UUID | None
    source_object_type: str
    source_object_id: str
    source_object_version: str | None
    correlation_key: str | None
    causation_activity_id: UUID | None
    supersedes_activity_id: UUID | None
    occurred_at: datetime



@dataclass(frozen=True, slots=True)
class OrganizationReplayStateWorkItem:
    work_item_id: UUID
    status: str
    priority: str
    department: str
    assigned_position_key: str
    parent_work_item_id: UUID | None
    coverage_state: str
    known_from_activity_id: UUID
    last_activity_id: UUID
    last_occurred_at: datetime


@dataclass(frozen=True, slots=True)
class OrganizationReplayStateBlocker:
    blocker_id: UUID
    work_item_id: UUID | None
    status: str
    blocker_type: str
    severity: str
    requires_human_action: bool
    coverage_state: str
    known_from_activity_id: UUID
    last_activity_id: UUID
    last_occurred_at: datetime


@dataclass(frozen=True, slots=True)
class OrganizationReplayStateDecision:
    decision_id: UUID
    work_item_id: UUID | None
    status: str
    decision_type: str
    authority_level: str
    coverage_state: str
    known_from_activity_id: UUID
    last_activity_id: UUID
    last_occurred_at: datetime


@dataclass(frozen=True, slots=True)
class OrganizationReplayStateHumanRequest:
    request_id: UUID
    work_item_id: UUID | None
    status: str
    request_type: str
    required_role: str
    coverage_state: str
    known_from_activity_id: UUID
    last_activity_id: UUID
    last_occurred_at: datetime


@dataclass(frozen=True, slots=True)
class OrganizationReplayStateConversation:
    conversation_id: str
    work_item_id: UUID | None
    status: str
    coverage_state: str
    known_from_activity_id: UUID
    last_activity_id: UUID
    last_occurred_at: datetime


@dataclass(frozen=True, slots=True)
class OrganizationReplayState:
    contract_version: str
    generated_at: datetime
    scope: str
    root_work_item_id: UUID
    objective_key: str
    cursor_activity_id: UUID
    cursor_occurred_at: datetime
    cursor_coverage_state: str
    reconstruction_posture: str
    canonical_projection: bool
    authoritative: bool
    mutations_allowed: bool
    supported_dimensions: tuple[str, ...]
    unsupported_dimensions: tuple[str, ...]
    unapplied_transition_count: int
    work_items: tuple[OrganizationReplayStateWorkItem, ...]
    blockers: tuple[OrganizationReplayStateBlocker, ...]
    decisions: tuple[OrganizationReplayStateDecision, ...]
    human_requests: tuple[OrganizationReplayStateHumanRequest, ...]
    conversations: tuple[OrganizationReplayStateConversation, ...]


@dataclass(frozen=True, slots=True)
class OrganizationReplayStateDiffCursor:
    activity_id: UUID
    occurred_at: datetime
    coverage_state: str
    reconstruction_posture: str
    unapplied_transition_count: int


@dataclass(frozen=True, slots=True)
class OrganizationReplayStateDelta:
    entity_id: str
    change_kind: str
    changed_fields: tuple[str, ...]
    before: object | None
    after: object | None


@dataclass(frozen=True, slots=True)
class OrganizationReplayStateDiff:
    contract_version: str
    generated_at: datetime
    scope: str
    root_work_item_id: UUID
    objective_key: str
    comparison_basis: str
    from_cursor: OrganizationReplayStateDiffCursor
    to_cursor: OrganizationReplayStateDiffCursor
    comparison_posture: str
    canonical_projection: bool
    authoritative: bool
    mutations_allowed: bool
    supported_dimensions: tuple[str, ...]
    unsupported_dimensions: tuple[str, ...]
    unchanged_entities_omitted: bool
    changed_entity_count: int
    work_items: tuple[OrganizationReplayStateDelta, ...]
    blockers: tuple[OrganizationReplayStateDelta, ...]
    decisions: tuple[OrganizationReplayStateDelta, ...]
    human_requests: tuple[OrganizationReplayStateDelta, ...]
    conversations: tuple[OrganizationReplayStateDelta, ...]


@dataclass(frozen=True, slots=True)
class OrganizationReplay:
    contract_version: str
    generated_at: datetime
    scope: str
    root_work_item_id: UUID
    objective_key: str
    work_item_ids: tuple[UUID, ...]
    canonical_projection: bool
    authoritative: bool
    mutations_allowed: bool
    coverage: OrganizationReplayCoverage
    total_events: int
    returned_events: int
    truncated: bool
    events: tuple[OrganizationReplayEvent, ...]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _work_tree_ids(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
) -> tuple[UUID, ...]:
    rows = list(
        session.exec(
            select(OrganizationalWorkItem).where(
                OrganizationalWorkItem.tenant_key == tenant_key
            )
        ).all()
    )
    by_id = {row.id: row for row in rows}
    if root_work_item_id not in by_id:
        raise DependencyConflict("replay root WorkItem is missing from canonical organization records")

    children: dict[UUID, list[UUID]] = {}
    for row in rows:
        if row.parent_work_item_id is None:
            continue
        children.setdefault(row.parent_work_item_id, []).append(row.id)

    ordered: list[UUID] = []
    seen: set[UUID] = set()
    stack: list[UUID] = [root_work_item_id]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        ordered.append(current)
        for child in sorted(children.get(current, ()), key=str, reverse=True):
            stack.append(child)
    return tuple(ordered)


def _event_kind(activity: OrganizationActivity) -> str:
    if activity.activity_type == "organization.work.assigned.v1":
        return "handoff"
    if activity.source_object_type == "organization_conversation":
        return "conversation"
    if activity.activity_type.startswith("organization.work.evidence."):
        return "evidence"
    if activity.source_object_type == "organization_work_item_dependency":
        return "dependency"
    if activity.activity_class.value == "blocker":
        return "blocker"
    if activity.activity_class.value == "decision":
        return "decision"
    if activity.activity_class.value == "human_action":
        return "human_action"
    if activity.activity_class.value == "contribution":
        return "contribution"
    if activity.activity_class.value == "work":
        return "work"
    return "operational"


def _coverage_state(
    activity: OrganizationActivity,
    *,
    coverage_start: datetime | None,
) -> str:
    if coverage_start is None:
        return "partial_no_epoch"
    if _as_utc(activity.occurred_at) < _as_utc(coverage_start):
        return "pre_epoch_partial"
    return "covered"


def latest_austria_organization_replay(
    session: Session,
    *,
    tenant_key: str,
) -> OrganizationReplay | None:
    """Project persisted semantic Activity into a Board-safe temporal replay.

    This function never backfills or synthesizes missing history. The explicit
    semantic Activity coverage epoch is the completeness boundary.
    """

    snapshot = latest_austria_live_organization_snapshot(session, tenant_key=tenant_key)
    if snapshot is None:
        return None

    work_item_ids = _work_tree_ids(
        session,
        tenant_key=tenant_key,
        root_work_item_id=snapshot.root_work_item_id,
    )
    conditions = (
        OrganizationActivity.tenant_key == tenant_key,
        OrganizationActivity.work_item_id.in_(work_item_ids),
    )
    total_events = int(
        session.exec(
            select(func.count()).select_from(OrganizationActivity).where(*conditions)
        ).one()
    )
    newest = list(
        session.exec(
            select(OrganizationActivity)
            .where(*conditions)
            .order_by(
                OrganizationActivity.occurred_at.desc(),
                OrganizationActivity.created_at.desc(),
                OrganizationActivity.stream_sequence.desc(),
                OrganizationActivity.id.desc(),
            )
            .limit(ORGANIZATION_REPLAY_EVENT_LIMIT)
        ).all()
    )
    activities = tuple(reversed(newest))

    epoch = activity_coverage_epoch(session, tenant_key)
    coverage_start = epoch.occurred_at if epoch is not None else None
    coverage = OrganizationReplayCoverage(
        activity_history_basis=(
            "explicit_activity_coverage_epoch"
            if epoch is not None
            else "partial_activity_coverage"
        ),
        activity_history_established=epoch is not None,
        activity_history_coverage_start=coverage_start,
        pre_epoch_history="partial_no_backfill",
        evidence_history="semantic_work_evidence_amendments_only",
        risk_escalation_history="unavailable_no_semantic_activity_adapter",
        source_snapshot_history="unavailable_not_linked_to_replay_activity",
        conversation_history="lifecycle_only_transcript_not_persisted",
    )

    events = tuple(
        OrganizationReplayEvent(
            activity_id=activity.id,
            event_kind=_event_kind(activity),
            coverage_state=_coverage_state(activity, coverage_start=coverage_start),
            stream_sequence=activity.stream_sequence,
            activity_class=activity.activity_class.value,
            activity_type=activity.activity_type,
            title=activity.title,
            summary=activity.summary,
            actor_type=activity.actor_type.value,
            actor_id=activity.actor_id,
            department=activity.department,
            position_key=activity.position_key,
            authority_level=activity.authority_level,
            work_item_id=activity.work_item_id,
            source_object_type=activity.source_object_type,
            source_object_id=activity.source_object_id,
            source_object_version=activity.source_object_version,
            correlation_key=activity.correlation_key,
            causation_activity_id=activity.causation_activity_id,
            supersedes_activity_id=activity.supersedes_activity_id,
            occurred_at=activity.occurred_at,
        )
        for activity in activities
    )
    return OrganizationReplay(
        contract_version=ORGANIZATION_REPLAY_CONTRACT_VERSION,
        generated_at=now_utc(),
        scope="austria_mobility_latest_work_tree",
        root_work_item_id=snapshot.root_work_item_id,
        objective_key=snapshot.objective_key,
        work_item_ids=work_item_ids,
        canonical_projection=True,
        authoritative=False,
        mutations_allowed=False,
        coverage=coverage,
        total_events=total_events,
        returned_events=len(events),
        truncated=total_events > len(events),
        events=events,
    )

def _payload_object(activity: OrganizationActivity) -> dict[str, object]:
    try:
        payload = json.loads(activity.payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict(
            f"Activity {activity.id} has invalid replay payload JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise DependencyConflict(f"Activity {activity.id} replay payload is not an object")
    return payload


def _required_payload_string(
    activity: OrganizationActivity,
    payload: dict[str, object],
    key: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise DependencyConflict(
            f"Activity {activity.id} replay payload field {key!r} is invalid"
        )
    return value


def _required_payload_bool(
    activity: OrganizationActivity,
    payload: dict[str, object],
    key: str,
) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise DependencyConflict(
            f"Activity {activity.id} replay payload field {key!r} is invalid"
        )
    return value


def _optional_payload_uuid(
    activity: OrganizationActivity,
    payload: dict[str, object],
    key: str,
) -> UUID | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise DependencyConflict(
            f"Activity {activity.id} replay payload field {key!r} is invalid"
        )
    try:
        return UUID(value)
    except ValueError as exc:
        raise DependencyConflict(
            f"Activity {activity.id} replay payload field {key!r} is not a UUID"
        ) from exc


def _source_uuid(activity: OrganizationActivity) -> UUID:
    try:
        return UUID(activity.source_object_id)
    except ValueError as exc:
        raise DependencyConflict(
            f"Activity {activity.id} source identity is not a UUID"
        ) from exc


def _merge_coverage(current: str, incoming: str) -> str:
    rank = {"covered": 0, "pre_epoch_partial": 1, "partial_no_epoch": 2}
    return current if rank.get(current, 3) >= rank.get(incoming, 3) else incoming


def latest_austria_organization_replay_state(
    session: Session,
    *,
    tenant_key: str,
    cursor_activity_id: UUID,
) -> OrganizationReplayState | None:
    """Reconstruct bounded as-of state only from explicit semantic Activity transitions."""

    snapshot = latest_austria_live_organization_snapshot(session, tenant_key=tenant_key)
    if snapshot is None:
        return None

    work_item_ids = _work_tree_ids(
        session,
        tenant_key=tenant_key,
        root_work_item_id=snapshot.root_work_item_id,
    )
    conditions = (
        OrganizationActivity.tenant_key == tenant_key,
        OrganizationActivity.work_item_id.in_(work_item_ids),
    )
    cursor = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.id == cursor_activity_id,
            *conditions,
        )
    ).first()
    if cursor is None:
        return None

    ordered = list(
        session.exec(
            select(OrganizationActivity)
            .where(*conditions)
            .order_by(
                OrganizationActivity.occurred_at.asc(),
                OrganizationActivity.created_at.asc(),
                OrganizationActivity.stream_sequence.asc(),
                OrganizationActivity.id.asc(),
            )
            .limit(ORGANIZATION_REPLAY_STATE_EVENT_LIMIT + 1)
        ).all()
    )
    cursor_index = next(
        (index for index, activity in enumerate(ordered) if activity.id == cursor_activity_id),
        None,
    )
    if cursor_index is None:
        if len(ordered) > ORGANIZATION_REPLAY_STATE_EVENT_LIMIT:
            raise DependencyConflict(
                "replay state cursor exceeds the bounded reconstruction window"
            )
        raise DependencyConflict("replay state cursor is missing from the ordered Activity stream")
    activities = ordered[: cursor_index + 1]

    epoch = activity_coverage_epoch(session, tenant_key)
    coverage_start = epoch.occurred_at if epoch is not None else None
    cursor_coverage_state = _coverage_state(cursor, coverage_start=coverage_start)

    work_states: dict[UUID, dict[str, object]] = {}
    blocker_states: dict[UUID, dict[str, object]] = {}
    decision_states: dict[UUID, dict[str, object]] = {}
    human_states: dict[UUID, dict[str, object]] = {}
    conversation_states: dict[str, dict[str, object]] = {}
    unapplied_transition_count = 0

    for activity in activities:
        coverage_state = _coverage_state(activity, coverage_start=coverage_start)
        payload = _payload_object(activity)
        activity_type = activity.activity_type

        if activity_type == "organization.work.created.v1":
            if activity.work_item_id is None:
                raise DependencyConflict("work creation Activity lacks WorkItem identity")
            work_states[activity.work_item_id] = {
                "work_item_id": activity.work_item_id,
                "status": _required_payload_string(activity, payload, "status"),
                "priority": _required_payload_string(activity, payload, "priority"),
                "department": _required_payload_string(activity, payload, "department"),
                "assigned_position_key": _required_payload_string(
                    activity, payload, "assigned_position_key"
                ),
                "parent_work_item_id": _optional_payload_uuid(
                    activity, payload, "parent_work_item_id"
                ),
                "coverage_state": coverage_state,
                "known_from_activity_id": activity.id,
                "last_activity_id": activity.id,
                "last_occurred_at": activity.occurred_at,
            }
            continue

        if (
            activity.source_object_type == "organizational_work_item"
            and activity.work_item_id is not None
            and (
                activity_type.startswith("organization.work.status.")
                or activity_type == "organization.work.assigned.v1"
            )
        ):
            state = work_states.get(activity.work_item_id)
            if state is None:
                unapplied_transition_count += 1
                continue
            if activity_type.startswith("organization.work.status."):
                state["status"] = _required_payload_string(activity, payload, "status")
            else:
                state["assigned_position_key"] = _required_payload_string(
                    activity, payload, "assigned_position_key"
                )
                state["status"] = _required_payload_string(activity, payload, "status")
            state["coverage_state"] = _merge_coverage(
                str(state["coverage_state"]), coverage_state
            )
            state["last_activity_id"] = activity.id
            state["last_occurred_at"] = activity.occurred_at
            continue

        if activity_type == "organization.blocker.opened.v1":
            blocker_id = _source_uuid(activity)
            blocker_states[blocker_id] = {
                "blocker_id": blocker_id,
                "work_item_id": activity.work_item_id,
                "status": _required_payload_string(activity, payload, "status"),
                "blocker_type": _required_payload_string(activity, payload, "blocker_type"),
                "severity": _required_payload_string(activity, payload, "severity"),
                "requires_human_action": _required_payload_bool(
                    activity, payload, "requires_human_action"
                ),
                "coverage_state": coverage_state,
                "known_from_activity_id": activity.id,
                "last_activity_id": activity.id,
                "last_occurred_at": activity.occurred_at,
            }
            continue

        if activity_type.startswith("organization.blocker.status."):
            blocker_id = _source_uuid(activity)
            state = blocker_states.get(blocker_id)
            if state is None:
                unapplied_transition_count += 1
                continue
            state["status"] = _required_payload_string(activity, payload, "status")
            state["severity"] = _required_payload_string(activity, payload, "severity")
            state["coverage_state"] = _merge_coverage(
                str(state["coverage_state"]), coverage_state
            )
            state["last_activity_id"] = activity.id
            state["last_occurred_at"] = activity.occurred_at
            continue

        if activity_type == "organization.decision.created.v1":
            decision_id = _source_uuid(activity)
            decision_states[decision_id] = {
                "decision_id": decision_id,
                "work_item_id": activity.work_item_id,
                "status": _required_payload_string(activity, payload, "status"),
                "decision_type": _required_payload_string(activity, payload, "decision_type"),
                "authority_level": _required_payload_string(
                    activity, payload, "authority_level"
                ),
                "coverage_state": coverage_state,
                "known_from_activity_id": activity.id,
                "last_activity_id": activity.id,
                "last_occurred_at": activity.occurred_at,
            }
            continue

        if activity_type.startswith("organization.decision.status."):
            decision_id = _source_uuid(activity)
            state = decision_states.get(decision_id)
            if state is None:
                unapplied_transition_count += 1
                continue
            state["status"] = _required_payload_string(activity, payload, "status")
            state["decision_type"] = _required_payload_string(
                activity, payload, "decision_type"
            )
            state["authority_level"] = _required_payload_string(
                activity, payload, "authority_level"
            )
            state["coverage_state"] = _merge_coverage(
                str(state["coverage_state"]), coverage_state
            )
            state["last_activity_id"] = activity.id
            state["last_occurred_at"] = activity.occurred_at
            continue

        if activity_type == "organization.human_request.created.v1":
            request_id = _source_uuid(activity)
            human_states[request_id] = {
                "request_id": request_id,
                "work_item_id": activity.work_item_id,
                "status": _required_payload_string(activity, payload, "status"),
                "request_type": _required_payload_string(activity, payload, "request_type"),
                "required_role": _required_payload_string(activity, payload, "required_role"),
                "coverage_state": coverage_state,
                "known_from_activity_id": activity.id,
                "last_activity_id": activity.id,
                "last_occurred_at": activity.occurred_at,
            }
            continue

        if activity_type.startswith("organization.human_request.status."):
            request_id = _source_uuid(activity)
            state = human_states.get(request_id)
            if state is None:
                unapplied_transition_count += 1
                continue
            state["status"] = _required_payload_string(activity, payload, "status")
            state["request_type"] = _required_payload_string(
                activity, payload, "request_type"
            )
            state["coverage_state"] = _merge_coverage(
                str(state["coverage_state"]), coverage_state
            )
            state["last_activity_id"] = activity.id
            state["last_occurred_at"] = activity.occurred_at
            continue

        if (
            activity.source_object_type == "organization_conversation"
            and activity_type == "organization.conversation.opened.v1"
        ):
            conversation_states[activity.source_object_id] = {
                "conversation_id": activity.source_object_id,
                "work_item_id": activity.work_item_id,
                "status": "open",
                "coverage_state": coverage_state,
                "known_from_activity_id": activity.id,
                "last_activity_id": activity.id,
                "last_occurred_at": activity.occurred_at,
            }
            continue

        if (
            activity.source_object_type == "organization_conversation"
            and activity_type == "organization.conversation.closed.v1"
        ):
            state = conversation_states.get(activity.source_object_id)
            if state is None:
                unapplied_transition_count += 1
                continue
            state["status"] = "closed"
            state["coverage_state"] = _merge_coverage(
                str(state["coverage_state"]), coverage_state
            )
            state["last_activity_id"] = activity.id
            state["last_occurred_at"] = activity.occurred_at

    reconstructed_coverages = [
        str(item["coverage_state"])
        for collection in (
            work_states.values(),
            blocker_states.values(),
            decision_states.values(),
            human_states.values(),
            conversation_states.values(),
        )
        for item in collection
    ]
    if cursor_coverage_state == "partial_no_epoch":
        reconstruction_posture = "partial_no_epoch"
    elif cursor_coverage_state == "pre_epoch_partial":
        reconstruction_posture = "pre_epoch_partial"
    elif unapplied_transition_count or any(
        value != "covered" for value in reconstructed_coverages
    ):
        reconstruction_posture = "covered_cursor_with_partial_prerequisites"
    else:
        reconstruction_posture = "covered"

    return OrganizationReplayState(
        contract_version=ORGANIZATION_REPLAY_STATE_CONTRACT_VERSION,
        generated_at=now_utc(),
        scope="austria_mobility_latest_work_tree_as_of_activity",
        root_work_item_id=snapshot.root_work_item_id,
        objective_key=snapshot.objective_key,
        cursor_activity_id=cursor.id,
        cursor_occurred_at=cursor.occurred_at,
        cursor_coverage_state=cursor_coverage_state,
        reconstruction_posture=reconstruction_posture,
        canonical_projection=True,
        authoritative=False,
        mutations_allowed=False,
        supported_dimensions=(
            "work_item_status_assignment",
            "blocker_lifecycle",
            "decision_lifecycle",
            "human_request_lifecycle",
            "conversation_lifecycle",
        ),
        unsupported_dimensions=(
            "risk_escalation_history",
            "source_snapshot_history",
            "conversation_transcript",
            "historical_deadline_projection_v1",
            "historical_evidence_content_state_v1",
        ),
        unapplied_transition_count=unapplied_transition_count,
        work_items=tuple(
            OrganizationReplayStateWorkItem(**item)
            for _, item in sorted(work_states.items(), key=lambda pair: str(pair[0]))
        ),
        blockers=tuple(
            OrganizationReplayStateBlocker(**item)
            for _, item in sorted(blocker_states.items(), key=lambda pair: str(pair[0]))
        ),
        decisions=tuple(
            OrganizationReplayStateDecision(**item)
            for _, item in sorted(decision_states.items(), key=lambda pair: str(pair[0]))
        ),
        human_requests=tuple(
            OrganizationReplayStateHumanRequest(**item)
            for _, item in sorted(human_states.items(), key=lambda pair: str(pair[0]))
        ),
        conversations=tuple(
            OrganizationReplayStateConversation(**item)
            for _, item in sorted(conversation_states.items(), key=lambda pair: pair[0])
        ),
    )

def _state_diff_collection(
    before_items: tuple[object, ...],
    after_items: tuple[object, ...],
    *,
    id_attr: str,
    compared_fields: tuple[str, ...],
) -> tuple[OrganizationReplayStateDelta, ...]:
    before_by_id = {str(getattr(item, id_attr)): item for item in before_items}
    after_by_id = {str(getattr(item, id_attr)): item for item in after_items}
    deltas: list[OrganizationReplayStateDelta] = []

    for entity_id in sorted(set(before_by_id) | set(after_by_id)):
        before = before_by_id.get(entity_id)
        after = after_by_id.get(entity_id)
        if before is None:
            deltas.append(
                OrganizationReplayStateDelta(
                    entity_id=entity_id,
                    change_kind="added",
                    changed_fields=(),
                    before=None,
                    after=after,
                )
            )
            continue
        if after is None:
            deltas.append(
                OrganizationReplayStateDelta(
                    entity_id=entity_id,
                    change_kind="removed",
                    changed_fields=(),
                    before=before,
                    after=None,
                )
            )
            continue

        changed_fields = tuple(
            field
            for field in compared_fields
            if getattr(before, field) != getattr(after, field)
        )
        if changed_fields:
            deltas.append(
                OrganizationReplayStateDelta(
                    entity_id=entity_id,
                    change_kind="changed",
                    changed_fields=changed_fields,
                    before=before,
                    after=after,
                )
            )

    return tuple(deltas)


def latest_austria_organization_replay_state_diff(
    session: Session,
    *,
    tenant_key: str,
    from_cursor_activity_id: UUID,
    to_cursor_activity_id: UUID,
) -> OrganizationReplayStateDiff | None:
    """Compare two proven M.8.2 projections without reconstructing a second history model."""

    from_state = latest_austria_organization_replay_state(
        session,
        tenant_key=tenant_key,
        cursor_activity_id=from_cursor_activity_id,
    )
    to_state = latest_austria_organization_replay_state(
        session,
        tenant_key=tenant_key,
        cursor_activity_id=to_cursor_activity_id,
    )
    if from_state is None or to_state is None:
        return None
    if (
        from_state.root_work_item_id != to_state.root_work_item_id
        or from_state.objective_key != to_state.objective_key
    ):
        raise DependencyConflict("replay state comparison spans different organization roots")
    if (
        not from_state.canonical_projection
        or not to_state.canonical_projection
        or from_state.authoritative
        or to_state.authoritative
        or from_state.mutations_allowed
        or to_state.mutations_allowed
    ):
        raise DependencyConflict("replay state comparison received an invalid reconstruction posture")

    work_items = _state_diff_collection(
        tuple(from_state.work_items),
        tuple(to_state.work_items),
        id_attr="work_item_id",
        compared_fields=(
            "status",
            "priority",
            "department",
            "assigned_position_key",
            "parent_work_item_id",
            "coverage_state",
        ),
    )
    blockers = _state_diff_collection(
        tuple(from_state.blockers),
        tuple(to_state.blockers),
        id_attr="blocker_id",
        compared_fields=(
            "work_item_id",
            "status",
            "blocker_type",
            "severity",
            "requires_human_action",
            "coverage_state",
        ),
    )
    decisions = _state_diff_collection(
        tuple(from_state.decisions),
        tuple(to_state.decisions),
        id_attr="decision_id",
        compared_fields=(
            "work_item_id",
            "status",
            "decision_type",
            "authority_level",
            "coverage_state",
        ),
    )
    human_requests = _state_diff_collection(
        tuple(from_state.human_requests),
        tuple(to_state.human_requests),
        id_attr="request_id",
        compared_fields=(
            "work_item_id",
            "status",
            "request_type",
            "required_role",
            "coverage_state",
        ),
    )
    conversations = _state_diff_collection(
        tuple(from_state.conversations),
        tuple(to_state.conversations),
        id_attr="conversation_id",
        compared_fields=("work_item_id", "status", "coverage_state"),
    )

    postures = {
        from_state.reconstruction_posture,
        to_state.reconstruction_posture,
    }
    if postures == {"covered"}:
        comparison_posture = "covered"
    elif "partial_no_epoch" in postures:
        comparison_posture = "partial_no_epoch"
    elif "pre_epoch_partial" in postures:
        comparison_posture = "pre_epoch_partial"
    else:
        comparison_posture = "covered_cursors_with_partial_prerequisites"

    supported_dimensions = tuple(
        dict.fromkeys((*from_state.supported_dimensions, *to_state.supported_dimensions))
    )
    unsupported_dimensions = tuple(
        dict.fromkeys((*from_state.unsupported_dimensions, *to_state.unsupported_dimensions))
    )
    changed_entity_count = sum(
        len(items)
        for items in (work_items, blockers, decisions, human_requests, conversations)
    )

    return OrganizationReplayStateDiff(
        contract_version=ORGANIZATION_REPLAY_STATE_DIFF_CONTRACT_VERSION,
        generated_at=now_utc(),
        scope="austria_mobility_latest_work_tree_activity_cursor_diff",
        root_work_item_id=from_state.root_work_item_id,
        objective_key=from_state.objective_key,
        comparison_basis="two_organization_replay_state_v1_projections",
        from_cursor=OrganizationReplayStateDiffCursor(
            activity_id=from_state.cursor_activity_id,
            occurred_at=from_state.cursor_occurred_at,
            coverage_state=from_state.cursor_coverage_state,
            reconstruction_posture=from_state.reconstruction_posture,
            unapplied_transition_count=from_state.unapplied_transition_count,
        ),
        to_cursor=OrganizationReplayStateDiffCursor(
            activity_id=to_state.cursor_activity_id,
            occurred_at=to_state.cursor_occurred_at,
            coverage_state=to_state.cursor_coverage_state,
            reconstruction_posture=to_state.reconstruction_posture,
            unapplied_transition_count=to_state.unapplied_transition_count,
        ),
        comparison_posture=comparison_posture,
        canonical_projection=True,
        authoritative=False,
        mutations_allowed=False,
        supported_dimensions=supported_dimensions,
        unsupported_dimensions=unsupported_dimensions,
        unchanged_entities_omitted=True,
        changed_entity_count=changed_entity_count,
        work_items=work_items,
        blockers=blockers,
        decisions=decisions,
        human_requests=human_requests,
        conversations=conversations,
    )

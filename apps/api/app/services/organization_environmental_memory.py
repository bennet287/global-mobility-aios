from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, now_utc
from app.services.organization_command import DependencyConflict
from app.services.organization_replay import OrganizationReplay, latest_austria_organization_replay


ORGANIZATION_ENVIRONMENTAL_MEMORY_CONTRACT_VERSION = "organization-environmental-memory.v1"


@dataclass(frozen=True, slots=True)
class EnvironmentalMemoryCoverage:
    activity_history_basis: str
    activity_history_established: bool
    activity_history_coverage_start: datetime | None
    pre_epoch_history: str
    bounded_replay_window: str
    replay_truncated: bool
    path_history: str


@dataclass(frozen=True, slots=True)
class EnvironmentalMemoryKindAggregate:
    event_kind: str
    event_count: int


@dataclass(frozen=True, slots=True)
class EnvironmentalMemoryPathFrequency:
    previous_position_key: str
    assigned_position_key: str
    handoff_count: int
    work_item_count: int
    first_occurred_at: datetime
    last_occurred_at: datetime
    coverage_state: str


@dataclass(frozen=True, slots=True)
class EnvironmentalMemoryHeatCell:
    department: str
    event_kind: str
    event_count: int
    covered_event_count: int


@dataclass(frozen=True, slots=True)
class EnvironmentalMemoryTimelineBucket:
    bucket_start: datetime
    event_count: int
    handoff_count: int
    blocker_count: int
    decision_count: int
    conversation_count: int
    coverage_state: str


@dataclass(frozen=True, slots=True)
class OrganizationEnvironmentalMemory:
    contract_version: str
    generated_at: datetime
    scope: str
    root_work_item_id: UUID
    objective_key: str
    source_contract_version: str
    canonical_projection: bool
    authoritative: bool
    predictive: bool
    mutations_allowed: bool
    visualization_only: bool
    window_event_count: int
    window_start: datetime | None
    window_end: datetime | None
    coverage: EnvironmentalMemoryCoverage
    kind_aggregates: tuple[EnvironmentalMemoryKindAggregate, ...]
    path_frequencies: tuple[EnvironmentalMemoryPathFrequency, ...]
    heat_cells: tuple[EnvironmentalMemoryHeatCell, ...]
    timeline: tuple[EnvironmentalMemoryTimelineBucket, ...]
    unsupported_dimensions: tuple[str, ...]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _merge_coverage(current: str, incoming: str) -> str:
    rank = {"covered": 0, "pre_epoch_partial": 1, "partial_no_epoch": 2}
    return current if rank.get(current, 3) >= rank.get(incoming, 3) else incoming


def _payload_object(activity: OrganizationActivity) -> dict[str, object]:
    try:
        payload = json.loads(activity.payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict(
            f"Environmental memory Activity {activity.id} has invalid payload JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise DependencyConflict(
            f"Environmental memory Activity {activity.id} payload is not an object"
        )
    return payload


def _handoff_rows(
    session: Session,
    *,
    tenant_key: str,
    replay: OrganizationReplay,
) -> tuple[OrganizationActivity, ...]:
    activity_ids = tuple(
        event.activity_id
        for event in replay.events
        if event.activity_type == "organization.work.assigned.v1"
    )
    if not activity_ids:
        return ()

    rows = list(
        session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.tenant_key == tenant_key,
                OrganizationActivity.id.in_(activity_ids),
            )
        ).all()
    )
    by_id = {row.id: row for row in rows}
    missing = [str(activity_id) for activity_id in activity_ids if activity_id not in by_id]
    if missing:
        raise DependencyConflict(
            "Environmental memory handoff Activity identity is unavailable: "
            + ", ".join(missing)
        )
    return tuple(by_id[activity_id] for activity_id in activity_ids)


def _path_frequencies(
    session: Session,
    *,
    tenant_key: str,
    replay: OrganizationReplay,
) -> tuple[EnvironmentalMemoryPathFrequency, ...]:
    event_coverage = {
        event.activity_id: event.coverage_state
        for event in replay.events
    }
    stats: dict[tuple[str, str], dict[str, object]] = {}

    for activity in _handoff_rows(session, tenant_key=tenant_key, replay=replay):
        if activity.work_item_id is None:
            raise DependencyConflict("Environmental memory handoff lacks WorkItem lineage")
        payload = _payload_object(activity)
        previous_position_key = payload.get("previous_position_key")
        assigned_position_key = payload.get("assigned_position_key")
        if (
            not isinstance(previous_position_key, str)
            or not previous_position_key
            or not isinstance(assigned_position_key, str)
            or not assigned_position_key
            or previous_position_key == assigned_position_key
        ):
            raise DependencyConflict(
                f"Environmental memory handoff {activity.id} has invalid routing identity"
            )
        key = (previous_position_key, assigned_position_key)
        occurred_at = _utc(activity.occurred_at)
        coverage_state = event_coverage[activity.id]
        item = stats.get(key)
        if item is None:
            stats[key] = {
                "handoff_count": 1,
                "work_item_ids": {activity.work_item_id},
                "first_occurred_at": occurred_at,
                "last_occurred_at": occurred_at,
                "coverage_state": coverage_state,
            }
            continue
        item["handoff_count"] = int(item["handoff_count"]) + 1
        work_item_ids = item["work_item_ids"]
        if not isinstance(work_item_ids, set):
            raise DependencyConflict("Environmental memory path aggregate is inconsistent")
        work_item_ids.add(activity.work_item_id)
        item["first_occurred_at"] = min(
            _utc(item["first_occurred_at"]), occurred_at  # type: ignore[arg-type]
        )
        item["last_occurred_at"] = max(
            _utc(item["last_occurred_at"]), occurred_at  # type: ignore[arg-type]
        )
        item["coverage_state"] = _merge_coverage(
            str(item["coverage_state"]), coverage_state
        )

    result = [
        EnvironmentalMemoryPathFrequency(
            previous_position_key=previous,
            assigned_position_key=assigned,
            handoff_count=int(item["handoff_count"]),
            work_item_count=len(item["work_item_ids"]),  # type: ignore[arg-type]
            first_occurred_at=item["first_occurred_at"],  # type: ignore[arg-type]
            last_occurred_at=item["last_occurred_at"],  # type: ignore[arg-type]
            coverage_state=str(item["coverage_state"]),
        )
        for (previous, assigned), item in stats.items()
    ]
    return tuple(
        sorted(
            result,
            key=lambda item: (
                -item.handoff_count,
                item.previous_position_key,
                item.assigned_position_key,
            ),
        )
    )


def latest_austria_organization_environmental_memory(
    session: Session,
    *,
    tenant_key: str,
) -> OrganizationEnvironmentalMemory | None:
    """Return the M.9.1 structured historical baseline derived from the sealed Replay window."""

    replay = latest_austria_organization_replay(session, tenant_key=tenant_key)
    if replay is None:
        return None

    kind_counts = Counter(event.event_kind for event in replay.events)
    kind_aggregates = tuple(
        EnvironmentalMemoryKindAggregate(event_kind=kind, event_count=count)
        for kind, count in sorted(kind_counts.items())
    )

    heat_stats: dict[tuple[str, str], list[int]] = {}
    timeline_stats: dict[datetime, dict[str, object]] = {}
    for event in replay.events:
        department = event.department or "unassigned"
        heat_key = (department, event.event_kind)
        heat = heat_stats.setdefault(heat_key, [0, 0])
        heat[0] += 1
        if event.coverage_state == "covered":
            heat[1] += 1

        bucket_start = _utc(event.occurred_at).replace(
            minute=0,
            second=0,
            microsecond=0,
        )
        bucket = timeline_stats.get(bucket_start)
        if bucket is None:
            bucket = {
                "event_count": 0,
                "handoff_count": 0,
                "blocker_count": 0,
                "decision_count": 0,
                "conversation_count": 0,
                "coverage_state": "covered",
            }
            timeline_stats[bucket_start] = bucket
        bucket["event_count"] = int(bucket["event_count"]) + 1
        if event.event_kind == "handoff":
            bucket["handoff_count"] = int(bucket["handoff_count"]) + 1
        elif event.event_kind == "blocker":
            bucket["blocker_count"] = int(bucket["blocker_count"]) + 1
        elif event.event_kind == "decision":
            bucket["decision_count"] = int(bucket["decision_count"]) + 1
        elif event.event_kind == "conversation":
            bucket["conversation_count"] = int(bucket["conversation_count"]) + 1
        bucket["coverage_state"] = _merge_coverage(
            str(bucket["coverage_state"]),
            event.coverage_state,
        )

    heat_cells = tuple(
        EnvironmentalMemoryHeatCell(
            department=department,
            event_kind=event_kind,
            event_count=counts[0],
            covered_event_count=counts[1],
        )
        for (department, event_kind), counts in sorted(heat_stats.items())
    )
    timeline = tuple(
        EnvironmentalMemoryTimelineBucket(
            bucket_start=bucket_start,
            event_count=int(item["event_count"]),
            handoff_count=int(item["handoff_count"]),
            blocker_count=int(item["blocker_count"]),
            decision_count=int(item["decision_count"]),
            conversation_count=int(item["conversation_count"]),
            coverage_state=str(item["coverage_state"]),
        )
        for bucket_start, item in sorted(timeline_stats.items())
    )

    events = replay.events
    return OrganizationEnvironmentalMemory(
        contract_version=ORGANIZATION_ENVIRONMENTAL_MEMORY_CONTRACT_VERSION,
        generated_at=now_utc(),
        scope="austria_mobility_latest_replay_window_environmental_memory",
        root_work_item_id=replay.root_work_item_id,
        objective_key=replay.objective_key,
        source_contract_version=replay.contract_version,
        canonical_projection=True,
        authoritative=False,
        predictive=False,
        mutations_allowed=False,
        visualization_only=True,
        window_event_count=len(events),
        window_start=events[0].occurred_at if events else None,
        window_end=events[-1].occurred_at if events else None,
        coverage=EnvironmentalMemoryCoverage(
            activity_history_basis=replay.coverage.activity_history_basis,
            activity_history_established=replay.coverage.activity_history_established,
            activity_history_coverage_start=replay.coverage.activity_history_coverage_start,
            pre_epoch_history=replay.coverage.pre_epoch_history,
            bounded_replay_window="sealed_organization_replay_v1_returned_window",
            replay_truncated=replay.truncated,
            path_history="organization.work.assigned.v1_semantic_activity_in_replay_window",
        ),
        kind_aggregates=kind_aggregates,
        path_frequencies=_path_frequencies(
            session,
            tenant_key=tenant_key,
            replay=replay,
        ),
        heat_cells=heat_cells,
        timeline=timeline,
        unsupported_dimensions=(
            "risk_escalation_history",
            "source_snapshot_history",
            "conversation_transcript",
            "future_state_prediction_v1",
            "reaction_diffusion_signal_v1",
        ),
    )

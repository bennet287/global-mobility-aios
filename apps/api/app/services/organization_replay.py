from __future__ import annotations

from dataclasses import dataclass
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
ORGANIZATION_REPLAY_EVENT_LIMIT = 500


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

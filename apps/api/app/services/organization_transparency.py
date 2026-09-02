from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID

from sqlmodel import Session, select

from app.core.organization_constitution import (
    OrganizationActivityClass as ConstitutionalActivityClass,
    transparency_rule,
)
from app.models.domain import OrganizationActivity


class TransparencyDataError(RuntimeError):
    """Raised when durable transparency data violates the V1.3 trace contract."""


class TransparencyRecordRole(StrEnum):
    GOVERNANCE = "GOVERNANCE"
    ORGANIZATION_EFFECT = "ORGANIZATION_EFFECT"
    SUPPORTING = "SUPPORTING"


@dataclass(frozen=True, slots=True)
class TransparencyActivityRecord:
    activity_id: UUID
    tenant_key: str
    activity_key: str
    activity_type: str
    role: TransparencyRecordRole
    physical_activity_class: str
    constitutional_activity_class: ConstitutionalActivityClass | None
    board_inspectable: bool
    requires_durable_record: bool | None
    requires_full_lineage: bool | None
    may_compact_after_policy_window: bool | None
    actor_type: str
    actor_id: str
    department: str | None
    position_key: str | None
    authority_level: str | None
    source_object_type: str
    source_object_id: str
    source_object_version: str | None
    work_item_id: UUID | None
    correlation_key: str | None
    trace_id: str | None
    causation_activity_id: UUID | None
    supersedes_activity_id: UUID | None
    occurred_at: datetime
    title: str
    summary: str
    payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class GovernedActionTrace:
    tenant_key: str
    trace_id: str
    governance: TransparencyActivityRecord
    records: tuple[TransparencyActivityRecord, ...]

    @property
    def organization_effects(self) -> tuple[TransparencyActivityRecord, ...]:
        return tuple(
            record
            for record in self.records
            if record.role is TransparencyRecordRole.ORGANIZATION_EFFECT
        )

    @property
    def board_inspectable(self) -> bool:
        return all(record.board_inspectable for record in self.records)


def _payload(activity: OrganizationActivity) -> dict[str, Any]:
    try:
        value = json.loads(activity.payload_json or "{}")
    except json.JSONDecodeError as exc:
        raise TransparencyDataError(
            f"activity {activity.id} has invalid transparency payload JSON"
        ) from exc
    if not isinstance(value, dict):
        raise TransparencyDataError(
            f"activity {activity.id} transparency payload must be an object"
        )
    return value


def _constitutional_class(
    activity: OrganizationActivity,
    payload: Mapping[str, Any],
) -> ConstitutionalActivityClass | None:
    raw = payload.get("constitutional_activity_class")
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise TransparencyDataError(
            f"activity {activity.id} has non-string constitutional activity class"
        )
    try:
        return ConstitutionalActivityClass(raw)
    except ValueError as exc:
        raise TransparencyDataError(
            f"activity {activity.id} has unsupported constitutional activity class {raw!r}"
        ) from exc


def _trace_id(
    activity: OrganizationActivity,
    payload: Mapping[str, Any],
) -> str | None:
    raw = payload.get("trace_id")
    if raw is not None and not isinstance(raw, str):
        raise TransparencyDataError(f"activity {activity.id} has invalid trace_id")
    if activity.activity_key.startswith("governance:") and raw is not None:
        if activity.correlation_key is None:
            raise TransparencyDataError(
                f"governance activity {activity.id} is missing its correlation key"
            )
        if activity.correlation_key != raw:
            raise TransparencyDataError(
                f"governance activity {activity.id} trace_id/correlation mismatch"
            )
    return raw or activity.correlation_key


def _record_role(activity: OrganizationActivity) -> TransparencyRecordRole:
    if activity.activity_key.startswith("governance:"):
        return TransparencyRecordRole.GOVERNANCE
    if activity.work_item_id is not None or activity.activity_class.value in {
        "domain",
        "work",
        "decision",
        "blocker",
        "human_action",
        "contribution",
    }:
        return TransparencyRecordRole.ORGANIZATION_EFFECT
    return TransparencyRecordRole.SUPPORTING


def transparency_activity_record(activity: OrganizationActivity) -> TransparencyActivityRecord:
    """Project one durable Activity into the V1.3 Board-transparency contract.

    Existing pre-V1.3 Activities remain Board-inspectable but are not silently assigned
    a constitutional retention/lineage class. Governance Activities emitted by the
    V1.3 kernel carry that class explicitly in their durable payload.
    """

    payload = _payload(activity)
    constitutional_class = _constitutional_class(activity, payload)
    rule = transparency_rule(constitutional_class) if constitutional_class is not None else None

    return TransparencyActivityRecord(
        activity_id=activity.id,
        tenant_key=activity.tenant_key,
        activity_key=activity.activity_key,
        activity_type=activity.activity_type,
        role=_record_role(activity),
        physical_activity_class=activity.activity_class.value,
        constitutional_activity_class=constitutional_class,
        board_inspectable=True if rule is None else rule.board_inspectable,
        requires_durable_record=None if rule is None else rule.requires_durable_record,
        requires_full_lineage=None if rule is None else rule.requires_full_lineage,
        may_compact_after_policy_window=(
            None if rule is None else rule.may_compact_after_policy_window
        ),
        actor_type=activity.actor_type.value,
        actor_id=activity.actor_id,
        department=activity.department,
        position_key=activity.position_key,
        authority_level=activity.authority_level,
        source_object_type=activity.source_object_type,
        source_object_id=activity.source_object_id,
        source_object_version=activity.source_object_version,
        work_item_id=activity.work_item_id,
        correlation_key=activity.correlation_key,
        trace_id=_trace_id(activity, payload),
        causation_activity_id=activity.causation_activity_id,
        supersedes_activity_id=activity.supersedes_activity_id,
        occurred_at=activity.occurred_at,
        title=activity.title,
        summary=activity.summary,
        payload=MappingProxyType(dict(payload)),
    )


def activities_for_trace(
    session: Session,
    *,
    tenant_key: str,
    trace_id: UUID | str,
) -> tuple[TransparencyActivityRecord, ...]:
    """Return tenant-scoped durable Activities correlated to one governed trace."""

    key = str(trace_id)
    activities = session.exec(
        select(OrganizationActivity)
        .where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.correlation_key == key,
        )
        .order_by(
            OrganizationActivity.occurred_at,
            OrganizationActivity.created_at,
            OrganizationActivity.stream_sequence,
        )
    ).all()
    return tuple(transparency_activity_record(activity) for activity in activities)


def activities_for_work_item(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
) -> tuple[TransparencyActivityRecord, ...]:
    """Return the durable Board-inspectable Activity history for one WorkItem."""

    activities = session.exec(
        select(OrganizationActivity)
        .where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.work_item_id == work_item_id,
        )
        .order_by(
            OrganizationActivity.occurred_at,
            OrganizationActivity.created_at,
            OrganizationActivity.stream_sequence,
        )
    ).all()
    return tuple(transparency_activity_record(activity) for activity in activities)


def governed_action_trace(
    session: Session,
    *,
    tenant_key: str,
    trace_id: UUID | str,
) -> GovernedActionTrace | None:
    """Reconstruct one governed action from its durable correlated Activities.

    C.1 requires exactly one governance Activity for a governed trace. A trace with
    multiple governance roots fails closed instead of returning an ambiguous lineage.
    """

    key = str(trace_id)
    records = activities_for_trace(session, tenant_key=tenant_key, trace_id=key)
    if not records:
        return None
    governance = tuple(
        record for record in records if record.role is TransparencyRecordRole.GOVERNANCE
    )
    if len(governance) != 1:
        raise TransparencyDataError(
            f"governed trace {key!r} requires exactly one governance Activity"
        )
    root = governance[0]
    if root.trace_id != key:
        raise TransparencyDataError(
            f"governance Activity for trace {key!r} does not carry the requested trace identity"
        )
    return GovernedActionTrace(
        tenant_key=tenant_key,
        trace_id=key,
        governance=root,
        records=records,
    )

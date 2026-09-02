from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationPosition,
    OrganizationalWorkItem,
)
from app.services.organization_activity import append_activity
from app.services.organization_command import (
    DependencyConflict,
    OrganizationCommandContext,
    require_mutation_role,
    tenant_record,
)


CONVERSATION_OPENED_ACTIVITY_TYPE = "organization.conversation.opened.v1"
CONVERSATION_CLOSED_ACTIVITY_TYPE = "organization.conversation.closed.v1"
CONVERSATION_SOURCE_TYPE = "organization_conversation"
CONVERSATION_SOURCE_VERSION = "v1"


def conversation_activity_key(conversation_id: str, lifecycle: str) -> str:
    return f"organization:conversation:{conversation_id}:{lifecycle}:v1"


def conversation_stream_key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}"


def is_reserved_conversation_activity(
    *,
    activity_key: str,
    stream_key: str,
    activity_type: str,
    source_object_type: str,
) -> bool:
    return (
        activity_type
        in {CONVERSATION_OPENED_ACTIVITY_TYPE, CONVERSATION_CLOSED_ACTIVITY_TYPE}
        or source_object_type == CONVERSATION_SOURCE_TYPE
        or activity_key.startswith("organization:conversation:")
        or stream_key.startswith("conversation:")
    )


def _normalized_conversation_id(conversation_id: str) -> str:
    value = conversation_id.strip()
    if not value or len(value) > 255:
        raise DependencyConflict("conversation identity is invalid")
    return value


def _normalized_participants(participant_position_keys: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(
        dict.fromkeys(value.strip() for value in participant_position_keys if value.strip())
    )
    if len(normalized) < 2:
        raise DependencyConflict("conversation requires at least two unique active positions")
    return normalized


def _existing_activity(
    session: Session,
    *,
    tenant_key: str,
    activity_key: str,
) -> OrganizationActivity | None:
    return session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.activity_key == activity_key,
        )
    ).first()


def _append_opened_activity(
    session: Session,
    context: OrganizationCommandContext,
    *,
    conversation_id: str,
    work_item_id: UUID,
    participant_position_keys: tuple[str, ...],
    summary: str,
    occurred_at: datetime,
    causation_activity_id: UUID | None,
) -> OrganizationActivity:
    return append_activity(
        session,
        context,
        activity_key=conversation_activity_key(conversation_id, "opened"),
        stream_key=conversation_stream_key(conversation_id),
        activity_class=OrganizationActivityClass.work,
        activity_type=CONVERSATION_OPENED_ACTIVITY_TYPE,
        title="Organization conversation opened",
        summary=summary,
        source_object_type=CONVERSATION_SOURCE_TYPE,
        source_object_id=conversation_id,
        source_object_version=CONVERSATION_SOURCE_VERSION,
        occurred_at=occurred_at,
        work_item_id=work_item_id,
        causation_activity_id=causation_activity_id,
        payload={
            "conversation_id": conversation_id,
            "participant_position_keys": participant_position_keys,
            "work_item_id": work_item_id,
            "lifecycle_status": "open",
            "authority_effect": "none",
            "transcript_persisted": False,
            "opened_at": occurred_at,
        },
    )


def open_conversation(
    session: Session,
    context: OrganizationCommandContext,
    *,
    conversation_id: str,
    work_item_id: UUID,
    participant_position_keys: tuple[str, ...],
    summary: str,
    occurred_at: datetime,
    causation_activity_id: UUID | None = None,
) -> OrganizationActivity:
    """Append one canonical collaboration lifecycle start without creating authority or chat truth."""

    # Authorization must happen before tenant or conversation lookup so callers cannot
    # use command errors as an existence oracle.
    require_mutation_role(context)
    conversation_id = _normalized_conversation_id(conversation_id)
    participants = _normalized_participants(participant_position_keys)
    existing = _existing_activity(
        session,
        tenant_key=context.tenant_key,
        activity_key=conversation_activity_key(conversation_id, "opened"),
    )
    if existing is not None:
        return _append_opened_activity(
            session,
            context,
            conversation_id=conversation_id,
            work_item_id=work_item_id,
            participant_position_keys=participants,
            summary=summary,
            occurred_at=occurred_at,
            causation_activity_id=causation_activity_id,
        )

    work = tenant_record(
        session,
        OrganizationalWorkItem,
        work_item_id,
        context.tenant_key,
        label="conversation work item",
    )
    if work.assigned_position_key not in participants:
        raise DependencyConflict(
            "conversation participants must include the position assigned to the linked work item"
        )
    active_positions = {
        row.position_key
        for row in session.exec(
            select(OrganizationPosition).where(
                OrganizationPosition.position_key.in_(participants),
                OrganizationPosition.status == "active",
            )
        ).all()
    }
    missing = [position_key for position_key in participants if position_key not in active_positions]
    if missing:
        raise DependencyConflict(
            "conversation participant position is not active: " + ", ".join(missing)
        )
    return _append_opened_activity(
        session,
        context,
        conversation_id=conversation_id,
        work_item_id=work_item_id,
        participant_position_keys=participants,
        summary=summary,
        occurred_at=occurred_at,
        causation_activity_id=causation_activity_id,
    )


def close_conversation(
    session: Session,
    context: OrganizationCommandContext,
    *,
    conversation_id: str,
    summary: str,
    occurred_at: datetime,
) -> OrganizationActivity:
    """Append the terminal lifecycle Activity while preserving the opening lineage."""

    require_mutation_role(context)
    conversation_id = _normalized_conversation_id(conversation_id)
    opened = _existing_activity(
        session,
        tenant_key=context.tenant_key,
        activity_key=conversation_activity_key(conversation_id, "opened"),
    )
    if opened is None:
        raise DependencyConflict("conversation cannot close before its canonical opening activity")
    try:
        opened_payload = json.loads(opened.payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict("conversation opening Activity is invalid") from exc
    if (
        not isinstance(opened_payload, dict)
        or opened.activity_type != CONVERSATION_OPENED_ACTIVITY_TYPE
        or opened.source_object_type != CONVERSATION_SOURCE_TYPE
        or opened.source_object_id != conversation_id
        or opened.source_object_version != CONVERSATION_SOURCE_VERSION
        or opened.work_item_id is None
        or opened_payload.get("conversation_id") != conversation_id
        or opened_payload.get("lifecycle_status") != "open"
        or opened_payload.get("authority_effect") != "none"
        or opened_payload.get("transcript_persisted") is not False
    ):
        raise DependencyConflict("conversation opening Activity is inconsistent")
    return append_activity(
        session,
        context,
        activity_key=conversation_activity_key(conversation_id, "closed"),
        stream_key=conversation_stream_key(conversation_id),
        activity_class=OrganizationActivityClass.work,
        activity_type=CONVERSATION_CLOSED_ACTIVITY_TYPE,
        title="Organization conversation closed",
        summary=summary,
        source_object_type=CONVERSATION_SOURCE_TYPE,
        source_object_id=conversation_id,
        source_object_version=CONVERSATION_SOURCE_VERSION,
        occurred_at=occurred_at,
        work_item_id=opened.work_item_id,
        causation_activity_id=opened.id,
        payload={
            "conversation_id": conversation_id,
            "work_item_id": opened.work_item_id,
            "lifecycle_status": "closed",
            "authority_effect": "none",
            "transcript_persisted": False,
            "opened_activity_id": opened.id,
            "closed_at": occurred_at,
        },
    )

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.models.domain import (
    OrganizationActivity,
    OrganizationActorType,
    OrganizationPosition,
)
from app.services.organization_command import (
    AuthorityDenied,
    DependencyConflict,
    IdempotencyConflict,
    OrganizationCommandContext,
)
from app.services.organization_conversation import (
    CONVERSATION_CLOSED_ACTIVITY_TYPE,
    CONVERSATION_OPENED_ACTIVITY_TYPE,
    close_conversation,
    open_conversation,
)
from app.services.organization_work import create_work_item


NOW = datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc)


def _context(*, role: str = "admin") -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="m5-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="m5-owner",
        role=role,
        department="operations",
        position_key="board" if role == "admin" else "reader",
        authority_level="L4" if role == "admin" else "L0",
        request_id="m5-conversation-test",
    )


def _positions(session: Session) -> None:
    session.add_all(
        [
            OrganizationPosition(
                position_key="m5_lead",
                title="M.5 Lead",
                department="operations",
                authority_level="L2",
            ),
            OrganizationPosition(
                position_key="m5_specialist",
                title="M.5 Specialist",
                department="operations",
                reports_to_position_key="m5_lead",
                authority_level="L1",
            ),
            OrganizationPosition(
                position_key="m5_observer",
                title="M.5 Observer",
                department="operations",
                authority_level="L1",
            ),
            OrganizationPosition(
                position_key="m5_inactive",
                title="M.5 Inactive",
                department="operations",
                authority_level="L1",
                status="suspended",
            ),
        ]
    )
    session.commit()


def _work(session: Session):
    return create_work_item(
        session,
        _context(),
        idempotency_key="m5-conversation-work",
        title="Coordinate pathway evidence",
        objective="Prove canonical collaboration without transcript or authority claims.",
        department="operations",
        authority_level="L2",
        assigned_position_key="m5_lead",
    )


def test_conversation_lifecycle_is_immutable_idempotent_and_non_authorizing(
    db_session: Session,
) -> None:
    _positions(db_session)
    work = _work(db_session)
    opened = open_conversation(
        db_session,
        _context(),
        conversation_id="m5-pathway-evidence",
        work_item_id=work.id,
        participant_position_keys=("m5_lead", "m5_specialist", "m5_specialist"),
        summary="Coordinate pathway evidence before owner synthesis.",
        occurred_at=NOW,
    )
    replay = open_conversation(
        db_session,
        _context(),
        conversation_id="m5-pathway-evidence",
        work_item_id=work.id,
        participant_position_keys=("m5_lead", "m5_specialist"),
        summary="Coordinate pathway evidence before owner synthesis.",
        occurred_at=NOW,
    )
    assert replay.id == opened.id
    assert opened.activity_type == CONVERSATION_OPENED_ACTIVITY_TYPE
    opened_payload = json.loads(opened.payload_json)
    assert opened_payload["participant_position_keys"] == ["m5_lead", "m5_specialist"]
    assert opened_payload["authority_effect"] == "none"
    assert opened_payload["transcript_persisted"] is False

    with pytest.raises(IdempotencyConflict):
        open_conversation(
            db_session,
            _context(),
            conversation_id="m5-pathway-evidence",
            work_item_id=work.id,
            participant_position_keys=("m5_lead", "m5_specialist"),
            summary="Conflicting reuse of the same conversation identity.",
            occurred_at=NOW,
        )

    closed = close_conversation(
        db_session,
        _context(),
        conversation_id="m5-pathway-evidence",
        summary="Coordination completed; no transcript was retained.",
        occurred_at=NOW + timedelta(minutes=12),
    )
    close_replay = close_conversation(
        db_session,
        _context(),
        conversation_id="m5-pathway-evidence",
        summary="Coordination completed; no transcript was retained.",
        occurred_at=NOW + timedelta(minutes=12),
    )
    assert close_replay.id == closed.id
    assert closed.activity_type == CONVERSATION_CLOSED_ACTIVITY_TYPE
    assert closed.causation_activity_id == opened.id
    closed_payload = json.loads(closed.payload_json)
    assert closed_payload["opened_activity_id"] == str(opened.id)
    assert closed_payload["authority_effect"] == "none"
    assert closed_payload["transcript_persisted"] is False
    assert db_session.exec(
        select(func.count()).select_from(OrganizationActivity).where(
            OrganizationActivity.activity_type.in_(
                (CONVERSATION_OPENED_ACTIVITY_TYPE, CONVERSATION_CLOSED_ACTIVITY_TYPE)
            )
        )
    ).one() == 2


def test_conversation_rejects_invalid_participants_and_authorizes_before_lookup(
    db_session: Session,
) -> None:
    _positions(db_session)
    work = _work(db_session)
    for participants in (
        ("m5_lead",),
        ("m5_specialist", "m5_observer"),
        ("m5_lead", "m5_inactive"),
    ):
        with pytest.raises(DependencyConflict):
            open_conversation(
                db_session,
                _context(),
                conversation_id=f"invalid-{participants[-1]}",
                work_item_id=work.id,
                participant_position_keys=participants,
                summary="This invalid conversation must not be persisted.",
                occurred_at=NOW,
            )

    with pytest.raises(AuthorityDenied):
        open_conversation(
            db_session,
            _context(role="read_only"),
            conversation_id="unauthorized-probe",
            work_item_id=uuid4(),
            participant_position_keys=("m5_lead", "m5_specialist"),
            summary="The caller must be rejected before the missing WorkItem is looked up.",
            occurred_at=NOW,
        )


def test_conversation_http_commands_reserve_lifecycle_activity_semantics(
    client: TestClient,
    db_session: Session,
) -> None:
    _positions(db_session)
    work = _work(db_session)
    payload = {
        "conversation_id": "m5-api-conversation",
        "work_item_id": str(work.id),
        "participant_position_keys": ["m5_lead", "m5_specialist"],
        "summary": "Coordinate the linked governed WorkItem.",
        "occurred_at": NOW.isoformat(),
    }
    opened = client.post("/api/v1/organization/conversations/open", json=payload)
    assert opened.status_code == 201, opened.text
    assert opened.json()["activity_type"] == CONVERSATION_OPENED_ACTIVITY_TYPE
    replay = client.post("/api/v1/organization/conversations/open", json=payload)
    assert replay.status_code == 201
    assert replay.json()["id"] == opened.json()["id"]

    forged = client.post(
        "/api/v1/organization/activities",
        json={
            "activity_key": "forged-conversation",
            "stream_key": "forged-stream",
            "activity_class": "work",
            "activity_type": CONVERSATION_OPENED_ACTIVITY_TYPE,
            "title": "Forged conversation",
            "summary": "Must be rejected by the generic Activity endpoint.",
            "source_object_type": "test",
            "source_object_id": "forged",
            "occurred_at": NOW.isoformat(),
            "payload": {},
        },
    )
    assert forged.status_code == 422

    closed = client.post(
        "/api/v1/organization/conversations/m5-api-conversation/close",
        json={
            "summary": "The bounded coordination lifecycle is closed.",
            "occurred_at": (NOW + timedelta(minutes=3)).isoformat(),
        },
    )
    assert closed.status_code == 201, closed.text
    assert closed.json()["activity_type"] == CONVERSATION_CLOSED_ACTIVITY_TYPE

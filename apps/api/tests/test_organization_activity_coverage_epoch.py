from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func
from sqlmodel import Session, create_engine, select

from app.models.domain import (
    AuditLog,
    OrganizationActivity,
    OrganizationActivityStream,
    OrganizationContribution,
    OrganizationalWorkItem,
)
from app.services.organization_activity import (
    ACTIVITY_COVERAGE_ACTIVITY_KEY,
    ACTIVITY_COVERAGE_ACTIVITY_TYPE,
    ACTIVITY_COVERAGE_SOURCE_TYPE,
    ACTIVITY_COVERAGE_STREAM_KEY,
    activity_coverage_epoch,
    establish_activity_coverage_epoch,
)
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_observatory import observatory_summary


BASE = "/api/v1/organization"
OBS = f"{BASE}/observatory"


def _headers(role: str, user: str = "e3d-admin") -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def test_activity_coverage_epoch_requires_admin_human_and_activates_observatory(
    raw_client,
    db_session: Session,
) -> None:
    before = raw_client.get(f"{OBS}/summary", headers=_headers("read_only", "e3d-reader"))
    assert before.status_code == 200, before.text
    before_coverage = before.json()["coverage"]
    assert before_coverage["activity_history_basis"] == "partial_activity_coverage"
    assert before_coverage["activity_history_established"] is False
    assert before_coverage["activity_history_coverage_start"] is None

    operator = raw_client.post(
        f"{BASE}/activity-coverage/establish",
        headers=_headers("operator", "e3d-operator"),
        json={"reason": "Operator must not establish the coverage epoch."},
    )
    assert operator.status_code == 403, operator.text

    contributions_before = db_session.exec(
        select(func.count()).select_from(OrganizationContribution)
    ).one()
    audits_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()

    established = raw_client.post(
        f"{BASE}/activity-coverage/establish",
        headers=_headers("admin"),
        json={"reason": "E3B/E3C material-writer reconciliation passed cross-database acceptance."},
    )
    assert established.status_code == 200, established.text
    marker = established.json()
    assert marker["activity_key"] == ACTIVITY_COVERAGE_ACTIVITY_KEY
    assert marker["activity_type"] == ACTIVITY_COVERAGE_ACTIVITY_TYPE
    assert marker["activity_class"] == "operational"
    assert marker["source_object_type"] == ACTIVITY_COVERAGE_SOURCE_TYPE
    assert marker["source_object_id"] == "default"
    assert marker["actor_type"] == "human"
    assert marker["actor_id"] == "e3d-admin"

    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == contributions_before
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before + 1

    after = raw_client.get(f"{OBS}/summary", headers=_headers("read_only", "e3d-reader"))
    assert after.status_code == 200, after.text
    coverage = after.json()["coverage"]
    assert coverage["activity_history_basis"] == "explicit_activity_coverage_epoch"
    assert coverage["activity_history_established"] is True
    assert coverage["activity_history_coverage_start"] == marker["occurred_at"]
    assert any("pre-epoch history remains partial" in warning for warning in after.json()["warnings"])

    departments = raw_client.get(f"{OBS}/departments", headers=_headers("read_only", "e3d-reader"))
    assert departments.status_code == 200, departments.text
    assert departments.json()["coverage"] == coverage

    activities_before_replay = db_session.exec(
        select(func.count()).select_from(OrganizationActivity)
    ).one()
    audits_before_replay = db_session.exec(select(func.count()).select_from(AuditLog)).one()
    replay = raw_client.post(
        f"{BASE}/activity-coverage/establish",
        headers=_headers("admin"),
        json={"reason": "A later replay reason must not create a second epoch."},
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["id"] == marker["id"]
    assert replay.json()["occurred_at"] == marker["occurred_at"]
    assert db_session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activities_before_replay
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audits_before_replay


def test_activity_coverage_epoch_never_backfills_pre_epoch_rows_or_becomes_contribution(
    raw_client,
    db_session: Session,
) -> None:
    legacy_work = OrganizationalWorkItem(
        idempotency_key=f"e3d-pre-epoch-{uuid4().hex}",
        title="Pre-epoch legacy work",
        objective="Prove E3D does not synthesize semantic history.",
        department="Operations",
        authority_level="L2",
        assigned_position_key="operations_manager",
        status="queued",
        created_by="pre-epoch-fixture",
    )
    db_session.add(legacy_work)
    db_session.commit()
    db_session.refresh(legacy_work)

    assert db_session.exec(
        select(func.count()).select_from(OrganizationActivity).where(
            OrganizationActivity.source_object_type == "organizational_work_item",
            OrganizationActivity.source_object_id == str(legacy_work.id),
        )
    ).one() == 0

    established = raw_client.post(
        f"{BASE}/activity-coverage/establish",
        headers=_headers("admin"),
        json={"reason": "Establish coverage without reconstructing old work history."},
    )
    assert established.status_code == 200, established.text

    assert db_session.exec(
        select(func.count()).select_from(OrganizationActivity).where(
            OrganizationActivity.source_object_type == "organizational_work_item",
            OrganizationActivity.source_object_id == str(legacy_work.id),
        )
    ).one() == 0
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == 0
    assert db_session.exec(
        select(func.count()).select_from(OrganizationActivity).where(
            OrganizationActivity.activity_key == ACTIVITY_COVERAGE_ACTIVITY_KEY
        )
    ).one() == 1


def test_reserved_coverage_marker_cannot_be_forged_through_generic_activity_api(raw_client) -> None:
    now = datetime.now(timezone.utc).isoformat()
    forged_key = raw_client.post(
        f"{BASE}/activities",
        headers=_headers("admin"),
        json={
            "activity_key": ACTIVITY_COVERAGE_ACTIVITY_KEY,
            "stream_key": "forged-coverage-stream",
            "activity_class": "operational",
            "activity_type": "forged.coverage.marker",
            "title": "Forged marker",
            "summary": "The generic Activity API must not activate coverage.",
            "source_object_type": "api_test",
            "source_object_id": "forged",
            "occurred_at": now,
        },
    )
    assert forged_key.status_code == 422, forged_key.text

    forged_stream = raw_client.post(
        f"{BASE}/activities",
        headers=_headers("admin"),
        json={
            "activity_key": "forged-coverage-stream-key",
            "stream_key": ACTIVITY_COVERAGE_STREAM_KEY,
            "activity_class": "operational",
            "activity_type": "forged.coverage.stream",
            "title": "Forged stream marker",
            "summary": "The reserved stream must use the governed command.",
            "source_object_type": "api_test",
            "source_object_id": "forged",
            "occurred_at": now,
        },
    )
    assert forged_stream.status_code == 422, forged_stream.text

    forged_type = raw_client.post(
        f"{BASE}/activities",
        headers=_headers("admin"),
        json={
            "activity_key": "forged-coverage-key",
            "stream_key": "forged-coverage-stream",
            "activity_class": "operational",
            "activity_type": ACTIVITY_COVERAGE_ACTIVITY_TYPE,
            "title": "Forged marker",
            "summary": "The reserved activity type must use the governed command.",
            "source_object_type": "api_test",
            "source_object_id": "forged",
            "occurred_at": now,
        },
    )
    assert forged_type.status_code == 422, forged_type.text

    summary = raw_client.get(f"{OBS}/summary", headers=_headers("read_only", "e3d-reader"))
    assert summary.status_code == 200, summary.text
    assert summary.json()["coverage"]["activity_history_established"] is False


def test_postgresql_activity_coverage_epoch_is_atomic_idempotent_and_outer_rollback_leaves_no_residue() -> None:
    database_url = os.getenv("ORGANIZATION_POSTGRES_TEST_URL")
    if not database_url:
        pytest.skip("ORGANIZATION_POSTGRES_TEST_URL is not configured")

    engine = create_engine(database_url)
    connection = engine.connect()
    outer = connection.begin()
    marker_id = None
    try:
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            context = OrganizationCommandContext(
                tenant_key="default",
                actor_id="e3d-pg-admin",
                actor_type="human",
                authenticated_user_id="e3d-pg-admin",
                role="admin",
                department="executive",
                position_key="board",
                authority_level="L4",
            )
            contributions_before = session.exec(
                select(func.count()).select_from(OrganizationContribution)
            ).one()
            assert activity_coverage_epoch(session, "default") is None

            marker = establish_activity_coverage_epoch(
                session,
                context,
                reason="Cross-database E3D coverage activation acceptance.",
            )
            marker_id = marker.id
            summary = observatory_summary(session, "default")
            assert summary["coverage"]["activity_history_established"] is True
            assert summary["coverage"]["activity_history_basis"] == "explicit_activity_coverage_epoch"
            assert summary["coverage"]["activity_history_coverage_start"] == marker.occurred_at
            assert session.exec(select(func.count()).select_from(OrganizationContribution)).one() == contributions_before

            replay = establish_activity_coverage_epoch(
                session,
                context,
                reason="Replay remains the same immutable epoch.",
            )
            assert replay.id == marker.id
            assert replay.occurred_at == marker.occurred_at
    finally:
        outer.rollback()
        connection.close()

    try:
        with Session(engine) as verification:
            assert marker_id is not None
            assert verification.get(OrganizationActivity, marker_id) is None
            assert verification.exec(
                select(func.count()).select_from(OrganizationActivity).where(
                    OrganizationActivity.activity_key == ACTIVITY_COVERAGE_ACTIVITY_KEY
                )
            ).one() == 0
            assert verification.exec(
                select(func.count()).select_from(OrganizationActivityStream).where(
                    OrganizationActivityStream.stream_key == ACTIVITY_COVERAGE_STREAM_KEY
                )
            ).one() == 0
    finally:
        engine.dispose()

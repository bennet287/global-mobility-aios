from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session

from app.core.db import register_models
from app.models.domain import OrganizationActivityClass, OrganizationActorType, now_utc
from app.services.organization_activity import stage_activity
from app.services.organization_command import (
    ConcurrentWriteConflict,
    DependencyConflict,
    OrganizationCommandContext,
)


def test_activity_stream_creation_race_is_a_specific_retryable_conflict() -> None:
    session = MagicMock(spec=Session)
    session.exec.return_value.first.return_value = None
    session.get_bind.return_value.dialect.name = "sqlite"
    session.flush.side_effect = IntegrityError(
        "INSERT INTO organization_activity_streams",
        {},
        Exception("unique activity stream"),
    )
    context = OrganizationCommandContext(
        tenant_key="default",
        actor_id="pytest-operator",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="pytest-operator",
        role="operator",
    )

    with pytest.raises(
        ConcurrentWriteConflict,
        match="activity stream was created concurrently; retry the source transaction",
    ):
        stage_activity(
            session,
            context,
            activity_key="pytest:activity:concurrency",
            stream_key="pytest:stream:concurrency",
            activity_class=OrganizationActivityClass.operational,
            activity_type="pytest.concurrent_activity.v1",
            title="Concurrent activity",
            summary="Exercise the retryable stream-creation classification.",
            source_object_type="pytest",
            source_object_id="concurrency",
            occurred_at=now_utc(),
        )

    assert issubclass(ConcurrentWriteConflict, DependencyConflict)
    session.rollback.assert_not_called()


def test_organizational_action_output_metadata_matches_migration_uniqueness() -> None:
    register_models()
    table = SQLModel.metadata.tables["organizational_action_outputs"]
    matching = [
        constraint
        for constraint in table.constraints
        if constraint.name == "uq_organizational_action_output_key"
    ]

    assert len(matching) == 1
    assert tuple(column.name for column in matching[0].columns) == ("output_key",)
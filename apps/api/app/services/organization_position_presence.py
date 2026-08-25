from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.services.organization_command import DependencyConflict


ORGANIZATION_POSITION_PRESENCE_CONTRACT_VERSION = "organization-position-presence.v1"
PRESENCE_BASIS_EXECUTION_ATTEMPT = "durable_execution_attempt"
PRESENCE_BASIS_NONE = "none"
HEARTBEAT_NOT_ESTABLISHED = "not_established"


@dataclass(frozen=True, slots=True)
class OrganizationPositionPresenceSnapshot:
    contract_version: str
    position_key: str
    work_item_id: UUID
    presence_state: str
    presence_basis: str
    observed_at: datetime | None
    execution_attempt_id: UUID | None
    execution_attempt_status: str | None
    heartbeat_state: str
    heartbeat_observed_at: datetime | None
    heartbeat_fresh_until: datetime | None
    authority_effect: bool


def organization_position_presence_snapshot(
    session: Session,
    *,
    work_item_id: UUID,
) -> OrganizationPositionPresenceSnapshot:
    """Project bounded position presence from durable AIOS execution state.

    This contract deliberately does not infer an online/offline heartbeat. A currently
    running durable OrganizationExecutionAttempt establishes only that AIOS has recorded
    the position as executing work. Heartbeat freshness remains explicitly unestablished
    until a real heartbeat substrate is implemented.
    """

    work_item = session.get(OrganizationalWorkItem, work_item_id)
    if work_item is None:
        raise DependencyConflict("presence projection WorkItem was not found")

    attempts = list(
        session.exec(
            select(OrganizationExecutionAttempt)
            .where(OrganizationExecutionAttempt.work_item_id == work_item_id)
            .order_by(
                OrganizationExecutionAttempt.attempt_number.desc(),
                OrganizationExecutionAttempt.started_at.desc(),
            )
        ).all()
    )
    running_attempts = [attempt for attempt in attempts if attempt.status == "running"]
    if len(running_attempts) > 1:
        raise DependencyConflict("presence projection found multiple running execution attempts")

    if running_attempts:
        if work_item.status != "running":
            raise DependencyConflict(
                "presence projection found a running execution attempt for a non-running WorkItem"
            )
        attempt = running_attempts[0]
        return OrganizationPositionPresenceSnapshot(
            contract_version=ORGANIZATION_POSITION_PRESENCE_CONTRACT_VERSION,
            position_key=work_item.assigned_position_key,
            work_item_id=work_item.id,
            presence_state="executing",
            presence_basis=PRESENCE_BASIS_EXECUTION_ATTEMPT,
            observed_at=attempt.started_at,
            execution_attempt_id=attempt.id,
            execution_attempt_status=attempt.status,
            heartbeat_state=HEARTBEAT_NOT_ESTABLISHED,
            heartbeat_observed_at=None,
            heartbeat_fresh_until=None,
            authority_effect=False,
        )

    if work_item.status == "running":
        raise DependencyConflict(
            "presence projection found a running WorkItem without a running execution attempt"
        )

    if attempts:
        attempt = attempts[0]
        return OrganizationPositionPresenceSnapshot(
            contract_version=ORGANIZATION_POSITION_PRESENCE_CONTRACT_VERSION,
            position_key=work_item.assigned_position_key,
            work_item_id=work_item.id,
            presence_state="not_executing",
            presence_basis=PRESENCE_BASIS_EXECUTION_ATTEMPT,
            observed_at=attempt.completed_at or attempt.started_at,
            execution_attempt_id=attempt.id,
            execution_attempt_status=attempt.status,
            heartbeat_state=HEARTBEAT_NOT_ESTABLISHED,
            heartbeat_observed_at=None,
            heartbeat_fresh_until=None,
            authority_effect=False,
        )

    return OrganizationPositionPresenceSnapshot(
        contract_version=ORGANIZATION_POSITION_PRESENCE_CONTRACT_VERSION,
        position_key=work_item.assigned_position_key,
        work_item_id=work_item.id,
        presence_state="not_established",
        presence_basis=PRESENCE_BASIS_NONE,
        observed_at=None,
        execution_attempt_id=None,
        execution_attempt_status=None,
        heartbeat_state=HEARTBEAT_NOT_ESTABLISHED,
        heartbeat_observed_at=None,
        heartbeat_fresh_until=None,
        authority_effect=False,
    )

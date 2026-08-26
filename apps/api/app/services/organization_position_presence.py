from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.services.organization_command import DependencyConflict
from app.services.organization_execution_heartbeat import (
    HEARTBEAT_INACTIVE,
    HEARTBEAT_NOT_ESTABLISHED,
    heartbeat_freshness_state,
    latest_execution_heartbeat,
)


ORGANIZATION_POSITION_PRESENCE_CONTRACT_VERSION = "organization-position-presence.v2"
PRESENCE_BASIS_EXECUTION_ATTEMPT = "durable_execution_attempt"
PRESENCE_BASIS_NONE = "none"


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
    tenant_key: str,
    work_item_id: UUID,
    as_of: datetime | None = None,
) -> OrganizationPositionPresenceSnapshot:
    """Project execution presence and bounded checkpoint-lease freshness.

    Presence remains derived from durable OrganizationExecutionAttempt state. Heartbeat
    freshness is separate and comes only from durable AIOS worker checkpoints. A fresh
    checkpoint lease is not a claim that a human, provider, or model is continuously
    online; a stale lease is not an offline claim. Neither state has authority effect.
    """

    work_item = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first()
    if work_item is None:
        raise DependencyConflict("presence projection WorkItem was not found for the tenant")

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
        heartbeat = latest_execution_heartbeat(
            session,
            tenant_key=tenant_key,
            work_item_id=work_item.id,
            execution_attempt_id=attempt.id,
            position_key=work_item.assigned_position_key,
        )
        return OrganizationPositionPresenceSnapshot(
            contract_version=ORGANIZATION_POSITION_PRESENCE_CONTRACT_VERSION,
            position_key=work_item.assigned_position_key,
            work_item_id=work_item.id,
            presence_state="executing",
            presence_basis=PRESENCE_BASIS_EXECUTION_ATTEMPT,
            observed_at=attempt.started_at,
            execution_attempt_id=attempt.id,
            execution_attempt_status=attempt.status,
            heartbeat_state=heartbeat_freshness_state(heartbeat, as_of=as_of),
            heartbeat_observed_at=heartbeat.observed_at if heartbeat is not None else None,
            heartbeat_fresh_until=heartbeat.fresh_until if heartbeat is not None else None,
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
            heartbeat_state=HEARTBEAT_INACTIVE,
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

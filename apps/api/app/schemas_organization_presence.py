from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrganizationPresenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OrganizationPositionPresenceRead(OrganizationPresenceRead):
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


class AustriaOrganizationPresenceSnapshotRead(OrganizationPresenceRead):
    generated_at: datetime
    root_work_item_id: UUID
    positions: list[OrganizationPositionPresenceRead]
    heartbeat_capability_state: str


class AustriaOrganizationPresenceLatestRead(OrganizationPresenceRead):
    established: bool
    snapshot: AustriaOrganizationPresenceSnapshotRead | None

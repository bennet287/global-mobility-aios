from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


AutomationChannel = Literal["email", "messaging", "calendar", "crm"]
AutomationEventType = Literal[
    "case.created",
    "case.status_changed",
    "compliance.created",
    "compliance.status_changed",
    "task.status_changed",
]


class AutomationRuleCreate(BaseModel):
    corporate_account_id: UUID
    name: str = Field(min_length=3, max_length=120)
    event_type: AutomationEventType
    channels: list[AutomationChannel] = Field(min_length=1, max_length=4)
    destinations: dict[AutomationChannel, str] = Field(default_factory=dict)
    subject_template: str | None = Field(default=None, max_length=240)
    body_template: str | None = Field(default=None, max_length=4000)
    requires_human_approval: bool = True

    @field_validator("channels")
    @classmethod
    def unique_channels(cls, value: list[AutomationChannel]) -> list[AutomationChannel]:
        return list(dict.fromkeys(value))


class AutomationRuleStatusUpdate(BaseModel):
    status: Literal["active", "paused"]
    reason: str = Field(min_length=3, max_length=500)


class AutomationRuleRead(BaseModel):
    id: UUID
    corporate_account_id: UUID
    name: str
    event_type: str
    channels: list[AutomationChannel]
    destinations: dict[str, str]
    subject_template: str | None = None
    body_template: str | None = None
    requires_human_approval: bool
    status: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class AutomationEventIngest(BaseModel):
    corporate_account_id: UUID
    corporate_mobility_case_id: UUID
    event_type: AutomationEventType
    idempotency_key: str = Field(min_length=8, max_length=200)
    payload: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class AutomationEventRead(BaseModel):
    id: UUID
    idempotency_key: str
    corporate_account_id: UUID
    corporate_mobility_case_id: UUID | None = None
    event_type: str
    entity_type: str
    entity_id: str
    source: str
    payload: dict[str, object]
    status: str
    occurred_at: datetime
    created_by: str
    created_at: datetime
    delivery_count: int = 0


class AutomationDeliveryDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=3, max_length=500)


class AutomationDeliveryDispatch(BaseModel):
    provider_message_id: str = Field(min_length=2, max_length=240)


class AutomationDeliveryRead(BaseModel):
    id: UUID
    automation_event_id: UUID
    automation_rule_id: UUID
    connector_config_id: UUID | None = None
    channel: str
    destination: str | None = None
    subject: str | None = None
    payload: dict[str, object]
    status: str
    requires_human_approval: bool
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_reason: str | None = None
    dispatched_by: str | None = None
    dispatched_at: datetime | None = None
    provider_message_id: str | None = None
    attempt_count: int
    next_attempt_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime


ConnectorProviderType = Literal[
    "console",
    "smtp",
    "sendgrid",
    "twilio",
    "google_calendar",
    "salesforce",
    "hubspot",
    "webhook",
]


class ConnectorConfigCreate(BaseModel):
    corporate_account_id: UUID
    channel: AutomationChannel
    provider_type: ConnectorProviderType
    credentials: dict[str, str | int | bool | None] = Field(default_factory=dict)
    from_address: str | None = Field(default=None, max_length=240)
    sender_label: str | None = Field(default=None, max_length=120)


class ConnectorConfigStatusUpdate(BaseModel):
    status: Literal["active", "paused"]
    reason: str = Field(min_length=3, max_length=500)


class ConnectorConfigRead(BaseModel):
    id: UUID
    corporate_account_id: UUID
    channel: str
    provider_type: str
    credentials: dict[str, object]
    from_address: str | None = None
    sender_label: str | None = None
    status: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

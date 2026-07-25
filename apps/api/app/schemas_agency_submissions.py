from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


SubmissionChannel = Literal["online", "in_person", "courier", "agency"]
SubmissionStatus = Literal[
    "submitted",
    "acknowledged",
    "under_review",
    "decision_received",
    "returned",
]


class AgencySubmissionCreate(BaseModel):
    application_id: UUID
    authority_name: str = Field(min_length=1, max_length=240)
    submission_channel: SubmissionChannel
    submitted_at: datetime
    reference_number: str | None = Field(default=None, max_length=120)
    tracking_url: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)


class AgencySubmissionStatusUpdate(BaseModel):
    status: SubmissionStatus
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("status")
    @classmethod
    def _normalize_status(cls, value: str) -> str:
        return value.strip().lower()


class AgencySubmissionRead(BaseModel):
    id: UUID
    application_id: UUID
    authority_name: str
    submission_channel: str
    submitted_at: datetime
    reference_number: str | None = None
    tracking_url: str | None = None
    status: str
    notes: str | None = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


AppointmentType = Literal["biometric", "interview", "document_submission", "other"]
AppointmentStatus = Literal["scheduled", "completed", "cancelled", "no_show"]


class AuthorityAppointmentCreate(BaseModel):
    application_id: UUID
    appointment_type: AppointmentType
    authority_name: str = Field(min_length=1, max_length=240)
    location: str | None = Field(default=None, max_length=240)
    scheduled_at: datetime
    timezone: str | None = Field(default="UTC", max_length=64)
    reference_number: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class AuthorityAppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("status")
    @classmethod
    def _normalize_status(cls, value: str) -> str:
        return value.strip().lower()


class AuthorityAppointmentRead(BaseModel):
    id: UUID
    application_id: UUID
    appointment_type: str
    authority_name: str
    location: str | None = None
    scheduled_at: datetime
    timezone: str | None = None
    status: str
    reference_number: str | None = None
    notes: str | None = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

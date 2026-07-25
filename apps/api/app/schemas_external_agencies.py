from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


ExternalAgencyStatus = Literal["active", "suspended", "retired"]
AssignmentStatus = Literal["assigned", "in_progress", "handed_off", "completed", "cancelled"]


class ExternalAgencyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    country: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    contact_email: str | None = Field(default=None, max_length=240)
    contact_phone: str | None = Field(default=None, max_length=60)
    website: str | None = Field(default=None, max_length=500)
    sla_due_hours: int = Field(default=72, ge=1, le=8760)
    notes: str | None = Field(default=None, max_length=2000)


class ExternalAgencyStatusUpdate(BaseModel):
    status: ExternalAgencyStatus
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("status")
    @classmethod
    def _normalize_status(cls, value: str) -> str:
        return value.strip().lower()


class ExternalAgencyRead(BaseModel):
    id: UUID
    name: str
    country: str | None = None
    city: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    status: str
    sla_due_hours: int
    notes: str | None = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class ExternalAgencyAssignmentCreate(BaseModel):
    application_id: UUID
    external_agency_id: UUID
    agency_reference_number: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class ExternalAgencyAssignmentStatusUpdate(BaseModel):
    status: AssignmentStatus
    reason: str = Field(min_length=3, max_length=500)
    agency_reference_number: str | None = Field(default=None, max_length=120)

    @field_validator("status")
    @classmethod
    def _normalize_status(cls, value: str) -> str:
        return value.strip().lower()


class ExternalAgencyAssignmentRead(BaseModel):
    id: UUID
    application_id: UUID
    external_agency_id: UUID
    status: str
    agency_reference_number: str | None = None
    handoff_at: datetime | None = None
    completed_at: datetime | None = None
    sla_due_at: datetime | None = None
    sla_status: str
    sla_breached_at: datetime | None = None
    notes: str | None = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

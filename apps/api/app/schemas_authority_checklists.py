from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


ChecklistCategory = Literal["document", "fee", "form", "step"]
ChecklistItemStatus = Literal["pending", "completed", "not_applicable"]


class AuthorityChecklistTemplateCreate(BaseModel):
    authority_name: str = Field(min_length=1, max_length=240)
    country: str | None = Field(default=None, max_length=120)
    item_key: str = Field(min_length=1, max_length=120)
    item_label: str = Field(min_length=1, max_length=240)
    category: ChecklistCategory
    is_required: bool = True
    sort_order: int = Field(default=0, ge=0)


class AuthorityChecklistTemplateRead(BaseModel):
    id: UUID
    authority_name: str
    country: str | None = None
    item_key: str
    item_label: str
    category: str
    is_required: bool
    sort_order: int
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class ApplicationChecklistItemCreate(BaseModel):
    application_id: UUID
    authority_name: str = Field(min_length=1, max_length=240)
    item_key: str = Field(min_length=1, max_length=120)
    item_label: str = Field(min_length=1, max_length=240)
    category: ChecklistCategory
    is_required: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class ApplicationChecklistItemStatusUpdate(BaseModel):
    status: ChecklistItemStatus
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("status")
    @classmethod
    def _normalize_status(cls, value: str) -> str:
        return value.strip().lower()


class ApplicationChecklistItemRead(BaseModel):
    id: UUID
    application_id: UUID
    template_item_id: UUID | None = None
    authority_name: str
    item_key: str
    item_label: str
    category: str
    is_required: bool
    status: str
    notes: str | None = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class ApplyTemplateRequest(BaseModel):
    application_id: UUID
    authority_name: str = Field(min_length=1, max_length=240)

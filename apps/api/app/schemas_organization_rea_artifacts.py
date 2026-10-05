"""Bounded business inputs; these records never grant REA execution."""
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

Text = Annotated[StrictStr, Field(min_length=1, max_length=2000)]
Key = Annotated[StrictStr, Field(min_length=1, max_length=255)]
MAX_ARTIFACT_BYTES = 256 * 1024 * 1024


class ReaArtifactScope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_sha256: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    artifact_bytes: Annotated[StrictInt, Field(ge=1, le=MAX_ARTIFACT_BYTES)]
    source_reference: Text
    provenance: Text
    custodian_reference: Text
    rights_reference: Text
    purpose: Text
    reconstruction_scope: Text
    exact_tools: Annotated[list[Key], Field(min_length=1, max_length=122)]
    expires_at: datetime

    @field_validator("exact_tools", mode="before")
    @classmethod
    def tools(cls, value):
        from app.services.organization_rea_catalog import get_rea_tool, ReaCatalogInvalid
        if type(value) is not list or any(type(item) is not str for item in value) or len(value) != len(set(value)):
            raise ValueError("exact_tools must be a unique list")
        try:
            for item in value:
                get_rea_tool(item)
        except ReaCatalogInvalid as exc:
            raise ValueError("unknown exact REA tool") from exc
        return sorted(value)

    @field_validator("expires_at", mode="before")
    @classmethod
    def datetime_type(cls, value):
        if not isinstance(value, (str, datetime)):
            raise ValueError("expiry must be an explicit datetime")
        return value

    @field_validator("expires_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("expiry must be timezone-aware")
        return value.astimezone(timezone.utc)

    @field_validator("source_reference", "provenance", "custodian_reference", "rights_reference", "purpose", "reconstruction_scope")
    @classmethod
    def meaningful(cls, value):
        try:
            value.encode("utf-8")
        except UnicodeError as exc:
            raise ValueError("reference/scope must be valid UTF-8") from exc
        if not value.strip() or "\x00" in value:
            raise ValueError("reference/scope must be nonblank and NUL-free")
        return value


class ReaArtifactProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision_key: Key
    work_item_id: UUID
    scope: ReaArtifactScope
    supersedes_decision_id: UUID | None = None

    @field_validator("decision_key")
    @classmethod
    def key(cls, value):
        return ReaArtifactScope.meaningful(value)


class ReaArtifactRevocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision_key: Key
    reason: Text

    @field_validator("decision_key", "reason")
    @classmethod
    def strings(cls, value):
        return ReaArtifactScope.meaningful(value)


class ReaArtifactAuthorizationRead(BaseModel):
    decision_id: UUID
    work_item_id: UUID
    contract_sha256: str
    artifact_sha256: str
    artifact_bytes: int
    exact_tools: list[str]
    expires_at: datetime
    execution_authorized: bool = False

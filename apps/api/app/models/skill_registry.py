from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class OrganizationSkill(SQLModel, table=True):
    __tablename__ = "organization_skills"
    __table_args__ = (
        UniqueConstraint("skill_key", "version", name="uq_org_skill_key_version"),
        Index(
            "ux_organization_skills_active_skill_key",
            "skill_key",
            unique=True,
            sqlite_where=text("status = 'active'"),
            postgresql_where=text("status = 'active'"),
        ),
        CheckConstraint(
            "origin IN ('native','imported','learned')",
            name="ck_org_skill_origin",
        ),
        CheckConstraint(
            "status IN ('active','deprecated','superseded','quarantined')",
            name="ck_org_skill_status",
        ),
        CheckConstraint(
            "validation_status IN ('unvalidated','passed','failed')",
            name="ck_org_skill_validation_status",
        ),
        CheckConstraint("version >= 1", name="ck_org_skill_version_positive"),
        CheckConstraint("length(content_sha256) = 64", name="ck_org_skill_content_sha256"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    skill_key: str = Field(index=True)
    name: str
    capability_family: str = Field(index=True)
    description: str
    origin: str = Field(default="native", index=True)
    source_ref: str | None = Field(default=None, index=True)
    source_license: str | None = None
    version: int = Field(default=1, index=True)
    content_sha256: str = Field(index=True)
    compatible_departments_json: str = "[]"
    compatible_position_keys_json: str = "[]"
    tool_requirements_json: str = "[]"
    permission_requirements_json: str = "[]"
    input_schema_json: str = "{}"
    output_schema_json: str = "{}"
    evidence_expectations_json: str = "[]"
    validation_status: str = Field(default="unvalidated", index=True)
    validation_summary_json: str = "{}"
    performance_summary_json: str = "{}"
    status: str = Field(default="active", index=True)
    supersedes_skill_id: UUID | None = Field(
        default=None,
        index=True,
        foreign_key="organization_skills.id",
    )
    created_by: str = Field(default="system", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class OrganizationPositionSkill(SQLModel, table=True):
    __tablename__ = "organization_position_skills"
    __table_args__ = (
        UniqueConstraint(
            "organization_position_id",
            "organization_skill_id",
            name="uq_org_position_skill_binding",
        ),
        CheckConstraint(
            "status IN ('eligible','disabled')",
            name="ck_org_position_skill_status",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    organization_position_id: UUID = Field(
        index=True,
        foreign_key="organization_positions.id",
    )
    organization_skill_id: UUID = Field(
        index=True,
        foreign_key="organization_skills.id",
    )
    status: str = Field(default="eligible", index=True)
    assignment_reason: str
    assigned_by: str = Field(default="system", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)

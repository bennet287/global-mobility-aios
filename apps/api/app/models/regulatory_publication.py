from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class RegulatoryPublicationSet(SQLModel, table=True):
    __tablename__ = "regulatory_publication_sets"
    __table_args__ = (
        UniqueConstraint("regulatory_change_id", name="uq_reg_pub_set_change"),
        CheckConstraint(
            "length(source_snapshot_hash) = 64",
            name="ck_reg_pub_set_snapshot_hash",
        ),
        CheckConstraint(
            "length(intended_mutations_sha256) = 64",
            name="ck_reg_pub_set_mutations_hash",
        ),
        CheckConstraint(
            "autonomy_profile_sequence >= 1",
            name="ck_reg_pub_set_profile_sequence_positive",
        ),
        CheckConstraint(
            "intended_rule_count >= 1 AND intended_rule_count <= 100",
            name="ck_reg_pub_set_rule_count_bound",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    regulatory_change_id: UUID = Field(index=True, foreign_key="regulatory_changes.id")
    source_snapshot_id: UUID = Field(index=True, foreign_key="source_snapshots.id")
    source_snapshot_hash: str = Field(index=True)
    publication_mode: str = Field(default="board_delegated_machine", index=True)
    actor_type: str = Field(index=True)
    actor_key: str = Field(index=True)
    authorization_audit_id: UUID = Field(index=True, foreign_key="audit_logs.id")
    authority_bridge_audit_id: UUID = Field(index=True, foreign_key="audit_logs.id")
    autonomy_profile_id: str = Field(index=True)
    autonomy_profile_sequence: int
    intended_rule_count: int
    intended_mutations_sha256: str = Field(index=True)
    published_rules_json: str = "[]"
    status: str = Field(default="published", index=True)
    published_at: datetime = Field(default_factory=now_utc, index=True)
    created_at: datetime = Field(default_factory=now_utc)


class RegulatoryReviewDisposition(SQLModel, table=True):
    __tablename__ = "regulatory_review_dispositions"
    __table_args__ = (
        UniqueConstraint("human_review_id", name="uq_reg_review_disposition_review"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    human_review_id: UUID = Field(index=True, foreign_key="human_reviews.id")
    regulatory_change_id: UUID = Field(index=True, foreign_key="regulatory_changes.id")
    publication_set_id: UUID = Field(index=True, foreign_key="regulatory_publication_sets.id")
    disposition: str = Field(default="waived_board_delegation", index=True)
    actor_type: str = Field(index=True)
    actor_key: str = Field(index=True)
    authority_bridge_audit_id: UUID = Field(index=True, foreign_key="audit_logs.id")
    disposition_reason: str
    created_at: datetime = Field(default_factory=now_utc, index=True)

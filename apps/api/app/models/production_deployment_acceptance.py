from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class ProductionDeploymentAcceptanceRun(SQLModel, table=True):
    """Prepared Phase 22 deployment identity; existence is not evidence of deployment."""

    __tablename__ = "production_deployment_acceptance_runs"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_prod_deploy_accept_run_tenant_id"),
        UniqueConstraint(
            "tenant_key",
            "deployment_run_key",
            name="uq_prod_deploy_accept_run_tenant_key",
        ),
        CheckConstraint(
            "execution_mode = 'canary'",
            name="ck_prod_deploy_accept_run_mode",
        ),
        CheckConstraint(
            "environment_class = 'canary'",
            name="ck_prod_deploy_accept_run_environment_class",
        ),
        CheckConstraint(
            "length(target_environment_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_environment_fp",
        ),
        CheckConstraint(
            "length(release_commit_sha) = 40",
            name="ck_prod_deploy_accept_run_release_sha",
        ),
        CheckConstraint(
            "length(release_configuration_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_release_config_fp",
        ),
        CheckConstraint(
            "length(rollback_release_commit_sha) = 40",
            name="ck_prod_deploy_accept_run_rollback_sha",
        ),
        CheckConstraint(
            "release_commit_sha <> rollback_release_commit_sha",
            name="ck_prod_deploy_accept_run_distinct_rollback",
        ),
        CheckConstraint(
            "length(rollback_configuration_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_rollback_config_fp",
        ),
        CheckConstraint(
            "acceptance_contract_version >= 1",
            name="ck_prod_deploy_accept_run_contract_version",
        ),
        CheckConstraint(
            "length(acceptance_contract_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_contract_fp",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_record_fp",
        ),
        CheckConstraint(
            "length(prepared_activity_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_activity_fp",
        ),
        CheckConstraint(
            "(networking_contract_key IS NULL AND networking_contract_version IS NULL "
            "AND networking_contract_fingerprint IS NULL AND networking_contract_json IS NULL) "
            "OR (networking_contract_key IS NOT NULL AND networking_contract_version IS NOT NULL "
            "AND networking_contract_fingerprint IS NOT NULL AND networking_contract_json IS NOT NULL)",
            name="ck_prod_deploy_accept_run_networking_all_or_none",
        ),
        CheckConstraint(
            "networking_contract_key IS NULL OR networking_contract_key = 'phase22.single_vps.public_networking'",
            name="ck_prod_deploy_accept_run_networking_key",
        ),
        CheckConstraint(
            "networking_contract_version IS NULL OR networking_contract_version = 1",
            name="ck_prod_deploy_accept_run_networking_version",
        ),
        CheckConstraint(
            "networking_contract_fingerprint IS NULL OR length(networking_contract_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_networking_fp",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_prod_deploy_accept_run_work_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "admission_decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_prod_deploy_accept_run_decision_tenant",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "prepared_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_prod_deploy_accept_run_activity_tenant",
        ),
        Index(
            "ix_prod_deploy_accept_run_environment",
            "tenant_key",
            "environment_key",
            "created_at",
        ),
        Index(
            "ix_prod_deploy_accept_run_work",
            "tenant_key",
            "work_item_id",
        ),
        Index(
            "ix_prod_deploy_accept_run_release",
            "tenant_key",
            "release_commit_sha",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str
    deployment_run_key: str
    execution_mode: str = "canary"
    environment_key: str
    environment_class: str = "canary"
    target_environment_fingerprint: str = Field(max_length=64)
    environment_constraints_json: str
    release_commit_sha: str = Field(max_length=40)
    release_configuration_fingerprint: str = Field(max_length=64)
    rollback_release_commit_sha: str = Field(max_length=40)
    rollback_configuration_fingerprint: str = Field(max_length=64)
    acceptance_contract_key: str
    acceptance_contract_version: int
    acceptance_contract_fingerprint: str = Field(max_length=64)
    required_gate_keys_json: str
    networking_contract_key: str | None = None
    networking_contract_version: int | None = None
    networking_contract_fingerprint: str | None = Field(default=None, max_length=64)
    networking_contract_json: str | None = None
    work_item_id: UUID
    admission_decision_id: UUID
    reason: str
    record_fingerprint: str = Field(max_length=64)
    prepared_activity_id: UUID
    prepared_activity_fingerprint: str = Field(max_length=64)
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)


class ProductionDeploymentAcceptanceCheckReceipt(SQLModel, table=True):
    """Immutable target-host gate receipt. No public write endpoint exists in foundation v1."""

    __tablename__ = "production_deployment_acceptance_check_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_key", "id", name="uq_prod_deploy_receipt_tenant_id"),
        UniqueConstraint(
            "tenant_key",
            "deployment_run_id",
            "gate_key",
            name="uq_prod_deploy_receipt_run_gate",
        ),
        CheckConstraint(
            "gate_version >= 1",
            name="ck_prod_deploy_receipt_gate_version",
        ),
        CheckConstraint(
            "status IN ('satisfied','failed','blocked','unknown')",
            name="ck_prod_deploy_receipt_status",
        ),
        CheckConstraint(
            "length(observed_target_environment_fingerprint) = 64",
            name="ck_prod_deploy_receipt_environment_fp",
        ),
        CheckConstraint(
            "length(observed_release_commit_sha) = 40",
            name="ck_prod_deploy_receipt_release_sha",
        ),
        CheckConstraint(
            "length(observed_release_configuration_fingerprint) = 64",
            name="ck_prod_deploy_receipt_release_config_fp",
        ),
        CheckConstraint(
            "executor_contract_version >= 1",
            name="ck_prod_deploy_receipt_executor_version",
        ),
        CheckConstraint(
            "length(executor_identity_fingerprint) = 64",
            name="ck_prod_deploy_receipt_executor_fp",
        ),
        CheckConstraint(
            "length(evidence_digest) = 64",
            name="ck_prod_deploy_receipt_evidence_digest",
        ),
        CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_prod_deploy_receipt_record_fp",
        ),
        ForeignKeyConstraint(
            ["tenant_key", "deployment_run_id"],
            ["production_deployment_acceptance_runs.tenant_key", "production_deployment_acceptance_runs.id"],
            name="fk_prod_deploy_receipt_run_tenant",
        ),
        Index(
            "ix_prod_deploy_receipt_run",
            "tenant_key",
            "deployment_run_id",
        ),
        Index(
            "ix_prod_deploy_receipt_status",
            "tenant_key",
            "status",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_key: str
    deployment_run_id: UUID
    gate_key: str
    gate_version: int
    status: str
    observed_target_environment_fingerprint: str = Field(max_length=64)
    observed_release_commit_sha: str = Field(max_length=40)
    observed_release_configuration_fingerprint: str = Field(max_length=64)
    executor_contract_key: str
    executor_contract_version: int
    executor_identity_fingerprint: str = Field(max_length=64)
    evidence_digest: str = Field(max_length=64)
    evidence_reference: str
    redacted_details_json: str = "{}"
    observed_at: datetime
    record_fingerprint: str = Field(max_length=64)
    created_by: str
    created_at: datetime = Field(default_factory=now_utc)

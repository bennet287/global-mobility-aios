"""Add Phase 22 deployment acceptance foundation.

Revision ID: 0098_production_deployment_acceptance
Revises: 0097_grsi_admission_dependency_policy
"""
from alembic import op
import sqlalchemy as sa


revision = "0098_production_deployment_acceptance"
down_revision = "0097_grsi_admission_dependency_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "production_deployment_acceptance_runs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("deployment_run_key", sa.String(), nullable=False),
        sa.Column("execution_mode", sa.String(), nullable=False),
        sa.Column("environment_key", sa.String(), nullable=False),
        sa.Column("environment_class", sa.String(), nullable=False),
        sa.Column("target_environment_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("environment_constraints_json", sa.String(), nullable=False),
        sa.Column("release_commit_sha", sa.String(length=40), nullable=False),
        sa.Column("release_configuration_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("rollback_release_commit_sha", sa.String(length=40), nullable=False),
        sa.Column("rollback_configuration_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("acceptance_contract_key", sa.String(), nullable=False),
        sa.Column("acceptance_contract_version", sa.Integer(), nullable=False),
        sa.Column("acceptance_contract_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("required_gate_keys_json", sa.String(), nullable=False),
        sa.Column("work_item_id", sa.Uuid(), nullable=False),
        sa.Column("admission_decision_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("prepared_activity_id", sa.Uuid(), nullable=False),
        sa.Column("prepared_activity_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_prod_deploy_accept_run_tenant_id",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "deployment_run_key",
            name="uq_prod_deploy_accept_run_tenant_key",
        ),
        sa.CheckConstraint(
            "execution_mode = 'canary'",
            name="ck_prod_deploy_accept_run_mode",
        ),
        sa.CheckConstraint(
            "environment_class = 'canary'",
            name="ck_prod_deploy_accept_run_environment_class",
        ),
        sa.CheckConstraint(
            "length(target_environment_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_environment_fp",
        ),
        sa.CheckConstraint(
            "length(release_commit_sha) = 40",
            name="ck_prod_deploy_accept_run_release_sha",
        ),
        sa.CheckConstraint(
            "length(release_configuration_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_release_config_fp",
        ),
        sa.CheckConstraint(
            "length(rollback_release_commit_sha) = 40",
            name="ck_prod_deploy_accept_run_rollback_sha",
        ),
        sa.CheckConstraint(
            "release_commit_sha <> rollback_release_commit_sha",
            name="ck_prod_deploy_accept_run_distinct_rollback",
        ),
        sa.CheckConstraint(
            "length(rollback_configuration_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_rollback_config_fp",
        ),
        sa.CheckConstraint(
            "acceptance_contract_version >= 1",
            name="ck_prod_deploy_accept_run_contract_version",
        ),
        sa.CheckConstraint(
            "length(acceptance_contract_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_contract_fp",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_record_fp",
        ),
        sa.CheckConstraint(
            "length(prepared_activity_fingerprint) = 64",
            name="ck_prod_deploy_accept_run_activity_fp",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_prod_deploy_accept_run_work_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "admission_decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_prod_deploy_accept_run_decision_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "prepared_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_prod_deploy_accept_run_activity_tenant",
        ),
    )
    op.create_index(
        "ix_prod_deploy_accept_run_environment",
        "production_deployment_acceptance_runs",
        ["tenant_key", "environment_key", "created_at"],
    )
    op.create_index(
        "ix_prod_deploy_accept_run_work",
        "production_deployment_acceptance_runs",
        ["tenant_key", "work_item_id"],
    )
    op.create_index(
        "ix_prod_deploy_accept_run_release",
        "production_deployment_acceptance_runs",
        ["tenant_key", "release_commit_sha"],
    )

    op.create_table(
        "production_deployment_acceptance_check_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("deployment_run_id", sa.Uuid(), nullable=False),
        sa.Column("gate_key", sa.String(), nullable=False),
        sa.Column("gate_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("observed_target_environment_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("observed_release_commit_sha", sa.String(length=40), nullable=False),
        sa.Column("observed_release_configuration_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("executor_contract_key", sa.String(), nullable=False),
        sa.Column("executor_contract_version", sa.Integer(), nullable=False),
        sa.Column("executor_identity_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("evidence_digest", sa.String(length=64), nullable=False),
        sa.Column("evidence_reference", sa.String(), nullable=False),
        sa.Column("redacted_details_json", sa.String(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_prod_deploy_receipt_tenant_id",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "deployment_run_id",
            "gate_key",
            name="uq_prod_deploy_receipt_run_gate",
        ),
        sa.CheckConstraint(
            "gate_version >= 1",
            name="ck_prod_deploy_receipt_gate_version",
        ),
        sa.CheckConstraint(
            "status IN ('satisfied','failed','blocked','unknown')",
            name="ck_prod_deploy_receipt_status",
        ),
        sa.CheckConstraint(
            "length(observed_target_environment_fingerprint) = 64",
            name="ck_prod_deploy_receipt_environment_fp",
        ),
        sa.CheckConstraint(
            "length(observed_release_commit_sha) = 40",
            name="ck_prod_deploy_receipt_release_sha",
        ),
        sa.CheckConstraint(
            "length(observed_release_configuration_fingerprint) = 64",
            name="ck_prod_deploy_receipt_release_config_fp",
        ),
        sa.CheckConstraint(
            "executor_contract_version >= 1",
            name="ck_prod_deploy_receipt_executor_version",
        ),
        sa.CheckConstraint(
            "length(executor_identity_fingerprint) = 64",
            name="ck_prod_deploy_receipt_executor_fp",
        ),
        sa.CheckConstraint(
            "length(evidence_digest) = 64",
            name="ck_prod_deploy_receipt_evidence_digest",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_prod_deploy_receipt_record_fp",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "deployment_run_id"],
            ["production_deployment_acceptance_runs.tenant_key", "production_deployment_acceptance_runs.id"],
            name="fk_prod_deploy_receipt_run_tenant",
        ),
    )
    op.create_index(
        "ix_prod_deploy_receipt_run",
        "production_deployment_acceptance_check_receipts",
        ["tenant_key", "deployment_run_id"],
    )
    op.create_index(
        "ix_prod_deploy_receipt_status",
        "production_deployment_acceptance_check_receipts",
        ["tenant_key", "status"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(
        sa.text("SELECT COUNT(*) FROM production_deployment_acceptance_check_receipts")
    ).scalar_one():
        raise RuntimeError("Cannot discard governed deployment acceptance receipts")
    if connection.execute(
        sa.text("SELECT COUNT(*) FROM production_deployment_acceptance_runs")
    ).scalar_one():
        raise RuntimeError("Cannot discard governed deployment acceptance runs")

    op.drop_index(
        "ix_prod_deploy_receipt_status",
        table_name="production_deployment_acceptance_check_receipts",
    )
    op.drop_index(
        "ix_prod_deploy_receipt_run",
        table_name="production_deployment_acceptance_check_receipts",
    )
    op.drop_table("production_deployment_acceptance_check_receipts")

    op.drop_index(
        "ix_prod_deploy_accept_run_release",
        table_name="production_deployment_acceptance_runs",
    )
    op.drop_index(
        "ix_prod_deploy_accept_run_work",
        table_name="production_deployment_acceptance_runs",
    )
    op.drop_index(
        "ix_prod_deploy_accept_run_environment",
        table_name="production_deployment_acceptance_runs",
    )
    op.drop_table("production_deployment_acceptance_runs")

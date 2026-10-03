"""Bind immutable Phase 22 release/networking expectations to prepared runs.

Revision ID: 0100_phase22_release_networking_contract
Revises: 0099_grsi_canary_dependency_policy
"""
from alembic import op
import sqlalchemy as sa


revision = "0100_phase22_release_networking_contract"
down_revision = "0099_grsi_canary_dependency_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("production_deployment_acceptance_runs") as batch:
        batch.add_column(sa.Column("networking_contract_key", sa.String(), nullable=True))
        batch.add_column(sa.Column("networking_contract_version", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column("networking_contract_fingerprint", sa.String(length=64), nullable=True)
        )
        batch.add_column(sa.Column("networking_contract_json", sa.String(), nullable=True))
        batch.create_check_constraint(
            "ck_prod_deploy_accept_run_networking_all_or_none",
            "(networking_contract_key IS NULL AND networking_contract_version IS NULL "
            "AND networking_contract_fingerprint IS NULL AND networking_contract_json IS NULL) "
            "OR (networking_contract_key IS NOT NULL AND networking_contract_version IS NOT NULL "
            "AND networking_contract_fingerprint IS NOT NULL AND networking_contract_json IS NOT NULL)",
        )
        batch.create_check_constraint(
            "ck_prod_deploy_accept_run_networking_key",
            "networking_contract_key IS NULL OR networking_contract_key = "
            "'phase22.single_vps.public_networking'",
        )
        batch.create_check_constraint(
            "ck_prod_deploy_accept_run_networking_version",
            "networking_contract_version IS NULL OR networking_contract_version = 1",
        )
        batch.create_check_constraint(
            "ck_prod_deploy_accept_run_networking_fp",
            "networking_contract_fingerprint IS NULL OR length(networking_contract_fingerprint) = 64",
        )


def downgrade() -> None:
    connection = op.get_bind()
    bound = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM production_deployment_acceptance_runs "
            "WHERE networking_contract_key IS NOT NULL "
            "OR networking_contract_version IS NOT NULL "
            "OR networking_contract_fingerprint IS NOT NULL "
            "OR networking_contract_json IS NOT NULL"
        )
    ).scalar_one()
    if bound:
        raise RuntimeError(
            "Cannot discard Phase 22 networking contracts from governed deployment runs"
        )

    with op.batch_alter_table("production_deployment_acceptance_runs") as batch:
        batch.drop_constraint(
            "ck_prod_deploy_accept_run_networking_fp",
            type_="check",
        )
        batch.drop_constraint(
            "ck_prod_deploy_accept_run_networking_version",
            type_="check",
        )
        batch.drop_constraint(
            "ck_prod_deploy_accept_run_networking_key",
            type_="check",
        )
        batch.drop_constraint(
            "ck_prod_deploy_accept_run_networking_all_or_none",
            type_="check",
        )
        batch.drop_column("networking_contract_json")
        batch.drop_column("networking_contract_fingerprint")
        batch.drop_column("networking_contract_version")
        batch.drop_column("networking_contract_key")

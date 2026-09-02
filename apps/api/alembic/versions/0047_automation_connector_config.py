"""Automation connector configs and delivery retry columns.

Revision ID: 0047_automation_connector_config
Revises: 0046_governed_automation_outbox
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0047_automation_connector_config"
down_revision = "0046_governed_automation_outbox"
branch_labels = None
depends_on = None


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "automation_connector_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_account_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("provider_type", sa.String(), nullable=False),
        sa.Column("credentials_json", sa.String(), nullable=False),
        sa.Column("from_address", sa.String(), nullable=True),
        sa.Column("sender_label", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "automation_connector_configs",
        (
            "id",
            "corporate_account_id",
            "channel",
            "provider_type",
            "status",
            "from_address",
            "created_by",
            "updated_by",
            "created_at",
        ),
    )

    with op.batch_alter_table("automation_deliveries") as batch_op:
        batch_op.add_column(sa.Column("connector_config_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("next_attempt_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_automation_deliveries_connector_config_id",
            "automation_connector_configs",
            ["connector_config_id"],
            ["id"],
        )
        batch_op.create_index("ix_automation_deliveries_connector_config_id", ["connector_config_id"])
        batch_op.create_index("ix_automation_deliveries_next_attempt_at", ["next_attempt_at"])


def downgrade() -> None:
    with op.batch_alter_table("automation_deliveries") as batch_op:
        batch_op.drop_index("ix_automation_deliveries_next_attempt_at")
        batch_op.drop_index("ix_automation_deliveries_connector_config_id")
        batch_op.drop_constraint("fk_automation_deliveries_connector_config_id", type_="foreignkey")
        batch_op.drop_column("next_attempt_at")
        batch_op.drop_column("connector_config_id")
    op.drop_table("automation_connector_configs")

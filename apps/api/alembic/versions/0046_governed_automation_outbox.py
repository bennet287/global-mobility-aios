"""Governed case-event automation outbox.

Revision ID: 0046_governed_automation_outbox
Revises: 0045_partner_api_credentials
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0046_governed_automation_outbox"
down_revision = "0045_partner_api_credentials"
branch_labels = None
depends_on = None


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "automation_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_account_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("channels", sa.String(), nullable=False),
        sa.Column("destinations_json", sa.String(), nullable=True),
        sa.Column("subject_template", sa.String(), nullable=True),
        sa.Column("body_template", sa.String(), nullable=True),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "automation_rules",
        ("id", "corporate_account_id", "event_type", "status", "created_by", "updated_by", "created_at"),
    )

    op.create_table(
        "automation_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("corporate_account_id", sa.Uuid(), nullable=False),
        sa.Column("corporate_mobility_case_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("payload_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    _indexes(
        "automation_events",
        (
            "id",
            "idempotency_key",
            "corporate_account_id",
            "corporate_mobility_case_id",
            "event_type",
            "entity_type",
            "entity_id",
            "source",
            "status",
            "occurred_at",
            "created_by",
            "created_at",
        ),
    )

    op.create_table(
        "automation_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("automation_event_id", sa.Uuid(), nullable=False),
        sa.Column("automation_rule_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("destination", sa.String(), nullable=True),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("payload_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_reason", sa.String(), nullable=True),
        sa.Column("dispatched_by", sa.String(), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(), nullable=True),
        sa.Column("provider_message_id", sa.String(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["automation_event_id"], ["automation_events.id"]),
        sa.ForeignKeyConstraint(["automation_rule_id"], ["automation_rules.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "automation_deliveries",
        (
            "id",
            "automation_event_id",
            "automation_rule_id",
            "channel",
            "status",
            "reviewed_by",
            "reviewed_at",
            "dispatched_by",
            "dispatched_at",
            "provider_message_id",
            "created_at",
        ),
    )


def downgrade() -> None:
    op.drop_table("automation_deliveries")
    op.drop_table("automation_events")
    op.drop_table("automation_rules")

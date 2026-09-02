"""Add AI organization governance ledgers.

Revision ID: 0056_ai_organization_governance
Revises: 0055_client_portal_device_binding
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0056_ai_organization_governance"
down_revision = "0055_client_portal_device_binding"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "organization_positions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("position_key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=False),
        sa.Column("reports_to_position_key", sa.String(), nullable=True),
        sa.Column("role_card_name", sa.String(), nullable=True),
        sa.Column("authority_level", sa.String(), nullable=False),
        sa.Column("contract_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("position_key", "version", name="uq_org_position_version"),
    )
    op.create_index("ix_org_positions_key", "organization_positions", ["position_key"])
    op.create_index("ix_org_positions_department", "organization_positions", ["department"])
    op.create_index("ix_org_positions_status", "organization_positions", ["status"])

    op.create_table(
        "organizational_work_items",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("automation_event_id", _uuid(), nullable=True),
        sa.Column("lead_id", _uuid(), nullable=True),
        sa.Column("corporate_account_id", _uuid(), nullable=True),
        sa.Column("corporate_mobility_case_id", _uuid(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("objective", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=False),
        sa.Column("authority_level", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("assigned_position_key", sa.String(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("context_json", sa.String(), nullable=False),
        sa.Column("output_json", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["automation_event_id"], ["automation_events.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_org_work_idempotency"),
    )
    for column in ("automation_event_id", "lead_id", "corporate_account_id", "corporate_mobility_case_id", "department", "authority_level", "status", "assigned_position_key", "risk_level", "created_at"):
        op.create_index(f"ix_org_work_{column}", "organizational_work_items", [column])

    op.create_table(
        "delegation_records",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=False),
        sa.Column("delegator_position_key", sa.String(), nullable=False),
        sa.Column("delegate_position_key", sa.String(), nullable=False),
        sa.Column("task", sa.String(), nullable=False),
        sa.Column("authority_basis", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("result_ref", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["work_item_id"], ["organizational_work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("work_item_id", "delegator_position_key", "delegate_position_key", "status", "created_at"):
        op.create_index(f"ix_delegation_{column}", "delegation_records", [column])

    op.create_table(
        "executive_decisions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("decision_key", sa.String(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=True),
        sa.Column("authority_level", sa.String(), nullable=False),
        sa.Column("requested_by_position", sa.String(), nullable=False),
        sa.Column("decision_owner_position", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("recommendation", sa.String(), nullable=False),
        sa.Column("alternatives_json", sa.String(), nullable=False),
        sa.Column("evidence_json", sa.String(), nullable=False),
        sa.Column("impact_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("decided_by", sa.String(), nullable=True),
        sa.Column("decision_reason", sa.String(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["work_item_id"], ["organizational_work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_key", name="uq_executive_decision_key"),
    )
    for column in ("work_item_id", "authority_level", "decision_owner_position", "status", "created_at"):
        op.create_index(f"ix_exec_decision_{column}", "executive_decisions", [column])

    op.create_table(
        "risk_escalations",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("risk_key", sa.String(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("evidence_json", sa.String(), nullable=False),
        sa.Column("containment_json", sa.String(), nullable=False),
        sa.Column("accountable_position_key", sa.String(), nullable=False),
        sa.Column("escalated_to_position_key", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("requires_board_attention", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["work_item_id"], ["organizational_work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("risk_key", name="uq_risk_escalation_key"),
    )
    for column in ("work_item_id", "category", "severity", "escalated_to_position_key", "status", "requires_board_attention", "created_at"):
        op.create_index(f"ix_risk_{column}", "risk_escalations", [column])

    op.create_table(
        "board_packets",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("packet_key", sa.String(), nullable=False),
        sa.Column("packet_type", sa.String(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ceo_summary", sa.String(), nullable=False),
        sa.Column("content_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("prepared_by_position", sa.String(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("packet_key", name="uq_board_packet_key"),
    )
    for column in ("packet_type", "period_start", "period_end", "status", "prepared_by_position", "published_at", "created_at"):
        op.create_index(f"ix_board_packet_{column}", "board_packets", [column])

    op.create_table(
        "organization_controls",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("control_key", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("changed_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("control_key", name="uq_org_control_key"),
    )
    for column in ("status", "changed_by", "created_at"):
        op.create_index(f"ix_org_control_{column}", "organization_controls", [column])


def downgrade() -> None:
    op.drop_table("organization_controls")
    op.drop_table("board_packets")
    op.drop_table("risk_escalations")
    op.drop_table("executive_decisions")
    op.drop_table("delegation_records")
    op.drop_table("organizational_work_items")
    op.drop_table("organization_positions")

"""Add durable executive council consultations.

Revision ID: 0061_exec_council_consultations
Revises: 0060_org_execution_controls
Create Date: 2026-08-03
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "0061_exec_council_consultations"
down_revision = "0060_org_execution_controls"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def _ceo_contract_json() -> str:
    return json.dumps(
        {
            "audit_required": True,
            "capabilities": [
                "coordinate_executive_council",
                "resolve_evidence_complete_internal_l3",
                "escalate_l4_emergency_and_conflict",
            ],
            "direct_action_authority": [],
            "evidence_required": True,
            "external_action_authorized": False,
            "may_act_within": "L3",
            "must_escalate_above": "L3",
            "prohibited_direct_actions": [
                "authority.submit",
                "client.external_send",
                "contract.sign",
                "deployment.production",
                "payment.initiate",
            ],
            "self_approval_allowed": False,
        },
        sort_keys=True,
    )


def upgrade() -> None:
    op.create_table(
        "executive_council_consultations",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("consultation_key", sa.String(), nullable=False),
        sa.Column("decision_id", _uuid(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=False),
        sa.Column("requested_by_position", sa.String(), nullable=False),
        sa.Column("consulted_position", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("evidence_json", sa.String(), nullable=False),
        sa.Column("recommendation", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("dissent", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["decision_id"], ["executive_decisions.id"]),
        sa.ForeignKeyConstraint(["work_item_id"], ["organizational_work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultation_key",
            name="uq_executive_council_consultation_key",
        ),
    )
    for column in (
        "consultation_key",
        "decision_id",
        "work_item_id",
        "requested_by_position",
        "consulted_position",
        "domain",
        "dissent",
        "status",
        "created_at",
        "completed_at",
    ):
        op.create_index(
            f"ix_executive_council_consultation_{column}",
            "executive_council_consultations",
            [column],
        )

    positions = sa.table(
        "organization_positions",
        sa.column("position_key", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("contract_json", sa.String()),
    )
    op.execute(
        positions.update()
        .where(positions.c.position_key == "ceo", positions.c.version == 1)
        .values(contract_json=_ceo_contract_json())
    )


def downgrade() -> None:
    op.drop_table("executive_council_consultations")

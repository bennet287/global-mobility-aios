"""Bind explicit human decision acceptance to one internal durable output.

Revision ID: 0090_reviewed_decision_output
Revises: 0089_provider_circuit_breaker
"""

from alembic import op
import sqlalchemy as sa


revision = "0090_reviewed_decision_output"
down_revision = "0089_provider_circuit_breaker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("executive_decisions") as batch:
        batch.add_column(sa.Column("accepted_action_output_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("accepted_action_output_sha256", sa.String(length=64), nullable=True))
        batch.create_foreign_key(
            "fk_exec_decision_accepted_output", "organizational_action_outputs",
            ["accepted_action_output_id"], ["id"],
        )
        batch.create_check_constraint(
            "ck_exec_decision_accepted_output_pair",
            "(accepted_action_output_id IS NULL) = (accepted_action_output_sha256 IS NULL)",
        )


def downgrade() -> None:
    with op.batch_alter_table("executive_decisions") as batch:
        batch.drop_constraint("ck_exec_decision_accepted_output_pair", type_="check")
        batch.drop_constraint("fk_exec_decision_accepted_output", type_="foreignkey")
        batch.drop_column("accepted_action_output_sha256")
        batch.drop_column("accepted_action_output_id")

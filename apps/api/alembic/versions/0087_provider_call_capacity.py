"""Authorize bounded provider call counts with atomic attempt admission.

Revision ID: 0087_provider_call_capacity
Revises: 0086_provider_call_attempt_coverage
"""

from alembic import op
import sqlalchemy as sa


revision = "0087_provider_call_capacity"
down_revision = "0086_provider_call_attempt_coverage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_call_allocations",
        sa.Column("provider", sa.String(), primary_key=True, nullable=False),
        sa.Column("authorized_calls", sa.Integer(), nullable=False),
        sa.Column("used_calls", sa.Integer(), nullable=False),
        sa.Column("paused", sa.Boolean(), nullable=False),
        sa.Column("authorized_by", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("authorized_calls >= 0", name="ck_provider_call_allocation_authorized"),
        sa.CheckConstraint(
            "used_calls >= 0 AND used_calls <= authorized_calls",
            name="ck_provider_call_allocation_used",
        ),
    )
    with op.batch_alter_table("provider_call_attempts", reflect_kwargs={"resolve_fks": False}) as batch:
        batch.add_column(sa.Column("allocation_provider", sa.String(), nullable=True))
        batch.create_foreign_key(
            "fk_provider_call_attempt_allocation",
            "provider_call_allocations", ["allocation_provider"], ["provider"],
        )
    op.create_index(
        "ix_provider_call_attempts_allocation_provider",
        "provider_call_attempts", ["allocation_provider"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text(
        "SELECT COUNT(*) FROM provider_call_attempts WHERE allocation_provider IS NOT NULL"
    )).scalar_one():
        raise RuntimeError("Cannot discard provider call allocation evidence")
    if connection.execute(sa.text("SELECT COUNT(*) FROM provider_call_allocations")).scalar_one():
        raise RuntimeError("Cannot discard authorized provider call capacity")
    op.drop_index("ix_provider_call_attempts_allocation_provider", table_name="provider_call_attempts")
    with op.batch_alter_table("provider_call_attempts", reflect_kwargs={"resolve_fks": False}) as batch:
        batch.drop_constraint("fk_provider_call_attempt_allocation", type_="foreignkey")
        batch.drop_column("allocation_provider")
    op.drop_table("provider_call_allocations")

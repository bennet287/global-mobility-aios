"""Allow GRSI admission dependency policy for canary execution.

Revision ID: 0099_grsi_canary_dependency_policy
Revises: 0098_production_deployment_acceptance
"""
from alembic import op
import sqlalchemy as sa


revision = "0099_grsi_canary_dependency_policy"
down_revision = "0098_production_deployment_acceptance"
branch_labels = None
depends_on = None

_TABLE = "organization_improvement_admission_dependency_policies"
_CONSTRAINT = "ck_org_improv_adm_policy_mode"


def _replace_mode_constraint(expression: str) -> None:
    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        with op.batch_alter_table(_TABLE, recreate="always") as batch_op:
            batch_op.drop_constraint(_CONSTRAINT, type_="check")
            batch_op.create_check_constraint(_CONSTRAINT, expression)
        return

    op.drop_constraint(_CONSTRAINT, _TABLE, type_="check")
    op.create_check_constraint(_CONSTRAINT, _TABLE, expression)


def upgrade() -> None:
    _replace_mode_constraint("execution_mode IN ('shadow','canary')")


def downgrade() -> None:
    connection = op.get_bind()
    canary_rows = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM organization_improvement_admission_dependency_policies "
            "WHERE execution_mode = 'canary'"
        )
    ).scalar_one()
    if canary_rows:
        raise RuntimeError(
            "Cannot narrow GRSI admission policy while governed canary policy rows exist"
        )
    _replace_mode_constraint("execution_mode = 'shadow'")

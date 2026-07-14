"""Authority-specific source parser profiles.

Revision ID: 0010_authority_parser_profiles
Revises: 0009_verified_rule_lifecycle
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_authority_parser_profiles"
down_revision = "0009_verified_rule_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("source_monitors") as batch:
        batch.add_column(sa.Column("parser_profile", sa.String(), nullable=False, server_default="generic"))
        batch.add_column(sa.Column("parser_config_json", sa.String(), nullable=True))
        batch.create_index("ix_source_monitors_parser_profile", ["parser_profile"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("source_monitors") as batch:
        batch.drop_index("ix_source_monitors_parser_profile")
        batch.drop_column("parser_config_json")
        batch.drop_column("parser_profile")

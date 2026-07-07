"""MVP-1 baseline schema

Revision ID: 0001_mvp1_baseline
Revises:
Create Date: 2026-07-06
"""

from alembic import op
from sqlmodel import SQLModel

from app.core.db import register_models

revision = "0001_mvp1_baseline"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    register_models()
    SQLModel.metadata.create_all(bind=op.get_bind())

def downgrade() -> None:
    register_models()
    SQLModel.metadata.drop_all(bind=op.get_bind())

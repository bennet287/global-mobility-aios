"""Persist structured case facts used by pathway assessment.

Revision ID: 0073_austria_candidate_integrity
Revises: 0072_intake_submission_idempotency
Create Date: 2026-08-13
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "0073_austria_candidate_integrity"
down_revision = "0072_intake_submission_idempotency"
branch_labels = None
depends_on = None


_COLUMNS = (
    ("nationality", sa.String()),
    ("current_country", sa.String()),
    ("occupation_title", sa.String()),
    ("years_experience", sa.Float()),
    ("job_offer_status", sa.String()),
    ("qualification_recognition", sa.String()),
    ("german_level", sa.String()),
    ("employment_province", sa.String()),
)


def upgrade() -> None:
    for name, column_type in _COLUMNS:
        op.add_column("leads", sa.Column(name, column_type, nullable=True))

    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT lead_id, answers_json FROM intake_sessions "
        "WHERE lead_id IS NOT NULL ORDER BY updated_at DESC"
    )).fetchall()
    seen: set[str] = set()
    for lead_id, raw_answers in rows:
        key = str(lead_id)
        if key in seen:
            continue
        seen.add(key)
        try:
            answers = json.loads(raw_answers or "{}")
        except (TypeError, ValueError):
            answers = {}
        bind.execute(
            sa.text(
                "UPDATE leads SET nationality=:nationality, current_country=:current_country, "
                "occupation_title=:occupation_title, years_experience=:years_experience, "
                "job_offer_status=:job_offer_status, qualification_recognition=:qualification_recognition, "
                "german_level=:german_level, employment_province=:employment_province WHERE id=:lead_id"
            ),
            {
                "lead_id": lead_id,
                "nationality": answers.get("nationality"),
                "current_country": answers.get("current_country"),
                "occupation_title": answers.get("profession"),
                "years_experience": answers.get("years_experience"),
                "job_offer_status": answers.get("job_offer_status"),
                "qualification_recognition": answers.get("qualification_recognition"),
                "german_level": answers.get("language_level"),
                "employment_province": answers.get("employment_province"),
            },
        )


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.drop_column("leads", name)

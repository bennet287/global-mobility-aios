from __future__ import annotations

import sys
from pathlib import Path

from sqlmodel import Session, select

from app.models.domain import Lead

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.seed_demo_data import DEMO_SOURCE, seed_demo_data  # noqa: E402


def test_demo_seed_creates_exactly_four_demo_leads(db_session: Session) -> None:
    summary = seed_demo_data(db_session, reset_demo=True)

    demo_leads = db_session.exec(select(Lead).where(Lead.source == DEMO_SOURCE)).all()

    assert summary["status"] == "seeded"
    assert summary["demo_leads"] == 4
    assert len(demo_leads) == 4
    assert {
        "Demo 1 - Blocked Visa Claim",
        "Demo 2 - Documents Pending",
        "Demo 3 - Ready For Application",
        "Demo 4 - Completed Journey",
    } == {lead.full_name for lead in demo_leads}

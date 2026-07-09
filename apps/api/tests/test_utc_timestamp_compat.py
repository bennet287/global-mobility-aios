from __future__ import annotations

from datetime import datetime
from typing import Callable

from app.routers import application_draft_control
from app.routers import application_engine
from app.routers import authority_decision
from app.routers import client_communications
from app.routers import document_verification
from app.routers import post_approval_onboarding
from app.routers import truth_resolution
from scripts import seed_demo_data


UTC_HELPERS: tuple[Callable[[], datetime], ...] = (
    truth_resolution._utcnow,
    application_draft_control._utcnow,
    application_engine._utcnow,
    authority_decision._utcnow,
    post_approval_onboarding._utcnow,
    document_verification._utcnow,
    client_communications._utcnow,
    seed_demo_data._utcnow,
)


def test_utc_helpers_keep_existing_naive_database_timestamp_shape() -> None:
    for helper in UTC_HELPERS:
        value = helper()

        assert isinstance(value, datetime)
        assert value.tzinfo is None

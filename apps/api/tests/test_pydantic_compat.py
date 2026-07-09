from __future__ import annotations

import warnings
from typing import Callable

from app.models.domain import Lead
from app.routers import admin_ui_sync
from app.routers import application_draft_control
from app.routers import application_engine
from app.routers import application_lifecycle
from app.routers import authority_decision
from app.routers import client_communications
from app.routers import document_verification
from app.routers import post_approval_onboarding
from app.routers import truth_resolution


MODEL_FIELD_HELPERS: tuple[Callable[[object], set[str]], ...] = (
    truth_resolution._model_fields,
    application_lifecycle._model_fields,
    application_draft_control._model_fields,
    admin_ui_sync._model_fields,
    document_verification._model_fields,
    client_communications._model_fields,
    application_engine._model_fields,
    authority_decision._model_fields,
    post_approval_onboarding._model_fields,
)


def test_model_field_helpers_do_not_touch_deprecated_pydantic_fields() -> None:
    caught_messages: list[str] = []

    for helper in MODEL_FIELD_HELPERS:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fields = helper(Lead)

        assert "id" in fields
        caught_messages.extend(str(item.message) for item in caught)

    assert not any("__fields__" in message for message in caught_messages)

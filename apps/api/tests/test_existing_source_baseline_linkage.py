from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.domain import (
    JurisdictionSourceCertification,
    OfficialSource,
)
from app.services.coverage_baseline_capture import _item_state


def _result(first):
    result = MagicMock()
    result.first.return_value = first
    return result


def test_certification_only_legacy_item_reuses_existing_baseline():
    jurisdiction_id = uuid4()
    authority_id = uuid4()
    source_id = uuid4()
    monitor_id = uuid4()
    certification_id = uuid4()

    assessment = SimpleNamespace(
        status="approved",
        jurisdiction_id=jurisdiction_id,
        official_source_id=uuid4(),
    )

    certification = SimpleNamespace(
        id=certification_id,
        status="approved",
        certification_scope="supplemental_visa",
        official_source_id=source_id,
        regulatory_authority_id=authority_id,
    )

    source = SimpleNamespace(
        id=source_id,
        active=True,
        jurisdiction_id=jurisdiction_id,
        regulatory_authority_id=authority_id,
    )

    monitor = SimpleNamespace(
        id=monitor_id,
        official_source_id=source_id,
        status="active",
    )

    snapshot = SimpleNamespace(
        id=uuid4(),
        status="baseline",
        content_hash="a" * 64,
        captured_at=datetime.now(timezone.utc),
        url="https://official.example/visa",
    )

    item = SimpleNamespace(
        id=uuid4(),
        alpha2_code="AT",
        jurisdiction_id=jurisdiction_id,
        immigration_assessment_id=None,
        source_certification_id=certification_id,
        regulatory_authority_id=None,
        official_source_id=None,
        source_monitor_id=None,
    )

    session = MagicMock()

    def fake_get(model, object_id):
        if (
            model is JurisdictionSourceCertification
            and object_id == certification_id
        ):
            return certification

        if model is OfficialSource and object_id == source_id:
            return source

        return None

    session.get.side_effect = fake_get

    # _item_state:
    # 1. approved jurisdiction assessment
    # 2. existing monitor for certified source
    # 3. existing immutable snapshot
    # 4. latest retrieval run
    session.exec.side_effect = [
        _result(assessment),
        _result(monitor),
        _result(snapshot),
        _result(None),
    ]

    state = _item_state(session, item)

    assert state["state"] == "baseline_ready"
    assert state["eligible_to_queue"] is False

    assert state["official_source_id"] == source_id
    assert state["source_monitor_id"] == monitor_id

    assert state["latest_snapshot"]["id"] == snapshot.id

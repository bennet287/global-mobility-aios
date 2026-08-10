from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.domain import (
    JurisdictionCoverageEvidenceBatch,
    JurisdictionSourceCertification,
    OfficialSource,
    RegulatoryAuthority,
)
from app.services.coverage_evidence_batches import (
    reconcile_coverage_batch_existing_source_linkage,
)


def _result(*, first=None, rows=None):
    result = MagicMock()
    result.first.return_value = first
    result.all.return_value = [] if rows is None else rows
    return result


def _fixtures():
    jurisdiction_id = uuid4()

    batch = SimpleNamespace(
        id=uuid4(),
    )

    authority = SimpleNamespace(
        id=uuid4(),
        active=True,
        jurisdiction_id=jurisdiction_id,
    )

    source = SimpleNamespace(
        id=uuid4(),
        active=True,
        jurisdiction_id=jurisdiction_id,
        regulatory_authority_id=authority.id,
    )

    monitor = SimpleNamespace(
        id=uuid4(),
        official_source_id=source.id,
        status="active",
    )

    certification = SimpleNamespace(
        id=uuid4(),
        status="approved",
        jurisdiction_id=jurisdiction_id,
        regulatory_authority_id=authority.id,
        official_source_id=source.id,
    )

    item = SimpleNamespace(
        id=uuid4(),
        batch_id=batch.id,
        row_number=1,
        alpha2_code="AT",
        jurisdiction_id=jurisdiction_id,
        source_certification_id=certification.id,
        regulatory_authority_id=None,
        official_source_id=None,
        source_monitor_id=None,
    )

    return (
        batch,
        authority,
        source,
        monitor,
        certification,
        item,
    )


def _session(
    batch,
    authority,
    source,
    monitor,
    certification,
    item,
):
    session = MagicMock()

    def fake_get(model, object_id):
        if (
            model is JurisdictionCoverageEvidenceBatch
            and object_id == batch.id
        ):
            return batch

        if (
            model is JurisdictionSourceCertification
            and object_id == certification.id
        ):
            return certification

        if (
            model is RegulatoryAuthority
            and object_id == authority.id
        ):
            return authority

        if (
            model is OfficialSource
            and object_id == source.id
        ):
            return source

        return None

    session.get.side_effect = fake_get
    session.exec.side_effect = [
        _result(rows=[item]),
        _result(first=monitor),
    ]

    return session


def test_reconciliation_backfills_only_derived_linkage():
    (
        batch,
        authority,
        source,
        monitor,
        certification,
        item,
    ) = _fixtures()

    session = _session(
        batch,
        authority,
        source,
        monitor,
        certification,
        item,
    )

    with patch(
        "app.services.coverage_evidence_batches."
        "record_audit"
    ) as record_audit:
        result = (
            reconcile_coverage_batch_existing_source_linkage(
                session,
                batch.id,
                actor="linkage-remediation-operator",
            )
        )

    assert result["changed"] == 1

    assert (
        item.regulatory_authority_id
        == authority.id
    )
    assert item.official_source_id == source.id
    assert item.source_monitor_id == monitor.id

    session.commit.assert_called_once()
    record_audit.assert_called_once()

    safety = result["safety"]

    assert safety["changes_certification"] is False
    assert safety["changes_source"] is False
    assert safety["changes_snapshot"] is False
    assert safety["changes_payload"] is False
    assert safety["creates_coverage_claim"] is False
    assert safety["publishes_verified_rule"] is False


def test_reconciliation_rejects_conflicting_source():
    (
        batch,
        authority,
        source,
        monitor,
        certification,
        item,
    ) = _fixtures()

    item.official_source_id = uuid4()

    session = _session(
        batch,
        authority,
        source,
        monitor,
        certification,
        item,
    )

    with pytest.raises(
        ValueError,
        match="conflicts with the approved certification",
    ):
        reconcile_coverage_batch_existing_source_linkage(
            session,
            batch.id,
            actor="linkage-remediation-operator",
        )

    session.commit.assert_not_called()


def test_reconciliation_is_idempotent():
    (
        batch,
        authority,
        source,
        monitor,
        certification,
        item,
    ) = _fixtures()

    item.regulatory_authority_id = authority.id
    item.official_source_id = source.id
    item.source_monitor_id = monitor.id

    session = _session(
        batch,
        authority,
        source,
        monitor,
        certification,
        item,
    )

    with patch(
        "app.services.coverage_evidence_batches."
        "record_audit"
    ) as record_audit:
        result = (
            reconcile_coverage_batch_existing_source_linkage(
                session,
                batch.id,
                actor="linkage-remediation-operator",
            )
        )

    assert result["changed"] == 0

    session.commit.assert_not_called()
    record_audit.assert_not_called()

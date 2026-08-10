from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.domain import OfficialSource, RegulatoryAuthority
from app.schemas import RegulatorySourceAuthorityReassignmentRequest
from app.services.regulatory_intelligence import reassign_official_source_authority


def _session_for(source, target, approved_primary, blocking=None):
    session = MagicMock()

    def fake_get(model, object_id):
        if model is OfficialSource and object_id == source.id:
            return source
        if model is RegulatoryAuthority and object_id == target.id:
            return target
        return None

    session.get.side_effect = fake_get

    approved_result = MagicMock()
    approved_result.first.return_value = approved_primary
    blocking_result = MagicMock()
    blocking_result.first.return_value = blocking
    session.exec.side_effect = [approved_result, blocking_result]
    return session


def test_reassignment_changes_only_authority_relationship_and_audits():
    jurisdiction_id = uuid4()
    source_id = uuid4()
    old_authority_id = uuid4()
    target_authority_id = uuid4()

    source = SimpleNamespace(
        id=source_id,
        active=True,
        jurisdiction_id=jurisdiction_id,
        regulatory_authority_id=old_authority_id,
    )
    target = SimpleNamespace(
        id=target_authority_id,
        active=True,
        jurisdiction_id=jurisdiction_id,
    )
    approved_primary = SimpleNamespace(regulatory_authority_id=target_authority_id)
    session = _session_for(source, target, approved_primary)

    payload = RegulatorySourceAuthorityReassignmentRequest(
        target_regulatory_authority_id=target_authority_id,
        reason="Correct duplicate authority ownership created during source onboarding.",
    )

    with patch("app.services.regulatory_intelligence.record_audit") as record_audit:
        updated, returned_target, changed = reassign_official_source_authority(
            session,
            source_id,
            payload,
            actor="remediation-operator",
        )

    assert updated is source
    assert returned_target is target
    assert changed is True
    assert source.id == source_id
    assert source.jurisdiction_id == jurisdiction_id
    assert source.regulatory_authority_id == target_authority_id
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(source)

    record_audit.assert_called_once()
    kwargs = record_audit.call_args.kwargs
    assert kwargs["action"] == "regulatory_source_authority_reassigned"
    assert kwargs["entity_type"] == "official_source"
    assert kwargs["entity_id"] == source_id
    assert kwargs["before_state"]["regulatory_authority_id"] == old_authority_id
    assert kwargs["after_state"]["regulatory_authority_id"] == target_authority_id
    assert kwargs["actor"] == "remediation-operator"


def test_reassignment_rejects_cross_jurisdiction_target():
    source = SimpleNamespace(
        id=uuid4(),
        active=True,
        jurisdiction_id=uuid4(),
        regulatory_authority_id=uuid4(),
    )
    target = SimpleNamespace(
        id=uuid4(),
        active=True,
        jurisdiction_id=uuid4(),
    )
    session = MagicMock()

    def fake_get(model, object_id):
        if model is OfficialSource and object_id == source.id:
            return source
        if model is RegulatoryAuthority and object_id == target.id:
            return target
        return None

    session.get.side_effect = fake_get
    payload = RegulatorySourceAuthorityReassignmentRequest(
        target_regulatory_authority_id=target.id,
        reason="Cross-jurisdiction reassignment must fail closed.",
    )

    with pytest.raises(ValueError, match="does not belong"):
        reassign_official_source_authority(
            session,
            source.id,
            payload,
            actor="remediation-operator",
        )

    assert source.regulatory_authority_id != target.id
    session.commit.assert_not_called()


def test_reassignment_rejects_source_with_pending_or_approved_certification():
    jurisdiction_id = uuid4()
    source = SimpleNamespace(
        id=uuid4(),
        active=True,
        jurisdiction_id=jurisdiction_id,
        regulatory_authority_id=uuid4(),
    )
    target = SimpleNamespace(
        id=uuid4(),
        active=True,
        jurisdiction_id=jurisdiction_id,
    )
    approved_primary = SimpleNamespace(regulatory_authority_id=target.id)
    blocking = SimpleNamespace(status="pending_review")
    session = _session_for(source, target, approved_primary, blocking=blocking)

    payload = RegulatorySourceAuthorityReassignmentRequest(
        target_regulatory_authority_id=target.id,
        reason="Certified-source provenance must not be silently rewritten.",
    )

    with pytest.raises(ValueError, match="pending or approved"):
        reassign_official_source_authority(
            session,
            source.id,
            payload,
            actor="remediation-operator",
        )

    session.commit.assert_not_called()


def test_reassignment_is_idempotent_after_target_is_already_attached():
    jurisdiction_id = uuid4()
    target_id = uuid4()
    source = SimpleNamespace(
        id=uuid4(),
        active=True,
        jurisdiction_id=jurisdiction_id,
        regulatory_authority_id=target_id,
    )
    target = SimpleNamespace(
        id=target_id,
        active=True,
        jurisdiction_id=jurisdiction_id,
    )
    approved_primary = SimpleNamespace(regulatory_authority_id=target_id)

    session = MagicMock()

    def fake_get(model, object_id):
        if model is OfficialSource and object_id == source.id:
            return source
        if model is RegulatoryAuthority and object_id == target.id:
            return target
        return None

    session.get.side_effect = fake_get
    approved_result = MagicMock()
    approved_result.first.return_value = approved_primary
    session.exec.return_value = approved_result

    payload = RegulatorySourceAuthorityReassignmentRequest(
        target_regulatory_authority_id=target.id,
        reason="Idempotent remediation retry after the source is already attached.",
    )

    with patch("app.services.regulatory_intelligence.record_audit") as record_audit:
        _, _, changed = reassign_official_source_authority(
            session,
            source.id,
            payload,
            actor="remediation-operator",
        )

    assert changed is False
    session.commit.assert_not_called()
    record_audit.assert_not_called()

from __future__ import annotations

import json

from sqlmodel import Session, select

from app.models.domain import AuditLog, Jurisdiction, OfficialSource, RegulatoryChange, SourceSnapshot
from app.services.audit_log import record_audit
from app.services.regulatory_autonomy import ROUTING_VERSION
from app.services.regulatory_machine_verification import (
    VERIFICATION_ACTION,
    evaluate_catalog_differential,
    verify_routed_regulatory_changes,
)


def _program(program_id: str, name: str, *, active: bool = True) -> dict:
    return {
        "program_id": program_id,
        "name": name,
        "status": "active" if active else "retired",
        "active": active,
        "summary": "",
        "effective_date": None,
    }


def test_new_program_is_verified_from_snapshot_catalog_delta() -> None:
    result = evaluate_catalog_differential(
        change_type="new_program",
        previous_catalog=[_program("study", "Study Visa")],
        current_catalog=[
            _program("study", "Study Visa"),
            _program("talent", "Global Talent Visa"),
        ],
        missing_means_retired=False,
    )

    assert result.valid is True
    assert result.added_program_ids == ("talent",)
    assert result.reasons == ()


def test_program_retirement_is_verified_from_explicit_inactive_transition() -> None:
    result = evaluate_catalog_differential(
        change_type="program_removed",
        previous_catalog=[_program("legacy", "Legacy Route")],
        current_catalog=[_program("legacy", "Legacy Route", active=False)],
        missing_means_retired=False,
    )

    assert result.valid is True
    assert result.deactivated_program_ids == ("legacy",)
    assert result.removed_program_ids == ()


def test_program_absence_only_counts_when_source_contract_declares_retirement_semantics() -> None:
    unresolved = evaluate_catalog_differential(
        change_type="program_removed",
        previous_catalog=[_program("legacy", "Legacy Route")],
        current_catalog=[_program("study", "Study Visa")],
        missing_means_retired=False,
    )
    verified = evaluate_catalog_differential(
        change_type="program_removed",
        previous_catalog=[_program("legacy", "Legacy Route")],
        current_catalog=[_program("study", "Study Visa")],
        missing_means_retired=True,
    )

    assert unresolved.valid is False
    assert "program_absence_not_semantically_retired" in unresolved.reasons
    assert verified.valid is True
    assert verified.removed_program_ids == ("legacy",)


def test_duplicate_program_identity_blocks_machine_verification() -> None:
    result = evaluate_catalog_differential(
        change_type="new_program",
        previous_catalog=[_program("study", "Study Visa")],
        current_catalog=[
            _program("talent", "Global Talent Visa"),
            _program("talent", "Duplicate Talent Visa"),
        ],
        missing_means_retired=False,
    )

    assert result.valid is False
    assert "program_catalog_duplicate_identity" in result.reasons


def test_unsupported_interpretive_change_type_cannot_be_machine_verified() -> None:
    result = evaluate_catalog_differential(
        change_type="rule_change",
        previous_catalog=[_program("study", "Study Visa")],
        current_catalog=[_program("study", "Study Visa")],
        missing_means_retired=False,
    )

    assert result.valid is False
    assert result.reasons == ("unsupported_machine_verification_change_type",)


def test_database_verification_is_idempotent_and_never_changes_canonical_state(
    db_session: Session,
) -> None:
    jurisdiction = Jurisdiction(code="AT-RIA2", name="RI.A2 Test Jurisdiction")
    db_session.add(jurisdiction)
    db_session.commit()
    db_session.refresh(jurisdiction)

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="RI.A2 Test Jurisdiction",
        domain="visa",
        name="RI.A2 Official Program Catalog",
        url="https://example.invalid/programs.json",
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    previous = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="sha256:previous",
        status="changed",
        metadata_json=json.dumps({
            "parser_profile": "structured_program_catalog_v1",
            "program_catalog": [_program("study", "Study Visa")],
            "missing_means_retired": False,
        }),
    )
    db_session.add(previous)
    db_session.commit()
    db_session.refresh(previous)

    current = SourceSnapshot(
        official_source_id=source.id,
        previous_snapshot_id=previous.id,
        url=source.url,
        content_hash="sha256:current",
        status="changed",
        metadata_json=json.dumps({
            "parser_profile": "structured_program_catalog_v1",
            "program_catalog": [
                _program("study", "Study Visa"),
                _program("talent", "Global Talent Visa"),
            ],
            "missing_means_retired": False,
        }),
    )
    db_session.add(current)
    db_session.commit()
    db_session.refresh(current)

    change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        previous_snapshot_id=previous.id,
        current_snapshot_id=current.id,
        domain="visa",
        change_type="new_program",
        title="Global Talent Visa added",
        summary="Structured official catalog added the talent program.",
        materiality="medium",
        status="pending_review",
    )
    db_session.add(change)
    db_session.commit()
    db_session.refresh(change)

    record_audit(
        db_session,
        action="regulatory_autonomy_routed",
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "routing_version": ROUTING_VERSION,
            "route": "machine_verification_candidate",
            "machine_verification_candidate": True,
            "canonical_write_allowed": False,
            "reasons": [],
            "evidence": {"source_snapshot_id": str(current.id)},
        },
        actor="pytest-routing-agent",
        source=ROUTING_VERSION,
    )
    db_session.commit()

    first = verify_routed_regulatory_changes(db_session)
    second = verify_routed_regulatory_changes(db_session)

    audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == VERIFICATION_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
    ).all()
    persisted_change = db_session.get(RegulatoryChange, change.id)

    assert first["independently_verified"] == 1
    assert first["audit_writes"] == 1
    assert first["canonical_writes"] == 0
    assert second["independently_verified"] == 1
    assert second["audit_writes"] == 0
    assert second["canonical_writes"] == 0
    assert len(audits) == 1
    assert persisted_change is not None
    assert persisted_change.status == "pending_review"
    assert persisted_change.reviewed_at is None
    assert persisted_change.published_at is None

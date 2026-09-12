from __future__ import annotations

from sqlmodel import select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    RegulatoryChange,
    SourceSnapshot,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.regulatory_integrity_watchdog import WATCHDOG_ACTION, WATCHDOG_VERSION
from app.services.regulatory_reassessment_propagation import (
    PROPAGATION_ACTION,
    identify_reassessment_impact,
    propagate_regulatory_reassessment_impacts,
)


def _seed_integrity_clear_change(db_session):
    jurisdiction = Jurisdiction(code="AT", name="Austria")
    db_session.add(jurisdiction)
    db_session.flush()

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="visa",
        name="Austrian authority",
        url="https://example.gv.at/immigration",
    )
    db_session.add(source)
    db_session.flush()

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="a" * 64,
        status="changed",
        captured_at=now_utc(),
    )
    db_session.add(snapshot)
    db_session.flush()

    change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        current_snapshot_id=snapshot.id,
        domain="visa",
        change_type="new_program",
        title="New route",
        summary="A new route was independently verified.",
        materiality="medium",
        status="pending_review",
        detected_at=now_utc(),
    )
    db_session.add(change)
    db_session.flush()

    record_audit(
        db_session,
        action=WATCHDOG_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "watchdog_version": WATCHDOG_VERSION,
            "eligible_for_future_promotion": True,
            "canonical_write_allowed": False,
        },
        actor="pytest",
        source=WATCHDOG_VERSION,
    )
    db_session.commit()
    return jurisdiction, source, change


def _published_pathway(db_session, *, jurisdiction, source, key: str, domain: str = "study"):
    pathway = MobilityPathway(
        pathway_key=key,
        name=key.replace("-", " ").title(),
        country="Austria",
        domain=domain,
        jurisdiction_id=jurisdiction.id,
        catalogue_status="published",
    )
    db_session.add(pathway)
    db_session.flush()
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        official_source_id=source.id,
        published_at=now_utc(),
        approved_by="pytest-reviewer",
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    return pathway, version


def test_ri_a4_identifies_matching_published_pathway_without_mutating_it(db_session) -> None:
    jurisdiction, source, change = _seed_integrity_clear_change(db_session)
    _, matching = _published_pathway(
        db_session,
        jurisdiction=jurisdiction,
        source=source,
        key="at-study",
        domain="study",
    )
    _, unrelated = _published_pathway(
        db_session,
        jurisdiction=jurisdiction,
        source=source,
        key="at-scholarship",
        domain="scholarship",
    )

    before_matching_status = matching.lifecycle_status
    before_unrelated_status = unrelated.lifecycle_status
    result = identify_reassessment_impact(db_session, change)

    assert result.pathway_version_ids == (str(matching.id),)
    assert result.eligibility_revision_ids == ()
    assert result.reassessment_write_allowed is False
    assert result.canonical_write_allowed is False

    db_session.refresh(matching)
    db_session.refresh(unrelated)
    assert matching.lifecycle_status == before_matching_status
    assert unrelated.lifecycle_status == before_unrelated_status


def test_ri_a4_propagation_is_idempotent_and_writes_only_audit(db_session) -> None:
    jurisdiction, source, change = _seed_integrity_clear_change(db_session)
    _, matching = _published_pathway(
        db_session,
        jurisdiction=jurisdiction,
        source=source,
        key="at-work",
        domain="work",
    )

    first = propagate_regulatory_reassessment_impacts(db_session)
    second = propagate_regulatory_reassessment_impacts(db_session)

    audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == PROPAGATION_ACTION)
        .where(AuditLog.entity_id == str(change.id))
    ).all()

    assert first["pathway_candidates"] == 1
    assert first["reassessment_writes"] == 0
    assert first["canonical_writes"] == 0
    assert first["audit_writes"] == 1
    assert second["audit_writes"] == 0
    assert len(audits) == 1

    db_session.refresh(change)
    db_session.refresh(matching)
    assert change.status == "pending_review"
    assert change.reviewed_at is None
    assert change.published_at is None
    assert matching.lifecycle_status == "published"


def test_ri_a4_fanout_is_bounded(db_session) -> None:
    jurisdiction, source, change = _seed_integrity_clear_change(db_session)
    _, first = _published_pathway(
        db_session,
        jurisdiction=jurisdiction,
        source=source,
        key="at-study-1",
        domain="study",
    )
    _published_pathway(
        db_session,
        jurisdiction=jurisdiction,
        source=source,
        key="at-study-2",
        domain="study",
    )

    impact = identify_reassessment_impact(db_session, change, max_pathways=1)

    assert impact.pathway_version_ids == (str(first.id),)
    assert impact.fanout_limited is True
    assert "pathway_fanout_limit_reached" in impact.reasons
    assert impact.reassessment_write_allowed is False

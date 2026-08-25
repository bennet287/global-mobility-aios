from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    JurisdictionCoverageEvidenceBatch,
    JurisdictionImmigrationAssessment,
    JurisdictionRegistryEntry,
    JurisdictionRegistryRelease,
    JurisdictionSourceCertification,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    ShortageOccupationEntry,
    SourceMonitor,
    SourceSnapshot,
    VerifiedRule,
)
from app.services.pathway_evidence import pathway_version_evidence_rows
from scripts.prepare_austria_governed_source_review import (
    NATIONAL_URL,
    PATHWAY_KEY,
    PreparationBlocked,
    REGIONAL_URL,
    prepare_review_state,
)


NATIONAL_TEXT = """Austria-wide shortage occupations
For the year 2026, the following occupations are deemed shortage professions:
1. Test Engineers
Test engineer, Test technician
2. Test Nurses
Test nurse, Test clinical nurse
"""

REGIONAL_TEXT = """Regional shortage occupations
For the year 2026, the following occupations are deemed shortage professions:
1. Test Bakers (Wien)
Test baker, Test pastry baker
2. Test Tilers (Kärnten, Tirol)
Test tiler, Test wall tiler
"""


def _seed_austria_registry(session: Session) -> Jurisdiction:
    jurisdiction = Jurisdiction(
        code="AT",
        name="Austria",
        jurisdiction_type="country",
        region="Europe",
        active=True,
    )
    session.add(jurisdiction)
    session.flush()

    release = JurisdictionRegistryRelease(
        version="pytest-at-registry-v1",
        source_name="pytest registry",
        source_url="https://example.test/registry",
        source_sha256="a" * 64,
        expected_entries=1,
        imported_entries=1,
        status="active",
        released_by="pytest",
    )
    session.add(release)
    session.flush()

    session.add(
        JurisdictionRegistryEntry(
            registry_release_id=release.id,
            jurisdiction_id=jurisdiction.id,
            alpha2_code="AT",
            alpha3_code="AUT",
            m49_code="040",
            canonical_name="Austria",
            jurisdiction_type="country",
            membership_status="un_member",
            region="Europe",
            subregion="Western Europe",
            immigration_rule_status="unassessed",
            coverage_required=True,
            payload_sha256="b" * 64,
        )
    )
    session.commit()
    session.refresh(jurisdiction)
    return jurisdiction


def _fake_retrieval(session: Session, monitor_id):
    monitor = session.get(SourceMonitor, monitor_id)
    assert monitor is not None
    source = session.get(OfficialSource, monitor.official_source_id)
    assert source is not None

    existing = session.exec(
        select(SourceSnapshot)
        .where(SourceSnapshot.official_source_id == source.id)
        .order_by(SourceSnapshot.captured_at.desc())
    ).first()
    if existing is not None:
        return SimpleNamespace(status="unchanged", snapshot_id=existing.id)

    if source.url == NATIONAL_URL:
        content = NATIONAL_TEXT
    elif source.url == REGIONAL_URL:
        content = REGIONAL_TEXT
    else:  # pragma: no cover - defensive test guard
        raise AssertionError(f"Unexpected source URL: {source.url}")

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        content_text=content,
        http_status=200,
        retrieval_method="http",
        parser_version="pytest-v1",
        status="baseline",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return SimpleNamespace(status="baseline", snapshot_id=snapshot.id)


def test_prepare_review_state_creates_only_review_ready_draft(
    db_session: Session,
) -> None:
    jurisdiction = _seed_austria_registry(db_session)

    result = prepare_review_state(
        db_session,
        actor="pytest-preparer",
        expected_national_group_count=2,
        expected_regional_group_count=2,
        retrieval_executor=_fake_retrieval,
    )

    assert result["prepared_for_independent_human_review"] is True
    assert result["professional_review_required"] is True
    assert result["provider_invoked"] is False
    assert result["external_action_authorized"] is False
    assert result["pathway_published_by_this_operation"] is False
    assert result["verified_rule_published_by_this_operation"] is False
    assert result["pathway_publication_ready"] is False
    assert result["pathway_status"] == "draft"
    assert result["pathway_version_status"] == "draft"
    assert result["sources"]["national"]["entry_count"] == 2
    assert result["sources"]["regional"]["entry_count"] == 2

    pathway = db_session.exec(
        select(MobilityPathway).where(MobilityPathway.pathway_key == PATHWAY_KEY)
    ).one()
    version = db_session.exec(
        select(MobilityPathwayVersion).where(
            MobilityPathwayVersion.pathway_id == pathway.id
        )
    ).one()
    assert pathway.jurisdiction_id == jurisdiction.id
    assert pathway.catalogue_status == "draft"
    assert version.lifecycle_status == "draft"
    assert version.approved_by is None
    assert version.published_at is None

    evidence_roles = {
        row.evidence_role for row in pathway_version_evidence_rows(db_session, version)
    }
    assert evidence_roles == {
        "core_route",
        "national_occupation_list",
        "regional_occupation_list",
    }

    assessments = list(db_session.exec(select(JurisdictionImmigrationAssessment)).all())
    certifications = list(db_session.exec(select(JurisdictionSourceCertification)).all())
    rules = list(db_session.exec(select(VerifiedRule)).all())
    assert len(assessments) == 1
    assert assessments[0].status == "pending_review"
    assert len(certifications) == 1
    assert certifications[0].status == "pending_review"
    assert rules == []
    assert len(list(db_session.exec(select(OfficialSource)).all())) == 2
    assert len(list(db_session.exec(select(SourceMonitor)).all())) == 2
    assert len(list(db_session.exec(select(ShortageOccupationEntry)).all())) == 4
    assert len(list(db_session.exec(select(JurisdictionCoverageEvidenceBatch)).all())) == 1


def test_prepare_review_state_is_idempotent(
    db_session: Session,
) -> None:
    _seed_austria_registry(db_session)

    first = prepare_review_state(
        db_session,
        actor="pytest-preparer",
        expected_national_group_count=2,
        expected_regional_group_count=2,
        retrieval_executor=_fake_retrieval,
    )
    second = prepare_review_state(
        db_session,
        actor="pytest-preparer",
        expected_national_group_count=2,
        expected_regional_group_count=2,
        retrieval_executor=_fake_retrieval,
    )

    assert second["coverage_batch_created"] is False
    assert second["pathway_created"] is False
    assert second["coverage_batch_id"] == first["coverage_batch_id"]
    assert second["pathway_id"] == first["pathway_id"]
    assert second["pathway_version_id"] == first["pathway_version_id"]
    assert len(list(db_session.exec(select(OfficialSource)).all())) == 2
    assert len(list(db_session.exec(select(SourceMonitor)).all())) == 2
    assert len(list(db_session.exec(select(SourceSnapshot)).all())) == 2
    assert len(list(db_session.exec(select(ShortageOccupationEntry)).all())) == 4
    assert len(list(db_session.exec(select(JurisdictionSourceCertification)).all())) == 1
    assert len(list(db_session.exec(select(JurisdictionImmigrationAssessment)).all())) == 1
    assert len(list(db_session.exec(select(MobilityPathwayVersion)).all())) == 1


def test_prepare_review_state_retrieval_failure_stops_before_truth_draft(
    db_session: Session,
) -> None:
    _seed_austria_registry(db_session)

    def failing_retrieval(session: Session, monitor_id):
        monitor = session.get(SourceMonitor, monitor_id)
        assert monitor is not None
        source = session.get(OfficialSource, monitor.official_source_id)
        assert source is not None
        if source.url == REGIONAL_URL:
            raise RuntimeError("pytest regional retrieval failure")
        return _fake_retrieval(session, monitor_id)

    with pytest.raises(RuntimeError, match="regional retrieval failure"):
        prepare_review_state(
            db_session,
            actor="pytest-preparer",
            expected_national_group_count=2,
            expected_regional_group_count=2,
            retrieval_executor=failing_retrieval,
        )

    assert list(db_session.exec(select(MobilityPathway)).all()) == []
    assert list(db_session.exec(select(ShortageOccupationEntry)).all()) == []
    assert list(db_session.exec(select(JurisdictionCoverageEvidenceBatch)).all()) == []
    assert list(db_session.exec(select(JurisdictionSourceCertification)).all()) == []
    assert list(db_session.exec(select(JurisdictionImmigrationAssessment)).all()) == []


def test_prepare_review_state_requires_governed_registry_before_mutation(
    db_session: Session,
) -> None:
    with pytest.raises(
        PreparationBlocked,
        match="active_jurisdiction_registry_release_missing",
    ):
        prepare_review_state(
            db_session,
            actor="pytest-preparer",
            expected_national_group_count=2,
            expected_regional_group_count=2,
            retrieval_executor=_fake_retrieval,
        )

    assert list(db_session.exec(select(OfficialSource)).all()) == []
    assert list(db_session.exec(select(MobilityPathway)).all()) == []

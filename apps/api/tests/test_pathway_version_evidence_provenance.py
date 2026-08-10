from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.domain import (
    Jurisdiction,
    JurisdictionSourceCertification,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.pathway_catalogue import (
    _risk_explanation,
    pathway_version_read,
)
from app.services.pathway_evidence import pathway_version_evidence_rows
from app.services.pathway_regulatory_impacts import _candidate_versions


def _source_snapshot_rule(
    session: Session,
    *,
    jurisdiction: Jurisdiction,
    suffix: str,
) -> tuple[OfficialSource, SourceSnapshot, VerifiedRule]:
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="germany",
        domain="work",
        name=f"Germany skilled work {suffix}",
        url=f"https://example.gov.de/skilled-work/{suffix}",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=f"pathway-{suffix}-snapshot",
        content_text=f"Reviewed skilled work evidence for {suffix}.",
        retrieval_method="http",
        status="captured",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    rule = VerifiedRule(
        country="germany",
        domain="work",
        rule_key=f"de-skilled-work-{suffix}",
        statement=f"Reviewed skilled work rule for {suffix}.",
        official_source_id=source.id,
        jurisdiction_id=jurisdiction.id,
        source_snapshot_id=snapshot.id,
        confidence=0.98,
        active=True,
        approved_by=f"pytest-{suffix}-reviewer",
        published_at=now_utc(),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return source, snapshot, rule


def _jurisdiction(session: Session) -> Jurisdiction:
    jurisdiction = Jurisdiction(code="DE", name="Germany", region="Europe")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)
    return jurisdiction


def _approved_supplemental_certification(
    session: Session,
    *,
    jurisdiction: Jurisdiction,
    source: OfficialSource,
) -> JurisdictionSourceCertification:
    certification = JurisdictionSourceCertification(
        jurisdiction_id=jurisdiction.id,
        registry_entry_id=uuid4(),
        regulatory_authority_id=uuid4(),
        official_source_id=source.id,
        certification_version=1,
        certification_scope="supplemental_work",
        coverage_domains_json='["work"]',
        evidence_notes="Pytest approved supplemental source evidence.",
        status="approved",
        proposed_by="pytest-certification-proposer",
        reviewed_by="pytest-certification-reviewer",
        reviewed_at=now_utc(),
        review_notes="Independent test review completed.",
    )
    session.add(certification)
    session.commit()
    session.refresh(certification)
    return certification


def test_multi_source_pathway_publication_requires_certified_required_supplemental_evidence(
    client: TestClient,
    db_session: Session,
) -> None:
    jurisdiction = _jurisdiction(db_session)
    core_source, core_snapshot, core_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="core",
    )
    supplemental_source, supplemental_snapshot, supplemental_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="occupation-list",
    )

    created = client.post(
        "/api/v1/pathways",
        json={
            "pathway_key": "de-skilled-worker-multi-source",
            "name": "Germany Skilled Worker Multi-source Pathway",
            "country": "Germany",
            "domain": "work",
            "jurisdiction_id": str(jurisdiction.id),
            "description": "Multi-source pathway provenance fixture.",
            "official_source_id": str(core_source.id),
            "source_snapshot_id": str(core_snapshot.id),
            "evidence_links": [
                {
                    "evidence_role": "national_occupation_list",
                    "official_source_id": str(supplemental_source.id),
                    "source_snapshot_id": str(supplemental_snapshot.id),
                    "required_for_publication": True,
                    "metadata": {"year": 2026, "scope": "national"},
                }
            ],
            "verified_rule_ids": [str(core_rule.id), str(supplemental_rule.id)],
            "eligibility_criteria": {},
            "required_documents": ["passport"],
            "costs": {"currency": "EUR"},
            "processing_time": {},
            "benefits": [],
            "risks": [],
        },
    )
    assert created.status_code == 201, created.text
    version = created.json()["current_version"]
    assert version["official_source_id"] == str(core_source.id)
    assert version["source_snapshot_id"] == str(core_snapshot.id)
    assert {item["evidence_role"] for item in version["evidence_links"]} == {
        "core_route",
        "national_occupation_list",
    }

    blocked = client.post(
        f"/api/v1/pathways/versions/{version['id']}/publish",
        json={"review_notes": "Reviewed all declared evidence."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert blocked.status_code == 400, blocked.text
    assert "approved source certification" in blocked.json()["detail"].lower()

    _approved_supplemental_certification(
        db_session,
        jurisdiction=jurisdiction,
        source=supplemental_source,
    )
    published = client.post(
        f"/api/v1/pathways/versions/{version['id']}/publish",
        json={"review_notes": "Reviewed all declared multi-source evidence."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert published.status_code == 200, published.text
    assert published.json()["current_version"]["lifecycle_status"] == "published"


def test_pathway_publication_rejects_rule_provenance_not_declared_by_version(
    client: TestClient,
    db_session: Session,
) -> None:
    jurisdiction = _jurisdiction(db_session)
    core_source, core_snapshot, core_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="declared-core",
    )
    _, _, undeclared_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="undeclared",
    )
    created = client.post(
        "/api/v1/pathways",
        json={
            "pathway_key": "de-undeclared-rule-provenance",
            "name": "Germany Undeclared Rule Provenance",
            "country": "Germany",
            "domain": "work",
            "jurisdiction_id": str(jurisdiction.id),
            "official_source_id": str(core_source.id),
            "source_snapshot_id": str(core_snapshot.id),
            "verified_rule_ids": [str(core_rule.id), str(undeclared_rule.id)],
        },
    )
    assert created.status_code == 201, created.text
    version_id = created.json()["current_version"]["id"]
    blocked = client.post(
        f"/api/v1/pathways/versions/{version_id}/publish",
        json={"review_notes": "Attempted publication with undeclared rule provenance."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert blocked.status_code == 400, blocked.text
    assert "not declared" in blocked.json()["detail"].lower()


def test_legacy_single_source_version_has_core_route_fallback(db_session: Session) -> None:
    jurisdiction = _jurisdiction(db_session)
    source, snapshot, _ = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="legacy",
    )
    pathway = MobilityPathway(
        pathway_key="de-legacy-fallback",
        name="Germany Legacy Fallback",
        country="germany",
        domain="work",
        jurisdiction_id=jurisdiction.id,
        catalogue_status="draft",
        created_by="pytest",
    )
    db_session.add(pathway)
    db_session.commit()
    db_session.refresh(pathway)
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        created_by="pytest",
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)

    rows = pathway_version_evidence_rows(db_session, version)
    assert len(rows) == 1
    assert rows[0].evidence_role == "core_route"
    assert rows[0].official_source_id == source.id
    assert rows[0].source_snapshot_id == snapshot.id


def test_risk_analysis_checks_every_pathway_evidence_link(db_session: Session) -> None:
    jurisdiction = _jurisdiction(db_session)
    core_source, core_snapshot, core_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="risk-core",
    )
    supporting_source, supporting_snapshot, _ = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="risk-supporting",
    )
    supporting_snapshot.captured_at = now_utc() - timedelta(days=220)
    db_session.add(supporting_snapshot)
    db_session.commit()

    pathway = MobilityPathway(
        pathway_key="de-risk-multi-source",
        name="Germany Risk Multi-source",
        country="germany",
        domain="work",
        jurisdiction_id=jurisdiction.id,
        catalogue_status="active",
        created_by="pytest",
    )
    db_session.add(pathway)
    db_session.commit()
    db_session.refresh(pathway)
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        official_source_id=core_source.id,
        source_snapshot_id=core_snapshot.id,
        verified_rule_ids_json=f'["{core_rule.id}"]',
        approved_by="pytest-reviewer",
        published_at=now_utc(),
        created_by="pytest",
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    db_session.add(
        MobilityPathwayVersionEvidence(
            pathway_version_id=version.id,
            evidence_role="supporting",
            official_source_id=supporting_source.id,
            source_snapshot_id=supporting_snapshot.id,
            required_for_publication=False,
            metadata_json="{}",
        )
    )
    db_session.commit()

    read = pathway_version_read(db_session, version)
    risk = _risk_explanation(db_session, read, [])
    assert any(
        "supporting snapshot is 220 days old" in message
        for message in risk.regulatory_risks
    )


def test_regulatory_impact_source_match_uses_any_declared_evidence_source(
    db_session: Session,
) -> None:
    jurisdiction = _jurisdiction(db_session)
    core_source, core_snapshot, _ = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="impact-core",
    )
    supplemental_source, supplemental_snapshot, supplemental_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="impact-supplemental",
    )
    pathway = MobilityPathway(
        pathway_key="de-impact-evidence-source",
        name="Germany Impact Evidence Source",
        country="germany",
        domain="work",
        jurisdiction_id=jurisdiction.id,
        catalogue_status="active",
        created_by="pytest",
    )
    db_session.add(pathway)
    db_session.commit()
    db_session.refresh(pathway)
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        official_source_id=core_source.id,
        source_snapshot_id=core_snapshot.id,
        verified_rule_ids_json="[]",
        approved_by="pytest-reviewer",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        created_by="pytest",
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    db_session.add(
        MobilityPathwayVersionEvidence(
            pathway_version_id=version.id,
            evidence_role="national_occupation_list",
            official_source_id=supplemental_source.id,
            source_snapshot_id=supplemental_snapshot.id,
            required_for_publication=True,
            metadata_json='{"year": 2026}',
        )
    )
    db_session.commit()

    candidates = _candidate_versions(
        db_session,
        supplemental_rule,
        event_at=now_utc(),
    )
    assert len(candidates) == 1
    _, _, match_basis = candidates[0]
    assert "official_source_match" in match_basis


def test_non_core_rule_provenance_cannot_be_marked_optional_to_bypass_certification(
    client: TestClient,
    db_session: Session,
) -> None:
    jurisdiction = _jurisdiction(db_session)
    core_source, core_snapshot, core_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="optional-core",
    )
    supplemental_source, supplemental_snapshot, supplemental_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="optional-supplemental",
    )
    created = client.post(
        "/api/v1/pathways",
        json={
            "pathway_key": "de-optional-rule-provenance",
            "name": "Germany Optional Rule Provenance",
            "country": "Germany",
            "domain": "work",
            "jurisdiction_id": str(jurisdiction.id),
            "official_source_id": str(core_source.id),
            "source_snapshot_id": str(core_snapshot.id),
            "evidence_links": [
                {
                    "evidence_role": "supporting",
                    "official_source_id": str(supplemental_source.id),
                    "source_snapshot_id": str(supplemental_snapshot.id),
                    "required_for_publication": False,
                }
            ],
            "verified_rule_ids": [str(core_rule.id), str(supplemental_rule.id)],
        },
    )
    assert created.status_code == 201, created.text
    blocked = client.post(
        f"/api/v1/pathways/versions/{created.json()['current_version']['id']}/publish",
        json={"review_notes": "Optional evidence must not bypass governance."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert blocked.status_code == 400, blocked.text
    assert "must be required for publication" in blocked.json()["detail"].lower()


def test_core_source_with_pending_certification_history_is_not_publishable(
    client: TestClient,
    db_session: Session,
) -> None:
    jurisdiction = _jurisdiction(db_session)
    core_source, core_snapshot, core_rule = _source_snapshot_rule(
        db_session,
        jurisdiction=jurisdiction,
        suffix="pending-core",
    )
    db_session.add(
        JurisdictionSourceCertification(
            jurisdiction_id=jurisdiction.id,
            registry_entry_id=uuid4(),
            regulatory_authority_id=uuid4(),
            official_source_id=core_source.id,
            certification_version=1,
            certification_scope="supplemental_work",
            coverage_domains_json='["work"]',
            evidence_notes="Pending certification fixture.",
            status="pending_review",
            proposed_by="pytest-certification-proposer",
        )
    )
    db_session.commit()

    created = client.post(
        "/api/v1/pathways",
        json={
            "pathway_key": "de-pending-core-certification",
            "name": "Germany Pending Core Certification",
            "country": "Germany",
            "domain": "work",
            "jurisdiction_id": str(jurisdiction.id),
            "official_source_id": str(core_source.id),
            "source_snapshot_id": str(core_snapshot.id),
            "verified_rule_ids": [str(core_rule.id)],
        },
    )
    assert created.status_code == 201, created.text
    blocked = client.post(
        f"/api/v1/pathways/versions/{created.json()['current_version']['id']}/publish",
        json={"review_notes": "Pending source certification must remain held."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert blocked.status_code == 400, blocked.text
    assert "no approved source certification" in blocked.json()["detail"].lower()


def test_0070_migration_backfills_core_route_and_chains_from_0069() -> None:
    root = Path(__file__).resolve().parents[3]
    migration = (
        root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0070_pathway_version_evidence_provenance.py"
    ).read_text(encoding="utf-8")

    assert 'down_revision = "0069_source_certification_multiplicity"' in migration
    assert "mobility_pathway_version_evidence" in migration
    assert "uq_pathway_version_evidence_identity" in migration
    assert "'core_route'" in migration
    assert "FROM mobility_pathway_versions" in migration

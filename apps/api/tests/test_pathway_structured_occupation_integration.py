from __future__ import annotations

import hashlib
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    JurisdictionSourceCertification,
    MobilityPathwayVersion,
    OfficialSource,
    ShortageOccupationEntry,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.shortage_occupations import shortage_occupation_projection_summary


def _source_snapshot(
    session: Session,
    *,
    jurisdiction: Jurisdiction,
    name: str,
    url: str,
) -> tuple[OfficialSource, SourceSnapshot]:
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="austria",
        domain="visa",
        name=name,
        url=url,
        source_type="official_portal",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=hashlib.sha256(f"snapshot:{name}".encode()).hexdigest(),
        content_text=f"Immutable official evidence for {name}.",
        retrieval_method="http",
        status="captured",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return source, snapshot


def _structured_entries(
    session: Session,
    *,
    jurisdiction: Jurisdiction,
    source: OfficialSource,
    snapshot: SourceSnapshot,
    scope: str,
    count: int,
) -> dict:
    for ordinal in range(1, count + 1):
        entry_hash = hashlib.sha256(
            f"{snapshot.id}:{scope}:{ordinal}".encode("utf-8")
        ).hexdigest()
        session.add(
            ShortageOccupationEntry(
                jurisdiction_id=jurisdiction.id,
                official_source_id=source.id,
                source_snapshot_id=snapshot.id,
                year=2026,
                scope=scope,
                source_ordinal=ordinal,
                occupation_group=f"{scope.title()} occupation group {ordinal}",
                normalized_occupation_group=f"{scope} occupation group {ordinal}",
                occupation_aliases_json=f'["{scope} occupation alias {ordinal}"]',
                province_codes_json='["AT-9"]' if scope == "regional" else "[]",
                province_names_json='["Wien"]' if scope == "regional" else "[]",
                extraction_version="austria_migration_shortage_v1",
                entry_sha256=entry_hash,
                metadata_json='{"derived_from_immutable_snapshot": true}',
            )
        )
    session.commit()
    return shortage_occupation_projection_summary(
        session,
        source_snapshot_id=snapshot.id,
        year=2026,
        scope=scope,
    )


def _pending_certification(
    session: Session,
    *,
    jurisdiction: Jurisdiction,
    source: OfficialSource,
    version: int,
) -> JurisdictionSourceCertification:
    row = JurisdictionSourceCertification(
        jurisdiction_id=jurisdiction.id,
        registry_entry_id=uuid4(),
        regulatory_authority_id=uuid4(),
        official_source_id=source.id,
        certification_version=version,
        certification_scope="supplemental_visa",
        coverage_domains_json='["visa"]',
        evidence_notes="Pytest pending source review.",
        status="pending_review",
        proposed_by="pytest-certification-proposer",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _approve(row: JurisdictionSourceCertification, session: Session) -> None:
    row.status = "approved"
    row.reviewed_by = "pytest-independent-source-reviewer"
    row.reviewed_at = now_utc()
    row.review_notes = "Synthetic independent source-review fixture approved."
    session.add(row)
    session.commit()


def _fixture(client: TestClient, session: Session) -> dict:
    jurisdiction = Jurisdiction(code="AT", name="Austria", region="Europe")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)

    core_source, core_snapshot = _source_snapshot(
        session,
        jurisdiction=jurisdiction,
        name="Austria skilled-worker core route",
        url="https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/skilled-workers-in-shortage-occupations/",
    )
    core_rule = VerifiedRule(
        country="austria",
        domain="visa",
        rule_key="at-skilled-worker-core-test",
        statement="Applicants must satisfy the published skilled-worker route requirements.",
        official_source_id=core_source.id,
        jurisdiction_id=jurisdiction.id,
        source_snapshot_id=core_snapshot.id,
        confidence=0.98,
        active=True,
        approved_by="pytest-rule-reviewer",
        published_at=now_utc(),
    )
    session.add(core_rule)
    session.commit()
    session.refresh(core_rule)

    national_source, national_snapshot = _source_snapshot(
        session,
        jurisdiction=jurisdiction,
        name="Austria 2026 national shortage occupations",
        url="https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/austria-wide-shortage-occupations/",
    )
    regional_source, regional_snapshot = _source_snapshot(
        session,
        jurisdiction=jurisdiction,
        name="Austria 2026 regional shortage occupations",
        url="https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/regional-shortage-occupations/",
    )
    national_summary = _structured_entries(
        session,
        jurisdiction=jurisdiction,
        source=national_source,
        snapshot=national_snapshot,
        scope="national",
        count=2,
    )
    regional_summary = _structured_entries(
        session,
        jurisdiction=jurisdiction,
        source=regional_source,
        snapshot=regional_snapshot,
        scope="regional",
        count=3,
    )
    national_cert = _pending_certification(
        session,
        jurisdiction=jurisdiction,
        source=national_source,
        version=2,
    )
    regional_cert = _pending_certification(
        session,
        jurisdiction=jurisdiction,
        source=regional_source,
        version=1,
    )

    created = client.post(
        "/api/v1/pathways",
        json={
            "pathway_key": "at-rwr-skilled-worker-shortage-occupation",
            "name": "Austria Skilled Worker Structured Integration",
            "country": "Austria",
            "domain": "visa",
            "jurisdiction_id": str(jurisdiction.id),
            "official_source_id": str(core_source.id),
            "source_snapshot_id": str(core_snapshot.id),
            "verified_rule_ids": [str(core_rule.id)],
            "required_documents": ["passport"],
            "metadata": {
                "current_shortage_list_verified": False,
                "external_validation_gate": "held",
            },
        },
    )
    assert created.status_code == 201, created.text
    pathway = created.json()

    integration_payload = {
        "source_version_id": pathway["current_version"]["id"],
        "year": 2026,
        "national_source_snapshot_id": str(national_snapshot.id),
        "regional_source_snapshot_id": str(regional_snapshot.id),
        "expected_national_entry_count": national_summary["entry_count"],
        "expected_regional_entry_count": regional_summary["entry_count"],
        "expected_national_entry_set_sha256": national_summary["entry_set_sha256"],
        "expected_regional_entry_set_sha256": regional_summary["entry_set_sha256"],
        "expected_national_snapshot_content_hash": national_summary["source_snapshot_content_hash"],
        "expected_regional_snapshot_content_hash": regional_summary["source_snapshot_content_hash"],
    }
    return {
        "jurisdiction": jurisdiction,
        "pathway": pathway,
        "integration_payload": integration_payload,
        "national_summary": national_summary,
        "regional_summary": regional_summary,
        "national_cert": national_cert,
        "regional_cert": regional_cert,
    }


def test_structured_occupation_integration_creates_idempotent_draft_and_holds_publication(
    client: TestClient,
    db_session: Session,
) -> None:
    fixture = _fixture(client, db_session)
    pathway_id = UUID(fixture["pathway"]["id"])

    source_readiness = client.get(
        f"/api/v1/pathways/versions/{fixture['pathway']['current_version']['id']}/publication-readiness"
    )
    assert source_readiness.status_code == 200, source_readiness.text
    assert source_readiness.json()["ready"] is False
    assert "requires structured evidence roles" in " ".join(source_readiness.json()["blockers"]).lower()
    legacy_publish = client.post(
        f"/api/v1/pathways/versions/{fixture['pathway']['current_version']['id']}/publish",
        json={"review_notes": "Historical core-only draft must remain held."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert legacy_publish.status_code == 400, legacy_publish.text
    assert "requires structured evidence roles" in legacy_publish.json()["detail"].lower()

    response = client.post(
        f"/api/v1/pathways/{pathway_id}/structured-occupation-draft",
        json=fixture["integration_payload"],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["created"] is True
    version = body["pathway_version"]
    assert version["version_number"] == 2
    assert version["lifecycle_status"] == "draft"
    assert version["supersedes_version_id"] == fixture["integration_payload"]["source_version_id"]

    evidence = {row["evidence_role"]: row for row in version["evidence_links"]}
    assert set(evidence) == {
        "core_route",
        "national_occupation_list",
        "regional_occupation_list",
    }
    for role, summary in (
        ("national_occupation_list", fixture["national_summary"]),
        ("regional_occupation_list", fixture["regional_summary"]),
    ):
        metadata = evidence[role]["metadata"]
        assert evidence[role]["required_for_publication"] is True
        assert metadata["projection_type"] == "structured_shortage_occupation"
        assert metadata["entry_count"] == summary["entry_count"]
        assert metadata["entry_set_sha256"] == summary["entry_set_sha256"]
        assert metadata["source_snapshot_content_hash"] == summary["source_snapshot_content_hash"]

    readiness = body["publication_readiness"]
    assert readiness["ready"] is False
    assert readiness["requires_independent_reviewer"] is True
    assert readiness["evidence_certification_statuses"]["national_occupation_list"] == "pending_review"
    assert readiness["evidence_certification_statuses"]["regional_occupation_list"] == "pending_review"
    assert "approved source certification" in " ".join(readiness["blockers"]).lower()

    again = client.post(
        f"/api/v1/pathways/{pathway_id}/structured-occupation-draft",
        json=fixture["integration_payload"],
    )
    assert again.status_code == 201, again.text
    assert again.json()["created"] is False
    assert again.json()["pathway_version"]["id"] == version["id"]
    versions = list(
        db_session.exec(
            select(MobilityPathwayVersion).where(MobilityPathwayVersion.pathway_id == pathway_id)
        ).all()
    )
    assert len(versions) == 2

    blocked = client.post(
        f"/api/v1/pathways/versions/{version['id']}/publish",
        json={"review_notes": "Attempted publication while source certification is pending."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert blocked.status_code == 400, blocked.text
    assert "approved source certification" in blocked.json()["detail"].lower()


def test_structured_occupation_integration_rejects_operator_pinned_hash_mismatch(
    client: TestClient,
    db_session: Session,
) -> None:
    fixture = _fixture(client, db_session)
    pathway_id = UUID(fixture["pathway"]["id"])
    payload = dict(fixture["integration_payload"])
    payload["expected_national_entry_set_sha256"] = "0" * 64

    response = client.post(
        f"/api/v1/pathways/{pathway_id}/structured-occupation-draft",
        json=payload,
    )
    assert response.status_code == 400, response.text
    assert "operator-pinned national entry-set hash" in response.json()["detail"].lower()
    versions = list(
        db_session.exec(
            select(MobilityPathwayVersion).where(MobilityPathwayVersion.pathway_id == pathway_id)
        ).all()
    )
    assert len(versions) == 1


def test_direct_structured_occupation_role_requires_canonical_projection_metadata(
    client: TestClient,
    db_session: Session,
) -> None:
    fixture = _fixture(client, db_session)
    source_version = fixture["pathway"]["current_version"]
    national = fixture["national_summary"]

    response = client.post(
        f"/api/v1/pathways/{fixture['pathway']['id']}/versions",
        json={
            "official_source_id": source_version["official_source_id"],
            "source_snapshot_id": source_version["source_snapshot_id"],
            "evidence_links": [
                {
                    "evidence_role": "national_occupation_list",
                    "official_source_id": str(national["official_source_id"]),
                    "source_snapshot_id": str(national["source_snapshot_id"]),
                    "required_for_publication": True,
                    "metadata": {"year": 2026, "scope": "national"},
                }
            ],
            "verified_rule_ids": source_version["verified_rule_ids"],
        },
    )
    assert response.status_code == 400, response.text
    assert "projection_type" in response.json()["detail"]



def test_structured_occupation_evidence_cannot_be_optional(
    client: TestClient,
    db_session: Session,
) -> None:
    fixture = _fixture(client, db_session)
    source_version = fixture["pathway"]["current_version"]
    summary = fixture["national_summary"]

    response = client.post(
        f"/api/v1/pathways/{fixture['pathway']['id']}/versions",
        json={
            "official_source_id": source_version["official_source_id"],
            "source_snapshot_id": source_version["source_snapshot_id"],
            "evidence_links": [
                {
                    "evidence_role": "national_occupation_list",
                    "official_source_id": str(summary["official_source_id"]),
                    "source_snapshot_id": str(summary["source_snapshot_id"]),
                    "required_for_publication": False,
                    "metadata": {
                        "projection_type": "structured_shortage_occupation",
                        "year": 2026,
                        "scope": "national",
                        "entry_count": summary["entry_count"],
                        "entry_set_sha256": summary["entry_set_sha256"],
                        "extraction_version": summary["extraction_version"],
                        "source_snapshot_content_hash": summary["source_snapshot_content_hash"],
                    },
                }
            ],
            "verified_rule_ids": source_version["verified_rule_ids"],
        },
    )
    assert response.status_code == 400, response.text
    assert "must be required for publication" in response.json()["detail"].lower()

def test_publication_readiness_opens_only_after_both_synthetic_source_certifications_are_approved(
    client: TestClient,
    db_session: Session,
) -> None:
    fixture = _fixture(client, db_session)
    pathway_id = UUID(fixture["pathway"]["id"])
    integrated = client.post(
        f"/api/v1/pathways/{pathway_id}/structured-occupation-draft",
        json=fixture["integration_payload"],
    )
    assert integrated.status_code == 201, integrated.text
    version_id = integrated.json()["pathway_version"]["id"]

    _approve(fixture["national_cert"], db_session)
    still_held = client.get(f"/api/v1/pathways/versions/{version_id}/publication-readiness")
    assert still_held.status_code == 200, still_held.text
    assert still_held.json()["ready"] is False
    assert still_held.json()["evidence_certification_statuses"]["national_occupation_list"] == "approved"
    assert still_held.json()["evidence_certification_statuses"]["regional_occupation_list"] == "pending_review"

    _approve(fixture["regional_cert"], db_session)
    ready = client.get(f"/api/v1/pathways/versions/{version_id}/publication-readiness")
    assert ready.status_code == 200, ready.text
    assert ready.json()["ready"] is True
    assert ready.json()["blockers"] == []

    published = client.post(
        f"/api/v1/pathways/versions/{version_id}/publish",
        json={"review_notes": "Synthetic pathway review after both source certifications were approved."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert published.status_code == 200, published.text
    assert published.json()["current_version"]["lifecycle_status"] == "published"


def test_structured_occupation_integration_rejects_stale_source_version_branch(
    client: TestClient,
    db_session: Session,
) -> None:
    fixture = _fixture(client, db_session)
    pathway_id = UUID(fixture["pathway"]["id"])
    source_version = fixture["pathway"]["current_version"]

    extra = client.post(
        f"/api/v1/pathways/{pathway_id}/versions",
        json={
            "official_source_id": source_version["official_source_id"],
            "source_snapshot_id": source_version["source_snapshot_id"],
            "verified_rule_ids": source_version["verified_rule_ids"],
            "metadata": {"purpose": "newer draft fixture"},
        },
    )
    assert extra.status_code == 201, extra.text

    response = client.post(
        f"/api/v1/pathways/{pathway_id}/structured-occupation-draft",
        json=fixture["integration_payload"],
    )
    assert response.status_code == 400, response.text
    assert "not the current latest version" in response.json()["detail"].lower()

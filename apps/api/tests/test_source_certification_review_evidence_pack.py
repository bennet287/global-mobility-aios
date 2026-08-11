import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    JurisdictionSourceCertification,
    OfficialSource,
    RegulatoryAuthority,
    ShortageOccupationEntry,
    SourceSnapshot,
    now_utc,
)
from app.services.jurisdiction_registry import review_source_certification
from app.services.source_certification_review import (
    source_certification_review_pack,
    source_certification_review_queue,
    source_certification_review_workspace,
)


def _structured_certification_fixture(session: Session, *, entries: int = 2):
    jurisdiction = Jurisdiction(code="AT", name="Austria", region="Europe")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)

    authority = RegulatoryAuthority(
        jurisdiction_id=jurisdiction.id,
        name="Federal Ministry of the Interior",
        authority_type="immigration_authority",
        website_url="https://www.bmi.gv.at/",
        domains_json='["visa"]',
        active=True,
    )
    session.add(authority)
    session.commit()
    session.refresh(authority)

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        regulatory_authority_id=authority.id,
        country="austria",
        domain="visa",
        name="Austria 2026 shortage occupations",
        url="https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/austria-wide-shortage-occupations/",
        source_type="official_portal",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="a" * 64,
        content_text="Shortage occupations for the year 2026\n1. Engineers\n2. Technicians",
        http_status=200,
        retrieval_method="http",
        parser_version="austria_migration_shortage_v1",
        status="captured",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    for ordinal in range(1, entries + 1):
        session.add(
            ShortageOccupationEntry(
                jurisdiction_id=jurisdiction.id,
                official_source_id=source.id,
                source_snapshot_id=snapshot.id,
                year=2026,
                scope="national",
                source_ordinal=ordinal,
                occupation_group=f"Group {ordinal}",
                normalized_occupation_group=f"group {ordinal}",
                occupation_aliases_json=json.dumps([f"Alias {ordinal}"]),
                province_codes_json="[]",
                province_names_json="[]",
                extraction_version="austria_migration_shortage_v1",
                entry_sha256=f"{ordinal:064x}",
                metadata_json='{"derived_from_immutable_snapshot": true}',
            )
        )
    session.commit()

    certification = JurisdictionSourceCertification(
        jurisdiction_id=jurisdiction.id,
        registry_entry_id=uuid4(),
        regulatory_authority_id=authority.id,
        official_source_id=source.id,
        certification_version=1,
        certification_scope="supplemental_visa",
        coverage_domains_json='["visa"]',
        evidence_notes="Review the immutable 2026 shortage-occupation evidence.",
        status="pending_review",
        proposed_by="pytest-source-proposer",
    )
    session.add(certification)
    session.commit()
    session.refresh(certification)

    return jurisdiction, authority, source, snapshot, certification


def test_structured_source_review_pack_is_deterministic_and_complete(db_session: Session) -> None:
    _, _, source, snapshot, certification = _structured_certification_fixture(db_session)

    first = source_certification_review_pack(db_session, certification.id)
    second = source_certification_review_pack(db_session, certification.id)

    assert first.evidence_pack_sha256 == second.evidence_pack_sha256
    assert len(first.evidence_pack_sha256) == 64
    assert first.official_source["id"] == str(source.id)
    assert first.source_snapshot["id"] == str(snapshot.id)
    assert len(first.source_snapshot["content_text_sha256"]) == 64
    assert first.structured_projection["year"] == 2026
    assert first.structured_projection["scope"] == "national"
    assert first.structured_projection["entry_count"] == 2
    assert len(first.structured_entries) == 2
    assert first.structured_entries[0]["normalized_occupation_group"] == "group 1"
    assert first.source_content_text.startswith("Shortage occupations for the year 2026")
    assert any("personally reviewed" in item for item in first.review_checklist)


def test_structured_review_requires_attestation_and_exact_pack_hash(db_session: Session) -> None:
    _, _, _, snapshot, certification = _structured_certification_fixture(db_session)
    pack = source_certification_review_pack(db_session, certification.id)

    with pytest.raises(ValueError, match="Independent-human attestation"):
        review_source_certification(
            db_session,
            certification_id=certification.id,
            decision="approved",
            notes="Reviewed the structured source evidence.",
            actor="pytest-independent-reviewer",
        )

    with pytest.raises(ValueError, match="does not match"):
        review_source_certification(
            db_session,
            certification_id=certification.id,
            decision="approved",
            notes="Reviewed the structured source evidence.",
            actor="pytest-independent-reviewer",
            independent_human_attestation=True,
            evidence_pack_sha256="0" * 64,
            source_snapshot_id=snapshot.id,
        )

    approved = review_source_certification(
        db_session,
        certification_id=certification.id,
        decision="approved",
        notes="Personally compared every structured group with the immutable source snapshot.",
        actor="pytest-independent-reviewer",
        independent_human_attestation=True,
        evidence_pack_sha256=pack.evidence_pack_sha256,
        source_snapshot_id=snapshot.id,
    )
    assert approved.status == "approved"
    assert approved.reviewed_by == "pytest-independent-reviewer"

    audit = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == "jurisdiction_source_certification_reviewed")
        .order_by(AuditLog.created_at.desc())
    ).first()
    assert audit is not None
    payload = json.loads(audit.after_state_json or "{}")
    assert payload["review_evidence"]["independent_human_attestation"] is True
    assert payload["review_evidence"]["evidence_pack_sha256"] == pack.evidence_pack_sha256
    assert payload["review_evidence"]["source_snapshot_id"] == str(snapshot.id)


def test_structured_review_identity_separation_is_case_insensitive(db_session: Session) -> None:
    _, _, _, snapshot, certification = _structured_certification_fixture(db_session)
    pack = source_certification_review_pack(db_session, certification.id)

    with pytest.raises(ValueError, match="different from the proposer"):
        review_source_certification(
            db_session,
            certification_id=certification.id,
            decision="rejected",
            notes="Reviewer identity must remain independent.",
            actor="PYTEST-SOURCE-PROPOSER",
            independent_human_attestation=True,
            evidence_pack_sha256=pack.evidence_pack_sha256,
            source_snapshot_id=snapshot.id,
        )


def test_multiple_structured_projections_require_snapshot_pin(db_session: Session) -> None:
    jurisdiction, _, source, snapshot, certification = _structured_certification_fixture(db_session)
    second_snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="b" * 64,
        content_text="Shortage occupations for the year 2027\n1. New group",
        http_status=200,
        retrieval_method="http",
        parser_version="austria_migration_shortage_v1",
        status="captured",
    )
    db_session.add(second_snapshot)
    db_session.commit()
    db_session.refresh(second_snapshot)
    db_session.add(
        ShortageOccupationEntry(
            jurisdiction_id=jurisdiction.id,
            official_source_id=source.id,
            source_snapshot_id=second_snapshot.id,
            year=2027,
            scope="national",
            source_ordinal=1,
            occupation_group="New group",
            normalized_occupation_group="new group",
            occupation_aliases_json='["New group"]',
            province_codes_json="[]",
            province_names_json="[]",
            extraction_version="austria_migration_shortage_v1",
            entry_sha256="f" * 64,
            metadata_json="{}",
        )
    )
    db_session.commit()

    with pytest.raises(ValueError, match="pin source_snapshot_id"):
        source_certification_review_pack(db_session, certification.id)

    pinned = source_certification_review_pack(
        db_session,
        certification.id,
        source_snapshot_id=snapshot.id,
    )
    assert pinned.source_snapshot["id"] == str(snapshot.id)
    assert pinned.structured_projection["year"] == 2026


def test_non_structured_certification_preserves_legacy_review_flow(db_session: Session) -> None:
    jurisdiction = Jurisdiction(code="NZ", name="New Zealand", region="Oceania")
    db_session.add(jurisdiction)
    db_session.commit()
    db_session.refresh(jurisdiction)
    authority = RegulatoryAuthority(
        jurisdiction_id=jurisdiction.id,
        name="Immigration authority",
        active=True,
    )
    db_session.add(authority)
    db_session.commit()
    db_session.refresh(authority)
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        regulatory_authority_id=authority.id,
        country="new zealand",
        domain="visa",
        name="Official immigration source",
        url="https://example.govt.nz/immigration",
        active=True,
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    certification = JurisdictionSourceCertification(
        jurisdiction_id=jurisdiction.id,
        registry_entry_id=uuid4(),
        regulatory_authority_id=authority.id,
        official_source_id=source.id,
        certification_version=1,
        certification_scope="supplemental_visa",
        coverage_domains_json='["visa"]',
        evidence_notes="Legacy non-structured source evidence.",
        status="pending_review",
        proposed_by="legacy-proposer",
    )
    db_session.add(certification)
    db_session.commit()
    db_session.refresh(certification)

    reviewed = review_source_certification(
        db_session,
        certification_id=certification.id,
        decision="rejected",
        notes="Rejected without a structured evidence projection.",
        actor="legacy-reviewer",
    )
    assert reviewed.status == "rejected"


def test_review_pack_api_and_review_endpoint_enforce_human_attestation(
    client: TestClient,
    db_session: Session,
) -> None:
    _, _, _, snapshot, certification = _structured_certification_fixture(db_session)

    pack_response = client.get(
        f"/api/v1/global-intelligence/registry/source-certifications/{certification.id}/review-pack",
        params={"source_snapshot_id": str(snapshot.id)},
    )
    assert pack_response.status_code == 200, pack_response.text
    pack = pack_response.json()
    assert pack["structured_projection"]["entry_count"] == 2

    blocked = client.post(
        f"/api/v1/global-intelligence/registry/source-certifications/{certification.id}/review",
        json={
            "decision": "approved",
            "notes": "Attempt without the independent-human attestation.",
            "evidence_pack_sha256": pack["evidence_pack_sha256"],
            "source_snapshot_id": str(snapshot.id),
        },
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-independent-reviewer"},
    )
    assert blocked.status_code == 400, blocked.text
    assert "attestation" in blocked.json()["detail"].lower()

    approved = client.post(
        f"/api/v1/global-intelligence/registry/source-certifications/{certification.id}/review",
        json={
            "decision": "approved",
            "notes": "Personally reviewed the immutable snapshot and every structured entry.",
            "evidence_pack_sha256": pack["evidence_pack_sha256"],
            "source_snapshot_id": str(snapshot.id),
            "independent_human_attestation": True,
        },
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-independent-reviewer"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"


def test_structured_review_queue_exposes_deterministic_pack_without_mutation(
    db_session: Session,
) -> None:
    _, _, _, snapshot, certification = _structured_certification_fixture(db_session)

    queue = source_certification_review_queue(
        db_session,
        reviewer_identity="pytest-independent-reviewer",
        reviewer_role="reviewer",
    )

    item = next(row for row in queue.items if row.certification["id"] == certification.id)
    assert item.review_pack_state == "ready"
    assert item.can_submit_review is True
    assert item.reviewer_identity_conflict is False
    assert item.selected_source_snapshot_id == snapshot.id
    assert item.evidence_pack_sha256 is not None
    assert len(item.available_projections) == 1
    assert item.available_projections[0].entry_count == 2
    db_session.refresh(certification)
    assert certification.status == "pending_review"
    assert certification.reviewed_by is None


def test_review_workspace_read_only_role_cannot_submit(
    db_session: Session,
) -> None:
    _, _, _, snapshot, certification = _structured_certification_fixture(db_session)

    workspace = source_certification_review_workspace(
        db_session,
        certification.id,
        reviewer_identity="pytest-read-only-reviewer",
        reviewer_role="read_only",
        source_snapshot_id=snapshot.id,
    )

    assert workspace.review_pack_state == "ready"
    assert workspace.reviewer_identity_conflict is False
    assert workspace.can_submit_review is False
    assert "read-only" in " ".join(workspace.submission_requirements).lower()


def test_review_workspace_blocks_proposer_identity_case_insensitively(
    db_session: Session,
) -> None:
    _, _, _, snapshot, certification = _structured_certification_fixture(db_session)

    workspace = source_certification_review_workspace(
        db_session,
        certification.id,
        reviewer_identity="PYTEST-SOURCE-PROPOSER",
        reviewer_role="reviewer",
        source_snapshot_id=snapshot.id,
    )

    assert workspace.review_pack_state == "ready"
    assert workspace.reviewer_identity_conflict is True
    assert workspace.can_submit_review is False
    assert workspace.review_pack is not None
    assert workspace.review_history == []
    assert "matches the proposer" in " ".join(workspace.submission_requirements).lower()


def test_review_workspace_requires_snapshot_selection_when_multiple_projections_exist(
    db_session: Session,
) -> None:
    jurisdiction, _, source, snapshot, certification = _structured_certification_fixture(db_session)
    second_snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="c" * 64,
        content_text="Shortage occupations for the year 2027\n1. Later group",
        http_status=200,
        retrieval_method="http",
        parser_version="austria_migration_shortage_v1",
        status="captured",
    )
    db_session.add(second_snapshot)
    db_session.commit()
    db_session.refresh(second_snapshot)
    db_session.add(
        ShortageOccupationEntry(
            jurisdiction_id=jurisdiction.id,
            official_source_id=source.id,
            source_snapshot_id=second_snapshot.id,
            year=2027,
            scope="national",
            source_ordinal=1,
            occupation_group="Later group",
            normalized_occupation_group="later group",
            occupation_aliases_json='["Later group"]',
            province_codes_json="[]",
            province_names_json="[]",
            extraction_version="austria_migration_shortage_v1",
            entry_sha256="e" * 64,
            metadata_json="{}",
        )
    )
    db_session.commit()

    workspace = source_certification_review_workspace(
        db_session,
        certification.id,
        reviewer_identity="pytest-independent-reviewer",
        reviewer_role="reviewer",
    )
    assert workspace.review_pack_state == "snapshot_pin_required"
    assert workspace.review_pack is None
    assert workspace.can_submit_review is False
    assert {item.source_snapshot_id for item in workspace.available_projections} == {
        snapshot.id,
        second_snapshot.id,
    }

    pinned = source_certification_review_workspace(
        db_session,
        certification.id,
        reviewer_identity="pytest-independent-reviewer",
        reviewer_role="reviewer",
        source_snapshot_id=snapshot.id,
    )
    assert pinned.review_pack_state == "ready"
    assert pinned.can_submit_review is True
    assert pinned.review_pack is not None
    assert pinned.review_pack.source_snapshot["id"] == str(snapshot.id)


def test_review_workspace_history_returns_attested_audit_receipt(db_session: Session) -> None:
    _, _, _, snapshot, certification = _structured_certification_fixture(db_session)
    pack = source_certification_review_pack(db_session, certification.id)

    review_source_certification(
        db_session,
        certification_id=certification.id,
        decision="rejected",
        notes="Independent reviewer found a projection mismatch that requires remediation.",
        actor="pytest-independent-reviewer",
        independent_human_attestation=True,
        evidence_pack_sha256=pack.evidence_pack_sha256,
        source_snapshot_id=snapshot.id,
    )

    workspace = source_certification_review_workspace(
        db_session,
        certification.id,
        reviewer_identity="pytest-independent-reviewer",
        reviewer_role="reviewer",
        source_snapshot_id=snapshot.id,
    )
    assert workspace.can_submit_review is False
    assert workspace.certification["status"] == "rejected"
    assert len(workspace.review_history) == 1
    history = workspace.review_history[0]
    assert history.actor == "pytest-independent-reviewer"
    assert history.decision == "rejected"
    assert history.independent_human_attestation is True
    assert history.evidence_pack_sha256 == pack.evidence_pack_sha256
    assert history.source_snapshot_id == snapshot.id


def test_review_workspace_api_exposes_authenticated_reviewer_and_history(
    client: TestClient,
    db_session: Session,
) -> None:
    _, _, _, snapshot, certification = _structured_certification_fixture(db_session)
    headers = {"X-GMAI-Role": "reviewer", "X-GMAI-User": "pytest-ui-reviewer"}

    queue_response = client.get(
        "/api/v1/global-intelligence/registry/source-certifications/review-queue",
        headers=headers,
    )
    assert queue_response.status_code == 200, queue_response.text
    queue = queue_response.json()
    assert queue["reviewer_identity"] == "pytest-ui-reviewer"
    assert queue["total"] >= 1

    workspace_response = client.get(
        f"/api/v1/global-intelligence/registry/source-certifications/{certification.id}/review-workspace",
        params={"source_snapshot_id": str(snapshot.id)},
        headers=headers,
    )
    assert workspace_response.status_code == 200, workspace_response.text
    workspace = workspace_response.json()
    assert workspace["reviewer_identity"] == "pytest-ui-reviewer"
    assert workspace["review_pack_state"] == "ready"
    assert workspace["can_submit_review"] is True
    assert workspace["review_history"] == []

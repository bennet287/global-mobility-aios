from __future__ import annotations

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
    OrganizationContribution,
    RegulatoryAuthority,
    ShortageOccupationEntry,
    SourceSnapshot,
)
from app.services.jurisdiction_registry import review_source_certification
from app.services.organization_command import AuthorityDenied
from app.services.organization_source_certification import (
    source_certification_organization_context,
    stage_source_certification_review_contribution,
)
from app.services.source_certification_review import source_certification_review_pack


def _structured_certification_fixture(session: Session):
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
        url=(
            "https://www.migration.gv.at/en/types-of-immigration/"
            "permanent-immigration/austria-wide-shortage-occupations/"
        ),
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
        content_text="Shortage occupations for 2026\n1. Engineers",
        http_status=200,
        retrieval_method="http",
        parser_version="austria_migration_shortage_v1",
        status="captured",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    session.add(
        ShortageOccupationEntry(
            jurisdiction_id=jurisdiction.id,
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            year=2026,
            scope="national",
            source_ordinal=1,
            occupation_group="Engineers",
            normalized_occupation_group="engineers",
            occupation_aliases_json='["Engineer"]',
            province_codes_json="[]",
            province_names_json="[]",
            extraction_version="austria_migration_shortage_v1",
            entry_sha256="1" * 64,
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
        evidence_notes="Review immutable structured evidence.",
        status="pending_review",
        proposed_by="source-proposer",
    )
    session.add(certification)
    session.commit()
    session.refresh(certification)
    return snapshot, certification


def _contributions(session: Session) -> list[OrganizationContribution]:
    return list(session.exec(select(OrganizationContribution)).all())


def _source_review_audit(session: Session, certification_id) -> AuditLog | None:
    return session.exec(
        select(AuditLog)
        .where(
            AuditLog.action == "jurisdiction_source_certification_reviewed",
            AuditLog.entity_id == str(certification_id),
        )
        .order_by(AuditLog.created_at.desc())
    ).first()


def _review_via_api(
    client: TestClient,
    session: Session,
    certification: JurisdictionSourceCertification,
    snapshot: SourceSnapshot,
    *,
    decision: str = "approved",
    role: str = "admin",
    actor: str = "independent-reviewer",
):
    pack = source_certification_review_pack(session, certification.id, source_snapshot_id=snapshot.id)
    return client.post(
        f"/api/v1/global-intelligence/registry/source-certifications/{certification.id}/review",
        json={
            "decision": decision,
            "notes": "Personally reviewed the immutable snapshot and structured projection.",
            "evidence_pack_sha256": pack.evidence_pack_sha256,
            "source_snapshot_id": str(snapshot.id),
            "independent_human_attestation": True,
        },
        headers={"X-GMAI-Role": role, "X-GMAI-User": actor},
    )


def test_pending_source_certification_emits_no_contribution(db_session: Session) -> None:
    _snapshot, certification = _structured_certification_fixture(db_session)

    assert certification.status == "pending_review"
    assert _contributions(db_session) == []


def test_approved_structured_review_atomically_emits_one_safe_contribution(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    snapshot, certification = _structured_certification_fixture(db_session)

    response = _review_via_api(raw_client, db_session, certification, snapshot)
    assert response.status_code == 200, response.text

    rows = _contributions(db_session)
    assert len(rows) == 1
    contribution = rows[0]
    assert contribution.source_object_type == "jurisdiction_source_certification"
    assert contribution.source_object_id == str(certification.id)
    assert contribution.source_state == "approved"
    assert contribution.contribution_type == "source_certification_review_completed"
    assert contribution.verified_by == "independent-reviewer"
    assert contribution.actor_id == "independent-reviewer"
    assert contribution.impact_kind == "validation"
    assert "does not establish applicant eligibility" in contribution.outcome_summary

    source_audit = _source_review_audit(db_session, certification.id)
    contribution_audit = db_session.exec(
        select(AuditLog).where(AuditLog.action == "organization.contribution.create")
    ).first()
    assert source_audit is not None
    assert contribution_audit is not None


def test_rejected_review_emits_review_outcome_not_certification_claim(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    snapshot, certification = _structured_certification_fixture(db_session)

    response = _review_via_api(
        raw_client,
        db_session,
        certification,
        snapshot,
        decision="rejected",
        role="reviewer",
        actor="independent-reviewer",
    )
    assert response.status_code == 200, response.text

    contribution = _contributions(db_session)[0]
    assert contribution.source_state == "rejected"
    assert contribution.contribution_type == "source_certification_review_completed"
    assert "review rejected" in contribution.outcome_summary.lower()
    assert "eligibility" in contribution.outcome_summary.lower()


def test_structured_review_without_attestation_emits_nothing(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    snapshot, certification = _structured_certification_fixture(db_session)
    pack = source_certification_review_pack(db_session, certification.id, source_snapshot_id=snapshot.id)

    response = raw_client.post(
        f"/api/v1/global-intelligence/registry/source-certifications/{certification.id}/review",
        json={
            "decision": "approved",
            "notes": "Attempt without independent attestation.",
            "evidence_pack_sha256": pack.evidence_pack_sha256,
            "source_snapshot_id": str(snapshot.id),
        },
        headers={"X-GMAI-Role": "reviewer", "X-GMAI-User": "independent-reviewer"},
    )

    assert response.status_code == 400
    db_session.refresh(certification)
    assert certification.status == "pending_review"
    assert _contributions(db_session) == []
    assert _source_review_audit(db_session, certification.id) is None


def test_emitter_failure_rolls_back_source_transition_and_both_audits(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot, certification = _structured_certification_fixture(db_session)
    pack = source_certification_review_pack(db_session, certification.id, source_snapshot_id=snapshot.id)

    def fail_emitter(*args, **kwargs):
        raise RuntimeError("synthetic emitter failure")

    monkeypatch.setattr(
        "app.services.jurisdiction_registry.stage_source_certification_review_contribution",
        fail_emitter,
    )

    with pytest.raises(RuntimeError, match="synthetic emitter failure"):
        review_source_certification(
            db_session,
            certification_id=certification.id,
            decision="approved",
            notes="Review should roll back with emitter failure.",
            actor="independent-reviewer",
            reviewer_role="reviewer",
            independent_human_attestation=True,
            evidence_pack_sha256=pack.evidence_pack_sha256,
            source_snapshot_id=snapshot.id,
        )

    db_session.refresh(certification)
    assert certification.status == "pending_review"
    assert certification.reviewed_by is None
    assert _contributions(db_session) == []
    assert _source_review_audit(db_session, certification.id) is None
    assert db_session.exec(
        select(AuditLog).where(AuditLog.action == "organization.contribution.create")
    ).first() is None


def test_untrusted_emitter_role_rolls_back_review(db_session: Session) -> None:
    snapshot, certification = _structured_certification_fixture(db_session)
    pack = source_certification_review_pack(db_session, certification.id, source_snapshot_id=snapshot.id)

    with pytest.raises(AuthorityDenied):
        review_source_certification(
            db_session,
            certification_id=certification.id,
            decision="approved",
            notes="Operator is not a source-certification review authority.",
            actor="operator-user",
            reviewer_role="operator",
            independent_human_attestation=True,
            evidence_pack_sha256=pack.evidence_pack_sha256,
            source_snapshot_id=snapshot.id,
        )

    db_session.refresh(certification)
    assert certification.status == "pending_review"
    assert _contributions(db_session) == []
    assert _source_review_audit(db_session, certification.id) is None


def test_source_certification_emitter_replay_is_idempotent(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    snapshot, certification = _structured_certification_fixture(db_session)
    response = _review_via_api(raw_client, db_session, certification, snapshot)
    assert response.status_code == 200, response.text

    source_audit = _source_review_audit(db_session, certification.id)
    assert source_audit is not None
    audit_payload = json.loads(source_audit.after_state_json or "{}")
    context = source_certification_organization_context(
        actor="independent-reviewer",
        role="admin",
    )
    first = _contributions(db_session)[0]
    replay = stage_source_certification_review_contribution(
        db_session,
        context,
        certification=certification,
        review_evidence=audit_payload["review_evidence"],
    )
    db_session.commit()

    assert replay.id == first.id
    assert len(_contributions(db_session)) == 1
    contribution_audits = list(
        db_session.exec(
            select(AuditLog).where(AuditLog.action == "organization.contribution.create")
        ).all()
    )
    assert len(contribution_audits) == 1


def test_legacy_direct_review_without_trusted_role_preserves_no_emitter_behavior(
    db_session: Session,
) -> None:
    snapshot, certification = _structured_certification_fixture(db_session)
    pack = source_certification_review_pack(db_session, certification.id, source_snapshot_id=snapshot.id)

    reviewed = review_source_certification(
        db_session,
        certification_id=certification.id,
        decision="approved",
        notes="Legacy direct service review remains compatible.",
        actor="independent-reviewer",
        independent_human_attestation=True,
        evidence_pack_sha256=pack.evidence_pack_sha256,
        source_snapshot_id=snapshot.id,
    )

    assert reviewed.status == "approved"
    assert _contributions(db_session) == []

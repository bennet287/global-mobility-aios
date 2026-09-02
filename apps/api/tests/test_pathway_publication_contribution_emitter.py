from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    OrganizationContribution,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.organization_command import ContributionSourceRejected
from app.services.organization_contribution import validate_authoritative_outcome
from app.services.organization_pathway_publication import (
    pathway_publication_organization_context,
    stage_pathway_version_publication_contribution,
)
from app.services.pathway_catalogue import publish_pathway_version


ADMIN_HEADERS = {"X-GMAI-Role": "admin", "X-GMAI-User": "pathway-publisher"}
OPERATOR_HEADERS = {"X-GMAI-Role": "operator", "X-GMAI-User": "pathway-operator"}


def _evidence_fixture(
    session: Session,
    *,
    suffix: str,
) -> tuple[Jurisdiction, OfficialSource, SourceSnapshot, VerifiedRule]:
    jurisdiction = Jurisdiction(code=f"D{suffix[-1:].upper()}", name="Germany", region="Europe")
    session.add(jurisdiction)
    session.flush()
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="germany",
        domain="work",
        name=f"Germany governed pathway source {suffix}",
        url=f"https://official.example/pathways/{suffix}",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.flush()
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=(suffix.encode("utf-8").hex() + "a" * 64)[:64],
        content_text=f"Governed pathway publication evidence for {suffix}.",
        http_status=200,
        retrieval_method="http",
        parser_version="test-v1",
        status="captured",
    )
    session.add(snapshot)
    session.flush()
    rule = VerifiedRule(
        country="germany",
        domain="work",
        rule_key=f"de-pathway-{suffix}",
        statement=f"Governed skilled-work rule for {suffix}.",
        official_source_id=source.id,
        jurisdiction_id=jurisdiction.id,
        source_snapshot_id=snapshot.id,
        confidence=0.99,
        active=True,
        approved_by="rule-reviewer",
        published_at=now_utc(),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return jurisdiction, source, snapshot, rule


def _version_payload(source: OfficialSource, snapshot: SourceSnapshot, rule: VerifiedRule) -> dict:
    return {
        "official_source_id": str(source.id),
        "source_snapshot_id": str(snapshot.id),
        "verified_rule_ids": [str(rule.id)],
        "eligibility_criteria": {"minimum_years_experience": 2},
        "required_documents": ["passport", "qualification evidence"],
        "costs": {"currency": "EUR", "government_fee": 100},
        "processing_time": {"minimum_weeks": 4, "maximum_weeks": 12},
        "benefits": ["Governed skilled-employment pathway"],
        "risks": ["Applicant eligibility requires case-specific assessment"],
        "metadata": {"fixture": "d3c"},
    }


def _create_draft(
    raw_client: TestClient,
    session: Session,
    *,
    suffix: str,
    creator: str = "pathway-proposer",
) -> tuple[dict, MobilityPathway, MobilityPathwayVersion, OfficialSource, SourceSnapshot, VerifiedRule]:
    jurisdiction, source, snapshot, rule = _evidence_fixture(session, suffix=suffix)
    payload = {
        "pathway_key": f"de-skilled-worker-{suffix}",
        "name": f"Germany Skilled Worker {suffix}",
        "country": "Germany",
        "domain": "work",
        "jurisdiction_id": str(jurisdiction.id),
        "description": "Governed D3C pathway publication fixture.",
        **_version_payload(source, snapshot, rule),
    }
    response = raw_client.post(
        "/api/v1/pathways",
        json=payload,
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": creator},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    pathway = session.get(MobilityPathway, UUID(body["id"]))
    version = session.get(MobilityPathwayVersion, UUID(body["current_version"]["id"]))
    assert pathway is not None and version is not None
    return body, pathway, version, source, snapshot, rule


def _contributions(session: Session) -> list[OrganizationContribution]:
    return list(session.exec(select(OrganizationContribution)).all())


def test_draft_pathway_version_emits_no_contribution(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _body, _pathway, version, _source, _snapshot, _rule = _create_draft(
        raw_client,
        db_session,
        suffix="draft",
    )

    assert version.lifecycle_status == "draft"
    assert _contributions(db_session) == []
    context = pathway_publication_organization_context(
        actor="pathway-publisher",
        role="admin",
    )
    with pytest.raises(ContributionSourceRejected, match="not in the published authoritative state"):
        stage_pathway_version_publication_contribution(
            db_session,
            context,
            pathway=db_session.get(MobilityPathway, version.pathway_id),
            version=version,
        )
    db_session.rollback()


def test_authenticated_pathway_publication_emits_one_safe_contribution(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    body, pathway, version, _source, _snapshot, _rule = _create_draft(
        raw_client,
        db_session,
        suffix="publish",
    )

    response = raw_client.post(
        f"/api/v1/pathways/versions/{body['current_version']['id']}/publish",
        json={"review_notes": "Independent governed pathway publication review completed."},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200, response.text

    rows = _contributions(db_session)
    assert len(rows) == 1
    contribution = rows[0]
    assert contribution.source_object_type == "mobility_pathway_version"
    assert contribution.source_object_id == str(version.id)
    assert contribution.source_state == "published"
    assert contribution.contribution_type == "pathway_version_published"
    assert contribution.actor_id == "pathway-publisher"
    assert contribution.verified_by == "pathway-publisher"
    assert contribution.impact_kind == "knowledge"
    assert "does not establish applicant eligibility" in contribution.outcome_summary
    assert "visa approval" in contribution.outcome_summary

    db_session.refresh(pathway)
    db_session.refresh(version)
    assert pathway.catalogue_status == "active"
    assert version.lifecycle_status == "published"
    assert version.approved_by == "pathway-publisher"
    publication_audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.action == "mobility_pathway_version_published",
            AuditLog.entity_id == str(version.id),
        )
    ).first()
    contribution_audit = db_session.exec(
        select(AuditLog).where(AuditLog.action == "organization.contribution.create")
    ).first()
    assert publication_audit is not None
    assert contribution_audit is not None


def test_operator_publication_compatibility_is_preserved(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    body, _pathway, version, _source, _snapshot, _rule = _create_draft(
        raw_client,
        db_session,
        suffix="operator",
    )

    response = raw_client.post(
        f"/api/v1/pathways/versions/{body['current_version']['id']}/publish",
        json={"review_notes": "Independent operator publication review completed."},
        headers=OPERATOR_HEADERS,
    )

    assert response.status_code == 200, response.text
    db_session.refresh(version)
    assert version.approved_by == "pathway-operator"
    rows = _contributions(db_session)
    assert len(rows) == 1
    assert rows[0].actor_id == "pathway-operator"


def test_pathway_publication_adapter_replay_is_idempotent(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _body, pathway, version, _source, _snapshot, _rule = _create_draft(
        raw_client,
        db_session,
        suffix="replay",
    )
    publish_pathway_version(
        db_session,
        version.id,
        actor="pathway-publisher",
        review_notes="Independent publication review completed.",
        publisher_role="admin",
    )
    db_session.expire_all()
    persisted_pathway = db_session.get(MobilityPathway, pathway.id)
    persisted_version = db_session.get(MobilityPathwayVersion, version.id)
    assert persisted_pathway is not None and persisted_version is not None
    first = _contributions(db_session)[0]
    context = pathway_publication_organization_context(
        actor="pathway-publisher",
        role="admin",
    )

    replay = stage_pathway_version_publication_contribution(
        db_session,
        context,
        pathway=persisted_pathway,
        version=persisted_version,
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


def test_pathway_publication_detects_verified_rule_drift(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _body, pathway, version, _source, _snapshot, rule = _create_draft(
        raw_client,
        db_session,
        suffix="drift",
    )
    publish_pathway_version(
        db_session,
        version.id,
        actor="pathway-publisher",
        review_notes="Independent publication review completed.",
        publisher_role="admin",
    )
    rule.active = False
    db_session.add(rule)
    db_session.flush()
    context = pathway_publication_organization_context(
        actor="pathway-publisher",
        role="admin",
    )

    with pytest.raises(
        ContributionSourceRejected,
        match="publication gate",
    ):
        stage_pathway_version_publication_contribution(
            db_session,
            context,
            pathway=pathway,
            version=version,
        )
    db_session.rollback()


def test_pathway_publication_rolls_back_if_contribution_staging_fails(
    raw_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _body, pathway, version, _source, _snapshot, _rule = _create_draft(
        raw_client,
        db_session,
        suffix="rollback",
    )

    def _fail_emission(*args, **kwargs):
        raise RuntimeError("synthetic pathway Contribution staging failure")

    monkeypatch.setattr(
        "app.services.organization_pathway_publication.stage_pathway_version_publication_contribution",
        _fail_emission,
    )

    with pytest.raises(RuntimeError, match="synthetic pathway Contribution staging failure"):
        publish_pathway_version(
            db_session,
            version.id,
            actor="pathway-publisher",
            review_notes="Independent publication review completed.",
            publisher_role="admin",
        )

    db_session.expire_all()
    persisted_pathway = db_session.get(MobilityPathway, pathway.id)
    persisted_version = db_session.get(MobilityPathwayVersion, version.id)
    assert persisted_pathway is not None and persisted_pathway.catalogue_status == "draft"
    assert persisted_version is not None and persisted_version.lifecycle_status == "draft"
    assert persisted_version.approved_by is None
    assert persisted_version.published_at is None
    assert _contributions(db_session) == []
    publish_audits = db_session.exec(
        select(AuditLog).where(
            AuditLog.action.in_([
                "mobility_pathway_version_published",
                "organization.contribution.create",
            ])
        )
    ).all()
    assert publish_audits == []


def test_new_published_revision_supersedes_previous_and_emits_distinct_contribution(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    body, pathway, version_one, source, snapshot, rule = _create_draft(
        raw_client,
        db_session,
        suffix="revision",
    )
    first = raw_client.post(
        f"/api/v1/pathways/versions/{version_one.id}/publish",
        json={"review_notes": "First governed pathway version published."},
        headers=ADMIN_HEADERS,
    )
    assert first.status_code == 200, first.text

    version_two_response = raw_client.post(
        f"/api/v1/pathways/{body['id']}/versions",
        json={
            **_version_payload(source, snapshot, rule),
            "metadata": {"fixture": "d3c", "revision": 2},
        },
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "revision-proposer"},
    )
    assert version_two_response.status_code == 201, version_two_response.text
    version_two_id = UUID(version_two_response.json()["id"])

    second = raw_client.post(
        f"/api/v1/pathways/versions/{version_two_id}/publish",
        json={"review_notes": "Second governed pathway version independently published."},
        headers=OPERATOR_HEADERS,
    )
    assert second.status_code == 200, second.text

    db_session.expire_all()
    version_one = db_session.get(MobilityPathwayVersion, version_one.id)
    version_two = db_session.get(MobilityPathwayVersion, version_two_id)
    assert version_one is not None and version_one.lifecycle_status == "superseded"
    assert version_two is not None and version_two.lifecycle_status == "published"
    assert version_two.version_number == 2
    assert version_two.supersedes_version_id == version_one.id
    rows = sorted(_contributions(db_session), key=lambda row: row.effective_at)
    assert len(rows) == 2
    assert {row.source_object_id for row in rows} == {str(version_one.id), str(version_two.id)}
    assert len({row.contribution_key for row in rows}) == 2
    assert db_session.get(MobilityPathway, pathway.id).catalogue_status == "active"


def test_generic_contribution_source_policy_remains_closed_to_pathway_versions(
    db_session: Session,
) -> None:
    context = pathway_publication_organization_context(
        actor="pathway-publisher",
        role="admin",
    )

    with pytest.raises(
        ContributionSourceRejected,
        match="no authoritative contribution adapter is enabled",
    ):
        validate_authoritative_outcome(
            db_session,
            context,
            source_type="mobility_pathway_version",
            source_id="11111111-1111-1111-1111-111111111111",
            source_version="forbidden-generic-source-version",
            outcome_type="pathway_version_published",
            verification_basis="Generic API must not select the sealed D3C source adapter.",
        )

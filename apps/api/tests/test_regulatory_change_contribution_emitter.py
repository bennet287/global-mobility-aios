from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    OfficialSource,
    OrganizationContribution,
    RegulatoryChange,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.schemas import RegulatoryChangePublishRequest
from app.services.organization_command import ContributionSourceRejected
from app.services.organization_contribution import validate_authoritative_outcome
from app.services.organization_regulatory_change_publication import (
    regulatory_change_publication_organization_context,
    stage_regulatory_change_publication_contribution,
)
from app.services.regulatory_intelligence import publish_regulatory_change


def _approved_change_fixture(session: Session):
    jurisdiction = Jurisdiction(code="AT", name="Austria", region="Europe")
    session.add(jurisdiction)
    session.flush()
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="austria",
        domain="visa",
        name="Austria official immigration change fixture",
        url="https://official.example/regulatory-change",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.flush()
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="b" * 64,
        content_text="Reviewed official change evidence.",
        http_status=200,
        retrieval_method="http",
        parser_version="test-v1",
        status="changed",
    )
    session.add(snapshot)
    session.flush()
    change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        current_snapshot_id=snapshot.id,
        domain="visa",
        change_type="policy_change",
        title="Reviewed official immigration policy change",
        summary="The reviewed official source changed one governed immigration rule.",
        materiality="material",
        status="approved",
        reviewed_at=now_utc(),
        reviewed_by="change-reviewer",
        review_notes="Reviewed against the immutable official source snapshot.",
    )
    session.add(change)
    session.commit()
    session.refresh(change)
    return jurisdiction, source, snapshot, change


def _publish_payload(*, reviewer: str = "rule-publisher") -> dict:
    return {
        "rule_key": "reviewed_policy_change",
        "statement": "The reviewed official policy change is now published as governed regulatory knowledge.",
        "reviewer": reviewer,
        "confidence": 0.99,
    }


def _contributions(session: Session) -> list[OrganizationContribution]:
    return list(session.exec(select(OrganizationContribution)).all())


def test_approved_but_unpublished_regulatory_change_emits_nothing(db_session: Session) -> None:
    _jurisdiction, _source, _snapshot, change = _approved_change_fixture(db_session)

    assert change.status == "approved"
    assert _contributions(db_session) == []


def test_authenticated_publication_atomically_emits_one_safe_contribution(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _jurisdiction, _source, _snapshot, change = _approved_change_fixture(db_session)

    response = raw_client.post(
        f"/api/v1/regulatory-intelligence/changes/{change.id}/publish",
        json=_publish_payload(),
        headers={"X-GMAI-Role": "reviewer", "X-GMAI-User": "rule-publisher"},
    )
    assert response.status_code == 200, response.text

    rule_id = response.json()["verified_rule"]["id"]
    rows = _contributions(db_session)
    assert len(rows) == 1
    contribution = rows[0]
    assert contribution.source_object_type == "regulatory_change"
    assert contribution.source_object_id == str(change.id)
    assert contribution.source_state == "published"
    assert contribution.contribution_type == "regulatory_change_publication_completed"
    assert contribution.actor_id == "rule-publisher"
    assert contribution.verified_by == "rule-publisher"
    assert contribution.impact_kind == "knowledge"
    assert "does not establish applicant eligibility" in contribution.outcome_summary

    persisted_change = db_session.get(RegulatoryChange, change.id)
    rule = db_session.get(VerifiedRule, UUID(rule_id))
    assert persisted_change is not None and persisted_change.status == "published"
    assert rule is not None and rule.approved_by == "rule-publisher"
    publish_audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.action == "verified_rule_published",
            AuditLog.entity_id == str(rule.id),
        )
    ).first()
    contribution_audit = db_session.exec(
        select(AuditLog).where(AuditLog.action == "organization.contribution.create")
    ).first()
    assert publish_audit is not None
    assert contribution_audit is not None


def test_regulatory_change_publication_api_replay_is_idempotent(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _jurisdiction, _source, _snapshot, change = _approved_change_fixture(db_session)
    headers = {"X-GMAI-Role": "reviewer", "X-GMAI-User": "rule-publisher"}
    payload = _publish_payload()

    first = raw_client.post(
        f"/api/v1/regulatory-intelligence/changes/{change.id}/publish",
        json=payload,
        headers=headers,
    )
    repeated = raw_client.post(
        f"/api/v1/regulatory-intelligence/changes/{change.id}/publish",
        json=payload,
        headers=headers,
    )

    assert first.status_code == 200, first.text
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["verified_rule"]["id"] == first.json()["verified_rule"]["id"]
    assert len(_contributions(db_session)) == 1
    contribution_audits = list(
        db_session.exec(
            select(AuditLog).where(AuditLog.action == "organization.contribution.create")
        ).all()
    )
    assert len(contribution_audits) == 1


def test_regulatory_change_publication_adapter_replay_is_idempotent(db_session: Session) -> None:
    _jurisdiction, _source, _snapshot, change = _approved_change_fixture(db_session)
    payload = RegulatoryChangePublishRequest(**_publish_payload())
    rule = publish_regulatory_change(
        db_session,
        change.id,
        payload,
        publisher_actor="rule-publisher",
        publisher_role="reviewer",
    )
    persisted_change = db_session.get(RegulatoryChange, change.id)
    assert persisted_change is not None
    first = _contributions(db_session)[0]
    context = regulatory_change_publication_organization_context(
        actor="rule-publisher",
        role="reviewer",
    )

    replay = stage_regulatory_change_publication_contribution(
        db_session,
        context,
        change=persisted_change,
        rule=rule,
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


def test_regulatory_change_publication_detects_published_rule_drift(db_session: Session) -> None:
    _jurisdiction, _source, _snapshot, change = _approved_change_fixture(db_session)
    rule = publish_regulatory_change(
        db_session,
        change.id,
        RegulatoryChangePublishRequest(**_publish_payload()),
        publisher_actor="rule-publisher",
        publisher_role="reviewer",
    )
    persisted_change = db_session.get(RegulatoryChange, change.id)
    assert persisted_change is not None
    rule.approved_by = "tampered-publisher"
    db_session.add(rule)
    db_session.flush()
    context = regulatory_change_publication_organization_context(
        actor="rule-publisher",
        role="reviewer",
    )

    with pytest.raises(ContributionSourceRejected, match="publisher does not match"):
        stage_regulatory_change_publication_contribution(
            db_session,
            context,
            change=persisted_change,
            rule=rule,
        )
    db_session.rollback()


def test_regulatory_change_publication_rolls_back_if_contribution_staging_fails(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _jurisdiction, _source, _snapshot, change = _approved_change_fixture(db_session)

    def _fail_emission(*args, **kwargs):
        raise RuntimeError("synthetic Contribution staging failure")

    monkeypatch.setattr(
        "app.services.organization_regulatory_change_publication.stage_regulatory_change_publication_contribution",
        _fail_emission,
    )

    with pytest.raises(RuntimeError, match="synthetic Contribution staging failure"):
        publish_regulatory_change(
            db_session,
            change.id,
            RegulatoryChangePublishRequest(**_publish_payload()),
            publisher_actor="rule-publisher",
            publisher_role="reviewer",
        )

    db_session.expire_all()
    persisted = db_session.get(RegulatoryChange, change.id)
    assert persisted is not None
    assert persisted.status == "approved"
    assert persisted.published_at is None
    assert db_session.exec(select(VerifiedRule)).all() == []
    assert _contributions(db_session) == []
    publish_audits = db_session.exec(
        select(AuditLog).where(
            AuditLog.action.in_([
                "regulatory_change_published",
                "verified_rule_published",
                "organization.contribution.create",
            ])
        )
    ).all()
    assert publish_audits == []


def test_publication_body_cannot_choose_a_different_publisher_identity(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    _jurisdiction, _source, _snapshot, change = _approved_change_fixture(db_session)

    response = raw_client.post(
        f"/api/v1/regulatory-intelligence/changes/{change.id}/publish",
        json=_publish_payload(reviewer="spoofed-reviewer"),
        headers={"X-GMAI-Role": "reviewer", "X-GMAI-User": "authenticated-publisher"},
    )

    assert response.status_code == 400
    assert "match the authenticated publisher" in response.json()["detail"]
    db_session.refresh(change)
    assert change.status == "approved"
    assert db_session.exec(select(VerifiedRule)).all() == []
    assert _contributions(db_session) == []


def test_generic_contribution_source_policy_remains_closed_to_regulatory_changes(
    db_session: Session,
) -> None:
    context = regulatory_change_publication_organization_context(
        actor="rule-publisher",
        role="admin",
    )

    with pytest.raises(
        ContributionSourceRejected,
        match="no authoritative contribution adapter is enabled",
    ):
        validate_authoritative_outcome(
            db_session,
            context,
            source_type="regulatory_change",
            source_id="11111111-1111-1111-1111-111111111111",
            source_version="forbidden-generic-source-version",
            outcome_type="regulatory_change_publication_completed",
            verification_basis="Generic API must not select the sealed D3B source adapter.",
        )

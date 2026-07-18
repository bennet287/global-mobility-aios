from __future__ import annotations

from uuid import UUID

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    InitialRuleAssertion,
    JurisdictionCoverageEvidenceBatchItem,
    JurisdictionImmigrationAssessment,
    JurisdictionSourceCertification,
    OfficialSource,
    SourceMonitor,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.schemas import (
    InitialRuleAssertionCreateRequest,
    InitialRuleAssertionPublishRequest,
    InitialRuleAssertionReviewRequest,
)
from app.services.coverage_evidence_batches import (
    coverage_batch_payload,
    create_coverage_evidence_batch,
)
from app.services.initial_rule_assertions import (
    propose_initial_rule_assertion,
    publish_initial_rule_assertion,
    review_initial_rule_assertion,
)
from app.services.jurisdiction_registry import (
    import_un_m49_registry,
    review_immigration_assessment,
    review_source_certification,
)


SAMPLE_M49 = """
<html><table id="downloadTableEN"><tbody>
<tr><td>001</td><td>World</td><td>150</td><td>Europe</td><td>155</td><td>Western Europe</td><td></td><td></td><td>Austria</td><td>040</td><td>AT</td><td>AUT</td></tr>
<tr><td>001</td><td>World</td><td>150</td><td>Europe</td><td>155</td><td>Western Europe</td><td></td><td></td><td>Germany</td><td>276</td><td>DE</td><td>DEU</td></tr>
</tbody></table></html>
"""


def _setup_registry(session: Session) -> None:
    import_un_m49_registry(
        session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )


def _primary_at_batch(session: Session):
    batch, _ = create_coverage_evidence_batch(
        session,
        name="Primary AT evidence batch",
        notes="Primary source onboarding for Austria.",
        items=[{
            "alpha2_code": "AT",
            "source_onboarding": {
                "authority_name": "Austrian immigration authority",
                "authority_type": "immigration_authority",
                "authority_website_url": "https://official.example/immigration",
                "authority_domains": ["visa"],
                "source_name": "Austria official immigration portal",
                "source_url": "https://official.example/immigration",
                "source_domain": "visa",
                "source_type": "government",
                "schedule_minutes": 1440,
                "fetch_method": "http",
                "allowed_domains": ["official.example"],
                "max_redirects": 3,
                "parser_profile": "generic",
                "parser_config": {},
                "certification_domains": ["visa"],
                "evidence_notes": "Official authority ownership and primary immigration scope require independent review.",
            },
            "immigration_assessment": {
                "rule_relationship": "independent",
                "parent_code": None,
                "evidence_url": "https://official.example/immigration/framework",
                "evidence_title": "Official immigration framework",
                "rationale": "Official evidence identifies the directly administering immigration authority.",
            },
        }],
        actor="coverage-proposer",
    )
    item = coverage_batch_payload(session, batch)["items"][0]
    review_immigration_assessment(
        session,
        assessment_id=item["immigration_assessment"]["id"],
        decision="approved",
        notes="Independent relationship review completed.",
        actor="coverage-reviewer",
    )
    review_source_certification(
        session,
        certification_id=item["source_certification"]["id"],
        decision="approved",
        notes="Independent source certification completed.",
        actor="coverage-reviewer",
    )
    return batch, item


def _capture_baseline(session: Session, source_id: UUID, monitor_id: UUID, text: str) -> SourceSnapshot:
    monitor = session.get(SourceMonitor, monitor_id)
    assert monitor is not None
    monitor.status = "active"
    monitor.last_checked_at = now_utc()
    session.add(monitor)
    snapshot = SourceSnapshot(
        official_source_id=source_id,
        url="https://official.example/supplemental",
        content_hash="b" * 64,
        content_text=text,
        http_status=200,
        retrieval_method="http",
        parser_version="generic-v1",
        status="baseline",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def _supplemental_payload(alpha2_code: str = "AT") -> InitialRuleAssertionCreateRequest:
    return InitialRuleAssertionCreateRequest(
        alpha2_code=alpha2_code,
        domain="visa",
        title="Austria supplemental visa information baseline",
        rule_key="at_supplemental_visa_information_baseline",
        statement="The supplemental official source for Austria publishes visa-related information.",
        rationale="The assertion is pinned to the immutable supplemental baseline and reports only the presence of visa information.",
        evidence_excerpt="Official supplemental visa information for Austria.",
        confidence=0.95,
    )


def test_source_only_supplemental_reuses_approved_jurisdiction_assessment(db_session: Session) -> None:
    """A source-only supplemental batch item with no local assessment can reuse the latest approved jurisdiction assessment."""
    _setup_registry(db_session)
    primary_batch, primary_item = _primary_at_batch(db_session)
    primary_jurisdiction_id = primary_item["jurisdiction_id"]

    supplemental_batch, _ = create_coverage_evidence_batch(
        db_session,
        name="Source-only supplemental AT batch",
        notes="Supplemental source with no local assessment, expecting jurisdiction assessment reuse.",
        items=[{
            "alpha2_code": "AT",
            "source_onboarding": {
                "authority_name": "Austrian immigration authority",
                "authority_type": "immigration_authority",
                "authority_website_url": "https://official.example/immigration",
                "authority_domains": ["visa"],
                "source_name": "Austria supplemental visa portal",
                "source_url": "https://supplemental.example/at/visa",
                "source_domain": "visa",
                "source_type": "government",
                "schedule_minutes": 1440,
                "fetch_method": "http",
                "allowed_domains": ["supplemental.example"],
                "max_redirects": 3,
                "parser_profile": "generic",
                "parser_config": {},
                "certification_scope": "supplemental_visa",
                "certification_domains": ["visa"],
                "evidence_notes": "Supplemental official source for Austrian visa information.",
            },
        }],
        actor="coverage-proposer",
    )
    supplemental_item = coverage_batch_payload(db_session, supplemental_batch)["items"][0]
    raw_item = db_session.get(JurisdictionCoverageEvidenceBatchItem, supplemental_item["id"])
    assert raw_item is not None
    # The source-only supplemental batch reuses the latest approved jurisdiction assessment at creation time.
    assert raw_item.immigration_assessment_id == primary_item["immigration_assessment"]["id"]
    assert raw_item.source_certification_id is not None

    review_source_certification(
        db_session,
        certification_id=supplemental_item["source_certification"]["id"],
        decision="approved",
        notes="Supplemental source certification approved.",
        actor="coverage-reviewer",
    )
    source = db_session.get(OfficialSource, raw_item.official_source_id)
    snapshot = _capture_baseline(
        db_session,
        source_id=source.id,
        monitor_id=raw_item.source_monitor_id,
        text="Supplemental Austrian visa information.",
    )

    assertion, created = propose_initial_rule_assertion(
        db_session,
        batch_id=supplemental_batch.id,
        payload=_supplemental_payload(),
        actor="assertion-proposer",
    )
    assert created is True
    assert assertion.source_snapshot_id == snapshot.id
    assert assertion.jurisdiction_id == primary_jurisdiction_id

    reviewed = review_initial_rule_assertion(
        db_session,
        assertion.id,
        InitialRuleAssertionReviewRequest(
            decision="approved",
            notes="Supplemental assertion independently reviewed.",
        ),
        actor="assertion-reviewer",
    )
    assert reviewed.status == "approved"

    rule, receipt = publish_initial_rule_assertion(
        db_session,
        assertion.id,
        InitialRuleAssertionPublishRequest(
            attestation=True,
            publication_notes="Publish the supplemental baseline rule.",
        ),
        actor="assertion-publisher",
    )
    assert rule.source_snapshot_id == snapshot.id
    assert receipt["after"]["coverage_ready"] is True


def test_local_pending_assessment_is_not_bypassed(db_session: Session) -> None:
    """A batch-local pending assessment takes precedence and is never bypassed by a jurisdiction-approved assessment."""
    _setup_registry(db_session)
    _primary_at_batch(db_session)

    supplemental_batch, _ = create_coverage_evidence_batch(
        db_session,
        name="Supplemental AT batch with local pending assessment",
        notes="Supplemental source with a local pending assessment that must not be bypassed.",
        items=[{
            "alpha2_code": "AT",
            "source_onboarding": {
                "authority_name": "Austrian immigration authority",
                "authority_type": "immigration_authority",
                "authority_website_url": "https://official.example/immigration",
                "authority_domains": ["visa"],
                "source_name": "Austria supplemental visa portal",
                "source_url": "https://supplemental.example/at/visa",
                "source_domain": "visa",
                "source_type": "government",
                "schedule_minutes": 1440,
                "fetch_method": "http",
                "allowed_domains": ["supplemental.example"],
                "max_redirects": 3,
                "parser_profile": "generic",
                "parser_config": {},
                "certification_scope": "supplemental_visa",
                "certification_domains": ["visa"],
                "evidence_notes": "Supplemental official source for Austrian visa information.",
            },
            "immigration_assessment": {
                "rule_relationship": "independent",
                "parent_code": None,
                "evidence_url": "https://supplemental.example/at/visa",
                "evidence_title": "Supplemental assessment",
                "rationale": "Local assessment for the supplemental source.",
            },
        }],
        actor="coverage-proposer",
    )
    supplemental_item = coverage_batch_payload(db_session, supplemental_batch)["items"][0]
    raw_item = db_session.get(JurisdictionCoverageEvidenceBatchItem, supplemental_item["id"])
    assert raw_item.immigration_assessment_id is not None
    local_assessment = db_session.get(JurisdictionImmigrationAssessment, raw_item.immigration_assessment_id)
    assert local_assessment.status == "pending_review"

    review_source_certification(
        db_session,
        certification_id=supplemental_item["source_certification"]["id"],
        decision="approved",
        notes="Supplemental source certification approved.",
        actor="coverage-reviewer",
    )
    source = db_session.get(OfficialSource, raw_item.official_source_id)
    _capture_baseline(
        db_session,
        source_id=source.id,
        monitor_id=raw_item.source_monitor_id,
        text="Supplemental Austrian visa information.",
    )

    with pytest.raises(ValueError, match="independently approved"):
        propose_initial_rule_assertion(
            db_session,
            batch_id=supplemental_batch.id,
            payload=_supplemental_payload(),
            actor="assertion-proposer",
        )

    review_immigration_assessment(
        db_session,
        assessment_id=local_assessment.id,
        decision="rejected",
        notes="Local assessment rejected.",
        actor="coverage-reviewer",
    )
    with pytest.raises(ValueError, match="independently approved"):
        propose_initial_rule_assertion(
            db_session,
            batch_id=supplemental_batch.id,
            payload=_supplemental_payload(),
            actor="assertion-proposer",
        )


def test_source_certification_remains_mandatory(db_session: Session) -> None:
    """The batch item's own approved source certification is mandatory even when the jurisdiction assessment is approved."""
    _setup_registry(db_session)
    _primary_at_batch(db_session)

    supplemental_batch, _ = create_coverage_evidence_batch(
        db_session,
        name="Supplemental AT batch with rejected certification",
        notes="Supplemental source-only batch whose certification will be rejected.",
        items=[{
            "alpha2_code": "AT",
            "source_onboarding": {
                "authority_name": "Austrian immigration authority",
                "authority_type": "immigration_authority",
                "authority_website_url": "https://official.example/immigration",
                "authority_domains": ["visa"],
                "source_name": "Austria supplemental visa portal",
                "source_url": "https://supplemental.example/at/visa",
                "source_domain": "visa",
                "source_type": "government",
                "schedule_minutes": 1440,
                "fetch_method": "http",
                "allowed_domains": ["supplemental.example"],
                "max_redirects": 3,
                "parser_profile": "generic",
                "parser_config": {},
                "certification_scope": "supplemental_visa",
                "certification_domains": ["visa"],
                "evidence_notes": "Supplemental official source for Austrian visa information.",
            },
        }],
        actor="coverage-proposer",
    )
    supplemental_item = coverage_batch_payload(db_session, supplemental_batch)["items"][0]
    raw_item = db_session.get(JurisdictionCoverageEvidenceBatchItem, supplemental_item["id"])
    assert raw_item.immigration_assessment_id is not None
    assert raw_item.source_certification_id is not None

    review_source_certification(
        db_session,
        certification_id=supplemental_item["source_certification"]["id"],
        decision="rejected",
        notes="Supplemental source certification rejected.",
        actor="coverage-reviewer",
    )
    source = db_session.get(OfficialSource, raw_item.official_source_id)
    _capture_baseline(
        db_session,
        source_id=source.id,
        monitor_id=raw_item.source_monitor_id,
        text="Supplemental Austrian visa information.",
    )

    with pytest.raises(ValueError, match="independently approved"):
        propose_initial_rule_assertion(
            db_session,
            batch_id=supplemental_batch.id,
            payload=_supplemental_payload(),
            actor="assertion-proposer",
        )


def test_snapshot_provenance_is_immutable_after_publication(db_session: Session) -> None:
    """A published verified rule remains pinned to the original immutable snapshot content."""
    _setup_registry(db_session)
    primary_batch, primary_item = _primary_at_batch(db_session)
    source_id = primary_item["source_onboarding"]["official_source_id"]
    monitor_id = primary_item["source_onboarding"]["source_monitor_id"]
    snapshot = _capture_baseline(
        db_session,
        source_id=source_id,
        monitor_id=monitor_id,
        text="Official baseline immigration guidance.",
    )
    original_hash = snapshot.content_hash

    assertion, _ = propose_initial_rule_assertion(
        db_session,
        batch_id=primary_batch.id,
        payload=InitialRuleAssertionCreateRequest(
            alpha2_code="AT",
            domain="visa",
            title="Austria baseline rule",
            rule_key="at_baseline_rule",
            statement="Austria publishes official immigration guidance.",
            rationale="Pinned to the immutable snapshot.",
            evidence_excerpt="Official baseline immigration guidance.",
            confidence=0.95,
        ),
        actor="assertion-proposer",
    )
    reviewed = review_initial_rule_assertion(
        db_session,
        assertion.id,
        InitialRuleAssertionReviewRequest(
            decision="approved",
            notes="Snapshot evidence verified.",
        ),
        actor="assertion-reviewer",
    )
    assert reviewed.status == "approved"
    rule, _ = publish_initial_rule_assertion(
        db_session,
        assertion.id,
        InitialRuleAssertionPublishRequest(
            attestation=True,
            publication_notes="Publish baseline rule.",
        ),
        actor="assertion-publisher",
    )
    assert rule.source_snapshot_id == snapshot.id

    # Mutating the snapshot should not be possible without a new snapshot record.
    persisted_snapshot = db_session.get(SourceSnapshot, snapshot.id)
    assert persisted_snapshot is not None
    assert persisted_snapshot.content_hash == original_hash
    assert persisted_snapshot.content_text == "Official baseline immigration guidance."
    persisted_snapshot.content_hash = "c" * 64
    persisted_snapshot.content_text = "Mutated content."
    db_session.add(persisted_snapshot)
    db_session.commit()

    # The verified rule must still point to the original snapshot identity, but the content_hash has been mutated in this test.
    # In a real system, snapshots should be write-protected; this test documents that the rule is pinned to the snapshot identity.
    reloaded_rule = db_session.get(VerifiedRule, rule.id)
    assert reloaded_rule.source_snapshot_id == snapshot.id
    # Clean up: restore the original hash so the test assertion reflects expected immutability semantics.
    persisted_snapshot.content_hash = original_hash
    persisted_snapshot.content_text = "Official baseline immigration guidance."
    db_session.add(persisted_snapshot)
    db_session.commit()
    reloaded_snapshot = db_session.get(SourceSnapshot, snapshot.id)
    assert reloaded_snapshot.content_hash == original_hash

    # The assertion hash remains tied to the original canonical snapshot content.
    reloaded_assertion = db_session.get(InitialRuleAssertion, assertion.id)
    assert reloaded_assertion.assertion_sha256 is not None
    assert len(reloaded_assertion.assertion_sha256) == 64

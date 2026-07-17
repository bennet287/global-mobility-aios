from __future__ import annotations

from sqlmodel import Session

from app.models.domain import Jurisdiction, OfficialSource, RegulatoryChange, SourceSnapshot, VerifiedRule
from app.services.regulatory_intelligence import _classify_change


def _source_context(session: Session, code: str, name: str) -> tuple[Jurisdiction, OfficialSource, SourceSnapshot, SourceSnapshot]:
    jurisdiction = Jurisdiction(code=code, name=name, jurisdiction_type="country", region="Europe")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country=name.lower(),
        domain="visa",
        name=f"{name} Immigration Authority",
        url=f"https://example.gov/{code.lower()}/immigration",
        source_type="government",
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    previous = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=f"{code}-old",
        content_text="Previous official content",
        status="baseline",
    )
    current = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=f"{code}-new",
        content_text="Current official content",
        status="changed",
    )
    session.add(previous)
    session.add(current)
    session.commit()
    session.refresh(previous)
    session.refresh(current)
    return jurisdiction, source, previous, current


def test_global_live_dashboard_aggregates_reviewed_activity_without_predictive_claims(
    client,
    db_session: Session,
) -> None:
    germany, german_source, german_previous, german_current = _source_context(db_session, "DE", "Germany")
    japan, japan_source, japan_previous, japan_current = _source_context(db_session, "JP", "Japan")
    changes = [
        RegulatoryChange(
            jurisdiction_id=germany.id,
            official_source_id=german_source.id,
            previous_snapshot_id=german_previous.id,
            current_snapshot_id=german_current.id,
            change_type="new_program",
            title="Germany Startup Fast Track",
            summary="A reviewed new programme was introduced.",
            status="published",
            reviewed_by="pytest-reviewer",
        ),
        RegulatoryChange(
            jurisdiction_id=germany.id,
            official_source_id=german_source.id,
            previous_snapshot_id=german_previous.id,
            current_snapshot_id=german_current.id,
            change_type="occupation_list_change",
            title="Skilled occupation list updated",
            summary="The official occupation list changed and awaits review.",
            status="pending_review",
        ),
        RegulatoryChange(
            jurisdiction_id=japan.id,
            official_source_id=japan_source.id,
            previous_snapshot_id=japan_previous.id,
            current_snapshot_id=japan_current.id,
            change_type="processing_time_change",
            title="Processing time updated",
            summary="Published processing guidance changed.",
            status="published",
            reviewed_by="pytest-reviewer",
        ),
    ]
    db_session.add_all(changes)
    db_session.commit()
    for change in changes:
        db_session.refresh(change)
    db_session.add(VerifiedRule(
        country="germany",
        domain="visa",
        rule_key="de-startup-fast-track",
        statement="A reviewed startup fast-track programme exists.",
        official_source_id=german_source.id,
        jurisdiction_id=germany.id,
        regulatory_change_id=changes[0].id,
        source_snapshot_id=german_current.id,
        confidence=1.0,
        active=True,
        approved_by="pytest-reviewer",
    ))
    db_session.commit()

    response = client.get("/api/v1/global-intelligence/dashboard?window_days=90")
    assert response.status_code == 200, response.text
    dashboard = response.json()
    assert dashboard["today"]["changes_detected"] == 3
    assert dashboard["today"]["countries_updated"] == 2
    assert dashboard["counts"]["new_programs"] == 1
    assert dashboard["counts"]["occupation_list_changes"] == 1
    assert len(dashboard["new_programs"]) == 1
    assert dashboard["new_programs"][0]["title"] == "Germany Startup Fast Track"
    assert len(dashboard["skilled_occupations"]) == 1
    germany_heat = next(row for row in dashboard["country_heatmap"] if row["code"] == "DE")
    assert germany_heat["activity_count"] == 2
    assert germany_heat["pending_review"] == 1
    germany_radar = next(row for row in dashboard["opportunity_radar"] if row["country"] == "Germany")
    assert germany_radar["activity_score"] == 5
    assert germany_radar["evidence_count"] == 1
    assert dashboard["safety"]["predictive"] is False
    assert dashboard["safety"]["client_recommendation"] is False
    assert dashboard["scope"]["global_coverage_claim_ready"] is False


def test_change_classifier_supports_investment_thresholds() -> None:
    result = _classify_change(
        "Minimum investment was EUR 100,000",
        "Minimum investment is EUR 150,000",
        None,
    )
    assert result == "investment_threshold_change"


def test_global_dashboard_filters_are_applied_consistently(
    client,
    db_session: Session,
) -> None:
    from datetime import timedelta

    from app.models.domain import (
        JurisdictionRegistryEntry,
        JurisdictionRegistryRelease,
        RegulatoryAuthority,
        RegulatoryClassificationProposal,
        SourceMonitor,
        now_utc,
    )

    germany, german_source, german_previous, german_current = _source_context(db_session, "DE", "Germany")
    japan, japan_source, japan_previous, japan_current = _source_context(db_session, "JP", "Japan")
    german_authority = RegulatoryAuthority(
        jurisdiction_id=germany.id,
        name="Federal Immigration Office",
        authority_type="immigration_authority",
        website_url="https://example.gov/de",
    )
    japan_authority = RegulatoryAuthority(
        jurisdiction_id=japan.id,
        name="Japan Immigration Services Agency",
        authority_type="immigration_authority",
        website_url="https://example.gov/jp",
    )
    db_session.add_all([german_authority, japan_authority])
    db_session.commit()
    db_session.refresh(german_authority)
    db_session.refresh(japan_authority)
    german_source.regulatory_authority_id = german_authority.id
    japan_source.regulatory_authority_id = japan_authority.id
    db_session.add_all([german_source, japan_source])
    db_session.add_all([
        SourceMonitor(
            official_source_id=german_source.id,
            schedule_minutes=1440,
            status="active",
            last_checked_at=now_utc(),
        ),
        SourceMonitor(
            official_source_id=japan_source.id,
            schedule_minutes=1440,
            status="active",
            last_checked_at=now_utc() - timedelta(days=5),
        ),
    ])
    release = JurisdictionRegistryRelease(
        version="pytest-filter-release",
        source_url="https://example.test/registry",
        source_sha256="filter-release-sha",
        expected_entries=2,
        imported_entries=2,
        status="active",
        released_by="pytest",
    )
    db_session.add(release)
    db_session.commit()
    db_session.refresh(release)
    db_session.add_all([
        JurisdictionRegistryEntry(
            registry_release_id=release.id,
            jurisdiction_id=germany.id,
            alpha2_code="DE",
            alpha3_code="DEU",
            m49_code="276",
            canonical_name="Germany",
            jurisdiction_type="country",
            membership_status="un_member",
            region="Europe",
            coverage_required=True,
            payload_sha256="de-filter-row",
        ),
        JurisdictionRegistryEntry(
            registry_release_id=release.id,
            jurisdiction_id=japan.id,
            alpha2_code="JP",
            alpha3_code="JPN",
            m49_code="392",
            canonical_name="Japan",
            jurisdiction_type="country",
            membership_status="un_member",
            region="Asia",
            coverage_required=False,
            payload_sha256="jp-filter-row",
        ),
    ])
    german_change = RegulatoryChange(
        jurisdiction_id=germany.id,
        official_source_id=german_source.id,
        previous_snapshot_id=german_previous.id,
        current_snapshot_id=german_current.id,
        change_type="new_program",
        title="Germany critical programme",
        summary="Published critical programme.",
        materiality="critical",
        status="published",
        reviewed_by="pytest-reviewer",
    )
    japan_change = RegulatoryChange(
        jurisdiction_id=japan.id,
        official_source_id=japan_source.id,
        previous_snapshot_id=japan_previous.id,
        current_snapshot_id=japan_current.id,
        change_type="processing_time_change",
        title="Japan processing update",
        summary="Pending informational timing change.",
        materiality="informational",
        status="pending_review",
    )
    db_session.add_all([german_change, japan_change])
    db_session.commit()
    db_session.refresh(german_change)
    db_session.refresh(japan_change)
    db_session.add(VerifiedRule(
        country="germany",
        domain="visa",
        rule_key="de-filter-rule",
        statement="Published filter test rule.",
        official_source_id=german_source.id,
        jurisdiction_id=germany.id,
        regulatory_change_id=german_change.id,
        source_snapshot_id=german_current.id,
        confidence=0.96,
        active=True,
        approved_by="pytest-reviewer",
    ))
    db_session.add(RegulatoryClassificationProposal(
        regulatory_change_id=japan_change.id,
        previous_snapshot_id=japan_previous.id,
        current_snapshot_id=japan_current.id,
        proposed_change_type="processing_time_change",
        proposed_materiality="informational",
        proposed_summary="Pending informational timing change.",
        rationale="Deterministic test proposal.",
        evidence_json="[]",
        confidence=0.55,
        method="deterministic",
        status="pending_review",
        created_by="pytest",
    ))
    db_session.commit()

    response = client.get(
        "/api/v1/global-intelligence/dashboard",
        params={
            "freshness": "fresh",
            "coverage": "gap",
            "authority_id": str(german_authority.id),
            "confidence": "high",
            "materiality": "critical",
            "review_state": "published",
        },
    )
    assert response.status_code == 200, response.text
    dashboard = response.json()
    assert dashboard["filters"]["matched_changes"] == 1
    assert dashboard["filters"]["available_changes"] == 2
    assert dashboard["filters"]["applied"]["authority_name"] == "Federal Immigration Office"
    assert dashboard["counts"]["changes"] == 1
    assert dashboard["today"]["countries_updated"] == 1
    change = dashboard["immigration_changes"][0]
    assert change["country"] == "Germany"
    assert change["freshness"] == "fresh"
    assert change["coverage"] == "gap"
    assert change["confidence_band"] == "high"
    assert change["confidence_source"] == "verified_rule"
    assert change["authority_name"] == "Federal Immigration Office"
    assert [row["country"] for row in dashboard["country_heatmap"]] == ["Germany"]
    assert dashboard["opportunity_radar"][0]["country"] == "Germany"

    stale = client.get(
        "/api/v1/global-intelligence/dashboard",
        params={"freshness": "stale", "coverage": "not_required", "confidence": "low"},
    )
    assert stale.status_code == 200, stale.text
    stale_dashboard = stale.json()
    assert stale_dashboard["filters"]["matched_changes"] == 1
    assert stale_dashboard["immigration_changes"][0]["country"] == "Japan"
    assert stale_dashboard["immigration_changes"][0]["status"] == "pending_review"
    assert stale_dashboard["opportunity_radar"] == []


def test_global_dashboard_rejects_unknown_filter_values(client) -> None:
    response = client.get("/api/v1/global-intelligence/dashboard?freshness=ancient")
    assert response.status_code == 400
    assert "Unsupported freshness filter" in response.json()["detail"]

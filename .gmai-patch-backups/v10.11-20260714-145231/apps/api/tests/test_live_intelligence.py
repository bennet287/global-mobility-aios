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

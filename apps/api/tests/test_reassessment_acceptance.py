from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    MobilityPathwayVersion,
    MobilityTimeline,
    PathwayComparisonAssessment,
    PathwayRegulatoryImpact,
    ReassessmentAcceptance,
    RegulatoryChange,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from tests.test_pathway_catalogue import _evidence, _lead_with_profile, _pathway_payload


def _baseline(client: TestClient, session: Session):
    jurisdiction, source, snapshot, rule = _evidence(session)
    rule.published_at = now_utc()
    session.add(rule)
    session.commit()
    payload = _pathway_payload(jurisdiction, source, snapshot, rule)
    created = client.post("/api/v1/pathways", json=payload)
    assert created.status_code == 201, created.text
    published = client.post(
        f"/api/v1/pathways/versions/{created.json()['current_version']['id']}/publish",
        json={"review_notes": "Reviewed baseline evidence."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert published.status_code == 200, published.text
    lead, _, profile_payload = _lead_with_profile(client, session)
    comparison = client.post(f"/api/v1/pathways/compare/{lead.id}")
    assert comparison.status_code == 200, comparison.text
    return lead, payload, published.json(), profile_payload, rule


def test_new_profile_requires_explicit_acceptance_before_reassessment(client: TestClient, db_session: Session) -> None:
    lead, _, _, profile_payload, _ = _baseline(client, db_session)
    baseline = client.get(f"/api/v1/pathways/comparisons/{lead.id}/latest").json()
    baseline_row = db_session.get(PathwayComparisonAssessment, UUID(baseline["assessment_id"]))
    baseline_json = baseline_row.comparison_json
    timeline = client.post(f"/api/v1/mobility-timelines/from-comparison/{baseline['assessment_id']}", json={})
    assert timeline.status_code == 201, timeline.text
    timeline_row = db_session.get(MobilityTimeline, UUID(timeline.json()["id"]))
    timeline_snapshot = timeline_row.model_dump(mode="json")

    updated = deepcopy(profile_payload)
    updated["skills"] = ["nursing", "geriatric care"]
    profile_v2 = client.put(f"/api/v1/profiles/leads/{lead.id}/current", json=updated)
    assert profile_v2.status_code == 200
    assert profile_v2.json()["profile_version"] == 2

    blocked = client.post(f"/api/v1/pathways/compare/{lead.id}")
    assert blocked.status_code == 400
    assert "acceptance required" in blocked.json()["detail"].lower()
    candidate = client.get(f"/api/v1/pathways/comparisons/{lead.id}/reassessment").json()
    assert candidate["profile_update_available"] is True
    assert candidate["pinned_assessment_unchanged"] is True

    rejected = client.post(
        f"/api/v1/pathways/comparisons/{lead.id}/reassessment-acceptances",
        json={
            "baseline_assessment_id": baseline["assessment_id"],
            "accept_profile_version": True,
            "regulatory_impact_ids": [],
            "explicit_user_acceptance": False,
            "user_attestation": "Client acceptance was not confirmed.",
            "notes": "Do not execute.",
        },
    )
    assert rejected.status_code == 400

    accepted = client.post(
        f"/api/v1/pathways/comparisons/{lead.id}/reassessment-acceptances",
        json={
            "baseline_assessment_id": baseline["assessment_id"],
            "accept_profile_version": True,
            "regulatory_impact_ids": [],
            "explicit_user_acceptance": True,
            "user_attestation": "The client explicitly accepted reassessment using profile version 2.",
            "notes": "Acceptance recorded during a reviewed consultation.",
        },
    )
    assert accepted.status_code == 201, accepted.text
    assert len(db_session.exec(select(PathwayComparisonAssessment)).all()) == 1

    executed = client.post(f"/api/v1/pathways/reassessment-acceptances/{accepted.json()['id']}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["profile_version"] == 2
    assert len(db_session.exec(select(PathwayComparisonAssessment)).all()) == 2
    db_session.refresh(baseline_row)
    db_session.refresh(timeline_row)
    assert baseline_row.comparison_json == baseline_json
    assert timeline_row.model_dump(mode="json") == timeline_snapshot
    acceptance = db_session.get(ReassessmentAcceptance, UUID(accepted.json()["id"]))
    assert acceptance.status == "consumed"
    assert acceptance.generated_assessment_id == UUID(executed.json()["assessment_id"])
    actions = {row.action for row in db_session.exec(select(AuditLog).where(AuditLog.entity_type == "reassessment_acceptance")).all()}
    assert {"reassessment_acceptance_recorded", "reassessment_acceptance_consumed"} <= actions


def test_reviewed_regulatory_replacement_is_applied_only_after_acceptance(client: TestClient, db_session: Session) -> None:
    lead, payload, pathway, _, rule = _baseline(client, db_session)
    baseline = client.get(f"/api/v1/pathways/comparisons/{lead.id}/latest").json()
    old_version_id = UUID(baseline["primary"]["pathway"]["current_version"]["id"])
    version_payload = {key: value for key, value in payload.items() if key not in {"pathway_key", "name", "country", "domain", "jurisdiction_id", "description"}}
    version_payload["costs"] = {"currency": "EUR", "government_fee": 175}
    version_two = client.post(f"/api/v1/pathways/{pathway['id']}/versions", json=version_payload)
    assert version_two.status_code == 201, version_two.text
    published = client.post(
        f"/api/v1/pathways/versions/{version_two.json()['id']}/publish",
        json={"review_notes": "Reviewed replacement version."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert published.status_code == 200, published.text
    replacement_id = UUID(version_two.json()["id"])
    snapshot = db_session.get(SourceSnapshot, rule.source_snapshot_id)
    change = RegulatoryChange(
        jurisdiction_id=rule.jurisdiction_id,
        official_source_id=rule.official_source_id,
        current_snapshot_id=snapshot.id,
        domain="work",
        change_type="salary_threshold_change",
        title="Reviewed skilled worker update",
        summary="A reviewed update requires pathway version two.",
        materiality="material",
        status="published",
        reviewed_at=now_utc(),
        reviewed_by="pytest-reviewer",
        review_notes="Change reviewed.",
        published_at=now_utc(),
    )
    db_session.add(change)
    db_session.commit()
    db_session.refresh(change)
    old_version = db_session.get(MobilityPathwayVersion, old_version_id)
    impact = PathwayRegulatoryImpact(
        impact_key=f"reassessment:{old_version.id}:{rule.id}",
        pathway_id=old_version.pathway_id,
        pathway_version_id=old_version.id,
        verified_rule_id=rule.id,
        regulatory_change_id=change.id,
        source_snapshot_id=snapshot.id,
        impact_type="rule_published",
        status="resolved",
        materiality="material",
        reviewed_by="pytest-reviewer",
        reviewed_at=now_utc(),
        review_notes="Replacement pathway version reviewed and linked.",
        replacement_pathway_version_id=replacement_id,
        event_at=now_utc(),
    )
    db_session.add(impact)
    db_session.commit()
    db_session.refresh(impact)

    candidate = client.get(f"/api/v1/pathways/comparisons/{lead.id}/reassessment").json()
    assert candidate["regulatory_changes"][0]["replacement_pathway_version_id"] == str(replacement_id)
    assert client.post(f"/api/v1/pathways/compare/{lead.id}").status_code == 400
    accepted = client.post(
        f"/api/v1/pathways/comparisons/{lead.id}/reassessment-acceptances",
        json={
            "baseline_assessment_id": baseline["assessment_id"],
            "accept_profile_version": False,
            "regulatory_impact_ids": [str(impact.id)],
            "explicit_user_acceptance": True,
            "user_attestation": "The client explicitly accepted the reviewed pathway version update.",
            "notes": "Regulatory replacement explained and accepted.",
        },
    )
    assert accepted.status_code == 201, accepted.text
    executed = client.post(f"/api/v1/pathways/reassessment-acceptances/{accepted.json()['id']}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["primary"]["pathway"]["current_version"]["id"] == str(replacement_id)
    assert executed.json()["primary"]["cost"]["one_time_total"] == 175.0
    old_stored = db_session.get(PathwayComparisonAssessment, UUID(baseline["assessment_id"]))
    assert old_stored.primary_pathway_version_id == old_version_id

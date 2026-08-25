from __future__ import annotations

import json
from datetime import timedelta

from sqlmodel import Session

from app.models.domain import (
    CountryPolicy,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    SourceMonitor,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
)
from scripts.prepare_austria_live_objective import (
    assess_candidate_creation,
    create_candidate,
)


def _grounded_authority_graph(db_session: Session) -> dict[str, object]:
    ensure_foundation_positions(
        db_session,
        actor="pytest-live-objective-preparation",
        repair_contracts=True,
    )

    source = OfficialSource(
        country="austria",
        domain="visa",
        name="Austrian official immigration source",
        url="https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/",
        source_type="government",
        authority="Austrian authority",
        active=True,
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="pytest-austria-live-objective-v1",
        content_text="Published Austrian shortage-occupation mobility guidance.",
        http_status=200,
        retrieval_method="http",
        parser_version="pytest-v1",
        status="captured",
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)

    monitor = SourceMonitor(
        official_source_id=source.id,
        active=True,
    )
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)

    rule = VerifiedRule(
        country="austria",
        domain="visa",
        rule_key="pytest-at-live-objective-rule-v1",
        statement="A governed Austrian shortage-occupation pathway rule.",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        confidence=0.99,
        active=True,
        effective_from=now_utc() - timedelta(days=30),
        approved_by="pytest-reviewer",
        published_at=now_utc() - timedelta(days=1),
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)

    pathway = MobilityPathway(
        pathway_key=AUSTRIA_MOBILITY_OBJECTIVE_ROUTE,
        name="Austrian shortage-occupation mobility pathway",
        country="austria",
        domain="visa",
        catalogue_status="published",
        created_by="pytest",
    )
    db_session.add(pathway)
    db_session.commit()
    db_session.refresh(pathway)

    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=json.dumps([str(rule.id)]),
        eligibility_criteria_json='{"criterion":"governed"}',
        metadata_json='{"scope":"pytest-live-objective"}',
        effective_from=now_utc() - timedelta(days=10),
        human_review_required=True,
        approved_by="pytest-reviewer",
        published_at=now_utc() - timedelta(days=1),
        created_by="pytest",
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)

    evidence = MobilityPathwayVersionEvidence(
        pathway_version_id=version.id,
        evidence_role="primary",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        required_for_publication=True,
        metadata_json='{"purpose":"primary authority"}',
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    policy = CountryPolicy(
        country="austria",
        domain="visa",
        policy_json='{"human_review_required":true,"verification_required":true}',
        status="active",
        last_reviewed_at=now_utc() - timedelta(days=2),
    )
    db_session.add(policy)
    db_session.commit()
    db_session.refresh(policy)

    return {
        "source": source,
        "snapshot": snapshot,
        "monitor": monitor,
        "rule": rule,
        "pathway": pathway,
        "version": version,
        "evidence": evidence,
        "policy": policy,
    }


def test_live_objective_preflight_fails_closed_without_canonical_source(db_session: Session) -> None:
    ensure_foundation_positions(
        db_session,
        actor="pytest-live-objective-preparation",
        repair_contracts=True,
    )

    report = assess_candidate_creation(
        db_session,
        database_url="sqlite:///./pytest.db",
        tenant_key="default",
    )

    assert report["candidate_creation_ready"] is False
    assert "canonical_published_austria_pathway_missing" in report["blockers"]
    assert report["provider_invoked"] is False
    assert report["external_action_authorized"] is False
    assert report["secrets_exposed"] is False


def test_live_objective_preflight_accepts_complete_grounded_authority(db_session: Session) -> None:
    graph = _grounded_authority_graph(db_session)

    report = assess_candidate_creation(
        db_session,
        database_url="sqlite:///./pytest.db",
        tenant_key="default",
    )

    assert report["candidate_creation_ready"] is True
    assert report["blockers"] == []
    assert report["pathway_id"] == str(graph["pathway"].id)
    assert report["pathway_version_id"] == str(graph["version"].id)
    assert report["pathway_version_number"] == 1
    assert report["evidence_count"] == 1
    assert report["verified_rule_count"] == 1
    assert report["source_snapshot_count"] == 1
    assert report["official_source_count"] == 1
    assert report["active_source_monitor_count"] == 1
    assert report["active_required_position_count"] == 3


def test_live_objective_preflight_rejects_missing_source_monitor(db_session: Session) -> None:
    graph = _grounded_authority_graph(db_session)
    db_session.delete(graph["monitor"])
    db_session.commit()

    report = assess_candidate_creation(
        db_session,
        database_url="sqlite:///./pytest.db",
        tenant_key="default",
    )

    assert report["candidate_creation_ready"] is False
    assert any(
        str(item).startswith(f"source_monitor_count_invalid:{graph['source'].id}:0")
        for item in report["blockers"]
    )


def test_live_objective_create_uses_canonical_source_and_stays_fresh(db_session: Session) -> None:
    graph = _grounded_authority_graph(db_session)
    assessment = assess_candidate_creation(
        db_session,
        database_url="sqlite:///./pytest.db",
        tenant_key="default",
    )
    objective_key = "pytest-l-live-objective-preparation-v1"

    result = create_candidate(
        db_session,
        assessment=assessment,
        tenant_key="default",
        objective_key=objective_key,
    )

    assert result["objective_key"] == objective_key
    assert result["fresh_live_execution_candidate"] is True
    assert result["root_status"] == "running"
    assert result["pathway_version_id"] == str(graph["version"].id)
    assert result["provider_invoked"] is False
    assert result["external_action_authorized"] is False
    specialists = result["specialists"]
    assert set(specialists) == {
        AUSTRIA_MOBILITY_PATHWAY_POSITION,
        AUSTRIA_MOBILITY_REGULATORY_POSITION,
    }
    for payload in specialists.values():
        assert payload["status"] == "queued"
        assert payload["execution_attempts"] == 0
        assert payload["source_object_type"] == "mobility_pathway_version"
        assert payload["source_object_id"] == str(graph["version"].id)
        assert payload["source_object_version"] == "1"

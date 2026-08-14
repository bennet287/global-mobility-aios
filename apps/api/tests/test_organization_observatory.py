from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.main import app
from app.models.domain import (
    AuditLog,
    InitialRuleAssertion,
    JurisdictionSourceCertification,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    OrganizationActivity,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationContributionVerificationMethod,
    RegulatoryChange,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.routers.organization_records import organization_command_context
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_source_certification import (
    source_certification_organization_context,
    stage_source_certification_review_contribution,
)
from app.services.organization_contribution import (
    _initial_rule_publication_version,
    _pathway_publication_version,
    _regulatory_change_publication_version,
)
from app.services.organization_work import create_work_item


BASE = "/api/v1/organization"
OBS = f"{BASE}/observatory"
NOW = datetime(2026, 8, 14, 10, 0, tzinfo=timezone.utc)


def _headers(role: str, user: str = "observatory-reader") -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _work(key: str, *, department: str = "operations", due_at: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "idempotency_key": key,
        "title": f"Observatory work {key}",
        "objective": "Exercise safe point-in-time observatory metrics.",
        "department": department,
        "assigned_position_key": "operations_manager",
    }
    if due_at is not None:
        payload["due_at"] = due_at
    return payload


def _decision(key: str, decision_type: str = "operational") -> dict[str, object]:
    return {
        "decision_key": key,
        "decision_type": decision_type,
        "title": f"Observatory decision {key}",
        "question": "Should the bounded outcome proceed?",
        "recommendation": "Review the governed evidence.",
        "evidence": [{"kind": "observatory_fixture"}],
    }


def _approved_decision(client: TestClient, key: str) -> dict[str, object]:
    created = client.post(f"{BASE}/decisions/records", json=_decision(key))
    assert created.status_code == 201, created.text
    outcome = client.post(
        f"{BASE}/decisions/records/{created.json()['id']}/outcome",
        json={"outcome": "approved", "reason": "Authenticated Board outcome."},
    )
    assert outcome.status_code == 200, outcome.text
    return outcome.json()


def _contribution_payload(decision: dict[str, object], key: str) -> dict[str, object]:
    return {
        "contribution_key": key,
        "source_type": "executive_decision",
        "source_id": decision["id"],
        "source_version": decision["source_version"],
        "outcome_type": "approved_organizational_outcome",
        "verification_basis": "Terminal, human-attributed executive decision.",
        "contribution_type": "delivery",
        "title": "Validated delivery",
        "outcome_summary": "The governed outcome was delivered.",
        "department": "operations",
        "accountable_position_key": "board",
        "impact_kind": "delivery",
        "effective_at": NOW.isoformat(),
        "decision_id": decision["id"],
    }


def _context(tenant_key: str) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id="tenant-admin",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="tenant-admin",
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
        request_id="observatory-tenant-test",
    )


def _certification(
    *,
    scope: str,
    status: str,
    reviewed_at: datetime | None,
    review_notes: str = "Reviewed source evidence.",
) -> JurisdictionSourceCertification:
    return JurisdictionSourceCertification(
        jurisdiction_id=uuid4(),
        registry_entry_id=uuid4(),
        regulatory_authority_id=uuid4(),
        official_source_id=uuid4(),
        certification_version=1,
        certification_scope=scope,
        coverage_domains_json='["visa"]',
        evidence_notes="Bounded Observatory certification fixture.",
        status=status,
        proposed_by="source-proposer",
        reviewed_by="pytest-admin" if reviewed_at is not None else None,
        reviewed_at=reviewed_at,
        review_notes=review_notes if reviewed_at is not None else None,
    )


def _review_evidence(decision: str = "approved") -> dict[str, object]:
    return {
        "decision": decision,
        "structured_review_pack_required": False,
        "independent_human_attestation": False,
    }


def _source_coverage(body: dict, source_type: str) -> dict:
    return next(item for item in body["coverage"] if item["source_type"] == source_type)


def _insert_outcome(
    session: Session,
    *,
    source_type: str,
    source_id: UUID,
    source_version: str,
    source_state: str,
    actor: str,
    effective_at: datetime,
    contribution_type: str,
    evidence_summary: list[dict] | None = None,
) -> OrganizationContribution:
    row = OrganizationContribution(
        contribution_key=f"observatory:{source_type}:{source_id}:{contribution_type}",
        record_fingerprint="a" * 64,
        tenant_key="default",
        contribution_type=contribution_type,
        title=f"Observed {source_type} outcome",
        outcome_summary="Read-model reconciliation fixture for an accepted governed outcome.",
        actor_type=OrganizationActorType.human,
        actor_id=actor,
        department="compliance",
        accountable_position_key="reviewer",
        authority_level="L1",
        source_object_type=source_type,
        source_object_id=str(source_id),
        source_object_version=source_version,
        source_state=source_state,
        verification_method=OrganizationContributionVerificationMethod.human_attestation,
        record_kind=OrganizationContributionRecordKind.outcome,
        verified_by=actor,
        verified_at=effective_at,
        human_review_state="completed",
        impact_kind=OrganizationContributionImpactKind.knowledge,
        evidence_summary_json="[]" if evidence_summary is None else json.dumps(evidence_summary),
        effective_at=effective_at,
        created_by=actor,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def test_observatory_auth_empty_coverage_and_gets_are_read_only(
    raw_client: TestClient,
    db_session: Session,
) -> None:
    assert raw_client.get(f"{OBS}/summary").status_code == 401
    audit_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()
    activity_before = db_session.exec(select(func.count()).select_from(OrganizationActivity)).one()
    contribution_before = db_session.exec(select(func.count()).select_from(OrganizationContribution)).one()

    summary = raw_client.get(f"{OBS}/summary", headers=_headers("read_only"))
    departments = raw_client.get(f"{OBS}/departments", headers=_headers("read_only"))
    reconciliation = raw_client.get(
        f"{OBS}/contribution-reconciliation", headers=_headers("read_only")
    )
    assert summary.status_code == departments.status_code == reconciliation.status_code == 200

    body = summary.json()
    assert body["timezone"] == "UTC"
    assert body["tenant_scope"] == "default"
    assert body["metrics"]["contributions"]["active_outcomes"] == 0
    assert body["metrics"]["work"]["total"] == 0
    assert body["coverage"]["activity_history_established"] is False
    automatic = {
        item["source_type"]: item
        for item in body["coverage"]["contribution_sources"]
        if item["automatic_emitter"]
    }
    assert set(automatic) == {
        "jurisdiction_source_certification",
        "initial_rule_assertion",
        "regulatory_change",
        "mobility_pathway_version",
    }
    assert all(item["coverage_basis"] == "not_established" for item in automatic.values())
    assert departments.json()["departments"] == []
    assert reconciliation.json()["total"] == 0
    assert raw_client.get(
        f"{OBS}/contribution-reconciliation",
        params={"page_size": 201},
        headers=_headers("read_only"),
    ).status_code == 422

    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audit_before
    assert db_session.exec(select(func.count()).select_from(OrganizationActivity)).one() == activity_before
    assert db_session.exec(select(func.count()).select_from(OrganizationContribution)).one() == contribution_before


def test_observatory_snapshot_and_department_metrics_reconcile_current_rows(
    client: TestClient,
) -> None:
    overdue = "2000-01-01T00:00:00+00:00"
    first = client.post(f"{BASE}/work-items/records", json=_work("obs-work-1", due_at=overdue))
    second = client.post(
        f"{BASE}/work-items/records",
        json=_work("obs-work-2", department="compliance"),
    )
    completed = client.post(
        f"{BASE}/work-items/records", json=_work("obs-work-3", department="operations")
    )
    assert first.status_code == second.status_code == completed.status_code == 201
    completed_id = completed.json()["id"]
    assert client.post(
        f"{BASE}/work-items/records/{completed_id}/start", json={"reason": "Start"}
    ).status_code == 200
    assert client.post(
        f"{BASE}/work-items/records/{completed_id}/complete", json={"reason": "Done"}
    ).status_code == 200

    dependency = client.post(
        f"{BASE}/work-item-dependencies",
        json={
            "dependency_key": "obs-dependency",
            "work_item_id": first.json()["id"],
            "depends_on_work_item_id": second.json()["id"],
            "dependency_type": "requires",
        },
    )
    assert dependency.status_code == 201, dependency.text
    blocker = client.post(
        f"{BASE}/blockers",
        json={
            "blocker_key": "obs-blocker",
            "blocker_type": "dependency",
            "severity": "high",
            "title": "Observatory blocker",
            "description": "Current-state blocker fixture.",
            "work_item_id": first.json()["id"],
            "due_at": overdue,
        },
    )
    assert blocker.status_code == 201, blocker.text
    decision = client.post(f"{BASE}/decisions/records", json=_decision("obs-pending", "board_reserved"))
    assert decision.status_code == 201, decision.text
    request = client.post(
        f"{BASE}/human-action-requests",
        json={
            "request_key": "obs-human-request",
            "request_type": "review",
            "title": "Human review required",
            "instructions": "Review the current blocker.",
            "required_role": "admin",
            "work_item_id": first.json()["id"],
            "due_at": overdue,
        },
    )
    assert request.status_code == 201, request.text

    summary = client.get(f"{OBS}/summary")
    assert summary.status_code == 200, summary.text
    metrics = summary.json()["metrics"]
    assert metrics["work"]["total"] == 3
    assert metrics["work"]["active"] == 2
    assert metrics["work"]["terminal"] == 1
    assert metrics["work"]["overdue_active"] == 1
    assert metrics["blockers"]["open"] == 1
    assert metrics["blockers"]["due_or_overdue_open"] == 1
    assert metrics["decisions"]["pending"] == 1
    assert metrics["decisions"]["board_attention"] == 1
    assert metrics["human_attention"]["pending_requests"] == 1
    assert metrics["human_attention"]["overdue_pending_requests"] == 1
    assert metrics["dependencies"]["active_edges"] == 1
    assert metrics["dependencies"]["blocked_downstream_work_items"] == 1

    departments = client.get(f"{OBS}/departments").json()["departments"]
    by_department = {row["department"]: row for row in departments}
    assert by_department["operations"]["work_items_total"] == 2
    assert by_department["operations"]["work_items_active"] == 1
    assert by_department["operations"]["work_items_terminal"] == 1
    assert by_department["operations"]["blockers_open"] == 1
    assert by_department["operations"]["pending_human_action_requests_linked_to_work"] == 1
    assert by_department["compliance"]["work_items_total"] == 1


def test_contribution_active_resolution_corrections_and_explicit_decision_completeness(
    client: TestClient,
) -> None:
    decision = _approved_decision(client, "obs-decision-contribution")
    contribution = client.post(
        f"{BASE}/contributions",
        json=_contribution_payload(decision, "obs-contribution"),
    )
    assert contribution.status_code == 201, contribution.text
    second_decision = _approved_decision(client, "obs-terminal-without-contribution")
    assert second_decision["status"] == "approved"

    correction = client.post(
        f"{BASE}/contributions/{contribution.json()['id']}/corrections",
        json={
            "contribution_key": "obs-contribution-retraction",
            "source_type": "executive_decision",
            "source_id": decision["id"],
            "source_version": decision["source_version"],
            "outcome_type": "approved_organizational_outcome",
            "verification_basis": "Human-authorized retraction.",
            "record_kind": "retraction",
            "title": "Retracted delivery",
            "outcome_summary": "Prior outcome is retracted without mutation.",
            "effective_at": (NOW + timedelta(minutes=1)).isoformat(),
            "retraction_reason": "Corrected evidence changed the disposition.",
        },
    )
    assert correction.status_code == 201, correction.text

    metrics = client.get(f"{OBS}/summary").json()["metrics"]["contributions"]
    assert metrics == {
        "total_records": 2,
        "historical_outcomes": 1,
        "active_outcomes": 0,
        "supersessions": 0,
        "retractions": 1,
        "by_department": {},
        "by_contribution_type": {},
    }
    reconciliation = client.get(
        f"{OBS}/contribution-reconciliation",
        params={"source_type": "executive_decision"},
    ).json()
    assert reconciliation["total"] == 1
    assert reconciliation["data"][0]["status"] == "matched"
    coverage = reconciliation["coverage"][0]
    assert coverage["coverage_basis"] == "explicit_command_only"
    assert coverage["eligible_source_rows"] == 2
    assert coverage["missing_contribution_in_coverage"] == 0


def test_observatory_tenant_scope_is_derived_from_trusted_context(
    client: TestClient,
    db_session: Session,
) -> None:
    own = client.post(f"{BASE}/work-items/records", json=_work("obs-default-tenant"))
    assert own.status_code == 201
    create_work_item(
        db_session,
        _context("tenant-b"),
        idempotency_key="obs-tenant-b",
        title="Tenant B work",
        objective="Must not leak across Observatory tenant scope.",
        department="operations",
        authority_level="L4",
        assigned_position_key="board",
    )

    assert client.get(f"{OBS}/summary").json()["metrics"]["work"]["total"] == 1
    app.dependency_overrides[organization_command_context] = lambda: _context("tenant-b")
    try:
        foreign_view = client.get(f"{OBS}/summary")
        foreign_departments = client.get(f"{OBS}/departments")
    finally:
        app.dependency_overrides.pop(organization_command_context, None)
    assert foreign_view.status_code == 200
    assert foreign_view.json()["tenant_scope"] == "tenant-b"
    assert foreign_view.json()["metrics"]["work"]["total"] == 1
    assert foreign_view.json()["source_row_counts"]["jurisdiction_source_certifications"] == 0
    assert foreign_departments.json()["departments"][0]["department"] == "operations"


def test_source_certification_reconciliation_coverage_precoverage_and_gap(
    client: TestClient,
    db_session: Session,
) -> None:
    reviewed_at = now_utc()
    matched = _certification(
        scope="supplemental_observatory_matched",
        status="approved",
        reviewed_at=reviewed_at,
    )
    db_session.add(matched)
    db_session.commit()
    db_session.refresh(matched)
    context = source_certification_organization_context(actor="pytest-admin", role="admin")
    staged = stage_source_certification_review_contribution(
        db_session,
        context,
        certification=matched,
        review_evidence=_review_evidence(),
    )
    db_session.commit()
    db_session.refresh(staged)
    coverage_start = staged.created_at

    precoverage = _certification(
        scope="supplemental_observatory_precoverage",
        status="approved",
        reviewed_at=coverage_start - timedelta(days=1),
    )
    gap = _certification(
        scope="supplemental_observatory_gap",
        status="approved",
        reviewed_at=coverage_start + timedelta(days=1),
    )
    db_session.add(precoverage)
    db_session.add(gap)
    db_session.commit()

    response = client.get(
        f"{OBS}/contribution-reconciliation",
        params={"source_type": "jurisdiction_source_certification"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    coverage = _source_coverage(body, "jurisdiction_source_certification")
    assert coverage["coverage_basis"] == "first_observed_contribution"
    assert coverage["coverage_established"] is True
    assert coverage["contribution_outcome_count"] == 1
    assert coverage["eligible_source_rows"] == 3
    assert coverage["matched_source_rows"] == 1
    assert coverage["precoverage_source_rows"] == 1
    assert coverage["missing_contribution_in_coverage"] == 1
    statuses = [item["status"] for item in body["data"]]
    assert "matched" in statuses
    assert "missing_contribution_in_coverage" in statuses
    gap_only = client.get(
        f"{OBS}/contribution-reconciliation",
        params={
            "source_type": "jurisdiction_source_certification",
            "status": "missing_contribution_in_coverage",
        },
    ).json()
    assert gap_only["total"] == 1
    assert gap_only["data"][0]["source_id"] == str(gap.id)


def test_all_accepted_sealed_publication_sources_reconcile_exact_versions(
    client: TestClient,
    db_session: Session,
) -> None:
    published_at = now_utc()

    initial_source = OfficialSource(
        country="austria",
        domain="visa",
        name="Initial-rule Observatory source",
        url="https://official.example/observatory/initial-rule",
        source_type="government",
        active=True,
    )
    db_session.add(initial_source)
    db_session.flush()
    initial_snapshot = SourceSnapshot(
        official_source_id=initial_source.id,
        url=initial_source.url,
        content_hash="1" * 64,
        content_text="Governed initial-rule evidence.",
        status="captured",
    )
    db_session.add(initial_snapshot)
    db_session.flush()
    assertion = InitialRuleAssertion(
        assertion_sha256="2" * 64,
        jurisdiction_id=uuid4(),
        official_source_id=initial_source.id,
        source_snapshot_id=initial_snapshot.id,
        domain="visa",
        title="Observed governed rule",
        rule_key="at-observatory-rule",
        statement="Observed governed rule statement.",
        rationale="Independent review fixture.",
        evidence_excerpt="Official evidence excerpt.",
        confidence=0.99,
        status="published",
        proposed_by="rule-proposer",
        reviewed_by="rule-reviewer",
        reviewed_at=published_at - timedelta(minutes=1),
        review_notes="Reviewed independently.",
        published_by="rule-publisher",
        published_at=published_at,
    )
    rule = VerifiedRule(
        country="austria",
        domain="visa",
        rule_key=assertion.rule_key,
        statement=assertion.statement,
        official_source_id=initial_source.id,
        jurisdiction_id=assertion.jurisdiction_id,
        initial_rule_assertion_id=assertion.id,
        source_snapshot_id=initial_snapshot.id,
        confidence=assertion.confidence,
        active=True,
        approved_by="rule-publisher",
        published_at=published_at,
    )
    assertion.published_rule_id = rule.id
    db_session.add(assertion)
    db_session.add(rule)
    db_session.commit()
    initial_version = _initial_rule_publication_version(assertion, rule)
    _insert_outcome(
        db_session,
        source_type="initial_rule_assertion",
        source_id=assertion.id,
        source_version=initial_version,
        source_state="published",
        actor="rule-publisher",
        effective_at=published_at,
        contribution_type="verified_rule_publication_completed",
    )

    regulatory_source = OfficialSource(
        country="austria",
        domain="visa",
        name="Regulatory Observatory source",
        url="https://official.example/observatory/regulatory-change",
        source_type="government",
        active=True,
    )
    db_session.add(regulatory_source)
    db_session.flush()
    regulatory_snapshot = SourceSnapshot(
        official_source_id=regulatory_source.id,
        url=regulatory_source.url,
        content_hash="3" * 64,
        content_text="Governed regulatory-change evidence.",
        status="captured",
    )
    db_session.add(regulatory_snapshot)
    db_session.flush()
    change = RegulatoryChange(
        jurisdiction_id=uuid4(),
        official_source_id=regulatory_source.id,
        current_snapshot_id=regulatory_snapshot.id,
        domain="visa",
        change_type="rule_change",
        title="Observed regulatory change",
        summary="Reviewed regulatory change fixture.",
        materiality="material",
        status="published",
        reviewed_at=published_at - timedelta(minutes=1),
        reviewed_by="regulatory-reviewer",
        review_notes="Reviewed independently.",
        published_at=published_at,
    )
    regulatory_rule = VerifiedRule(
        country="austria",
        domain="visa",
        rule_key="at-observatory-reg-change",
        statement="Published regulatory change statement.",
        official_source_id=regulatory_source.id,
        jurisdiction_id=change.jurisdiction_id,
        regulatory_change_id=change.id,
        source_snapshot_id=regulatory_snapshot.id,
        confidence=0.98,
        active=True,
        approved_by="regulatory-publisher",
        published_at=published_at,
    )
    db_session.add(change)
    db_session.add(regulatory_rule)
    db_session.commit()
    regulatory_version = _regulatory_change_publication_version(change, regulatory_rule)
    _insert_outcome(
        db_session,
        source_type="regulatory_change",
        source_id=change.id,
        source_version=regulatory_version,
        source_state="published",
        actor="regulatory-publisher",
        effective_at=published_at,
        contribution_type="regulatory_change_publication_completed",
        evidence_summary=[
            {
                "source_type": "regulatory_change",
                "verified_rule_id": str(regulatory_rule.id),
            }
        ],
    )

    pathway_source = OfficialSource(
        country="germany",
        domain="work",
        name="Pathway Observatory source",
        url="https://official.example/observatory/pathway",
        source_type="government",
        active=True,
    )
    db_session.add(pathway_source)
    db_session.flush()
    pathway_snapshot = SourceSnapshot(
        official_source_id=pathway_source.id,
        url=pathway_source.url,
        content_hash="4" * 64,
        content_text="Governed pathway evidence.",
        status="captured",
    )
    db_session.add(pathway_snapshot)
    db_session.flush()
    pathway_rule = VerifiedRule(
        country="germany",
        domain="work",
        rule_key="de-observatory-pathway",
        statement="Published pathway rule.",
        official_source_id=pathway_source.id,
        source_snapshot_id=pathway_snapshot.id,
        confidence=0.99,
        active=True,
        approved_by="pathway-rule-reviewer",
        published_at=published_at,
    )
    pathway = MobilityPathway(
        pathway_key="de-observatory-published-pathway",
        name="Germany Observatory Published Pathway",
        country="germany",
        domain="work",
        catalogue_status="active",
        created_by="pathway-proposer",
    )
    db_session.add(pathway_rule)
    db_session.add(pathway)
    db_session.flush()
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        official_source_id=pathway_source.id,
        source_snapshot_id=pathway_snapshot.id,
        verified_rule_ids_json=json.dumps([str(pathway_rule.id)]),
        eligibility_criteria_json="{}",
        required_documents_json="[]",
        costs_json="{}",
        processing_time_json="{}",
        benefits_json="[]",
        risks_json="[]",
        metadata_json="{}",
        human_review_required=True,
        approved_by="pathway-publisher",
        review_notes="Independent publication review.",
        published_at=published_at,
        created_by="pathway-proposer",
    )
    db_session.add(version)
    db_session.flush()
    db_session.add(
        MobilityPathwayVersionEvidence(
            pathway_version_id=version.id,
            evidence_role="core_route",
            official_source_id=pathway_source.id,
            source_snapshot_id=pathway_snapshot.id,
            required_for_publication=True,
            metadata_json="{}",
        )
    )
    db_session.commit()
    pathway_version = _pathway_publication_version(db_session, pathway, version)
    _insert_outcome(
        db_session,
        source_type="mobility_pathway_version",
        source_id=version.id,
        source_version=pathway_version,
        source_state="published",
        actor="pathway-publisher",
        effective_at=published_at,
        contribution_type="pathway_version_published",
    )

    response = client.get(
        f"{OBS}/contribution-reconciliation",
        params={"status": "matched", "page_size": 200},
    )
    assert response.status_code == 200, response.text
    matched_types = {item["source_type"] for item in response.json()["data"]}
    assert {
        "initial_rule_assertion",
        "regulatory_change",
        "mobility_pathway_version",
    }.issubset(matched_types)
    for source_type in (
        "initial_rule_assertion",
        "regulatory_change",
        "mobility_pathway_version",
    ):
        coverage = _source_coverage(response.json(), source_type)
        assert coverage["coverage_established"] is True
        assert coverage["missing_contribution_in_coverage"] == 0


def test_duplicate_contribution_identity_is_reported_without_repair(
    client: TestClient,
    db_session: Session,
) -> None:
    decision = _approved_decision(client, "obs-duplicate-decision")
    created = client.post(
        f"{BASE}/contributions",
        json=_contribution_payload(decision, "obs-duplicate-original"),
    )
    assert created.status_code == 201, created.text
    original = db_session.get(OrganizationContribution, UUID(created.json()["id"]))
    assert original is not None

    duplicate = OrganizationContribution(
        contribution_key="obs-duplicate-injected",
        record_fingerprint="d" * 64,
        tenant_key=original.tenant_key,
        contribution_type=original.contribution_type,
        title=original.title,
        outcome_summary=original.outcome_summary,
        actor_type=original.actor_type,
        actor_id=original.actor_id,
        department=original.department,
        accountable_position_key=original.accountable_position_key,
        authority_level=original.authority_level,
        source_object_type=original.source_object_type,
        source_object_id=original.source_object_id,
        source_object_version=original.source_object_version,
        source_state=original.source_state,
        verification_method=original.verification_method,
        record_kind=OrganizationContributionRecordKind.outcome,
        verified_by=original.verified_by,
        verified_at=original.verified_at,
        human_review_state=original.human_review_state,
        decision_id=original.decision_id,
        impact_kind=original.impact_kind,
        evidence_summary_json=original.evidence_summary_json,
        effective_at=original.effective_at,
        created_by=original.created_by,
    )
    db_session.add(duplicate)
    db_session.commit()
    audit_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()

    response = client.get(
        f"{OBS}/contribution-reconciliation",
        params={"status": "duplicate_outcome"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 2
    assert {item["contribution_id"] for item in body["data"]} == {
        str(original.id),
        str(duplicate.id),
    }
    assert all(len(item["duplicate_contribution_ids"]) == 1 for item in body["data"])
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audit_before


def test_source_version_drift_is_visible_and_get_never_repairs_it(
    client: TestClient,
    db_session: Session,
) -> None:
    certification = _certification(
        scope="supplemental_observatory_drift",
        status="approved",
        reviewed_at=now_utc(),
    )
    db_session.add(certification)
    db_session.commit()
    context = source_certification_organization_context(actor="pytest-admin", role="admin")
    contribution = stage_source_certification_review_contribution(
        db_session,
        context,
        certification=certification,
        review_evidence=_review_evidence(),
    )
    db_session.commit()
    original_version = contribution.source_object_version

    certification.review_notes = "Materially changed after the accepted outcome."
    db_session.add(certification)
    db_session.commit()
    audit_before = db_session.exec(select(func.count()).select_from(AuditLog)).one()

    response = client.get(
        f"{OBS}/contribution-reconciliation",
        params={"status": "source_version_drift"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    item = response.json()["data"][0]
    assert item["contribution_source_version"] == original_version
    assert item["current_source_version"] != original_version
    assert db_session.exec(select(func.count()).select_from(AuditLog)).one() == audit_before


def test_activity_volume_does_not_become_contribution_productivity(
    client: TestClient,
) -> None:
    created = client.post(
        f"{BASE}/activities",
        json={
            "activity_key": "observatory-activity-only",
            "stream_key": "observatory-activity-stream",
            "activity_class": "operational",
            "activity_type": "runtime_signal",
            "title": "Runtime activity",
            "summary": "Activity is not Contribution authority.",
            "source_object_type": "workflow_run",
            "source_object_id": str(uuid4()),
            "source_object_version": "v1",
            "occurred_at": NOW.isoformat(),
        },
    )
    assert created.status_code == 201, created.text
    summary = client.get(f"{OBS}/summary").json()
    assert summary["source_row_counts"]["organization_activities"] == 1
    assert summary["metrics"]["contributions"]["total_records"] == 0
    assert summary["coverage"]["activity_history_established"] is False


def test_draft_pathway_and_pending_certification_are_zero_emitter_safety_rows(
    client: TestClient,
    db_session: Session,
) -> None:
    pending = _certification(
        scope="supplemental_observatory_pending",
        status="pending_review",
        reviewed_at=None,
    )
    pathway = MobilityPathway(
        pathway_key="at-round6-observatory-safety",
        name="Austria Round 6 draft safety pathway",
        country="Austria",
        domain="work",
        catalogue_status="draft",
        created_by="pytest",
    )
    db_session.add(pending)
    db_session.add(pathway)
    db_session.flush()
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=4,
        lifecycle_status="draft",
        metadata_json='{"compatibility_status":"INTERNAL_SIMULATION_ONLY","publication_ready":false}',
        human_review_required=True,
        created_by="pytest",
    )
    db_session.add(version)
    db_session.commit()

    summary = client.get(f"{OBS}/summary").json()
    assert summary["metrics"]["contributions"]["historical_outcomes"] == 0
    reconciliation = client.get(f"{OBS}/contribution-reconciliation").json()
    cert_coverage = _source_coverage(reconciliation, "jurisdiction_source_certification")
    pathway_coverage = _source_coverage(reconciliation, "mobility_pathway_version")
    assert cert_coverage["eligible_source_rows"] == 0
    assert pathway_coverage["eligible_source_rows"] == 0
    assert cert_coverage["missing_contribution_in_coverage"] == 0
    assert pathway_coverage["missing_contribution_in_coverage"] == 0
    assert reconciliation["total"] == 0

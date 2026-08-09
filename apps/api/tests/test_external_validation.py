from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    ExternalValidationFinding,
    Jurisdiction,
    Lead,
    LeadIntent,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    PathwayComparisonAssessment,
    SourceSnapshot,
    TruthClaim,
    VerificationStatus,
    VerifiedRule,
)
from app.services.external_validation import external_validation_gate_passed


def _seed_scenario(client: TestClient) -> dict:
    response = client.post("/api/v1/external-validation/scenarios/seed-defaults")
    assert response.status_code == 200, response.text
    scenario = response.json()
    assert scenario["scenario_key"] == "at-skilled-worker-discovery-v1"
    assert "pathway_comparison" in scenario["required_evidence_types"]
    return scenario


def _evidence_graph(session: Session) -> dict[str, object]:
    jurisdiction = Jurisdiction(code="AT", name="Austria", region="Europe")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="austria",
        domain="work",
        name="Austria official mobility source",
        url="https://www.oesterreich.gv.at/",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="external-validation-at-snapshot",
        content_text="Reviewed official-source snapshot used by the validation fixture.",
        status="captured",
        retrieval_method="manual",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    rule = VerifiedRule(
        country="austria",
        domain="work",
        rule_key="at-validation-rule",
        statement="Validation-only reviewed work-route rule statement.",
        official_source_id=source.id,
        jurisdiction_id=jurisdiction.id,
        source_snapshot_id=snapshot.id,
        confidence=0.99,
        active=True,
        approved_by="independent-rule-reviewer",
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)

    pathway = MobilityPathway(
        pathway_key="at-validation-pathway",
        name="Austria validation pathway",
        country="austria",
        domain="work",
        jurisdiction_id=jurisdiction.id,
        catalogue_status="active",
        created_by="pytest",
    )
    session.add(pathway)
    session.commit()
    session.refresh(pathway)

    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=f'["{rule.id}"]',
        eligibility_criteria_json="{}",
        required_documents_json="[]",
        created_by="pathway-author",
        approved_by="pathway-reviewer",
        human_review_required=True,
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    lead = Lead(
        full_name="External Validation User",
        email="external.validation@example.com",
        intent=LeadIntent.overseas_job,
        target_country="Austria",
        source="external-validation-pytest",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    comparison = PathwayComparisonAssessment(
        lead_id=lead.id,
        primary_pathway_id=pathway.id,
        primary_pathway_version_id=version.id,
        status="complete",
        comparison_json="{}",
        human_review_required=True,
        generated_by="pytest",
    )
    session.add(comparison)
    session.commit()
    session.refresh(comparison)

    claim = TruthClaim(
        lead_id=lead.id,
        claim="Validation claim grounded in reviewed source evidence.",
        domain="work",
        country="Austria",
        verdict=VerificationStatus.verified,
        confidence=0.99,
        requires_human_review=False,
        explanation="Verified for external-validation test coverage.",
    )
    session.add(claim)
    session.commit()
    session.refresh(claim)

    return {
        "jurisdiction": jurisdiction,
        "source": source,
        "snapshot": snapshot,
        "rule": rule,
        "pathway": pathway,
        "version": version,
        "lead": lead,
        "comparison": comparison,
        "claim": claim,
    }


def _create_run(client: TestClient, scenario: dict, graph: dict[str, object]) -> dict:
    response = client.post(
        "/api/v1/external-validation/runs",
        json={
            "run_key": "at-external-validation-run-001",
            "scenario_id": scenario["id"],
            "lead_id": str(graph["lead"].id),
            "pathway_comparison_assessment_id": str(graph["comparison"].id),
            "founder_intervention_count": 1,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _attach_required_evidence(client: TestClient, run_id: str, graph: dict[str, object]) -> None:
    evidence = [
        ("truth_claim", graph["claim"].id, "Truth Engine claim"),
        ("verified_rule", graph["rule"].id, "Reviewed verified rule"),
        ("official_source", graph["source"].id, "Official source"),
        ("source_snapshot", graph["snapshot"].id, "Immutable source snapshot"),
        ("pathway_version", graph["version"].id, "Published pathway version"),
        ("pathway_comparison", graph["comparison"].id, "Pinned pathway comparison"),
    ]
    for evidence_type, entity_id, label in evidence:
        response = client.post(
            f"/api/v1/external-validation/runs/{run_id}/evidence",
            json={"evidence_type": evidence_type, "entity_id": str(entity_id), "label": label},
        )
        assert response.status_code == 201, response.text


def _submit_passing_reviews(client: TestClient, run_id: str) -> None:
    user = client.post(
        f"/api/v1/external-validation/runs/{run_id}/reviews",
        json={
            "reviewer_type": "mobility_user",
            "reviewer_name": "External Mobility User",
            "reviewer_origin": "external_human",
            "external_human_attestation": True,
            "workflow_completed": True,
            "understanding_rating": 5,
            "usefulness_rating": 4,
            "feedback": "The recommendation and next steps were understandable.",
        },
    )
    assert user.status_code == 201, user.text

    professional = client.post(
        f"/api/v1/external-validation/runs/{run_id}/reviews",
        json={
            "reviewer_type": "professional_operator",
            "reviewer_name": "Independent Mobility Professional",
            "reviewer_organization": "Independent practice",
            "reviewer_origin": "external_human",
            "external_human_attestation": True,
            "workflow_completed": True,
            "usefulness_rating": 5,
            "jurisdiction_pathway_correct": True,
            "material_rule_traceability_percent": 100,
            "unsupported_legal_certainty_count": 0,
            "missing_critical_document_count": 0,
            "feedback": "The workflow is operationally useful and evidence traceability is complete.",
        },
    )
    assert professional.status_code == 201, professional.text


def test_external_validation_gate_stays_held_until_external_reviews_and_evidence_exist(
    client: TestClient,
    db_session: Session,
) -> None:
    scenario = _seed_scenario(client)
    graph = _evidence_graph(db_session)
    run = _create_run(client, scenario, graph)

    evaluated = client.post(f"/api/v1/external-validation/runs/{run['id']}/evaluate")
    assert evaluated.status_code == 200, evaluated.text
    gate = evaluated.json()["gate"]
    assert gate["status"] == "held"
    assert set(gate["required_reviewer_types"]) == {"mobility_user", "professional_operator"}
    assert "truth_claim" in gate["required_evidence_types"]
    assert external_validation_gate_passed(db_session) is False


def test_external_validation_pass_requires_two_distinct_external_humans_and_complete_provenance(
    client: TestClient,
    db_session: Session,
) -> None:
    scenario = _seed_scenario(client)
    graph = _evidence_graph(db_session)
    run = _create_run(client, scenario, graph)
    _attach_required_evidence(client, run["id"], graph)
    _submit_passing_reviews(client, run["id"])

    evaluated = client.post(f"/api/v1/external-validation/runs/{run['id']}/evaluate")
    assert evaluated.status_code == 200, evaluated.text
    body = evaluated.json()
    assert body["gate_status"] == "passed"
    assert body["status"] == "completed"
    assert body["gate"]["founder_intervention_count"] == 1
    assert body["gate"]["critical_open"] == 0
    assert body["gate"]["high_open"] == 0
    assert external_validation_gate_passed(db_session) is True

    audits = db_session.exec(
        select(AuditLog).where(AuditLog.entity_type == "external_validation_run")
    ).all()
    assert any(item.action == "external_validation_gate_evaluated" for item in audits)


def test_same_external_person_cannot_satisfy_both_required_reviewer_types(
    client: TestClient,
    db_session: Session,
) -> None:
    scenario = _seed_scenario(client)
    graph = _evidence_graph(db_session)
    run = _create_run(client, scenario, graph)
    first = client.post(
        f"/api/v1/external-validation/runs/{run['id']}/reviews",
        json={
            "reviewer_type": "mobility_user",
            "reviewer_name": "Same Reviewer",
            "external_human_attestation": True,
            "workflow_completed": True,
            "understanding_rating": 5,
            "usefulness_rating": 5,
            "feedback": "External mobility-user feedback.",
        },
    )
    assert first.status_code == 201, first.text
    second = client.post(
        f"/api/v1/external-validation/runs/{run['id']}/reviews",
        json={
            "reviewer_type": "professional_operator",
            "reviewer_name": " same   reviewer ",
            "external_human_attestation": True,
            "workflow_completed": True,
            "usefulness_rating": 5,
            "jurisdiction_pathway_correct": True,
            "material_rule_traceability_percent": 100,
            "unsupported_legal_certainty_count": 0,
            "missing_critical_document_count": 0,
            "feedback": "Attempted duplicate reviewer.",
        },
    )
    assert second.status_code == 400
    assert "distinct external reviewers" in second.json()["detail"]


def test_high_finding_cannot_be_board_waived_and_blocks_gate_until_resolved(
    client: TestClient,
    db_session: Session,
) -> None:
    scenario = _seed_scenario(client)
    graph = _evidence_graph(db_session)
    run = _create_run(client, scenario, graph)
    _attach_required_evidence(client, run["id"], graph)
    _submit_passing_reviews(client, run["id"])

    finding = client.post(
        f"/api/v1/external-validation/runs/{run['id']}/findings",
        json={
            "severity": "high",
            "category": "pathway_accuracy",
            "title": "Material eligibility mismatch",
            "description": "Professional review identified a material pathway defect requiring remediation.",
        },
    )
    assert finding.status_code == 201, finding.text
    finding_id = finding.json()["id"]

    waived = client.post(
        f"/api/v1/external-validation/findings/{finding_id}/board-acceptance",
        json={"attestation": True, "reason": "Attempt to accept material risk for testing."},
    )
    assert waived.status_code == 400
    assert "cannot be waived" in waived.json()["detail"]

    failed = client.post(f"/api/v1/external-validation/runs/{run['id']}/evaluate")
    assert failed.status_code == 200
    assert failed.json()["gate_status"] == "failed"

    resolved = client.post(
        f"/api/v1/external-validation/findings/{finding_id}/triage",
        json={"status": "resolved", "remediation_notes": "Corrected the defect and independently retested the output."},
    )
    assert resolved.status_code == 200, resolved.text

    passed = client.post(f"/api/v1/external-validation/runs/{run['id']}/evaluate")
    assert passed.status_code == 200, passed.text
    assert passed.json()["gate_status"] == "passed"


def test_medium_finding_requires_triage_or_board_acceptance_before_pass(
    client: TestClient,
    db_session: Session,
) -> None:
    scenario = _seed_scenario(client)
    graph = _evidence_graph(db_session)
    run = _create_run(client, scenario, graph)
    _attach_required_evidence(client, run["id"], graph)
    _submit_passing_reviews(client, run["id"])

    finding = client.post(
        f"/api/v1/external-validation/runs/{run['id']}/findings",
        json={
            "severity": "medium",
            "category": "ux",
            "title": "Source explanation could be clearer",
            "description": "The result is correct but the source explanation is harder to follow than necessary.",
        },
    )
    assert finding.status_code == 201, finding.text

    held = client.post(f"/api/v1/external-validation/runs/{run['id']}/evaluate")
    assert held.status_code == 200
    assert held.json()["gate_status"] == "held"

    accepted = client.post(
        f"/api/v1/external-validation/findings/{finding.json()['id']}/board-acceptance",
        json={
            "attestation": True,
            "reason": "Human Board accepts this documented medium UX risk for the validation gate.",
        },
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted_risk"

    passed = client.post(f"/api/v1/external-validation/runs/{run['id']}/evaluate")
    assert passed.status_code == 200, passed.text
    assert passed.json()["gate_status"] == "passed"


def test_professional_failure_metrics_fail_gate_deterministically(
    client: TestClient,
    db_session: Session,
) -> None:
    scenario = _seed_scenario(client)
    graph = _evidence_graph(db_session)
    run = _create_run(client, scenario, graph)
    _attach_required_evidence(client, run["id"], graph)

    user = client.post(
        f"/api/v1/external-validation/runs/{run['id']}/reviews",
        json={
            "reviewer_type": "mobility_user",
            "reviewer_name": "Mobility User Two",
            "external_human_attestation": True,
            "workflow_completed": True,
            "understanding_rating": 5,
            "usefulness_rating": 5,
            "feedback": "Clear enough for the validation run.",
        },
    )
    assert user.status_code == 201
    professional = client.post(
        f"/api/v1/external-validation/runs/{run['id']}/reviews",
        json={
            "reviewer_type": "professional_operator",
            "reviewer_name": "Professional Two",
            "external_human_attestation": True,
            "workflow_completed": True,
            "usefulness_rating": 5,
            "jurisdiction_pathway_correct": False,
            "material_rule_traceability_percent": 90,
            "unsupported_legal_certainty_count": 1,
            "missing_critical_document_count": 1,
            "feedback": "Material defects remain.",
        },
    )
    assert professional.status_code == 201

    evaluated = client.post(f"/api/v1/external-validation/runs/{run['id']}/evaluate")
    assert evaluated.status_code == 200
    assert evaluated.json()["gate_status"] == "failed"
    reasons = " ".join(evaluated.json()["gate"]["reasons"])
    assert "traceability" in reasons.lower()
    assert "unsupported legal-certainty" in reasons.lower()


def test_validation_run_requires_pinned_lead_and_pathway_comparison(
    client: TestClient,
) -> None:
    scenario = _seed_scenario(client)
    response = client.post(
        "/api/v1/external-validation/runs",
        json={
            "run_key": "at-external-validation-missing-anchors",
            "scenario_id": scenario["id"],
            "founder_intervention_count": 0,
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    missing = {item["loc"][-1] for item in detail if item.get("type") == "missing"}
    assert {"lead_id", "pathway_comparison_assessment_id"} <= missing


def test_validation_gate_rejects_unrelated_pathway_version_evidence(
    client: TestClient,
    db_session: Session,
) -> None:
    scenario = _seed_scenario(client)
    graph = _evidence_graph(db_session)
    run = _create_run(client, scenario, graph)

    unrelated_version = MobilityPathwayVersion(
        pathway_id=graph["pathway"].id,
        version_number=99,
        lifecycle_status="published",
        official_source_id=graph["source"].id,
        source_snapshot_id=graph["snapshot"].id,
        verified_rule_ids_json=f'["{graph["rule"].id}"]',
        eligibility_criteria_json="{}",
        required_documents_json="[]",
        created_by="pathway-author",
        approved_by="pathway-reviewer",
        human_review_required=True,
    )
    db_session.add(unrelated_version)
    db_session.commit()
    db_session.refresh(unrelated_version)

    evidence = [
        ("truth_claim", graph["claim"].id, "Truth Engine claim"),
        ("verified_rule", graph["rule"].id, "Reviewed verified rule"),
        ("official_source", graph["source"].id, "Official source"),
        ("source_snapshot", graph["snapshot"].id, "Immutable source snapshot"),
        ("pathway_version", unrelated_version.id, "Wrong pathway version"),
        ("pathway_comparison", graph["comparison"].id, "Pinned pathway comparison"),
    ]
    for evidence_type, entity_id, label in evidence:
        response = client.post(
            f"/api/v1/external-validation/runs/{run['id']}/evidence",
            json={"evidence_type": evidence_type, "entity_id": str(entity_id), "label": label},
        )
        assert response.status_code == 201, response.text

    _submit_passing_reviews(client, run["id"])
    evaluated = client.post(f"/api/v1/external-validation/runs/{run['id']}/evaluate")
    assert evaluated.status_code == 200, evaluated.text
    gate = evaluated.json()["gate"]
    assert gate["status"] == "failed"
    assert any("primary version" in reason.lower() for reason in gate["reasons"])

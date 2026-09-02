from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    AuditLog,
    DocumentExtractionJob,
    DocumentFraudRiskAssessment,
    DocumentRecord,
)
from app.services.document_fraud_risk import generate_document_fraud_risk_assessment
from app.services.document_intelligence import ensure_builtin_schemas

from .conftest import create_lead


def test_exact_file_reuse_is_explainable_idempotent_and_non_mutating(db_session: Session) -> None:
    lead = create_lead(db_session, name="Integrity Lead One")
    other = create_lead(db_session, name="Integrity Lead Two")
    first = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport-one.pdf",
        status="verified",
        file_hash="shared-document-hash",
    )
    second = DocumentRecord(
        lead_id=other.id,
        document_type="passport",
        filename="passport-two.pdf",
        status="verified",
        file_hash="shared-document-hash",
    )
    db_session.add_all([first, second])
    db_session.commit()

    assessment, created = generate_document_fraud_risk_assessment(
        db_session,
        lead.id,
        actor="pytest-integrity-monitor",
    )
    assert created is True
    assert assessment.result_status == "high_priority_review"
    assert assessment.review_status == "pending"
    assert assessment.high_indicator_count == 1
    assert assessment.automated_fraud_determination is False
    assert assessment.adverse_action_taken is False
    indicators = json.loads(assessment.indicators_json)
    reuse = next(row for row in indicators if row["indicator_type"] == "exact_file_reuse_across_leads")
    assert reuse["severity"] == "high"
    assert reuse["evidence"]["file_hash"] == "shared-document-hash"
    assert reuse["evidence"]["matching_other_lead_count"] == 1

    repeated, repeated_created = generate_document_fraud_risk_assessment(
        db_session,
        lead.id,
        actor="pytest-integrity-monitor",
    )
    assert repeated_created is False
    assert repeated.id == assessment.id
    assert len(db_session.exec(select(DocumentFraudRiskAssessment)).all()) == 1

    db_session.refresh(first)
    db_session.refresh(second)
    assert first.status == "verified"
    assert second.status == "verified"


def test_api_scan_and_human_review_never_take_adverse_action(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session, name="Rejected Evidence Review Lead")
    application = ApplicationRecord(
        lead_id=lead.id,
        domain="visa",
        target_country="Germany",
        status="draft",
        risk_score=0.25,
    )
    document = DocumentRecord(
        lead_id=lead.id,
        document_type="bank_statement",
        filename="bank.pdf",
        status="rejected",
        file_hash="rejected-bank-hash",
    )
    db_session.add_all([application, document])
    db_session.commit()
    db_session.refresh(application)

    scan = client.post(
        "/api/v1/document-intelligence/fraud-risk-assessments/scan",
        json={"lead_id": str(lead.id)},
    )
    assert scan.status_code == 200, scan.text
    payload = scan.json()
    assert payload["created"] == 1
    assert payload["fraud_determinations"] == 0
    assert payload["documents_rejected"] == 0
    assert payload["eligibility_changed"] is False
    assert payload["external_actions_triggered"] == 0

    listed = client.get(
        f"/api/v1/document-intelligence/fraud-risk-assessments?lead_id={lead.id}"
    )
    assert listed.status_code == 200, listed.text
    assessment = listed.json()[0]
    assert assessment["risk_band"] == "review"
    assert assessment["review_status"] == "pending"
    assert assessment["fraud_determined"] is False
    assert assessment["adverse_action_taken"] is False
    assert assessment["documents_rejected"] == 0
    assert any(row["indicator_type"] == "rejected_or_invalid_evidence" for row in assessment["indicators"])

    reviewed = client.post(
        f"/api/v1/document-intelligence/fraud-risk-assessments/{assessment['id']}/review",
        json={
            "decision": "specialist_review_required",
            "notes": "Escalate the provenance question to a trained document specialist.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    reviewed_payload = reviewed.json()
    assert reviewed_payload["review_status"] == "specialist_review_required"
    assert reviewed_payload["fraud_determined"] is False
    assert reviewed_payload["adverse_action_taken"] is False

    repeated = client.post(
        f"/api/v1/document-intelligence/fraud-risk-assessments/{assessment['id']}/review",
        json={"decision": "cleared", "notes": "Second review must be blocked."},
    )
    assert repeated.status_code == 400

    db_session.refresh(document)
    db_session.refresh(application)
    assert document.status == "rejected"
    assert application.status == "draft"
    assert application.risk_score == 0.25

    actions = {
        row.action
        for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_type.in_([
                "document_fraud_risk_assessment",
                "document_integrity_monitor",
            ]))
        ).all()
    }
    assert {
        "document_fraud_risk_assessed",
        "document_fraud_risk_scan_completed",
        "document_fraud_risk_specialist_review_required",
    } <= actions


def test_approved_identifier_reuse_is_masked_and_source_linked(db_session: Session) -> None:
    schemas = ensure_builtin_schemas(db_session, actor="pytest")
    passport_schema = next(row for row in schemas if row.document_type == "passport")
    lead = create_lead(db_session, name="Identifier Lead One")
    other = create_lead(db_session, name="Identifier Lead Two")
    first = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport-one.pdf",
        status="verified",
        file_hash="passport-hash-one",
    )
    second = DocumentRecord(
        lead_id=other.id,
        document_type="passport",
        filename="passport-two.pdf",
        status="verified",
        file_hash="passport-hash-two",
    )
    db_session.add_all([first, second])
    db_session.commit()
    db_session.refresh(first)
    db_session.refresh(second)

    first_job = DocumentExtractionJob(
        document_id=first.id,
        lead_id=lead.id,
        schema_definition_id=passport_schema.id,
        schema_version=passport_schema.version_number,
        status="approved",
        structured_data_json=json.dumps({"document_number": "P123456789"}),
        requested_by="pytest",
        reviewed_by="pytest-reviewer",
        review_notes="Approved extraction one.",
    )
    second_job = DocumentExtractionJob(
        document_id=second.id,
        lead_id=other.id,
        schema_definition_id=passport_schema.id,
        schema_version=passport_schema.version_number,
        status="approved",
        structured_data_json=json.dumps({"document_number": "P123456789"}),
        requested_by="pytest",
        reviewed_by="pytest-reviewer",
        review_notes="Approved extraction two.",
    )
    db_session.add_all([first_job, second_job])
    db_session.commit()

    assessment, created = generate_document_fraud_risk_assessment(
        db_session,
        lead.id,
        actor="pytest-integrity-monitor",
    )
    assert created is True
    indicators = json.loads(assessment.indicators_json)
    reused = next(row for row in indicators if row["indicator_type"] == "approved_identifier_reuse_across_leads")
    assert reused["severity"] == "high"
    assert reused["evidence"]["masked_identifier"].endswith("6789")
    assert "P123456789" not in json.dumps(reused)
    assert reused["evidence"]["matching_other_lead_count"] == 1
    assert str(first_job.id) in reused["source_record_ids"]
    assert str(second_job.id) in reused["source_record_ids"]

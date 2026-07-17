from __future__ import annotations

import json
from datetime import timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    AuditLog,
    DocumentConsistencyAssessment,
    DocumentExtractionJob,
    DocumentRecord,
    DocumentRequirementAssessment,
    EligibilityAssessment,
    MobilityPathway,
    MobilityPathwayVersion,
    now_utc,
)
from app.services.document_intelligence import ensure_builtin_schemas
from app.services.document_requirement_assessments import generate_document_requirement_assessment

from .conftest import create_lead


def _published_pathway(session: Session) -> tuple[MobilityPathway, MobilityPathwayVersion]:
    pathway = MobilityPathway(
        pathway_key="de-document-requirement-test",
        name="Germany Document Requirement Test",
        country="Germany",
        domain="work",
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
        required_documents_json=json.dumps([
            "Valid passport",
            "CV / resume",
            "Degree or professional certificate",
            "Financial proof",
        ]),
        approved_by="pytest-reviewer",
        review_notes="Published for deterministic document requirement tests.",
        published_at=now_utc(),
        created_by="pytest",
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return pathway, version


def test_exact_pathway_requirement_assessment_is_immutable_and_idempotent(
    db_session: Session,
) -> None:
    lead = create_lead(db_session, name="Pathway Requirement Lead")
    pathway, version = _published_pathway(db_session)
    reference = now_utc()
    passport = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport.pdf",
        status="verified",
        file_hash="passport-hash",
        expiry_date=reference + timedelta(days=400),
    )
    bank = DocumentRecord(
        lead_id=lead.id,
        document_type="bank_statement",
        filename="bank.pdf",
        status="received",
        file_hash="bank-hash",
    )
    degree = DocumentRecord(
        lead_id=lead.id,
        document_type="degree_certificate",
        filename="degree.pdf",
        status="verified",
        file_hash="degree-hash",
        expiry_date=reference - timedelta(days=1),
    )
    db_session.add_all([passport, bank, degree])
    db_session.commit()

    assessment, created = generate_document_requirement_assessment(
        db_session,
        lead.id,
        pathway_version_id=version.id,
        actor="pytest-requirement-monitor",
        as_of=reference,
    )
    assert created is True
    assert assessment.pathway_id == pathway.id
    assert assessment.pathway_version_id == version.id
    assert assessment.requirement_source == "published_pathway_version"
    assert assessment.result_status == "gaps_and_inconsistencies"
    assert assessment.required_count == 4
    assert assessment.satisfied_count == 1
    assert assessment.missing_count == 1
    assert assessment.inconsistency_count == 2

    findings = json.loads(assessment.findings_json)
    outcomes = {row["requirement_key"]: row["outcome"] for row in findings if row["finding_type"] == "requirement_coverage"}
    assert outcomes["valid_passport"] == "satisfied"
    assert outcomes["cv_resume"] == "missing"
    assert outcomes["degree_or_professional_certificate"] == "expired"
    assert outcomes["financial_proof"] == "present_unverified"

    repeated, repeated_created = generate_document_requirement_assessment(
        db_session,
        lead.id,
        pathway_version_id=version.id,
        actor="pytest-requirement-monitor",
        as_of=reference,
    )
    assert repeated_created is False
    assert repeated.id == assessment.id
    assert len(db_session.exec(select(DocumentRequirementAssessment)).all()) == 1

    cv = DocumentRecord(
        lead_id=lead.id,
        document_type="cv",
        filename="cv.pdf",
        status="verified",
        file_hash="cv-hash",
    )
    db_session.add(cv)
    db_session.commit()
    changed, changed_created = generate_document_requirement_assessment(
        db_session,
        lead.id,
        pathway_version_id=version.id,
        actor="pytest-requirement-monitor",
        as_of=reference,
    )
    assert changed_created is True
    assert changed.id != assessment.id
    assert changed.missing_count == 0
    assert len(db_session.exec(select(DocumentRequirementAssessment)).all()) == 2

    db_session.refresh(passport)
    db_session.refresh(bank)
    db_session.refresh(degree)
    assert passport.status == "verified"
    assert bank.status == "received"
    assert degree.status == "verified"


def test_application_baseline_detects_missing_and_duplicate_conflicts_and_requires_review(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session, name="Application Requirement Lead")
    application = ApplicationRecord(
        lead_id=lead.id,
        domain="work",
        target_country="Germany",
        status="draft",
    )
    first_passport = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport-old.pdf",
        status="verified",
        file_hash="old-passport",
        expiry_date=now_utc() + timedelta(days=200),
    )
    second_passport = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport-new.pdf",
        status="verified",
        file_hash="new-passport",
        expiry_date=now_utc() + timedelta(days=500),
    )
    db_session.add_all([application, first_passport, second_passport])
    db_session.commit()
    db_session.refresh(application)

    scanned = client.post(
        "/api/v1/document-intelligence/requirement-assessments/scan",
        json={"lead_id": str(lead.id)},
    )
    assert scanned.status_code == 200, scanned.text
    assert scanned.json()["created"] == 1
    assert scanned.json()["documents_created"] == 0
    assert scanned.json()["external_messages_sent"] == 0

    listed = client.get(
        f"/api/v1/document-intelligence/requirement-assessments?lead_id={lead.id}"
    )
    assert listed.status_code == 200, listed.text
    assessment = listed.json()[0]
    assert assessment["application_id"] == str(application.id)
    assert assessment["requirement_source"] == "application_domain_baseline"
    assert assessment["review_status"] == "pending"
    assert assessment["missing_count"] >= 4
    assert assessment["inconsistency_count"] >= 1
    assert assessment["source_records_unchanged"] is True
    assert assessment["documents_created"] == 0
    assert assessment["eligibility_changed"] is False
    assert any(row["outcome"] == "duplicate_conflict" for row in assessment["findings"])

    missing_note = client.post(
        f"/api/v1/document-intelligence/requirement-assessments/{assessment['id']}/review",
        json={"decision": "approved", "notes": ""},
    )
    assert missing_note.status_code == 422

    reviewed = client.post(
        f"/api/v1/document-intelligence/requirement-assessments/{assessment['id']}/review",
        json={
            "decision": "approved",
            "notes": "Confirmed the gap ledger for controlled document collection.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["review_status"] == "approved"
    assert reviewed.json()["reviewed_by"] == "pytest-admin"
    assert reviewed.json()["source_records_unchanged"] is True

    repeated = client.post(
        f"/api/v1/document-intelligence/requirement-assessments/{assessment['id']}/review",
        json={"decision": "rejected", "notes": "Duplicate review must be blocked."},
    )
    assert repeated.status_code == 400

    actions = {
        row.action
        for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_type.in_([
                "document_requirement_assessment",
                "document_requirement_monitor",
            ]))
        ).all()
    }
    assert {
        "document_requirement_assessed",
        "document_requirement_scan_completed",
        "document_requirement_approved",
    } <= actions


def test_existing_consistency_mismatch_is_promoted_to_requirement_finding(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session, name="Mismatch Requirement Lead")
    document = DocumentRecord(
        lead_id=lead.id,
        document_type="cv",
        filename="cv.pdf",
        status="verified",
        file_hash="cv-mismatch-hash",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    profile_response = client.put(
        f"/api/v1/profiles/leads/{lead.id}/current",
        json={
            "current_country": "India",
            "education": [],
            "employment": [],
            "skills": [],
            "languages": [],
            "family_status": "single",
            "family_details_confirmed": True,
            "finances": {},
            "goals": [{"domain": "work", "target_country": "Germany", "priority": "high"}],
            "constraints": [],
            "constraints_confirmed": True,
            "consent_status": "granted",
            "consent_purposes": ["document_validation"],
            "evidence_document_ids": [str(document.id)],
        },
    )
    assert profile_response.status_code == 200, profile_response.text
    profile = profile_response.json()

    schema = next(row for row in ensure_builtin_schemas(db_session, actor="pytest") if row.document_type == "cv")
    job = DocumentExtractionJob(
        document_id=document.id,
        lead_id=lead.id,
        schema_definition_id=schema.id,
        schema_version=schema.version_number,
        status="approved",
        structured_data_json=json.dumps({"profession": "Engineer"}),
        field_confidence_json="{}",
        warnings_json="[]",
        reviewed_by="pytest-reviewer",
        review_notes="Approved transcription.",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    mismatch = DocumentConsistencyAssessment(
        extraction_job_id=job.id,
        document_id=document.id,
        lead_id=lead.id,
        profile_id=UUID(profile["id"]),
        profile_version=profile["profile_version"],
        result_status="inconsistencies_found",
        review_status="approved",
        match_count=0,
        mismatch_count=1,
        missing_count=0,
        findings_json="[]",
        source_facts_json="{}",
        summary="Approved mismatch for requirement aggregation.",
        generated_by="pytest",
        reviewed_by="pytest-reviewer",
        review_notes="Mismatch confirmed.",
        reviewed_at=now_utc(),
    )
    eligibility = EligibilityAssessment(
        lead_id=lead.id,
        profile_id=UUID(profile["id"]),
        profile_version=profile["profile_version"],
        target_country="Germany",
        domain="work",
        status="needs_documents",
        required_documents_json=json.dumps(["CV / resume"]),
    )
    db_session.add_all([mismatch, eligibility])
    db_session.commit()

    generated = client.post(
        "/api/v1/document-intelligence/requirement-assessments/generate",
        json={"lead_id": str(lead.id)},
    )
    assert generated.status_code == 201, generated.text
    assessment = generated.json()
    assert assessment["requirement_source"] == "eligibility_assessment"
    assert assessment["result_status"] == "inconsistencies_found"
    assert assessment["missing_count"] == 0
    assert assessment["inconsistency_count"] == 1
    assert assessment["findings"][0]["outcome"] == "fact_inconsistency"

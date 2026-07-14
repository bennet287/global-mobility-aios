from __future__ import annotations

import json
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    AuditLog,
    DocumentConsistencyAssessment,
    DocumentExtractionJob,
    DocumentRecord,
)
from app.services.document_intelligence import ensure_builtin_schemas

from .conftest import create_lead


def _profile_payload(document_id: UUID, *, years: float = 5, role: str = "Software Engineer") -> dict:
    return {
        "current_country": "India",
        "education": [{
            "qualification": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "institution": "Example University",
            "country": "India",
            "completion_year": 2020,
        }],
        "employment": [{
            "role": role,
            "employer": "Example Technology Ltd",
            "country": "India",
            "years": years,
            "current": True,
        }],
        "years_experience": years,
        "skills": ["software engineering"],
        "languages": [{"language": "English", "level": "C1"}],
        "family_status": "single",
        "family_details_confirmed": True,
        "finances": {"budget_eur": 12000},
        "goals": [{
            "domain": "work",
            "target_country": "Germany",
            "desired_role_or_program": role,
            "priority": "high",
        }],
        "constraints": [],
        "constraints_confirmed": True,
        "consent_status": "granted",
        "consent_purposes": ["document_validation"],
        "evidence_document_ids": [str(document_id)],
    }


def _approved_cv_extraction(session: Session, lead_id: UUID) -> tuple[DocumentRecord, DocumentExtractionJob]:
    document = DocumentRecord(
        lead_id=lead_id,
        document_type="cv",
        filename="cv.txt",
        status="received",
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    schemas = ensure_builtin_schemas(session, actor="pytest")
    schema = next(row for row in schemas if row.document_type == "cv")
    job = DocumentExtractionJob(
        document_id=document.id,
        lead_id=lead_id,
        schema_definition_id=schema.id,
        schema_version=schema.version_number,
        status="approved",
        structured_data_json=json.dumps({
            "full_name": "Ada Lovelace",
            "profession": "Software Engineer",
            "years_experience": 5.0,
        }),
        field_confidence_json=json.dumps({
            "full_name": 0.8,
            "profession": 0.8,
            "years_experience": 0.8,
        }),
        warnings_json="[]",
        reviewed_by="pytest-reviewer",
        review_notes="Extraction transcribed against source.",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return document, job


def test_consistency_assessment_pins_profile_and_application_snapshots(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session, name="Ada Lovelace", target_country="Germany")
    document, job = _approved_cv_extraction(db_session, lead.id)
    profile = client.put(
        f"/api/v1/profiles/leads/{lead.id}/current",
        json=_profile_payload(document.id),
    )
    assert profile.status_code == 200, profile.text
    application = ApplicationRecord(
        lead_id=lead.id,
        domain="work",
        target_country="Germany",
        target_institution_or_employer="Target Technology GmbH",
        status="draft",
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)

    generated = client.post(
        f"/api/v1/document-intelligence/extractions/{job.id}/validate",
        json={"application_id": str(application.id)},
    )
    assert generated.status_code == 201, generated.text
    assessment = generated.json()
    assert assessment["profile_version"] == 1
    assert assessment["application_id"] == str(application.id)
    assert assessment["result_status"] == "consistent"
    assert assessment["review_status"] == "pending"
    assert assessment["match_count"] == 4
    assert assessment["mismatch_count"] == 0
    assert {finding["finding_key"] for finding in assessment["findings"]} == {
        "identity_name_consistency",
        "experience_years_consistency",
        "profession_consistency",
        "application_document_relevance",
    }

    repeated = client.post(
        f"/api/v1/document-intelligence/extractions/{job.id}/validate",
        json={"application_id": str(application.id)},
    )
    assert repeated.status_code == 201
    assert repeated.json()["id"] == assessment["id"]

    reviewed = client.post(
        f"/api/v1/document-intelligence/validations/{assessment['id']}/review",
        json={"decision": "approved", "notes": "All compared facts checked against their source records."},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["review_status"] == "approved"
    assert reviewed.json()["reviewed_by"] == "pytest-admin"

    changed_profile = client.put(
        f"/api/v1/profiles/leads/{lead.id}/current",
        json=_profile_payload(document.id, years=8, role="Product Manager"),
    )
    assert changed_profile.status_code == 200
    regenerated = client.post(
        f"/api/v1/document-intelligence/extractions/{job.id}/validate",
        json={"application_id": str(application.id)},
    )
    assert regenerated.status_code == 201, regenerated.text
    new_assessment = regenerated.json()
    assert new_assessment["id"] != assessment["id"]
    assert new_assessment["profile_version"] == 2
    assert new_assessment["result_status"] == "inconsistencies_found"
    assert new_assessment["mismatch_count"] == 2

    old = client.get(f"/api/v1/document-intelligence/validations/{assessment['id']}")
    assert old.status_code == 200
    assert old.json()["profile_version"] == 1
    assert old.json()["match_count"] == 4
    assert old.json()["source_facts"]["profile"]["facts"]["years_experience"] == 5.0
    assert len(db_session.exec(select(DocumentConsistencyAssessment)).all()) == 2

    actions = {
        row.action for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_type == "document_consistency_assessment")
        ).all()
    }
    assert {"document_consistency_assessed", "document_consistency_approved"} <= actions


def test_consistency_validation_requires_approved_extraction_and_current_consent(
    client: TestClient,
    db_session: Session,
) -> None:
    lead = create_lead(db_session, name="Consent Guard", target_country="Germany")
    document, job = _approved_cv_extraction(db_session, lead.id)
    profile_payload = _profile_payload(document.id)
    profile = client.put(f"/api/v1/profiles/leads/{lead.id}/current", json=profile_payload)
    assert profile.status_code == 200
    job.status = "needs_review"
    db_session.add(job)
    db_session.commit()
    not_approved = client.post(
        f"/api/v1/document-intelligence/extractions/{job.id}/validate",
        json={},
    )
    assert not_approved.status_code == 400

    job.status = "approved"
    db_session.add(job)
    db_session.commit()
    withdrawn = client.put(
        f"/api/v1/profiles/leads/{lead.id}/current",
        json={**profile_payload, "consent_status": "withdrawn"},
    )
    assert withdrawn.status_code == 200
    restricted = client.post(
        f"/api/v1/document-intelligence/extractions/{job.id}/validate",
        json={},
    )
    assert restricted.status_code == 400
    assert "consent" in restricted.json()["detail"].lower()

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    DocumentConsistencyAssessment,
    DocumentExtractionJob,
    DocumentRecord,
    Lead,
    Profile,
    now_utc,
)
from app.schemas import DocumentConsistencyAssessmentRead, DocumentConsistencyFinding
from app.services.audit_log import record_audit
from app.services.document_intelligence import canonical_document_type
from app.services.mobility_profiles import current_mobility_profile, profile_facts


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _normalized(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _text_match(extracted: Any, expected: Any) -> bool:
    left = _normalized(extracted)
    right = _normalized(expected)
    if not left or not right:
        return False
    if left == right or left in right or right in left:
        return True
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    union = left_tokens | right_tokens
    return bool(union) and len(left_tokens & right_tokens) / len(union) >= 0.6


def _number_match(extracted: Any, expected: Any) -> bool:
    try:
        left = float(extracted)
        right = float(expected)
    except (TypeError, ValueError):
        return False
    return abs(left - right) <= max(0.5, abs(right) * 0.1)


def _finding(
    *,
    key: str,
    document_field: str,
    source: str,
    source_path: str,
    extracted: Any,
    expected: Any,
    comparator: str = "text",
    severity: str = "warning",
    missing_expected_explanation: str | None = None,
) -> DocumentConsistencyFinding:
    if extracted is None or extracted == "":
        outcome = "missing_document_value"
        explanation = f"The approved extraction has no value for {document_field}."
    elif expected is None or expected == "" or expected == []:
        outcome = "missing_source_value"
        explanation = missing_expected_explanation or f"No comparison value exists at {source_path}."
    else:
        matched = _number_match(extracted, expected) if comparator == "number" else _text_match(extracted, expected)
        outcome = "match" if matched else "mismatch"
        explanation = (
            f"Approved {document_field} is consistent with {source_path}."
            if matched
            else f"Approved {document_field} differs from {source_path}; a human must resolve which source is correct."
        )
    return DocumentConsistencyFinding(
        finding_key=key,
        document_field=document_field,
        source=source,
        source_path=source_path,
        outcome=outcome,
        severity="info" if outcome in {"match", "not_comparable"} else severity,
        extracted_value=extracted,
        source_value=expected,
        explanation=explanation,
    )


def _list_values(items: Any, keys: tuple[str, ...]) -> list[Any]:
    values: list[Any] = []
    if not isinstance(items, list):
        return values
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in keys:
            if item.get(key) not in {None, ""}:
                values.append(item[key])
                break
    return values


def _best_expected(extracted: Any, candidates: list[Any]) -> Any:
    if not candidates:
        return None
    return next((candidate for candidate in candidates if _text_match(extracted, candidate)), candidates[0])


def _application_snapshot(application: ApplicationRecord | None) -> dict[str, Any]:
    if application is None:
        return {}
    return {
        "id": str(application.id),
        "lead_id": str(application.lead_id) if application.lead_id else None,
        "domain": application.domain,
        "target_country": application.target_country,
        "target_institution_or_employer": application.target_institution_or_employer,
        "status": application.status,
        "risk_score": application.risk_score,
        "created_at": application.created_at,
    }


def _identity_finding(data: dict[str, Any], document_type: str, lead: Lead) -> DocumentConsistencyFinding | None:
    field_by_type = {
        "passport": "full_name",
        "cv": "full_name",
        "degree_certificate": "holder_name",
        "academic_transcript": "student_name",
        "employment_letter": "employee_name",
        "bank_statement": "account_holder",
    }
    field = field_by_type.get(document_type)
    if not field:
        return None
    return _finding(
        key="identity_name_consistency",
        document_field=field,
        source="lead",
        source_path="lead.full_name",
        extracted=data.get(field),
        expected=lead.full_name,
        severity="high",
    )


def _profile_findings(data: dict[str, Any], document_type: str, facts: dict[str, Any]) -> list[DocumentConsistencyFinding]:
    findings: list[DocumentConsistencyFinding] = []
    education = facts.get("education", [])
    employment = facts.get("employment", [])
    if document_type == "cv":
        findings.append(_finding(
            key="experience_years_consistency",
            document_field="years_experience",
            source="profile",
            source_path="profile.years_experience",
            extracted=data.get("years_experience"),
            expected=facts.get("years_experience"),
            comparator="number",
        ))
        role_candidates = _list_values(employment, ("role", "job_title", "position"))
        if facts.get("desired_role"):
            role_candidates.append(facts["desired_role"])
        findings.append(_finding(
            key="profession_consistency",
            document_field="profession",
            source="profile",
            source_path="profile.employment[].role",
            extracted=data.get("profession"),
            expected=_best_expected(data.get("profession"), role_candidates),
        ))
    elif document_type == "degree_certificate":
        qualifications = _list_values(education, ("qualification", "degree", "award"))
        institutions = _list_values(education, ("institution", "university", "school"))
        findings.extend([
            _finding(
                key="qualification_consistency",
                document_field="qualification",
                source="profile",
                source_path="profile.education[].qualification",
                extracted=data.get("qualification"),
                expected=_best_expected(data.get("qualification"), qualifications),
            ),
            _finding(
                key="education_institution_consistency",
                document_field="institution",
                source="profile",
                source_path="profile.education[].institution",
                extracted=data.get("institution"),
                expected=_best_expected(data.get("institution"), institutions),
            ),
        ])
    elif document_type == "academic_transcript":
        institutions = _list_values(education, ("institution", "university", "school"))
        programmes = _list_values(education, ("field_of_study", "programme", "program"))
        findings.extend([
            _finding(
                key="transcript_institution_consistency",
                document_field="institution",
                source="profile",
                source_path="profile.education[].institution",
                extracted=data.get("institution"),
                expected=_best_expected(data.get("institution"), institutions),
            ),
            _finding(
                key="transcript_programme_consistency",
                document_field="programme",
                source="profile",
                source_path="profile.education[].field_of_study",
                extracted=data.get("programme"),
                expected=_best_expected(data.get("programme"), programmes),
            ),
        ])
    elif document_type == "employment_letter":
        roles = _list_values(employment, ("role", "job_title", "position"))
        employers = _list_values(employment, ("employer", "company", "organization"))
        findings.extend([
            _finding(
                key="employment_role_consistency",
                document_field="job_title",
                source="profile",
                source_path="profile.employment[].role",
                extracted=data.get("job_title"),
                expected=_best_expected(data.get("job_title"), roles),
            ),
            _finding(
                key="employment_employer_consistency",
                document_field="employer",
                source="profile",
                source_path="profile.employment[].employer",
                extracted=data.get("employer"),
                expected=_best_expected(data.get("employer"), employers),
            ),
        ])
    elif document_type == "passport":
        findings.append(_finding(
            key="nationality_profile_gap",
            document_field="nationality",
            source="profile",
            source_path="profile.nationality",
            extracted=data.get("nationality"),
            expected=None,
            severity="warning",
            missing_expected_explanation="The Universal Mobility Profile does not yet store a nationality fact for comparison.",
        ))
    elif document_type == "bank_statement":
        findings.append(DocumentConsistencyFinding(
            finding_key="balance_budget_semantic_boundary",
            document_field="closing_balance",
            source="system",
            source_path="profile.finances.budget_eur",
            outcome="not_comparable",
            severity="info",
            extracted_value=data.get("closing_balance"),
            source_value=facts.get("budget_eur"),
            explanation="A statement closing balance and a declared mobility budget are different facts and are not compared as equal.",
        ))
    return findings


def _application_findings(
    data: dict[str, Any],
    document: DocumentRecord,
    document_type: str,
    application: ApplicationRecord | None,
) -> list[DocumentConsistencyFinding]:
    if application is None:
        return [DocumentConsistencyFinding(
            finding_key="application_context_missing",
            document_field="document_type",
            source="application",
            source_path="application",
            outcome="missing_source_value",
            severity="warning",
            extracted_value=document.document_type,
            source_value=None,
            explanation="No application record exists for route-context validation.",
        )]
    domain_aliases = {
        "overseas_job": "work", "job": "work", "education": "study", "study_abroad": "study",
        "immigration": "visa",
    }
    domain = domain_aliases.get(_normalized(application.domain).replace(" ", "_"), _normalized(application.domain).replace(" ", "_"))
    allowed_domains = {
        "passport": {"work", "study", "visa", "family", "settlement", "scholarship", "digital_nomad"},
        "cv": {"work", "study", "scholarship", "digital_nomad"},
        "degree_certificate": {"work", "study", "scholarship", "visa"},
        "academic_transcript": {"study", "scholarship", "work"},
        "employment_letter": {"work", "visa", "settlement", "digital_nomad"},
        "bank_statement": {"work", "study", "visa", "family", "settlement", "scholarship", "digital_nomad"},
    }.get(document_type, set())
    relevant = domain in allowed_domains
    findings = [DocumentConsistencyFinding(
        finding_key="application_document_relevance",
        document_field="document_type",
        source="application",
        source_path="application.domain",
        outcome="match" if relevant else "mismatch",
        severity="info" if relevant else "warning",
        extracted_value=document.document_type,
        source_value=application.domain,
        explanation=(
            "This document type is relevant to the recorded application domain."
            if relevant else "This document type is not normally associated with the recorded application domain; review its purpose."
        ),
    )]
    original_type = canonical_document_type(document.document_type)
    is_target_employment_document = document.document_type.strip().lower().replace(" ", "_").replace("-", "_") in {
        "job_offer", "employment_contract", "job_offer_or_employment_contract",
    }
    if original_type == "employment_letter" and is_target_employment_document:
        findings.append(_finding(
            key="application_employer_consistency",
            document_field="employer",
            source="application",
            source_path="application.target_institution_or_employer",
            extracted=data.get("employer"),
            expected=application.target_institution_or_employer,
            severity="high",
        ))
    return findings


def assessment_read(assessment: DocumentConsistencyAssessment) -> DocumentConsistencyAssessmentRead:
    return DocumentConsistencyAssessmentRead(
        **assessment.model_dump(exclude={"findings_json", "source_facts_json"}),
        findings=_load(assessment.findings_json, []),
        source_facts=_load(assessment.source_facts_json, {}),
    )


def generate_consistency_assessment(
    session: Session,
    extraction_job_id: UUID,
    *,
    application_id: UUID | None,
    actor: str,
) -> DocumentConsistencyAssessmentRead:
    job = session.get(DocumentExtractionJob, extraction_job_id)
    if job is None:
        raise ValueError("Document extraction job not found")
    if job.status != "approved":
        raise ValueError("Only a human-approved extraction can be validated")
    document = session.get(DocumentRecord, job.document_id)
    if document is None or document.lead_id is None:
        raise ValueError("Document is not linked to a lead")
    lead = session.get(Lead, document.lead_id)
    profile = current_mobility_profile(session, document.lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    if profile is None:
        raise ValueError("A current Universal Mobility Profile is required")
    if profile.consent_status != "granted":
        raise ValueError("Current profile consent must be granted for consistency validation")
    application = session.get(ApplicationRecord, application_id) if application_id else session.exec(
        select(ApplicationRecord)
        .where(ApplicationRecord.lead_id == document.lead_id)
        .order_by(ApplicationRecord.created_at.desc())
    ).first()
    if application_id and application is None:
        raise ValueError("Application not found")
    if application and application.lead_id != document.lead_id:
        raise ValueError("Application belongs to another lead")
    existing_statement = (
        select(DocumentConsistencyAssessment)
        .where(DocumentConsistencyAssessment.extraction_job_id == job.id)
        .where(DocumentConsistencyAssessment.profile_id == profile.id)
    )
    if application:
        existing_statement = existing_statement.where(DocumentConsistencyAssessment.application_id == application.id)
    else:
        existing_statement = existing_statement.where(DocumentConsistencyAssessment.application_id.is_(None))
    existing = session.exec(existing_statement.order_by(DocumentConsistencyAssessment.created_at.desc())).first()
    if existing:
        return assessment_read(existing)

    data = _load(job.structured_data_json, {})
    facts = profile_facts(profile)
    document_type = canonical_document_type(document.document_type)
    findings: list[DocumentConsistencyFinding] = []
    identity = _identity_finding(data, document_type, lead)
    if identity:
        findings.append(identity)
    findings.extend(_profile_findings(data, document_type, facts))
    findings.extend(_application_findings(data, document, document_type, application))
    match_count = sum(item.outcome == "match" for item in findings)
    mismatch_count = sum(item.outcome == "mismatch" for item in findings)
    missing_count = sum(item.outcome in {"missing_document_value", "missing_source_value"} for item in findings)
    if mismatch_count:
        result_status = "inconsistencies_found"
    elif missing_count:
        result_status = "insufficient_context"
    else:
        result_status = "consistent"
    summary = (
        f"Compared approved extraction against lead identity, profile v{profile.profile_version}, and "
        f"{'application ' + str(application.id) if application else 'no application context'}: "
        f"{match_count} match(es), {mismatch_count} mismatch(es), and {missing_count} missing comparison value(s). "
        "A human reviewer must decide the assessment; no source facts were changed."
    )
    now = now_utc()
    assessment = DocumentConsistencyAssessment(
        extraction_job_id=job.id,
        document_id=document.id,
        lead_id=lead.id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        application_id=application.id if application else None,
        result_status=result_status,
        review_status="pending",
        match_count=match_count,
        mismatch_count=mismatch_count,
        missing_count=missing_count,
        findings_json=_dump([item.model_dump(mode="json") for item in findings]),
        source_facts_json=_dump({
            "lead": {"id": str(lead.id), "full_name": lead.full_name},
            "profile": {"id": str(profile.id), "version": profile.profile_version, "facts": facts},
            "application": _application_snapshot(application),
            "extraction": {"job_id": str(job.id), "schema_version": job.schema_version, "structured_data": data},
        }),
        summary=summary,
        generated_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(assessment)
    session.flush()
    record_audit(
        session,
        action="document_consistency_assessed",
        entity_type="document_consistency_assessment",
        entity_id=assessment.id,
        after_state={
            "extraction_job_id": str(job.id),
            "profile_id": str(profile.id),
            "profile_version": profile.profile_version,
            "application_id": str(application.id) if application else None,
            "result_status": result_status,
            "match_count": match_count,
            "mismatch_count": mismatch_count,
            "missing_count": missing_count,
        },
        reason="Generated immutable document-to-profile/application consistency assessment",
        actor=actor,
        source="document_consistency_v9_1",
    )
    session.commit()
    session.refresh(assessment)
    return assessment_read(assessment)


def review_consistency_assessment(
    session: Session,
    assessment_id: UUID,
    *,
    decision: str,
    notes: str,
    actor: str,
) -> DocumentConsistencyAssessmentRead:
    assessment = session.get(DocumentConsistencyAssessment, assessment_id)
    if assessment is None:
        raise ValueError("Document consistency assessment not found")
    if assessment.review_status != "pending":
        raise ValueError("Only a pending consistency assessment can be reviewed")
    profile = current_mobility_profile(session, assessment.lead_id)
    if profile is None or profile.consent_status != "granted":
        raise ValueError("Current profile consent must be granted for consistency review")
    now = now_utc()
    assessment.review_status = decision
    assessment.reviewed_by = actor
    assessment.review_notes = notes
    assessment.reviewed_at = now
    assessment.updated_at = now
    record_audit(
        session,
        action=f"document_consistency_{decision}",
        entity_type="document_consistency_assessment",
        entity_id=assessment.id,
        after_state={
            "result_status": assessment.result_status,
            "review_status": decision,
            "reviewed_by": actor,
        },
        reason=notes,
        actor=actor,
        source="document_consistency_v9_1",
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment_read(assessment)

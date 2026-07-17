from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    DocumentConsistencyAssessment,
    DocumentExtractionJob,
    DocumentRecord,
    DocumentRequirementAssessment,
    EligibilityAssessment,
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityTimeline,
    PathwayComparisonAssessment,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.document_intelligence import canonical_document_type
from app.services.eligibility_engine import _required_documents
from app.services.mobility_profiles import current_mobility_profile


REVIEW_DECISIONS = {"approved", "rejected"}
PUBLISHED_VERSION_STATES = {"published", "superseded", "retired"}
REJECTED_DOCUMENT_STATES = {"rejected", "invalid", "failed", "deleted"}
VERIFIED_DOCUMENT_STATES = {"verified", "approved", "accepted"}


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def _load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _normal(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _domain(value: Any) -> str:
    normalized = _normal(getattr(value, "value", value))
    return {
        "study_abroad": "study",
        "overseas_job": "work",
        "job": "work",
        "education": "study",
        "immigration": "visa",
    }.get(normalized, normalized or "general")


def _expected_types(label: str) -> list[str]:
    text = _normal(label)
    mappings: list[tuple[tuple[str, ...], list[str]]] = [
        (("passport",), ["passport"]),
        (("cv", "resume", "curriculum_vitae"), ["cv"]),
        (("academic_transcript", "transcript"), ["academic_transcript"]),
        (("degree", "professional_certificate", "qualification_certificate"), ["degree_certificate"]),
        (("employment_contract", "job_offer", "employment_letter", "work_experience"), ["employment_letter"]),
        (("bank_statement", "financial_proof", "proof_of_financial", "proof_of_funds", "financial_means"), ["bank_statement", "proof_of_funds", "salary_proof"]),
        (("language_test", "language_ability", "language_certificate"), ["language_test", "language_certificate"]),
        (("admission_letter", "confirmation_of_enrolment", "confirmation_of_enrollment", "coe"), ["admission_letter", "confirmation_of_enrolment"]),
        (("statement_of_purpose", "motivation_letter", "purpose_of_travel"), ["statement_of_purpose", "motivation_letter", "purpose_statement"]),
        (("accommodation", "invitation_letter"), ["accommodation_evidence", "invitation_letter"]),
        (("travel_itinerary", "return_ticket"), ["travel_itinerary", "return_ticket"]),
        (("birth_certificate",), ["birth_certificate"]),
        (("marriage_certificate",), ["marriage_certificate"]),
        (("police_clearance", "criminal_record"), ["police_clearance"]),
        (("medical", "health_certificate"), ["medical_certificate"]),
        (("photo", "photograph"), ["passport_photo"]),
    ]
    for needles, types in mappings:
        if any(needle in text for needle in needles):
            return types
    canonical = canonical_document_type(text)
    return [canonical] if canonical else ["unspecified_document"]


def _normalize_requirements(raw: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, item in enumerate(raw, start=1):
        if isinstance(item, dict):
            label = str(item.get("name") or item.get("label") or item.get("document_type") or "").strip()
            optional = bool(item.get("optional", False))
            supplied_types = item.get("document_types") or item.get("accepted_types") or []
        else:
            label = str(item or "").strip()
            optional = "if available" in label.lower() or "optional" in label.lower()
            supplied_types = []
        if not label:
            continue
        expected = [canonical_document_type(str(value)) for value in supplied_types if value]
        expected = list(dict.fromkeys(expected or _expected_types(label)))
        key = _normal(label)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({
            "requirement_key": key or f"requirement_{position}",
            "label": label,
            "expected_document_types": expected,
            "optional": optional,
            "position": position,
        })
    return normalized


def _latest_application(session: Session, lead_id: UUID) -> ApplicationRecord | None:
    return session.exec(
        select(ApplicationRecord)
        .where(ApplicationRecord.lead_id == lead_id)
        .order_by(ApplicationRecord.created_at.desc())
    ).first()


def _version_requirements(
    session: Session,
    version_id: UUID,
    *,
    explicit: bool,
) -> tuple[MobilityPathwayVersion, MobilityPathway, list[Any]] | None:
    version = session.get(MobilityPathwayVersion, version_id)
    if version is None:
        if explicit:
            raise ValueError("Pathway version not found")
        return None
    pathway = session.get(MobilityPathway, version.pathway_id)
    if pathway is None:
        if explicit:
            raise ValueError("Pathway not found")
        return None
    if version.lifecycle_status not in PUBLISHED_VERSION_STATES or version.published_at is None:
        if explicit:
            raise ValueError("Only a human-published pathway version can supply document requirements")
        return None
    requirements = _load(version.required_documents_json, [])
    if not requirements:
        if explicit:
            raise ValueError("Selected pathway version has no required-document criteria")
        return None
    return version, pathway, requirements


def _resolve_requirements(
    session: Session,
    lead: Lead,
    *,
    application_id: UUID | None,
    pathway_version_id: UUID | None,
) -> dict[str, Any]:
    application = session.get(ApplicationRecord, application_id) if application_id else _latest_application(session, lead.id)
    if application_id and application is None:
        raise ValueError("Application not found")
    if application and application.lead_id != lead.id:
        raise ValueError("Application belongs to another lead")

    version_source: tuple[MobilityPathwayVersion, MobilityPathway, list[Any]] | None = None
    if pathway_version_id:
        version_source = _version_requirements(session, pathway_version_id, explicit=True)
    else:
        timeline = session.exec(
            select(MobilityTimeline)
            .where(MobilityTimeline.lead_id == lead.id)
            .order_by(MobilityTimeline.created_at.desc())
        ).first()
        if timeline:
            version_source = _version_requirements(
                session,
                timeline.primary_pathway_version_id,
                explicit=False,
            )
        if version_source is None:
            comparison = session.exec(
                select(PathwayComparisonAssessment)
                .where(PathwayComparisonAssessment.lead_id == lead.id)
                .where(PathwayComparisonAssessment.primary_pathway_version_id.is_not(None))
                .order_by(PathwayComparisonAssessment.created_at.desc())
            ).first()
            if comparison and comparison.primary_pathway_version_id:
                version_source = _version_requirements(
                    session,
                    comparison.primary_pathway_version_id,
                    explicit=False,
                )

    if version_source:
        version, pathway, raw = version_source
        return {
            "application": application,
            "pathway": pathway,
            "pathway_version": version,
            "eligibility_assessment": None,
            "requirement_source": "published_pathway_version",
            "requirements": _normalize_requirements(raw),
            "source_snapshot": {
                "type": "published_pathway_version",
                "pathway_id": str(pathway.id),
                "pathway_key": pathway.pathway_key,
                "pathway_name": pathway.name,
                "country": pathway.country,
                "domain": pathway.domain,
                "pathway_version_id": str(version.id),
                "version_number": version.version_number,
                "lifecycle_status": version.lifecycle_status,
                "published_at": version.published_at,
                "approved_by": version.approved_by,
                "official_source_id": version.official_source_id,
                "source_snapshot_id": version.source_snapshot_id,
                "verified_rule_ids": _load(version.verified_rule_ids_json, []),
                "application": application.model_dump(mode="json") if application else None,
            },
        }

    eligibility_statement = (
        select(EligibilityAssessment)
        .where(EligibilityAssessment.lead_id == lead.id)
        .order_by(EligibilityAssessment.created_at.desc())
    )
    eligibility_rows = list(session.exec(eligibility_statement).all())
    eligibility = next(
        (
            row for row in eligibility_rows
            if _load(row.required_documents_json, [])
            and (not application or _domain(row.domain) == _domain(application.domain))
            and (not application or not application.target_country or not row.target_country or _normal(row.target_country) == _normal(application.target_country))
        ),
        None,
    )
    if eligibility:
        raw = _load(eligibility.required_documents_json, [])
        return {
            "application": application,
            "pathway": None,
            "pathway_version": None,
            "eligibility_assessment": eligibility,
            "requirement_source": "eligibility_assessment",
            "requirements": _normalize_requirements(raw),
            "source_snapshot": {
                "type": "eligibility_assessment",
                "eligibility_assessment_id": str(eligibility.id),
                "domain": eligibility.domain,
                "target_country": eligibility.target_country,
                "status": eligibility.status,
                "created_at": eligibility.created_at,
                "application": application.model_dump(mode="json") if application else None,
            },
        }

    domain = _domain(application.domain if application else lead.intent)
    raw = _required_documents(domain)
    if not raw:
        raise ValueError("No document requirements are available for this lead")
    return {
        "application": application,
        "pathway": None,
        "pathway_version": None,
        "eligibility_assessment": None,
        "requirement_source": "application_domain_baseline" if application else "lead_intent_baseline",
        "requirements": _normalize_requirements(raw),
        "source_snapshot": {
            "type": "application_domain_baseline" if application else "lead_intent_baseline",
            "domain": domain,
            "target_country": application.target_country if application else lead.target_country,
            "application": application.model_dump(mode="json") if application else None,
            "warning": "Baseline requirements are deterministic operational guidance and require human confirmation against a reviewed pathway.",
        },
    }


def _document_snapshot(
    documents: list[DocumentRecord],
    extractions: list[DocumentExtractionJob],
    consistency: list[DocumentConsistencyAssessment],
) -> list[dict[str, Any]]:
    jobs_by_document: dict[UUID, list[DocumentExtractionJob]] = {}
    for job in extractions:
        jobs_by_document.setdefault(job.document_id, []).append(job)
    assessments_by_document: dict[UUID, list[DocumentConsistencyAssessment]] = {}
    for assessment in consistency:
        assessments_by_document.setdefault(assessment.document_id, []).append(assessment)
    rows: list[dict[str, Any]] = []
    for document in sorted(documents, key=lambda row: str(row.id)):
        jobs = sorted(jobs_by_document.get(document.id, []), key=lambda row: row.created_at, reverse=True)
        assessments = sorted(assessments_by_document.get(document.id, []), key=lambda row: row.created_at, reverse=True)
        rows.append({
            "id": str(document.id),
            "document_type": document.document_type,
            "canonical_document_type": canonical_document_type(document.document_type),
            "filename": document.filename,
            "status": document.status,
            "file_hash": document.file_hash,
            "expiry_date": document.expiry_date,
            "verified_by": document.verified_by,
            "verified_at": document.verified_at,
            "updated_at": document.updated_at,
            "latest_extraction": ({
                "id": str(jobs[0].id),
                "status": jobs[0].status,
                "schema_version": jobs[0].schema_version,
                "reviewed_by": jobs[0].reviewed_by,
                "reviewed_at": jobs[0].reviewed_at,
            } if jobs else None),
            "consistency_assessments": [{
                "id": str(item.id),
                "result_status": item.result_status,
                "review_status": item.review_status,
                "mismatch_count": item.mismatch_count,
                "missing_count": item.missing_count,
                "profile_version": item.profile_version,
            } for item in assessments],
        })
    return rows


def _is_expired(document: DocumentRecord, reference: datetime) -> bool:
    if document.expiry_date is None:
        return False
    expiry = document.expiry_date
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    return expiry <= reference


def _has_fact_inconsistency(document_id: UUID, assessments: list[DocumentConsistencyAssessment]) -> bool:
    return any(
        row.document_id == document_id
        and row.result_status == "inconsistencies_found"
        and row.review_status != "rejected"
        and row.mismatch_count > 0
        for row in assessments
    )


def _coverage_findings(
    requirements: list[dict[str, Any]],
    documents: list[DocumentRecord],
    consistency: list[DocumentConsistencyAssessment],
    *,
    reference: datetime,
) -> tuple[list[dict[str, Any]], int, int, int, int]:
    by_type: dict[str, list[DocumentRecord]] = {}
    for document in documents:
        by_type.setdefault(canonical_document_type(document.document_type), []).append(document)

    findings: list[dict[str, Any]] = []
    required_count = sum(not row["optional"] for row in requirements)
    satisfied_count = 0
    missing_count = 0
    inconsistency_count = 0

    for requirement in requirements:
        expected = set(requirement["expected_document_types"])
        candidates = [doc for doc_type, rows in by_type.items() if doc_type in expected for doc in rows]
        usable = [doc for doc in candidates if _normal(doc.status) not in REJECTED_DOCUMENT_STATES]
        nonexpired = [doc for doc in usable if not _is_expired(doc, reference)]
        verified = [
            doc for doc in nonexpired
            if _normal(doc.status) in VERIFIED_DOCUMENT_STATES or doc.verified_at is not None
        ]
        inconsistent = [doc for doc in nonexpired if _has_fact_inconsistency(doc.id, consistency)]

        outcome: str
        severity: str
        explanation: str
        evidence = {
            "candidate_document_ids": [str(doc.id) for doc in candidates],
            "candidate_statuses": {str(doc.id): doc.status for doc in candidates},
            "candidate_expiry_dates": {str(doc.id): doc.expiry_date for doc in candidates},
        }
        if not candidates:
            if requirement["optional"]:
                outcome, severity = "optional_missing", "info"
                explanation = "No matching document is recorded, but this requirement is explicitly optional."
            else:
                outcome, severity = "missing", "high"
                explanation = "No stored document matches the required document type."
                missing_count += 1
        elif not usable:
            outcome, severity = "rejected", "high"
            explanation = "Matching documents exist, but every candidate is rejected or invalid."
            inconsistency_count += 1
        elif not nonexpired:
            outcome, severity = "expired", "high"
            explanation = "Matching documents exist, but every usable candidate is expired."
            inconsistency_count += 1
        elif inconsistent:
            outcome, severity = "fact_inconsistency", "high"
            explanation = "A matching document has unresolved or human-approved profile/application mismatch findings."
            inconsistency_count += 1
        elif not verified:
            outcome, severity = "present_unverified", "warning"
            explanation = "A matching document is stored but has not completed authenticity verification."
            inconsistency_count += 1
        else:
            outcome, severity = "satisfied", "info"
            explanation = "At least one current, verified matching document is recorded."
            if not requirement["optional"]:
                satisfied_count += 1

        findings.append({
            "finding_key": f"coverage:{requirement['requirement_key']}",
            "finding_type": "requirement_coverage",
            "requirement_key": requirement["requirement_key"],
            "requirement_label": requirement["label"],
            "expected_document_types": requirement["expected_document_types"],
            "optional": requirement["optional"],
            "outcome": outcome,
            "severity": severity,
            "document_ids": [str(doc.id) for doc in candidates],
            "document_names": [doc.filename for doc in candidates],
            "explanation": explanation,
            "evidence": evidence,
        })

        active_candidates = [doc for doc in nonexpired if _normal(doc.status) not in REJECTED_DOCUMENT_STATES]
        if len(active_candidates) > 1:
            hashes = {doc.file_hash for doc in active_candidates if doc.file_hash}
            expiries = {doc.expiry_date.isoformat() for doc in active_candidates if doc.expiry_date}
            statuses = {_normal(doc.status) for doc in active_candidates}
            if len(hashes) > 1 or len(expiries) > 1 or len(statuses) > 1:
                findings.append({
                    "finding_key": f"duplicate:{requirement['requirement_key']}",
                    "finding_type": "cross_document_inconsistency",
                    "requirement_key": requirement["requirement_key"],
                    "requirement_label": requirement["label"],
                    "expected_document_types": requirement["expected_document_types"],
                    "optional": requirement["optional"],
                    "outcome": "duplicate_conflict",
                    "severity": "warning",
                    "document_ids": [str(doc.id) for doc in active_candidates],
                    "document_names": [doc.filename for doc in active_candidates],
                    "explanation": "Multiple active candidates have different hashes, expiry dates, or verification states and require human reconciliation.",
                    "evidence": {
                        "file_hashes": sorted(value for value in hashes if value),
                        "expiry_dates": sorted(expiries),
                        "statuses": sorted(statuses),
                    },
                })
                inconsistency_count += 1

    return findings, required_count, satisfied_count, missing_count, inconsistency_count


def assessment_read(assessment: DocumentRequirementAssessment) -> dict[str, Any]:
    return {
        **assessment.model_dump(exclude={
            "requirements_json",
            "findings_json",
            "source_snapshot_json",
            "document_snapshot_json",
        }),
        "requirements": _load(assessment.requirements_json, []),
        "findings": _load(assessment.findings_json, []),
        "source_snapshot": _load(assessment.source_snapshot_json, {}),
        "document_snapshot": _load(assessment.document_snapshot_json, []),
        "source_records_unchanged": True,
        "documents_created": 0,
        "eligibility_changed": False,
    }


def generate_document_requirement_assessment(
    session: Session,
    lead_id: UUID,
    *,
    application_id: UUID | None = None,
    pathway_version_id: UUID | None = None,
    actor: str = "system",
    as_of: datetime | None = None,
) -> tuple[DocumentRequirementAssessment, bool]:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    profile = current_mobility_profile(session, lead_id)
    if profile and profile.consent_status == "withdrawn":
        raise ValueError("Current profile consent is withdrawn")

    resolved = _resolve_requirements(
        session,
        lead,
        application_id=application_id,
        pathway_version_id=pathway_version_id,
    )
    requirements = resolved["requirements"]
    if not requirements:
        raise ValueError("No document requirements are available for assessment")

    documents = list(session.exec(
        select(DocumentRecord).where(DocumentRecord.lead_id == lead_id)
    ).all())
    extractions = list(session.exec(
        select(DocumentExtractionJob).where(DocumentExtractionJob.lead_id == lead_id)
    ).all())
    consistency = list(session.exec(
        select(DocumentConsistencyAssessment).where(DocumentConsistencyAssessment.lead_id == lead_id)
    ).all())
    reference = as_of or now_utc()
    findings, required_count, satisfied_count, missing_count, inconsistency_count = _coverage_findings(
        requirements,
        documents,
        consistency,
        reference=reference,
    )
    document_snapshot = _document_snapshot(documents, extractions, consistency)
    key_payload = {
        "lead_id": str(lead_id),
        "application_id": str(resolved["application"].id) if resolved["application"] else None,
        "pathway_version_id": str(resolved["pathway_version"].id) if resolved["pathway_version"] else None,
        "eligibility_assessment_id": str(resolved["eligibility_assessment"].id) if resolved["eligibility_assessment"] else None,
        "requirement_source": resolved["requirement_source"],
        "requirements": requirements,
        "source_snapshot": resolved["source_snapshot"],
        "documents": document_snapshot,
    }
    assessment_key = hashlib.sha256(_dump(key_payload).encode("utf-8")).hexdigest()
    existing = session.exec(
        select(DocumentRequirementAssessment).where(
            DocumentRequirementAssessment.assessment_key == assessment_key
        )
    ).first()
    if existing:
        return existing, False

    if missing_count and inconsistency_count:
        result_status = "gaps_and_inconsistencies"
    elif missing_count:
        result_status = "missing_documents"
    elif inconsistency_count:
        result_status = "inconsistencies_found"
    else:
        result_status = "complete"
    summary = (
        f"Assessed {required_count} required document item(s) from {resolved['requirement_source']}: "
        f"{satisfied_count} satisfied, {missing_count} missing, and {inconsistency_count} inconsistency signal(s). "
        "The assessment is a human-review queue item; no document, profile, application, eligibility, or timeline record was changed."
    )
    assessment = DocumentRequirementAssessment(
        assessment_key=assessment_key,
        lead_id=lead_id,
        application_id=resolved["application"].id if resolved["application"] else None,
        pathway_id=resolved["pathway"].id if resolved["pathway"] else None,
        pathway_version_id=resolved["pathway_version"].id if resolved["pathway_version"] else None,
        eligibility_assessment_id=resolved["eligibility_assessment"].id if resolved["eligibility_assessment"] else None,
        profile_id=profile.id if profile else None,
        profile_version=profile.profile_version if profile else None,
        requirement_source=resolved["requirement_source"],
        result_status=result_status,
        review_status="pending",
        required_count=required_count,
        satisfied_count=satisfied_count,
        missing_count=missing_count,
        inconsistency_count=inconsistency_count,
        requirements_json=_dump(requirements),
        findings_json=_dump(findings),
        source_snapshot_json=_dump(resolved["source_snapshot"]),
        document_snapshot_json=_dump(document_snapshot),
        summary=summary,
        generated_by=actor,
        created_at=reference,
        updated_at=reference,
    )
    session.add(assessment)
    session.flush()
    record_audit(
        session,
        action="document_requirement_assessed",
        entity_type="document_requirement_assessment",
        entity_id=assessment.id,
        after_state={
            "lead_id": lead_id,
            "application_id": assessment.application_id,
            "pathway_version_id": assessment.pathway_version_id,
            "eligibility_assessment_id": assessment.eligibility_assessment_id,
            "requirement_source": assessment.requirement_source,
            "result_status": result_status,
            "required_count": required_count,
            "satisfied_count": satisfied_count,
            "missing_count": missing_count,
            "inconsistency_count": inconsistency_count,
            "documents_created": 0,
            "source_records_unchanged": True,
        },
        reason="Generated immutable missing-document and inconsistency assessment",
        actor=actor,
        source="document_requirement_detection_v9_3",
    )
    session.commit()
    session.refresh(assessment)
    return assessment, True


def scan_document_requirement_assessments(
    session: Session,
    *,
    lead_id: UUID | None = None,
    actor: str = "document-requirement-monitor",
) -> dict[str, Any]:
    if lead_id:
        leads = [session.get(Lead, lead_id)]
        if leads[0] is None:
            raise ValueError("Lead not found")
    else:
        leads = list(session.exec(select(Lead).order_by(Lead.created_at)).all())
    created = 0
    existing = 0
    skipped = 0
    assessment_ids: list[str] = []
    for lead in leads:
        if lead is None:
            continue
        try:
            assessment, was_created = generate_document_requirement_assessment(
                session,
                lead.id,
                actor=actor,
            )
        except ValueError as exc:
            if "consent is withdrawn" in str(exc).lower() or "requirements" in str(exc).lower():
                skipped += 1
                continue
            raise
        assessment_ids.append(str(assessment.id))
        created += int(was_created)
        existing += int(not was_created)
    record_audit(
        session,
        action="document_requirement_scan_completed",
        entity_type="document_requirement_monitor",
        entity_id=lead_id or "global",
        after_state={
            "lead_id": lead_id,
            "leads_scanned": len(leads),
            "created": created,
            "existing": existing,
            "skipped": skipped,
            "documents_created": 0,
            "external_messages_sent": 0,
        },
        reason="Completed deterministic document requirement scan",
        actor=actor,
        source="document_requirement_detection_v9_3",
    )
    session.commit()
    return {
        "lead_id": lead_id,
        "leads_scanned": len(leads),
        "created": created,
        "existing": existing,
        "skipped": skipped,
        "assessment_ids": assessment_ids,
        "documents_created": 0,
        "external_messages_sent": 0,
    }


def review_document_requirement_assessment(
    session: Session,
    assessment_id: UUID,
    *,
    decision: str,
    notes: str,
    actor: str,
) -> DocumentRequirementAssessment:
    if decision not in REVIEW_DECISIONS:
        raise ValueError("Unsupported document requirement review decision")
    assessment = session.get(DocumentRequirementAssessment, assessment_id)
    if assessment is None:
        raise ValueError("Document requirement assessment not found")
    if assessment.review_status != "pending":
        raise ValueError("Only a pending document requirement assessment can be reviewed")
    profile = current_mobility_profile(session, assessment.lead_id)
    if profile and profile.consent_status == "withdrawn":
        raise ValueError("Current profile consent is withdrawn")
    cleaned_notes = notes.strip()
    if len(cleaned_notes) < 3:
        raise ValueError("A review note is required")
    before = assessment.model_dump()
    reviewed_at = now_utc()
    assessment.review_status = decision
    assessment.reviewed_by = actor
    assessment.reviewed_at = reviewed_at
    assessment.review_notes = cleaned_notes
    assessment.updated_at = reviewed_at
    session.add(assessment)
    record_audit(
        session,
        action=f"document_requirement_{decision}",
        entity_type="document_requirement_assessment",
        entity_id=assessment.id,
        before_state=before,
        after_state={
            "review_status": decision,
            "reviewed_by": actor,
            "source_records_unchanged": True,
            "documents_created": 0,
        },
        reason=cleaned_notes,
        actor=actor,
        source="document_requirement_detection_v9_3",
    )
    session.commit()
    session.refresh(assessment)
    return assessment

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    DocumentConsistencyAssessment,
    DocumentExtractionJob,
    DocumentFraudRiskAssessment,
    DocumentRecord,
    DocumentRequirementAssessment,
    Lead,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.mobility_profiles import current_mobility_profile


REVIEW_DECISIONS = {"cleared", "specialist_review_required", "dismissed"}
REJECTED_DOCUMENT_STATES = {"rejected", "invalid", "failed"}
IDENTIFIER_FIELDS = {"document_number", "passport_number", "certificate_number", "licence_number", "license_number"}


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
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _masked(value: Any) -> str:
    text = re.sub(r"\s+", "", str(value or "").strip())
    if not text:
        return ""
    if len(text) <= 4:
        return "*" * len(text)
    return f"{'*' * max(4, len(text) - 4)}{text[-4:]}"


def _value_hash(value: Any) -> str:
    return hashlib.sha256(_normal(value).encode("utf-8")).hexdigest()


def _latest_application(session: Session, lead_id: UUID) -> ApplicationRecord | None:
    return session.exec(
        select(ApplicationRecord)
        .where(ApplicationRecord.lead_id == lead_id)
        .order_by(ApplicationRecord.created_at.desc())
    ).first()


def _document_snapshot(documents: list[DocumentRecord]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(document.id),
            "lead_id": str(document.lead_id) if document.lead_id else None,
            "document_type": document.document_type,
            "filename": document.filename,
            "file_hash": document.file_hash,
            "status": document.status,
            "storage_provider": document.storage_provider,
            "mime_type": document.mime_type,
            "file_size_bytes": document.file_size_bytes,
            "expiry_date": document.expiry_date,
            "verified_by": document.verified_by,
            "verified_at": document.verified_at,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }
        for document in sorted(documents, key=lambda item: str(item.id))
    ]


def _add_indicator(
    indicators: list[dict[str, Any]],
    *,
    indicator_type: str,
    severity: str,
    document_ids: list[UUID],
    document_names: list[str],
    source_record_type: str,
    source_record_ids: list[str],
    explanation: str,
    evidence: dict[str, Any],
) -> None:
    identity = {
        "indicator_type": indicator_type,
        "document_ids": sorted(str(value) for value in document_ids),
        "source_record_ids": sorted(source_record_ids),
        "evidence": evidence,
    }
    indicator_key = hashlib.sha256(_dump(identity).encode("utf-8")).hexdigest()
    if any(row["indicator_key"] == indicator_key for row in indicators):
        return
    indicators.append({
        "indicator_key": indicator_key,
        "indicator_type": indicator_type,
        "severity": severity,
        "document_ids": [str(value) for value in document_ids],
        "document_names": document_names,
        "source_record_type": source_record_type,
        "source_record_ids": source_record_ids,
        "explanation": explanation,
        "evidence": evidence,
        "human_review_required": True,
    })


def _exact_file_reuse_indicators(
    session: Session,
    lead_id: UUID,
    documents: list[DocumentRecord],
    indicators: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    provenance: list[dict[str, Any]] = []
    by_hash: dict[str, list[DocumentRecord]] = defaultdict(list)
    for document in documents:
        if document.file_hash:
            by_hash[document.file_hash].append(document)

    for digest, own_documents in sorted(by_hash.items()):
        all_matches = list(session.exec(
            select(DocumentRecord).where(DocumentRecord.file_hash == digest)
        ).all())
        foreign = [row for row in all_matches if row.lead_id and row.lead_id != lead_id]
        if foreign:
            matching_leads = sorted({str(row.lead_id) for row in foreign if row.lead_id})
            _add_indicator(
                indicators,
                indicator_type="exact_file_reuse_across_leads",
                severity="high",
                document_ids=[row.id for row in own_documents],
                document_names=[row.filename for row in own_documents],
                source_record_type="document_record",
                source_record_ids=[str(row.id) for row in [*own_documents, *foreign]],
                explanation=(
                    "The exact uploaded file bytes also appear on document records belonging to another lead. "
                    "This can have legitimate operational causes, but identity and provenance must be reviewed by a human."
                ),
                evidence={
                    "file_hash": digest,
                    "matching_other_lead_count": len(matching_leads),
                    "matching_other_document_ids": sorted(str(row.id) for row in foreign),
                    "other_lead_ids": matching_leads,
                },
            )
        own_types = sorted({row.document_type for row in own_documents})
        if len(own_types) > 1:
            _add_indicator(
                indicators,
                indicator_type="same_file_multiple_document_types",
                severity="warning",
                document_ids=[row.id for row in own_documents],
                document_names=[row.filename for row in own_documents],
                source_record_type="document_record",
                source_record_ids=[str(row.id) for row in own_documents],
                explanation=(
                    "Identical file bytes are classified as more than one document type for this lead. "
                    "A reviewer should confirm the intended evidence classification."
                ),
                evidence={"file_hash": digest, "document_types": own_types},
            )
        provenance.append({
            "file_hash": digest,
            "own_document_ids": sorted(str(row.id) for row in own_documents),
            "all_matching_document_ids": sorted(str(row.id) for row in all_matches),
        })
    return provenance


def _approved_consistency_indicators(
    assessments: list[DocumentConsistencyAssessment],
    documents_by_id: dict[UUID, DocumentRecord],
    indicators: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    provenance: list[dict[str, Any]] = []
    for assessment in assessments:
        if assessment.review_status != "approved":
            continue
        findings = _load(assessment.findings_json, [])
        mismatches = [finding for finding in findings if finding.get("outcome") == "mismatch"]
        if not mismatches:
            continue
        document = documents_by_id.get(assessment.document_id)
        for finding in mismatches:
            identity = finding.get("finding_key") == "identity_name_consistency"
            severity = "high" if identity or finding.get("severity") == "high" else "warning"
            _add_indicator(
                indicators,
                indicator_type="approved_identity_mismatch" if identity else "approved_material_fact_mismatch",
                severity=severity,
                document_ids=[assessment.document_id],
                document_names=[document.filename] if document else [],
                source_record_type="document_consistency_assessment",
                source_record_ids=[str(assessment.id)],
                explanation=(
                    "A human-approved consistency assessment recorded an identity mismatch between extracted document facts and the pinned source record."
                    if identity else
                    "A human-approved consistency assessment recorded a material mismatch between extracted document facts and the pinned source record."
                ),
                evidence={
                    "assessment_id": str(assessment.id),
                    "finding_key": finding.get("finding_key"),
                    "document_field": finding.get("document_field"),
                    "source_path": finding.get("source_path"),
                    "extracted_value": finding.get("extracted_value"),
                    "source_value": finding.get("source_value"),
                    "assessment_reviewed_by": assessment.reviewed_by,
                    "assessment_reviewed_at": assessment.reviewed_at,
                },
            )
        provenance.append({
            "assessment_id": str(assessment.id),
            "document_id": str(assessment.document_id),
            "review_status": assessment.review_status,
            "reviewed_by": assessment.reviewed_by,
            "finding_keys": sorted(str(item.get("finding_key")) for item in mismatches),
        })
    return provenance


def _approved_requirement_indicators(
    assessments: list[DocumentRequirementAssessment],
    documents_by_id: dict[UUID, DocumentRecord],
    indicators: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    provenance: list[dict[str, Any]] = []
    for assessment in assessments:
        if assessment.review_status != "approved":
            continue
        relevant = [
            finding for finding in _load(assessment.findings_json, [])
            if finding.get("outcome") in {"duplicate_conflict", "fact_inconsistency"}
        ]
        for finding in relevant:
            ids = [UUID(value) for value in finding.get("document_ids", [])]
            names = [documents_by_id[value].filename for value in ids if value in documents_by_id]
            outcome = str(finding.get("outcome"))
            _add_indicator(
                indicators,
                indicator_type="conflicting_duplicate_evidence" if outcome == "duplicate_conflict" else "approved_cross_document_inconsistency",
                severity="high" if outcome == "duplicate_conflict" else "warning",
                document_ids=ids,
                document_names=names,
                source_record_type="document_requirement_assessment",
                source_record_ids=[str(assessment.id)],
                explanation=(
                    "A human-approved requirement assessment identified conflicting duplicate evidence."
                    if outcome == "duplicate_conflict" else
                    "A human-approved requirement assessment identified a cross-document fact inconsistency."
                ),
                evidence={
                    "assessment_id": str(assessment.id),
                    "finding_key": finding.get("finding_key"),
                    "requirement_label": finding.get("requirement_label"),
                    "outcome": outcome,
                    "assessment_reviewed_by": assessment.reviewed_by,
                    "assessment_reviewed_at": assessment.reviewed_at,
                },
            )
        if relevant:
            provenance.append({
                "assessment_id": str(assessment.id),
                "review_status": assessment.review_status,
                "reviewed_by": assessment.reviewed_by,
                "finding_keys": sorted(str(item.get("finding_key")) for item in relevant),
            })
    return provenance


def _rejected_and_integrity_indicators(
    documents: list[DocumentRecord],
    jobs: list[DocumentExtractionJob],
    indicators: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    documents_by_id = {document.id: document for document in documents}
    provenance: list[dict[str, Any]] = []
    for document in documents:
        if document.status.lower() in REJECTED_DOCUMENT_STATES:
            _add_indicator(
                indicators,
                indicator_type="rejected_or_invalid_evidence",
                severity="warning",
                document_ids=[document.id],
                document_names=[document.filename],
                source_record_type="document_record",
                source_record_ids=[str(document.id)],
                explanation=(
                    "This evidence record is in a rejected or invalid state. The state alone does not prove fraud, "
                    "but it should be considered during document integrity review."
                ),
                evidence={"document_status": document.status, "verified_by": document.verified_by, "verified_at": document.verified_at},
            )
    for job in jobs:
        if job.status != "failed" or "hash does not match" not in str(job.error_message or "").lower():
            continue
        document = documents_by_id.get(job.document_id)
        _add_indicator(
            indicators,
            indicator_type="extraction_integrity_failure",
            severity="high",
            document_ids=[job.document_id],
            document_names=[document.filename] if document else [],
            source_record_type="document_extraction_job",
            source_record_ids=[str(job.id)],
            explanation=(
                "Server retrieval produced bytes that did not match the immutable upload hash. "
                "This is an integrity failure requiring storage and evidence provenance review."
            ),
            evidence={"job_id": str(job.id), "error_code": job.error_code, "error_message": job.error_message},
        )
    for job in jobs:
        provenance.append({
            "job_id": str(job.id),
            "document_id": str(job.document_id),
            "status": job.status,
            "error_code": job.error_code,
            "error_message": job.error_message if job.status == "failed" else None,
            "reviewed_by": job.reviewed_by,
            "reviewed_at": job.reviewed_at,
        })
    return provenance


def _approved_identifier_indicators(
    session: Session,
    lead_id: UUID,
    jobs: list[DocumentExtractionJob],
    documents_by_id: dict[UUID, DocumentRecord],
    indicators: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    approved_jobs = list(session.exec(
        select(DocumentExtractionJob).where(DocumentExtractionJob.status == "approved")
    ).all())
    job_documents = {
        document.id: document for document in session.exec(
            select(DocumentRecord).where(DocumentRecord.id.in_([job.document_id for job in approved_jobs]))
        ).all()
    } if approved_jobs else {}

    identifiers: dict[tuple[str, str], list[tuple[DocumentExtractionJob, DocumentRecord, Any]]] = defaultdict(list)
    for job in approved_jobs:
        document = job_documents.get(job.document_id)
        if document is None or document.lead_id is None:
            continue
        structured = _load(job.structured_data_json, {})
        for field in IDENTIFIER_FIELDS:
            value = structured.get(field)
            normalized = _normal(value)
            if normalized:
                identifiers[(field, hashlib.sha256(normalized.encode("utf-8")).hexdigest())].append((job, document, value))

    provenance: list[dict[str, Any]] = []
    current_job_ids = {job.id for job in jobs}
    for (field, digest), rows in sorted(identifiers.items()):
        current = [row for row in rows if row[0].id in current_job_ids]
        if not current:
            continue
        foreign = [row for row in rows if row[1].lead_id != lead_id]
        if not foreign:
            continue
        current_docs = [row[1] for row in current]
        _add_indicator(
            indicators,
            indicator_type="approved_identifier_reuse_across_leads",
            severity="high",
            document_ids=[row.id for row in current_docs],
            document_names=[row.filename for row in current_docs],
            source_record_type="document_extraction_job",
            source_record_ids=sorted(str(row[0].id) for row in rows),
            explanation=(
                "The same identifier from human-approved structured extractions appears on evidence linked to another lead. "
                "The raw identifier is masked; a specialist must determine whether the reuse is legitimate."
            ),
            evidence={
                "field": field,
                "identifier_hash": digest,
                "masked_identifier": _masked(current[0][2]),
                "matching_other_lead_count": len({str(row[1].lead_id) for row in foreign}),
                "matching_other_document_ids": sorted(str(row[1].id) for row in foreign),
            },
        )
        provenance.append({
            "field": field,
            "identifier_hash": digest,
            "masked_identifier": _masked(current[0][2]),
            "job_ids": sorted(str(row[0].id) for row in rows),
            "document_ids": sorted(str(row[1].id) for row in rows),
        })
    return provenance


def assessment_read(assessment: DocumentFraudRiskAssessment) -> dict[str, Any]:
    return {
        **assessment.model_dump(exclude={"indicators_json", "source_snapshot_json"}),
        "indicators": _load(assessment.indicators_json, []),
        "source_snapshot": _load(assessment.source_snapshot_json, {}),
        "fraud_determined": False,
        "documents_rejected": 0,
        "eligibility_changed": False,
        "external_actions_triggered": 0,
    }


def generate_document_fraud_risk_assessment(
    session: Session,
    lead_id: UUID,
    *,
    actor: str = "system",
) -> tuple[DocumentFraudRiskAssessment, bool]:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    profile = current_mobility_profile(session, lead_id)
    if profile and profile.consent_status == "withdrawn":
        raise ValueError("Current profile consent is withdrawn")

    documents = list(session.exec(
        select(DocumentRecord).where(DocumentRecord.lead_id == lead_id)
    ).all())
    if not documents:
        raise ValueError("No documents are available for integrity-risk assessment")
    jobs = list(session.exec(
        select(DocumentExtractionJob).where(DocumentExtractionJob.lead_id == lead_id)
    ).all())
    consistency = list(session.exec(
        select(DocumentConsistencyAssessment).where(DocumentConsistencyAssessment.lead_id == lead_id)
    ).all())
    requirement_assessments = list(session.exec(
        select(DocumentRequirementAssessment).where(DocumentRequirementAssessment.lead_id == lead_id)
    ).all())
    application = _latest_application(session, lead_id)
    documents_by_id = {document.id: document for document in documents}
    indicators: list[dict[str, Any]] = []

    source_snapshot = {
        "lead": {"id": str(lead.id), "full_name": lead.full_name, "intent": str(getattr(lead.intent, "value", lead.intent))},
        "profile": {
            "id": str(profile.id),
            "profile_version": profile.profile_version,
            "consent_status": profile.consent_status,
        } if profile else None,
        "application": application.model_dump(mode="json") if application else None,
        "documents": _document_snapshot(documents),
        "exact_file_reuse": _exact_file_reuse_indicators(session, lead_id, documents, indicators),
        "approved_consistency_assessments": _approved_consistency_indicators(consistency, documents_by_id, indicators),
        "approved_requirement_assessments": _approved_requirement_indicators(requirement_assessments, documents_by_id, indicators),
        "extraction_jobs": _rejected_and_integrity_indicators(documents, jobs, indicators),
        "approved_identifiers": _approved_identifier_indicators(session, lead_id, jobs, documents_by_id, indicators),
    }
    indicators.sort(key=lambda row: (0 if row["severity"] == "high" else 1, row["indicator_type"], row["indicator_key"]))
    key_payload = {
        "lead_id": str(lead_id),
        "profile_id": str(profile.id) if profile else None,
        "profile_version": profile.profile_version if profile else None,
        "application_id": str(application.id) if application else None,
        "indicators": indicators,
        "source_snapshot": source_snapshot,
    }
    assessment_key = hashlib.sha256(_dump(key_payload).encode("utf-8")).hexdigest()
    existing = session.exec(
        select(DocumentFraudRiskAssessment).where(DocumentFraudRiskAssessment.assessment_key == assessment_key)
    ).first()
    if existing:
        return existing, False

    high_count = sum(1 for row in indicators if row["severity"] == "high")
    warning_count = sum(1 for row in indicators if row["severity"] == "warning")
    risk_band = "high" if high_count else "review" if warning_count else "none"
    result_status = "high_priority_review" if high_count else "indicators_found" if warning_count else "no_indicators"
    review_required = bool(indicators)
    summary = (
        f"Generated {len(indicators)} explainable document integrity indicator(s): {high_count} high and {warning_count} warning. "
        "These are triage signals only. The system did not determine fraud, reject evidence, change eligibility, or initiate any external action."
    )
    now = now_utc()
    assessment = DocumentFraudRiskAssessment(
        assessment_key=assessment_key,
        lead_id=lead_id,
        profile_id=profile.id if profile else None,
        profile_version=profile.profile_version if profile else None,
        application_id=application.id if application else None,
        result_status=result_status,
        review_status="pending" if review_required else "not_required",
        risk_band=risk_band,
        indicator_count=len(indicators),
        high_indicator_count=high_count,
        warning_indicator_count=warning_count,
        indicators_json=_dump(indicators),
        source_snapshot_json=_dump(source_snapshot),
        summary=summary,
        human_review_required=review_required,
        automated_fraud_determination=False,
        adverse_action_taken=False,
        generated_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(assessment)
    session.flush()
    record_audit(
        session,
        action="document_fraud_risk_assessed",
        entity_type="document_fraud_risk_assessment",
        entity_id=assessment.id,
        after_state={
            "lead_id": lead_id,
            "result_status": result_status,
            "risk_band": risk_band,
            "indicator_count": len(indicators),
            "high_indicator_count": high_count,
            "warning_indicator_count": warning_count,
            "automated_fraud_determination": False,
            "adverse_action_taken": False,
            "documents_rejected": 0,
            "eligibility_changed": False,
            "external_actions_triggered": 0,
        },
        reason="Generated immutable, explainable document integrity-risk indicators",
        actor=actor,
        source="document_fraud_risk_indicators_v9_4",
    )
    session.commit()
    session.refresh(assessment)
    return assessment, True


def scan_document_fraud_risk_assessments(
    session: Session,
    *,
    lead_id: UUID | None = None,
    actor: str = "document-integrity-monitor",
) -> dict[str, Any]:
    if lead_id:
        lead = session.get(Lead, lead_id)
        if lead is None:
            raise ValueError("Lead not found")
        leads = [lead]
    else:
        leads = list(session.exec(select(Lead).order_by(Lead.created_at)).all())

    created = 0
    existing = 0
    skipped = 0
    assessment_ids: list[str] = []
    for lead in leads:
        try:
            assessment, was_created = generate_document_fraud_risk_assessment(session, lead.id, actor=actor)
        except ValueError as exc:
            if "consent is withdrawn" in str(exc).lower() or "no documents" in str(exc).lower():
                skipped += 1
                continue
            raise
        assessment_ids.append(str(assessment.id))
        created += int(was_created)
        existing += int(not was_created)

    record_audit(
        session,
        action="document_fraud_risk_scan_completed",
        entity_type="document_integrity_monitor",
        entity_id=lead_id or "global",
        after_state={
            "lead_id": lead_id,
            "leads_scanned": len(leads),
            "created": created,
            "existing": existing,
            "skipped": skipped,
            "fraud_determinations": 0,
            "documents_rejected": 0,
            "eligibility_changed": False,
            "external_actions_triggered": 0,
        },
        reason="Completed deterministic document integrity-risk scan",
        actor=actor,
        source="document_fraud_risk_indicators_v9_4",
    )
    session.commit()
    return {
        "lead_id": lead_id,
        "leads_scanned": len(leads),
        "created": created,
        "existing": existing,
        "skipped": skipped,
        "assessment_ids": assessment_ids,
        "fraud_determinations": 0,
        "documents_rejected": 0,
        "eligibility_changed": False,
        "external_actions_triggered": 0,
    }


def review_document_fraud_risk_assessment(
    session: Session,
    assessment_id: UUID,
    *,
    decision: str,
    notes: str,
    actor: str,
) -> DocumentFraudRiskAssessment:
    if decision not in REVIEW_DECISIONS:
        raise ValueError("Unsupported document integrity-risk review decision")
    assessment = session.get(DocumentFraudRiskAssessment, assessment_id)
    if assessment is None:
        raise ValueError("Document integrity-risk assessment not found")
    if assessment.review_status != "pending":
        raise ValueError("Only a pending document integrity-risk assessment can be reviewed")
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
    assessment.automated_fraud_determination = False
    assessment.adverse_action_taken = False
    session.add(assessment)
    record_audit(
        session,
        action=f"document_fraud_risk_{decision}",
        entity_type="document_fraud_risk_assessment",
        entity_id=assessment.id,
        before_state=before,
        after_state={
            "review_status": decision,
            "reviewed_by": actor,
            "automated_fraud_determination": False,
            "adverse_action_taken": False,
            "documents_rejected": 0,
            "eligibility_changed": False,
            "external_actions_triggered": 0,
        },
        reason=cleaned_notes,
        actor=actor,
        source="document_fraud_risk_indicators_v9_4",
    )
    session.commit()
    session.refresh(assessment)
    return assessment

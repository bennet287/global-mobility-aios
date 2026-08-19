from __future__ import annotations

import hashlib
import json
import re
from io import BytesIO
from typing import Any
from uuid import UUID

from pypdf import PdfReader
from sqlmodel import Session, select

from app.models.domain import (
    DocumentExtractionJob,
    DocumentRecord,
    DocumentSchemaDefinition,
    now_utc,
)
from app.schemas import DocumentExtractionJobRead, DocumentSchemaDefinitionRead
from app.services.audit_log import record_audit
from app.services.document_storage import document_storage_client
from app.services.docling_adapter import STATUS_SUCCESS, normalize_document_bytes
from app.services.mobility_profiles import current_mobility_profile


DOCUMENT_TYPE_ALIASES = {
    "resume": "cv",
    "resume_cv": "cv",
    "curriculum_vitae": "cv",
    "highest_degree_certificate": "degree_certificate",
    "degree": "degree_certificate",
    "certificate": "degree_certificate",
    "academic_transcripts": "academic_transcript",
    "transcript": "academic_transcript",
    "work_experience_letters": "employment_letter",
    "employment_evidence": "employment_letter",
    "job_offer": "employment_letter",
    "employment_contract": "employment_letter",
    "job_offer_or_employment_contract": "employment_letter",
    "financial_proof": "bank_statement",
    "proof_of_funds": "bank_statement",
}


def _field(field_type: str, patterns: list[str], *, required: bool = False) -> dict[str, Any]:
    return {"type": field_type, "patterns": patterns, "required": required}


BUILTIN_SCHEMAS: dict[str, dict[str, Any]] = {
    "passport": {
        "schema_key": "passport_identity_v1",
        "fields": {
            "full_name": _field("string", [r"(?:Full\s+Name|Name)\s*[:\n]\s*([A-Za-z][A-Za-z .'-]{2,80})"], required=True),
            "nationality": _field("string", [r"(?:Nationality|Citizenship)\s*[:\n]\s*([A-Za-z][A-Za-z .'-]{2,50})"]),
            "document_number": _field("string", [r"(?:Passport|Document)\s*(?:No\.?|Number)\s*[:\n]\s*([A-Z0-9]{5,20})"], required=True),
            "date_of_birth": _field("date_string", [r"(?:Date of Birth|DOB)\s*[:\n]\s*([0-9]{1,4}[/.-][0-9]{1,2}[/.-][0-9]{1,4})"]),
            "expiry_date": _field("date_string", [r"(?:Date of Expiry|Expiry Date|Expires)\s*[:\n]\s*([0-9]{1,4}[/.-][0-9]{1,2}[/.-][0-9]{1,4})"], required=True),
        },
    },
    "cv": {
        "schema_key": "cv_profile_v1",
        "fields": {
            "full_name": _field("string", [r"(?:Full\s+Name|Name)\s*[:\n]\s*([A-Za-z][A-Za-z .'-]{2,80})"]),
            "profession": _field("string", [r"(?:Profession|Occupation|Job Title)\s*[:\n]\s*([A-Za-z][A-Za-z /&+.-]{2,100})"]),
            "years_experience": _field("number", [r"([0-9]{1,2}(?:\.[0-9])?)\+?\s*years?\s+(?:of\s+)?experience"]),
            "email": _field("string", [r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})"]),
        },
    },
    "degree_certificate": {
        "schema_key": "degree_certificate_v1",
        "fields": {
            "holder_name": _field("string", [r"(?:awarded to|Name)\s*[:\n]?\s*([A-Za-z][A-Za-z .'-]{2,80})"], required=True),
            "qualification": _field("string", [r"(?:Degree|Qualification|Award)\s*[:\n]\s*([A-Za-z][A-Za-z /&().'-]{2,120})"], required=True),
            "institution": _field("string", [r"(?:University|Institution)\s*[:\n]\s*([A-Za-z][A-Za-z /&().'-]{2,120})"]),
            "graduation_year": _field("integer", [r"(?:Graduation Year|Year Awarded)\s*[:\n]\s*((?:19|20)[0-9]{2})"]),
        },
    },
    "academic_transcript": {
        "schema_key": "academic_transcript_v1",
        "fields": {
            "student_name": _field("string", [r"(?:Student Name|Name)\s*[:\n]\s*([A-Za-z][A-Za-z .'-]{2,80})"], required=True),
            "institution": _field("string", [r"(?:University|Institution)\s*[:\n]\s*([A-Za-z][A-Za-z /&().'-]{2,120})"]),
            "programme": _field("string", [r"(?:Programme|Program|Course)\s*[:\n]\s*([A-Za-z][A-Za-z /&().'-]{2,120})"]),
            "final_grade": _field("string", [r"(?:Final Grade|GPA|Result)\s*[:\n]\s*([A-Z0-9.+/% -]{1,30})"]),
        },
    },
    "employment_letter": {
        "schema_key": "employment_letter_v1",
        "fields": {
            "employee_name": _field("string", [r"(?:Employee Name|Name)\s*[:\n]\s*([A-Za-z][A-Za-z .'-]{2,80})"], required=True),
            "employer": _field("string", [r"(?:Employer|Company)\s*[:\n]\s*([A-Za-z0-9][A-Za-z0-9 /&().'-]{2,120})"]),
            "job_title": _field("string", [r"(?:Job Title|Position|Role)\s*[:\n]\s*([A-Za-z][A-Za-z /&+.-]{2,100})"], required=True),
            "start_date": _field("date_string", [r"(?:Start Date|Employed From)\s*[:\n]\s*([0-9]{1,4}[/.-][0-9]{1,2}[/.-][0-9]{1,4})"]),
        },
    },
    "bank_statement": {
        "schema_key": "bank_statement_v1",
        "fields": {
            "account_holder": _field("string", [r"(?:Account Holder|Customer Name|Name)\s*[:\n]\s*([A-Za-z][A-Za-z .'-]{2,80})"], required=True),
            "statement_date": _field("date_string", [r"(?:Statement Date|As of)\s*[:\n]\s*([0-9]{1,4}[/.-][0-9]{1,2}[/.-][0-9]{1,4})"]),
            "closing_balance": _field("number", [r"(?:Closing Balance|Available Balance)\s*[:\n]\s*(?:[A-Z]{3}|[$€£])?\s*([0-9,]+(?:\.[0-9]{1,2})?)"], required=True),
            "currency": _field("string", [r"(?:Currency)\s*[:\n]\s*([A-Z]{3})"]),
        },
    },
}


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def canonical_document_type(document_type: str) -> str:
    normalized = document_type.strip().lower().replace(" ", "_").replace("-", "_")
    return DOCUMENT_TYPE_ALIASES.get(normalized, normalized)


def ensure_builtin_schemas(session: Session, *, actor: str = "system") -> list[DocumentSchemaDefinition]:
    rows: list[DocumentSchemaDefinition] = []
    created = 0
    for document_type, definition in BUILTIN_SCHEMAS.items():
        schema_key = definition["schema_key"]
        row = session.exec(
            select(DocumentSchemaDefinition)
            .where(DocumentSchemaDefinition.schema_key == schema_key)
            .where(DocumentSchemaDefinition.version_number == 1)
        ).first()
        if row is None:
            fields = definition["fields"]
            properties = {name: {"type": "number" if rule["type"] == "number" else "integer" if rule["type"] == "integer" else "string"} for name, rule in fields.items()}
            required = [name for name, rule in fields.items() if rule.get("required")]
            now = now_utc()
            row = DocumentSchemaDefinition(
                schema_key=schema_key,
                document_type=document_type,
                version_number=1,
                lifecycle_status="published",
                json_schema_json=_dump({
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "additionalProperties": False,
                    "properties": properties,
                    "required": required,
                }),
                extraction_rules_json=_dump({"fields": fields}),
                approved_by="platform-baseline",
                review_notes="Built-in deterministic extraction schema; extracted values still require human review.",
                published_at=now,
                created_by=actor,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()
            created += 1
        rows.append(row)
    if created:
        record_audit(
            session,
            action="document_schemas_seeded",
            entity_type="document_schema_definition",
            after_state={"created": created, "schema_keys": [row.schema_key for row in rows]},
            reason="Installed versioned built-in document extraction schemas",
            actor=actor,
            source="document_intelligence_v9_0",
        )
    session.commit()
    for row in rows:
        session.refresh(row)
    return rows


def schema_read(schema: DocumentSchemaDefinition) -> DocumentSchemaDefinitionRead:
    return DocumentSchemaDefinitionRead(
        **schema.model_dump(exclude={"json_schema_json", "extraction_rules_json"}),
        json_schema=_load(schema.json_schema_json, {}),
        extraction_rules=_load(schema.extraction_rules_json, {}),
    )


def job_read(session: Session, job: DocumentExtractionJob) -> DocumentExtractionJobRead:
    schema = session.get(DocumentSchemaDefinition, job.schema_definition_id)
    return DocumentExtractionJobRead(
        **job.model_dump(exclude={"structured_data_json", "field_confidence_json", "warnings_json"}),
        schema_key=schema.schema_key if schema else "missing_schema",
        document_type=schema.document_type if schema else "unknown",
        structured_data=_load(job.structured_data_json, {}),
        field_confidence=_load(job.field_confidence_json, {}),
        warnings=_load(job.warnings_json, []),
    )


def create_extraction_job(
    session: Session,
    document_id: UUID,
    *,
    language: str,
    actor: str,
) -> DocumentExtractionJob:
    document = session.get(DocumentRecord, document_id)
    if document is None:
        raise ValueError("Document not found")
    if not document.storage_key or document.storage_provider not in {"local", "minio"}:
        raise ValueError("Document has no server-readable stored file")
    if document.lead_id:
        profile = current_mobility_profile(session, document.lead_id)
        if profile and profile.consent_status == "withdrawn":
            raise ValueError("Current profile consent is withdrawn")
    active = session.exec(
        select(DocumentExtractionJob)
        .where(DocumentExtractionJob.document_id == document_id)
        .where(DocumentExtractionJob.status.in_(["queued", "processing"]))
    ).first()
    if active:
        return active
    schemas = ensure_builtin_schemas(session, actor=actor)
    canonical = canonical_document_type(document.document_type)
    schema = next((row for row in schemas if row.document_type == canonical), None)
    if schema is None:
        raise ValueError(f"No published extraction schema supports document type '{document.document_type}'")
    now = now_utc()
    job = DocumentExtractionJob(
        document_id=document.id,
        lead_id=document.lead_id,
        schema_definition_id=schema.id,
        schema_version=schema.version_number,
        language=language,
        input_file_hash=document.file_hash,
        requested_by=actor,
        queued_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.flush()
    record_audit(
        session,
        action="document_extraction_queued",
        entity_type="document_extraction_job",
        entity_id=job.id,
        after_state={
            "document_id": str(document.id),
            "schema_id": str(schema.id),
            "schema_version": schema.version_number,
            "input_file_hash": document.file_hash,
        },
        reason="Queued server-side document extraction",
        actor=actor,
        source="document_intelligence_v9_0",
    )
    session.commit()
    session.refresh(job)
    return job


def _extract_text(content: bytes, *, mime_type: str | None, filename: str, language: str) -> tuple[str, list[str]]:
    mime = (mime_type or "").lower()
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    warnings: list[str] = []

    # Optional Docling normalization (Technology Radar V1.1 Wave 2 pilot).
    # When enabled and successful, its markdown output becomes the extraction text.
    # When disabled, unavailable, or empty, the pipeline falls back to the
    # existing extractors below.
    docling_result = normalize_document_bytes(content, mime_type=mime_type, filename=filename)
    if docling_result.status == STATUS_SUCCESS:
        normalized = docling_result.normalized_text.strip()
        if normalized:
            warnings.append("Document normalized with Docling; structured extraction still requires human review.")
            warnings.extend(docling_result.warnings)
            return normalized, warnings

    if mime.startswith("text/") or suffix in {"txt", "csv", "md"}:
        return content.decode("utf-8", errors="replace").strip(), warnings
    if mime == "application/pdf" or suffix == "pdf":
        reader = PdfReader(BytesIO(content))
        text = "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
        if not text:
            raise ValueError("PDF contains no embedded text; scanned-PDF OCR is not yet available")
        warnings.append("PDF text layer extracted; visual layout was not interpreted.")
        return text, warnings
    if mime.startswith("image/") or suffix in {"png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp"}:
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("Server OCR dependencies are unavailable") from exc
        text = pytesseract.image_to_string(Image.open(BytesIO(content)), lang=language).strip()
        if not text:
            raise ValueError("OCR produced no usable text")
        warnings.append("Image OCR output may contain recognition errors and requires human review.")
        return text, warnings
    raise ValueError(f"Unsupported document format: {mime_type or suffix or 'unknown'}")


def _convert(value: str, field_type: str) -> Any:
    value = " ".join(value.strip().split())
    if field_type == "number":
        return float(value.replace(",", ""))
    if field_type == "integer":
        return int(value.replace(",", ""))
    return value


def _parse_structured(text: str, schema: DocumentSchemaDefinition) -> tuple[dict[str, Any], dict[str, float], list[str]]:
    rules = _load(schema.extraction_rules_json, {}).get("fields", {})
    data: dict[str, Any] = {}
    confidence: dict[str, float] = {}
    warnings: list[str] = []
    for field_name, rule in rules.items():
        value = None
        for pattern in rule.get("patterns", []):
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = _convert(match.group(1), rule.get("type", "string"))
                break
        if value is not None:
            data[field_name] = value
            confidence[field_name] = 0.8
        elif rule.get("required"):
            warnings.append(f"Required field '{field_name}' was not extracted.")
    return data, confidence, warnings


def execute_extraction_job(session: Session, job_id: UUID) -> DocumentExtractionJob:
    job = session.get(DocumentExtractionJob, job_id)
    if job is None:
        raise ValueError("Document extraction job not found")
    if job.status not in {"queued", "processing"}:
        return job
    document = session.get(DocumentRecord, job.document_id)
    schema = session.get(DocumentSchemaDefinition, job.schema_definition_id)
    if document is None or schema is None:
        raise ValueError("Extraction job provenance is incomplete")
    now = now_utc()
    job.status = "processing"
    job.started_at = job.started_at or now
    job.attempt_count += 1
    job.updated_at = now
    session.add(job)
    session.commit()
    try:
        content = document_storage_client().get_document(document.storage_key or "")
        digest = hashlib.sha256(content).hexdigest()
        if document.file_hash and digest != document.file_hash:
            raise ValueError("Stored document hash does not match upload provenance")
        text, extraction_warnings = _extract_text(
            content,
            mime_type=document.mime_type,
            filename=document.filename,
            language=job.language,
        )
        data, confidence, parsing_warnings = _parse_structured(text, schema)
        completed = now_utc()
        job.extracted_text = text[:1_000_000]
        job.structured_data_json = _dump(data)
        job.field_confidence_json = _dump(confidence)
        job.warnings_json = _dump([*extraction_warnings, *parsing_warnings])
        job.status = "needs_review"
        job.completed_at = completed
        job.updated_at = completed
        job.error_code = None
        job.error_message = None
        record_audit(
            session,
            action="document_extraction_completed",
            entity_type="document_extraction_job",
            entity_id=job.id,
            after_state={
                "status": job.status,
                "document_id": str(document.id),
                "schema_version": job.schema_version,
                "field_names": sorted(data),
                "warning_count": len(extraction_warnings) + len(parsing_warnings),
            },
            reason="Server-side extraction completed and awaits human review",
            actor="document-worker",
            source="document_intelligence_v9_0",
        )
    except Exception as exc:
        completed = now_utc()
        job.status = "failed"
        job.error_code = "extraction_failed"
        job.error_message = str(exc)[:2000]
        job.completed_at = completed
        job.updated_at = completed
        record_audit(
            session,
            action="document_extraction_failed",
            entity_type="document_extraction_job",
            entity_id=job.id,
            after_state={"status": "failed", "error_code": job.error_code},
            reason=job.error_message,
            actor="document-worker",
            source="document_intelligence_v9_0",
        )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def review_extraction_job(
    session: Session,
    job_id: UUID,
    *,
    decision: str,
    notes: str,
    actor: str,
) -> DocumentExtractionJob:
    job = session.get(DocumentExtractionJob, job_id)
    if job is None:
        raise ValueError("Document extraction job not found")
    if job.status != "needs_review":
        raise ValueError("Only an extraction awaiting review can be decided")
    document = session.get(DocumentRecord, job.document_id)
    if document is None:
        raise ValueError("Document not found")
    now = now_utc()
    job.status = decision
    job.reviewed_by = actor
    job.review_notes = notes
    job.reviewed_at = now
    job.updated_at = now
    if decision == "approved":
        metadata = _load(document.extracted_metadata_json, {})
        metadata["document_intelligence"] = {
            "approved_extraction_job_id": str(job.id),
            "schema_definition_id": str(job.schema_definition_id),
            "schema_version": job.schema_version,
            "structured_data": _load(job.structured_data_json, {}),
            "reviewed_by": actor,
            "reviewed_at": now.isoformat(),
            "verification_boundary": "Extraction approval does not verify document authenticity.",
        }
        document.extracted_metadata_json = _dump(metadata)
        document.updated_at = now
        session.add(document)
    record_audit(
        session,
        action=f"document_extraction_{decision}",
        entity_type="document_extraction_job",
        entity_id=job.id,
        after_state={"status": decision, "reviewed_by": actor, "document_status": document.status},
        reason=notes,
        actor=actor,
        source="document_intelligence_v9_0",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job

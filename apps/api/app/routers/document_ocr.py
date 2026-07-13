from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import DocumentRecord, Lead
from app.schemas import DocumentOcrExtractRequest, DocumentOcrExtractResponse
from app.services.audit_log import record_audit

router = APIRouter(tags=["document-ocr"])


def _extract_field(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _parse_fields(text: str, document_type: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    # Common labels
    name = (
        _extract_field(text, [r"Name[:\s]+([A-Za-z\s\.]+)", r"Full Name[:\s]+([A-Za-z\s\.]+)"])
        or _extract_field(text, [r"\bName\b\s*\n?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)"])
    )
    if name:
        fields["full_name"] = name

    nationality = _extract_field(
        text,
        [
            r"Nationality[:\s]+([A-Za-z\s\.]+)",
            r"Citizenship[:\s]+([A-Za-z\s\.]+)",
            r"Country of Birth[:\s]+([A-Za-z\s\.]+)",
        ],
    )
    if nationality:
        fields["nationality"] = nationality

    profession = _extract_field(
        text,
        [
            r"Profession[:\s]+([A-Za-z\s\.]+)",
            r"Occupation[:\s]+([A-Za-z\s\.]+)",
            r"Job Title[:\s]+([A-Za-z\s\.]+)",
        ],
    )
    if profession:
        fields["profession"] = profession

    # Passport number / document number
    doc_number = _extract_field(text, [r"Passport No\.?[:\s]+([A-Z0-9]+)", r"Document No\.?[:\s]+([A-Z0-9]+)"])
    if doc_number:
        fields["document_number"] = doc_number

    # Date of birth
    dob = _extract_field(text, [r"Date of Birth[:\s]+([0-9]{1,2}[/.\-][0-9]{1,2}[/.\-][0-9]{2,4})"])
    if dob:
        fields["date_of_birth"] = dob

    if document_type == "cv":
        # Look for years of experience phrase
        exp_match = re.search(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", text, re.IGNORECASE)
        if exp_match:
            fields["years_experience"] = float(exp_match.group(1))

    return fields


@router.post("/api/v1/documents/ocr-extract", response_model=DocumentOcrExtractResponse)
def ocr_extract(payload: DocumentOcrExtractRequest, session: Session = Depends(get_session)) -> DocumentOcrExtractResponse:
    lead = session.get(Lead, payload.lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    parsed_fields = _parse_fields(payload.extracted_text, payload.document_type)

    # Heuristic: fill lead fields if currently empty
    updated = False
    if parsed_fields.get("full_name") and not lead.full_name:
        lead.full_name = parsed_fields["full_name"]
        updated = True
    if parsed_fields.get("profession") and "profession" not in (lead.notes or "").lower():
        lead.notes = f"{lead.notes or ''}\nProfession (from OCR): {parsed_fields['profession']}".strip()
        updated = True
    if updated:
        session.add(lead)

    metadata = {
        "ocr": {
            "language": payload.language,
            "confidence": payload.confidence,
            "parsed_fields": parsed_fields,
        }
    }
    document = DocumentRecord(
        lead_id=payload.lead_id,
        document_type=payload.document_type,
        filename=payload.filename,
        storage_provider="ocr_client",
        storage_key=None,
        mime_type="application/ocr-text",
        status="extracted",
        extracted_metadata_json=json.dumps(metadata, default=str, sort_keys=True),
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    record_audit(
        session,
        actor="system",
        action="document_ocr_extract",
        entity_type="document",
        entity_id=str(document.id),
        after_state={
            "lead_id": str(lead.id),
            "document_type": payload.document_type,
            "parsed_fields": parsed_fields,
            "confidence": payload.confidence,
        },
        reason="OCR text extracted from client-uploaded image.",
        source="document_ocr_v7.3",
    )

    return DocumentOcrExtractResponse(
        document_id=document.id,
        document_type=payload.document_type,
        extracted_text=payload.extracted_text,
        parsed_fields=parsed_fields,
        message="Document text extracted and stored. Review parsed fields before relying on them.",
    )

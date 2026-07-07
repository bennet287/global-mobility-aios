from typing import Optional
from uuid import UUID
from sqlmodel import Session

from app.models.domain import DocumentRecord
from app.schemas import DocumentCreate


class DocumentService:
    def create_record(self, session: Session, payload: DocumentCreate) -> DocumentRecord:
        record = DocumentRecord(
            lead_id=payload.lead_id,
            document_type=payload.document_type,
            filename=payload.filename,
            storage_key=payload.storage_key,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def completeness_check(self, lead_id: Optional[UUID]) -> dict:
        # Placeholder policy. Replace with country/program-specific checklists.
        required = ["passport", "cv", "transcript", "degree_certificate", "financial_proof"]
        return {
            "lead_id": str(lead_id) if lead_id else None,
            "required_documents": required,
            "status": "policy_template_only",
            "next_step": "Load country/program-specific document rules from official sources.",
        }

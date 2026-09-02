from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import DocumentRecord
from app.schemas import DocumentCreate, DocumentRead
from app.services.document_service import DocumentService
from app.services.document_storage import public_document_metadata

router = APIRouter()


@router.post("/documents", response_model=DocumentRead)
def create_document(payload: DocumentCreate, session: Session = Depends(get_session)) -> dict:
    return public_document_metadata(DocumentService().create_record(session, payload))


@router.get("/documents", response_model=List[DocumentRead])
def list_documents(lead_id: Optional[UUID] = None, session: Session = Depends(get_session)) -> list[dict]:
    query = select(DocumentRecord)
    if lead_id:
        query = query.where(DocumentRecord.lead_id == lead_id)
    return [public_document_metadata(row) for row in session.exec(query.order_by(DocumentRecord.created_at.desc())).all()]


@router.get("/documents/checklist")
def document_checklist(lead_id: Optional[UUID] = None) -> dict:
    return DocumentService().completeness_check(lead_id)

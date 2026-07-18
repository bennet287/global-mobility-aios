from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import DocumentRecord
from app.schemas import DocumentCreate, DocumentRead
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/documents", response_model=DocumentRead)
def create_document(payload: DocumentCreate, session: Session = Depends(get_session)) -> DocumentRecord:
    return DocumentService().create_record(session, payload)


@router.get("/documents", response_model=List[DocumentRead])
def list_documents(lead_id: Optional[UUID] = None, session: Session = Depends(get_session)) -> list[DocumentRecord]:
    query = select(DocumentRecord)
    if lead_id:
        query = query.where(DocumentRecord.lead_id == lead_id)
    return list(session.exec(query.order_by(DocumentRecord.created_at.desc())).all())


@router.get("/documents/checklist")
def document_checklist(lead_id: Optional[UUID] = None) -> dict:
    return DocumentService().completeness_check(lead_id)

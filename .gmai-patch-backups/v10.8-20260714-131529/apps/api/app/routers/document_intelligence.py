from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    DocumentConsistencyAssessment,
    DocumentExpiryReminderTask,
    DocumentExtractionJob,
    DocumentSchemaDefinition,
)
from app.schemas import (
    DocumentConsistencyAssessmentRead,
    DocumentConsistencyGenerateRequest,
    DocumentConsistencyReviewRequest,
    DocumentExpiryReminderRead,
    DocumentExpiryReminderReviewRequest,
    DocumentExpiryScanRequest,
    DocumentExpiryScanResult,
    DocumentExtractionJobRead,
    DocumentExtractionRequest,
    DocumentExtractionReviewRequest,
    DocumentSchemaDefinitionRead,
)
from app.services.document_consistency import (
    assessment_read,
    generate_consistency_assessment,
    review_consistency_assessment,
)
from app.services.document_expiry_reminders import (
    reminder_read,
    review_document_expiry_reminder,
    scan_document_expiry_reminders,
)
from app.services.document_intelligence import (
    create_extraction_job,
    ensure_builtin_schemas,
    job_read,
    review_extraction_job,
    schema_read,
)
from app.tasks.document_extraction_tasks import run_document_extraction_task

router = APIRouter(prefix="/api/v1/document-intelligence", tags=["document-intelligence-v9.0"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return getattr(context, "username", "api-operator")


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    return HTTPException(status_code=404 if "not found" in message.lower() else 400, detail=message)


@router.post("/schemas/seed", response_model=list[DocumentSchemaDefinitionRead])
def api_seed_schemas(
    request: Request,
    session: Session = Depends(get_session),
) -> list[DocumentSchemaDefinitionRead]:
    return [schema_read(row) for row in ensure_builtin_schemas(session, actor=_actor(request))]


@router.get("/schemas", response_model=list[DocumentSchemaDefinitionRead])
def api_list_schemas(session: Session = Depends(get_session)) -> list[DocumentSchemaDefinitionRead]:
    rows = session.exec(
        select(DocumentSchemaDefinition)
        .order_by(DocumentSchemaDefinition.document_type, DocumentSchemaDefinition.version_number.desc())
    ).all()
    return [schema_read(row) for row in rows]


@router.post("/documents/{document_id}/extract", response_model=DocumentExtractionJobRead, status_code=202)
def api_queue_extraction(
    document_id: UUID,
    payload: DocumentExtractionRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentExtractionJobRead:
    try:
        job = create_extraction_job(
            session,
            document_id,
            language=payload.language,
            actor=_actor(request),
        )
        if not job.task_id and job.status == "queued":
            task = run_document_extraction_task.delay(str(job.id))
            job.task_id = task.id
            session.add(job)
            session.commit()
            session.refresh(job)
        return job_read(session, job)
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/extractions", response_model=list[DocumentExtractionJobRead])
def api_list_extractions(
    lead_id: UUID | None = None,
    document_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[DocumentExtractionJobRead]:
    statement = select(DocumentExtractionJob).order_by(DocumentExtractionJob.created_at.desc())
    if lead_id:
        statement = statement.where(DocumentExtractionJob.lead_id == lead_id)
    if document_id:
        statement = statement.where(DocumentExtractionJob.document_id == document_id)
    if status:
        statement = statement.where(DocumentExtractionJob.status == status)
    rows = session.exec(statement.limit(max(1, min(limit, 500)))).all()
    return [job_read(session, row) for row in rows]


@router.get("/extractions/{job_id}", response_model=DocumentExtractionJobRead)
def api_get_extraction(
    job_id: UUID,
    session: Session = Depends(get_session),
) -> DocumentExtractionJobRead:
    job = session.get(DocumentExtractionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Document extraction job not found")
    return job_read(session, job)


@router.post("/extractions/{job_id}/review", response_model=DocumentExtractionJobRead)
def api_review_extraction(
    job_id: UUID,
    payload: DocumentExtractionReviewRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentExtractionJobRead:
    try:
        job = review_extraction_job(
            session,
            job_id,
            decision=payload.decision,
            notes=payload.notes,
            actor=_actor(request),
        )
        return job_read(session, job)
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.post("/extractions/{job_id}/validate", response_model=DocumentConsistencyAssessmentRead, status_code=201)
def api_validate_extraction(
    job_id: UUID,
    payload: DocumentConsistencyGenerateRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentConsistencyAssessmentRead:
    try:
        return generate_consistency_assessment(
            session,
            job_id,
            application_id=payload.application_id,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


@router.get("/validations", response_model=list[DocumentConsistencyAssessmentRead])
def api_list_validations(
    lead_id: UUID | None = None,
    review_status: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[DocumentConsistencyAssessmentRead]:
    statement = select(DocumentConsistencyAssessment).order_by(DocumentConsistencyAssessment.created_at.desc())
    if lead_id:
        statement = statement.where(DocumentConsistencyAssessment.lead_id == lead_id)
    if review_status:
        statement = statement.where(DocumentConsistencyAssessment.review_status == review_status)
    rows = session.exec(statement.limit(max(1, min(limit, 500)))).all()
    return [assessment_read(row) for row in rows]


@router.get("/validations/{assessment_id}", response_model=DocumentConsistencyAssessmentRead)
def api_get_validation(
    assessment_id: UUID,
    session: Session = Depends(get_session),
) -> DocumentConsistencyAssessmentRead:
    assessment = session.get(DocumentConsistencyAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Document consistency assessment not found")
    return assessment_read(assessment)


@router.post("/validations/{assessment_id}/review", response_model=DocumentConsistencyAssessmentRead)
def api_review_validation(
    assessment_id: UUID,
    payload: DocumentConsistencyReviewRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentConsistencyAssessmentRead:
    try:
        return review_consistency_assessment(
            session,
            assessment_id,
            decision=payload.decision,
            notes=payload.notes,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc

@router.post("/expiry-reminders/scan", response_model=DocumentExpiryScanResult)
def api_scan_expiry_reminders(
    payload: DocumentExpiryScanRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentExpiryScanResult:
    result = scan_document_expiry_reminders(
        session,
        lead_id=payload.lead_id,
        actor=_actor(request),
    )
    return DocumentExpiryScanResult(**result)


@router.get("/expiry-reminders", response_model=list[DocumentExpiryReminderRead])
def api_list_expiry_reminders(
    lead_id: UUID | None = None,
    status: str | None = None,
    reminder_type: str | None = None,
    limit: int = 100,
    session: Session = Depends(get_session),
) -> list[DocumentExpiryReminderRead]:
    statement = select(DocumentExpiryReminderTask).order_by(
        DocumentExpiryReminderTask.status,
        DocumentExpiryReminderTask.expiry_date,
        DocumentExpiryReminderTask.created_at.desc(),
    )
    if lead_id:
        statement = statement.where(DocumentExpiryReminderTask.lead_id == lead_id)
    if status:
        statement = statement.where(DocumentExpiryReminderTask.status == status)
    if reminder_type:
        statement = statement.where(DocumentExpiryReminderTask.reminder_type == reminder_type)
    rows = session.exec(statement.limit(max(1, min(limit, 500)))).all()
    return [reminder_read(row) for row in rows]


@router.get("/expiry-reminders/{reminder_id}", response_model=DocumentExpiryReminderRead)
def api_get_expiry_reminder(
    reminder_id: UUID,
    session: Session = Depends(get_session),
) -> DocumentExpiryReminderRead:
    reminder = session.get(DocumentExpiryReminderTask, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Document expiry reminder not found")
    return reminder_read(reminder)


@router.post("/expiry-reminders/{reminder_id}/review", response_model=DocumentExpiryReminderRead)
def api_review_expiry_reminder(
    reminder_id: UUID,
    payload: DocumentExpiryReminderReviewRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> DocumentExpiryReminderRead:
    try:
        reminder = review_document_expiry_reminder(
            session,
            reminder_id,
            decision=payload.decision,
            notes=payload.notes,
            actor=_actor(request),
        )
        return reminder_read(reminder)
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc


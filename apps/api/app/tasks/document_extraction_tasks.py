from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.services.document_intelligence import execute_extraction_job


@celery_app.task(bind=True, max_retries=1, default_retry_delay=30)
def run_document_extraction_task(self, extraction_job_id: str) -> dict:
    with Session(db_module.engine) as session:
        job = execute_extraction_job(session, UUID(extraction_job_id))
        return {
            "job_id": str(job.id),
            "document_id": str(job.document_id),
            "status": job.status,
            "error_code": job.error_code,
        }

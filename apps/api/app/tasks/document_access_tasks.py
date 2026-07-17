from __future__ import annotations

from app.core.celery_app import celery_app
from app.core.db import engine
from app.services.document_access import expire_document_access_grants
from sqlmodel import Session


@celery_app.task(name="app.tasks.document_access_tasks.expire_document_access_grants_task")
def expire_document_access_grants_task() -> dict:
    with Session(engine) as session:
        return expire_document_access_grants(session)

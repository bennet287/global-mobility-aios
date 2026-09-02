from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlmodel import Session, select

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.models.domain import SourceMonitor, now_utc
from app.services.source_retrieval import execute_source_monitor


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def run_source_monitor_task(self, monitor_id: str, retrieval_run_id: str | None = None) -> dict:
    with Session(db_module.engine) as session:
        run = execute_source_monitor(
            session,
            UUID(monitor_id),
            retrieval_run_id=UUID(retrieval_run_id) if retrieval_run_id else None,
        )
        result = {
            "monitor_id": monitor_id,
            "retrieval_run_id": str(run.id),
            "status": run.status,
            "snapshot_id": str(run.snapshot_id) if run.snapshot_id else None,
            "regulatory_change_id": str(run.regulatory_change_id) if run.regulatory_change_id else None,
            "error_code": run.error_code,
        }
        if run.status == "failed" and self.request.retries < self.max_retries:
            raise self.retry(exc=RuntimeError(run.error_message or run.error_code or "Source retrieval failed"))
        return result


@celery_app.task
def enqueue_due_source_monitors(limit: int = 100) -> dict:
    now = now_utc()
    with Session(db_module.engine) as session:
        monitors = session.exec(
            select(SourceMonitor)
            .where(SourceMonitor.status.in_(["active", "error"]))
            .where((SourceMonitor.next_check_at.is_(None)) | (SourceMonitor.next_check_at <= now))
            .order_by(SourceMonitor.next_check_at)
            .limit(min(max(limit, 1), 500))
        ).all()
        monitor_ids = [str(monitor.id) for monitor in monitors]
        for monitor in monitors:
            # Lease the due slot before enqueueing so the next beat does not
            # enqueue the same monitor while this task is waiting for a worker.
            monitor.next_check_at = now + timedelta(minutes=max(15, monitor.schedule_minutes))
            monitor.updated_at = now
            session.add(monitor)
        session.commit()

    for monitor_id in monitor_ids:
        run_source_monitor_task.delay(monitor_id)
    return {"queued": len(monitor_ids), "monitor_ids": monitor_ids}

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlmodel import Session, select

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.models.domain import SourceMonitor, now_utc
from app.services.regulatory_authority_bridge import scan_regulatory_authority_bridge
from app.services.regulatory_autonomy import route_pending_regulatory_changes
from app.services.regulatory_freshness_guard import scan_regulatory_freshness
from app.services.regulatory_integrity_watchdog import scan_regulatory_integrity
from app.services.regulatory_machine_verification import verify_routed_regulatory_changes
from app.services.regulatory_program_discovery import discover_new_program_candidates
from app.services.regulatory_promotion_authorization import generate_machine_promotion_authorization_envelopes
from app.services.regulatory_promotion_policy import run_shadow_promotion_policy
from app.services.regulatory_publication_execution_adapter import scan_regulatory_publication_execution_preflight
from app.services.regulatory_reassessment_propagation import propagate_regulatory_reassessment_impacts
from app.services.regulatory_rule_compiler import compile_discovered_regulatory_candidates
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
            monitor.next_check_at = now + timedelta(minutes=max(15, monitor.schedule_minutes))
            monitor.updated_at = now
            session.add(monitor)
        session.commit()

    for monitor_id in monitor_ids:
        run_source_monitor_task.delay(monitor_id)
    return {"queued": len(monitor_ids), "monitor_ids": monitor_ids}


@celery_app.task
def route_pending_regulatory_changes_task(limit: int = 100) -> dict:
    with Session(db_module.engine) as session:
        return route_pending_regulatory_changes(session, limit=limit)


@celery_app.task
def verify_routed_regulatory_changes_task(limit: int = 100) -> dict:
    with Session(db_module.engine) as session:
        return verify_routed_regulatory_changes(session, limit=limit)


@celery_app.task
def scan_regulatory_integrity_task(limit: int = 100) -> dict:
    with Session(db_module.engine) as session:
        return scan_regulatory_integrity(session, limit=limit)


@celery_app.task
def propagate_regulatory_reassessment_impacts_task(limit: int = 100) -> dict:
    with Session(db_module.engine) as session:
        return propagate_regulatory_reassessment_impacts(session, limit=limit)


@celery_app.task
def discover_new_program_candidates_task(limit: int = 100) -> dict:
    with Session(db_module.engine) as session:
        return discover_new_program_candidates(session, limit=limit)


@celery_app.task
def compile_discovered_regulatory_candidates_task(limit: int = 100) -> dict:
    with Session(db_module.engine) as session:
        return compile_discovered_regulatory_candidates(session, limit=limit)


@celery_app.task
def run_shadow_promotion_policy_task(limit: int = 100) -> dict:
    """Evaluate RI.A7 promotion eligibility without enabling publication authority."""

    with Session(db_module.engine) as session:
        return run_shadow_promotion_policy(session, limit=limit)


@celery_app.task
def scan_regulatory_freshness_task(limit: int = 100) -> dict:
    """Evaluate RI.A8 freshness/quarantine state without canonical rollback writes."""

    with Session(db_module.engine) as session:
        return scan_regulatory_freshness(session, limit=limit)


@celery_app.task
def generate_machine_promotion_authorization_envelopes_task(limit: int = 100) -> dict:
    """Generate RI.A7.1 evidence-ready envelopes while machine execution remains disabled."""

    with Session(db_module.engine) as session:
        return generate_machine_promotion_authorization_envelopes(session, limit=limit)


@celery_app.task
def scan_regulatory_authority_bridge_task(limit: int = 100) -> dict:
    """Assess RI.A7.2 Board delegation without enabling machine publication writes."""

    with Session(db_module.engine) as session:
        return scan_regulatory_authority_bridge(session, limit=limit)


@celery_app.task
def scan_regulatory_publication_execution_preflight_task(limit: int = 100) -> dict:
    """Run RI.A7.3 publication execution safety preflight with canonical writes disabled."""

    with Session(db_module.engine) as session:
        return scan_regulatory_publication_execution_preflight(session, limit=limit)

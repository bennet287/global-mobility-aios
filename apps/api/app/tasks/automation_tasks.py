from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.models.domain import AutomationDelivery
from app.services.automation_connector import (
    STALE_DISPATCHING_MINUTES,
    attempt_delivery_dispatch,
    reconcile_automation_deliveries,
    reset_stale_dispatching_deliveries,
)


MAX_BATCH_SIZE = 100


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@celery_app.task
def dispatch_automation_deliveries_task(batch_size: int = MAX_BATCH_SIZE) -> dict:
    dispatched = 0
    failed = 0
    locked = 0
    with Session(db_module.engine) as session:
        reset_stale_dispatching_deliveries(session, actor="automation-worker")

        now = _utc_now()
        statement = (
            select(AutomationDelivery)
            .where(AutomationDelivery.status.in_(["ready", "retry"]))
            .where(
                (AutomationDelivery.next_attempt_at.is_(None))
                | (AutomationDelivery.next_attempt_at <= now)
            )
            .order_by(AutomationDelivery.created_at)
            .limit(min(max(batch_size, 1), MAX_BATCH_SIZE))
            .with_for_update()
        )
        deliveries = list(session.exec(statement).all())
        for delivery in deliveries:
            delivery.status = "dispatching"
            delivery.next_attempt_at = now + timedelta(minutes=STALE_DISPATCHING_MINUTES)
            delivery.updated_at = now
            session.add(delivery)
        session.commit()
        locked = len(deliveries)

        for delivery in deliveries:
            try:
                updated = attempt_delivery_dispatch(session, delivery, actor="automation-worker")
                if updated.status == "dispatched":
                    dispatched += 1
                else:
                    failed += 1
            except Exception:
                session.rollback()
                failed += 1
    return {"processed": locked, "dispatched": dispatched, "failed": failed}


@celery_app.task
def reconcile_automation_deliveries_task(max_age_hours: int = 24) -> dict[str, int]:
    with Session(db_module.engine) as session:
        reset_stale_dispatching_deliveries(session, actor="reconciliation-worker")
        result = reconcile_automation_deliveries(
            session, max_age_hours=max_age_hours, actor="automation-worker"
        )
    return result

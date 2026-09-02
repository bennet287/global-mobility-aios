from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    JurisdictionCoverageEvidenceBatch,
    JurisdictionCoverageEvidenceBatchItem,
    JurisdictionImmigrationAssessment,
    JurisdictionSourceCertification,
    OfficialSource,
    SourceMonitor,
    SourceRetrievalRun,
    SourceSnapshot,
    now_utc,
)
from app.services.audit_log import record_audit

_IN_PROGRESS_RUN_STATUSES = {"queued", "running"}


def _latest_run(session: Session, monitor_id: UUID) -> SourceRetrievalRun | None:
    return session.exec(
        select(SourceRetrievalRun)
        .where(SourceRetrievalRun.monitor_id == monitor_id)
        .order_by(SourceRetrievalRun.started_at.desc())
        .limit(1)
    ).first()


def _latest_snapshot(session: Session, source_id: UUID) -> SourceSnapshot | None:
    return session.exec(
        select(SourceSnapshot)
        .where(SourceSnapshot.official_source_id == source_id)
        .order_by(SourceSnapshot.captured_at.desc())
        .limit(1)
    ).first()


def _item_state(session: Session, item: JurisdictionCoverageEvidenceBatchItem) -> dict[str, Any]:
    # A source-only supplemental batch intentionally has no local assessment.
    # In that case only, reuse the latest independently approved assessment
    # for the same jurisdiction. A batch-local pending or rejected
    # assessment is never bypassed.
    if item.immigration_assessment_id:
        assessment = session.get(
            JurisdictionImmigrationAssessment,
            item.immigration_assessment_id,
        )
    else:
        assessment = session.exec(
            select(JurisdictionImmigrationAssessment)
            .where(
                JurisdictionImmigrationAssessment.jurisdiction_id
                == item.jurisdiction_id
            )
            .where(
                JurisdictionImmigrationAssessment.status == "approved"
            )
            .order_by(
                JurisdictionImmigrationAssessment.reviewed_at.desc()
            )
        ).first()
    certification = (
        session.get(JurisdictionSourceCertification, item.source_certification_id)
        if item.source_certification_id
        else None
    )

    # Certification-only items created before v13.10.2.3 may have
    # null denormalized linkage columns. Resolve them read-only from
    # the immutable source certification.
    effective_source_id = item.official_source_id or (
        certification.official_source_id if certification else None
    )
    effective_authority_id = item.regulatory_authority_id or (
        certification.regulatory_authority_id if certification else None
    )

    source = (
        session.get(OfficialSource, effective_source_id)
        if effective_source_id
        else None
    )

    if item.source_monitor_id:
        monitor = session.get(
            SourceMonitor,
            item.source_monitor_id,
        )
    elif source is not None:
        monitor = session.exec(
            select(SourceMonitor).where(
                SourceMonitor.official_source_id == source.id
            )
        ).first()
    else:
        monitor = None

    effective_monitor_id = (
        item.source_monitor_id
        or (monitor.id if monitor else None)
    )

    latest_snapshot = _latest_snapshot(
        session,
        source.id,
    ) if source else None

    latest_run = _latest_run(
        session,
        monitor.id,
    ) if monitor else None

    supplemental_scope = bool(
        certification
        and certification.certification_scope.startswith("supplemental_")
    )
    source_only_supplement = item.immigration_assessment_id is None
    assessment_approved = bool(
        assessment
        and assessment.status == "approved"
        and assessment.jurisdiction_id == item.jurisdiction_id
        and (
            supplemental_scope
            or source_only_supplement
            or assessment.official_source_id is None
            or assessment.official_source_id == effective_source_id
        )
    )
    certification_approved = bool(
        certification
        and certification.status == "approved"
        and certification.official_source_id == effective_source_id
        and certification.regulatory_authority_id == effective_authority_id
    )
    source_active = bool(source and source.active)
    monitor_active = bool(monitor and monitor.status in {"active", "error"})

    if not assessment_approved or not certification_approved:
        state = "pending_independent_review"
    elif latest_snapshot is not None:
        state = "baseline_ready"
    elif latest_run and latest_run.status in _IN_PROGRESS_RUN_STATUSES:
        state = "retrieval_in_progress"
    elif not source or not monitor:
        state = "source_monitor_missing"
    elif not source_active:
        state = "source_inactive"
    elif not monitor_active:
        state = "monitor_inactive"
    elif latest_run and latest_run.status == "failed":
        state = "retrieval_failed"
    else:
        state = "ready_to_queue"

    return {
        "batch_item_id": item.id,
        "alpha2_code": item.alpha2_code,
        "jurisdiction_id": item.jurisdiction_id,
        "official_source_id": effective_source_id,
        "source_monitor_id": effective_monitor_id,
        "assessment_status": assessment.status if assessment else "missing",
        "certification_status": certification.status if certification else "missing",
        "source_active": source_active,
        "monitor_status": monitor.status if monitor else "missing",
        "state": state,
        "eligible_to_queue": state in {"ready_to_queue", "retrieval_failed"},
        "latest_run": None
        if latest_run is None
        else {
            "id": latest_run.id,
            "status": latest_run.status,
            "attempt": latest_run.attempt,
            "started_at": latest_run.started_at,
            "completed_at": latest_run.completed_at,
            "error_code": latest_run.error_code,
            "error_message": latest_run.error_message,
        },
        "latest_snapshot": None
        if latest_snapshot is None
        else {
            "id": latest_snapshot.id,
            "status": latest_snapshot.status,
            "content_hash": latest_snapshot.content_hash,
            "captured_at": latest_snapshot.captured_at,
            "url": latest_snapshot.url,
        },
    }


def coverage_batch_baseline_status(session: Session, batch_id: UUID) -> dict[str, Any]:
    batch = session.get(JurisdictionCoverageEvidenceBatch, batch_id)
    if batch is None:
        raise ValueError("Coverage evidence batch not found")
    rows = session.exec(
        select(JurisdictionCoverageEvidenceBatchItem)
        .where(JurisdictionCoverageEvidenceBatchItem.batch_id == batch.id)
        .order_by(JurisdictionCoverageEvidenceBatchItem.row_number)
    ).all()
    items = [_item_state(session, row) for row in rows]
    counts: dict[str, int] = {}
    for item in items:
        counts[item["state"]] = counts.get(item["state"], 0) + 1
    return {
        "batch_id": batch.id,
        "batch_name": batch.name,
        "submitted_by": batch.submitted_by,
        "item_count": len(items),
        "counts": counts,
        "eligible_to_queue": sum(1 for item in items if item["eligible_to_queue"]),
        "baseline_ready": counts.get("baseline_ready", 0),
        "in_progress": counts.get("retrieval_in_progress", 0),
        "failed": counts.get("retrieval_failed", 0),
        "pending_review": counts.get("pending_independent_review", 0),
        "items": items,
        "safety": {
            "publishes_verified_rule": False,
            "creates_coverage_claim": False,
            "requires_approved_assessment_and_certification": True,
            "message": "Baseline capture stores official-source evidence only. It does not approve a rule or make a coverage claim.",
        },
    }


def queue_coverage_batch_baselines(
    session: Session,
    *,
    batch_id: UUID,
    actor: str,
    alpha2_codes: set[str] | None = None,
) -> dict[str, Any]:
    status = coverage_batch_baseline_status(session, batch_id)
    queued: list[SourceRetrievalRun] = []
    skipped: list[dict[str, Any]] = []
    now = now_utc()

    selected_codes = None if alpha2_codes is None else {code.strip().upper() for code in alpha2_codes}

    for item_status in status["items"]:
        if selected_codes is not None and item_status["alpha2_code"].upper() not in selected_codes:
            skipped.append({"alpha2_code": item_status["alpha2_code"], "state": "not_selected"})
            continue
        if not item_status["eligible_to_queue"]:
            skipped.append({"alpha2_code": item_status["alpha2_code"], "state": item_status["state"]})
            continue
        monitor_id = item_status["source_monitor_id"]
        source_id = item_status["official_source_id"]
        if not monitor_id or not source_id:
            skipped.append({"alpha2_code": item_status["alpha2_code"], "state": "source_monitor_missing"})
            continue
        monitor = session.exec(
            select(SourceMonitor)
            .where(SourceMonitor.id == monitor_id)
            .with_for_update()
        ).one_or_none()
        source = session.get(OfficialSource, source_id)
        if monitor is None or source is None:
            skipped.append({"alpha2_code": item_status["alpha2_code"], "state": "source_monitor_missing"})
            continue
        latest = _latest_run(session, monitor.id)
        if latest and latest.status in _IN_PROGRESS_RUN_STATUSES:
            skipped.append({"alpha2_code": item_status["alpha2_code"], "state": "retrieval_in_progress"})
            continue
        prior_attempts = len(
            session.exec(
                select(SourceRetrievalRun).where(SourceRetrievalRun.monitor_id == monitor.id)
            ).all()
        )
        run = SourceRetrievalRun(
            monitor_id=monitor.id,
            official_source_id=source.id,
            status="queued",
            attempt=prior_attempts + 1,
            requested_url=source.url,
            started_at=now,
        )
        monitor.next_check_at = now + timedelta(minutes=max(15, monitor.schedule_minutes))
        monitor.updated_at = now
        session.add(run)
        session.add(monitor)
        queued.append(run)

    if queued:
        record_audit(
            session,
            action="coverage_baseline_capture_queued",
            entity_type="jurisdiction_coverage_evidence_batch",
            entity_id=batch_id,
            after_state={
                "queued_count": len(queued),
                "monitor_ids": [run.monitor_id for run in queued],
                "retrieval_run_ids": [run.id for run in queued],
                "skipped_count": len(skipped),
            },
            actor=actor,
            source="global_intelligence",
        )
        session.commit()
        for run in queued:
            session.refresh(run)

    queue_failures: list[dict[str, Any]] = []
    if queued:
        from app.tasks.source_monitor_tasks import run_source_monitor_task

        for run in queued:
            try:
                run_source_monitor_task.delay(str(run.monitor_id), str(run.id))
            except Exception as exc:  # pragma: no cover - broker failures are environment-specific
                persisted = session.get(SourceRetrievalRun, run.id)
                if persisted is not None:
                    persisted.status = "failed"
                    persisted.error_code = "queue_failed"
                    persisted.error_message = str(exc)
                    persisted.completed_at = now_utc()
                    session.add(persisted)
                    session.commit()
                queue_failures.append(
                    {
                        "retrieval_run_id": run.id,
                        "monitor_id": run.monitor_id,
                        "error": str(exc),
                    }
                )

    refreshed = coverage_batch_baseline_status(session, batch_id)
    refreshed["queued"] = len(queued) - len(queue_failures)
    refreshed["queue_failures"] = queue_failures
    refreshed["skipped"] = skipped
    return refreshed

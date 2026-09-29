from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision, OrganizationActivity, OrganizationBlocker,
    OrganizationHumanAction, OrganizationHumanActionRequest,
    OrganizationRecordReference, OrganizationalWorkItem, RiskEscalation,
)
from app.schemas_organization_grc_evidence import GRCEvidenceExportEntry, GRCEvidenceExportRead
from app.services.organization_command import (
    NotFound, OrganizationCommandContext, require_human, tenant_record,
)
from app.services.organization_grc_traceability import project_organization_grc_traceability


def _value(value: object) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def export_grc_risk_evidence(
    session: Session, context: OrganizationCommandContext, *, risk_id: UUID,
) -> GRCEvidenceExportRead:
    """Export source identities for one tenant-scoped risk without certifying evidence.

    The GRC trace owns relationship selection. Global AuditLog has no tenant column,
    so references to it remain declared pointers and its contents are never loaded.
    The export is a current read projection, not a signed or transactional snapshot.
    """
    require_human(context, admin=True)
    with session.no_autoflush:
        risk = session.get(RiskEscalation, risk_id)
        if risk is None or risk.work_item_id is None:
            raise NotFound("risk was not found in this tenant")
        work = tenant_record(
            session, OrganizationalWorkItem, risk.work_item_id,
            context.tenant_key, label="risk WorkItem",
        )
        trace = next(
            (item for item in project_organization_grc_traceability(
                session, tenant_key=context.tenant_key,
            ) if item.risk_id == risk.id),
            None,
        )
        if trace is None:
            raise NotFound("risk has no tenant-scoped GRC trace")

        entries: list[GRCEvidenceExportEntry] = [
            GRCEvidenceExportEntry(
                record_type="organizational_work_item", record_id=work.id,
                relation="tenant_scope", status=work.status,
                record_fingerprint=work.idempotency_fingerprint,
            ),
            GRCEvidenceExportEntry(
                record_type="risk_escalation", record_id=risk.id,
                relation="risk_for_work_item", related_record_type="organizational_work_item",
                related_record_id=work.id, status=risk.status,
            ),
        ]
        # Only decisions in explicit risk-source or linked-blocker lineage belong
        # here; the older same-WorkItem decision list is adjacency, not provenance.
        owners: dict[tuple[str, UUID], tuple[str, UUID]] = {("risk_escalation_id", risk.id): ("risk_escalation", risk.id)}
        activity_sources: set[tuple[str, str]] = set()
        for decision_trace in trace.governance_decisions:
            decision = tenant_record(
                session, ExecutiveDecision, decision_trace.decision_id,
                context.tenant_key, label="governance decision",
            )
            parent = next(
                (blocker for blocker in trace.remediation_blockers if blocker.decision_id == decision.id),
                None,
            )
            related_type, related_id = (
                ("organization_blocker", parent.blocker_id) if parent is not None
                else ("risk_escalation", risk.id)
            )
            entries.append(GRCEvidenceExportEntry(
                record_type="executive_decision", record_id=decision.id,
                relation="explicit_governance_decision", related_record_type=related_type,
                related_record_id=related_id, status=decision.status,
                record_fingerprint=decision.record_fingerprint,
                source_object_version=decision.source_object_version,
                supersedes_record_id=decision.supersedes_decision_id,
            ))
            owners[("decision_id", decision.id)] = ("executive_decision", decision.id)
            activity_sources.add(("executive_decision", str(decision.id)))

        seen_requests: set[UUID] = set()

        def add_requests(request_traces, parent_type: str, parent_id: UUID) -> None:
            for request_trace in request_traces:
                request = tenant_record(
                    session, OrganizationHumanActionRequest, request_trace.request_id,
                    context.tenant_key, label="governance human request",
                )
                if request.id in seen_requests:
                    continue
                seen_requests.add(request.id)
                entries.append(GRCEvidenceExportEntry(
                    record_type="organization_human_action_request", record_id=request.id,
                    relation=f"human_request:{_value(request.request_type)}",
                    related_record_type=parent_type, related_record_id=parent_id,
                    status=_value(request.status), record_fingerprint=request.record_fingerprint,
                    source_object_version=request.source_object_version,
                ))
                owners[("human_action_request_id", request.id)] = ("organization_human_action_request", request.id)
                activity_sources.add(("organization_human_action_request", str(request.id)))
                for action_trace in request_trace.actions:
                    action = tenant_record(
                        session, OrganizationHumanAction, action_trace.action_id,
                        context.tenant_key, label="governance human action",
                    )
                    entries.append(GRCEvidenceExportEntry(
                        record_type="organization_human_action", record_id=action.id,
                        relation=f"human_action:{_value(action.action_type)}",
                        related_record_type="organization_human_action_request",
                        related_record_id=request.id, status=action.outcome,
                        record_fingerprint=action.record_fingerprint,
                        source_object_version=action.source_object_version,
                        occurred_at=action.occurred_at,
                    ))
                    owners[("human_action_id", action.id)] = ("organization_human_action", action.id)
                    activity_sources.add(("organization_human_action", str(action.id)))

        for blocker_trace in trace.remediation_blockers:
            blocker = tenant_record(
                session, OrganizationBlocker, blocker_trace.blocker_id,
                context.tenant_key, label="risk blocker",
            )
            entries.append(GRCEvidenceExportEntry(
                record_type="organization_blocker", record_id=blocker.id,
                relation="explicit_risk_blocker", related_record_type="risk_escalation",
                related_record_id=risk.id, status=_value(blocker.status),
                record_fingerprint=blocker.record_fingerprint,
                source_object_version=blocker.source_object_version,
                supersedes_record_id=blocker.supersedes_blocker_id,
            ))
            owners[("blocker_id", blocker.id)] = ("organization_blocker", blocker.id)
            activity_sources.add(("organization_blocker", str(blocker.id)))
            add_requests(blocker_trace.human_requests, "organization_blocker", blocker.id)
        for decision_trace in trace.governance_decisions:
            add_requests(
                decision_trace.human_requests, "executive_decision", decision_trace.decision_id,
            )

        # Activities carry tenant and WorkItem scope plus the exact source identity.
        # Their fingerprints identify stored Activity commands, not evidence truth.
        activities = session.exec(select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == context.tenant_key,
            OrganizationActivity.work_item_id == work.id,
        )).all()
        for activity in activities:
            source = (activity.source_object_type, activity.source_object_id)
            if source not in activity_sources:
                continue
            entries.append(GRCEvidenceExportEntry(
                record_type="organization_activity", record_id=activity.id,
                relation=f"activity:{activity.activity_type}",
                related_record_type=activity.source_object_type,
                related_record_id=UUID(activity.source_object_id),
                record_fingerprint=activity.record_fingerprint,
                source_object_version=activity.source_object_version,
                supersedes_record_id=activity.supersedes_activity_id,
                occurred_at=activity.occurred_at,
            ))

        # The reference ledger is tenant scoped. Export its claims as pointers only;
        # never resolve a global audit-log target or assert a mapping is effective.
        owner_filters = [
            getattr(OrganizationRecordReference, field) == record_id
            for field, record_id in owners
        ]
        references = session.exec(select(OrganizationRecordReference).where(
            OrganizationRecordReference.tenant_key == context.tenant_key,
            or_(*owner_filters),
        )).all()
        for reference in references:
            owner = next((value for (field, record_id), value in owners.items()
                          if getattr(reference, field) == record_id), None)
            if owner is None:
                continue
            try:
                metadata = json.loads(reference.metadata_json)
            except (TypeError, ValueError):
                metadata = None
            mapping_state = metadata.get("mapping_state") if isinstance(metadata, dict) else None
            entries.append(GRCEvidenceExportEntry(
                record_type="organization_record_reference", record_id=reference.id,
                relation=f"declared_reference:{_value(reference.reference_role)}",
                related_record_type=owner[0], related_record_id=owner[1],
                status=mapping_state if isinstance(mapping_state, str) else None,
                record_fingerprint=reference.record_fingerprint,
                supersedes_record_id=reference.supersedes_reference_id,
                target_type=_value(reference.target_type), target_id=reference.target_id,
                target_version=reference.target_version,
                occurred_at=reference.created_at,
            ))

    return GRCEvidenceExportRead(
        tenant_key=context.tenant_key, risk_id=risk.id, work_item_id=work.id,
        source_records=tuple(sorted(entries, key=lambda entry: (
            entry.record_type, str(entry.record_id), entry.relation,
        ))),
    )

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlmodel import Session, func, select

from app.models.domain import (
    AutomationDelivery,
    AutomationEvent,
    AutomationRule,
    CorporateAccount,
    CorporateMobilityCase,
)
from app.schemas_automation import AutomationRuleCreate
from app.services.audit_log import record_audit, to_audit_dict
from app.services.automation_connector import find_connector_for_account_channel


AUTOMATION_CHANNELS = {"email", "messaging", "calendar", "crm"}
AUTOMATION_EVENT_TYPES = {
    "case.created",
    "case.status_changed",
    "compliance.created",
    "compliance.status_changed",
    "task.status_changed",
    "appointment.status_changed",
    "appointment.reminder",
    "submission.status_changed",
    "external_agency_assignment.status_changed",
    "authority_checklist.reminder",
}
EXTERNAL_CHANNELS = {"email", "messaging", "calendar"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


class _SafeValues(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _render(template: str | None, values: dict[str, Any], fallback: str) -> str:
    return (template or fallback).format_map(_SafeValues(values)).strip()


def rule_read(rule: AutomationRule) -> dict[str, Any]:
    return {
        **to_audit_dict(rule),
        "channels": [part for part in rule.channels.split(",") if part],
        "destinations": _load(rule.destinations_json, {}),
    }


def event_read(session: Session, event: AutomationEvent) -> dict[str, Any]:
    count = session.exec(
        select(func.count())
        .select_from(AutomationDelivery)
        .where(AutomationDelivery.automation_event_id == event.id)
    ).one()
    return {
        **to_audit_dict(event),
        "payload": _load(event.payload_json, {}),
        "delivery_count": int(count or 0),
    }


def delivery_read(delivery: AutomationDelivery) -> dict[str, Any]:
    return {
        **to_audit_dict(delivery),
        "payload": _load(delivery.payload_json, {}),
    }


def create_rule(
    session: Session,
    payload: AutomationRuleCreate,
    *,
    actor: str,
) -> AutomationRule:
    account = session.get(CorporateAccount, payload.corporate_account_id)
    if account is None:
        raise ValueError("Corporate account not found")
    if account.account_status != "active":
        raise ValueError("Automation rules require an active corporate account")
    channels = list(dict.fromkeys(payload.channels))
    unknown = set(channels) - AUTOMATION_CHANNELS
    if unknown:
        raise ValueError(f"Unsupported automation channels: {', '.join(sorted(unknown))}")
    missing_destinations = [channel for channel in channels if not payload.destinations.get(channel, "").strip()]
    if missing_destinations:
        raise ValueError(
            "Every automation channel requires a named destination: "
            + ", ".join(missing_destinations)
        )
    if not payload.requires_human_approval and set(channels) & EXTERNAL_CHANNELS:
        raise ValueError("Email, messaging, and calendar automation requires human approval")

    rule = AutomationRule(
        corporate_account_id=account.id,
        name=payload.name.strip(),
        event_type=payload.event_type,
        channels=",".join(channels),
        destinations_json=_json(
            {channel: payload.destinations[channel].strip() for channel in channels}
        ),
        subject_template=payload.subject_template.strip() if payload.subject_template else None,
        body_template=payload.body_template.strip() if payload.body_template else None,
        requires_human_approval=payload.requires_human_approval,
        created_by=actor,
        updated_by=actor,
    )
    session.add(rule)
    session.flush()
    record_audit(
        session,
        action="automation_rule_created",
        entity_type="automation_rule",
        entity_id=rule.id,
        after_state=rule_read(rule),
        actor=actor,
        source="automation_v12_3",
    )
    session.commit()
    session.refresh(rule)
    return rule


def update_rule_status(
    session: Session,
    rule: AutomationRule,
    *,
    status: str,
    reason: str,
    actor: str,
) -> AutomationRule:
    if status not in {"active", "paused"}:
        raise ValueError("Automation rule status must be active or paused")
    before = rule_read(rule)
    rule.status = status
    rule.updated_by = actor
    rule.updated_at = _now()
    session.add(rule)
    record_audit(
        session,
        action=f"automation_rule_{status}",
        entity_type="automation_rule",
        entity_id=rule.id,
        before_state=before,
        after_state=rule_read(rule),
        reason=reason.strip(),
        actor=actor,
        source="automation_v12_3",
    )
    session.commit()
    session.refresh(rule)
    return rule


def capture_event(
    session: Session,
    *,
    idempotency_key: str,
    corporate_account_id: UUID,
    case_id: UUID,
    event_type: str,
    entity_type: str,
    entity_id: UUID | str,
    payload: dict[str, Any],
    actor: str,
    source: str = "domain",
    occurred_at: datetime | None = None,
) -> tuple[AutomationEvent, bool]:
    clean_key = idempotency_key.strip()
    existing = session.exec(
        select(AutomationEvent).where(AutomationEvent.idempotency_key == clean_key)
    ).first()
    if existing is not None:
        if (
            existing.corporate_account_id != corporate_account_id
            or existing.event_type != event_type
            or existing.entity_id != str(entity_id)
        ):
            raise ValueError("Idempotency key is already bound to a different event")
        return existing, False
    if event_type not in AUTOMATION_EVENT_TYPES:
        raise ValueError("Unsupported automation event type")
    account = session.get(CorporateAccount, corporate_account_id)
    if account is None:
        raise ValueError("Corporate account not found")
    if account.account_status != "active":
        raise ValueError("Automation events require an active corporate account")
    case = session.get(CorporateMobilityCase, case_id)
    if case is None:
        raise ValueError("Corporate mobility case not found")
    if case.corporate_account_id != corporate_account_id:
        raise ValueError("Corporate mobility case does not belong to the automation account")

    safe_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"notes", "contact_email", "contact_name", "email", "phone"}
    }
    event = AutomationEvent(
        idempotency_key=clean_key,
        corporate_account_id=corporate_account_id,
        corporate_mobility_case_id=case_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        source=source,
        payload_json=_json(safe_payload),
        occurred_at=occurred_at or _now(),
        created_by=actor,
    )
    session.add(event)
    session.flush()

    rules = session.exec(
        select(AutomationRule).where(
            AutomationRule.corporate_account_id == corporate_account_id,
            AutomationRule.event_type == event_type,
            AutomationRule.status == "active",
        )
    ).all()
    values = {
        "event_type": event_type,
        "case_reference": case.case_reference,
        "case_status": case.status,
        "destination_country": case.destination_country,
        **safe_payload,
    }
    for rule in rules:
        destinations = _load(rule.destinations_json, {})
        for channel in (part for part in rule.channels.split(",") if part):
            connector_config = find_connector_for_account_channel(session, corporate_account_id, channel)
            status = "pending_review" if rule.requires_human_approval else "ready"
            delivery = AutomationDelivery(
                automation_event_id=event.id,
                automation_rule_id=rule.id,
                connector_config_id=connector_config.id if connector_config else None,
                channel=channel,
                destination=destinations.get(channel),
                subject=_render(
                    rule.subject_template,
                    values,
                    f"{case.case_reference}: {event_type}",
                ),
                payload_json=_json(
                    {
                        "event_type": event_type,
                        "case_reference": case.case_reference,
                        "channel": channel,
                        "body": _render(
                            rule.body_template,
                            values,
                            f"Case {case.case_reference} recorded {event_type}.",
                        ),
                        "facts": safe_payload,
                    }
                ),
                status=status,
                requires_human_approval=rule.requires_human_approval,
            )
            session.add(delivery)
    event.status = "queued" if rules else "recorded"
    session.add(event)
    record_audit(
        session,
        action="automation_event_captured",
        entity_type="automation_event",
        entity_id=event.id,
        after_state={
            "idempotency_key": clean_key,
            "event_type": event_type,
            "corporate_account_id": corporate_account_id,
            "case_id": case_id,
            "matched_rules": len(rules),
        },
        actor=actor,
        source="automation_v12_3",
    )
    return event, True


def decide_delivery(
    session: Session,
    delivery: AutomationDelivery,
    *,
    decision: str,
    reason: str,
    actor: str,
) -> AutomationDelivery:
    if delivery.status != "pending_review":
        raise ValueError("Automation delivery is not pending review")
    event = session.get(AutomationEvent, delivery.automation_event_id)
    if event is None:
        raise ValueError("Automation event not found")
    if event.created_by == actor:
        raise ValueError("Automation delivery requires a different reviewer")
    before = delivery_read(delivery)
    now = _now()
    delivery.status = "ready" if decision == "approved" else "rejected"
    delivery.reviewed_by = actor
    delivery.reviewed_at = now
    delivery.review_reason = reason.strip()
    delivery.updated_at = now
    session.add(delivery)
    record_audit(
        session,
        action=f"automation_delivery_{decision}",
        entity_type="automation_delivery",
        entity_id=delivery.id,
        before_state=before,
        after_state=delivery_read(delivery),
        reason=reason.strip(),
        actor=actor,
        source="automation_v12_3",
    )
    session.commit()
    session.refresh(delivery)
    return delivery


def record_dispatch(
    session: Session,
    delivery: AutomationDelivery,
    *,
    provider_message_id: str,
    actor: str,
) -> AutomationDelivery:
    if delivery.status != "ready":
        raise ValueError("Only approved or approval-free deliveries can be dispatched")
    before = delivery_read(delivery)
    now = _now()
    delivery.status = "dispatched"
    delivery.dispatched_by = actor
    delivery.dispatched_at = now
    delivery.provider_message_id = provider_message_id.strip()
    delivery.attempt_count += 1
    delivery.last_error = None
    delivery.updated_at = now
    session.add(delivery)
    record_audit(
        session,
        action="automation_delivery_dispatched",
        entity_type="automation_delivery",
        entity_id=delivery.id,
        before_state=before,
        after_state=delivery_read(delivery),
        actor=actor,
        source="automation_v12_3",
    )
    session.commit()
    session.refresh(delivery)
    return delivery

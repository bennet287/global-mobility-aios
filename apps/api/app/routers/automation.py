from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    AutomationConnectorConfig,
    AutomationDelivery,
    AutomationEvent,
    AutomationRule,
    CorporateMobilityCase,
)
from app.schemas_automation import (
    AutomationDeliveryDecision,
    AutomationDeliveryDispatch,
    AutomationDeliveryRead,
    AutomationEventIngest,
    AutomationEventRead,
    AutomationRuleCreate,
    AutomationRuleRead,
    AutomationRuleStatusUpdate,
    ConnectorConfigCreate,
    ConnectorConfigRead,
    ConnectorConfigStatusUpdate,
)
from app.services.automation import (
    capture_event,
    create_rule,
    decide_delivery,
    delivery_read,
    event_read,
    record_dispatch,
    rule_read,
    update_rule_status,
)
from app.services.automation_connector import (
    attempt_delivery_dispatch,
    connector_config_create,
    connector_config_update_status,
)
from app.services.audit_log import to_audit_dict


def _load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


router = APIRouter(prefix="/api/v1/automation", tags=["governed-automation-v12.4"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    not_found = "not found" in message.lower()
    conflict = "idempotency key" in message.lower() or "not pending" in message.lower()
    return HTTPException(
        status_code=404 if not_found else 409 if conflict else 400,
        detail=message,
    )


@router.post("/rules", response_model=AutomationRuleRead, status_code=201)
def api_create_rule(
    payload: AutomationRuleCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> AutomationRuleRead:
    try:
        rule = create_rule(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return AutomationRuleRead(**rule_read(rule))


@router.get("/rules", response_model=list[AutomationRuleRead])
def api_list_rules(
    corporate_account_id: UUID | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[AutomationRuleRead]:
    statement = select(AutomationRule).order_by(AutomationRule.updated_at.desc())
    if corporate_account_id:
        statement = statement.where(
            AutomationRule.corporate_account_id == corporate_account_id
        )
    if status:
        statement = statement.where(AutomationRule.status == status.strip().lower())
    return [
        AutomationRuleRead(**rule_read(rule))
        for rule in session.exec(statement.limit(limit)).all()
    ]


@router.post("/rules/{rule_id}/status", response_model=AutomationRuleRead)
def api_update_rule_status(
    rule_id: UUID,
    payload: AutomationRuleStatusUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> AutomationRuleRead:
    rule = session.get(AutomationRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    try:
        updated = update_rule_status(
            session,
            rule,
            status=payload.status,
            reason=payload.reason,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return AutomationRuleRead(**rule_read(updated))


@router.post("/events", response_model=AutomationEventRead, status_code=202)
def api_ingest_event(
    payload: AutomationEventIngest,
    request: Request,
    session: Session = Depends(get_session),
) -> AutomationEventRead:
    case = session.get(CorporateMobilityCase, payload.corporate_mobility_case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Corporate mobility case not found")
    try:
        event, created = capture_event(
            session,
            idempotency_key=payload.idempotency_key,
            corporate_account_id=payload.corporate_account_id,
            case_id=case.id,
            event_type=payload.event_type,
            entity_type="corporate_mobility_case",
            entity_id=case.id,
            payload=payload.payload,
            occurred_at=payload.occurred_at,
            actor=_actor(request),
            source="operator_api",
        )
        if created:
            session.commit()
            session.refresh(event)
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return AutomationEventRead(**event_read(session, event))


@router.get("/events", response_model=list[AutomationEventRead])
def api_list_events(
    corporate_account_id: UUID | None = None,
    event_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[AutomationEventRead]:
    statement = select(AutomationEvent).order_by(AutomationEvent.occurred_at.desc())
    if corporate_account_id:
        statement = statement.where(
            AutomationEvent.corporate_account_id == corporate_account_id
        )
    if event_type:
        statement = statement.where(AutomationEvent.event_type == event_type.strip())
    return [
        AutomationEventRead(**event_read(session, event))
        for event in session.exec(statement.limit(limit)).all()
    ]


@router.get("/deliveries", response_model=list[AutomationDeliveryRead])
def api_list_deliveries(
    corporate_account_id: UUID | None = None,
    status: str | None = None,
    channel: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[AutomationDeliveryRead]:
    statement = (
        select(AutomationDelivery)
        .join(AutomationEvent)
        .order_by(AutomationDelivery.created_at.desc())
    )
    if corporate_account_id:
        statement = statement.where(
            AutomationEvent.corporate_account_id == corporate_account_id
        )
    if status:
        statement = statement.where(AutomationDelivery.status == status.strip().lower())
    if channel:
        statement = statement.where(AutomationDelivery.channel == channel.strip().lower())
    return [
        AutomationDeliveryRead(**delivery_read(delivery))
        for delivery in session.exec(statement.limit(limit)).all()
    ]


@router.post(
    "/deliveries/{delivery_id}/decision",
    response_model=AutomationDeliveryRead,
)
def api_decide_delivery(
    delivery_id: UUID,
    payload: AutomationDeliveryDecision,
    request: Request,
    session: Session = Depends(get_session),
) -> AutomationDeliveryRead:
    delivery = session.get(AutomationDelivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Automation delivery not found")
    try:
        updated = decide_delivery(
            session,
            delivery,
            decision=payload.decision,
            reason=payload.reason,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return AutomationDeliveryRead(**delivery_read(updated))


@router.post(
    "/deliveries/{delivery_id}/dispatch-record",
    response_model=AutomationDeliveryRead,
)
def api_record_dispatch(
    delivery_id: UUID,
    payload: AutomationDeliveryDispatch,
    request: Request,
    session: Session = Depends(get_session),
) -> AutomationDeliveryRead:
    delivery = session.get(AutomationDelivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Automation delivery not found")
    try:
        updated = record_dispatch(
            session,
            delivery,
            provider_message_id=payload.provider_message_id,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return AutomationDeliveryRead(**delivery_read(updated))


@router.post("/connectors", response_model=ConnectorConfigRead, status_code=201)
def api_create_connector(
    payload: ConnectorConfigCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ConnectorConfigRead:
    try:
        config = connector_config_create(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return ConnectorConfigRead(**{
        **to_audit_dict(config),
        "credentials": _load(config.credentials_json, {}),
    })


@router.get("/connectors", response_model=list[ConnectorConfigRead])
def api_list_connectors(
    corporate_account_id: UUID | None = None,
    channel: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[ConnectorConfigRead]:
    statement = select(AutomationConnectorConfig).order_by(
        AutomationConnectorConfig.updated_at.desc()
    )
    if corporate_account_id:
        statement = statement.where(
            AutomationConnectorConfig.corporate_account_id == corporate_account_id
        )
    if channel:
        statement = statement.where(AutomationConnectorConfig.channel == channel.strip().lower())
    if status:
        statement = statement.where(AutomationConnectorConfig.status == status.strip().lower())
    return [
        ConnectorConfigRead(**{
            **to_audit_dict(config),
            "credentials": _load(config.credentials_json, {}),
        })
        for config in session.exec(statement.limit(limit)).all()
    ]


@router.post("/connectors/{config_id}/status", response_model=ConnectorConfigRead)
def api_update_connector_status(
    config_id: UUID,
    payload: ConnectorConfigStatusUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> ConnectorConfigRead:
    config = session.get(AutomationConnectorConfig, config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Connector config not found")
    try:
        updated = connector_config_update_status(
            session,
            config,
            status=payload.status,
            reason=payload.reason,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return ConnectorConfigRead(**{
        **to_audit_dict(updated),
        "credentials": _load(updated.credentials_json, {}),
    })


@router.post("/deliveries/{delivery_id}/dispatch", response_model=AutomationDeliveryRead)
def api_dispatch_delivery(
    delivery_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> AutomationDeliveryRead:
    delivery = session.get(AutomationDelivery, delivery_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="Automation delivery not found")
    try:
        updated = attempt_delivery_dispatch(session, delivery, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _error(exc) from exc
    return AutomationDeliveryRead(**delivery_read(updated))

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import ApplicationAuthorityChecklistItem, AuthorityChecklistTemplate, ApplicationRecord
from app.schemas_authority_checklists import (
    ApplicationChecklistItemCreate,
    ApplicationChecklistItemRead,
    ApplicationChecklistItemStatusUpdate,
    ApplyTemplateRequest,
    AuthorityChecklistTemplateCreate,
    AuthorityChecklistTemplateRead,
)
from app.services.audit_log import to_audit_dict
from app.services.automation import event_read
from app.services.authority_checklists import (
    apply_template_to_application,
    create_checklist_item,
    create_template,
    delete_checklist_item,
    emit_checklist_reminder_events,
    list_checklist_items,
    list_checklist_items_for_application,
    list_templates,
    update_checklist_item_status,
)


router = APIRouter(tags=["authority-checklist-tracking"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _handle_value_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if "not found" in lowered:
        return HTTPException(status_code=404, detail=message)
    return HTTPException(status_code=400, detail=message)


@router.post(
    "/api/v1/authority-checklist-templates",
    response_model=AuthorityChecklistTemplateRead,
    status_code=201,
)
def api_create_template(
    payload: AuthorityChecklistTemplateCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> AuthorityChecklistTemplateRead:
    try:
        template = create_template(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return AuthorityChecklistTemplateRead(**to_audit_dict(template))


@router.get(
    "/api/v1/authority-checklist-templates",
    response_model=list[AuthorityChecklistTemplateRead],
)
def api_list_templates(
    authority_name: str | None = None,
    country: str | None = None,
    session: Session = Depends(get_session),
) -> list[AuthorityChecklistTemplateRead]:
    templates = list_templates(session, authority_name=authority_name, country=country)
    return [AuthorityChecklistTemplateRead(**to_audit_dict(t)) for t in templates]


@router.post(
    "/api/v1/authority-checklist-templates/apply",
    response_model=list[ApplicationChecklistItemRead],
    status_code=201,
)
def api_apply_template(
    payload: ApplyTemplateRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> list[ApplicationChecklistItemRead]:
    try:
        items = apply_template_to_application(
            session,
            application_id=payload.application_id,
            authority_name=payload.authority_name,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return [ApplicationChecklistItemRead(**to_audit_dict(item)) for item in items]


@router.post(
    "/api/v1/application-authority-checklist-items",
    response_model=ApplicationChecklistItemRead,
    status_code=201,
)
def api_create_checklist_item(
    payload: ApplicationChecklistItemCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ApplicationChecklistItemRead:
    try:
        item = create_checklist_item(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return ApplicationChecklistItemRead(**to_audit_dict(item))


@router.get(
    "/api/v1/applications/{application_id}/authority-checklist",
    response_model=list[ApplicationChecklistItemRead],
)
def api_list_checklist_items_for_application(
    application_id: UUID,
    session: Session = Depends(get_session),
) -> list[ApplicationChecklistItemRead]:
    items = list_checklist_items_for_application(session, application_id)
    return [ApplicationChecklistItemRead(**to_audit_dict(item)) for item in items]


@router.post(
    "/api/v1/applications/{application_id}/authority-checklist/reminders",
    response_model=list[dict[str, Any]],
    status_code=201,
)
def api_create_checklist_reminders(
    application_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    application = session.get(ApplicationRecord, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    try:
        events = emit_checklist_reminder_events(
            session, application_id=application_id, actor=_actor(request)
        )
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return [event_read(session, event) for event in events]


@router.get(
    "/api/v1/application-authority-checklist-items",
    response_model=list[ApplicationChecklistItemRead],
)
def api_list_checklist_items(
    application_id: UUID | None = None,
    authority_name: str | None = None,
    status: str | None = None,
    session: Session = Depends(get_session),
) -> list[ApplicationChecklistItemRead]:
    items = list_checklist_items(
        session,
        application_id=application_id,
        authority_name=authority_name,
        status=status,
    )
    return [ApplicationChecklistItemRead(**to_audit_dict(item)) for item in items]


@router.get(
    "/api/v1/application-authority-checklist-items/{item_id}",
    response_model=ApplicationChecklistItemRead,
)
def api_get_checklist_item(
    item_id: UUID,
    session: Session = Depends(get_session),
) -> ApplicationChecklistItemRead:
    item = session.get(ApplicationAuthorityChecklistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return ApplicationChecklistItemRead(**to_audit_dict(item))


@router.post(
    "/api/v1/application-authority-checklist-items/{item_id}/status",
    response_model=ApplicationChecklistItemRead,
)
def api_update_checklist_item_status(
    item_id: UUID,
    payload: ApplicationChecklistItemStatusUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> ApplicationChecklistItemRead:
    item = session.get(ApplicationAuthorityChecklistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    try:
        updated = update_checklist_item_status(
            session,
            item,
            payload=payload,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return ApplicationChecklistItemRead(**to_audit_dict(updated))


@router.delete(
    "/api/v1/application-authority-checklist-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
def api_delete_checklist_item(
    item_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
) -> Response:
    item = session.get(ApplicationAuthorityChecklistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    delete_checklist_item(session, item, actor=_actor(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)

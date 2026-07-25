from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ApplicationAuthorityChecklistItem,
    ApplicationRecord,
    AuthorityChecklistTemplate,
    AutomationEvent,
    Lead,
)
from app.schemas_authority_checklists import (
    ApplicationChecklistItemCreate,
    ApplicationChecklistItemStatusUpdate,
    AuthorityChecklistTemplateCreate,
)
from app.services.audit_log import record_audit, to_audit_dict
from app.services.automation import capture_event
from app.services.automation_bridge import _find_corporate_case_for_lead


CHECKLIST_CATEGORIES = {"document", "fee", "form", "step"}
CHECKLIST_STATUSES = {"pending", "completed", "not_applicable"}


def validate_required_checklist_items_complete(
    session: Session,
    application_id: UUID,
    authority_name: str,
) -> None:
    pending = session.exec(
        select(ApplicationAuthorityChecklistItem).where(
            ApplicationAuthorityChecklistItem.application_id == application_id,
            ApplicationAuthorityChecklistItem.authority_name == authority_name.strip(),
            ApplicationAuthorityChecklistItem.is_required.is_(True),  # type: ignore[arg-type]
            ApplicationAuthorityChecklistItem.status == "pending",
        )
    ).all()
    if pending:
        labels = ", ".join(item.item_label for item in pending)
        raise ValueError(
            f"Submission blocked: required checklist items are incomplete for {authority_name}: {labels}"
        )


def emit_checklist_reminder_events(
    session: Session,
    application_id: UUID,
    actor: str,
) -> list[AutomationEvent]:
    application = session.get(ApplicationRecord, application_id)
    if application is None:
        raise ValueError("Application not found")
    if application.lead_id is None:
        return []

    lead = session.get(Lead, application.lead_id)
    if lead is None:
        return []

    corporate_case = _find_corporate_case_for_lead(session, lead.id)
    if corporate_case is None:
        return []

    today = _now().date().isoformat()
    items = session.exec(
        select(ApplicationAuthorityChecklistItem).where(
            ApplicationAuthorityChecklistItem.application_id == application_id,
            ApplicationAuthorityChecklistItem.status == "pending",
        )
    ).all()

    created_events: list[AutomationEvent] = []
    for item in items:
        event, _ = capture_event(
            session,
            idempotency_key=f"authority_checklist.reminder:{item.id}:{today}",
            corporate_account_id=corporate_case.corporate_account_id,
            case_id=corporate_case.id,
            event_type="authority_checklist.reminder",
            entity_type="application_authority_checklist_item",
            entity_id=item.id,
            payload={
                "application_id": str(application.id),
                "lead_id": str(lead.id),
                "lead_name": lead.full_name,
                "case_reference": corporate_case.case_reference,
                "authority_name": item.authority_name,
                "item_key": item.item_key,
                "item_label": item.item_label,
                "is_required": item.is_required,
                "status": item.status,
            },
            actor=actor,
            source="authority_checklist_v12_8",
        )
        created_events.append(event)
    return created_events


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_template(
    session: Session,
    payload: AuthorityChecklistTemplateCreate,
    *,
    actor: str,
) -> AuthorityChecklistTemplate:
    category = payload.category.strip().lower()
    if category not in CHECKLIST_CATEGORIES:
        raise ValueError(f"Invalid checklist category: {payload.category}")

    template = AuthorityChecklistTemplate(
        authority_name=payload.authority_name.strip(),
        country=payload.country.strip() if payload.country else None,
        item_key=payload.item_key.strip().lower(),
        item_label=payload.item_label.strip(),
        category=category,
        is_required=payload.is_required,
        sort_order=payload.sort_order,
        created_by=actor,
        updated_by=actor,
    )
    session.add(template)
    session.flush()
    record_audit(
        session,
        action="authority_checklist_template_created",
        entity_type="authority_checklist_template",
        entity_id=template.id,
        after_state=to_audit_dict(template),
        actor=actor,
        source="authority_checklist_v12_8",
    )
    session.commit()
    session.refresh(template)
    return template


def list_templates(
    session: Session,
    *,
    authority_name: str | None = None,
    country: str | None = None,
    limit: int = 500,
) -> Sequence[AuthorityChecklistTemplate]:
    statement = select(AuthorityChecklistTemplate).order_by(
        AuthorityChecklistTemplate.authority_name,
        AuthorityChecklistTemplate.sort_order,
        AuthorityChecklistTemplate.item_label,
    )
    if authority_name is not None:
        statement = statement.where(
            AuthorityChecklistTemplate.authority_name == authority_name.strip()
        )
    if country is not None:
        statement = statement.where(
            AuthorityChecklistTemplate.country == country.strip()
        )
    return session.exec(statement.limit(limit)).all()


def apply_template_to_application(
    session: Session,
    *,
    application_id: UUID,
    authority_name: str,
    actor: str,
) -> Sequence[ApplicationAuthorityChecklistItem]:
    application = session.get(ApplicationRecord, application_id)
    if application is None:
        raise ValueError("Application not found")

    templates = list_templates(session, authority_name=authority_name)
    if not templates:
        raise ValueError(f"No checklist template found for authority: {authority_name}")

    items: list[ApplicationAuthorityChecklistItem] = []
    for template in templates:
        existing = session.exec(
            select(ApplicationAuthorityChecklistItem).where(
                ApplicationAuthorityChecklistItem.application_id == application_id,
                ApplicationAuthorityChecklistItem.template_item_id == template.id,
            )
        ).first()
        if existing is not None:
            continue
        item = ApplicationAuthorityChecklistItem(
            application_id=application.id,
            template_item_id=template.id,
            authority_name=template.authority_name,
            item_key=template.item_key,
            item_label=template.item_label,
            category=template.category,
            is_required=template.is_required,
            status="pending",
            created_by=actor,
            updated_by=actor,
        )
        session.add(item)
        items.append(item)

    if items:
        session.flush()
        for item in items:
            record_audit(
                session,
                action="application_checklist_item_created",
                entity_type="application_authority_checklist_item",
                entity_id=item.id,
                after_state=to_audit_dict(item),
                actor=actor,
                source="authority_checklist_v12_8",
            )
        session.commit()
        for item in items:
            session.refresh(item)
    return items


def create_checklist_item(
    session: Session,
    payload: ApplicationChecklistItemCreate,
    *,
    actor: str,
) -> ApplicationAuthorityChecklistItem:
    application = session.get(ApplicationRecord, payload.application_id)
    if application is None:
        raise ValueError("Application not found")

    category = payload.category.strip().lower()
    if category not in CHECKLIST_CATEGORIES:
        raise ValueError(f"Invalid checklist category: {payload.category}")

    item = ApplicationAuthorityChecklistItem(
        application_id=application.id,
        authority_name=payload.authority_name.strip(),
        item_key=payload.item_key.strip().lower(),
        item_label=payload.item_label.strip(),
        category=category,
        is_required=payload.is_required,
        status="pending",
        notes=payload.notes.strip() if payload.notes else None,
        created_by=actor,
        updated_by=actor,
    )
    session.add(item)
    session.flush()
    record_audit(
        session,
        action="application_checklist_item_created",
        entity_type="application_authority_checklist_item",
        entity_id=item.id,
        after_state=to_audit_dict(item),
        actor=actor,
        source="authority_checklist_v12_8",
    )
    session.commit()
    session.refresh(item)
    return item


def update_checklist_item_status(
    session: Session,
    item: ApplicationAuthorityChecklistItem,
    *,
    payload: ApplicationChecklistItemStatusUpdate,
    actor: str,
) -> ApplicationAuthorityChecklistItem:
    normalized_status = payload.status.strip().lower()
    if normalized_status not in CHECKLIST_STATUSES:
        raise ValueError(f"Invalid checklist item status: {payload.status}")

    before = to_audit_dict(item)
    now = _now()
    item.status = normalized_status
    if payload.notes is not None:
        item.notes = payload.notes.strip() if payload.notes.strip() else None
    item.updated_by = actor
    item.updated_at = now
    session.add(item)

    record_audit(
        session,
        action=f"application_checklist_item_{normalized_status}",
        entity_type="application_authority_checklist_item",
        entity_id=item.id,
        before_state=before,
        after_state=to_audit_dict(item),
        actor=actor,
        source="authority_checklist_v12_8",
    )
    session.commit()
    session.refresh(item)
    return item


def list_checklist_items_for_application(
    session: Session,
    application_id: UUID,
) -> Sequence[ApplicationAuthorityChecklistItem]:
    return session.exec(
        select(ApplicationAuthorityChecklistItem)
        .where(ApplicationAuthorityChecklistItem.application_id == application_id)
        .order_by(
            ApplicationAuthorityChecklistItem.authority_name,
            ApplicationAuthorityChecklistItem.created_at,
        )
    ).all()


def list_checklist_items(
    session: Session,
    *,
    application_id: UUID | None = None,
    authority_name: str | None = None,
    status: str | None = None,
    limit: int = 500,
) -> Sequence[ApplicationAuthorityChecklistItem]:
    statement = select(ApplicationAuthorityChecklistItem).order_by(
        ApplicationAuthorityChecklistItem.created_at.desc()
    )
    if application_id is not None:
        statement = statement.where(
            ApplicationAuthorityChecklistItem.application_id == application_id
        )
    if authority_name is not None:
        statement = statement.where(
            ApplicationAuthorityChecklistItem.authority_name == authority_name.strip()
        )
    if status is not None:
        statement = statement.where(
            ApplicationAuthorityChecklistItem.status == status.strip().lower()
        )
    return session.exec(statement.limit(limit)).all()


def delete_checklist_item(
    session: Session,
    item: ApplicationAuthorityChecklistItem,
    *,
    actor: str,
) -> None:
    record_audit(
        session,
        action="application_checklist_item_deleted",
        entity_type="application_authority_checklist_item",
        entity_id=item.id,
        before_state=to_audit_dict(item),
        actor=actor,
        source="authority_checklist_v12_8",
    )
    session.delete(item)
    session.commit()

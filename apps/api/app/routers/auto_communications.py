from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import Lead
from app.services.auto_communications import (
    AUTO_TEMPLATES,
    generate_auto_communications_for_lead,
    list_auto_communications,
    parse_auto_communication,
)

router = APIRouter(prefix="/api/v1/auto-communications", tags=["auto-communications"])


@router.get("/templates")
def get_auto_communication_templates() -> dict[str, Any]:
    return {
        "templates": {
            key: {"subject": template["subject"], "body": template["body"].splitlines()[0]}
            for key, template in AUTO_TEMPLATES.items()
        },
    }


@router.post("/leads/{lead_id}")
def create_auto_communications(
    lead_id: UUID,
    trigger: str,
    context: dict[str, Any] | None = None,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        follow_ups = generate_auto_communications_for_lead(session, lead_id, trigger, context or {})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "created",
        "lead_id": lead_id,
        "trigger": trigger,
        "created_count": len(follow_ups),
        "communications": [parse_auto_communication(f) for f in follow_ups],
    }


@router.get("/leads/{lead_id}")
def list_lead_auto_communications(
    lead_id: UUID,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    follow_ups = list_auto_communications(session, lead_id)
    return {
        "lead_id": lead_id,
        "total": len(follow_ups),
        "communications": [parse_auto_communication(f) for f in follow_ups],
    }

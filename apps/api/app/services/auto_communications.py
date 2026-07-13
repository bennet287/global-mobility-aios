from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import FollowUp, Lead

AUTO_PREFIX = "[auto_communication:v1.0]"

AUTO_TEMPLATES: dict[str, dict[str, str]] = {
    "intake_welcome": {
        "subject": "Welcome - we received your {target_country} case",
        "body": """Dear {client_name},

Thank you for starting your case with Global Mobility AIOS.

We have received your details for {target_country}. A consultant will review your profile and the documents you upload.

You can return to your case at any time using this link:
{return_link}

Next steps:
1. Upload your passport and any relevant documents.
2. Review your eligibility preview once it is ready.
3. Wait for a consultant to contact you.

Kind regards,
Global Mobility Support Team""",
    },
    "document_received": {
        "subject": "Document received: {document_type}",
        "body": """Dear {client_name},

We have received your {document_type} and our team will review it shortly.

If the document needs clarification, a consultant will reach out to you.

Return to your case: {return_link}

Kind regards,
Global Mobility Support Team""",
    },
    "eligibility_update": {
        "subject": "Your eligibility preview is ready",
        "body": """Dear {client_name},

Your eligibility preview has been prepared for consultant review.

Current status: {status}
Overall score: {score}%

This is an internal preliminary assessment, not a guarantee of approval. A consultant will review it and contact you with the next steps.

Return to your case: {return_link}

Kind regards,
Global Mobility Support Team""",
    },
    "missing_documents": {
        "subject": "Documents needed to progress your case",
        "body": """Dear {client_name},

To move your {target_country} case forward, please provide the following documents:

{missing_documents}

You can upload them through your case portal:
{return_link}

Kind regards,
Global Mobility Support Team""",
    },
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clean_text(value: Any) -> str:
    text = str(value or "").strip()
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _build_message(trigger: str, subject: str, body: str) -> str:
    return (
        f"{AUTO_PREFIX} trigger={_clean_text(trigger)} "
        f"subject={_clean_text(subject)} body={_clean_text(body)}"
    )


def _extract_from_message(message: str, prefix: str, end_marker: str | None = None) -> str | None:
    try:
        start_index = message.index(prefix) + len(prefix)
        if end_marker and end_marker in message[start_index:]:
            end_index = message.index(end_marker, start_index)
            return message[start_index:end_index].strip()
        return message[start_index:].strip()
    except ValueError:
        return None


def parse_auto_communication(follow_up: FollowUp) -> dict[str, Any]:
    message = str(getattr(follow_up, "message", "") or "")
    trigger = _extract_from_message(message, "trigger=", " subject=") or "unknown"
    subject = _extract_from_message(message, "subject=", " body=") or ""
    body = _extract_from_message(message, "body=") or ""
    return {
        "trigger": trigger,
        "subject": _clean_text(subject),
        "body": _clean_text(body),
        "status": getattr(follow_up, "status", "pending"),
        "channel": getattr(follow_up, "channel", "auto_email"),
        "due_at": getattr(follow_up, "due_at", None),
        "created_at": getattr(follow_up, "created_at", None),
    }


def render_auto_template(
    trigger: str,
    lead: Lead,
    context: dict[str, Any] | None = None,
) -> dict[str, str]:
    if trigger not in AUTO_TEMPLATES:
        raise ValueError(f"Unknown auto-communication trigger: {trigger}")

    template = AUTO_TEMPLATES[trigger]
    ctx = {
        "client_name": getattr(lead, "full_name", None) or "Client",
        "target_country": getattr(lead, "target_country", None) or "your destination",
        "document_type": context.get("document_type", "document") if context else "document",
        "status": context.get("status", "under review") if context else "under review",
        "score": str(context.get("score", "0")) if context else "0",
        "missing_documents": context.get("missing_documents", "") if context else "",
        "return_link": context.get("return_link", "") if context else "",
    }
    return {
        "trigger": trigger,
        "subject": template["subject"].format(**ctx),
        "body": template["body"].format(**ctx),
    }


def create_auto_communication(
    session: Session,
    lead_id: UUID,
    trigger: str,
    context: dict[str, Any] | None = None,
    due_in_hours: float = 1.0,
) -> FollowUp:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError(f"Lead {lead_id} not found")

    rendered = render_auto_template(trigger, lead, context)
    message = _build_message(trigger, rendered["subject"], rendered["body"])
    now = _utcnow()

    follow_up = FollowUp(
        lead_id=lead_id,
        channel="auto_email",
        message=message,
        status="pending",
        due_at=now + timedelta(hours=due_in_hours),
        created_at=now,
        updated_at=now,
    )
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return follow_up


def list_auto_communications(session: Session, lead_id: UUID | str | None = None) -> list[FollowUp]:
    query = select(FollowUp).where(FollowUp.message.contains(AUTO_PREFIX))
    if lead_id:
        resolved = lead_id if isinstance(lead_id, UUID) else UUID(str(lead_id))
        query = query.where(FollowUp.lead_id == resolved)
    query = query.order_by(FollowUp.created_at.desc())
    return list(session.exec(query).all())


def generate_auto_communications_for_lead(
    session: Session,
    lead_id: UUID,
    trigger: str,
    context: dict[str, Any] | None = None,
) -> list[FollowUp]:
    """Generate one or more auto-communications based on a trigger event."""
    created: list[FollowUp] = []

    if trigger == "intake_submitted":
        created.append(create_auto_communication(session, lead_id, "intake_welcome", context))
    elif trigger == "document_uploaded":
        created.append(create_auto_communication(session, lead_id, "document_received", context))
        # Also queue a missing-documents reminder if relevant.
        missing = context.get("missing_documents") if context else None
        if missing:
            ctx = {"missing_documents": missing, **(context or {})}
            created.append(create_auto_communication(session, lead_id, "missing_documents", ctx, due_in_hours=24))
    elif trigger == "eligibility_ready":
        created.append(create_auto_communication(session, lead_id, "eligibility_update", context))
    elif trigger == "missing_documents":
        created.append(create_auto_communication(session, lead_id, "missing_documents", context, due_in_hours=24))
    else:
        created.append(create_auto_communication(session, lead_id, trigger, context))

    return created

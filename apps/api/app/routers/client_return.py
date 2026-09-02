from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    ApplicationRecord,
    DocumentRecord,
    EligibilityAssessment,
    FollowUp,
    Lead,
    LeadIntent,
)
from app.routers.public_intake import _checklist
from app.schemas import (
    ClientDashboardDocument,
    ClientDashboardFollowUp,
    ClientLookupRequest,
    ClientLookupResult,
    ClientReturnDashboard,
    EligibilityAssessmentRead,
)
from app.models.domain import now_utc
from app.services.eligibility_engine import evaluate_lead_eligibility
from app.services.client_portal import resolve_client_portal_grant

router = APIRouter(prefix="/api/v1/public", tags=["client-return"])


@router.post("/lookup", response_model=list[ClientLookupResult])
def lookup_client_cases(
    payload: ClientLookupRequest,
    session: Session = Depends(get_session),
) -> list[ClientLookupResult]:
    if payload.email or payload.phone:
        raise HTTPException(
            status_code=400,
            detail="Email and phone lookup are disabled. Use an expiring client portal token.",
        )
    if not payload.session_token:
        raise HTTPException(status_code=400, detail="Provide a client portal token")
    try:
        grant = resolve_client_portal_grant(session, payload.session_token)
    except ValueError:
        return []
    lead_ids: set[UUID] = {grant.lead_id}

    if not lead_ids:
        return []

    results: list[ClientLookupResult] = []
    for lead_id in lead_ids:
        lead = session.get(Lead, lead_id)
        if lead is None:
            continue
        results.append(
            ClientLookupResult(
                lead_id=lead.id,
                full_name=lead.full_name,
                email=lead.email,
                phone=lead.phone,
                target_country=lead.target_country,
                status=lead.status.value if hasattr(lead.status, "value") else str(lead.status),
                updated_at=lead.updated_at,
            )
        )
    return results


@router.get("/return/{lead_id}", response_model=ClientReturnDashboard)
def get_client_return_dashboard(
    lead_id: UUID,
    x_gmai_portal_token: str = Header(alias="X-GMAI-Portal-Token"),
    session: Session = Depends(get_session),
) -> ClientReturnDashboard:
    try:
        resolve_client_portal_grant(
            session,
            x_gmai_portal_token,
            expected_lead_id=lead_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Client portal access is invalid or unavailable",
        ) from exc
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    eligibility_row = session.exec(
        select(EligibilityAssessment)
        .where(EligibilityAssessment.lead_id == lead_id)
        .order_by(EligibilityAssessment.created_at.desc())
    ).first()

    documents = list(session.exec(
        select(DocumentRecord)
        .where(DocumentRecord.lead_id == lead_id)
        .order_by(DocumentRecord.created_at.desc())
    ).all())

    follow_ups = list(session.exec(
        select(FollowUp)
        .where(FollowUp.lead_id == lead_id)
        .order_by(FollowUp.created_at.desc())
    ).all())

    application = session.exec(
        select(ApplicationRecord)
        .where(ApplicationRecord.lead_id == lead_id)
        .order_by(ApplicationRecord.created_at.desc())
    ).first()

    # If there is no persisted assessment, run a lightweight in-memory evaluation
    # so the dashboard always has something useful to show.
    eligibility = None
    if eligibility_row:
        eligibility = EligibilityAssessmentRead.from_model(eligibility_row)
    else:
        try:
            fresh = evaluate_lead_eligibility(session, lead_id)
            eligibility = EligibilityAssessmentRead(
                id=UUID(int=0),
                lead_id=lead_id,
                target_country=fresh.get("target_country"),
                domain=fresh.get("domain", "general"),
                overall_score=fresh.get("overall_score", 0.0),
                confidence=fresh.get("confidence", 0.0),
                status=fresh.get("status", "insufficient_profile"),
                summary=fresh.get("summary"),
                risks=fresh.get("risks", []),
                required_documents=fresh.get("required_documents", []),
                pathways=fresh.get("pathways", []),
                factors=fresh.get("factors", {}),
                created_at=now_utc(),
                updated_at=now_utc(),
            )
        except Exception:
            eligibility = None

    checklist = _checklist(
        lead.intent if isinstance(lead.intent, LeadIntent) else LeadIntent.unknown,
        lead.target_country,
    )

    application_stage = None
    if application:
        application_stage = application.status

    required_docs = eligibility.required_documents if eligibility else checklist
    uploaded_doc_types = {d.document_type.lower() for d in documents}
    missing_docs = [
        doc for doc in required_docs
        if not any(dt in doc.lower() for dt in uploaded_doc_types)
    ]

    if lead.status.value == "converted":
        next_action = "Your case is being handled by a consultant."
    elif lead.status.value == "human_review":
        next_action = "Your case is under consultant review."
    elif missing_docs:
        next_action = f"Please upload the following documents: {', '.join(missing_docs[:3])}."
    elif eligibility and eligibility.status in {"needs_documents", "insufficient_profile"}:
        next_action = "Please complete your profile and upload the required documents."
    elif follow_ups and follow_ups[0].status == "pending":
        next_action = "A consultant will reach out to you soon."
    else:
        next_action = "Your case is being reviewed; a consultant will contact you with the next step."

    return ClientReturnDashboard(
        lead_id=lead.id,
        full_name=lead.full_name,
        email=lead.email,
        phone=lead.phone,
        target_country=lead.target_country,
        status=lead.status.value if hasattr(lead.status, "value") else str(lead.status),
        intent=lead.intent.value if hasattr(lead.intent, "value") else str(lead.intent),
        checklist=checklist,
        session_token=None,
        eligibility=eligibility,
        documents=[
            ClientDashboardDocument(
                id=d.id,
                document_type=d.document_type,
                filename=d.filename,
                status=d.status,
                uploaded_at=d.uploaded_at,
            )
            for d in documents
        ],
        follow_ups=[
            ClientDashboardFollowUp(
                id=f.id,
                channel=f.channel,
                status=f.status.value if hasattr(f.status, "value") else str(f.status),
                message=f.message,
                due_at=f.due_at,
            )
            for f in follow_ups
        ],
        application_stage=application_stage,
        next_action=next_action,
        updated_at=lead.updated_at,
    )

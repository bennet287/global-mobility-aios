from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app.core.db import get_session
from app.models.domain import Lead, LeadStatus, ReviewDecision, VerificationAudit
from app.schemas import DashboardSummary, LeadCreate, LeadRead

router = APIRouter()


@router.post("/leads", response_model=LeadRead)
def create_lead(payload: LeadCreate, session: Session = Depends(get_session)) -> Lead:
    lead = Lead(**payload.model_dump())
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


@router.get("/leads", response_model=List[LeadRead])
def list_leads(session: Session = Depends(get_session)) -> list[Lead]:
    return list(session.exec(select(Lead).order_by(Lead.created_at.desc())).all())


@router.get("/leads/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: UUID, session: Session = Depends(get_session)) -> Lead:
    lead = session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/crm/summary", response_model=DashboardSummary)
def dashboard_summary(session: Session = Depends(get_session)) -> DashboardSummary:
    leads_total = session.exec(select(func.count()).select_from(Lead)).one()
    leads_new = session.exec(
        select(func.count()).select_from(Lead).where(Lead.status == LeadStatus.new)
    ).one()
    leads_human_review = session.exec(
        select(func.count()).select_from(Lead).where(Lead.status == LeadStatus.human_review)
    ).one()
    leads_converted = session.exec(
        select(func.count()).select_from(Lead).where(Lead.status == LeadStatus.converted)
    ).one()

    truth_queue_pending = session.exec(
        select(func.count())
        .select_from(VerificationAudit)
        .where(VerificationAudit.review_status == ReviewDecision.pending)
    ).one()
    truth_queue_resolved = session.exec(
        select(func.count())
        .select_from(VerificationAudit)
        .where(VerificationAudit.review_status != ReviewDecision.pending)
    ).one()

    recent_leads = list(session.exec(select(Lead).order_by(Lead.created_at.desc()).limit(8)).all())
    recent_truth_audits = list(
        session.exec(select(VerificationAudit).order_by(VerificationAudit.created_at.desc()).limit(8)).all()
    )

    return DashboardSummary(
        leads_total=leads_total,
        leads_new=leads_new,
        leads_human_review=leads_human_review,
        leads_converted=leads_converted,
        truth_queue_pending=truth_queue_pending,
        truth_queue_resolved=truth_queue_resolved,
        recent_leads=recent_leads,
        recent_truth_audits=recent_truth_audits,
    )

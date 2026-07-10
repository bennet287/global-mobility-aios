from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app.core.db import get_session
from app.models.domain import Lead, LeadStatus, TruthClaim, VerificationStatus
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


def _count(session: Session, statement) -> int:
    return int(session.exec(statement).one() or 0)


def _lead_to_read(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "full_name": lead.full_name,
        "email": lead.email,
        "phone": lead.phone,
        "source": lead.source,
        "intent": lead.intent,
        "target_country": lead.target_country,
        "status": lead.status,
        "notes": lead.notes,
    }


def _truth_claim_to_read(claim: TruthClaim) -> dict:
    return {
        "id": claim.id,
        "lead_id": claim.lead_id,
        "workflow_run_id": claim.workflow_run_id,
        "claim": claim.claim,
        "domain": claim.domain,
        "country": claim.country,
        "verdict": claim.verdict,
        "confidence": claim.confidence,
        "requires_human_review": claim.requires_human_review,
        "explanation": claim.explanation,
        "red_flags_json": claim.red_flags_json,
        "recommended_next_step": claim.recommended_next_step,
        "created_at": claim.created_at,
    }


@router.get("/crm/summary", response_model=DashboardSummary)
def dashboard_summary(session: Session = Depends(get_session)) -> dict:
    leads_total = _count(session, select(func.count()).select_from(Lead))
    leads_new = _count(
        session,
        select(func.count()).select_from(Lead).where(Lead.status == LeadStatus.new),
    )
    leads_human_review = _count(
        session,
        select(func.count()).select_from(Lead).where(Lead.status == LeadStatus.human_review),
    )
    leads_converted = _count(
        session,
        select(func.count()).select_from(Lead).where(Lead.status == LeadStatus.converted),
    )

    truth_queue_pending = _count(
        session,
        select(func.count())
        .select_from(TruthClaim)
        .where(TruthClaim.verdict == VerificationStatus.needs_review),
    )
    truth_queue_resolved = _count(
        session,
        select(func.count())
        .select_from(TruthClaim)
        .where(TruthClaim.verdict != VerificationStatus.needs_review),
    )

    recent_leads = list(
        session.exec(select(Lead).order_by(Lead.created_at.desc()).limit(8)).all()
    )
    recent_truth_audits = list(
        session.exec(select(TruthClaim).order_by(TruthClaim.created_at.desc()).limit(8)).all()
    )

    return {
        "leads_total": leads_total,
        "leads_new": leads_new,
        "leads_human_review": leads_human_review,
        "leads_converted": leads_converted,
        "truth_queue_pending": truth_queue_pending,
        "truth_queue_resolved": truth_queue_resolved,
        "recent_leads": [_lead_to_read(lead) for lead in recent_leads],
        "recent_truth_audits": [_truth_claim_to_read(claim) for claim in recent_truth_audits],
    }

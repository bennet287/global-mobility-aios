import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import get_session
from app.models.domain import SourceReference, TruthClaim, VerificationAudit
from app.schemas import SourceReferenceRead, TruthClaimRead, TruthRequest, TruthResponse
from app.services.official_sources import record_source_check_run, seed_official_sources
from app.services.truth_engine import TruthEngine

router = APIRouter()

@router.post("/truth/verify", response_model=TruthResponse)
def verify_claim(payload: TruthRequest, session: Session = Depends(get_session)) -> TruthResponse:
    seed_official_sources(session, commit=False)
    engine = TruthEngine(strict_mode=settings.truth_engine_strict_mode)
    result = engine.verify(payload)

    audit = VerificationAudit(
        claim=payload.claim,
        domain=payload.domain,
        country=payload.country,
        verdict=result.verdict,
        confidence=result.confidence,
        official_sources_found=len(result.official_sources),
        requires_human_review=result.requires_human_review,
        explanation=result.explanation,
    )
    session.add(audit)

    truth_claim = TruthClaim(
        claim=payload.claim,
        domain=payload.domain,
        country=payload.country,
        verdict=result.verdict,
        confidence=result.confidence,
        requires_human_review=result.requires_human_review,
        explanation=result.explanation,
        red_flags_json=json.dumps(result.red_flags),
        recommended_next_step=result.recommended_next_step,
    )
    session.add(truth_claim)
    session.commit()
    session.refresh(truth_claim)

    for url in result.official_sources:
        session.add(
            SourceReference(
                truth_claim_id=truth_claim.id,
                source_url=url,
                source_type="official",
                country=payload.country,
            )
        )

    record_source_check_run(
        session,
        truth_claim=truth_claim,
        request=payload,
        result=result,
        commit=False,
    )

    session.commit()
    return result

@router.get("/truth/claims", response_model=List[TruthClaimRead])
def list_truth_claims(
    session: Session = Depends(get_session),
    limit: int = 50,
    requires_review: bool | None = None,
) -> list[TruthClaim]:
    statement = select(TruthClaim).order_by(TruthClaim.created_at.desc()).limit(limit)

    if requires_review is not None:
        statement = (
            select(TruthClaim)
            .where(TruthClaim.requires_human_review == requires_review)
            .order_by(TruthClaim.created_at.desc())
            .limit(limit)
        )

    return list(session.exec(statement).all())

@router.get("/truth/claims/{claim_id}", response_model=TruthClaimRead)
def get_truth_claim(claim_id: UUID, session: Session = Depends(get_session)) -> TruthClaim:
    claim = session.get(TruthClaim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Truth claim not found")
    return claim

@router.get("/truth/claims/{claim_id}/sources", response_model=List[SourceReferenceRead])
def list_truth_claim_sources(claim_id: UUID, session: Session = Depends(get_session)) -> list[SourceReference]:
    return list(
        session.exec(
            select(SourceReference)
            .where(SourceReference.truth_claim_id == claim_id)
            .order_by(SourceReference.retrieved_at.desc())
        ).all()
    )

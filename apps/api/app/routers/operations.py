from datetime import timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

import yaml

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.domain import (
    FollowUp,
    FollowUpStatus,
    HumanReview,
    Lead,
    LeadStatus,
    ReviewStatus,
    SourceReference,
    TruthClaim,
    WorkflowRun,
    WorkflowStatus,
    now_utc,
)

router = APIRouter()


class ReviewActionRequest(BaseModel):
    reviewer_notes: Optional[str] = None


def _get_review(session: Session, review_id: UUID) -> HumanReview:
    review = session.get(HumanReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Human review not found")
    return review


def _maybe_create_follow_up(
    session: Session,
    review: HumanReview,
    message: str,
) -> FollowUp | None:
    if not review.lead_id:
        return None

    existing = session.exec(
        select(FollowUp)
        .where(FollowUp.lead_id == review.lead_id)
        .where(FollowUp.workflow_run_id == review.workflow_run_id)
    ).first()

    if existing:
        return existing

    follow_up = FollowUp(
        lead_id=review.lead_id,
        workflow_run_id=review.workflow_run_id,
        channel="email",
        status=FollowUpStatus.pending,
        due_at=now_utc() + timedelta(hours=24),
        message=message,
    )
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return follow_up


def _complete_workflow_if_present(session: Session, review: HumanReview) -> None:
    if not review.workflow_run_id:
        return

    workflow = session.get(WorkflowRun, review.workflow_run_id)
    if workflow:
        workflow.status = WorkflowStatus.completed
        workflow.completed_at = now_utc()
        session.add(workflow)


def _update_lead_status(session: Session, review: HumanReview, status: LeadStatus) -> None:
    if not review.lead_id:
        return

    lead = session.get(Lead, review.lead_id)
    if lead:
        lead.status = status
        lead.updated_at = now_utc()
        session.add(lead)


@router.post("/operations/reviews/{review_id}/approve")
def approve_review(
    review_id: UUID,
    payload: ReviewActionRequest,
    session: Session = Depends(get_session),
) -> dict:
    review = _get_review(session, review_id)

    review.status = ReviewStatus.approved
    review.reviewer_notes = payload.reviewer_notes or "AI truth-check decision approved by human reviewer."
    review.updated_at = now_utc()

    _update_lead_status(session, review, LeadStatus.qualified)
    _complete_workflow_if_present(session, review)

    follow_up = _maybe_create_follow_up(
        session,
        review,
        "Human review approved. Send a corrected, source-grounded explanation to the lead and request missing documents.",
    )

    session.add(review)
    session.commit()
    session.refresh(review)

    return jsonable_encoder(
        {
            "status": "approved",
            "review": review,
            "follow_up": follow_up,
        }
    )


@router.post("/operations/reviews/{review_id}/reject")
def reject_review(
    review_id: UUID,
    payload: ReviewActionRequest,
    session: Session = Depends(get_session),
) -> dict:
    review = _get_review(session, review_id)

    review.status = ReviewStatus.rejected
    review.reviewer_notes = payload.reviewer_notes or "AI truth-check decision rejected by human reviewer. Re-investigation required."
    review.updated_at = now_utc()

    _update_lead_status(session, review, LeadStatus.human_review)

    session.add(review)
    session.commit()
    session.refresh(review)

    return jsonable_encoder(
        {
            "status": "rejected",
            "review": review,
            "next_action": "Re-check official sources and update the truth claim manually.",
        }
    )


@router.post("/operations/reviews/{review_id}/resolve")
def resolve_review(
    review_id: UUID,
    payload: ReviewActionRequest,
    session: Session = Depends(get_session),
) -> dict:
    review = _get_review(session, review_id)

    review.status = ReviewStatus.resolved
    review.reviewer_notes = payload.reviewer_notes or "Human review resolved."
    review.updated_at = now_utc()

    _update_lead_status(session, review, LeadStatus.qualified)
    _complete_workflow_if_present(session, review)

    session.add(review)
    session.commit()
    session.refresh(review)

    return jsonable_encoder(
        {
            "status": "resolved",
            "review": review,
        }
    )


@router.post("/operations/follow-ups/{follow_up_id}/complete")
def complete_follow_up(
    follow_up_id: UUID,
    session: Session = Depends(get_session),
) -> dict:
    follow_up = session.get(FollowUp, follow_up_id)

    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    follow_up.status = FollowUpStatus.completed
    follow_up.updated_at = now_utc()

    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)

    return jsonable_encoder(
        {
            "status": "completed",
            "follow_up": follow_up,
        }
    )
# --- Truth Engine v1.2: official source evidence attachment ---

def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _source_registry_path() -> Path:
    candidates = [
        Path("knowledge/official_sources/sources.yaml"),
        Path("../../knowledge/official_sources/sources.yaml"),
        _project_root() / "knowledge" / "official_sources" / "sources.yaml",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return _project_root() / "knowledge" / "official_sources" / "sources.yaml"


def _normalize_key(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _domain_candidates(domain: str | None) -> list[str]:
    normalized = _normalize_key(domain)

    candidates = []

    if normalized:
        candidates.append(normalized)

    if normalized in {"education", "study", "study_abroad", "scholarship", "recruitment", "job", "overseas_job"}:
        candidates.append("visa")

    candidates.extend(["visa", "general"])

    deduped = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)

    return deduped


def _load_source_registry() -> dict:
    path = _source_registry_path()

    if not path.exists():
        return {}

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _country_node(data: dict, country: str | None) -> dict:
    if not country:
        return {}

    wanted = _normalize_key(country)

    for key, value in data.items():
        if _normalize_key(str(key)) == wanted and isinstance(value, dict):
            return value

    return {}


def _extract_sources(country: str | None, domain: str | None) -> list[dict]:
    data = _load_source_registry()
    node = _country_node(data, country)

    if not node:
        return []

    selected_entries = []

    for domain_key in _domain_candidates(domain):
        entries = node.get(domain_key)

        if isinstance(entries, list):
            selected_entries.extend(entries)

        if selected_entries:
            break

    if not selected_entries:
        for entries in node.values():
            if isinstance(entries, list):
                selected_entries.extend(entries)

    cleaned = []
    seen_urls = set()

    for entry in selected_entries:
        if not isinstance(entry, dict):
            continue

        url = entry.get("url")

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        cleaned.append(
            {
                "url": url,
                "title": entry.get("title"),
                "source_type": entry.get("source_type", "official"),
                "country": country,
            }
        )

    return cleaned


@router.post("/operations/truth-claims/{claim_id}/attach-sources")
def attach_sources_to_truth_claim(
    claim_id: UUID,
    session: Session = Depends(get_session),
) -> dict:
    claim = session.get(TruthClaim, claim_id)

    if not claim:
        raise HTTPException(status_code=404, detail="Truth claim not found")

    official_sources = _extract_sources(claim.country, claim.domain)

    if not official_sources:
        return jsonable_encoder(
            {
                "status": "no_sources_found",
                "truth_claim_id": claim_id,
                "country": claim.country,
                "domain": claim.domain,
                "attached_count": 0,
                "message": "No official sources found in knowledge/official_sources/sources.yaml for this country/domain.",
            }
        )

    existing_refs = session.exec(
        select(SourceReference).where(SourceReference.truth_claim_id == claim_id)
    ).all()

    existing_urls = {ref.source_url for ref in existing_refs}

    attached = []

    for source in official_sources:
        if source["url"] in existing_urls:
            continue

        ref = SourceReference(
            truth_claim_id=claim.id,
            source_url=source["url"],
            source_type=source["source_type"],
            title=source["title"],
            country=claim.country,
        )
        session.add(ref)
        attached.append(ref)

    session.commit()

    for ref in attached:
        session.refresh(ref)

    return jsonable_encoder(
        {
            "status": "attached",
            "truth_claim_id": claim_id,
            "country": claim.country,
            "domain": claim.domain,
            "attached_count": len(attached),
            "skipped_existing_count": len(official_sources) - len(attached),
            "sources": attached,
        }
    )

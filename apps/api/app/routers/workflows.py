import json
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import get_session
from app.models.domain import (
    AgentRun,
    FollowUp,
    HumanReview,
    Lead,
    LeadIntent,
    LeadStatus,
    Profile,
    SourceReference,
    TruthClaim,
    VerificationStatus,
    WorkflowRun,
    WorkflowStatus,
    now_utc,
)
from app.schemas import LeadIntakeWorkflowRequest, LeadIntakeWorkflowResponse, TruthRequest, WorkflowRunRead
from app.services.truth_engine import TruthEngine

router = APIRouter()

def _detect_intent(payload: LeadIntakeWorkflowRequest) -> LeadIntent:
    if payload.intent != LeadIntent.unknown:
        return payload.intent

    text = " ".join(
        part.lower()
        for part in [payload.notes or "", payload.claim or "", payload.target_country or ""]
    )

    if any(term in text for term in ["visa", "immigration", "embassy", "residence permit"]):
        return LeadIntent.visa
    if any(term in text for term in ["job", "work", "employer", "recruitment", "overseas"]):
        return LeadIntent.overseas_job
    if any(term in text for term in ["study", "university", "college", "admission", "scholarship"]):
        return LeadIntent.study_abroad
    if any(term in text for term in ["passport", "transcript", "sop", "lor", "document"]):
        return LeadIntent.document

    return LeadIntent.unknown

def _route(intent: LeadIntent) -> str:
    return {
        LeadIntent.study_abroad: "education",
        LeadIntent.overseas_job: "recruitment",
        LeadIntent.visa: "visa",
        LeadIntent.document: "documents",
        LeadIntent.unknown: "sales_qualification",
    }[intent]

def _json(data: object) -> str:
    return json.dumps(data, default=str)

@router.post("/workflows/lead-intake", response_model=LeadIntakeWorkflowResponse)
def lead_intake_workflow(
    payload: LeadIntakeWorkflowRequest,
    session: Session = Depends(get_session),
) -> LeadIntakeWorkflowResponse:
    detected_intent = _detect_intent(payload)
    route = _route(detected_intent)

    lead = Lead(
        full_name=payload.full_name,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        source=payload.source,
        intent=detected_intent,
        target_country=payload.target_country,
        status=LeadStatus.qualified if detected_intent != LeadIntent.unknown else LeadStatus.new,
        notes=payload.notes,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    workflow_run = WorkflowRun(
        workflow_name="lead_intake",
        lead_id=lead.id,
        status=WorkflowStatus.started,
        detected_intent=detected_intent,
        route=route,
        input_json=payload.model_dump_json(),
    )
    session.add(workflow_run)
    session.commit()
    session.refresh(workflow_run)

    profile = Profile(
        lead_id=lead.id,
        profile_type="mobility",
        target_country=payload.target_country,
        highest_qualification=payload.profile.get("highest_qualification"),
        field_of_study=payload.profile.get("field_of_study"),
        current_country=payload.profile.get("current_country"),
        desired_role=payload.profile.get("desired_role"),
        years_experience=payload.profile.get("years_experience"),
        budget_eur=payload.profile.get("budget_eur"),
        skills_json=_json(payload.profile.get("skills", [])),
        language_scores_json=_json(payload.profile.get("language_scores", {})),
        missing_fields_json=_json(
            [
                field
                for field in ["email", "target_country"]
                if getattr(payload, field) in {None, ""}
            ]
        ),
    )
    session.add(profile)

    session.add(
        AgentRun(
            workflow_run_id=workflow_run.id,
            lead_id=lead.id,
            agent_name="Lead Intake Agent",
            task="Create lead profile and classify intent",
            input_json=payload.model_dump_json(),
            output_json=_json({"detected_intent": detected_intent, "route": route}),
        )
    )
    session.commit()
    session.refresh(profile)

    truth_claim: TruthClaim | None = None
    human_review: HumanReview | None = None
    follow_up: FollowUp | None = None
    next_actions: list[str] = []

    claim_text = payload.claim or _default_claim(detected_intent, payload.target_country)

    if claim_text:
        truth_result = TruthEngine(strict_mode=settings.truth_engine_strict_mode).verify(
            TruthRequest(
                claim=claim_text,
                domain="visa"
                if detected_intent == LeadIntent.visa
                else "study"
                if detected_intent == LeadIntent.study_abroad
                else "job"
                if detected_intent == LeadIntent.overseas_job
                else "general",
                country=payload.target_country,
                source_urls=[],
            )
        )

        truth_claim = TruthClaim(
            lead_id=lead.id,
            workflow_run_id=workflow_run.id,
            claim=claim_text,
            domain="visa" if detected_intent == LeadIntent.visa else route,
            country=payload.target_country,
            verdict=truth_result.verdict,
            confidence=truth_result.confidence,
            requires_human_review=truth_result.requires_human_review,
            explanation=truth_result.explanation,
            red_flags_json=_json(truth_result.red_flags),
            recommended_next_step=truth_result.recommended_next_step,
        )
        session.add(truth_claim)
        session.commit()
        session.refresh(truth_claim)

        for url in truth_result.official_sources:
            session.add(
                SourceReference(
                    truth_claim_id=truth_claim.id,
                    source_url=url,
                    source_type="official",
                    country=payload.target_country,
                )
            )

        session.add(
            AgentRun(
                workflow_run_id=workflow_run.id,
                lead_id=lead.id,
                agent_name="Visa Truth Agent" if detected_intent == LeadIntent.visa else "Reality Checker",
                task="Verify claim against official-source policy",
                input_json=_json({"claim": claim_text, "country": payload.target_country}),
                output_json=truth_result.model_dump_json(),
            )
        )

        if truth_result.requires_human_review or truth_result.verdict in {
            VerificationStatus.rejected,
            VerificationStatus.needs_review,
        }:
            lead.status = LeadStatus.human_review
            human_review = HumanReview(
                lead_id=lead.id,
                truth_claim_id=truth_claim.id,
                workflow_run_id=workflow_run.id,
                review_type="truth_check",
                priority="high" if truth_result.verdict == VerificationStatus.rejected else "medium",
                reason=truth_result.recommended_next_step,
            )
            session.add(human_review)
            workflow_run.status = WorkflowStatus.waiting_for_review
            next_actions.append("Human reviewer must validate the claim before client-facing advice is sent.")
        else:
            follow_up = FollowUp(
                lead_id=lead.id,
                workflow_run_id=workflow_run.id,
                channel="email",
                due_at=now_utc() + timedelta(hours=24),
                message=f"Follow up with {lead.full_name} about the {route} pathway for {payload.target_country or 'their target country' }.",
            )
            session.add(follow_up)
            workflow_run.status = WorkflowStatus.completed
            workflow_run.completed_at = now_utc()
            next_actions.append("Send 24-hour follow-up and request missing documents.")
    else:
        follow_up = FollowUp(
            lead_id=lead.id,
            workflow_run_id=workflow_run.id,
            channel="email",
            due_at=now_utc() + timedelta(hours=24),
            message="Follow up to complete lead qualification and collect target country/pathway details.",
        )
        session.add(follow_up)
        workflow_run.status = WorkflowStatus.completed
        workflow_run.completed_at = now_utc()
        next_actions.append("Complete lead qualification.")

    workflow_run.output_json = _json(
        {
            "lead_id": lead.id,
            "profile_id": profile.id,
            "route": route,
            "truth_claim_id": getattr(truth_claim, "id", None),
            "human_review_id": getattr(human_review, "id", None),
            "follow_up_id": getattr(follow_up, "id", None),
            "next_actions": next_actions,
        }
    )

    session.add(lead)
    session.add(workflow_run)
    session.commit()
    session.refresh(workflow_run)

    if human_review:
        session.refresh(human_review)
    if follow_up:
        session.refresh(follow_up)

    return LeadIntakeWorkflowResponse(
        workflow_run_id=workflow_run.id,
        lead_id=lead.id,
        profile_id=profile.id,
        detected_intent=detected_intent,
        route=route,
        truth_claim_id=getattr(truth_claim, "id", None),
        human_review_id=getattr(human_review, "id", None),
        follow_up_id=getattr(follow_up, "id", None),
        status=workflow_run.status,
        next_actions=next_actions,
    )

@router.get("/workflow-runs", response_model=list[WorkflowRunRead])
def list_workflow_runs(session: Session = Depends(get_session), limit: int = 50) -> list[WorkflowRun]:
    return list(session.exec(select(WorkflowRun).order_by(WorkflowRun.started_at.desc()).limit(limit)).all())

@router.get("/workflow-runs/{workflow_run_id}", response_model=WorkflowRunRead)
def get_workflow_run(workflow_run_id: UUID, session: Session = Depends(get_session)) -> WorkflowRun:
    workflow_run = session.get(WorkflowRun, workflow_run_id)
    if not workflow_run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return workflow_run

def _default_claim(intent: LeadIntent, country: str | None) -> str | None:
    if intent == LeadIntent.visa and country:
        return f"Visa eligibility rules for {country} must be verified from official sources before advice is given."
    if intent == LeadIntent.study_abroad and country:
        return f"Study abroad admission and visa pathway for {country} requires official-source validation."
    if intent == LeadIntent.overseas_job and country:
        return f"Overseas job placement pathway for {country} requires verified work authorization rules."
    return None

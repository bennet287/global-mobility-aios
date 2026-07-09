#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"

if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from sqlmodel import Session, select  # noqa: E402

from app.core.db import create_db_and_tables, engine  # noqa: E402
from app.models.domain import (  # noqa: E402
    AgentRun,
    ApplicationRecord,
    AuditLog,
    DocumentRecord,
    FollowUp,
    FollowUpStatus,
    HumanReview,
    Lead,
    LeadIntent,
    LeadStatus,
    Profile,
    ReviewStatus,
    SourceReference,
    TruthClaim,
    VerificationStatus,
    VisaCheck,
    WorkflowRun,
    WorkflowStatus,
)
from app.services.audit_log import record_audit  # noqa: E402


DEMO_SOURCE = "demo_v3_0"
ONBOARDING_PREFIX = "[post_approval_onboarding:v2.4]"
CLIENT_DRAFT_PREFIX = "[client_communication_draft:v2.6]"
AGENT_OUTPUT_PREFIX = "[agent_output_demo:v4.4]"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _j(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _same_id(a: Any, b: Any) -> bool:
    return str(a or "").replace("-", "").lower() == str(b or "").replace("-", "").lower()


def _delete_rows(session: Session, rows: Iterable[Any]) -> int:
    count = 0
    for row in list(rows):
        session.delete(row)
        count += 1
    return count


def _delete_all_rows(session: Session) -> int:
    total = 0
    for model in (
        AuditLog,
        AgentRun,
        SourceReference,
        HumanReview,
        TruthClaim,
        VisaCheck,
        DocumentRecord,
        ApplicationRecord,
        FollowUp,
        Profile,
        WorkflowRun,
        Lead,
    ):
        total += _delete_rows(session, session.exec(select(model)).all())
    session.commit()
    return total


def _delete_demo_rows(session: Session) -> int:
    demo_leads = session.exec(select(Lead).where(Lead.source == DEMO_SOURCE)).all()
    lead_ids = {getattr(lead, "id", None) for lead in demo_leads}

    workflows = [
        row for row in session.exec(select(WorkflowRun)).all()
        if any(_same_id(getattr(row, "lead_id", None), lead_id) for lead_id in lead_ids)
    ]
    workflow_ids = {getattr(row, "id", None) for row in workflows}
    truth_claims = [
        row for row in session.exec(select(TruthClaim)).all()
        if any(_same_id(getattr(row, "lead_id", None), lead_id) for lead_id in lead_ids)
    ]
    truth_claim_ids = {getattr(row, "id", None) for row in truth_claims}

    total = 0
    total += _delete_rows(session, [
        row for row in session.exec(select(AuditLog)).all()
        if getattr(row, "source", None) == DEMO_SOURCE
        or any(str(getattr(row, "entity_id", "")) == str(lead_id) for lead_id in lead_ids)
    ])
    total += _delete_rows(session, [
        row for row in session.exec(select(AgentRun)).all()
        if any(_same_id(getattr(row, "lead_id", None), lead_id) for lead_id in lead_ids)
        or any(_same_id(getattr(row, "workflow_run_id", None), workflow_id) for workflow_id in workflow_ids)
    ])
    total += _delete_rows(session, [
        row for row in session.exec(select(SourceReference)).all()
        if any(_same_id(getattr(row, "truth_claim_id", None), claim_id) for claim_id in truth_claim_ids)
    ])
    for model in (HumanReview, TruthClaim, VisaCheck, DocumentRecord, ApplicationRecord, FollowUp, Profile, WorkflowRun):
        total += _delete_rows(session, [
            row for row in session.exec(select(model)).all()
            if any(_same_id(getattr(row, "lead_id", None), lead_id) for lead_id in lead_ids)
        ])
    total += _delete_rows(session, demo_leads)
    session.commit()
    return total


def _add_profile(session: Session, lead: Lead, *, profile_type: str, qualification: str, budget: float, skills: Sequence[str]) -> Profile:
    profile = Profile(
        lead_id=lead.id,
        profile_type=profile_type,
        highest_qualification=qualification,
        field_of_study="Computer Science",
        current_country="India",
        target_country=lead.target_country,
        budget_eur=budget,
        skills_json=_j(list(skills)),
        language_scores_json=_j({"IELTS": "6.5"}),
        missing_fields_json="[]",
    )
    session.add(profile)
    return profile


def _add_workflow(session: Session, lead: Lead, *, route: str, status: WorkflowStatus = WorkflowStatus.completed) -> WorkflowRun:
    workflow = WorkflowRun(
        workflow_name="demo_v3_0_journey",
        lead_id=lead.id,
        status=status,
        detected_intent=lead.intent,
        route=route,
        input_json=_j({"source": DEMO_SOURCE}),
        output_json=_j({"demo_stage": route}),
        completed_at=_utcnow() if status == WorkflowStatus.completed else None,
    )
    session.add(workflow)
    return workflow


def _add_truth_claim(
    session: Session,
    lead: Lead,
    workflow: WorkflowRun,
    *,
    claim: str,
    verdict: VerificationStatus,
    requires_review: bool,
    explanation: str,
) -> TruthClaim:
    truth = TruthClaim(
        lead_id=lead.id,
        workflow_run_id=workflow.id,
        claim=claim,
        domain="visa",
        country=lead.target_country,
        verdict=verdict,
        confidence=0.94 if verdict == VerificationStatus.rejected else 0.91,
        requires_human_review=requires_review,
        explanation=explanation,
        red_flags_json=_j(["demo_v3_0"]) if requires_review else "[]",
        recommended_next_step=(
            "Resolve or replace this claim before sales conversion or application drafting."
            if requires_review
            else "Proceed using official-source-backed guidance."
        ),
    )
    session.add(truth)
    session.add(
        SourceReference(
            truth_claim_id=truth.id,
            source_url="https://www.auswaertiges-amt.de/",
            source_type="official",
            title="Official authority guidance",
            country=lead.target_country,
        )
    )
    return truth


def _add_documents(session: Session, lead: Lead, specs: Sequence[tuple[str, str]]) -> List[DocumentRecord]:
    docs = []
    for doc_type, status in specs:
        filename = f"{status.upper()}_{doc_type}.pdf" if status in {"received", "verified"} else f"PENDING_REQUIRED_{doc_type}.txt"
        doc = DocumentRecord(
            lead_id=lead.id,
            document_type=doc_type,
            filename=filename,
            storage_key=f"local://demo-v3-0/{lead.id}/{doc_type}" if status in {"received", "verified"} else None,
            status=status,
            extracted_metadata_json=_j({"seed": DEMO_SOURCE, "document_type": doc_type, "status": status}),
        )
        session.add(doc)
        docs.append(doc)
    return docs


def _add_follow_up(
    session: Session,
    lead: Lead,
    *,
    message: str,
    workflow: WorkflowRun | None = None,
    status: FollowUpStatus = FollowUpStatus.pending,
    channel: str = "email",
    due_offset_days: int = 0,
) -> FollowUp:
    follow_up = FollowUp(
        lead_id=lead.id,
        workflow_run_id=getattr(workflow, "id", None),
        channel=channel,
        status=status,
        due_at=_utcnow() + timedelta(days=due_offset_days),
        message=message,
    )
    session.add(follow_up)
    return follow_up


def _onboarding_message(task_key: str, title: str, body: str, note: str = "Seeded demo v3.0.") -> str:
    return f"{ONBOARDING_PREFIX} task={task_key} title={title} message={body} note={note}"


def _client_draft_message(template: str, title: str, subject: str, body: str, note: str = "Seeded demo v3.0.") -> str:
    return f"{CLIENT_DRAFT_PREFIX} template={template} title={title} subject={subject} body={body} note={note}"


def _audit(session: Session, *, action: str, entity_type: str, entity_id: Any, after_state: Dict[str, Any], reason: str) -> None:
    record_audit(
        session,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=None,
        after_state=after_state,
        reason=reason,
        source=DEMO_SOURCE,
    )


def _add_agent_run(
    session: Session,
    lead: Lead,
    *,
    agent_name: str,
    task: str,
    status: str,
    output: Dict[str, Any],
    workflow: WorkflowRun | None = None,
) -> AgentRun:
    run = AgentRun(
        workflow_run_id=getattr(workflow, "id", None),
        lead_id=lead.id,
        agent_name=agent_name,
        task=task,
        status=status,
        input_json=_j({"source": DEMO_SOURCE, "demo_version": "v4.4", "task": task}),
        output_json=_j({"demo": True, "version": "v4.4", **output}),
    )
    session.add(run)
    _audit(
        session,
        action="controlled_agent_run",
        entity_type="agent_run",
        entity_id=run.id,
        after_state={"agent_name": agent_name, "status": status, "lead_id": str(lead.id)},
        reason=f"Demo controlled agent output seeded as {status}.",
    )
    return run


def _add_agent_review_audit(
    session: Session,
    run: AgentRun,
    *,
    action: str,
    note: str,
) -> None:
    _audit(
        session,
        action=action,
        entity_type="agent_run",
        entity_id=run.id,
        after_state={
            "agent_name": run.agent_name,
            "agent_run_id": str(run.id),
            "status": run.status,
            "note": note,
        },
        reason=note,
    )


def _scenario_blocked_visa_claim(session: Session) -> Lead:
    lead = Lead(
        full_name="Demo 1 - Blocked Visa Claim",
        email="demo.blocked@example.com",
        source=DEMO_SOURCE,
        intent=LeadIntent.visa,
        target_country="Germany",
        status=LeadStatus.human_review,
        notes="Demo: unsafe visa guarantee claim blocks sales and application drafting.",
    )
    session.add(lead)
    _add_profile(session, lead, profile_type="student", qualification="Bachelor degree", budget=8500, skills=["Python", "Cloud"])
    workflow = _add_workflow(session, lead, route="blocked_truth", status=WorkflowStatus.waiting_for_review)
    truth = _add_truth_claim(
        session,
        lead,
        workflow,
        claim="Germany student visa is guaranteed without financial proof.",
        verdict=VerificationStatus.rejected,
        requires_review=True,
        explanation="Unsafe claim. Visa outcomes cannot be guaranteed and financial proof is normally required.",
    )
    session.add(
        HumanReview(
            lead_id=lead.id,
            truth_claim_id=truth.id,
            workflow_run_id=workflow.id,
            review_type="truth_check",
            status=ReviewStatus.pending,
            priority="high",
            reason="Rejected visa claim requires human review before progression.",
        )
    )
    _add_documents(session, lead, [("passport", "verified"), ("financial_proof", "missing")])
    _add_follow_up(session, lead, workflow=workflow, message="Explain that visa approval cannot be guaranteed and request official financial proof.")
    _audit(session, action="truth_claim_rejected", entity_type="truth_claim", entity_id=truth.id, after_state={"lead": lead.full_name}, reason="Demo rejected visa claim.")
    run = _add_agent_run(
        session,
        lead,
        workflow=workflow,
        agent_name="truth_explanation_agent",
        task="Explain why the unsafe visa guarantee claim is blocked.",
        status="rejected",
        output={
            "summary": "Unsafe visa guarantee explanation was rejected for client-facing use.",
            "blocked_actions": ["client_send", "legal_advice"],
            "conversion_target": "no conversion target",
        },
    )
    _add_agent_review_audit(session, run, action="agent_output_rejected", note="Rejected for demo: explanation requires reviewer rewrite.")
    return lead


def _scenario_documents_pending(session: Session) -> Lead:
    lead = Lead(
        full_name="Demo 2 - Documents Pending",
        email="demo.documents@example.com",
        source=DEMO_SOURCE,
        intent=LeadIntent.study_abroad,
        target_country="Austria",
        status=LeadStatus.needs_documents,
        notes="Demo: truth is clear, but application is blocked by missing documents.",
    )
    session.add(lead)
    _add_profile(session, lead, profile_type="student", qualification="Bachelor degree", budget=12000, skills=["Data Analysis", "German A2"])
    workflow = _add_workflow(session, lead, route="documents_pending")
    truth = _add_truth_claim(
        session,
        lead,
        workflow,
        claim="Austria study applications require document completeness checks before submission.",
        verdict=VerificationStatus.verified,
        requires_review=False,
        explanation="General document readiness guidance verified for demo workflow.",
    )
    _add_documents(session, lead, [("passport", "verified"), ("admission_letter", "missing"), ("financial_proof", "missing"), ("insurance", "needs_review")])
    _add_follow_up(session, lead, workflow=workflow, message="Request admission letter, financial proof, and insurance clarification.")
    _audit(session, action="document_received", entity_type="lead", entity_id=lead.id, after_state={"lead": lead.full_name, "truth_claim_id": str(truth.id)}, reason="Demo documents pending state.")
    _add_agent_run(
        session,
        lead,
        workflow=workflow,
        agent_name="document_checklist_agent",
        task="Summarize missing document blockers for the operator.",
        status="completed",
        output={
            "summary": "Admission letter and financial proof are missing; insurance needs review.",
            "missing_documents": ["admission_letter", "financial_proof", "insurance"],
            "conversion_target": "no conversion target",
        },
    )
    return lead


def _scenario_ready_for_application(session: Session) -> Lead:
    lead = Lead(
        full_name="Demo 3 - Ready For Application",
        email="demo.ready@example.com",
        source=DEMO_SOURCE,
        intent=LeadIntent.study_abroad,
        target_country="Canada",
        status=LeadStatus.qualified,
        notes="Demo: truth clear and all documents verified, ready for controlled application draft.",
    )
    session.add(lead)
    _add_profile(session, lead, profile_type="student", qualification="Bachelor degree", budget=18000, skills=["AI", "Cybersecurity"])
    workflow = _add_workflow(session, lead, route="ready_for_application")
    _add_truth_claim(
        session,
        lead,
        workflow,
        claim="Canada study pathway requires a complete application package and review before submission.",
        verdict=VerificationStatus.verified,
        requires_review=False,
        explanation="Demo official-source-backed guidance is clear.",
    )
    docs = _add_documents(session, lead, [("passport", "verified"), ("admission_letter", "verified"), ("financial_proof", "verified"), ("english_test", "verified")])
    for doc in docs:
        _audit(session, action="document_verified", entity_type="document", entity_id=doc.id, after_state={"document_type": doc.document_type}, reason="Demo ready document.")
    run = _add_agent_run(
        session,
        lead,
        workflow=workflow,
        agent_name="application_readiness_agent",
        task="Explain why this lead is ready for controlled application drafting.",
        status="approved",
        output={
            "summary": "Truth is clear and required documents are verified. Operator may create a controlled draft.",
            "truth_clear": True,
            "documents_verified": True,
            "ready_for_operator_review": True,
            "ready_for_submission": False,
            "conversion_target": "no conversion target",
        },
    )
    _add_agent_review_audit(session, run, action="agent_output_approved", note="Approved for demo: readiness explanation is safe for internal use.")
    return lead


def _scenario_completed_journey(session: Session) -> Lead:
    lead = Lead(
        full_name="Demo 4 - Completed Journey",
        email="demo.completed@example.com",
        source=DEMO_SOURCE,
        intent=LeadIntent.overseas_job,
        target_country="Australia",
        status=LeadStatus.converted,
        notes="Demo: authority approved, onboarding complete, client communications reviewed.",
    )
    session.add(lead)
    _add_profile(session, lead, profile_type="worker", qualification="Master degree", budget=22000, skills=["Project Management", "Cloud Operations"])
    workflow = _add_workflow(session, lead, route="completed_journey")
    _add_truth_claim(
        session,
        lead,
        workflow,
        claim="Australia work pathway requires authority decision tracking and post-approval onboarding.",
        verdict=VerificationStatus.verified,
        requires_review=False,
        explanation="Demo completed journey claim is verified.",
    )
    _add_documents(session, lead, [("passport", "verified"), ("job_offer", "verified"), ("financial_proof", "verified"), ("insurance", "verified")])
    app = ApplicationRecord(
        lead_id=lead.id,
        domain="overseas_job",
        target_country=lead.target_country,
        target_institution_or_employer="Demo Employer Pty Ltd",
        status="approved_by_authority",
        risk_score=0.15,
    )
    session.add(app)
    _audit(session, action="application_drafted", entity_type="application", entity_id=app.id, after_state={"status": "draft"}, reason="Demo journey draft.")
    _audit(session, action="authority_decision_recorded", entity_type="application", entity_id=app.id, after_state={"status": "approved_by_authority"}, reason="Demo authority approval.")

    onboarding_tasks = [
        ("confirm_authority_approval", "Confirm authority approval details", "Authority approval reference and validity were confirmed."),
        ("send_client_next_steps", "Send client post-approval next steps", "Client received post-approval checklist."),
        ("collect_travel_plan", "Collect travel plan", "Travel plan and arrival city collected."),
        ("verify_accommodation_arrival", "Verify accommodation and arrival plan", "Accommodation and arrival plan verified."),
        ("confirm_insurance_and_documents", "Confirm insurance and travel documents", "Insurance and travel documents confirmed."),
        ("local_registration_guidance", "Prepare local registration guidance", "Local registration guidance prepared."),
    ]
    for task_key, title, body in onboarding_tasks:
        task = _add_follow_up(
            session,
            lead,
            workflow=workflow,
            status=FollowUpStatus.completed,
            message=_onboarding_message(task_key, title, body),
        )
        _audit(session, action="onboarding_task_completed", entity_type="follow_up", entity_id=task.id, after_state={"task_key": task_key}, reason="Demo onboarding complete.")

    client_drafts = [
        ("approval_confirmation", "Approval confirmation", "Your application has been approved - next steps", "Congratulations - your application has been approved."),
        ("post_approval_next_steps", "Post-approval next steps", "Post-approval next steps checklist", "Please prepare using the post-approval checklist."),
        ("travel_checklist", "Travel checklist", "Travel preparation checklist", "Please share travel details before departure."),
        ("document_checklist", "Post-approval document checklist", "Documents to carry after approval", "Please carry passport, approval, insurance, and job documents."),
        ("local_registration_guidance", "Local registration guidance", "Arrival and local registration guidance", "Please follow official local registration instructions."),
    ]
    for template, title, subject, body in client_drafts:
        draft = _add_follow_up(
            session,
            lead,
            workflow=workflow,
            status=FollowUpStatus.completed,
            channel="email_draft",
            message=_client_draft_message(template, title, subject, body),
        )
        _audit(session, action="client_draft_reviewed", entity_type="follow_up", entity_id=draft.id, after_state={"template": template}, reason="Demo communication reviewed.")
    run = _add_agent_run(
        session,
        lead,
        workflow=workflow,
        agent_name="client_drafting_agent",
        task="Draft a final post-approval update for the client.",
        status="converted",
        output={
            "draft_subject": "Your approved application - final travel reminder",
            "draft_body": "Please keep your approval letter, passport, insurance, and arrival documents ready.",
            "send_allowed": False,
            "conversion_target": "client communication draft",
        },
    )
    converted = _add_follow_up(
        session,
        lead,
        workflow=workflow,
        status=FollowUpStatus.pending,
        channel="email_draft",
        message=(
            f"{AGENT_OUTPUT_PREFIX} source_agent_run={run.id} subject=Your approved application - final travel reminder "
            "body=Please keep your approval letter, passport, insurance, and arrival documents ready."
        ),
    )
    _audit(
        session,
        action="agent_output_converted_to_client_draft",
        entity_type="follow_up",
        entity_id=converted.id,
        after_state={"agent_run_id": str(run.id), "follow_up_status": "pending"},
        reason="Demo converted approved client drafting output into a pending communication draft.",
    )
    return lead


def seed_demo_data(session: Session, *, reset_demo: bool = True, reset_all: bool = False) -> Dict[str, Any]:
    deleted = _delete_all_rows(session) if reset_all else (_delete_demo_rows(session) if reset_demo else 0)

    leads = [
        _scenario_blocked_visa_claim(session),
        _scenario_documents_pending(session),
        _scenario_ready_for_application(session),
        _scenario_completed_journey(session),
    ]
    session.commit()

    for lead in leads:
        session.refresh(lead)

    demo_agent_runs = [
        run for run in session.exec(select(AgentRun)).all()
        if any(_same_id(getattr(run, "lead_id", None), getattr(lead, "id", None)) for lead in leads)
    ]
    agent_status_counts: Dict[str, int] = {}
    for run in demo_agent_runs:
        agent_status_counts[run.status] = agent_status_counts.get(run.status, 0) + 1

    return {
        "status": "seeded",
        "demo_source": DEMO_SOURCE,
        "demo_version": "v4.4",
        "deleted_rows": deleted,
        "demo_leads": len(leads),
        "demo_agent_runs": len(demo_agent_runs),
        "agent_status_counts": agent_status_counts,
        "lead_ids": [str(lead.id) for lead in leads],
        "scenarios": [
            "blocked_visa_claim",
            "documents_pending",
            "ready_for_application",
            "completed_journey",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Global Mobility AIOS demo data v4.4.")
    parser.add_argument("--no-reset-demo", action="store_true", help="Do not delete existing demo_v3_0 rows before seeding.")
    parser.add_argument("--reset-all", action="store_true", help="Delete all local rows before seeding demo data.")
    parser.add_argument("--yes", action="store_true", help="Required with --reset-all.")
    args = parser.parse_args()

    if args.reset_all and not args.yes:
        print("Refusing --reset-all without --yes. This protects non-demo local data.")
        return 2

    create_db_and_tables()
    with Session(engine) as session:
        summary = seed_demo_data(
            session,
            reset_demo=not args.no_reset_demo,
            reset_all=args.reset_all,
        )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

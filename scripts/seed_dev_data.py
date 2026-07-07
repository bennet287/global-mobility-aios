from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"

if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from sqlmodel import Session  # noqa: E402

from app.core.db import create_db_and_tables, engine  # noqa: E402
from app.models.domain import (  # noqa: E402
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
)

def main() -> None:
    create_db_and_tables()

    with Session(engine) as session:
        lead = Lead(
            full_name="Demo Visa Lead",
            email="demo.visa@example.com",
            source="seed",
            intent=LeadIntent.visa,
            target_country="Germany",
            status=LeadStatus.human_review,
            notes="Interested in a Germany study pathway and visa requirements.",
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)

        profile = Profile(
            lead_id=lead.id,
            profile_type="student",
            target_country="Germany",
            highest_qualification="Bachelor's degree",
            field_of_study="Computer Science",
            budget_eur=12000,
            skills_json=json.dumps(["Python", "Cloud", "Cybersecurity"]),
            language_scores_json=json.dumps({"IELTS": "6.5"}),
        )
        session.add(profile)

        workflow = WorkflowRun(
            workflow_name="lead_intake",
            lead_id=lead.id,
            status=WorkflowStatus.waiting_for_review,
            detected_intent=LeadIntent.visa,
            route="visa",
            input_json=json.dumps({"source": "seed"}),
            output_json=json.dumps({"next_actions": ["Human review required"]}),
        )
        session.add(workflow)
        session.commit()
        session.refresh(workflow)

        claim = TruthClaim(
            lead_id=lead.id,
            workflow_run_id=workflow.id,
            claim="Germany student visa is guaranteed without financial proof.",
            domain="visa",
            country="Germany",
            verdict=VerificationStatus.rejected,
            confidence=0.95,
            requires_human_review=True,
            explanation="High-risk visa misinformation wording detected.",
            red_flags_json=json.dumps(["guaranteed visa", "without financial proof"]),
            recommended_next_step="Reject and replace with official-source-based explanation.",
        )
        session.add(claim)
        session.commit()
        session.refresh(claim)

        session.add(
            SourceReference(
                truth_claim_id=claim.id,
                source_url="https://www.auswaertiges-amt.de/",
                source_type="official",
                title="Federal Foreign Office",
                country="Germany",
            )
        )

        session.add(
            HumanReview(
                lead_id=lead.id,
                truth_claim_id=claim.id,
                workflow_run_id=workflow.id,
                review_type="truth_check",
                priority="high",
                reason="High-risk visa claim requires human validation.",
            )
        )

        session.add(
            FollowUp(
                lead_id=lead.id,
                workflow_run_id=workflow.id,
                channel="email",
                status="pending",
                message="Request official documents and clarify financial proof requirements.",
            )
        )

        session.add(
            AgentRun(
                workflow_run_id=workflow.id,
                lead_id=lead.id,
                agent_name="Visa Truth Agent",
                task="Verify high-risk visa claim",
                status="completed",
                output_json=json.dumps({"verdict": "REJECTED", "confidence": 0.95}),
            )
        )

        session.commit()

    print("Seeded MVP-1 demo data.")

if __name__ == "__main__":
    main()

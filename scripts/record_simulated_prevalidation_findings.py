#!/usr/bin/env python3
"""Record simulated pre-validation findings for Phase 13.15.

This is NOT an external human validation run. It is an internal shadow run to
preserve the pre-fix baseline for the Austria intake and pathway-discovery UX.
It does NOT create external human reviews and therefore does NOT satisfy the
external-validation gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

API_PATH = Path(__file__).resolve().parents[1] / "apps" / "api"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from sqlmodel import Session, select  # noqa: E402

from app.core.db import engine, register_models  # noqa: E402
from app.models.domain import (  # noqa: E402
    Jurisdiction,
    Lead,
    LeadIntent,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    PathwayComparisonAssessment,
    SourceSnapshot,
    VerifiedRule,
)
from app.schemas import ExternalValidationFindingCreate, ExternalValidationRunCreate  # noqa: E402
from app.services.external_validation import (  # noqa: E402
    create_external_validation_finding,
    create_external_validation_run,
    seed_default_external_validation_scenario,
)


SIMULATED_ACTOR = "simulated-prevalidation-pipeline"


def _ensure_jurisdiction_at(session: Session) -> Jurisdiction:
    jurisdiction = session.exec(
        select(Jurisdiction).where(Jurisdiction.code == "AT")
    ).first()
    if jurisdiction is None:
        jurisdiction = Jurisdiction(code="AT", name="Austria", region="Europe")
        session.add(jurisdiction)
        session.commit()
        session.refresh(jurisdiction)
    return jurisdiction


def _synthetic_evidence_graph(session: Session) -> dict[str, object]:
    """Create a minimal but internally consistent evidence graph for a shadow run."""
    jurisdiction = _ensure_jurisdiction_at(session)

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="austria",
        domain="work",
        name="Austria simulated pre-validation source",
        url="https://example.invalid/simulated-prevalidation",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="simulated-prevalidation-at-snapshot",
        content_text="Shadow snapshot used only for internal simulated validation finding ledger.",
        status="captured",
        retrieval_method="manual",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    rule = VerifiedRule(
        country="austria",
        domain="work",
        rule_key="at-prevalidation-shadow-rule",
        statement="Simulated pre-validation rule statement.",
        official_source_id=source.id,
        jurisdiction_id=jurisdiction.id,
        source_snapshot_id=snapshot.id,
        confidence=0.95,
        active=True,
        approved_by="simulated-prevalidation-reviewer",
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)

    pathway = MobilityPathway(
        pathway_key="at-prevalidation-shadow-pathway",
        name="Austria shadow pre-validation pathway",
        country="austria",
        domain="work",
        jurisdiction_id=jurisdiction.id,
        catalogue_status="draft",
        created_by="simulated-prevalidation-pipeline",
    )
    session.add(pathway)
    session.commit()
    session.refresh(pathway)

    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="draft",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=json.dumps([str(rule.id)]),
        eligibility_criteria_json=json.dumps({}),
        required_documents_json=json.dumps([]),
        created_by="simulated-prevalidation-pipeline",
        approved_by=None,
        human_review_required=True,
    )
    session.add(version)
    session.commit()
    session.refresh(version)

    lead = Lead(
        full_name="Simulated Pre-Validation Tester",
        email="simulated.prevalidation@example.invalid",
        intent=LeadIntent.overseas_job,
        target_country="Austria",
        source="simulated-prevalidation",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)

    comparison = PathwayComparisonAssessment(
        lead_id=lead.id,
        primary_pathway_id=pathway.id,
        primary_pathway_version_id=version.id,
        status="incomplete",
        comparison_json=json.dumps({"shadow": True}),
        human_review_required=True,
        generated_by="simulated-prevalidation-pipeline",
    )
    session.add(comparison)
    session.commit()
    session.refresh(comparison)

    return {
        "jurisdiction": jurisdiction,
        "source": source,
        "snapshot": snapshot,
        "rule": rule,
        "pathway": pathway,
        "version": version,
        "lead": lead,
        "comparison": comparison,
    }


def main() -> int:
    register_models()

    findings_data = [
        {
            "severity": "critical",
            "category": "intake_country_coverage",
            "title": "Austria is not selectable in public intake",
            "description": (
                "The public-intake country dropdown lists Germany, Canada, Australia, UK, USA, and Other. "
                "Austria is not present. A real mobility user considering Austria skilled employment cannot "
                "start a case without assistance, so the Austria validation scenario is unreachable through "
                "the primary front door."
            ),
        },
        {
            "severity": "high",
            "category": "intake_case_facts",
            "title": "Intake lacks Austria skilled-employment material facts",
            "description": (
                "When Austria becomes selectable, the intake form still does not collect job-offer status, "
                "occupation, qualification-recognition state, or German-language level. These facts are material "
                "to Austria skilled-employment routing and create the next blocker after country selection."
            ),
        },
        {
            "severity": "medium",
            "category": "post_intake_messaging",
            "title": "Post-intake success message is generic",
            "description": (
                "After intake the page says 'A consultant will review it shortly' with no Austria-specific "
                "next step, expected timing, or self-service action. The user is left without direction."
            ),
        },
        {
            "severity": "medium",
            "category": "eligibility_evidence_communication",
            "title": "Eligibility preview does not surface source traceability to users",
            "description": (
                "The eligibility preview page includes a good disclaimer but does not show the official source, "
                "immutable snapshot, or verified rule behind each recommendation. A user cannot verify claims."
            ),
        },
        {
            "severity": "high",
            "category": "pathway_provenance",
            "title": "Source provenance is shown only as truncated UUIDs",
            "description": (
                "The planning/pathway comparison cards display provenance as 'Source abc12345' / 'Snapshot def67890'. "
                "A professional cannot determine the actual source URL, title, capture date, or regulatory year from "
                "these truncated identifiers."
            ),
        },
        {
            "severity": "high",
            "category": "pathway_version_transparency",
            "title": "Pathway-version display omits approval and lifecycle metadata",
            "description": (
                "The comparison card shows 'version N' but not whether the version is published, draft, approved, "
                "or by whom. Professional trust requires explicit lifecycle and approval identity."
            ),
        },
        {
            "severity": "medium",
            "category": "occupation_evidence",
            "title": "No shortage-occupation list or occupation matching visible",
            "description": (
                "The user-facing flow does not surface Austria national or regional shortage-occupation lists, "
                "nor an occupation-matching step. A user cannot understand whether their occupation may be relevant "
                "to the Austria skilled-employment route."
            ),
        },
    ]

    with Session(engine) as session:
        scenario = seed_default_external_validation_scenario(session, actor=SIMULATED_ACTOR)
        graph = _synthetic_evidence_graph(session)

        run = create_external_validation_run(
            session,
            ExternalValidationRunCreate(
                run_key=f"simulated-prevalidation-{uuid4().hex[:8]}",
                scenario_id=scenario.id,
                lead_id=graph["lead"].id,
                pathway_comparison_assessment_id=graph["comparison"].id,
                founder_intervention_count=2,
            ),
            actor=SIMULATED_ACTOR,
        )
        print(f"Created simulated pre-validation run: {run.run_key} ({run.id})")

        for item in findings_data:
            finding = create_external_validation_finding(
                session,
                run.id,
                ExternalValidationFindingCreate(**item),
                actor=SIMULATED_ACTOR,
            )
            print(f"  Created {finding.severity} finding: {finding.title}")

        print(
            "\nThis run does NOT include external human reviews and does NOT satisfy the "
            "external-validation gate. It is a pre-fix baseline for remediation tracking only."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

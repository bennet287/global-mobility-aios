from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.models.domain import (
    BusinessMobilityAdvisoryAssessment,
    DocumentRecord,
    FamilyOfficeMobilityAssessment,
    FamilyOfficeMobilityReview,
    InvestmentMobilityProgram,
    InvestmentMobilityProgramVersion,
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
)
from app.schemas_family_office_mobility import (
    FamilyOfficeAssessmentCreate,
    FamilyOfficeAssessmentRead,
    FamilyOfficeReviewCreate,
    FamilyOfficeWorkstream,
)
from app.services.audit_log import record_audit, to_audit_dict


SCORE_SEMANTICS = (
    "Family-office execution readiness from disclosed identity, controlled wealth evidence, "
    "beneficial-ownership transparency, adviser governance, screening posture, and independently "
    "published mobility intelligence. It is not an eligibility or approval probability, tax or "
    "legal opinion, banking assurance, investment recommendation, or asset-protection guarantee."
)

ALLOWED_PATHWAY_DOMAINS = {
    "investment", "wealth", "business", "entrepreneur", "startup", "tax", "corporate",
}
WEALTH_DOCUMENT_TYPES = {
    "bank_statement", "source_of_funds", "source_of_wealth", "tax_return",
    "audited_accounts", "business_ownership", "share_register", "trust_deed",
}
PROHIBITED_SIGNALS = {
    "hide ownership", "conceal ownership", "conceal funds", "nominee owner",
    "fake document", "forge", "backdate", "evade tax", "avoid sanctions",
    "bypass sanctions", "sham company", "misrepresent beneficial owner",
}


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def _load(value: str | None, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _band(score: float) -> str:
    if score >= 80:
        return "execution_ready"
    if score >= 60:
        return "workable_with_controls"
    if score >= 40:
        return "material_gaps"
    return "not_ready"


def family_office_read(row: FamilyOfficeMobilityAssessment) -> FamilyOfficeAssessmentRead:
    return FamilyOfficeAssessmentRead(
        **row.model_dump(),
        workstreams=[
            FamilyOfficeWorkstream.model_validate(value)
            for value in _load(row.workstreams_json, [])
        ],
        blockers=_load(row.blockers_json, []),
        next_actions=_load(row.next_actions_json, []),
        evidence_basis=_load(row.evidence_basis_json, []),
        grounded_pathway_versions=_load(row.grounded_pathway_versions_json, []),
        grounded_program_versions=_load(row.grounded_program_versions_json, []),
        escalation_flags=_load(row.escalation_flags_json, []),
        score_semantics=SCORE_SEMANTICS,
    )


def _grounding(session: Session, targets: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pathway_grounding: list[dict[str, Any]] = []
    pathways = session.exec(select(MobilityPathway).where(
        MobilityPathway.catalogue_status == "active"
    )).all()
    for pathway in pathways:
        if pathway.country.strip().lower() not in targets or pathway.domain not in ALLOWED_PATHWAY_DOMAINS:
            continue
        version = session.exec(select(MobilityPathwayVersion).where(
            MobilityPathwayVersion.pathway_id == pathway.id,
            MobilityPathwayVersion.lifecycle_status == "published",
        ).order_by(MobilityPathwayVersion.version_number.desc())).first()
        if version:
            pathway_grounding.append({
                "pathway_id": str(pathway.id),
                "pathway_version_id": str(version.id),
                "name": pathway.name,
                "country": pathway.country,
                "domain": pathway.domain,
                "source_snapshot_id": str(version.source_snapshot_id) if version.source_snapshot_id else None,
            })

    program_grounding: list[dict[str, Any]] = []
    programs = session.exec(select(InvestmentMobilityProgram).where(
        InvestmentMobilityProgram.catalogue_status == "active"
    )).all()
    for program in programs:
        if program.country.strip().lower() not in targets:
            continue
        version = session.exec(select(InvestmentMobilityProgramVersion).where(
            InvestmentMobilityProgramVersion.program_id == program.id,
            InvestmentMobilityProgramVersion.lifecycle_status == "published",
        ).order_by(InvestmentMobilityProgramVersion.version_number.desc())).first()
        if version:
            program_grounding.append({
                "program_id": str(program.id),
                "program_version_id": str(version.id),
                "name": program.name,
                "country": program.country,
                "program_type": program.program_type,
                "pathway_version_id": str(version.pathway_version_id),
                "source_snapshot_id": str(version.source_snapshot_id),
            })
    return pathway_grounding, program_grounding


def create_family_office_assessment(
    session: Session,
    payload: FamilyOfficeAssessmentCreate,
    *,
    actor: str,
) -> FamilyOfficeMobilityAssessment:
    lead = session.get(Lead, payload.lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    advisory = (
        session.get(BusinessMobilityAdvisoryAssessment, payload.business_advisory_assessment_id)
        if payload.business_advisory_assessment_id else None
    )
    if payload.business_advisory_assessment_id and advisory is None:
        raise ValueError("Business mobility advisory not found")
    if advisory and advisory.lead_id != lead.id:
        raise ValueError("Business mobility advisory must belong to the selected lead")
    if advisory and advisory.primary_intent not in {
        "family_office_relocation", "asset_and_family_mobility",
        "tax_residency_planning", "passive_investment",
    }:
        raise ValueError("Business mobility advisory is not a family-office or wealth assessment")

    documents: list[DocumentRecord] = []
    for document_id in payload.document_record_ids:
        document = session.get(DocumentRecord, document_id)
        if document is None:
            raise ValueError("Family-office evidence document not found")
        if document.lead_id != lead.id:
            raise ValueError("Family-office evidence documents must belong to the selected lead")
        documents.append(document)
    verified_documents = [document for document in documents if document.status == "verified"]
    verified_wealth_documents = [
        document for document in verified_documents
        if document.document_type.strip().lower() in WEALTH_DOCUMENT_TYPES
    ]

    targets = {value.strip().lower() for value in payload.target_jurisdictions}
    pathways, programs = _grounding(session, targets)
    blockers: list[str] = []
    actions: list[str] = []
    escalation_flags: list[str] = []

    identity_score = min(
        100.0,
        20.0
        + (20.0 if payload.citizenships else 0.0)
        + (20.0 if payload.current_tax_residencies else 0.0)
        + min(40.0, len(verified_documents) * 10.0),
    )
    if not payload.citizenships:
        blockers.append("Principal and family citizenships are not recorded.")
    if not payload.current_tax_residencies:
        blockers.append("Current tax residencies are not recorded for specialist review.")

    evidence_values = {"unconfirmed": 0.0, "documented": 45.0, "independently_verified": 70.0}
    wealth_evidence_score = min(
        100.0,
        (
            evidence_values[payload.source_of_wealth_status]
            + evidence_values[payload.source_of_funds_status]
        ) / 2
        + min(30.0, len(verified_wealth_documents) * 10.0),
    )
    if payload.source_of_wealth_status == "unconfirmed":
        blockers.append("Source of wealth is unconfirmed.")
    if payload.source_of_funds_status == "unconfirmed":
        blockers.append("Source of funds is unconfirmed.")
    if (
        "independently_verified" in {
            payload.source_of_wealth_status, payload.source_of_funds_status
        }
        and not verified_wealth_documents
    ):
        wealth_evidence_score = min(wealth_evidence_score, 45.0)
        blockers.append("An independently verified wealth status was declared without a linked verified wealth document.")

    disclosed_structures = sum(
        1 for structure in payload.structures if structure.beneficial_ownership_disclosed
    )
    structure_ratio = disclosed_structures / len(payload.structures) if payload.structures else 0.0
    ownership_transparency_score = (
        (40.0 if payload.beneficial_ownership_documented else 0.0)
        + (20.0 if payload.structures else 0.0)
        + structure_ratio * 40.0
    )
    if not payload.beneficial_ownership_documented:
        blockers.append("Ultimate beneficial ownership is not yet documented.")
    if not payload.structures:
        blockers.append("No entity, trust, foundation, or holding structure inventory is recorded.")
    elif disclosed_structures != len(payload.structures):
        blockers.append("One or more structures do not have disclosed beneficial ownership.")

    governance_score = (
        (20.0 if payload.screening_status == "cleared" else 5.0)
        + (20.0 if payload.tax_adviser_engaged else 0.0)
        + (20.0 if payload.legal_adviser_engaged else 0.0)
        + (20.0 if payload.succession_plan_documented else 0.0)
        + (20.0 if payload.banking_relationships_confirmed else 0.0)
    )
    if payload.screening_status != "cleared":
        blockers.append("PEP and sanctions screening is not cleared.")
        escalation_flags.append(f"screening_{payload.screening_status}")
    if payload.pep_or_sanctions_exposure_disclosed:
        escalation_flags.append("pep_or_sanctions_exposure_disclosed")
        actions.append("Route disclosed PEP or sanctions exposure to enhanced due diligence before execution.")
    if not payload.tax_adviser_engaged:
        actions.append("Engage a qualified cross-border tax adviser for residence, reporting, treaty, and exit analysis.")
    if not payload.legal_adviser_engaged:
        actions.append("Engage qualified counsel for ownership, succession, family, and mobility implementation.")
    if not payload.succession_plan_documented:
        actions.append("Document succession, incapacity, guardianship, and control-continuity requirements.")
    if not payload.banking_relationships_confirmed:
        actions.append("Pre-clear banking, custody, onboarding, and liquidity requirements with regulated institutions.")

    mobility_grounding_score = min(
        100.0,
        (60.0 if pathways else 0.0) + (40.0 if programs else 0.0),
    )
    if not pathways:
        blockers.append("No independently published business, wealth, investment, tax, or corporate pathway matches the target jurisdictions.")
    if not programs:
        actions.append("Do not treat capital thresholds as a route; complete independently reviewed program onboarding where required.")

    narrative = " ".join(payload.disclosed_constraints).lower()
    prohibited = [signal for signal in PROHIBITED_SIGNALS if signal in narrative]
    if prohibited:
        escalation_flags.append("concealment_evasion_or_misrepresentation_signal")
        blockers.append("A concealment, evasion, sanctions-circumvention, document, or ownership-misrepresentation signal prevents operationalization.")

    component_scores = [
        identity_score, wealth_evidence_score, ownership_transparency_score,
        governance_score, mobility_grounding_score,
    ]
    readiness_score = round(sum(component_scores) / len(component_scores), 1)
    if payload.screening_status != "cleared" or not payload.beneficial_ownership_documented:
        readiness_score = min(readiness_score, 55.0)
    if prohibited:
        readiness_score = min(readiness_score, 20.0)

    actions = _unique(actions + [
        "Link verified identity, family relationship, ownership, liquidity, source-of-wealth, and source-of-funds evidence.",
        "Map every family member, entity, asset class, tax residence, banking relationship, and destination to an accountable adviser.",
        "Re-verify all mobility pathways and program conditions before any filing, restructuring, transfer, or capital commitment.",
    ])
    unique_blockers = _unique(blockers)

    def workstream(key: str, title: str, score: float, relevant: tuple[str, ...], stream_actions: list[str]):
        stream_blockers = [
            blocker for blocker in unique_blockers
            if any(term in blocker.lower() for term in relevant)
        ]
        return FamilyOfficeWorkstream(
            workstream_key=key,
            title=title,
            readiness_score=round(score, 1),
            readiness_band=_band(score),
            findings=[] if stream_blockers else ["No material gap was identified from the facts and evidence currently supplied."],
            blockers=stream_blockers,
            next_actions=stream_actions,
        ).model_dump(mode="json")

    workstreams = [
        workstream(
            "identity_family", "Principal and family identity", identity_score,
            ("citizenship", "tax residenc"),
            ["Complete identity, relationship, dependant, residence, and citizenship evidence for every included family member."],
        ),
        workstream(
            "wealth_evidence", "Source of wealth and funds", wealth_evidence_score,
            ("wealth", "funds", "wealth document"),
            ["Create a reconciled source-of-wealth and source-of-funds evidence chain with independent review."],
        ),
        workstream(
            "ownership_control", "Ownership and control map", ownership_transparency_score,
            ("ownership", "structure"),
            ["Map legal ownership, beneficial ownership, control rights, protectors, trustees, directors, and beneficiaries."],
        ),
        workstream(
            "governance_advisers", "Governance, banking and specialists", governance_score,
            ("screening", "pep", "sanction"),
            ["Clear screening and assign qualified tax, legal, banking, investment, and succession advisers before execution."],
        ),
        workstream(
            "mobility_routes", "Family mobility and residence routes", mobility_grounding_score,
            ("pathway",),
            ["Compare only independently published pathways and programs against each family member and intended jurisdiction."],
        ),
    ]

    evidence_basis = [
        {
            "document_id": str(document.id),
            "document_type": document.document_type,
            "status": document.status,
        }
        for document in documents
    ]
    row = FamilyOfficeMobilityAssessment(
        lead_id=lead.id,
        business_advisory_assessment_id=payload.business_advisory_assessment_id,
        family_office_name=payload.family_office_name.strip() if payload.family_office_name else None,
        input_json=_dump(payload.model_dump(mode="json")),
        readiness_score=readiness_score,
        readiness_band=_band(readiness_score),
        identity_score=round(identity_score, 1),
        wealth_evidence_score=round(wealth_evidence_score, 1),
        ownership_transparency_score=round(ownership_transparency_score, 1),
        governance_score=round(governance_score, 1),
        mobility_grounding_score=round(mobility_grounding_score, 1),
        workstreams_json=_dump(workstreams),
        blockers_json=_dump(unique_blockers),
        next_actions_json=_dump(actions),
        evidence_basis_json=_dump(evidence_basis),
        grounded_pathway_versions_json=_dump(pathways),
        grounded_program_versions_json=_dump(programs),
        escalation_flags_json=_dump(_unique(escalation_flags)),
        status="pending_review",
        human_review_required=True,
        generated_by=actor,
    )
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="family_office_mobility_assessment_created",
        entity_type="family_office_mobility_assessment",
        entity_id=row.id,
        after_state=row,
        actor=actor,
        source="family_office_mobility_v11_10",
    )
    session.commit()
    session.refresh(row)
    return row


def review_family_office_assessment(
    session: Session,
    assessment: FamilyOfficeMobilityAssessment,
    payload: FamilyOfficeReviewCreate,
    *,
    actor: str,
) -> FamilyOfficeMobilityReview:
    if assessment.status != "pending_review":
        raise ValueError("Family-office mobility assessment is not pending review")
    if assessment.generated_by == actor:
        raise ValueError("Family-office mobility assessment requires a different reviewer")
    before = to_audit_dict(assessment)
    now = datetime.now(timezone.utc)
    review = FamilyOfficeMobilityReview(
        assessment_id=assessment.id,
        decision=payload.decision,
        reason=payload.reason.strip(),
        reviewer=actor,
    )
    assessment.status = payload.decision
    assessment.reviewed_by = actor
    assessment.reviewed_at = now
    assessment.review_notes = payload.reason.strip()
    assessment.updated_at = now
    session.add(review)
    session.add(assessment)
    session.flush()
    record_audit(
        session,
        action="family_office_mobility_assessment_reviewed",
        entity_type="family_office_mobility_assessment",
        entity_id=assessment.id,
        before_state=before,
        after_state=assessment,
        reason=payload.reason.strip(),
        actor=actor,
        source="family_office_mobility_v11_10",
    )
    session.commit()
    session.refresh(review)
    return review

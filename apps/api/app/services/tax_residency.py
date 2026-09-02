from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import combinations
from typing import Any

from sqlmodel import Session, select

from app.models.domain import (
    BusinessMobilityAdvisoryAssessment,
    DocumentRecord,
    FamilyOfficeMobilityAssessment,
    Lead,
    OfficialSource,
    SourceSnapshot,
    TaxResidencyAssessment,
    TaxResidencyAssessmentReview,
    TaxTreatyEvidence,
    TaxTreatyEvidenceDecision,
)
from app.schemas_tax_residency import (
    TaxIssue,
    TaxResidencyAssessmentCreate,
    TaxResidencyAssessmentRead,
    TaxResidencyReviewCreate,
    TaxResidencyWorkstream,
    TaxTreatyEvidenceCreate,
    TaxTreatyEvidenceDecisionCreate,
    TaxTreatyEvidenceRead,
)
from app.services.audit_log import record_audit, to_audit_dict


SCORE_SEMANTICS = (
    "Readiness to obtain a licensed cross-border tax analysis from disclosed presence, home, "
    "family, employment, ownership, income, controlled-document, adviser, and independently "
    "reviewed treaty evidence. It is not a tax-residency determination, treaty-entitlement "
    "conclusion, tax calculation, filing position, legal opinion, or tax-outcome guarantee."
)

PROHIBITED_SIGNALS = {
    "hide days", "conceal residence", "fake lease", "backdate lease", "evade tax",
    "hide income", "conceal income", "false tax return", "sham residence",
    "misrepresent presence", "hide beneficial ownership",
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
        return "specialist_ready"
    if score >= 60:
        return "workable_with_gaps"
    if score >= 40:
        return "material_gaps"
    return "not_ready"


def treaty_evidence_read(
    session: Session,
    row: TaxTreatyEvidence,
) -> TaxTreatyEvidenceRead:
    source = session.get(OfficialSource, row.official_source_id)
    snapshot = session.get(SourceSnapshot, row.source_snapshot_id)
    if source is None or snapshot is None or not snapshot.content_hash:
        raise ValueError("Tax treaty evidence provenance is incomplete")
    return TaxTreatyEvidenceRead(
        **row.model_dump(),
        source_url=source.url,
        source_content_hash=snapshot.content_hash,
    )


def create_treaty_evidence(
    session: Session,
    payload: TaxTreatyEvidenceCreate,
    *,
    actor: str,
) -> TaxTreatyEvidence:
    duplicate = session.exec(select(TaxTreatyEvidence).where(
        TaxTreatyEvidence.evidence_key == payload.evidence_key
    )).first()
    if duplicate:
        raise ValueError("Tax treaty evidence key already exists")
    source = session.get(OfficialSource, payload.official_source_id)
    if source is None:
        raise ValueError("Official source not found")
    if not source.active or source.domain != "tax":
        raise ValueError("An active tax-domain official source is required")
    pair = {payload.jurisdiction_a.strip().lower(), payload.jurisdiction_b.strip().lower()}
    if source.country.strip().lower() not in pair:
        raise ValueError("Official source country must match one treaty jurisdiction")
    snapshot = session.get(SourceSnapshot, payload.source_snapshot_id)
    if (
        snapshot is None
        or snapshot.official_source_id != source.id
        or not snapshot.content_hash
    ):
        raise ValueError("A content-addressed snapshot from the selected tax source is required")
    row = TaxTreatyEvidence(
        evidence_key=payload.evidence_key,
        jurisdiction_a=payload.jurisdiction_a.strip(),
        jurisdiction_b=payload.jurisdiction_b.strip(),
        topic=payload.topic,
        title=payload.title.strip(),
        statement=payload.statement.strip(),
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        status="pending_review",
        proposed_by=actor,
    )
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="tax_treaty_evidence_created",
        entity_type="tax_treaty_evidence",
        entity_id=row.id,
        after_state=row,
        actor=actor,
        source="tax_residency_v11_11",
    )
    session.commit()
    session.refresh(row)
    return row


def decide_treaty_evidence(
    session: Session,
    row: TaxTreatyEvidence,
    payload: TaxTreatyEvidenceDecisionCreate,
    *,
    actor: str,
) -> TaxTreatyEvidenceDecision:
    if row.status != "pending_review":
        raise ValueError("Tax treaty evidence is not pending review")
    if row.proposed_by == actor:
        raise ValueError("Tax treaty evidence requires a different reviewer")
    source = session.get(OfficialSource, row.official_source_id)
    snapshot = session.get(SourceSnapshot, row.source_snapshot_id)
    if (
        source is None or not source.active or source.domain != "tax"
        or snapshot is None or snapshot.official_source_id != source.id
        or not snapshot.content_hash
    ):
        raise ValueError("Tax treaty evidence provenance is incomplete")
    before = to_audit_dict(row)
    now = datetime.now(timezone.utc)
    decision = TaxTreatyEvidenceDecision(
        tax_treaty_evidence_id=row.id,
        decision=payload.decision,
        reason=payload.reason.strip(),
        reviewer=actor,
    )
    row.status = "published" if payload.decision == "approved" else "rejected"
    row.reviewed_by = actor
    row.reviewed_at = now
    row.review_notes = payload.reason.strip()
    row.updated_at = now
    session.add(decision)
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="tax_treaty_evidence_reviewed",
        entity_type="tax_treaty_evidence",
        entity_id=row.id,
        before_state=before,
        after_state=row,
        reason=payload.reason.strip(),
        actor=actor,
        source="tax_residency_v11_11",
    )
    session.commit()
    session.refresh(decision)
    return decision


def assessment_read(row: TaxResidencyAssessment) -> TaxResidencyAssessmentRead:
    return TaxResidencyAssessmentRead(
        **row.model_dump(),
        issue_matrix=[
            TaxIssue.model_validate(value)
            for value in _load(row.issue_matrix_json, [])
        ],
        workstreams=[
            TaxResidencyWorkstream.model_validate(value)
            for value in _load(row.workstreams_json, [])
        ],
        blockers=_load(row.blockers_json, []),
        next_actions=_load(row.next_actions_json, []),
        evidence_basis=_load(row.evidence_basis_json, []),
        treaty_evidence_ids=_load(row.treaty_evidence_ids_json, []),
        escalation_flags=_load(row.escalation_flags_json, []),
        score_semantics=SCORE_SEMANTICS,
    )


def _relevant_pairs(current: list[str], targets: list[str]) -> set[frozenset[str]]:
    jurisdictions = _unique([*current, *targets])
    return {
        frozenset((first.lower(), second.lower()))
        for first, second in combinations(jurisdictions, 2)
    }


def create_tax_residency_assessment(
    session: Session,
    payload: TaxResidencyAssessmentCreate,
    *,
    actor: str,
) -> TaxResidencyAssessment:
    lead = session.get(Lead, payload.lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    family_office = (
        session.get(FamilyOfficeMobilityAssessment, payload.family_office_assessment_id)
        if payload.family_office_assessment_id else None
    )
    if payload.family_office_assessment_id and family_office is None:
        raise ValueError("Family-office mobility assessment not found")
    if family_office and family_office.lead_id != lead.id:
        raise ValueError("Family-office assessment must belong to the selected lead")
    advisory = (
        session.get(BusinessMobilityAdvisoryAssessment, payload.business_advisory_assessment_id)
        if payload.business_advisory_assessment_id else None
    )
    if payload.business_advisory_assessment_id and advisory is None:
        raise ValueError("Business mobility advisory not found")
    if advisory and advisory.lead_id != lead.id:
        raise ValueError("Business mobility advisory must belong to the selected lead")

    documents: list[DocumentRecord] = []
    for document_id in payload.document_record_ids:
        document = session.get(DocumentRecord, document_id)
        if document is None:
            raise ValueError("Tax-residency evidence document not found")
        if document.lead_id != lead.id:
            raise ValueError("Tax-residency evidence documents must belong to the selected lead")
        documents.append(document)

    relevant_pairs = _relevant_pairs(payload.current_residencies, payload.target_residencies)
    treaty_records: list[TaxTreatyEvidence] = []
    for evidence_id in payload.treaty_evidence_ids:
        evidence = session.get(TaxTreatyEvidence, evidence_id)
        if evidence is None:
            raise ValueError("Tax treaty evidence not found")
        if evidence.status != "published":
            raise ValueError("Only independently published tax treaty evidence may be used")
        pair = frozenset((evidence.jurisdiction_a.lower(), evidence.jurisdiction_b.lower()))
        if pair not in relevant_pairs:
            raise ValueError("Tax treaty evidence does not match the assessment jurisdictions")
        tax_year_start = datetime(payload.tax_year, 1, 1).date()
        tax_year_end = datetime(payload.tax_year, 12, 31).date()
        if (
            evidence.effective_from
            and evidence.effective_from.date() > tax_year_end
        ) or (
            evidence.effective_to
            and evidence.effective_to.date() < tax_year_start
        ):
            raise ValueError(
                "Tax treaty evidence is not effective for the assessment tax year"
            )
        treaty_records.append(evidence)

    blockers: list[str] = []
    actions: list[str] = []
    escalation_flags: list[str] = []
    issues: list[dict[str, Any]] = []
    if not payload.current_residencies:
        blockers.append("Current claimed or filed tax residencies are not recorded.")
    if not payload.citizenships:
        blockers.append("Citizenships are not recorded for specialist review.")
    if not payload.available_homes:
        blockers.append("No available-home facts are recorded.")
    if not documents:
        blockers.append("No controlled client evidence is linked to the tax-residency fact pattern.")

    fact_inputs = [
        bool(payload.current_residencies), bool(payload.target_residencies),
        bool(payload.citizenships), bool(payload.presence_periods),
        bool(payload.available_homes), bool(payload.spouse_or_dependant_jurisdictions),
        bool(payload.employment_jurisdictions), bool(payload.income_categories),
        payload.planned_arrival_date is not None, payload.planned_departure_date is not None,
    ]
    fact_completeness = round(sum(fact_inputs) / len(fact_inputs) * 100.0, 1)
    verified_documents = sum(1 for document in documents if document.status == "verified")
    controlled_evidence = min(100.0, len(documents) * 12.0 + verified_documents * 13.0)
    covered_pairs = {
        frozenset((record.jurisdiction_a.lower(), record.jurisdiction_b.lower()))
        for record in treaty_records
    }
    treaty_grounding = (
        round(len(covered_pairs) / len(relevant_pairs) * 100.0, 1)
        if relevant_pairs else 0.0
    )
    specialist_coordination = round(
        (
            int(payload.tax_adviser_engaged)
            + int(payload.home_jurisdiction_adviser_engaged)
            + int(payload.destination_adviser_engaged)
        ) / 3 * 100.0,
        1,
    )

    presence_jurisdictions = [
        period.jurisdiction for period in payload.presence_periods if period.days > 0
    ]
    all_jurisdictions = _unique([
        *payload.current_residencies, *payload.target_residencies, *presence_jurisdictions,
    ])
    for jurisdiction in all_jurisdictions:
        issues.append(TaxIssue(
            issue_key=f"domestic_residence_{jurisdiction.lower().replace(' ', '_')}",
            title=f"Domestic residence analysis — {jurisdiction}",
            jurisdictions=[jurisdiction],
            severity="specialist_review",
            rationale="Domestic residence must be determined from the complete dated fact pattern and current official law.",
            evidence_state="controlled_documents_linked" if documents else "evidence_missing",
        ).model_dump(mode="json"))
    if len(all_jurisdictions) > 1:
        issues.append(TaxIssue(
            issue_key="dual_residence_and_tie_breaker",
            title="Potential dual residence and treaty coordination",
            jurisdictions=all_jurisdictions,
            severity="material",
            rationale="Multiple relevant jurisdictions require separate domestic-law analyses before any treaty tie-breaker can be considered.",
            evidence_state="published_treaty_evidence_linked" if covered_pairs else "treaty_evidence_missing",
        ).model_dump(mode="json"))
    if payload.director_or_control_jurisdictions or payload.business_structure_jurisdictions:
        issues.append(TaxIssue(
            issue_key="entity_residence_and_permanent_establishment",
            title="Entity residence, management and permanent-establishment exposure",
            jurisdictions=_unique([
                *payload.director_or_control_jurisdictions,
                *payload.business_structure_jurisdictions,
                *payload.target_residencies,
            ]),
            severity="material",
            rationale="Personal relocation can affect management, control, payroll, business-profit, and permanent-establishment analyses.",
            evidence_state="specialist_analysis_required",
        ).model_dump(mode="json"))
    if payload.employment_jurisdictions:
        issues.append(TaxIssue(
            issue_key="employment_and_social_security",
            title="Employment income, payroll and social-security coordination",
            jurisdictions=_unique([
                *payload.employment_jurisdictions, *payload.target_residencies,
            ]),
            severity="specialist_review",
            rationale="Work location, employer, payroll, and applicable social-security coordination require dated specialist analysis.",
            evidence_state="specialist_analysis_required",
        ).model_dump(mode="json"))
    issues.append(TaxIssue(
        issue_key="departure_arrival_and_filing",
        title="Departure, arrival, exit, entry and filing sequence",
        jurisdictions=_unique([
            *payload.current_residencies, *payload.target_residencies,
        ]),
        severity="specialist_review",
        rationale="Departure and arrival dates can affect residence, reporting, payment, exit, entry, and registration obligations.",
        evidence_state="dates_recorded" if payload.planned_arrival_date and payload.planned_departure_date else "dates_incomplete",
    ).model_dump(mode="json"))

    missing_pairs = relevant_pairs - covered_pairs
    if missing_pairs:
        blockers.append("One or more jurisdiction pairs lack independently published treaty evidence.")
        actions.append("Onboard and independently review the exact official treaty and protocol evidence for every relevant jurisdiction pair.")
    if not payload.tax_adviser_engaged:
        blockers.append("No coordinating cross-border tax adviser is recorded.")
    if not payload.home_jurisdiction_adviser_engaged:
        actions.append("Obtain a written domestic-law residence and departure analysis from the home-jurisdiction adviser.")
    if not payload.destination_adviser_engaged:
        actions.append("Obtain a written domestic-law residence and arrival analysis from the destination-jurisdiction adviser.")

    narrative = " ".join(payload.disclosed_constraints).lower()
    prohibited = [signal for signal in PROHIBITED_SIGNALS if signal in narrative]
    if prohibited:
        escalation_flags.append("tax_evasion_concealment_or_misrepresentation_signal")
        blockers.append("A tax-evasion, concealment, sham-residence, false-document, or misrepresentation signal prevents operationalization.")

    readiness = round(
        fact_completeness * .30
        + controlled_evidence * .25
        + treaty_grounding * .25
        + specialist_coordination * .20,
        1,
    )
    if not payload.tax_adviser_engaged or missing_pairs:
        readiness = min(readiness, 59.0)
    if prohibited:
        readiness = min(readiness, 10.0)

    actions = _unique(actions + [
        "Reconcile travel, immigration, accommodation, family, employment, director, ownership, banking, and income records into one dated fact pattern.",
        "Have licensed advisers determine domestic residence independently in each jurisdiction before applying treaty provisions.",
        "Record treaty article, protocol, effective date, official source, and exact snapshot for every material specialist conclusion.",
        "Create a reviewed departure, arrival, registration, filing, payroll, payment, and evidence-retention calendar.",
    ])
    blockers = _unique(blockers)

    def stream(key: str, title: str, score: float, terms: tuple[str, ...], stream_actions: list[str]):
        relevant = [
            blocker for blocker in blockers
            if any(term in blocker.lower() for term in terms)
        ]
        return TaxResidencyWorkstream(
            workstream_key=key,
            title=title,
            readiness_score=score,
            readiness_band=_band(score),
            blockers=relevant,
            next_actions=stream_actions,
        ).model_dump(mode="json")

    workstreams = [
        stream("fact_pattern", "Dated residence fact pattern", fact_completeness,
               ("residenc", "citizenship", "home"),
               ["Reconcile presence days, available homes, family ties, work, control, and arrival/departure dates."]),
        stream("controlled_evidence", "Controlled client evidence", controlled_evidence,
               ("evidence",),
               ["Link verified travel, accommodation, family, employment, ownership, income, and filing records."]),
        stream("treaty_grounding", "Treaty and protocol evidence", treaty_grounding,
               ("treaty", "jurisdiction pair"),
               ["Pin every relevant provision to an independently reviewed official-source snapshot."]),
        stream("entity_income", "Entity, income and payroll coordination",
               70.0 if payload.income_categories and (
                   payload.director_or_control_jurisdictions
                   or payload.employment_jurisdictions
               ) else 35.0,
               ("permanent", "employment", "payroll"),
               ["Obtain specialist analyses for income sourcing, payroll, entity residence, control, and permanent establishment."]),
        stream("specialist_sequence", "Adviser and filing sequence", specialist_coordination,
               ("adviser",),
               ["Assign home, destination, and coordinating advisers and approve the dated compliance calendar."]),
    ]

    evidence_basis = [
        {
            "document_id": str(document.id),
            "document_type": document.document_type,
            "status": document.status,
        }
        for document in documents
    ] + [
        {
            "tax_treaty_evidence_id": str(record.id),
            "evidence_key": record.evidence_key,
            "source_snapshot_id": str(record.source_snapshot_id),
            "status": record.status,
        }
        for record in treaty_records
    ]
    row = TaxResidencyAssessment(
        lead_id=lead.id,
        family_office_assessment_id=payload.family_office_assessment_id,
        business_advisory_assessment_id=payload.business_advisory_assessment_id,
        tax_year=payload.tax_year,
        input_json=_dump(payload.model_dump(mode="json")),
        readiness_score=readiness,
        readiness_band=_band(readiness),
        fact_completeness_score=fact_completeness,
        controlled_evidence_score=controlled_evidence,
        treaty_grounding_score=treaty_grounding,
        specialist_coordination_score=specialist_coordination,
        issue_matrix_json=_dump(issues),
        workstreams_json=_dump(workstreams),
        blockers_json=_dump(blockers),
        next_actions_json=_dump(actions),
        evidence_basis_json=_dump(evidence_basis),
        treaty_evidence_ids_json=_dump([str(record.id) for record in treaty_records]),
        escalation_flags_json=_dump(escalation_flags),
        status="specialist_review_required",
        human_review_required=True,
        generated_by=actor,
    )
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="tax_residency_assessment_created",
        entity_type="tax_residency_assessment",
        entity_id=row.id,
        after_state=row,
        actor=actor,
        source="tax_residency_v11_11",
    )
    session.commit()
    session.refresh(row)
    return row


def review_tax_residency_assessment(
    session: Session,
    row: TaxResidencyAssessment,
    payload: TaxResidencyReviewCreate,
    *,
    actor: str,
) -> TaxResidencyAssessmentReview:
    if row.status != "specialist_review_required":
        raise ValueError("Tax-residency assessment is not awaiting specialist review")
    if row.generated_by == actor:
        raise ValueError("Tax-residency assessment requires a different specialist reviewer")
    before = to_audit_dict(row)
    now = datetime.now(timezone.utc)
    review = TaxResidencyAssessmentReview(
        assessment_id=row.id,
        decision=payload.decision,
        reason=payload.reason.strip(),
        reviewer=actor,
    )
    row.status = payload.decision
    row.reviewed_by = actor
    row.reviewed_at = now
    row.review_notes = payload.reason.strip()
    row.updated_at = now
    session.add(review)
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="tax_residency_assessment_reviewed",
        entity_type="tax_residency_assessment",
        entity_id=row.id,
        before_state=before,
        after_state=row,
        reason=payload.reason.strip(),
        actor=actor,
        source="tax_residency_v11_11",
    )
    session.commit()
    session.refresh(review)
    return review

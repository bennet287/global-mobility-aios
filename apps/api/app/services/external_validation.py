from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import Session, select

from app.models.domain import (
    DocumentRecord,
    ExternalValidationEvidence,
    ExternalValidationFinding,
    ExternalValidationReview,
    ExternalValidationRun,
    ExternalValidationScenario,
    Jurisdiction,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    PathwayComparisonAssessment,
    SourceSnapshot,
    TruthClaim,
    VerifiedRule,
    now_utc,
)
from app.schemas import (
    ExternalValidationBoardAcceptance,
    ExternalValidationEvidenceCreate,
    ExternalValidationEvidenceRead,
    ExternalValidationFindingCreate,
    ExternalValidationFindingRead,
    ExternalValidationFindingTriage,
    ExternalValidationGateRead,
    ExternalValidationReviewCreate,
    ExternalValidationReviewRead,
    ExternalValidationRunCreate,
    ExternalValidationRunRead,
    ExternalValidationRunUpdate,
    ExternalValidationScenarioCreate,
    ExternalValidationScenarioRead,
)
from app.services.audit_log import record_audit


VALIDATION_ROOT = Path(__file__).resolve().parents[2] / "validation"
DEFAULT_SCENARIO_FILE = VALIDATION_ROOT / "scenarios" / "austria_skilled_worker_v1.json"
REQUIRED_REVIEWER_TYPES = ("mobility_user", "professional_operator")
MATERIAL_SEVERITIES = frozenset({"critical", "high"})
BOARD_ACCEPTABLE_SEVERITIES = frozenset({"medium", "low"})
TERMINAL_TRIAGE_STATUSES = frozenset({"triaged", "resolved", "accepted_risk"})


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _actor_key(value: str) -> str:
    return " ".join(value.strip().lower().split())


def scenario_read(row: ExternalValidationScenario) -> ExternalValidationScenarioRead:
    return ExternalValidationScenarioRead(
        id=row.id,
        scenario_key=row.scenario_key,
        title=row.title,
        jurisdiction_code=row.jurisdiction_code,
        domain=row.domain,
        persona=_load(row.persona_json, {}),
        objectives=_load(row.objectives_json, []),
        required_evidence_types=_load(row.required_evidence_types_json, []),
        status=row.status,
        source_fixture=row.source_fixture,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def review_read(row: ExternalValidationReview) -> ExternalValidationReviewRead:
    return ExternalValidationReviewRead(**row.model_dump())


def finding_read(row: ExternalValidationFinding) -> ExternalValidationFindingRead:
    return ExternalValidationFindingRead(**row.model_dump())


def evidence_read(row: ExternalValidationEvidence) -> ExternalValidationEvidenceRead:
    payload = row.model_dump()
    payload["metadata"] = _load(payload.pop("metadata_json", None), {})
    return ExternalValidationEvidenceRead(**payload)


def create_external_validation_scenario(
    session: Session,
    payload: ExternalValidationScenarioCreate,
    *,
    actor: str,
    source_fixture: str | None = None,
) -> ExternalValidationScenario:
    key = payload.scenario_key.strip().lower()
    existing = session.exec(
        select(ExternalValidationScenario).where(ExternalValidationScenario.scenario_key == key)
    ).first()
    if existing is not None:
        raise ValueError("External validation scenario key already exists")
    now = now_utc()
    row = ExternalValidationScenario(
        scenario_key=key,
        title=payload.title.strip(),
        jurisdiction_code=payload.jurisdiction_code.strip().upper(),
        domain=payload.domain.strip().lower(),
        persona_json=_dump(payload.persona),
        objectives_json=_dump(payload.objectives),
        required_evidence_types_json=_dump(payload.required_evidence_types),
        status="active",
        source_fixture=source_fixture,
        created_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="external_validation_scenario_created",
        entity_type="external_validation_scenario",
        entity_id=row.id,
        after_state=scenario_read(row).model_dump(mode="json"),
        reason="Created a bounded external-validation scenario; no legal conclusion is encoded by the scenario itself.",
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(row)
    return row


def seed_default_external_validation_scenario(
    session: Session,
    *,
    actor: str,
) -> ExternalValidationScenario:
    if not DEFAULT_SCENARIO_FILE.exists():
        raise ValueError("Default Austria validation scenario fixture is missing")
    data = json.loads(DEFAULT_SCENARIO_FILE.read_text(encoding="utf-8"))
    key = str(data["scenario_key"]).strip().lower()
    existing = session.exec(
        select(ExternalValidationScenario).where(ExternalValidationScenario.scenario_key == key)
    ).first()
    if existing is not None:
        return existing
    payload = ExternalValidationScenarioCreate(**data)
    return create_external_validation_scenario(
        session,
        payload,
        actor=actor,
        source_fixture="validation/scenarios/austria_skilled_worker_v1.json",
    )


def list_external_validation_scenarios(
    session: Session,
    *,
    status: str | None = None,
    limit: int = 100,
) -> list[ExternalValidationScenarioRead]:
    statement = select(ExternalValidationScenario).order_by(ExternalValidationScenario.created_at.desc())
    if status:
        statement = statement.where(ExternalValidationScenario.status == status.strip().lower())
    rows = session.exec(statement.limit(max(1, min(limit, 500)))).all()
    return [scenario_read(row) for row in rows]


def _validate_run_links(
    session: Session,
    payload: ExternalValidationRunCreate,
) -> ExternalValidationScenario:
    scenario = session.get(ExternalValidationScenario, payload.scenario_id)
    if scenario is None:
        raise ValueError("External validation scenario not found")
    if scenario.status != "active":
        raise ValueError("External validation scenario is not active")
    if payload.lead_id is not None:
        from app.models.domain import Lead

        if session.get(Lead, payload.lead_id) is None:
            raise ValueError("Lead not found")
    if payload.pathway_comparison_assessment_id is not None:
        comparison = session.get(PathwayComparisonAssessment, payload.pathway_comparison_assessment_id)
        if comparison is None:
            raise ValueError("Pathway comparison assessment not found")
        if payload.lead_id is not None and comparison.lead_id != payload.lead_id:
            raise ValueError("Pathway comparison assessment does not belong to the selected lead")
    return scenario


def create_external_validation_run(
    session: Session,
    payload: ExternalValidationRunCreate,
    *,
    actor: str,
) -> ExternalValidationRun:
    _validate_run_links(session, payload)
    run_key = payload.run_key or f"validation-{now_utc().strftime('%Y%m%dT%H%M%S')}-{uuid4().hex[:8]}"
    if session.exec(select(ExternalValidationRun).where(ExternalValidationRun.run_key == run_key)).first():
        raise ValueError("External validation run key already exists")
    now = now_utc()
    row = ExternalValidationRun(
        run_key=run_key,
        scenario_id=payload.scenario_id,
        lead_id=payload.lead_id,
        pathway_comparison_assessment_id=payload.pathway_comparison_assessment_id,
        status="in_review",
        gate_status="held",
        gate_reasons_json=_dump(["External validation requires both external reviewer types and complete evidence capture."]),
        founder_intervention_count=payload.founder_intervention_count,
        workflow_started_at=payload.workflow_started_at or now,
        created_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="external_validation_run_created",
        entity_type="external_validation_run",
        entity_id=row.id,
        after_state=row,
        reason="Started an external Truth Engine/pathway validation run.",
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(row)
    return row


def update_external_validation_run(
    session: Session,
    run_id: UUID,
    payload: ExternalValidationRunUpdate,
    *,
    actor: str,
) -> ExternalValidationRun:
    row = session.get(ExternalValidationRun, run_id)
    if row is None:
        raise ValueError("External validation run not found")
    before = row.model_dump(mode="json")
    if payload.founder_intervention_count is not None:
        row.founder_intervention_count = payload.founder_intervention_count
    if payload.workflow_completed_at is not None:
        row.workflow_completed_at = payload.workflow_completed_at
    row.updated_at = now_utc()
    session.add(row)
    record_audit(
        session,
        action="external_validation_run_updated",
        entity_type="external_validation_run",
        entity_id=row.id,
        before_state=before,
        after_state=row,
        reason="Updated externally observed run metrics; gate evaluation remains deterministic.",
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(row)
    return row


def submit_external_validation_review(
    session: Session,
    run_id: UUID,
    payload: ExternalValidationReviewCreate,
    *,
    actor: str,
) -> ExternalValidationReview:
    run = session.get(ExternalValidationRun, run_id)
    if run is None:
        raise ValueError("External validation run not found")
    if run.status == "completed" and run.gate_status == "passed":
        raise ValueError("Passed validation runs are immutable; start a new run for retesting")
    existing = session.exec(
        select(ExternalValidationReview).where(
            ExternalValidationReview.run_id == run_id,
            ExternalValidationReview.reviewer_type == payload.reviewer_type,
        )
    ).first()
    if existing is not None:
        raise ValueError(f"{payload.reviewer_type} review is already recorded for this run")
    other_reviews = session.exec(
        select(ExternalValidationReview).where(ExternalValidationReview.run_id == run_id)
    ).all()
    reviewer_key = _actor_key(payload.reviewer_name)
    if any(_actor_key(item.reviewer_name) == reviewer_key for item in other_reviews):
        raise ValueError("The mobility user and professional/operator must be distinct external reviewers")
    if payload.reviewer_origin != "external_human" or not payload.external_human_attestation:
        raise ValueError("External validation review must attest to an external human origin")
    row = ExternalValidationReview(
        run_id=run_id,
        reviewer_type=payload.reviewer_type,
        reviewer_name=payload.reviewer_name.strip(),
        reviewer_organization=(payload.reviewer_organization or "").strip() or None,
        reviewer_origin="external_human",
        external_human_attestation=True,
        workflow_completed=payload.workflow_completed,
        understanding_rating=payload.understanding_rating,
        usefulness_rating=payload.usefulness_rating,
        jurisdiction_pathway_correct=payload.jurisdiction_pathway_correct,
        material_rule_traceability_percent=payload.material_rule_traceability_percent,
        unsupported_legal_certainty_count=payload.unsupported_legal_certainty_count,
        missing_critical_document_count=payload.missing_critical_document_count,
        feedback=payload.feedback.strip(),
        submitted_by=actor,
        submitted_at=now_utc(),
    )
    session.add(row)
    run.gate_status = "held"
    run.updated_at = now_utc()
    session.add(run)
    session.flush()
    record_audit(
        session,
        action="external_validation_review_recorded",
        entity_type="external_validation_review",
        entity_id=row.id,
        after_state=review_read(row).model_dump(mode="json"),
        reason=(
            "Recorded externally-originated human feedback. The AI organization is not permitted to create "
            "or self-attest this review."
        ),
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(row)
    return row


def create_external_validation_finding(
    session: Session,
    run_id: UUID,
    payload: ExternalValidationFindingCreate,
    *,
    actor: str,
) -> ExternalValidationFinding:
    run = session.get(ExternalValidationRun, run_id)
    if run is None:
        raise ValueError("External validation run not found")
    if payload.review_id is not None:
        review = session.get(ExternalValidationReview, payload.review_id)
        if review is None or review.run_id != run_id:
            raise ValueError("External validation review does not belong to this run")
    now = now_utc()
    row = ExternalValidationFinding(
        run_id=run_id,
        review_id=payload.review_id,
        severity=payload.severity,
        category=payload.category.strip().lower().replace(" ", "_"),
        title=payload.title.strip(),
        description=payload.description.strip(),
        status="open",
        created_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    run.gate_status = "held"
    run.updated_at = now
    session.add(run)
    session.flush()
    record_audit(
        session,
        action="external_validation_finding_created",
        entity_type="external_validation_finding",
        entity_id=row.id,
        after_state=finding_read(row).model_dump(mode="json"),
        reason="Recorded an external-validation defect for explicit triage.",
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(row)
    return row


def triage_external_validation_finding(
    session: Session,
    finding_id: UUID,
    payload: ExternalValidationFindingTriage,
    *,
    actor: str,
) -> ExternalValidationFinding:
    row = session.get(ExternalValidationFinding, finding_id)
    if row is None:
        raise ValueError("External validation finding not found")
    if row.status == "accepted_risk":
        raise ValueError("Board-accepted findings cannot be changed through the ordinary triage lane")
    before = row.model_dump(mode="json")
    now = now_utc()
    row.status = payload.status
    row.remediation_notes = payload.remediation_notes.strip()
    if payload.status == "resolved":
        row.resolved_by = actor
        row.resolved_at = now
    else:
        row.resolved_by = None
        row.resolved_at = None
    row.updated_at = now
    session.add(row)
    run = session.get(ExternalValidationRun, row.run_id)
    if run is not None:
        run.gate_status = "held"
        run.updated_at = now
        session.add(run)
    record_audit(
        session,
        action="external_validation_finding_triaged",
        entity_type="external_validation_finding",
        entity_id=row.id,
        before_state=before,
        after_state=row,
        reason=payload.remediation_notes,
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(row)
    return row


def board_accept_external_validation_finding(
    session: Session,
    finding_id: UUID,
    payload: ExternalValidationBoardAcceptance,
    *,
    actor: str,
) -> ExternalValidationFinding:
    row = session.get(ExternalValidationFinding, finding_id)
    if row is None:
        raise ValueError("External validation finding not found")
    if not payload.attestation:
        raise ValueError("Human Board attestation is required")
    if row.severity not in BOARD_ACCEPTABLE_SEVERITIES:
        raise ValueError("Critical and high external-validation findings cannot be waived; they must be resolved")
    if row.status == "resolved":
        raise ValueError("Resolved findings do not require Board risk acceptance")
    before = row.model_dump(mode="json")
    now = now_utc()
    row.status = "accepted_risk"
    row.board_acceptance_reason = payload.reason.strip()
    row.board_accepted_by = actor
    row.board_accepted_at = now
    row.updated_at = now
    session.add(row)
    run = session.get(ExternalValidationRun, row.run_id)
    if run is not None:
        run.gate_status = "held"
        run.updated_at = now
        session.add(run)
    record_audit(
        session,
        action="external_validation_finding_board_accepted",
        entity_type="external_validation_finding",
        entity_id=row.id,
        before_state=before,
        after_state=row,
        reason=payload.reason,
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(row)
    return row


def _evidence_target(session: Session, evidence_type: str, entity_id: UUID | None) -> Any:
    if evidence_type == "operator_note":
        return None
    mapping = {
        "truth_claim": TruthClaim,
        "verified_rule": VerifiedRule,
        "official_source": OfficialSource,
        "source_snapshot": SourceSnapshot,
        "pathway": MobilityPathway,
        "pathway_version": MobilityPathwayVersion,
        "pathway_comparison": PathwayComparisonAssessment,
        "document": DocumentRecord,
    }
    model = mapping.get(evidence_type)
    if model is None or entity_id is None:
        raise ValueError("Unsupported external validation evidence reference")
    target = session.get(model, entity_id)
    if target is None:
        raise ValueError(f"Referenced {evidence_type} evidence was not found")
    return target


def add_external_validation_evidence(
    session: Session,
    run_id: UUID,
    payload: ExternalValidationEvidenceCreate,
    *,
    actor: str,
) -> ExternalValidationEvidence:
    run = session.get(ExternalValidationRun, run_id)
    if run is None:
        raise ValueError("External validation run not found")
    if payload.finding_id is not None:
        finding = session.get(ExternalValidationFinding, payload.finding_id)
        if finding is None or finding.run_id != run_id:
            raise ValueError("External validation finding does not belong to this run")
    target = _evidence_target(session, payload.evidence_type, payload.entity_id)
    if run.lead_id is not None and payload.evidence_type == "truth_claim":
        if target.lead_id != run.lead_id:
            raise ValueError("Truth claim evidence does not belong to the validation lead")
    if run.lead_id is not None and payload.evidence_type == "document":
        if target.lead_id != run.lead_id:
            raise ValueError("Document evidence does not belong to the validation lead")
    if run.lead_id is not None and payload.evidence_type == "pathway_comparison":
        if target.lead_id != run.lead_id:
            raise ValueError("Pathway comparison evidence does not belong to the validation lead")
    if run.pathway_comparison_assessment_id is not None and payload.evidence_type == "pathway_comparison":
        if target.id != run.pathway_comparison_assessment_id:
            raise ValueError("Pathway comparison evidence does not match the run's pinned comparison")

    source_url = (payload.source_url or "").strip() or None
    if source_url is None and payload.evidence_type == "official_source":
        source_url = target.url
    elif source_url is None and payload.evidence_type == "source_snapshot":
        source_url = target.url
    elif source_url is None and payload.evidence_type == "verified_rule" and target.official_source_id:
        source = session.get(OfficialSource, target.official_source_id)
        source_url = source.url if source is not None else None

    row = ExternalValidationEvidence(
        run_id=run_id,
        finding_id=payload.finding_id,
        evidence_type=payload.evidence_type,
        entity_id=payload.entity_id,
        label=payload.label.strip(),
        source_url=source_url,
        metadata_json=_dump(payload.metadata),
        added_by=actor,
        created_at=now_utc(),
    )
    session.add(row)
    run.gate_status = "held"
    run.updated_at = now_utc()
    session.add(run)
    session.flush()
    record_audit(
        session,
        action="external_validation_evidence_added",
        entity_type="external_validation_evidence",
        entity_id=row.id,
        after_state=evidence_read(row).model_dump(mode="json"),
        reason="Pinned validation evidence to a durable internal entity and provenance reference.",
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(row)
    return row


def _uuid_set(values: Any) -> set[UUID]:
    result: set[UUID] = set()
    for value in values if isinstance(values, list) else []:
        try:
            result.add(UUID(str(value)))
        except (TypeError, ValueError):
            continue
    return result


def _evidence_integrity_failures(
    session: Session,
    run: ExternalValidationRun,
    scenario: ExternalValidationScenario,
    evidence: list[ExternalValidationEvidence],
) -> list[str]:
    """Validate that captured evidence forms one coherent, governed pathway graph.

    The gate must not pass because unrelated records happen to satisfy the required
    evidence-type checklist. The pinned comparison is the root of trust: its lead,
    primary pathway version, verified-rule lineage, official sources, and source
    snapshots must all agree with the records captured for this validation run.
    """

    failures: list[str] = []
    ids_by_type: dict[str, set[UUID]] = {}
    for item in evidence:
        if item.entity_id is not None:
            ids_by_type.setdefault(item.evidence_type, set()).add(item.entity_id)

    comparison = session.get(PathwayComparisonAssessment, run.pathway_comparison_assessment_id)
    if comparison is None:
        return ["Pinned pathway comparison is missing."]
    if comparison.lead_id != run.lead_id:
        failures.append("Pinned pathway comparison does not belong to the validation lead.")
    if comparison.id not in ids_by_type.get("pathway_comparison", set()):
        failures.append("Captured pathway-comparison evidence does not include the run's pinned comparison.")

    version_id = comparison.primary_pathway_version_id
    if version_id is None:
        failures.append("Pinned pathway comparison does not identify a primary pathway version.")
        return failures
    version = session.get(MobilityPathwayVersion, version_id)
    if version is None:
        failures.append("Primary pathway version referenced by the comparison is missing.")
        return failures
    if version.id not in ids_by_type.get("pathway_version", set()):
        failures.append("Captured pathway-version evidence does not match the comparison's primary version.")
    if version.lifecycle_status != "published" or not version.approved_by:
        failures.append("Primary pathway version is not an independently approved published version.")

    pathway = session.get(MobilityPathway, version.pathway_id)
    if pathway is None:
        failures.append("Primary mobility pathway referenced by the version is missing.")
    else:
        if comparison.primary_pathway_id is None:
            failures.append("Pinned pathway comparison does not identify a primary pathway.")
        elif comparison.primary_pathway_id != pathway.id:
            failures.append("Pinned comparison pathway and primary pathway version disagree.")
        if pathway.domain.strip().lower() != scenario.domain.strip().lower():
            failures.append("Primary pathway domain does not match the validation scenario.")
        if pathway.jurisdiction_id is None:
            failures.append("Primary pathway is not pinned to a governed jurisdiction.")
        else:
            jurisdiction = session.get(Jurisdiction, pathway.jurisdiction_id)
            if jurisdiction is None or jurisdiction.code.strip().upper() != scenario.jurisdiction_code.strip().upper():
                failures.append("Primary pathway jurisdiction does not match the validation scenario.")

    required_rule_ids = _uuid_set(_load(version.verified_rule_ids_json, []))
    captured_rule_ids = ids_by_type.get("verified_rule", set())
    if not required_rule_ids:
        failures.append("Published pathway version has no verified-rule lineage to validate.")
    else:
        missing_rules = required_rule_ids - captured_rule_ids
        if missing_rules:
            failures.append(
                f"Validation evidence is missing {len(missing_rules)} verified rule(s) referenced by the pathway version."
            )

    expected_source_ids: set[UUID] = set()
    expected_snapshot_ids: set[UUID] = set()
    if version.official_source_id is not None:
        expected_source_ids.add(version.official_source_id)
    if version.source_snapshot_id is not None:
        expected_snapshot_ids.add(version.source_snapshot_id)

    for rule_id in required_rule_ids:
        rule = session.get(VerifiedRule, rule_id)
        if rule is None:
            failures.append(f"Verified rule {rule_id} referenced by the pathway version is missing.")
            continue
        if not rule.active or not rule.approved_by:
            failures.append(f"Verified rule {rule.rule_key} is not active and independently approved.")
        if rule.domain.strip().lower() != scenario.domain.strip().lower():
            failures.append(f"Verified rule {rule.rule_key} does not match the validation scenario domain.")
        if pathway is not None and rule.jurisdiction_id != pathway.jurisdiction_id:
            failures.append(f"Verified rule {rule.rule_key} does not match the primary pathway jurisdiction.")
        if rule.official_source_id is not None:
            expected_source_ids.add(rule.official_source_id)
        if rule.source_snapshot_id is not None:
            expected_snapshot_ids.add(rule.source_snapshot_id)

    if not expected_source_ids:
        failures.append("Published pathway/rule lineage has no official source to validate.")
    captured_source_ids = ids_by_type.get("official_source", set())
    missing_sources = expected_source_ids - captured_source_ids
    if missing_sources:
        failures.append(
            f"Validation evidence is missing {len(missing_sources)} official source(s) required by the pathway/rule lineage."
        )
    for source_id in expected_source_ids:
        source = session.get(OfficialSource, source_id)
        if source is None or not source.active:
            failures.append("A required official source is missing or inactive.")

    if not expected_snapshot_ids:
        failures.append("Published pathway/rule lineage has no source snapshot to validate.")
    captured_snapshot_ids = ids_by_type.get("source_snapshot", set())
    missing_snapshots = expected_snapshot_ids - captured_snapshot_ids
    if missing_snapshots:
        failures.append(
            f"Validation evidence is missing {len(missing_snapshots)} source snapshot(s) required by the pathway/rule lineage."
        )
    for snapshot_id in expected_snapshot_ids:
        snapshot = session.get(SourceSnapshot, snapshot_id)
        if snapshot is None:
            failures.append("A required source snapshot is missing.")
            continue
        if not snapshot.content_hash:
            failures.append("A required source snapshot is not content-hash pinned.")
        if snapshot.official_source_id is not None and snapshot.official_source_id not in expected_source_ids:
            failures.append("A required source snapshot is not linked to the expected official-source lineage.")

    truth_claim_ids = ids_by_type.get("truth_claim", set())
    for claim_id in truth_claim_ids:
        claim = session.get(TruthClaim, claim_id)
        if claim is None:
            failures.append("Captured Truth Engine claim is missing.")
            continue
        verdict = getattr(claim.verdict, "value", claim.verdict)
        if claim.lead_id != run.lead_id:
            failures.append("Captured Truth Engine claim does not belong to the validation lead.")
        if str(verdict).lower() != "verified":
            failures.append("Captured Truth Engine claim is not verified.")
        if claim.domain.strip().lower() != scenario.domain.strip().lower():
            failures.append("Captured Truth Engine claim domain does not match the validation scenario.")

    return failures


def external_validation_gate(
    session: Session,
    run: ExternalValidationRun,
) -> ExternalValidationGateRead:
    scenario = session.get(ExternalValidationScenario, run.scenario_id)
    if scenario is None:
        return ExternalValidationGateRead(
            status="held",
            reasons=["Validation scenario is missing."],
            founder_intervention_count=run.founder_intervention_count,
        )
    reviews = session.exec(
        select(ExternalValidationReview).where(ExternalValidationReview.run_id == run.id)
    ).all()
    findings = session.exec(
        select(ExternalValidationFinding).where(ExternalValidationFinding.run_id == run.id)
    ).all()
    evidence = session.exec(
        select(ExternalValidationEvidence).where(ExternalValidationEvidence.run_id == run.id)
    ).all()

    by_type = {review.reviewer_type: review for review in reviews if review.external_human_attestation}
    completed_reviewer_types = sorted(by_type)
    required_evidence_types = sorted(set(_load(scenario.required_evidence_types_json, [])))
    captured_evidence_types = sorted({item.evidence_type for item in evidence})

    held_reasons: list[str] = []
    fail_reasons: list[str] = []

    for reviewer_type in REQUIRED_REVIEWER_TYPES:
        if reviewer_type not in by_type:
            held_reasons.append(f"Missing required external {reviewer_type} review.")

    mobility_user = by_type.get("mobility_user")
    if mobility_user is not None:
        if not mobility_user.workflow_completed:
            fail_reasons.append("Mobility user did not complete the workflow.")
        if (mobility_user.understanding_rating or 0) < 4:
            fail_reasons.append("Mobility-user understanding rating is below 4/5.")
        if (mobility_user.usefulness_rating or 0) < 4:
            fail_reasons.append("Mobility-user usefulness rating is below 4/5.")

    professional = by_type.get("professional_operator")
    if professional is not None:
        if not professional.workflow_completed:
            fail_reasons.append("Professional/operator did not complete the workflow.")
        if (professional.usefulness_rating or 0) < 4:
            fail_reasons.append("Professional/operator usefulness rating is below 4/5.")
        if professional.jurisdiction_pathway_correct is not True:
            fail_reasons.append("Professional/operator did not confirm jurisdiction/pathway correctness.")
        if (professional.material_rule_traceability_percent or 0.0) < 100.0:
            fail_reasons.append("Material-rule source traceability is below 100%.")
        if professional.unsupported_legal_certainty_count is None:
            fail_reasons.append("Unsupported legal-certainty count was not recorded.")
        elif professional.unsupported_legal_certainty_count != 0:
            fail_reasons.append("Unsupported legal-certainty statements were identified.")
        if professional.missing_critical_document_count is None:
            fail_reasons.append("Missing critical-document count was not recorded.")
        elif professional.missing_critical_document_count != 0:
            fail_reasons.append("Critical document requirements were identified as missing.")

    missing_evidence = [value for value in required_evidence_types if value not in captured_evidence_types]
    if missing_evidence:
        held_reasons.append("Missing required validation evidence types: " + ", ".join(missing_evidence) + ".")

    if not missing_evidence:
        fail_reasons.extend(_evidence_integrity_failures(session, run, scenario, evidence))

    critical_open = sum(1 for item in findings if item.severity == "critical" and item.status != "resolved")
    high_open = sum(1 for item in findings if item.severity == "high" and item.status != "resolved")
    medium_low_untriaged = sum(
        1
        for item in findings
        if item.severity in BOARD_ACCEPTABLE_SEVERITIES and item.status not in TERMINAL_TRIAGE_STATUSES
    )
    if critical_open:
        fail_reasons.append(f"{critical_open} critical finding(s) remain unresolved.")
    if high_open:
        fail_reasons.append(f"{high_open} high finding(s) remain unresolved.")
    if medium_low_untriaged:
        held_reasons.append(f"{medium_low_untriaged} medium/low finding(s) still require triage or Board acceptance.")

    if fail_reasons:
        status = "failed"
        reasons = fail_reasons + held_reasons
    elif held_reasons:
        status = "held"
        reasons = held_reasons
    else:
        status = "passed"
        reasons = [
            "Both required external reviewers completed the workflow and met the acceptance thresholds.",
            "Material rule traceability is 100%, unsupported legal certainty is zero, and critical document omissions are zero.",
            "No critical/high finding remains unresolved and all medium/low findings are triaged, resolved, or Board-accepted.",
        ]

    return ExternalValidationGateRead(
        status=status,
        reasons=reasons,
        completed_reviewer_types=completed_reviewer_types,
        required_evidence_types=required_evidence_types,
        captured_evidence_types=captured_evidence_types,
        founder_intervention_count=run.founder_intervention_count,
        critical_open=critical_open,
        high_open=high_open,
        medium_low_untriaged=medium_low_untriaged,
    )


def evaluate_external_validation_run(
    session: Session,
    run_id: UUID,
    *,
    actor: str,
) -> ExternalValidationRun:
    run = session.get(ExternalValidationRun, run_id)
    if run is None:
        raise ValueError("External validation run not found")
    before = run.model_dump(mode="json")
    gate = external_validation_gate(session, run)
    now = now_utc()
    run.gate_status = gate.status
    run.gate_reasons_json = _dump(gate.reasons)
    run.evaluated_at = now
    run.updated_at = now
    if gate.status == "passed":
        run.status = "completed"
        run.workflow_completed_at = run.workflow_completed_at or now
    else:
        run.status = "in_review"
    session.add(run)
    record_audit(
        session,
        action="external_validation_gate_evaluated",
        entity_type="external_validation_run",
        entity_id=run.id,
        before_state=before,
        after_state={**run.model_dump(mode="json"), "gate": gate.model_dump(mode="json")},
        reason=f"Deterministic external-validation gate evaluated as {gate.status}.",
        actor=actor,
        source="external_validation_v13_10_2",
    )
    session.commit()
    session.refresh(run)
    return run


def external_validation_run_read(
    session: Session,
    run: ExternalValidationRun,
) -> ExternalValidationRunRead:
    scenario = session.get(ExternalValidationScenario, run.scenario_id)
    if scenario is None:
        raise ValueError("External validation scenario not found")
    reviews = session.exec(
        select(ExternalValidationReview)
        .where(ExternalValidationReview.run_id == run.id)
        .order_by(ExternalValidationReview.submitted_at.asc())
    ).all()
    findings = session.exec(
        select(ExternalValidationFinding)
        .where(ExternalValidationFinding.run_id == run.id)
        .order_by(ExternalValidationFinding.created_at.asc())
    ).all()
    evidence = session.exec(
        select(ExternalValidationEvidence)
        .where(ExternalValidationEvidence.run_id == run.id)
        .order_by(ExternalValidationEvidence.created_at.asc())
    ).all()
    payload = run.model_dump()
    payload["gate_reasons"] = _load(payload.pop("gate_reasons_json", None), [])
    payload["scenario"] = scenario_read(scenario)
    payload["reviews"] = [review_read(row) for row in reviews]
    payload["findings"] = [finding_read(row) for row in findings]
    payload["evidence"] = [evidence_read(row) for row in evidence]
    payload["gate"] = external_validation_gate(session, run)
    return ExternalValidationRunRead(**payload)


def get_external_validation_run(session: Session, run_id: UUID) -> ExternalValidationRunRead:
    run = session.get(ExternalValidationRun, run_id)
    if run is None:
        raise ValueError("External validation run not found")
    return external_validation_run_read(session, run)


def list_external_validation_runs(
    session: Session,
    *,
    gate_status: str | None = None,
    scenario_id: UUID | None = None,
    limit: int = 100,
) -> list[ExternalValidationRunRead]:
    statement = select(ExternalValidationRun).order_by(ExternalValidationRun.created_at.desc())
    if gate_status:
        statement = statement.where(ExternalValidationRun.gate_status == gate_status.strip().lower())
    if scenario_id:
        statement = statement.where(ExternalValidationRun.scenario_id == scenario_id)
    rows = session.exec(statement.limit(max(1, min(limit, 200)))).all()
    return [external_validation_run_read(session, row) for row in rows]


def latest_external_validation_gate(session: Session) -> ExternalValidationRunRead | None:
    rows = session.exec(
        select(ExternalValidationRun).order_by(ExternalValidationRun.created_at.desc()).limit(1)
    ).all()
    if not rows:
        return None
    return external_validation_run_read(session, rows[0])


def external_validation_gate_passed(session: Session) -> bool:
    rows = session.exec(
        select(ExternalValidationRun).where(ExternalValidationRun.gate_status == "passed").limit(1)
    ).all()
    return bool(rows)

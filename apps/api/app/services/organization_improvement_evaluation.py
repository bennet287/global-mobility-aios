from __future__ import annotations

import json
import math
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationRecordReference, OrganizationReferenceRole, now_utc
from app.models.organization_improvement_evaluation import (
    OrganizationImprovementEvaluationCampaign,
    OrganizationImprovementEvaluationReport,
)
from app.models.organization_improvement_lineage import (
    OrganizationImprovementCandidate,
    OrganizationImprovementProposal,
)
from app.schemas_organization_improvement_evaluation import (
    ImprovementEvaluationCampaignRead,
    ImprovementEvaluationConstraint,
    ImprovementEvaluationConstraintResult,
    ImprovementEvaluationReportRead,
)
from app.services.organization_command import (
    AuditMutation,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_json,
    canonical_payload_json,
    commit_mutations,
    idempotent_existing,
    require_human,
    tenant_record,
)
from app.services.organization_improvement_lineage import _proposal_is_current


_EVALUATOR_ACTOR_TYPES = frozenset({"human", "agent", "worker", "system", "external_human"})
_COMPARISON_OPERATORS = frozenset(
    {
        "candidate_gte_baseline_plus",
        "candidate_lte_baseline_plus",
        "candidate_gte",
        "candidate_lte",
    }
)


def _required(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidReference(f"{label} is required")
    return normalized


def _sha256(label: str, value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
        raise InvalidReference(f"{label} must be a lowercase SHA-256 hex digest")
    return normalized


def _evidence_ids(
    session: Session,
    context: OrganizationCommandContext,
    reference_ids: list[UUID],
    *,
    label: str,
) -> tuple[UUID, ...]:
    if not reference_ids or len(set(reference_ids)) != len(reference_ids):
        raise InvalidReference(f"{label} requires unique concrete evidence references")
    resolved: list[UUID] = []
    for reference_id in reference_ids:
        row = tenant_record(
            session,
            OrganizationRecordReference,
            reference_id,
            context.tenant_key,
            label=label,
        )
        if row.reference_role is not OrganizationReferenceRole.evidence:
            raise InvalidReference(f"{label} references must use the evidence role")
        resolved.append(row.id)
    return tuple(sorted(resolved, key=str))


def _author_identities(values: list[str]) -> tuple[str, ...]:
    normalized = tuple(sorted({_required("candidate author identity", value) for value in values}))
    if not normalized:
        raise InvalidReference("at least one candidate author identity is required")
    if len(normalized) != len(values):
        raise InvalidReference("candidate author identities must be unique")
    return normalized


def _constraints(values: list[ImprovementEvaluationConstraint | dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    if not values:
        raise InvalidReference("evaluation campaign requires regression constraints")
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str, float]] = set()
    for raw in values:
        item = raw.model_dump() if isinstance(raw, ImprovementEvaluationConstraint) else dict(raw)
        metric_key = _required("constraint metric key", str(item.get("metric_key") or ""))
        operator = str(item.get("operator") or "").strip()
        if operator not in _COMPARISON_OPERATORS:
            raise InvalidReference("evaluation constraint operator is unsupported")
        value = item.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise InvalidReference("evaluation constraint values must be finite numbers")
        numeric = float(value)
        identity = (metric_key, operator, numeric)
        if identity in seen:
            raise InvalidReference("evaluation constraints must be unique")
        seen.add(identity)
        normalized.append({"metric_key": metric_key, "operator": operator, "value": numeric})
    return tuple(sorted(normalized, key=lambda item: (item["metric_key"], item["operator"], item["value"])))


def _measurements(label: str, values: dict[str, float]) -> dict[str, float]:
    if not values:
        raise InvalidReference(f"{label} measurements are required")
    normalized: dict[str, float] = {}
    for key, raw in values.items():
        metric_key = _required(f"{label} metric key", key)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
            raise InvalidReference(f"{label} measurements must be finite numbers")
        normalized[metric_key] = float(raw)
    return dict(sorted(normalized.items()))


def _eligible_candidate(
    session: Session,
    context: OrganizationCommandContext,
    candidate_id: UUID,
) -> tuple[OrganizationImprovementCandidate, OrganizationImprovementProposal]:
    candidate = tenant_record(
        session,
        OrganizationImprovementCandidate,
        candidate_id,
        context.tenant_key,
        label="improvement candidate",
    )
    if candidate.status != "prepared":
        raise InvalidTransition("evaluation requires a prepared improvement candidate")
    proposal = tenant_record(
        session,
        OrganizationImprovementProposal,
        candidate.proposal_id,
        context.tenant_key,
        label="improvement proposal",
    )
    if not _proposal_is_current(session, proposal):
        raise InvalidTransition("evaluation requires a current open improvement proposal")
    return candidate, proposal


def _constraint_results(
    constraints: tuple[dict[str, Any], ...],
    baseline: dict[str, float],
    candidate: dict[str, float],
) -> tuple[dict[str, Any], ...]:
    results: list[dict[str, Any]] = []
    for constraint in constraints:
        metric = constraint["metric_key"]
        operator = constraint["operator"]
        threshold = float(constraint["value"])
        if metric not in candidate:
            raise InvalidReference(f"candidate measurement is missing constrained metric {metric!r}")
        candidate_value = candidate[metric]
        baseline_value: float | None = None
        if operator in {"candidate_gte_baseline_plus", "candidate_lte_baseline_plus"}:
            if metric not in baseline:
                raise InvalidReference(f"baseline measurement is missing constrained metric {metric!r}")
            baseline_value = baseline[metric]
            boundary = baseline_value + threshold
            passed = candidate_value >= boundary if operator == "candidate_gte_baseline_plus" else candidate_value <= boundary
        elif operator == "candidate_gte":
            passed = candidate_value >= threshold
        else:
            passed = candidate_value <= threshold
        results.append(
            {
                "metric_key": metric,
                "operator": operator,
                "value": threshold,
                "baseline_value": baseline_value,
                "candidate_value": candidate_value,
                "passed": bool(passed),
            }
        )
    return tuple(results)


def create_evaluation_campaign(
    session: Session,
    context: OrganizationCommandContext,
    *,
    campaign_key: str,
    campaign_version: int,
    candidate_id: UUID,
    candidate_author_identities: list[str],
    candidate_author_evidence_reference_ids: list[UUID],
    evaluation_set_key: str,
    evaluation_set_version: str,
    evaluation_set_fingerprint: str,
    evaluation_set_reference_ids: list[UUID],
    regression_constraints: list[ImprovementEvaluationConstraint | dict[str, Any]],
    required_structurally_separate_evaluators: int = 1,
) -> OrganizationImprovementEvaluationCampaign:
    require_human(context, admin=True)
    candidate, proposal = _eligible_candidate(session, context, candidate_id)
    campaign_key = _required("campaign key", campaign_key)
    if campaign_version < 1:
        raise InvalidReference("campaign version must be positive")
    if required_structurally_separate_evaluators < 1 or required_structurally_separate_evaluators > 20:
        raise InvalidReference("required structurally separate evaluators must be between 1 and 20")
    authors = _author_identities(candidate_author_identities)
    author_evidence_ids = _evidence_ids(
        session,
        context,
        candidate_author_evidence_reference_ids,
        label="candidate author evidence",
    )
    evaluation_set_key = _required("evaluation set key", evaluation_set_key)
    evaluation_set_version = _required("evaluation set version", evaluation_set_version)
    evaluation_set_fingerprint = _sha256("evaluation set fingerprint", evaluation_set_fingerprint)
    evaluation_set_ids = _evidence_ids(
        session,
        context,
        evaluation_set_reference_ids,
        label="evaluation set evidence",
    )
    normalized_constraints = _constraints(regression_constraints)

    command = {
        "tenant_key": context.tenant_key,
        "campaign_key": campaign_key,
        "campaign_version": campaign_version,
        "candidate_id": str(candidate.id),
        "proposal_id": str(proposal.id),
        "target_type": candidate.target_type,
        "target_reference": candidate.target_reference,
        "baseline_version": candidate.baseline_version,
        "baseline_fingerprint": candidate.baseline_fingerprint,
        "candidate_version": candidate.candidate_version,
        "candidate_fingerprint": candidate.candidate_fingerprint,
        "candidate_author_identities": authors,
        "candidate_author_evidence_reference_ids": tuple(str(value) for value in author_evidence_ids),
        "evaluation_set_key": evaluation_set_key,
        "evaluation_set_version": evaluation_set_version,
        "evaluation_set_fingerprint": evaluation_set_fingerprint,
        "evaluation_set_reference_ids": tuple(str(value) for value in evaluation_set_ids),
        "regression_constraints": normalized_constraints,
        "required_structurally_separate_evaluators": required_structurally_separate_evaluators,
        "status": "open",
        "comparison_conclusion": "not_assessed",
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationImprovementEvaluationCampaign).where(
            OrganizationImprovementEvaluationCampaign.tenant_key == context.tenant_key,
            OrganizationImprovementEvaluationCampaign.campaign_key == campaign_key,
        )
    ).first()
    replay = idempotent_existing(
        existing,
        fingerprint,
        fingerprint_field="record_fingerprint",
        label="improvement evaluation campaign",
    )
    if replay is not None:
        return replay

    row = OrganizationImprovementEvaluationCampaign(
        tenant_key=context.tenant_key,
        campaign_key=campaign_key,
        campaign_version=campaign_version,
        candidate_id=candidate.id,
        proposal_id=proposal.id,
        target_type=candidate.target_type,
        target_reference=candidate.target_reference,
        baseline_version=candidate.baseline_version,
        baseline_fingerprint=candidate.baseline_fingerprint,
        candidate_version=candidate.candidate_version,
        candidate_fingerprint=candidate.candidate_fingerprint,
        candidate_author_identities_json=canonical_json(list(authors)),
        candidate_author_evidence_reference_ids_json=canonical_json([str(value) for value in author_evidence_ids]),
        evaluation_set_key=evaluation_set_key,
        evaluation_set_version=evaluation_set_version,
        evaluation_set_fingerprint=evaluation_set_fingerprint,
        evaluation_set_reference_ids_json=canonical_json([str(value) for value in evaluation_set_ids]),
        regression_constraints_json=canonical_json(list(normalized_constraints)),
        required_structurally_separate_evaluators=required_structurally_separate_evaluators,
        status="open",
        comparison_conclusion="not_assessed",
        record_fingerprint=fingerprint,
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.improvement.evaluation_campaign.create",
                "organization_improvement_evaluation_campaign",
                row.id,
                after_state=row,
                reason="authority-neutral current-vs-candidate evaluation campaign created",
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def record_evaluation_report(
    session: Session,
    context: OrganizationCommandContext,
    *,
    campaign_id: UUID,
    report_key: str,
    evaluator_actor_type: str,
    evaluator_identity: str,
    evaluator_independence_group: str,
    independence_evidence_reference_ids: list[UUID],
    baseline_measurements: dict[str, float],
    candidate_measurements: dict[str, float],
    evaluation_evidence_reference_ids: list[UUID],
    reproducibility_reference_ids: list[UUID],
) -> OrganizationImprovementEvaluationReport:
    require_human(context, admin=True)
    campaign = tenant_record(
        session,
        OrganizationImprovementEvaluationCampaign,
        campaign_id,
        context.tenant_key,
        label="improvement evaluation campaign",
    )
    if campaign.status != "open":
        raise InvalidTransition("evaluation reports can be recorded only while the campaign is open")
    _eligible_candidate(session, context, campaign.candidate_id)
    report_key = _required("report key", report_key)
    evaluator_actor_type = _required("evaluator actor type", evaluator_actor_type)
    if evaluator_actor_type not in _EVALUATOR_ACTOR_TYPES:
        raise InvalidReference("evaluator actor type is unsupported")
    evaluator_identity = _required("evaluator identity", evaluator_identity)
    evaluator_independence_group = _required("evaluator independence group", evaluator_independence_group)
    independence_ids = _evidence_ids(
        session,
        context,
        independence_evidence_reference_ids,
        label="evaluator independence evidence",
    )
    evaluation_ids = _evidence_ids(
        session,
        context,
        evaluation_evidence_reference_ids,
        label="evaluation evidence",
    )
    reproducibility_ids = _evidence_ids(
        session,
        context,
        reproducibility_reference_ids,
        label="reproducibility evidence",
    )
    baseline = _measurements("baseline", baseline_measurements)
    candidate = _measurements("candidate", candidate_measurements)
    constraints = tuple(json.loads(campaign.regression_constraints_json))
    results = _constraint_results(constraints, baseline, candidate)
    satisfied = all(item["passed"] for item in results)

    command = {
        "tenant_key": context.tenant_key,
        "report_key": report_key,
        "campaign_id": str(campaign.id),
        "campaign_record_fingerprint": campaign.record_fingerprint,
        "evaluator_actor_type": evaluator_actor_type,
        "evaluator_identity": evaluator_identity,
        "evaluator_independence_group": evaluator_independence_group,
        "independence_evidence_reference_ids": tuple(str(value) for value in independence_ids),
        "baseline_measurements": baseline,
        "candidate_measurements": candidate,
        "constraint_results": results,
        "evaluation_evidence_reference_ids": tuple(str(value) for value in evaluation_ids),
        "reproducibility_reference_ids": tuple(str(value) for value in reproducibility_ids),
        "constraints_satisfied": satisfied,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationImprovementEvaluationReport).where(
            OrganizationImprovementEvaluationReport.tenant_key == context.tenant_key,
            OrganizationImprovementEvaluationReport.report_key == report_key,
        )
    ).first()
    replay = idempotent_existing(
        existing,
        fingerprint,
        fingerprint_field="record_fingerprint",
        label="improvement evaluation report",
    )
    if replay is not None:
        return replay

    row = OrganizationImprovementEvaluationReport(
        tenant_key=context.tenant_key,
        report_key=report_key,
        campaign_id=campaign.id,
        evaluator_actor_type=evaluator_actor_type,
        evaluator_identity=evaluator_identity,
        evaluator_independence_group=evaluator_independence_group,
        independence_evidence_reference_ids_json=canonical_json([str(value) for value in independence_ids]),
        baseline_measurements_json=canonical_payload_json(baseline),
        candidate_measurements_json=canonical_payload_json(candidate),
        constraint_results_json=canonical_json(list(results)),
        evaluation_evidence_reference_ids_json=canonical_json([str(value) for value in evaluation_ids]),
        reproducibility_reference_ids_json=canonical_json([str(value) for value in reproducibility_ids]),
        constraints_satisfied=satisfied,
        record_fingerprint=fingerprint,
        recorded_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.improvement.evaluation_report.record",
                "organization_improvement_evaluation_report",
                row.id,
                after_state=row,
                reason="comparison evidence recorded without promotion or authority effect",
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def close_evaluation_campaign(
    session: Session,
    context: OrganizationCommandContext,
    *,
    campaign_id: UUID,
) -> OrganizationImprovementEvaluationCampaign:
    require_human(context, admin=True)
    row = tenant_record(
        session,
        OrganizationImprovementEvaluationCampaign,
        campaign_id,
        context.tenant_key,
        label="improvement evaluation campaign",
    )
    if row.status == "closed":
        return row
    _eligible_candidate(session, context, row.candidate_id)
    reports = tuple(
        session.exec(
            select(OrganizationImprovementEvaluationReport).where(
                OrganizationImprovementEvaluationReport.tenant_key == context.tenant_key,
                OrganizationImprovementEvaluationReport.campaign_id == row.id,
            )
        ).all()
    )
    if not reports:
        raise InvalidTransition("evaluation campaign cannot close without reports")
    authors = set(json.loads(row.candidate_author_identities_json))
    separate_evaluators = {report.evaluator_identity for report in reports if report.evaluator_identity not in authors}
    if len(separate_evaluators) < row.required_structurally_separate_evaluators:
        raise InvalidTransition(
            "evaluation campaign lacks the required structurally separate non-author evaluators"
        )
    before = row.model_dump()
    row.status = "closed"
    row.comparison_conclusion = (
        "constraints_met" if all(report.constraints_satisfied for report in reports) else "constraints_not_met"
    )
    row.closed_by = context.actor_id
    row.closed_at = now_utc()
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.improvement.evaluation_campaign.close",
                "organization_improvement_evaluation_campaign",
                row.id,
                before_state=before,
                after_state=row,
                reason="declared comparison campaign closed; no promotion or authority granted",
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def project_evaluation_campaign(row: OrganizationImprovementEvaluationCampaign) -> ImprovementEvaluationCampaignRead:
    return ImprovementEvaluationCampaignRead(
        **row.model_dump(),
        candidate_author_identities=tuple(json.loads(row.candidate_author_identities_json)),
        candidate_author_evidence_reference_ids=tuple(
            UUID(value) for value in json.loads(row.candidate_author_evidence_reference_ids_json)
        ),
        evaluation_set_reference_ids=tuple(UUID(value) for value in json.loads(row.evaluation_set_reference_ids_json)),
        regression_constraints=tuple(
            ImprovementEvaluationConstraint(**item) for item in json.loads(row.regression_constraints_json)
        ),
    )


def project_evaluation_report(row: OrganizationImprovementEvaluationReport) -> ImprovementEvaluationReportRead:
    return ImprovementEvaluationReportRead(
        **row.model_dump(),
        independence_evidence_reference_ids=tuple(
            UUID(value) for value in json.loads(row.independence_evidence_reference_ids_json)
        ),
        baseline_measurements=json.loads(row.baseline_measurements_json),
        candidate_measurements=json.loads(row.candidate_measurements_json),
        constraint_results=tuple(
            ImprovementEvaluationConstraintResult(**item) for item in json.loads(row.constraint_results_json)
        ),
        evaluation_evidence_reference_ids=tuple(
            UUID(value) for value in json.loads(row.evaluation_evidence_reference_ids_json)
        ),
        reproducibility_reference_ids=tuple(
            UUID(value) for value in json.loads(row.reproducibility_reference_ids_json)
        ),
    )


def list_evaluation_campaigns(
    session: Session,
    context: OrganizationCommandContext,
) -> tuple[ImprovementEvaluationCampaignRead, ...]:
    require_human(context, admin=True)
    rows = session.exec(
        select(OrganizationImprovementEvaluationCampaign)
        .where(OrganizationImprovementEvaluationCampaign.tenant_key == context.tenant_key)
        .order_by(
            OrganizationImprovementEvaluationCampaign.created_at.desc(),
            OrganizationImprovementEvaluationCampaign.id.desc(),
        )
    ).all()
    return tuple(project_evaluation_campaign(row) for row in rows)


def list_evaluation_reports(
    session: Session,
    context: OrganizationCommandContext,
    *,
    campaign_id: UUID,
) -> tuple[ImprovementEvaluationReportRead, ...]:
    require_human(context, admin=True)
    tenant_record(
        session,
        OrganizationImprovementEvaluationCampaign,
        campaign_id,
        context.tenant_key,
        label="improvement evaluation campaign",
    )
    rows = session.exec(
        select(OrganizationImprovementEvaluationReport)
        .where(
            OrganizationImprovementEvaluationReport.tenant_key == context.tenant_key,
            OrganizationImprovementEvaluationReport.campaign_id == campaign_id,
        )
        .order_by(
            OrganizationImprovementEvaluationReport.recorded_at.asc(),
            OrganizationImprovementEvaluationReport.id.asc(),
        )
    ).all()
    return tuple(project_evaluation_report(row) for row in rows)

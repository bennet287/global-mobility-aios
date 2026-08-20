from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlmodel import Session

from app.core.organization_constitution import MaterialActionType, RiskTier
from app.models.domain import Lead, MobilityPathway, MobilityPathwayVersion, OrganizationActivity, Profile, now_utc
from app.services.mobility_profiles import case_facts, current_mobility_profile
from app.services.organization_command import OrganizationCommandError, canonical_fingerprint
from app.services.organization_context_broker import (
    ContextBrokerError,
    ContextBundle,
    ContextPurpose,
    ContextReference,
    build_work_item_context_bundle,
)
from app.services.organization_eligibility_transition_intent import (
    ELIGIBILITY_INTENT_SCHEMA_VERSION,
    EligibilityProposedState,
    GovernedEligibilityTransitionIntentResult,
)
from app.services.organization_governance_kernel import GatewayOutcome, GatewayReason
from app.services.organization_transparency import TransparencyDataError, transparency_activity_record
from app.services.pathway_catalogue import _publication_evidence_blockers


DECISION_READINESS_SCHEMA_VERSION = "eligibility-decision-readiness.v1"


class DecisionReadinessError(RuntimeError):
    """Base error for the deterministic F.1 Decision Readiness vertical."""


class DecisionReadinessIntegrityError(DecisionReadinessError):
    """The accepted E.2 proposal or its canonical inputs are stale or inconsistent."""


class DecisionReadinessState(str, Enum):
    READY_FOR_INDEPENDENT_VERIFICATION = "ready_for_independent_verification"
    NOT_READY = "not_ready"
    HUMAN_INPUT_REQUIRED = "human_input_required"


class DecisionReadinessGateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    HUMAN_REQUIRED = "human_required"


class DecisionReadinessGateCode(str, Enum):
    PROPOSAL_STATE_ACTIONABLE = "proposal_state_actionable"
    GOVERNED_AUTHORITY_COMPLETE = "governed_authority_complete"
    REQUIRED_CASE_FACTS_PRESENT = "required_case_facts_present"
    PATHWAY_PUBLICATION_INTEGRITY = "pathway_publication_integrity"
    MATERIAL_FACT_PRECONDITIONS = "material_fact_preconditions"


@dataclass(frozen=True)
class DecisionReadinessGate:
    code: DecisionReadinessGateCode
    status: DecisionReadinessGateStatus
    detail: str


@dataclass(frozen=True)
class EligibilityDecisionReadinessResult:
    schema_version: str
    state: DecisionReadinessState
    readiness_score: float
    gates: tuple[DecisionReadinessGate, ...]
    intent_fingerprint: str
    context_hash: str
    profile_id: UUID
    profile_version: int
    pathway_version_id: UUID
    readiness_fingerprint: str
    assessed_at: datetime
    ready_for_independent_verification: bool
    independent_verification_required: bool = True
    authorization_effect: bool = False
    canonical_commit_allowed: bool = False


def _single_reference(context: ContextBundle, kind: str) -> ContextReference:
    matches = [reference for reference in context.canonical_references if reference.kind == kind]
    if len(matches) != 1:
        raise DecisionReadinessIntegrityError(
            f"Decision Readiness requires exactly one {kind} ContextBundle reference"
        )
    return matches[0]


def _record_reference(
    session: Session,
    *,
    context: ContextBundle,
    kind: str,
    model: type[Any],
) -> Any:
    reference = _single_reference(context, kind)
    try:
        record_id = UUID(reference.identifier)
    except (TypeError, ValueError, AttributeError) as exc:
        raise DecisionReadinessIntegrityError(f"{kind} ContextBundle reference is not a UUID") from exc
    record = session.get(model, record_id)
    if record is None:
        raise DecisionReadinessIntegrityError(f"{kind} ContextBundle reference could not be dereferenced")

    expected = canonical_fingerprint(record)
    if kind == "mobility_pathway_version":
        pathway = session.get(MobilityPathway, record.pathway_id)
        if pathway is None:
            raise DecisionReadinessIntegrityError("mobility pathway parent was not found")
        expected = canonical_fingerprint({"pathway": pathway, "pathway_version": record})
    if reference.version != expected:
        raise DecisionReadinessIntegrityError(f"{kind} changed after the accepted E.2 proposal")
    return record


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r} is not permitted")


def _json_object(raw: str | None, *, label: str) -> dict[str, Any]:
    candidate = raw if raw not in (None, "") else "{}"
    try:
        decoded = json.loads(candidate, parse_constant=_reject_json_constant)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DecisionReadinessIntegrityError(f"{label} is not valid JSON") from exc
    if not isinstance(decoded, dict):
        raise DecisionReadinessIntegrityError(f"{label} must be a JSON object")
    return decoded


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _attempt_integrity(
    session: Session,
    proposal: GovernedEligibilityTransitionIntentResult,
) -> None:
    if proposal.schema_version != ELIGIBILITY_INTENT_SCHEMA_VERSION:
        raise DecisionReadinessIntegrityError("unsupported E.2 eligibility-intent schema")
    if proposal.mutated:
        raise DecisionReadinessIntegrityError("Decision Readiness cannot consume an already-mutated proposal")
    if proposal.evaluation.outcome is not GatewayOutcome.REVIEW_REQUIRED:
        raise DecisionReadinessIntegrityError(
            "Decision Readiness accepts only E.2 proposals routed to REVIEW_REQUIRED"
        )
    if proposal.evaluation.reason is not GatewayReason.POLICY_REVIEW_REQUIRED:
        raise DecisionReadinessIntegrityError(
            "E.2 proposal is missing the explicit R3 verification review floor"
        )
    if proposal.evaluation.effective_risk_tier is not RiskTier.R3:
        raise DecisionReadinessIntegrityError("eligibility proposal no longer carries the R3 risk floor")
    if proposal.intent_fingerprint != canonical_fingerprint(proposal.intent):
        raise DecisionReadinessIntegrityError("eligibility intent fingerprint does not match the typed proposal")

    activity = session.get(OrganizationActivity, proposal.attempt_activity.id)
    if activity is None:
        raise DecisionReadinessIntegrityError("durable E.2 governance attempt was not found")
    try:
        record = transparency_activity_record(activity)
    except TransparencyDataError as exc:
        raise DecisionReadinessIntegrityError("durable E.2 governance attempt is malformed") from exc

    position_key = proposal.context.position.position_key
    if record.actor_id != position_key or record.position_key != position_key:
        raise DecisionReadinessIntegrityError("durable E.2 governance attempt has a different employee identity")
    if record.source_object_type != "lead_eligibility" or record.source_object_id != str(proposal.intent.lead_id):
        raise DecisionReadinessIntegrityError("durable E.2 governance attempt targets a different eligibility subject")
    if record.trace_id != str(proposal.evaluation.trace_id):
        raise DecisionReadinessIntegrityError("E.2 governance trace identity does not match the proposal")
    if record.work_item_id != proposal.intent.work_item_id:
        raise DecisionReadinessIntegrityError("E.2 governance attempt is linked to a different WorkItem")

    payload = record.payload
    expected_payload = {
        "governance_record_kind": "eligibility_intent_attempt",
        "actor_id": position_key,
        "action_type": MaterialActionType.ELIGIBILITY_TRANSITION.value,
        "outcome": GatewayOutcome.REVIEW_REQUIRED.value,
        "reason": GatewayReason.POLICY_REVIEW_REQUIRED.value,
        "effective_risk_tier": RiskTier.R3.value,
        "action_fingerprint": proposal.evaluation.action_fingerprint,
        "intent_fingerprint": proposal.intent_fingerprint,
        "context_hash": proposal.context.context_hash,
        "runtime_binding_hash": proposal.runtime_binding.binding_hash,
        "profile_id": str(proposal.intent.profile_id),
        "profile_version": proposal.intent.profile_version,
        "pathway_version_id": str(proposal.intent.pathway_version_id),
        "r3_verification_floor": "independent_verification_not_yet_satisfied",
    }
    for key, expected in expected_payload.items():
        if payload.get(key) != expected:
            raise DecisionReadinessIntegrityError(
                f"durable E.2 governance attempt does not match proposal field {key!r}"
            )


def _fresh_context(
    session: Session,
    proposal: GovernedEligibilityTransitionIntentResult,
) -> ContextBundle:
    try:
        current = build_work_item_context_bundle(
            session,
            tenant_key=proposal.context.tenant_key,
            position_key=proposal.context.position.position_key,
            work_item_id=proposal.intent.work_item_id,
            purpose=ContextPurpose.REVIEW,
        )
    except (ContextBrokerError, OrganizationCommandError) as exc:
        raise DecisionReadinessIntegrityError(
            "governed context is no longer eligible for Decision Readiness"
        ) from exc
    if current.context_hash != proposal.context.context_hash:
        raise DecisionReadinessIntegrityError("ContextBundle changed after the accepted E.2 proposal")
    if proposal.runtime_binding.context_hash != current.context_hash:
        raise DecisionReadinessIntegrityError("runtime binding no longer matches the accepted context")
    if proposal.runtime_binding.position_key != current.position.position_key:
        raise DecisionReadinessIntegrityError("runtime binding employee identity does not match ContextBundle")
    return current


def _lead_domain(lead: Lead) -> str:
    value = getattr(lead.intent, "value", lead.intent)
    normalized = str(value or "unknown").strip().casefold()
    if normalized in {"study_abroad", "study", "student"}:
        return "study"
    if normalized in {"overseas_job", "work", "job", "employment"}:
        return "work"
    if normalized in {"visa", "permanent", "residency", "immigration"}:
        return "visa"
    return "general"


def _current_domain_state(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    context: ContextBundle,
) -> tuple[Lead, Profile, MobilityPathway, MobilityPathwayVersion, dict[str, Any]]:
    lead = _record_reference(session, context=context, kind="lead", model=Lead)
    profile = _record_reference(session, context=context, kind="profile", model=Profile)
    pathway_version = _record_reference(
        session,
        context=context,
        kind="mobility_pathway_version",
        model=MobilityPathwayVersion,
    )
    pathway = session.get(MobilityPathway, pathway_version.pathway_id)
    if pathway is None:
        raise DecisionReadinessIntegrityError("mobility pathway parent was not found")

    if lead.id != proposal.intent.lead_id:
        raise DecisionReadinessIntegrityError("accepted eligibility intent references a different Lead")
    if profile.id != proposal.intent.profile_id or profile.profile_version != proposal.intent.profile_version:
        raise DecisionReadinessIntegrityError("accepted eligibility intent profile precondition is stale")
    if pathway_version.id != proposal.intent.pathway_version_id:
        raise DecisionReadinessIntegrityError("accepted eligibility intent references a different pathway version")
    if profile.lead_id != lead.id:
        raise DecisionReadinessIntegrityError("current Profile does not belong to the accepted Lead")

    current_profile = current_mobility_profile(session, lead.id)
    if current_profile is None or current_profile.id != profile.id:
        raise DecisionReadinessIntegrityError("accepted Profile is no longer the current mobility profile")
    if profile.lifecycle_status != "active" or profile.consent_status != "granted":
        raise DecisionReadinessIntegrityError("accepted Profile is no longer active with granted consent")

    facts = case_facts(session, lead, profile)
    target_country = str(facts.get("target_country") or "").strip().casefold()
    if target_country != pathway.country.casefold():
        raise DecisionReadinessIntegrityError("case target country no longer matches the governed pathway")
    if _lead_domain(lead).casefold() != pathway.domain.casefold():
        raise DecisionReadinessIntegrityError("case mobility domain no longer matches the governed pathway")
    return lead, profile, pathway, pathway_version, facts


def _authority_basis_integrity(
    proposal: GovernedEligibilityTransitionIntentResult,
    context: ContextBundle,
) -> None:
    evidence = {
        f"evidence:{reference.identifier}"
        for reference in context.evidence_refs
        if reference.kind == "mobility_pathway_version_evidence"
    }
    rules = {
        f"verified_rule:{reference.identifier}"
        for reference in context.verified_rule_refs
        if reference.kind == "verified_rule"
    }
    if not proposal.intent.evidence_basis or any(item not in evidence for item in proposal.intent.evidence_basis):
        raise DecisionReadinessIntegrityError("accepted intent Evidence basis is outside current governed authority")
    if not proposal.intent.rule_basis or any(item not in rules for item in proposal.intent.rule_basis):
        raise DecisionReadinessIntegrityError("accepted intent VerifiedRule basis is outside current governed authority")


def _proposal_state_gate(proposal: GovernedEligibilityTransitionIntentResult) -> DecisionReadinessGate:
    actionable = proposal.intent.proposed_state in {
        EligibilityProposedState.POTENTIALLY_ELIGIBLE,
        EligibilityProposedState.POTENTIALLY_INELIGIBLE,
    }
    return DecisionReadinessGate(
        code=DecisionReadinessGateCode.PROPOSAL_STATE_ACTIONABLE,
        status=(DecisionReadinessGateStatus.PASS if actionable else DecisionReadinessGateStatus.FAIL),
        detail=(
            "The E.2 proposal contains a bounded eligibility conclusion candidate."
            if actionable
            else "The E.2 proposal itself reports insufficient information or missing documents."
        ),
    )


def _authority_complete_gate(context: ContextBundle) -> DecisionReadinessGate:
    complete = (
        not context.unknowns
        and not context.contradictions
        and bool(context.evidence_refs)
        and bool(context.verified_rule_refs)
        and context.policy_version is not None
    )
    blockers: list[str] = []
    if context.unknowns:
        blockers.append("authority unknowns remain")
    if context.contradictions:
        blockers.append("authority contradictions remain")
    if not context.evidence_refs:
        blockers.append("governed pathway Evidence is missing")
    if not context.verified_rule_refs:
        blockers.append("governed VerifiedRules are missing")
    if context.policy_version is None:
        blockers.append("active CountryPolicy is missing")
    return DecisionReadinessGate(
        code=DecisionReadinessGateCode.GOVERNED_AUTHORITY_COMPLETE,
        status=(DecisionReadinessGateStatus.PASS if complete else DecisionReadinessGateStatus.FAIL),
        detail=(
            "Governed Evidence, VerifiedRules and CountryPolicy are complete with no unresolved authority contradictions."
            if complete
            else "; ".join(blockers)
        ),
    )


def _required_case_facts_gate(facts: dict[str, Any]) -> DecisionReadinessGate:
    required = ("nationality", "target_country", "goal")
    missing = [name for name in required if not _present(facts.get(name))]
    return DecisionReadinessGate(
        code=DecisionReadinessGateCode.REQUIRED_CASE_FACTS_PRESENT,
        status=(
            DecisionReadinessGateStatus.PASS
            if not missing
            else DecisionReadinessGateStatus.HUMAN_REQUIRED
        ),
        detail=(
            "Minimum structured case facts required to brief an independent verifier are present."
            if not missing
            else "Human input is required for case facts: " + ", ".join(missing)
        ),
    )


def _publication_integrity_gate(
    session: Session,
    *,
    pathway: MobilityPathway,
    pathway_version: MobilityPathwayVersion,
) -> DecisionReadinessGate:
    # Reuse the mature pathway publication checks rather than creating a second
    # interpretation of source certification, evidence-role and rule-provenance
    # requirements. Keep this bounded internal dependency until another real
    # consumer demonstrates a stable public extraction is warranted.
    try:
        blockers = _publication_evidence_blockers(session, pathway, pathway_version)
    except ValueError as exc:
        raise DecisionReadinessIntegrityError("pathway publication integrity could not be evaluated") from exc
    return DecisionReadinessGate(
        code=DecisionReadinessGateCode.PATHWAY_PUBLICATION_INTEGRITY,
        status=(DecisionReadinessGateStatus.PASS if not blockers else DecisionReadinessGateStatus.FAIL),
        detail=(
            "Current pathway Evidence still satisfies deterministic publication-integrity requirements."
            if not blockers
            else " | ".join(blockers)
        ),
    )


def _material_fact_gate(
    *,
    pathway: MobilityPathway,
    pathway_version: MobilityPathwayVersion,
    facts: dict[str, Any],
) -> DecisionReadinessGate:
    criteria = _json_object(pathway_version.eligibility_criteria_json, label="pathway eligibility criteria")
    requires_austrian_offer = criteria.get("binding_job_offer_in_austria_required")
    if requires_austrian_offer is not None and not isinstance(requires_austrian_offer, bool):
        raise DecisionReadinessIntegrityError(
            "binding_job_offer_in_austria_required must be a boolean when present"
        )
    if requires_austrian_offer is True:
        if pathway.country.casefold() != "austria":
            raise DecisionReadinessIntegrityError(
                "Austrian binding-job-offer criterion is attached to a non-Austrian pathway"
            )
        has_offer = facts.get("has_job_offer")
        if has_offer is True:
            status = DecisionReadinessGateStatus.PASS
            detail = "The structured case records the binding Austrian job-offer precondition as satisfied."
        elif has_offer is False:
            status = DecisionReadinessGateStatus.FAIL
            detail = "The governed pathway requires a binding Austrian job offer and the case records none."
        else:
            status = DecisionReadinessGateStatus.HUMAN_REQUIRED
            detail = "The governed pathway requires a binding Austrian job offer but the case fact is unresolved."
        return DecisionReadinessGate(
            code=DecisionReadinessGateCode.MATERIAL_FACT_PRECONDITIONS,
            status=status,
            detail=detail,
        )

    return DecisionReadinessGate(
        code=DecisionReadinessGateCode.MATERIAL_FACT_PRECONDITIONS,
        status=DecisionReadinessGateStatus.PASS,
        detail=(
            "No F.1-supported structured material-fact precondition is unresolved. "
            "Substantive eligibility remains the responsibility of the independent verifier, not this readiness gate."
        ),
    )


def _state(gates: tuple[DecisionReadinessGate, ...]) -> DecisionReadinessState:
    if any(gate.status is DecisionReadinessGateStatus.FAIL for gate in gates):
        return DecisionReadinessState.NOT_READY
    if any(gate.status is DecisionReadinessGateStatus.HUMAN_REQUIRED for gate in gates):
        return DecisionReadinessState.HUMAN_INPUT_REQUIRED
    return DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION


def assess_eligibility_decision_readiness(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
) -> EligibilityDecisionReadinessResult:
    """Assess whether one accepted E.2 proposal may enter independent verification.

    F.1 is deterministic and read-only. It never calls a model, mutates eligibility
    state, or authorizes the R3 action. READY means only that the proposal may be
    handed to a genuinely independent verifier in V1.3-G.

    LLM confidence is intentionally ignored. Profile completeness/readiness scores
    are also not material decision gates because they measure intake completeness,
    not eligibility-decision authority.
    """

    _attempt_integrity(session, proposal)
    current_context = _fresh_context(session, proposal)
    _, profile, pathway, pathway_version, facts = _current_domain_state(
        session,
        proposal=proposal,
        context=current_context,
    )
    _authority_basis_integrity(proposal, current_context)

    gates = (
        _proposal_state_gate(proposal),
        _authority_complete_gate(current_context),
        _required_case_facts_gate(facts),
        _publication_integrity_gate(
            session,
            pathway=pathway,
            pathway_version=pathway_version,
        ),
        _material_fact_gate(
            pathway=pathway,
            pathway_version=pathway_version,
            facts=facts,
        ),
    )
    state = _state(gates)
    passed = sum(gate.status is DecisionReadinessGateStatus.PASS for gate in gates)
    score = round(passed / len(gates), 4)
    readiness_fingerprint = canonical_fingerprint(
        {
            "schema_version": DECISION_READINESS_SCHEMA_VERSION,
            "intent_fingerprint": proposal.intent_fingerprint,
            "context_hash": current_context.context_hash,
            "profile_id": str(profile.id),
            "profile_version": profile.profile_version,
            "pathway_version_id": str(pathway_version.id),
            "gates": gates,
            "state": state,
            "readiness_score": score,
            "independent_verification_required": True,
            "authorization_effect": False,
            "canonical_commit_allowed": False,
        }
    )

    return EligibilityDecisionReadinessResult(
        schema_version=DECISION_READINESS_SCHEMA_VERSION,
        state=state,
        readiness_score=score,
        gates=gates,
        intent_fingerprint=proposal.intent_fingerprint,
        context_hash=current_context.context_hash,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        pathway_version_id=pathway_version.id,
        readiness_fingerprint=readiness_fingerprint,
        assessed_at=now_utc(),
        ready_for_independent_verification=(
            state is DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION
        ),
        independent_verification_required=True,
        authorization_effect=False,
        canonical_commit_allowed=False,
    )

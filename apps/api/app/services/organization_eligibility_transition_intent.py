from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any
from uuid import UUID

from sqlmodel import Session

from app.core.organization_constitution import (
    AutonomyLevel,
    ConsequenceClass,
    MaterialActionType,
    OrganizationActivityClass as ConstitutionalActivityClass,
    RiskTier,
)
from app.models.domain import (
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
    OrganizationActivity,
    Profile,
)
from app.services.llm_client import LLMProvider, LLMProviderError, LLMResponse
from app.services.mobility_domain import mobility_intent_domain
from app.services.mobility_profiles import case_facts, current_mobility_profile
from app.services.organization_activity import stage_activity
from app.services.organization_agent_runtime import (
    AgentRuntimeProfile,
    EmployeeRuntimeBinding,
    RuntimeClass,
    bind_employee_runtime,
)
from app.services.organization_command import (
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_json,
    system_bound_agent_command_context,
)
from app.services.organization_context_broker import (
    ContextBundle,
    ContextPurpose,
    ContextReference,
    build_work_item_context_bundle,
)
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayEvaluation,
    GatewayOutcome,
    GatewayReason,
    MaterialAction,
    PolicyDisposition,
    evaluate_material_action,
    organization_activity_projection,
)


ELIGIBILITY_INTENT_SCHEMA_VERSION = "eligibility-transition-intent.v1"
GOVERNED_ELIGIBILITY_CAPABILITY = "mobility.eligibility"


class EligibilityIntentError(RuntimeError):
    """Base error for the governed E.2 eligibility-intent vertical."""


class EligibilityIntentIntegrityError(EligibilityIntentError):
    """Canonical case/context state is incomplete, stale or internally inconsistent."""


class EligibilityIntentRuntimeError(EligibilityIntentError):
    """The selected technical runtime cannot execute the E.2 pilot safely."""


class EligibilityIntentOutputError(EligibilityIntentError):
    """The runtime returned an eligibility intent outside the typed contract."""


class EligibilityProposedState(str, Enum):
    POTENTIALLY_ELIGIBLE = "potentially_eligible"
    POTENTIALLY_INELIGIBLE = "potentially_ineligible"
    NEEDS_DOCUMENTS = "needs_documents"
    INSUFFICIENT_INFORMATION = "insufficient_information"


@dataclass(frozen=True)
class EligibilityTransitionIntent:
    work_item_id: UUID
    lead_id: UUID
    profile_id: UUID
    profile_version: int
    pathway_version_id: UUID
    proposed_state: EligibilityProposedState
    evidence_basis: tuple[str, ...]
    rule_basis: tuple[str, ...]
    rationale: str
    confidence: float


@dataclass(frozen=True)
class GovernedEligibilityTransitionIntentResult:
    schema_version: str
    context: ContextBundle
    runtime_binding: EmployeeRuntimeBinding
    intent: EligibilityTransitionIntent
    intent_fingerprint: str
    evaluation: GatewayEvaluation
    attempt_activity: OrganizationActivity
    provider: str
    model: str
    mutated: bool = False


def _single_reference(context: ContextBundle, kind: str) -> ContextReference:
    matches = [ref for ref in context.canonical_references if ref.kind == kind]
    if len(matches) != 1:
        raise EligibilityIntentIntegrityError(f"ContextBundle must contain exactly one {kind} reference")
    return matches[0]


def _fingerprinted_record(
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
        raise EligibilityIntentIntegrityError(f"{kind} reference is not a UUID") from exc
    record = session.get(model, record_id)
    if record is None:
        raise EligibilityIntentIntegrityError(f"{kind} reference could not be dereferenced")

    expected_fingerprint = canonical_fingerprint(record)
    if kind == "mobility_pathway_version":
        pathway = session.get(MobilityPathway, record.pathway_id)
        if pathway is None:
            raise EligibilityIntentIntegrityError("mobility pathway parent was not found")
        # D.3 intentionally versions the source reference over both the pathway and
        # its published version. E.2 consumes that exact contract rather than
        # redefining pathway-version identity locally.
        expected_fingerprint = canonical_fingerprint(
            {"pathway": pathway, "pathway_version": record}
        )
    if reference.version != expected_fingerprint:
        raise EligibilityIntentIntegrityError(f"{kind} changed after ContextBundle resolution")
    return record


def _required_case_facts(facts: dict[str, Any]) -> dict[str, Any]:
    target_country = str(facts.get("target_country") or "").strip()
    goal = str(facts.get("goal") or "").strip()
    if not target_country or not goal:
        raise EligibilityIntentIntegrityError(
            "case/profile facts are insufficient for a material eligibility proposal"
        )
    # Deliberately exclude direct identifiers/contact data. E.2 passes only the
    # minimum professional/mobility facts needed for this bounded pilot.
    return {
        "nationality": facts.get("nationality"),
        "current_country": facts.get("current_country"),
        "target_country": target_country,
        "goal": goal,
        "occupation_title": facts.get("occupation_title"),
        "years_experience": facts.get("years_experience"),
        "job_offer_status": facts.get("job_offer_status"),
        "has_job_offer": facts.get("has_job_offer"),
        "qualification_recognition": facts.get("qualification_recognition"),
        "german_level": facts.get("german_level"),
        "employment_province": facts.get("employment_province"),
        "highest_qualification": facts.get("highest_qualification"),
        "field_of_study": facts.get("field_of_study"),
        "desired_role": facts.get("desired_role"),
        "readiness_stage": facts.get("readiness_stage"),
        "completeness_score": facts.get("completeness_score"),
    }


def _case_and_pathway_payload(
    session: Session,
    *,
    context: ContextBundle,
) -> tuple[dict[str, Any], Lead, Profile, MobilityPathway, MobilityPathwayVersion, set[str], set[str]]:
    if context.unknowns:
        raise EligibilityIntentIntegrityError(
            "material eligibility intent requires complete governed Evidence/policy context"
        )
    if context.contradictions:
        raise EligibilityIntentIntegrityError(
            "material eligibility intent is blocked by unresolved ContextBundle contradictions"
        )
    if not context.evidence_refs or not context.verified_rule_refs:
        raise EligibilityIntentIntegrityError(
            "material eligibility intent requires governed Evidence and VerifiedRules"
        )
    if context.work_item.source_object_type != "mobility_pathway_version":
        raise EligibilityIntentIntegrityError(
            "eligibility intent requires a mobility_pathway_version WorkItem"
        )

    lead = _fingerprinted_record(session, context=context, kind="lead", model=Lead)
    profile = _fingerprinted_record(session, context=context, kind="profile", model=Profile)
    pathway_version = _fingerprinted_record(
        session,
        context=context,
        kind="mobility_pathway_version",
        model=MobilityPathwayVersion,
    )
    pathway = session.get(MobilityPathway, pathway_version.pathway_id)
    if pathway is None:
        raise EligibilityIntentIntegrityError("mobility pathway parent was not found")

    if profile.lead_id != lead.id:
        raise EligibilityIntentIntegrityError("profile does not belong to the bound lead")
    current_profile = current_mobility_profile(session, lead.id)
    if current_profile is None or current_profile.id != profile.id:
        raise EligibilityIntentIntegrityError("bound mobility profile is not the current profile version")
    if profile.lifecycle_status != "active":
        raise EligibilityIntentIntegrityError("bound mobility profile is not active")
    if profile.consent_status != "granted":
        raise EligibilityIntentIntegrityError(
            "material automated eligibility processing requires granted profile consent"
        )

    facts = case_facts(session, lead, profile)
    case_payload = _required_case_facts(facts)
    if str(case_payload["target_country"]).casefold() != pathway.country.casefold():
        raise EligibilityIntentIntegrityError("case target country does not match the governed pathway")
    if mobility_intent_domain(lead).casefold() != pathway.domain.casefold():
        raise EligibilityIntentIntegrityError("case intent domain does not match the governed pathway")

    evidence_tokens = {
        f"evidence:{ref.identifier}"
        for ref in context.evidence_refs
        if ref.kind == "mobility_pathway_version_evidence"
    }
    rule_tokens = {
        f"verified_rule:{ref.identifier}"
        for ref in context.verified_rule_refs
        if ref.kind == "verified_rule"
    }
    if len(evidence_tokens) != len(context.evidence_refs) or len(rule_tokens) != len(context.verified_rule_refs):
        raise EligibilityIntentIntegrityError("ContextBundle contains unexpected eligibility authority reference kinds")

    payload = {
        "schema_version": ELIGIBILITY_INTENT_SCHEMA_VERSION,
        "purpose": "propose_internal_eligibility_transition",
        "employee": {
            "position_key": context.position.position_key,
            "title": context.position.title,
            "department": context.position.department,
        },
        "work_item": {
            "id": str(context.work_item.work_item_id),
            "title": context.work_item.title,
            "objective": context.work_item.objective,
        },
        "case": {
            "lead_id": str(lead.id),
            "profile_id": str(profile.id),
            "profile_version": profile.profile_version,
            "facts": case_payload,
        },
        "pathway": {
            "pathway_id": str(pathway.id),
            "pathway_version_id": str(pathway_version.id),
            "pathway_version": pathway_version.version_number,
            "name": pathway.name,
            "country": pathway.country,
            "domain": pathway.domain,
        },
        "authority": {
            "context_hash": context.context_hash,
            "evidence_basis": sorted(evidence_tokens),
            "rule_basis": sorted(rule_tokens),
            "policy_version": context.policy_version,
        },
    }
    return payload, lead, profile, pathway, pathway_version, evidence_tokens, rule_tokens


_SYSTEM_PROMPT = """You are an internal AI employee inside Global Mobility AIOS.
Using ONLY the governed case/pathway authority payload supplied, propose one bounded eligibility-transition intent.
Do not invent facts, rules, Evidence, legal conclusions, or external authority.
This output is a proposal only; it cannot authorize or mutate eligibility state.
Return one JSON object with exactly these keys:
proposed_state, evidence_basis, rule_basis, rationale, confidence.
proposed_state must be one of: potentially_eligible, potentially_ineligible, needs_documents, insufficient_information.
evidence_basis and rule_basis must contain only tokens supplied in the governed payload.
confidence is informational only and must be a number from 0 to 1; it is never an authorization gate.
"""


def _string_tuple(value: Any, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise EligibilityIntentOutputError(f"{label} must be an array")
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise EligibilityIntentOutputError(f"{label} entries must be non-empty strings")
        values.append(item.strip())
    if len(values) != len(set(values)):
        raise EligibilityIntentOutputError(f"{label} contains duplicate references")
    return tuple(values)


def _validated_intent(
    content: str,
    *,
    work_item_id: UUID,
    lead: Lead,
    profile: Profile,
    pathway_version: MobilityPathwayVersion,
    allowed_evidence: set[str],
    allowed_rules: set[str],
) -> EligibilityTransitionIntent:
    try:
        raw = json.loads(content)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise EligibilityIntentOutputError("runtime eligibility intent is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise EligibilityIntentOutputError("runtime eligibility intent must be a JSON object")

    expected_keys = {"proposed_state", "evidence_basis", "rule_basis", "rationale", "confidence"}
    if set(raw) != expected_keys:
        raise EligibilityIntentOutputError("runtime eligibility intent does not match the typed schema")

    try:
        proposed_state = EligibilityProposedState(raw["proposed_state"])
    except (ValueError, TypeError) as exc:
        raise EligibilityIntentOutputError("runtime proposed an unsupported eligibility state") from exc

    evidence_basis = _string_tuple(raw["evidence_basis"], label="evidence_basis")
    rule_basis = _string_tuple(raw["rule_basis"], label="rule_basis")
    if not evidence_basis or not rule_basis:
        raise EligibilityIntentOutputError("eligibility intent must cite governed Evidence and VerifiedRules")
    if any(item not in allowed_evidence for item in evidence_basis):
        raise EligibilityIntentOutputError("eligibility intent cites Evidence outside the ContextBundle")
    if any(item not in allowed_rules for item in rule_basis):
        raise EligibilityIntentOutputError("eligibility intent cites a VerifiedRule outside the ContextBundle")

    rationale = raw["rationale"]
    if not isinstance(rationale, str) or not rationale.strip():
        raise EligibilityIntentOutputError("eligibility intent rationale is required")
    confidence = raw["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise EligibilityIntentOutputError("eligibility intent confidence must be numeric")
    confidence_value = float(confidence)
    if not 0.0 <= confidence_value <= 1.0:
        raise EligibilityIntentOutputError("eligibility intent confidence must be between 0 and 1")

    return EligibilityTransitionIntent(
        work_item_id=work_item_id,
        lead_id=lead.id,
        profile_id=profile.id,
        profile_version=profile.profile_version,
        pathway_version_id=pathway_version.id,
        proposed_state=proposed_state,
        evidence_basis=evidence_basis,
        rule_basis=rule_basis,
        rationale=rationale.strip(),
        confidence=confidence_value,
    )


def _persist_attempt(
    session: Session,
    *,
    command_context: OrganizationCommandContext,
    work_item_id: UUID,
    action: MaterialAction,
    evaluation: GatewayEvaluation,
    intent: EligibilityTransitionIntent,
    intent_fingerprint: str,
    context_hash: str,
    runtime_binding_hash: str,
) -> OrganizationActivity:
    if evaluation.outcome not in {GatewayOutcome.BLOCK, GatewayOutcome.REVIEW_REQUIRED}:
        raise EligibilityIntentIntegrityError("E.2 may persist only non-executing gateway outcomes")

    projection = organization_activity_projection(command_context, action, evaluation)
    projection = replace(
        projection,
        activity_key=f"governance:attempt:{evaluation.trace_id}",
        payload={
            **dict(projection.payload),
            "governance_record_kind": "eligibility_intent_attempt",
            "intent_schema_version": ELIGIBILITY_INTENT_SCHEMA_VERSION,
            "intent_fingerprint": intent_fingerprint,
            "context_hash": context_hash,
            "runtime_binding_hash": runtime_binding_hash,
            "lead_id": str(intent.lead_id),
            "profile_id": str(intent.profile_id),
            "profile_version": intent.profile_version,
            "pathway_version_id": str(intent.pathway_version_id),
            "proposed_state": intent.proposed_state.value,
            "confidence": intent.confidence,
            "evidence_basis": list(intent.evidence_basis),
            "rule_basis": list(intent.rule_basis),
            "r3_verification_floor": "independent_verification_not_yet_satisfied",
        },
    )
    trace_context = replace(command_context, correlation_key=str(evaluation.trace_id))
    activity = stage_activity(
        session,
        trace_context,
        activity_key=projection.activity_key,
        stream_key=projection.stream_key,
        activity_class=projection.activity_class,
        activity_type=projection.activity_type,
        title=projection.title,
        summary=projection.summary,
        source_object_type=projection.source_object_type,
        source_object_id=projection.source_object_id,
        source_object_version=projection.source_object_version,
        work_item_id=work_item_id,
        occurred_at=action.requested_at,
        payload=projection.payload,
        correlation_key=projection.correlation_key,
    )
    session.commit()
    session.refresh(activity)
    return activity


def governed_eligibility_transition_intent(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    work_item_id: UUID,
    runtime_profile: AgentRuntimeProfile,
    authority: CapabilityAuthority,
    provider: LLMProvider,
    idempotency_key: str,
) -> GovernedEligibilityTransitionIntentResult:
    """Run E.2: case-scoped runtime proposal → typed intent → R3 Command Gateway.

    E.2 is intentionally non-mutating. It proves that a bound AI employee can propose
    a material eligibility transition while AIOS independently validates the proposal,
    constructs the MaterialAction, and forces the R3 action to REVIEW_REQUIRED until
    independent verification exists. The durable governance attempt is Board-inspectable.

    The provider must be supplied explicitly. E.2 does not automatically resolve an
    external hosted provider because case-scoped provider-egress/sensitivity policy is
    not yet a sealed contract.
    """

    if runtime_profile.runtime_class is not RuntimeClass.HOSTED_API:
        raise EligibilityIntentRuntimeError("E.2 currently supports only hosted_api runtime bindings")

    context = build_work_item_context_bundle(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        work_item_id=work_item_id,
        purpose=ContextPurpose.REVIEW,
    )
    binding = bind_employee_runtime(
        session,
        context=context,
        profile=runtime_profile,
        required_capability="structured_output",
    )
    payload, lead, profile, pathway, pathway_version, evidence_tokens, rule_tokens = (
        _case_and_pathway_payload(session, context=context)
    )
    prompt_payload = canonical_json(payload)

    try:
        response: LLMResponse = provider.complete(
            system_prompt=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_payload}],
            response_format={"type": "json_object"},
        )
    except LLMProviderError as exc:
        raise EligibilityIntentRuntimeError("E.2 runtime execution failed") from exc

    if response.provider != binding.provider_key:
        raise EligibilityIntentRuntimeError("runtime response provider does not match the bound profile")
    if binding.model_key is not None and response.model != binding.model_key:
        raise EligibilityIntentRuntimeError("runtime response model does not match the bound profile")

    intent = _validated_intent(
        response.content,
        work_item_id=work_item_id,
        lead=lead,
        profile=profile,
        pathway_version=pathway_version,
        allowed_evidence=evidence_tokens,
        allowed_rules=rule_tokens,
    )

    # Re-read canonical state after runtime latency. The model never gets to carry a
    # stale case/context proposal across this boundary.
    session.expire_all()
    current_context = build_work_item_context_bundle(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        work_item_id=work_item_id,
        purpose=ContextPurpose.REVIEW,
    )
    if current_context.context_hash != context.context_hash:
        raise EligibilityIntentIntegrityError("case/context changed during runtime execution")
    current_profile = _fingerprinted_record(
        session,
        context=current_context,
        kind="profile",
        model=Profile,
    )
    if current_profile.id != intent.profile_id or current_profile.profile_version != intent.profile_version:
        raise EligibilityIntentIntegrityError("eligibility intent profile precondition is stale")

    intent_fingerprint = canonical_fingerprint(intent)
    command_context = system_bound_agent_command_context(
        tenant_key=current_context.tenant_key,
        position_key=current_context.position.position_key,
        department=current_context.position.department,
        authority_level=current_context.position.authority_level,
    )
    scope_key = f"{pathway.country.casefold()}:{pathway.domain.casefold()}"
    action = MaterialAction(
        action_type=MaterialActionType.ELIGIBILITY_TRANSITION,
        capability=GOVERNED_ELIGIBILITY_CAPABILITY,
        subject_type="lead_eligibility",
        subject_id=str(intent.lead_id),
        idempotency_key=idempotency_key,
        expected_version=current_profile.profile_version,
        proposed_change={
            "proposed_state": intent.proposed_state.value,
            "profile_id": str(intent.profile_id),
            "profile_version": intent.profile_version,
            "pathway_version_id": str(intent.pathway_version_id),
            "context_hash": current_context.context_hash,
            "runtime_binding_hash": binding.binding_hash,
            "intent_fingerprint": intent_fingerprint,
        },
        scope_key=scope_key,
        evidence_refs=tuple(sorted((*intent.evidence_basis, *intent.rule_basis))),
        rationale=intent.rationale,
        consequence_class=ConsequenceClass.APPEND_ONLY_CORRECTION,
    )

    # Preserve A0 as an unconditional prohibition. For A1-A5, the explicit E.2
    # verification floor is stricter than nominal autonomy and forces human review
    # until independent verification exists.
    policy_disposition = (
        PolicyDisposition.ALLOW
        if authority.autonomy_level is AutonomyLevel.A0
        else PolicyDisposition.HUMAN_REQUIRED
    )
    evaluation = evaluate_material_action(
        command_context,
        authority,
        action,
        current_version=current_profile.profile_version,
        policy_disposition=policy_disposition,
    )
    if evaluation.effective_risk_tier is not RiskTier.R3:
        raise EligibilityIntentIntegrityError("eligibility transition lost its constitutional R3 floor")
    if evaluation.constitutional_activity_class is not ConstitutionalActivityClass.MATERIAL:
        raise EligibilityIntentIntegrityError("eligibility transition must remain material activity")
    if evaluation.outcome not in {GatewayOutcome.BLOCK, GatewayOutcome.REVIEW_REQUIRED}:
        raise EligibilityIntentIntegrityError("E.2 is not authorized to execute an eligibility transition")
    if evaluation.outcome is GatewayOutcome.REVIEW_REQUIRED and evaluation.reason is not GatewayReason.POLICY_REVIEW_REQUIRED:
        raise EligibilityIntentIntegrityError("E.2 review route must preserve the explicit verification policy floor")

    attempt_activity = _persist_attempt(
        session,
        command_context=command_context,
        work_item_id=work_item_id,
        action=action,
        evaluation=evaluation,
        intent=intent,
        intent_fingerprint=intent_fingerprint,
        context_hash=current_context.context_hash,
        runtime_binding_hash=binding.binding_hash,
    )
    return GovernedEligibilityTransitionIntentResult(
        schema_version=ELIGIBILITY_INTENT_SCHEMA_VERSION,
        context=current_context,
        runtime_binding=binding,
        intent=intent,
        intent_fingerprint=intent_fingerprint,
        evaluation=evaluation,
        attempt_activity=attempt_activity,
        provider=response.provider,
        model=response.model,
        mutated=False,
    )

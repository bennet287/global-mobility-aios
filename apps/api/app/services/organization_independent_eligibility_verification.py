from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from sqlmodel import Session

from app.models.domain import (
    Lead,
    OrganizationActivity,
    OrganizationalWorkItem,
    Profile,
    now_utc,
)
from app.services.llm_client import (
    LLMProvider,
    LLMProviderConfigurationError,
    LLMProviderError,
    LLMProviderResponseContractError,
    LLMProviderTransportError,
    LLMResponse,
)
from app.services.mobility_profiles import case_facts, current_mobility_profile
from app.services.organization_activity import stage_activity
from app.services.organization_agent_runtime import (
    AgentRuntimeError,
    AgentRuntimeProfile,
    EmployeeRuntimeBinding,
    RuntimeClass,
    bind_employee_runtime,
)
from app.services.organization_command import (
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
from app.services.organization_decision_readiness import (
    DECISION_READINESS_SCHEMA_VERSION,
    DecisionReadinessError,
    DecisionReadinessState,
    EligibilityDecisionReadinessResult,
    assess_eligibility_decision_readiness,
)
from app.services.organization_eligibility_transition_intent import (
    EligibilityProposedState,
    GovernedEligibilityTransitionIntentResult,
)
from app.services.organization_eligibility_runtime_failure import (
    EligibilityRuntimeFailureProvenance,
)
from app.services.organization_mobility_pathway_brief import (
    MobilityPathwayBriefError,
    _governed_payload,
)
from app.services.organization_transparency import activities_for_work_item


INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION = "independent-eligibility-verification.v1"


class IndependentEligibilityVerificationError(RuntimeError):
    """Base error for the bounded G.1 independent-verification vertical."""


class IndependentEligibilityVerificationIntegrityError(IndependentEligibilityVerificationError):
    """The verifier, readiness result, or governed context is stale or not independent."""


class IndependentEligibilityVerificationRuntimeError(IndependentEligibilityVerificationError):
    """The verifier runtime cannot safely execute the G.1 contract."""

    def __init__(
        self,
        message: str,
        *,
        failure_provenance: EligibilityRuntimeFailureProvenance | None = None,
    ) -> None:
        super().__init__(message)
        self.failure_provenance = (
            failure_provenance
            or EligibilityRuntimeFailureProvenance.configuration_or_binding()
        )


class IndependentEligibilityVerificationOutputError(IndependentEligibilityVerificationError):
    """The verifier runtime returned output outside the typed G.1 contract."""


class IndependentEligibilityConclusion(str, Enum):
    SUPPORTS_POTENTIAL_ELIGIBILITY = "supports_potential_eligibility"
    SUPPORTS_POTENTIAL_INELIGIBILITY = "supports_potential_ineligibility"
    INSUFFICIENT_BASIS = "insufficient_basis"
    CONTRADICTION_FOUND = "contradiction_found"


class IndependentVerificationDisposition(str, Enum):
    AGREES = "agrees"
    DISAGREES = "disagrees"
    INSUFFICIENT_BASIS = "insufficient_basis"


@dataclass(frozen=True)
class IndependentEligibilityVerificationDraft:
    conclusion: IndependentEligibilityConclusion
    evidence_basis: tuple[str, ...]
    rule_basis: tuple[str, ...]
    findings: tuple[str, ...]
    unresolved_questions: tuple[str, ...]


@dataclass(frozen=True)
class GovernedIndependentEligibilityVerificationResult:
    schema_version: str
    proposer_trace_id: UUID
    proposer_activity_id: UUID
    proposer_position_key: str
    proposer_runtime_binding_hash: str
    readiness_fingerprint: str
    verifier_context: ContextBundle
    verifier_runtime_binding: EmployeeRuntimeBinding
    verification_work_item_id: UUID
    draft: IndependentEligibilityVerificationDraft
    disposition: IndependentVerificationDisposition
    verification_fingerprint: str
    verification_activity: OrganizationActivity
    provider: str
    model: str
    blind_review: bool = True
    proposer_conclusion_exposed: bool = False
    independent_verification_completed: bool = True
    eligible_for_verification_floor_integration: bool = False
    command_gateway_floor_satisfied: bool = False
    authorization_effect: bool = False
    canonical_commit_allowed: bool = False


def _single_reference(context: ContextBundle, kind: str) -> ContextReference:
    matches = [ref for ref in context.canonical_references if ref.kind == kind]
    if len(matches) != 1:
        raise IndependentEligibilityVerificationIntegrityError(
            f"verifier ContextBundle must contain exactly one {kind} reference"
        )
    return matches[0]


def _authority_projection(context: ContextBundle) -> dict[str, Any]:
    """Project only canonical subject/authority identity, excluding employee/WorkItem identity."""

    canonical = tuple(
        sorted(
            (
                ref.kind,
                ref.identifier,
                ref.version,
            )
            for ref in context.canonical_references
            if ref.kind in {"lead", "profile", "mobility_pathway_version", "country_policy"}
        )
    )
    evidence = tuple(sorted((ref.kind, ref.identifier, ref.version) for ref in context.evidence_refs))
    rules = tuple(sorted((ref.kind, ref.identifier, ref.version) for ref in context.verified_rule_refs))
    snapshots = tuple(sorted((ref.kind, ref.identifier, ref.version) for ref in context.source_snapshot_refs))
    return {
        "tenant_key": context.tenant_key,
        "canonical_references": canonical,
        "evidence_refs": evidence,
        "verified_rule_refs": rules,
        "source_snapshot_refs": snapshots,
        "unknowns": context.unknowns,
        "contradictions": context.contradictions,
        "policy_version": context.policy_version,
    }


def _authority_fingerprint(context: ContextBundle) -> str:
    return canonical_fingerprint(_authority_projection(context))


def _verification_work_item(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    verification_work_item_id: UUID,
    verifier_position_key: str,
) -> OrganizationalWorkItem:
    work = session.get(OrganizationalWorkItem, verification_work_item_id)
    if work is None or work.tenant_key != proposal.context.tenant_key:
        raise IndependentEligibilityVerificationIntegrityError("verification WorkItem is unavailable")
    if work.id == proposal.intent.work_item_id:
        raise IndependentEligibilityVerificationIntegrityError(
            "independent verification requires a separate verification WorkItem"
        )
    if work.assigned_position_key != verifier_position_key:
        raise IndependentEligibilityVerificationIntegrityError(
            "verification WorkItem is not assigned to the verifier position"
        )
    if work.lead_id != proposal.intent.lead_id or work.profile_id != proposal.intent.profile_id:
        raise IndependentEligibilityVerificationIntegrityError(
            "verification WorkItem is not bound to the same Lead/Profile"
        )
    if (
        work.source_object_type != "mobility_pathway_version"
        or work.source_object_id != str(proposal.intent.pathway_version_id)
    ):
        raise IndependentEligibilityVerificationIntegrityError(
            "verification WorkItem is not bound to the same governed pathway version"
        )
    return work


def _fresh_readiness(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
) -> EligibilityDecisionReadinessResult:
    if readiness.schema_version != DECISION_READINESS_SCHEMA_VERSION:
        raise IndependentEligibilityVerificationIntegrityError("unsupported Decision Readiness schema")
    if readiness.state is not DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION:
        raise IndependentEligibilityVerificationIntegrityError(
            "G.1 accepts only READY_FOR_INDEPENDENT_VERIFICATION proposals"
        )
    try:
        current = assess_eligibility_decision_readiness(session, proposal=proposal)
    except DecisionReadinessError as exc:
        raise IndependentEligibilityVerificationIntegrityError(
            "Decision Readiness is no longer valid for independent verification"
        ) from exc
    if current.readiness_fingerprint != readiness.readiness_fingerprint:
        raise IndependentEligibilityVerificationIntegrityError(
            "Decision Readiness changed before independent verification"
        )
    if not current.ready_for_independent_verification:
        raise IndependentEligibilityVerificationIntegrityError(
            "proposal is no longer ready for independent verification"
        )
    return current


def _verifier_context(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    verification_work_item_id: UUID,
    verifier_position_key: str,
) -> ContextBundle:
    if verifier_position_key == proposal.context.position.position_key:
        raise IndependentEligibilityVerificationIntegrityError(
            "proposer and verifier OrganizationPosition must be different"
        )
    _verification_work_item(
        session,
        proposal=proposal,
        verification_work_item_id=verification_work_item_id,
        verifier_position_key=verifier_position_key,
    )
    context = build_work_item_context_bundle(
        session,
        tenant_key=proposal.context.tenant_key,
        position_key=verifier_position_key,
        work_item_id=verification_work_item_id,
        purpose=ContextPurpose.REVIEW,
    )
    if context.unknowns or context.contradictions:
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier ContextBundle has unresolved governed authority gaps"
        )
    if _authority_fingerprint(context) != _authority_fingerprint(proposal.context):
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier and proposer are not bound to the same canonical case/pathway authority"
        )
    return context


def _verifier_binding(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    context: ContextBundle,
    runtime_profile: AgentRuntimeProfile,
) -> EmployeeRuntimeBinding:
    if runtime_profile.runtime_class is not RuntimeClass.HOSTED_API:
        raise IndependentEligibilityVerificationRuntimeError(
            "G.1 currently supports only hosted_api verifier runtimes",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.configuration_or_binding()
            ),
        )
    try:
        binding = bind_employee_runtime(
            session,
            context=context,
            profile=runtime_profile,
            required_capability="structured_output",
        )
    except AgentRuntimeError as exc:
        raise IndependentEligibilityVerificationRuntimeError(
            "G.1 verifier runtime binding failed",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.configuration_or_binding()
            ),
        ) from exc
    proposer_binding = proposal.runtime_binding
    if binding.position_key == proposer_binding.position_key:
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier runtime is bound to the proposing employee"
        )
    if binding.independence_group == proposer_binding.independence_group:
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier runtime must use a different independence group"
        )
    if proposer_binding.model_key is None or binding.model_key is None:
        raise IndependentEligibilityVerificationIntegrityError(
            "G.1 requires pinned proposer and verifier model identities"
        )
    if binding.provider_key == proposer_binding.provider_key:
        raise IndependentEligibilityVerificationIntegrityError(
            "G.1 verifier must use a different provider from the proposer"
        )
    if binding.model_key == proposer_binding.model_key:
        raise IndependentEligibilityVerificationIntegrityError(
            "G.1 verifier must use a different model identity from the proposer"
        )
    return binding


def resolve_independent_eligibility_verifier_execution(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification_work_item_id: UUID,
    verifier_position_key: str,
    verifier_runtime_profile: AgentRuntimeProfile,
) -> tuple[
    EligibilityDecisionReadinessResult,
    ContextBundle,
    EmployeeRuntimeBinding,
]:
    """Resolve the exact governed G.1 readiness/context/runtime execution basis.

    The fenced verifier runtime uses this same resolver before and after the
    verification WorkItem enters its running lifecycle. G.1 itself resolves it again
    immediately before provider execution, so the execution token can be bound to the
    exact ContextBundle/runtime binding that the verifier actually consumes.
    """

    fresh_readiness = _fresh_readiness(
        session,
        proposal=proposal,
        readiness=readiness,
    )
    context = _verifier_context(
        session,
        proposal=proposal,
        verification_work_item_id=verification_work_item_id,
        verifier_position_key=verifier_position_key,
    )
    binding = _verifier_binding(
        session,
        proposal=proposal,
        context=context,
        runtime_profile=verifier_runtime_profile,
    )
    return fresh_readiness, context, binding


def _case_payload(
    session: Session,
    *,
    context: ContextBundle,
) -> dict[str, Any]:
    lead_ref = _single_reference(context, "lead")
    profile_ref = _single_reference(context, "profile")
    try:
        lead_id = UUID(lead_ref.identifier)
        profile_id = UUID(profile_ref.identifier)
    except (TypeError, ValueError, AttributeError) as exc:
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier case references are malformed"
        ) from exc
    lead = session.get(Lead, lead_id)
    profile = session.get(Profile, profile_id)
    if lead is None or profile is None or profile.lead_id != lead.id:
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier case references could not be dereferenced"
        )
    if canonical_fingerprint(lead) != lead_ref.version or canonical_fingerprint(profile) != profile_ref.version:
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier case changed after ContextBundle resolution"
        )
    current_profile = current_mobility_profile(session, lead.id)
    if current_profile is None or current_profile.id != profile.id:
        raise IndependentEligibilityVerificationIntegrityError("verifier Profile is no longer current")
    if profile.lifecycle_status != "active" or profile.consent_status != "granted":
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier Profile is not active with granted consent"
        )
    facts = case_facts(session, lead, profile)
    # Deliberately exclude direct contact identity and proposer narrative/conclusion.
    return {
        "lead_id": str(lead.id),
        "profile_id": str(profile.id),
        "profile_version": profile.profile_version,
        "facts": {
            "nationality": facts.get("nationality"),
            "current_country": facts.get("current_country"),
            "target_country": facts.get("target_country"),
            "goal": facts.get("goal"),
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
        },
    }


def _blind_verifier_payload(
    session: Session,
    *,
    context: ContextBundle,
    readiness: EligibilityDecisionReadinessResult,
) -> tuple[dict[str, Any], set[str], set[str]]:
    try:
        pathway_payload, _, _, allowed_citations = _governed_payload(session, context=context)
    except MobilityPathwayBriefError as exc:
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier governed pathway authority could not be dereferenced"
        ) from exc
    evidence_tokens = {
        item["citation"] for item in pathway_payload["evidence"]
    }
    rule_tokens = {
        item["citation"] for item in pathway_payload["verified_rules"]
    }
    payload = {
        "schema_version": INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION,
        "purpose": "blind_precommit_eligibility_verification",
        "verifier": pathway_payload["employee"],
        "verification_work_item": pathway_payload["work_item"],
        "case": _case_payload(session, context=context),
        "pathway": pathway_payload["pathway"],
        "evidence": pathway_payload["evidence"],
        "verified_rules": pathway_payload["verified_rules"],
        "source_snapshots": pathway_payload["source_snapshots"],
        "country_policy": pathway_payload["country_policy"],
        "authority": {
            "verifier_context_hash": context.context_hash,
            "authority_fingerprint": _authority_fingerprint(context),
            "readiness_fingerprint": readiness.readiness_fingerprint,
            "allowed_citations": sorted(allowed_citations),
        },
        "blind_review_contract": {
            "proposer_conclusion_exposed": False,
            "proposer_rationale_exposed": False,
            "proposer_confidence_exposed": False,
            "task": "Independently assess the governed case against the governed pathway Evidence and VerifiedRules.",
        },
    }
    return payload, evidence_tokens, rule_tokens


_SYSTEM_PROMPT = """You are an independent internal verifier inside Global Mobility AIOS.
Perform a blind PRE-COMMIT verification using ONLY the governed case/pathway/Evidence/rule payload supplied.
You are not shown the proposing employee's conclusion, rationale, or confidence. Do not infer or ask for them.
Reach your own bounded conclusion from the governed Evidence and VerifiedRules.
Do not authorize, mutate, publish, submit, or communicate eligibility truth.
Return one JSON object with exactly these keys:
conclusion, evidence_basis, rule_basis, findings, unresolved_questions.
conclusion must be one of: supports_potential_eligibility, supports_potential_ineligibility, insufficient_basis, contradiction_found.
evidence_basis and rule_basis must cite only tokens supplied in the governed payload.
findings and unresolved_questions must be arrays of strings.
"""


def _string_tuple(value: Any, *, label: str, allow_empty: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise IndependentEligibilityVerificationOutputError(f"{label} must be an array")
    values: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise IndependentEligibilityVerificationOutputError(
                f"{label} entries must be non-empty strings"
            )
        values.append(item.strip())
    if not allow_empty and not values:
        raise IndependentEligibilityVerificationOutputError(f"{label} must not be empty")
    if len(values) != len(set(values)):
        raise IndependentEligibilityVerificationOutputError(f"{label} contains duplicate values")
    return tuple(values)


def _validated_draft(
    content: str,
    *,
    allowed_evidence: set[str],
    allowed_rules: set[str],
) -> IndependentEligibilityVerificationDraft:
    try:
        raw = json.loads(content)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise IndependentEligibilityVerificationOutputError(
            "verifier output is not valid JSON"
        ) from exc
    if not isinstance(raw, dict):
        raise IndependentEligibilityVerificationOutputError("verifier output must be a JSON object")
    expected = {"conclusion", "evidence_basis", "rule_basis", "findings", "unresolved_questions"}
    if set(raw) != expected:
        raise IndependentEligibilityVerificationOutputError(
            "verifier output does not match the typed G.1 schema"
        )
    try:
        conclusion = IndependentEligibilityConclusion(raw["conclusion"])
    except (TypeError, ValueError) as exc:
        raise IndependentEligibilityVerificationOutputError(
            "verifier returned an unsupported conclusion"
        ) from exc
    evidence = _string_tuple(raw["evidence_basis"], label="evidence_basis", allow_empty=False)
    rules = _string_tuple(raw["rule_basis"], label="rule_basis", allow_empty=False)
    if any(item not in allowed_evidence for item in evidence):
        raise IndependentEligibilityVerificationOutputError(
            "verifier cited Evidence outside governed authority"
        )
    if any(item not in allowed_rules for item in rules):
        raise IndependentEligibilityVerificationOutputError(
            "verifier cited a VerifiedRule outside governed authority"
        )
    findings = _string_tuple(raw["findings"], label="findings", allow_empty=False)
    unresolved = _string_tuple(raw["unresolved_questions"], label="unresolved_questions")
    return IndependentEligibilityVerificationDraft(
        conclusion=conclusion,
        evidence_basis=evidence,
        rule_basis=rules,
        findings=findings,
        unresolved_questions=unresolved,
    )


def _disposition(
    proposal: GovernedEligibilityTransitionIntentResult,
    draft: IndependentEligibilityVerificationDraft,
) -> IndependentVerificationDisposition:
    if draft.conclusion in {
        IndependentEligibilityConclusion.INSUFFICIENT_BASIS,
        IndependentEligibilityConclusion.CONTRADICTION_FOUND,
    }:
        return IndependentVerificationDisposition.INSUFFICIENT_BASIS
    expected = {
        EligibilityProposedState.POTENTIALLY_ELIGIBLE:
            IndependentEligibilityConclusion.SUPPORTS_POTENTIAL_ELIGIBILITY,
        EligibilityProposedState.POTENTIALLY_INELIGIBLE:
            IndependentEligibilityConclusion.SUPPORTS_POTENTIAL_INELIGIBILITY,
    }.get(proposal.intent.proposed_state)
    if expected is None:
        raise IndependentEligibilityVerificationIntegrityError(
            "G.1 received a non-actionable proposer conclusion"
        )
    return (
        IndependentVerificationDisposition.AGREES
        if draft.conclusion is expected
        else IndependentVerificationDisposition.DISAGREES
    )


def _persist_verification(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verifier_context: ContextBundle,
    verifier_binding: EmployeeRuntimeBinding,
    verification_work_item_id: UUID,
    draft: IndependentEligibilityVerificationDraft,
    disposition: IndependentVerificationDisposition,
    verification_fingerprint: str,
    idempotency_key: str,
    provider: str,
    model: str,
    commit: bool,
) -> OrganizationActivity:
    command_context = system_bound_agent_command_context(
        tenant_key=verifier_context.tenant_key,
        position_key=verifier_context.position.position_key,
        department=verifier_context.position.department,
        authority_level=verifier_context.position.authority_level,
        correlation_key=str(proposal.evaluation.trace_id),
    )
    activity = stage_activity(
        session,
        command_context,
        activity_key=f"verification:eligibility:{idempotency_key}",
        stream_key=f"verification:eligibility:{proposal.intent.lead_id}",
        activity_class="decision",
        activity_type="verification.eligibility.independent.v1",
        title="Independent eligibility verification completed",
        summary=(
            f"Blind verifier disposition={disposition.value}; proposer trace={proposal.evaluation.trace_id}; "
            "no eligibility mutation or authorization effect."
        ),
        source_object_type="lead_eligibility",
        source_object_id=str(proposal.intent.lead_id),
        source_object_version=str(proposal.intent.profile_version),
        work_item_id=verification_work_item_id,
        lead_id=proposal.intent.lead_id,
        profile_id=proposal.intent.profile_id,
        causation_activity_id=proposal.attempt_activity.id,
        occurred_at=now_utc(),
        correlation_key=str(proposal.evaluation.trace_id),
        payload={
            "constitutional_activity_class": "MATERIAL",
            "verification_schema_version": INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION,
            "verification_mode": "PRE_COMMIT",
            "verification_kind": "independent_eligibility_verification",
            "verification_fingerprint": verification_fingerprint,
            "disposition": disposition.value,
            "verifier_conclusion": draft.conclusion.value,
            "evidence_basis": list(draft.evidence_basis),
            "rule_basis": list(draft.rule_basis),
            "findings": list(draft.findings),
            "unresolved_questions": list(draft.unresolved_questions),
            "proposer_trace_id": str(proposal.evaluation.trace_id),
            "proposer_activity_id": str(proposal.attempt_activity.id),
            "proposer_position_key": proposal.context.position.position_key,
            "proposer_runtime_binding_hash": proposal.runtime_binding.binding_hash,
            "proposer_independence_group": proposal.runtime_binding.independence_group,
            "readiness_fingerprint": readiness.readiness_fingerprint,
            "verifier_position_key": verifier_context.position.position_key,
            "verifier_context_hash": verifier_context.context_hash,
            "verifier_authority_fingerprint": _authority_fingerprint(verifier_context),
            "verifier_runtime_binding_hash": verifier_binding.binding_hash,
            "verifier_runtime_profile_key": verifier_binding.runtime_profile_key,
            "verifier_independence_group": verifier_binding.independence_group,
            "provider": provider,
            "model": model,
            "blind_review": True,
            "proposer_conclusion_exposed": False,
            "independent_verification_completed": True,
            "eligible_for_verification_floor_integration": (
                disposition is IndependentVerificationDisposition.AGREES
            ),
            "command_gateway_floor_satisfied": False,
            "authorization_effect": False,
            "canonical_commit_allowed": False,
        },
    )
    if commit:
        session.commit()
        session.refresh(activity)
    else:
        session.flush()
    return activity


def verify_eligibility_proposal_independently(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification_work_item_id: UUID,
    verifier_position_key: str,
    verifier_runtime_profile: AgentRuntimeProfile,
    provider: LLMProvider,
    idempotency_key: str,
    commit_verification: bool = True,
) -> GovernedIndependentEligibilityVerificationResult:
    """Run G.1 blind independent verification without authorizing eligibility mutation.

    The verifier uses a separate WorkItem and OrganizationPosition, a runtime in a
    different independence group, and a different provider/model identity. The
    verifier sees the governed case/pathway Evidence and rules but never receives the
    proposing model's conclusion, rationale, or confidence. AIOS compares conclusions
    only after the verifier responds.

    ``commit_verification=False`` is reserved for the fenced runtime envelope. It stages
    verification lineage so the same transaction can prove the current runtime fence,
    append terminal execution provenance, and complete the WorkItem atomically.
    """

    fresh_readiness, context, binding = resolve_independent_eligibility_verifier_execution(
        session,
        proposal=proposal,
        readiness=readiness,
        verification_work_item_id=verification_work_item_id,
        verifier_position_key=verifier_position_key,
        verifier_runtime_profile=verifier_runtime_profile,
    )
    if provider.name != binding.provider_key:
        raise IndependentEligibilityVerificationRuntimeError(
            "verifier provider adapter does not match the bound runtime",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.configuration_or_binding()
            ),
        )
    payload, evidence_tokens, rule_tokens = _blind_verifier_payload(
        session,
        context=context,
        readiness=fresh_readiness,
    )
    prompt_payload = canonical_json(payload)

    try:
        response: LLMResponse = provider.complete(
            system_prompt=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_payload}],
            response_format={"type": "json_object"},
        )
    except LLMProviderConfigurationError as exc:
        raise IndependentEligibilityVerificationRuntimeError(
            "independent verifier runtime configuration failed",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.configuration_or_binding()
            ),
        ) from exc
    except LLMProviderResponseContractError as exc:
        raise IndependentEligibilityVerificationRuntimeError(
            "independent verifier provider response contract failed",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.provider_response_contract()
            ),
        ) from exc
    except LLMProviderTransportError as exc:
        raise IndependentEligibilityVerificationRuntimeError(
            "independent verifier provider transport failed",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.provider_transport()
            ),
        ) from exc
    except LLMProviderError as exc:
        # Backward-compatible custom-provider fallback after provider invocation.
        raise IndependentEligibilityVerificationRuntimeError(
            "independent verifier runtime execution failed",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.provider_transport()
            ),
        ) from exc

    if response.provider != binding.provider_key:
        raise IndependentEligibilityVerificationRuntimeError(
            "verifier response provider does not match bound runtime",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.provider_response_contract()
            ),
        )
    if response.model != binding.model_key:
        raise IndependentEligibilityVerificationRuntimeError(
            "verifier response model does not match bound runtime",
            failure_provenance=(
                EligibilityRuntimeFailureProvenance.provider_response_contract()
            ),
        )

    draft = _validated_draft(
        response.content,
        allowed_evidence=evidence_tokens,
        allowed_rules=rule_tokens,
    )

    # Recompute readiness and verifier context after runtime latency. The verifier
    # result cannot cross a stale case/Evidence/policy boundary.
    session.expire_all()
    latest_readiness = _fresh_readiness(
        session,
        proposal=proposal,
        readiness=fresh_readiness,
    )
    latest_context = _verifier_context(
        session,
        proposal=proposal,
        verification_work_item_id=verification_work_item_id,
        verifier_position_key=verifier_position_key,
    )
    if latest_context.context_hash != context.context_hash:
        raise IndependentEligibilityVerificationIntegrityError(
            "verifier context changed during independent verification"
        )
    if latest_readiness.readiness_fingerprint != fresh_readiness.readiness_fingerprint:
        raise IndependentEligibilityVerificationIntegrityError(
            "Decision Readiness changed during independent verification"
        )

    disposition = _disposition(proposal, draft)
    verification_payload = {
        "schema_version": INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION,
        "proposer_trace_id": str(proposal.evaluation.trace_id),
        "proposer_activity_id": str(proposal.attempt_activity.id),
        "intent_fingerprint": proposal.intent_fingerprint,
        "readiness_fingerprint": latest_readiness.readiness_fingerprint,
        "verifier_position_key": latest_context.position.position_key,
        "verifier_context_hash": latest_context.context_hash,
        "verifier_authority_fingerprint": _authority_fingerprint(latest_context),
        "verifier_runtime_binding_hash": binding.binding_hash,
        "verifier_independence_group": binding.independence_group,
        "provider": response.provider,
        "model": response.model,
        "draft": draft,
        "disposition": disposition,
        "blind_review": True,
        "proposer_conclusion_exposed": False,
        "command_gateway_floor_satisfied": False,
        "authorization_effect": False,
        "canonical_commit_allowed": False,
    }
    verification_fingerprint = canonical_fingerprint(verification_payload)
    activity = _persist_verification(
        session,
        proposal=proposal,
        readiness=latest_readiness,
        verifier_context=latest_context,
        verifier_binding=binding,
        verification_work_item_id=verification_work_item_id,
        draft=draft,
        disposition=disposition,
        verification_fingerprint=verification_fingerprint,
        idempotency_key=idempotency_key,
        provider=response.provider,
        model=response.model,
        commit=commit_verification,
    )

    # Existing transparency read should immediately expose the durable verifier event.
    if not any(
        row.activity_id == activity.id
        for row in activities_for_work_item(
            session,
            tenant_key=latest_context.tenant_key,
            work_item_id=verification_work_item_id,
        )
    ):
        raise IndependentEligibilityVerificationIntegrityError(
            "durable independent verification is not visible through WorkItem transparency"
        )

    return GovernedIndependentEligibilityVerificationResult(
        schema_version=INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION,
        proposer_trace_id=proposal.evaluation.trace_id,
        proposer_activity_id=proposal.attempt_activity.id,
        proposer_position_key=proposal.context.position.position_key,
        proposer_runtime_binding_hash=proposal.runtime_binding.binding_hash,
        readiness_fingerprint=latest_readiness.readiness_fingerprint,
        verifier_context=latest_context,
        verifier_runtime_binding=binding,
        verification_work_item_id=verification_work_item_id,
        draft=draft,
        disposition=disposition,
        verification_fingerprint=verification_fingerprint,
        verification_activity=activity,
        provider=response.provider,
        model=response.model,
        blind_review=True,
        proposer_conclusion_exposed=False,
        independent_verification_completed=True,
        eligible_for_verification_floor_integration=(
            disposition is IndependentVerificationDisposition.AGREES
        ),
        command_gateway_floor_satisfied=False,
        authorization_effect=False,
        canonical_commit_allowed=False,
    )

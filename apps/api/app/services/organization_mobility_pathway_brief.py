from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlmodel import Session

from app.models.domain import (
    CountryPolicy,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    SourceSnapshot,
    VerifiedRule,
)
from app.services.llm_client import LLMProvider, LLMProviderError, LLMProviderFactory, LLMResponse
from app.services.organization_agent_runtime import (
    AgentRuntimeProfile,
    EmployeeRuntimeBinding,
    RuntimeClass,
    bind_employee_runtime,
)
from app.services.organization_command import canonical_fingerprint, canonical_json
from app.services.organization_context_broker import (
    ContextBundle,
    ContextPurpose,
    ContextReference,
    build_work_item_context_bundle,
)


PATHWAY_BRIEF_SCHEMA_VERSION = "governed-mobility-pathway-brief.v1"
MAX_SOURCE_EXCERPT_CHARS = 6000


class MobilityPathwayBriefError(RuntimeError):
    """Base error for the first governed mobility vertical."""


class MobilityPathwayBriefRuntimeError(MobilityPathwayBriefError):
    """The selected runtime cannot execute this bounded vertical."""


class MobilityPathwayBriefOutputError(MobilityPathwayBriefError):
    """The runtime returned output that violates the vertical contract."""


@dataclass(frozen=True)
class MobilityPathwayBriefDraft:
    summary: str
    key_requirements: tuple[str, ...]
    material_risks: tuple[str, ...]
    evidence_gaps: tuple[str, ...]
    operator_questions: tuple[str, ...]
    evidence_basis: tuple[str, ...]
    human_review_required: bool
    client_facing: bool
    canonical_commit_allowed: bool
    external_action_authorized: bool


@dataclass(frozen=True)
class GovernedMobilityPathwayBriefResult:
    schema_version: str
    context: ContextBundle
    runtime_binding: EmployeeRuntimeBinding
    pathway_id: UUID
    pathway_version_id: UUID
    pathway_name: str
    vertical_status: str
    prompt_fingerprint: str
    provider: str
    model: str
    draft: MobilityPathwayBriefDraft


def _json_value(raw: str | None, *, label: str, expected_type: type, default: Any) -> Any:
    candidate = raw if raw not in (None, "") else json.dumps(default)
    try:
        value = json.loads(candidate)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MobilityPathwayBriefError(f"{label} is not valid JSON") from exc
    if not isinstance(value, expected_type):
        raise MobilityPathwayBriefError(f"{label} has the wrong JSON shape")
    return value


def _uuid(value: str, *, label: str) -> UUID:
    try:
        return UUID(value)
    except (TypeError, ValueError, AttributeError) as exc:
        raise MobilityPathwayBriefError(f"{label} must be a UUID") from exc


def _reference_map(refs: tuple[ContextReference, ...], *, kind: str) -> dict[UUID, ContextReference]:
    result: dict[UUID, ContextReference] = {}
    for ref in refs:
        if ref.kind != kind:
            raise MobilityPathwayBriefError(f"unexpected {kind} reference kind")
        identifier = _uuid(ref.identifier, label=f"{kind} reference")
        if identifier in result:
            raise MobilityPathwayBriefError(f"duplicate {kind} reference")
        result[identifier] = ref
    return result


def _source_excerpt(snapshot: SourceSnapshot) -> dict[str, Any]:
    text = snapshot.content_text or ""
    excerpt = text[:MAX_SOURCE_EXCERPT_CHARS]
    return {
        "snapshot_id": str(snapshot.id),
        "snapshot_fingerprint": canonical_fingerprint(snapshot),
        "content_hash": snapshot.content_hash,
        "status": snapshot.status,
        "captured_at": snapshot.captured_at,
        "excerpt": excerpt,
        "excerpt_truncated": len(text) > MAX_SOURCE_EXCERPT_CHARS,
    }


def _governed_payload(
    session: Session,
    *,
    context: ContextBundle,
) -> tuple[dict[str, Any], MobilityPathway, MobilityPathwayVersion, set[str]]:
    if context.work_item.source_object_type != "mobility_pathway_version":
        raise MobilityPathwayBriefError("pathway brief requires a mobility_pathway_version WorkItem")
    if not context.work_item.source_object_id:
        raise MobilityPathwayBriefError("pathway brief WorkItem is missing its pathway version")

    version_id = _uuid(context.work_item.source_object_id, label="pathway version id")
    pathway_version = session.get(MobilityPathwayVersion, version_id)
    if pathway_version is None:
        raise MobilityPathwayBriefError("pathway version was not found")
    pathway = session.get(MobilityPathway, pathway_version.pathway_id)
    if pathway is None:
        raise MobilityPathwayBriefError("pathway was not found")

    evidence_refs = _reference_map(
        context.evidence_refs,
        kind="mobility_pathway_version_evidence",
    )
    rule_refs = _reference_map(context.verified_rule_refs, kind="verified_rule")
    snapshot_refs = _reference_map(context.source_snapshot_refs, kind="source_snapshot")

    evidence_payload: list[dict[str, Any]] = []
    for evidence_id, ref in sorted(evidence_refs.items(), key=lambda pair: str(pair[0])):
        evidence = session.get(MobilityPathwayVersionEvidence, evidence_id)
        if evidence is None or evidence.pathway_version_id != pathway_version.id:
            raise MobilityPathwayBriefError("governed pathway evidence could not be dereferenced")
        if ref.version != canonical_fingerprint(evidence):
            raise MobilityPathwayBriefError("governed pathway evidence changed after context resolution")
        source = session.get(OfficialSource, evidence.official_source_id)
        snapshot = session.get(SourceSnapshot, evidence.source_snapshot_id)
        if source is None or snapshot is None:
            raise MobilityPathwayBriefError("governed pathway evidence provenance is unavailable")
        if snapshot.id not in snapshot_refs:
            raise MobilityPathwayBriefError("governed pathway evidence snapshot is outside ContextBundle authority")
        evidence_payload.append(
            {
                "citation": f"evidence:{evidence.id}",
                "role": evidence.evidence_role,
                "required_for_publication": evidence.required_for_publication,
                "official_source": {
                    "id": str(source.id),
                    "name": source.name,
                    "authority": source.authority,
                    "url": source.url,
                    "country": source.country,
                    "domain": source.domain,
                },
                "snapshot": _source_excerpt(snapshot),
            }
        )

    rule_payload: list[dict[str, Any]] = []
    for rule_id, ref in sorted(rule_refs.items(), key=lambda pair: str(pair[0])):
        rule = session.get(VerifiedRule, rule_id)
        if rule is None:
            raise MobilityPathwayBriefError("governed verified rule could not be dereferenced")
        if ref.version != canonical_fingerprint(rule):
            raise MobilityPathwayBriefError("governed verified rule changed after context resolution")
        if rule.source_snapshot_id is None or rule.source_snapshot_id not in snapshot_refs:
            raise MobilityPathwayBriefError("governed verified rule snapshot is outside ContextBundle authority")
        rule_payload.append(
            {
                "citation": f"verified_rule:{rule.id}",
                "rule_key": rule.rule_key,
                "statement": rule.statement,
                "confidence": rule.confidence,
                "effective_from": rule.effective_from,
                "effective_to": rule.effective_to,
                "source_snapshot_id": str(rule.source_snapshot_id),
            }
        )

    policy_payload: dict[str, Any] | None = None
    policy_refs = [ref for ref in context.canonical_references if ref.kind == "country_policy"]
    if len(policy_refs) > 1:
        raise MobilityPathwayBriefError("ContextBundle contains ambiguous country policy references")
    if policy_refs:
        policy_ref = policy_refs[0]
        policy_id = _uuid(policy_ref.identifier, label="country policy reference")
        policy = session.get(CountryPolicy, policy_id)
        if policy is None:
            raise MobilityPathwayBriefError("governed country policy could not be dereferenced")
        if context.policy_version != canonical_fingerprint(policy) or policy_ref.version != context.policy_version:
            raise MobilityPathwayBriefError("governed country policy changed after context resolution")
        policy_payload = {
            "citation": f"country_policy:{policy.id}",
            "country": policy.country,
            "domain": policy.domain,
            "policy": _json_value(
                policy.policy_json,
                label="country policy",
                expected_type=dict,
                default={},
            ),
            "policy_version": context.policy_version,
        }

    source_payload: list[dict[str, Any]] = []
    for snapshot_id, ref in sorted(snapshot_refs.items(), key=lambda pair: str(pair[0])):
        snapshot = session.get(SourceSnapshot, snapshot_id)
        if snapshot is None:
            raise MobilityPathwayBriefError("governed source snapshot could not be dereferenced")
        if ref.version != canonical_fingerprint(snapshot):
            raise MobilityPathwayBriefError("governed source snapshot changed after context resolution")
        source_payload.append(
            {
                "citation": f"source_snapshot:{snapshot.id}",
                **_source_excerpt(snapshot),
            }
        )

    pathway_ref = next(
        (
            ref
            for ref in context.canonical_references
            if ref.kind == "mobility_pathway_version" and ref.identifier == str(pathway_version.id)
        ),
        None,
    )
    if pathway_ref is None:
        raise MobilityPathwayBriefError("canonical pathway reference is missing")

    payload = {
        "schema_version": PATHWAY_BRIEF_SCHEMA_VERSION,
        "purpose": "internal_governed_pathway_brief",
        "employee": {
            "position_key": context.position.position_key,
            "title": context.position.title,
            "department": context.position.department,
        },
        "work_item": {
            "id": str(context.work_item.work_item_id),
            "title": context.work_item.title,
            "objective": context.work_item.objective,
            "risk_level": context.work_item.risk_level,
        },
        "context": {
            "context_hash": context.context_hash,
            "unknowns": context.unknowns,
            "contradictions": context.contradictions,
            "policy_version": context.policy_version,
        },
        "pathway": {
            "citation": f"mobility_pathway_version:{pathway_version.id}",
            "pathway_id": str(pathway.id),
            "pathway_key": pathway.pathway_key,
            "name": pathway.name,
            "country": pathway.country,
            "domain": pathway.domain,
            "pathway_version_id": str(pathway_version.id),
            "pathway_version": pathway_version.version_number,
            "pathway_fingerprint": pathway_ref.version,
            "eligibility_criteria": _json_value(
                pathway_version.eligibility_criteria_json,
                label="pathway eligibility criteria",
                expected_type=dict,
                default={},
            ),
            "required_documents": _json_value(
                pathway_version.required_documents_json,
                label="pathway required documents",
                expected_type=list,
                default=[],
            ),
            "costs": _json_value(
                pathway_version.costs_json,
                label="pathway costs",
                expected_type=dict,
                default={},
            ),
            "processing_time": _json_value(
                pathway_version.processing_time_json,
                label="pathway processing time",
                expected_type=dict,
                default={},
            ),
            "benefits": _json_value(
                pathway_version.benefits_json,
                label="pathway benefits",
                expected_type=list,
                default=[],
            ),
            "risks": _json_value(
                pathway_version.risks_json,
                label="pathway risks",
                expected_type=list,
                default=[],
            ),
        },
        "evidence": evidence_payload,
        "verified_rules": rule_payload,
        "source_snapshots": source_payload,
        "country_policy": policy_payload,
    }

    allowed_citations = {
        payload["pathway"]["citation"],
        *(item["citation"] for item in evidence_payload),
        *(item["citation"] for item in rule_payload),
        *(item["citation"] for item in source_payload),
    }
    if policy_payload is not None:
        allowed_citations.add(policy_payload["citation"])
    return payload, pathway, pathway_version, allowed_citations


_SYSTEM_PROMPT = """You are an internal AI employee inside Global Mobility AIOS.
Prepare a professional mobility pathway research brief using ONLY the governed JSON payload provided.
Do not add facts, requirements, costs, processing times, legal conclusions, or policy claims that are absent from the payload.
This is not an eligibility decision, legal advice, client communication, certification, submission, or canonical truth mutation.
Return one JSON object only with exactly these keys:
summary, key_requirements, material_risks, evidence_gaps, operator_questions, evidence_basis,
human_review_required, client_facing, canonical_commit_allowed, external_action_authorized.
All list fields must be arrays of strings. evidence_basis entries must be citation tokens copied exactly from the governed payload.
The safety flags must be: human_review_required=true, client_facing=false, canonical_commit_allowed=false, external_action_authorized=false.
"""


def _non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MobilityPathwayBriefOutputError(f"{label} must be a non-empty string")
    return value.strip()


def _string_tuple(value: Any, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise MobilityPathwayBriefOutputError(f"{label} must be an array")
    items = tuple(_non_empty_string(item, label=f"{label} item") for item in value)
    return items


def _validated_draft(content: str, *, allowed_citations: set[str]) -> MobilityPathwayBriefDraft:
    try:
        payload = json.loads(content)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MobilityPathwayBriefOutputError("runtime output is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise MobilityPathwayBriefOutputError("runtime output must be a JSON object")

    expected_keys = {
        "summary",
        "key_requirements",
        "material_risks",
        "evidence_gaps",
        "operator_questions",
        "evidence_basis",
        "human_review_required",
        "client_facing",
        "canonical_commit_allowed",
        "external_action_authorized",
    }
    if set(payload) != expected_keys:
        raise MobilityPathwayBriefOutputError("runtime output does not match the pathway-brief schema")

    evidence_basis = _string_tuple(payload["evidence_basis"], label="evidence_basis")
    if any(citation not in allowed_citations for citation in evidence_basis):
        raise MobilityPathwayBriefOutputError("runtime cited authority outside the governed ContextBundle")

    required_flags = {
        "human_review_required": True,
        "client_facing": False,
        "canonical_commit_allowed": False,
        "external_action_authorized": False,
    }
    for key, expected in required_flags.items():
        if payload.get(key) is not expected:
            raise MobilityPathwayBriefOutputError(f"unsafe pathway-brief flag {key}")

    return MobilityPathwayBriefDraft(
        summary=_non_empty_string(payload["summary"], label="summary"),
        key_requirements=_string_tuple(payload["key_requirements"], label="key_requirements"),
        material_risks=_string_tuple(payload["material_risks"], label="material_risks"),
        evidence_gaps=_string_tuple(payload["evidence_gaps"], label="evidence_gaps"),
        operator_questions=_string_tuple(payload["operator_questions"], label="operator_questions"),
        evidence_basis=evidence_basis,
        human_review_required=True,
        client_facing=False,
        canonical_commit_allowed=False,
        external_action_authorized=False,
    )


def _runtime_provider(profile: AgentRuntimeProfile, provider: LLMProvider | None) -> LLMProvider:
    if profile.runtime_class is not RuntimeClass.HOSTED_API:
        raise MobilityPathwayBriefRuntimeError("E.1 supports only the hosted_api runtime class")
    if provider is not None:
        return provider
    try:
        return LLMProviderFactory.get_provider(profile.provider_key)
    except LLMProviderError as exc:
        raise MobilityPathwayBriefRuntimeError("configured hosted runtime is unavailable") from exc


def prepare_governed_mobility_pathway_brief(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    work_item_id: UUID,
    runtime_profile: AgentRuntimeProfile,
    provider: LLMProvider | None = None,
) -> GovernedMobilityPathwayBriefResult:
    """Execute the first bounded end-to-end Global Mobility AIOS vertical.

    The vertical is read-only and produces an internal research draft. Governed
    ContextBundle state is resolved first, then bound to the technical runtime. Only
    canonical pathway/Evidence/rule/policy content is sent to the runtime; arbitrary
    WorkItem working-context JSON is deliberately excluded from the model payload.
    """

    context = build_work_item_context_bundle(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        work_item_id=work_item_id,
        purpose=ContextPurpose.RESEARCH,
    )
    binding = bind_employee_runtime(
        session,
        context=context,
        profile=runtime_profile,
        required_capability="structured_output",
    )
    governed_payload, pathway, pathway_version, allowed_citations = _governed_payload(
        session,
        context=context,
    )

    prompt_payload = canonical_json(governed_payload)
    response_format = {"type": "json_object"}
    prompt_fingerprint = canonical_fingerprint(
        {
            "system_prompt": _SYSTEM_PROMPT,
            "governed_payload": governed_payload,
            "response_format": response_format,
            "runtime_binding_hash": binding.binding_hash,
        }
    )

    runtime = _runtime_provider(runtime_profile, provider)
    try:
        response: LLMResponse = runtime.complete(
            system_prompt=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_payload}],
            response_format=response_format,
        )
    except LLMProviderError as exc:
        raise MobilityPathwayBriefRuntimeError("hosted runtime execution failed") from exc

    if response.provider != runtime_profile.provider_key:
        raise MobilityPathwayBriefRuntimeError("runtime response provider does not match the bound profile")

    draft = _validated_draft(response.content, allowed_citations=allowed_citations)
    vertical_status = (
        "insufficient_governed_context"
        if context.unknowns or context.contradictions
        else "prepared_for_human_review"
    )

    return GovernedMobilityPathwayBriefResult(
        schema_version=PATHWAY_BRIEF_SCHEMA_VERSION,
        context=context,
        runtime_binding=binding,
        pathway_id=pathway.id,
        pathway_version_id=pathway_version.id,
        pathway_name=pathway.name,
        vertical_status=vertical_status,
        prompt_fingerprint=prompt_fingerprint,
        provider=response.provider,
        model=response.model,
        draft=draft,
    )

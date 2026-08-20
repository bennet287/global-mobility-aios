from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    CountryPolicy,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityPathwayVersionEvidence,
    OfficialSource,
    OrganizationPosition,
    OrganizationalWorkItem,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.organization_command import canonical_fingerprint


class ContextAuthorityError(RuntimeError):
    """Governed authority-bearing context could not be resolved safely."""


@dataclass(frozen=True)
class AuthorityReference:
    kind: str
    identifier: str
    version: str | None = None


@dataclass(frozen=True)
class ContextAuthorityContribution:
    """Authority-bearing additions to a ContextBundle.

    The contribution contains references/fingerprints only. It never injects raw
    Evidence, rule text, policy payloads or runtime/provider identity into the
    ContextBundle. The model/runtime may dereference approved references through
    later bounded read/tool contracts.
    """

    source_reference_version: str | None = None
    canonical_references: tuple[AuthorityReference, ...] = ()
    evidence_refs: tuple[AuthorityReference, ...] = ()
    verified_rule_refs: tuple[AuthorityReference, ...] = ()
    source_snapshot_refs: tuple[AuthorityReference, ...] = ()
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    policy_version: str | None = None


class ContextAuthorityAdapter(Protocol):
    source_object_type: str

    def resolve(
        self,
        session: Session,
        *,
        position: OrganizationPosition,
        work_item: OrganizationalWorkItem,
        resolved_at: datetime,
    ) -> ContextAuthorityContribution: ...


def _json_object(raw: str | None, *, label: str) -> dict[str, object]:
    candidate = raw if raw not in (None, "") else "{}"
    try:
        decoded = json.loads(candidate)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ContextAuthorityError(f"{label} is not valid JSON") from exc
    if not isinstance(decoded, dict):
        raise ContextAuthorityError(f"{label} must be a JSON object")
    return decoded


def _uuid(value: str | UUID | None, *, label: str) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ContextAuthorityError(f"{label} must be a UUID") from exc


def _uuid_list(raw: str | None, *, label: str) -> tuple[UUID, ...]:
    candidate = raw if raw not in (None, "") else "[]"
    try:
        decoded = json.loads(candidate)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ContextAuthorityError(f"{label} is not valid JSON") from exc
    if not isinstance(decoded, list):
        raise ContextAuthorityError(f"{label} must be a JSON array")
    values: list[UUID] = []
    for item in decoded:
        values.append(_uuid(item, label=f"{label} item"))
    if len(set(values)) != len(values):
        raise ContextAuthorityError(f"{label} contains duplicate identifiers")
    return tuple(values)


def _position_allowed_tools(position: OrganizationPosition) -> tuple[str, ...]:
    """Resolve temporary D.3 tool entitlements from one explicit contract namespace.

    `OrganizationPosition.contract_json` is intentionally a transitional authority
    source. Only `context_authority.allowed_tools` is interpreted here. A dedicated
    ToolEntitlement model remains a later migration candidate once the first vertical
    proves the durable shape.
    """

    contract = _json_object(position.contract_json, label="position contract")
    namespace = contract.get("context_authority")
    if namespace is None:
        return ()
    if not isinstance(namespace, dict):
        raise ContextAuthorityError("position context_authority must be a JSON object")
    raw_tools = namespace.get("allowed_tools", [])
    if not isinstance(raw_tools, list):
        raise ContextAuthorityError("position context_authority.allowed_tools must be a JSON array")

    tools: set[str] = set()
    for raw_tool in raw_tools:
        if not isinstance(raw_tool, str) or not raw_tool.strip():
            raise ContextAuthorityError("position allowed tool names must be non-empty strings")
        tools.add(raw_tool.strip())
    return tuple(sorted(tools))


def _source_snapshot(
    session: Session,
    snapshot_id: UUID,
    *,
    label: str,
) -> SourceSnapshot:
    snapshot = session.get(SourceSnapshot, snapshot_id)
    if snapshot is None:
        raise ContextAuthorityError(f"{label} source snapshot was not found")
    return snapshot


def _official_source(
    session: Session,
    source_id: UUID,
    *,
    label: str,
) -> OfficialSource:
    source = session.get(OfficialSource, source_id)
    if source is None or not source.active:
        raise ContextAuthorityError(f"{label} official source is unavailable")
    return source


def _snapshot_reference(snapshot: SourceSnapshot) -> AuthorityReference:
    return AuthorityReference(
        kind="source_snapshot",
        identifier=str(snapshot.id),
        version=canonical_fingerprint(snapshot),
    )


def _rule_reference(rule: VerifiedRule) -> AuthorityReference:
    return AuthorityReference(
        kind="verified_rule",
        identifier=str(rule.id),
        version=canonical_fingerprint(rule),
    )


def _evidence_reference(evidence: MobilityPathwayVersionEvidence) -> AuthorityReference:
    return AuthorityReference(
        kind="mobility_pathway_version_evidence",
        identifier=str(evidence.id),
        version=canonical_fingerprint(evidence),
    )


def _validate_snapshot_source_link(
    session: Session,
    *,
    snapshot: SourceSnapshot,
    official_source_id: UUID | None,
    label: str,
) -> None:
    source_id = official_source_id or snapshot.official_source_id
    if source_id is None:
        raise ContextAuthorityError(f"{label} has no official-source provenance")
    source = _official_source(session, source_id, label=label)
    if snapshot.official_source_id is not None and snapshot.official_source_id != source.id:
        raise ContextAuthorityError(f"{label} source snapshot does not match its official source")


def _active_country_policy(
    session: Session,
    *,
    country: str,
    domain: str,
) -> CountryPolicy | None:
    rows = list(
        session.exec(
            select(CountryPolicy).where(
                CountryPolicy.country == country,
                CountryPolicy.domain == domain,
                CountryPolicy.status == "active",
            )
        ).all()
    )
    if len(rows) > 1:
        raise ContextAuthorityError("multiple active country policies make authority context ambiguous")
    if not rows:
        return None
    policy = rows[0]
    _json_object(policy.policy_json, label="country policy")
    return policy


def _effective_now(
    *,
    effective_from: datetime | None,
    effective_to: datetime | None,
    resolved_at: datetime,
) -> bool:
    if effective_from is not None and effective_from > resolved_at:
        return False
    if effective_to is not None and effective_to < resolved_at:
        return False
    return True


class MobilityPathwayVersionAuthorityAdapter:
    source_object_type = "mobility_pathway_version"

    def resolve(
        self,
        session: Session,
        *,
        position: OrganizationPosition,
        work_item: OrganizationalWorkItem,
        resolved_at: datetime,
    ) -> ContextAuthorityContribution:
        version_id = _uuid(work_item.source_object_id, label="mobility pathway version id")
        pathway_version = session.get(MobilityPathwayVersion, version_id)
        if pathway_version is None:
            raise ContextAuthorityError("mobility pathway version was not found")
        pathway = session.get(MobilityPathway, pathway_version.pathway_id)
        if pathway is None:
            raise ContextAuthorityError("mobility pathway parent was not found")

        if pathway_version.lifecycle_status != "published" or pathway_version.published_at is None:
            raise ContextAuthorityError("mobility pathway version is not published")
        if not _effective_now(
            effective_from=pathway_version.effective_from,
            effective_to=pathway_version.effective_to,
            resolved_at=resolved_at,
        ):
            raise ContextAuthorityError("mobility pathway version is outside its effective window")

        source_snapshots: dict[UUID, SourceSnapshot] = {}
        if pathway_version.source_snapshot_id is not None:
            snapshot = _source_snapshot(
                session,
                pathway_version.source_snapshot_id,
                label="mobility pathway version",
            )
            _validate_snapshot_source_link(
                session,
                snapshot=snapshot,
                official_source_id=pathway_version.official_source_id,
                label="mobility pathway version",
            )
            source_snapshots[snapshot.id] = snapshot
        elif pathway_version.official_source_id is not None:
            _official_source(session, pathway_version.official_source_id, label="mobility pathway version")

        evidence_rows = list(
            session.exec(
                select(MobilityPathwayVersionEvidence)
                .where(MobilityPathwayVersionEvidence.pathway_version_id == pathway_version.id)
                .order_by(MobilityPathwayVersionEvidence.id)
            ).all()
        )
        evidence_refs: list[AuthorityReference] = []
        for evidence in evidence_rows:
            snapshot = _source_snapshot(
                session,
                evidence.source_snapshot_id,
                label="pathway evidence",
            )
            _validate_snapshot_source_link(
                session,
                snapshot=snapshot,
                official_source_id=evidence.official_source_id,
                label="pathway evidence",
            )
            _json_object(evidence.metadata_json, label="pathway evidence metadata")
            source_snapshots[snapshot.id] = snapshot
            evidence_refs.append(_evidence_reference(evidence))

        rule_ids = _uuid_list(
            pathway_version.verified_rule_ids_json,
            label="mobility pathway verified rule ids",
        )
        rule_refs: list[AuthorityReference] = []
        for rule_id in rule_ids:
            rule = session.get(VerifiedRule, rule_id)
            if rule is None:
                raise ContextAuthorityError("referenced verified rule was not found")
            if not rule.active or rule.retired_at is not None:
                raise ContextAuthorityError("referenced verified rule is stale or retired")
            if rule.published_at is None:
                raise ContextAuthorityError("referenced verified rule is not published")
            if not _effective_now(
                effective_from=rule.effective_from,
                effective_to=rule.effective_to,
                resolved_at=resolved_at,
            ):
                raise ContextAuthorityError("referenced verified rule is outside its effective window")
            if rule.country.casefold() != pathway.country.casefold() or rule.domain.casefold() != pathway.domain.casefold():
                raise ContextAuthorityError("referenced verified rule does not match pathway country/domain")
            if rule.source_snapshot_id is None:
                raise ContextAuthorityError("referenced verified rule has no source-snapshot provenance")
            snapshot = _source_snapshot(session, rule.source_snapshot_id, label="verified rule")
            _validate_snapshot_source_link(
                session,
                snapshot=snapshot,
                official_source_id=rule.official_source_id,
                label="verified rule",
            )
            source_snapshots[snapshot.id] = snapshot
            rule_refs.append(_rule_reference(rule))

        policy = _active_country_policy(
            session,
            country=pathway.country,
            domain=pathway.domain,
        )
        canonical_refs: list[AuthorityReference] = []
        policy_version: str | None = None
        unknowns: list[str] = []
        if policy is None:
            unknowns.append("country_policy_missing")
        else:
            policy_version = canonical_fingerprint(policy)
            canonical_refs.append(
                AuthorityReference(
                    kind="country_policy",
                    identifier=str(policy.id),
                    version=policy_version,
                )
            )
        if not evidence_refs:
            unknowns.append("mobility_pathway_version_evidence_missing")

        source_version = canonical_fingerprint(
            {
                "pathway": pathway,
                "pathway_version": pathway_version,
            }
        )
        return ContextAuthorityContribution(
            source_reference_version=source_version,
            canonical_references=tuple(canonical_refs),
            evidence_refs=tuple(evidence_refs),
            verified_rule_refs=tuple(rule_refs),
            source_snapshot_refs=tuple(
                _snapshot_reference(source_snapshots[snapshot_id])
                for snapshot_id in sorted(source_snapshots, key=str)
            ),
            unknowns=tuple(sorted(unknowns)),
            allowed_tools=_position_allowed_tools(position),
            policy_version=policy_version,
        )


_MOBILITY_PATHWAY_VERSION_ADAPTER = MobilityPathwayVersionAuthorityAdapter()
_CONTEXT_AUTHORITY_ADAPTERS: dict[str, ContextAuthorityAdapter] = {
    _MOBILITY_PATHWAY_VERSION_ADAPTER.source_object_type: _MOBILITY_PATHWAY_VERSION_ADAPTER,
}


def context_authority_adapter_types() -> frozenset[str]:
    """Return the statically registered source types supported by governed adapters."""

    return frozenset(_CONTEXT_AUTHORITY_ADAPTERS)


def resolve_context_authority(
    session: Session,
    *,
    position: OrganizationPosition,
    work_item: OrganizationalWorkItem,
    resolved_at: datetime | None = None,
) -> ContextAuthorityContribution:
    """Resolve authority-bearing ContextBundle fields from canonical AIOS state.

    Working context JSON is never consulted for Evidence, rule, policy or tool
    authority. Unsupported source types retain D.1 behavior except that explicit
    position-contract tool entitlements may still be resolved.
    """

    tools = _position_allowed_tools(position)
    source_type = (work_item.source_object_type or "").strip()
    if not source_type:
        return ContextAuthorityContribution(allowed_tools=tools)

    adapter = _CONTEXT_AUTHORITY_ADAPTERS.get(source_type)
    if adapter is None:
        return ContextAuthorityContribution(allowed_tools=tools)

    contribution = adapter.resolve(
        session,
        position=position,
        work_item=work_item,
        resolved_at=resolved_at or now_utc(),
    )
    # Adapter-specific resolution may eventually add narrower tool constraints. D.3
    # currently uses the position contract as the sole MAY-USE source, so keep one
    # normalized authoritative set here.
    if contribution.allowed_tools != tools:
        raise ContextAuthorityError("context authority adapter returned non-canonical tool entitlements")
    return contribution

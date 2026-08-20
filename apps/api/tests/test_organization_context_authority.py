from __future__ import annotations

import json
from dataclasses import fields
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlmodel import Session

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
from app.services.organization_command import TenantMismatch, canonical_json
from app.services.organization_context_authority import context_authority_adapter_types
from app.services.organization_context_broker import (
    ContextBundle,
    ContextIntegrityError,
    build_work_item_context_bundle,
)


def _position(
    session: Session,
    *,
    contract_json: str = '{"context_authority":{"allowed_tools":["official_source.search","document.read"]}}',
) -> OrganizationPosition:
    row = OrganizationPosition(
        position_key="austria_mobility_specialist",
        title="Austria Immigration Specialist",
        department="Mobility",
        reports_to_position_key="mobility_operations_lead",
        role_card_name="austria_mobility_specialist",
        authority_level="L2",
        contract_json=contract_json,
        status="active",
        version=5,
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _authority_graph(
    session: Session,
    *,
    with_evidence: bool = True,
    with_policy: bool = True,
    rule_country: str = "austria",
    rule_domain: str = "visa",
) -> dict[str, object]:
    source = OfficialSource(
        country="austria",
        domain="visa",
        name="Austrian official immigration source",
        url=f"https://example.gv.at/{uuid4()}",
        source_type="government",
        authority="Austrian authority",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="snapshot-v1",
        content_text="Published Austrian mobility guidance.",
        http_status=200,
        retrieval_method="http",
        parser_version="pytest-v1",
        status="captured",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    rule = VerifiedRule(
        country=rule_country,
        domain=rule_domain,
        rule_key=f"at-rule-{uuid4()}",
        statement="A governed Austrian mobility rule.",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        confidence=0.99,
        active=True,
        effective_from=now_utc() - timedelta(days=30),
        approved_by="pytest-reviewer",
        published_at=now_utc() - timedelta(days=1),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)

    pathway = MobilityPathway(
        pathway_key=f"at-path-{uuid4()}",
        name="Austrian governed mobility pathway",
        country="austria",
        domain="visa",
        catalogue_status="published",
        created_by="pytest",
    )
    session.add(pathway)
    session.commit()
    session.refresh(pathway)

    pathway_version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=3,
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        verified_rule_ids_json=json.dumps([str(rule.id)]),
        eligibility_criteria_json='{"criterion":"governed"}',
        metadata_json='{"scope":"test"}',
        effective_from=now_utc() - timedelta(days=10),
        human_review_required=True,
        approved_by="pytest-reviewer",
        published_at=now_utc() - timedelta(days=1),
        created_by="pytest",
    )
    session.add(pathway_version)
    session.commit()
    session.refresh(pathway_version)

    evidence = None
    if with_evidence:
        evidence = MobilityPathwayVersionEvidence(
            pathway_version_id=pathway_version.id,
            evidence_role="primary",
            official_source_id=source.id,
            source_snapshot_id=snapshot.id,
            required_for_publication=True,
            metadata_json='{"purpose":"primary authority"}',
        )
        session.add(evidence)
        session.commit()
        session.refresh(evidence)

    policy = None
    if with_policy:
        policy = CountryPolicy(
            country="austria",
            domain="visa",
            policy_json='{"human_review_required":true,"verification_required":true}',
            status="active",
            last_reviewed_at=now_utc() - timedelta(days=2),
        )
        session.add(policy)
        session.commit()
        session.refresh(policy)

    return {
        "source": source,
        "snapshot": snapshot,
        "rule": rule,
        "pathway": pathway,
        "pathway_version": pathway_version,
        "evidence": evidence,
        "policy": policy,
    }


def _work(
    session: Session,
    pathway_version: MobilityPathwayVersion,
    *,
    tenant_key: str = "tenant-a",
    context_json: str = "{}",
) -> OrganizationalWorkItem:
    row = OrganizationalWorkItem(
        idempotency_key=f"authority-context-work-{uuid4()}",
        tenant_key=tenant_key,
        title="Assess Austrian pathway",
        objective="Use governed pathway Evidence and rules for a bounded assessment.",
        department="Mobility",
        authority_level="L2",
        assigned_position_key="austria_mobility_specialist",
        risk_level="routine",
        context_json=context_json,
        source_object_type="mobility_pathway_version",
        source_object_id=str(pathway_version.id),
        source_object_version="caller-hint-must-not-be-authoritative",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _bundle(session: Session, work: OrganizationalWorkItem) -> ContextBundle:
    return build_work_item_context_bundle(
        session,
        tenant_key="tenant-a",
        position_key="austria_mobility_specialist",
        work_item_id=work.id,
    )


def test_populates_deterministic_bundle_from_real_governed_authority(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(
        db_session,
        graph["pathway_version"],
        context_json=canonical_json(
            {
                "verified_rule_refs": ["self-promoted-rule"],
                "evidence_refs": ["self-promoted-evidence"],
                "allowed_tools": ["shell"],
                "policy_version": "latest",
                "provider": "self-selected-provider",
            }
        ),
    )

    first = _bundle(db_session, work)
    second = _bundle(db_session, work)

    assert first.context_hash == second.context_hash
    assert len(first.evidence_refs) == 1
    assert first.evidence_refs[0].kind == "mobility_pathway_version_evidence"
    assert len(first.verified_rule_refs) == 1
    assert first.verified_rule_refs[0].identifier == str(graph["rule"].id)
    assert len(first.source_snapshot_refs) == 1
    assert first.source_snapshot_refs[0].identifier == str(graph["snapshot"].id)
    assert first.allowed_tools == ("document.read", "official_source.search")
    assert first.policy_version is not None and len(first.policy_version) == 64
    assert any(ref.kind == "country_policy" for ref in first.canonical_references)
    pathway_ref = next(ref for ref in first.canonical_references if ref.kind == "mobility_pathway_version")
    assert pathway_ref.version != work.source_object_version
    assert pathway_ref.version is not None and len(pathway_ref.version) == 64

    # Working context remains visible only as working context; none of its attempted
    # authority promotion changes the governed fields above.
    assert "self-promoted-rule" in first.work_item.working_context_json
    assert "self-selected-provider" in first.work_item.working_context_json
    assert "shell" not in first.allowed_tools

    names = {item.name for item in fields(ContextBundle)}
    assert "provider" not in names
    assert "model" not in names
    assert "runtime_id" not in names
    assert "session_id" not in names


def test_context_hash_changes_when_pathway_version_changes(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"])
    first = _bundle(db_session, work)

    pathway_version = graph["pathway_version"]
    pathway_version.metadata_json = '{"scope":"changed"}'
    pathway_version.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(pathway_version)
    db_session.commit()

    second = _bundle(db_session, work)
    assert first.context_hash != second.context_hash
    first_ref = next(ref for ref in first.canonical_references if ref.kind == "mobility_pathway_version")
    second_ref = next(ref for ref in second.canonical_references if ref.kind == "mobility_pathway_version")
    assert first_ref.version != second_ref.version


def test_context_hash_changes_when_active_verified_rule_changes(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"])
    first = _bundle(db_session, work)

    rule = graph["rule"]
    rule.statement = "Updated governed Austrian mobility rule."
    rule.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(rule)
    db_session.commit()

    second = _bundle(db_session, work)
    assert first.context_hash != second.context_hash
    assert first.verified_rule_refs[0].version != second.verified_rule_refs[0].version


def test_context_hash_and_policy_version_change_when_country_policy_changes(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"])
    first = _bundle(db_session, work)

    policy = graph["policy"]
    policy.policy_json = '{"human_review_required":true,"verification_required":true,"review_depth":"deep"}'
    policy.updated_at = now_utc() + timedelta(seconds=1)
    db_session.add(policy)
    db_session.commit()

    second = _bundle(db_session, work)
    assert first.context_hash != second.context_hash
    assert first.policy_version != second.policy_version


def test_context_hash_changes_when_source_snapshot_changes(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"])
    first = _bundle(db_session, work)

    snapshot = graph["snapshot"]
    snapshot.content_hash = "snapshot-v2"
    snapshot.content_text = "Changed official source capture."
    snapshot.captured_at = now_utc() + timedelta(seconds=1)
    db_session.add(snapshot)
    db_session.commit()

    second = _bundle(db_session, work)
    assert first.context_hash != second.context_hash
    assert first.source_snapshot_refs[0].version != second.source_snapshot_refs[0].version


@pytest.mark.parametrize("rule_state", ["unpublished", "retired", "expired"])
def test_unusable_verified_rule_fails_closed(db_session: Session, rule_state: str) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"])
    rule = graph["rule"]

    if rule_state == "unpublished":
        rule.published_at = None
    elif rule_state == "retired":
        rule.active = False
        rule.retired_at = now_utc()
    else:
        rule.effective_to = now_utc() - timedelta(seconds=1)
    db_session.add(rule)
    db_session.commit()

    with pytest.raises(ContextIntegrityError):
        _bundle(db_session, work)


def test_malformed_rule_list_and_wrong_country_domain_fail_closed(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"])
    pathway_version = graph["pathway_version"]

    pathway_version.verified_rule_ids_json = "{not-a-list}"
    db_session.add(pathway_version)
    db_session.commit()
    with pytest.raises(ContextIntegrityError):
        _bundle(db_session, work)

    pathway_version.verified_rule_ids_json = json.dumps([str(graph["rule"].id)])
    rule = graph["rule"]
    rule.country = "germany"
    db_session.add_all([pathway_version, rule])
    db_session.commit()
    with pytest.raises(ContextIntegrityError):
        _bundle(db_session, work)


def test_foreign_tenant_work_item_remains_non_disclosing_before_global_adapter_resolution(
    db_session: Session,
) -> None:
    _position(db_session)
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"], tenant_key="tenant-b")

    with pytest.raises(TenantMismatch):
        _bundle(db_session, work)


def test_missing_pathway_evidence_is_empty_but_visible(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session, with_evidence=False)
    work = _work(db_session, graph["pathway_version"])

    bundle = _bundle(db_session, work)
    assert bundle.evidence_refs == ()
    assert "mobility_pathway_version_evidence_missing" in bundle.unknowns
    assert len(bundle.verified_rule_refs) == 1


def test_missing_country_policy_is_visible_without_fabricating_policy_version(db_session: Session) -> None:
    _position(db_session)
    graph = _authority_graph(db_session, with_policy=False)
    work = _work(db_session, graph["pathway_version"])

    bundle = _bundle(db_session, work)
    assert bundle.policy_version is None
    assert "country_policy_missing" in bundle.unknowns
    assert not any(ref.kind == "country_policy" for ref in bundle.canonical_references)


def test_position_without_tool_namespace_gets_no_tools(db_session: Session) -> None:
    _position(db_session, contract_json='{"jurisdiction":"AT","scope":"mobility_case"}')
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"])

    bundle = _bundle(db_session, work)
    assert bundle.allowed_tools == ()


def test_malformed_tool_entitlement_namespace_fails_closed(db_session: Session) -> None:
    _position(
        db_session,
        contract_json='{"context_authority":{"allowed_tools":"shell"}}',
    )
    graph = _authority_graph(db_session)
    work = _work(db_session, graph["pathway_version"])

    with pytest.raises(ContextIntegrityError):
        _bundle(db_session, work)


def test_context_authority_adapter_registry_is_explicit_and_bounded() -> None:
    assert context_authority_adapter_types() == frozenset({"mobility_pathway_version"})

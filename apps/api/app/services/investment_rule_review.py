from __future__ import annotations

import json
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    InvestmentMobilityRuleDecision,
    InvestmentMobilityRuleProposal,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.schemas_investment_rule_review import (
    InvestmentRuleProposalCreate,
    InvestmentRuleProposalRead,
    InvestmentRuleProposalReview,
)
from app.services.audit_log import record_audit


ALLOWED_DOMAINS = {"investment", "wealth", "business", "entrepreneur"}


def _dump(value) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)


def _load(value: str | None, default):
    return json.loads(value) if value else default


def investment_rule_proposal_read(
    session: Session,
    row: InvestmentMobilityRuleProposal,
) -> InvestmentRuleProposalRead:
    version = session.get(MobilityPathwayVersion, row.pathway_version_id)
    pathway = session.get(MobilityPathway, version.pathway_id) if version else None
    source = session.get(OfficialSource, row.official_source_id)
    snapshot = session.get(SourceSnapshot, row.source_snapshot_id)
    if version is None or pathway is None or source is None or snapshot is None or not snapshot.content_hash:
        raise ValueError("Investment rule proposal evidence is incomplete")
    return InvestmentRuleProposalRead(
        **row.model_dump(),
        pathway_id=pathway.id,
        pathway_name=pathway.name,
        country=pathway.country,
        domain=pathway.domain,
        source_url=source.url,
        source_content_hash=snapshot.content_hash,
        rules=_load(row.proposed_rules_json, []),
        created_verified_rule_ids=[
            UUID(str(value)) for value in _load(row.created_verified_rule_ids_json, [])
        ],
    )


def create_investment_rule_proposal(
    session: Session,
    payload: InvestmentRuleProposalCreate,
    *,
    actor: str,
) -> InvestmentMobilityRuleProposal:
    version = session.get(MobilityPathwayVersion, payload.pathway_version_id)
    if version is None:
        raise ValueError("Pathway version not found")
    if version.lifecycle_status != "draft":
        raise ValueError("Only a draft pathway version can receive a rule proposal")
    pathway = session.get(MobilityPathway, version.pathway_id)
    if pathway is None or pathway.domain not in ALLOWED_DOMAINS:
        raise ValueError("An investment, wealth, business, or entrepreneur pathway is required")
    source = session.get(OfficialSource, version.official_source_id) if version.official_source_id else None
    snapshot = session.get(SourceSnapshot, version.source_snapshot_id) if version.source_snapshot_id else None
    if source is None or not source.active or source.domain not in ALLOWED_DOMAINS:
        raise ValueError("An active eligible official source is required")
    if source.country != pathway.country:
        raise ValueError("Official source country does not match the pathway")
    if snapshot is None or snapshot.official_source_id != source.id or not snapshot.content_hash:
        raise ValueError("A content-addressed snapshot from the pathway source is required")
    existing = session.exec(select(InvestmentMobilityRuleProposal).where(
        InvestmentMobilityRuleProposal.pathway_version_id == version.id,
        InvestmentMobilityRuleProposal.status == "pending_review",
    )).first()
    if existing:
        raise ValueError("A pending rule proposal already exists for this pathway version")

    now = now_utc()
    row = InvestmentMobilityRuleProposal(
        pathway_version_id=version.id,
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        proposed_rules_json=_dump([rule.model_dump(mode="json") for rule in payload.rules]),
        proposed_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="investment_mobility_rule_proposal_created",
        entity_type="investment_mobility_rule_proposal",
        entity_id=row.id,
        after_state=row,
        reason="Created source-pinned investment rule proposal for independent review",
        actor=actor,
        source="investment_rule_review_v11_9",
    )
    session.commit()
    session.refresh(row)
    return row


def review_investment_rule_proposal(
    session: Session,
    proposal_id: UUID,
    payload: InvestmentRuleProposalReview,
    *,
    actor: str,
) -> InvestmentMobilityRuleProposal:
    proposal = session.get(InvestmentMobilityRuleProposal, proposal_id)
    if proposal is None:
        raise ValueError("Investment rule proposal not found")
    if proposal.status != "pending_review":
        raise ValueError("Only pending investment rule proposals can be reviewed")
    if proposal.proposed_by == actor:
        raise ValueError("Investment rule review requires an independent reviewer")
    version = session.get(MobilityPathwayVersion, proposal.pathway_version_id)
    pathway = session.get(MobilityPathway, version.pathway_id) if version else None
    source = session.get(OfficialSource, proposal.official_source_id)
    snapshot = session.get(SourceSnapshot, proposal.source_snapshot_id)
    if (
        version is None or pathway is None or source is None or snapshot is None
        or not snapshot.content_hash or snapshot.official_source_id != source.id
    ):
        raise ValueError("Investment rule proposal evidence is incomplete")

    now = now_utc()
    decision = InvestmentMobilityRuleDecision(
        proposal_id=proposal.id,
        decision=payload.decision,
        reason=payload.reason,
        reviewer=actor,
        created_at=now,
    )
    session.add(decision)
    proposal.status = payload.decision
    proposal.reviewed_by = actor
    proposal.reviewed_at = now
    proposal.review_notes = payload.reason
    proposal.updated_at = now

    created_rule_ids: list[UUID] = []
    replacement: MobilityPathwayVersion | None = None
    if payload.decision == "approved":
        rule_inputs = _load(proposal.proposed_rules_json, [])
        for item in rule_inputs:
            duplicate = session.exec(select(VerifiedRule).where(
                VerifiedRule.country == pathway.country,
                VerifiedRule.domain == pathway.domain,
                VerifiedRule.rule_key == item["rule_key"],
                VerifiedRule.active == True,  # noqa: E712
            )).first()
            if duplicate:
                raise ValueError(f"Active verified rule already exists: {item['rule_key']}")
            rule = VerifiedRule(
                country=pathway.country,
                domain=pathway.domain,
                rule_key=item["rule_key"],
                statement=item["statement"],
                official_source_id=source.id,
                jurisdiction_id=pathway.jurisdiction_id,
                source_snapshot_id=snapshot.id,
                confidence=1.0,
                active=True,
                approved_by=actor,
                published_at=now,
                created_at=now,
                updated_at=now,
            )
            session.add(rule)
            session.flush()
            created_rule_ids.append(rule.id)

        existing_versions = list(session.exec(
            select(MobilityPathwayVersion).where(
                MobilityPathwayVersion.pathway_id == pathway.id
            )
        ).all())
        replacement = MobilityPathwayVersion(
            pathway_id=pathway.id,
            version_number=max(row.version_number for row in existing_versions) + 1,
            lifecycle_status="draft",
            supersedes_version_id=version.id,
            official_source_id=version.official_source_id,
            source_snapshot_id=version.source_snapshot_id,
            verified_rule_ids_json=_dump([str(value) for value in created_rule_ids]),
            eligibility_criteria_json=version.eligibility_criteria_json,
            required_documents_json=version.required_documents_json,
            costs_json=version.costs_json,
            processing_time_json=version.processing_time_json,
            benefits_json=version.benefits_json,
            risks_json=version.risks_json,
            metadata_json=version.metadata_json,
            effective_from=version.effective_from,
            effective_to=version.effective_to,
            human_review_required=True,
            created_by=f"investment-rule-review:{actor}",
            created_at=now,
            updated_at=now,
        )
        version.lifecycle_status = "superseded"
        version.updated_at = now
        session.add(version)
        session.add(replacement)
        session.flush()
        proposal.created_verified_rule_ids_json = _dump([str(value) for value in created_rule_ids])
        proposal.replacement_pathway_version_id = replacement.id

    session.add(proposal)
    record_audit(
        session,
        action="investment_mobility_rule_proposal_reviewed",
        entity_type="investment_mobility_rule_proposal",
        entity_id=proposal.id,
        before_state={"status": "pending_review"},
        after_state={
            "status": proposal.status,
            "created_verified_rule_ids": created_rule_ids,
            "replacement_pathway_version_id": replacement.id if replacement else None,
        },
        reason=payload.reason,
        actor=actor,
        source="investment_rule_review_v11_9",
    )
    session.commit()
    session.refresh(proposal)
    return proposal

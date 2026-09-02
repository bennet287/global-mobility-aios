"""Harden the bounded CMO/Marketing runtime contract.

Revision ID: 0067_marketing_runtime_contract
Revises: 0066_soc_runtime_contract
Create Date: 2026-08-07
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "0067_marketing_runtime_contract"
down_revision = "0066_soc_runtime_contract"
branch_labels = None
depends_on = None


PROHIBITED_MARKETING_ACTIONS = [
    "authority.submit",
    "client.external_send",
    "contract.sign",
    "deployment.production",
    "infrastructure.mutate",
    "payment.initiate",
    "policy.publish",
    "position.suspend",
    "pricing.change",
    "production.irreversible",
    "secrets.access",
    "vendor.commit",
]


def _contract_json(position_key: str, *, hardened: bool) -> str:
    contract = {
        "audit_required": True,
        "evidence_required": True,
        "may_act_within": "L3" if position_key == "cmo" else "L2",
        "must_escalate_above": "L3" if position_key == "cmo" else "L2",
    }
    if hardened and position_key == "cmo":
        contract.update(
            {
                "capabilities": [
                    "delegate_bounded_marketing_analysis",
                    "synthesize_evidence_complete_marketing_review",
                    "escalate_pricing_policy_and_external_messaging_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_MARKETING_ACTIONS,
                "required_evidence_fields": [
                    "audience_evidence",
                    "brand_guidelines",
                    "budget_constraints",
                    "campaign_plan",
                    "channel_strategy",
                    "creative_assets",
                    "messaging",
                    "risks",
                    "sources",
                    "success_metrics",
                ],
                "required_specialist_positions": ["creative_director", "marketing_manager"],
                "self_approval_allowed": False,
            }
        )
    elif hardened and position_key == "creative_director":
        contract.update(
            {
                "capabilities": [
                    "assess_brand_creative_and_messaging_fit",
                    "assess_audience_and_creative_quality",
                    "raise_creative_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_MARKETING_ACTIONS,
                "required_evidence_fields": [
                    "audience_evidence",
                    "brand_guidelines",
                    "creative_assets",
                    "messaging",
                    "sources",
                ],
                "required_output_fields": [
                    "confidence",
                    "creative_assessment",
                    "dissent",
                    "escalation_required",
                    "evidence_basis",
                    "evidence_gaps",
                    "material_risks",
                    "recommendation",
                ],
                "self_approval_allowed": False,
            }
        )
    elif hardened and position_key == "marketing_manager":
        contract.update(
            {
                "capabilities": [
                    "assess_channel_fit_and_campaign_plan",
                    "assess_growth_metrics_and_dependencies",
                    "raise_marketing_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_MARKETING_ACTIONS,
                "required_evidence_fields": [
                    "budget_constraints",
                    "campaign_plan",
                    "channel_strategy",
                    "risks",
                    "sources",
                    "success_metrics",
                ],
                "required_output_fields": [
                    "confidence",
                    "dissent",
                    "escalation_required",
                    "evidence_basis",
                    "evidence_gaps",
                    "marketing_fit",
                    "material_risks",
                    "recommendation",
                ],
                "self_approval_allowed": False,
            }
        )
    return json.dumps(contract, sort_keys=True)


def _position_exists(position_key: str) -> bool:
    positions = sa.table(
        "organization_positions",
        sa.column("position_key", sa.String()),
        sa.column("version", sa.Integer()),
    )
    row = op.get_bind().execute(
        sa.select(positions.c.position_key).where(
            positions.c.position_key == position_key,
            positions.c.version == 1,
        )
    ).first()
    return row is not None


def _update_cmo_contract() -> None:
    positions = sa.table(
        "organization_positions",
        sa.column("position_key", sa.String()),
        sa.column("contract_json", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("updated_at", sa.DateTime()),
    )
    op.execute(
        positions.update()
        .where(positions.c.position_key == "cmo", positions.c.version == 1)
        .values(
            contract_json=_contract_json("cmo", hardened=True),
            updated_at=datetime.now(timezone.utc),
        )
    )


def _insert_position(position_key: str) -> None:
    title, department, reports_to, authority, role_card = {
        "creative_director": (
            "Creative Director Agent",
            "Marketing",
            "cmo",
            "L2",
            "Creative_Director.md",
        ),
        "marketing_manager": (
            "Marketing Manager Agent",
            "Marketing",
            "cmo",
            "L2",
            "Marketing_Manager.md",
        ),
    }[position_key]
    now = datetime.now(timezone.utc)
    positions = sa.table(
        "organization_positions",
        sa.column("id", sa.Uuid(as_uuid=False)),
        sa.column("position_key", sa.String()),
        sa.column("title", sa.String()),
        sa.column("department", sa.String()),
        sa.column("reports_to_position_key", sa.String()),
        sa.column("authority_level", sa.String()),
        sa.column("role_card_name", sa.String()),
        sa.column("contract_json", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("status", sa.String()),
        sa.column("created_by", sa.String()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    op.execute(
        positions.insert().values(
            id=str(uuid4()),
            position_key=position_key,
            title=title,
            department=department,
            reports_to_position_key=reports_to,
            authority_level=authority,
            role_card_name=role_card,
            contract_json=_contract_json(position_key, hardened=True),
            version=1,
            status="active",
            created_by="system",
            created_at=now,
            updated_at=now,
        )
    )


def upgrade() -> None:
    _update_cmo_contract()
    for position_key in ("creative_director", "marketing_manager"):
        if not _position_exists(position_key):
            _insert_position(position_key)


def downgrade() -> None:
    positions = sa.table(
        "organization_positions",
        sa.column("position_key", sa.String()),
    )
    op.execute(
        positions.delete().where(
            positions.c.position_key.in_(["creative_director", "marketing_manager"])
        )
    )

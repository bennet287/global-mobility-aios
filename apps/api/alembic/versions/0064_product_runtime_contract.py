"""Harden the bounded CPO/Product runtime contract.

Revision ID: 0064_product_runtime_contract
Revises: 0063_cto_runtime_contract
Create Date: 2026-08-03
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "0064_product_runtime_contract"
down_revision = "0063_cto_runtime_contract"
branch_labels = None
depends_on = None


PROHIBITED_PRODUCT_ACTIONS = [
    "authority.submit",
    "client.external_send",
    "contract.sign",
    "deployment.production",
    "infrastructure.mutate",
    "payment.initiate",
    "policy.publish",
    "pricing.change",
    "production.irreversible",
    "secrets.access",
    "vendor.commit",
]


def _contract_json(position_key: str, *, hardened: bool) -> str:
    contract = {
        "audit_required": True,
        "evidence_required": True,
        "may_act_within": "L3" if position_key == "cpo" else "L2",
        "must_escalate_above": "L3" if position_key == "cpo" else "L2",
    }
    if hardened and position_key == "cpo":
        contract.update(
            {
                "capabilities": [
                    "delegate_bounded_product_analysis",
                    "synthesize_evidence_complete_product_review",
                    "escalate_pricing_policy_and_irreversible_product_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_PRODUCT_ACTIONS,
                "required_evidence_fields": [
                    "user_evidence",
                    "market_evidence",
                    "scope",
                    "dependencies",
                    "roadmap_alignment",
                    "success_metrics",
                    "design_principles",
                    "ux_research",
                    "accessibility",
                    "sources",
                    "risks",
                ],
                "required_specialist_positions": ["design_agent", "product_manager"],
                "self_approval_allowed": False,
            }
        )
    elif hardened and position_key == "product_manager":
        contract.update(
            {
                "capabilities": [
                    "assess_product_fit_scope_and_roadmap_alignment",
                    "assess_dependencies_and_success_metrics",
                    "raise_product_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_PRODUCT_ACTIONS,
                "required_evidence_fields": [
                    "user_evidence",
                    "market_evidence",
                    "scope",
                    "dependencies",
                    "roadmap_alignment",
                    "success_metrics",
                    "sources",
                    "risks",
                ],
                "required_output_fields": [
                    "confidence",
                    "dissent",
                    "escalation_required",
                    "evidence_basis",
                    "evidence_gaps",
                    "material_risks",
                    "product_fit",
                    "recommendation",
                ],
                "self_approval_allowed": False,
            }
        )
    elif hardened and position_key == "design_agent":
        contract.update(
            {
                "capabilities": [
                    "assess_design_quality_ux_and_accessibility",
                    "assess_scope_fit_and_dependencies",
                    "raise_design_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_PRODUCT_ACTIONS,
                "required_evidence_fields": [
                    "accessibility",
                    "dependencies",
                    "design_principles",
                    "risks",
                    "scope",
                    "sources",
                    "ux_research",
                ],
                "required_output_fields": [
                    "confidence",
                    "design_assessment",
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
    return json.dumps(contract, sort_keys=True)


def _update_contract(position_key: str, *, before: str, after: str) -> None:
    positions = sa.table(
        "organization_positions",
        sa.column("position_key", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("contract_json", sa.String()),
    )
    op.execute(
        positions.update()
        .where(
            positions.c.position_key == position_key,
            positions.c.version == 1,
            positions.c.contract_json == before,
        )
        .values(contract_json=after)
    )


def upgrade() -> None:
    for position_key in ("cpo", "product_manager", "design_agent"):
        _update_contract(
            position_key,
            before=_contract_json(position_key, hardened=False),
            after=_contract_json(position_key, hardened=True),
        )


def downgrade() -> None:
    for position_key in ("cpo", "product_manager", "design_agent"):
        _update_contract(
            position_key,
            before=_contract_json(position_key, hardened=True),
            after=_contract_json(position_key, hardened=False),
        )

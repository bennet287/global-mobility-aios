"""Harden the bounded CTO runtime contract.

Revision ID: 0063_cto_runtime_contract
Revises: 0062_ceo_coordination_fencing
Create Date: 2026-08-03
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "0063_cto_runtime_contract"
down_revision = "0062_ceo_coordination_fencing"
branch_labels = None
depends_on = None


def _contract_json(position_key: str, *, hardened: bool) -> str:
    contract = {
        "audit_required": True,
        "evidence_required": True,
        "may_act_within": "L3" if position_key == "cto" else "L2",
        "must_escalate_above": "L3" if position_key == "cto" else "L2",
    }
    prohibited_actions = [
        "authority.submit",
        "client.external_send",
        "contract.sign",
        "deployment.production",
        "infrastructure.mutate",
        "payment.initiate",
        "production.irreversible",
        "secrets.access",
        "vendor.commit",
    ]
    if hardened and position_key == "cto":
        contract.update(
            {
                "capabilities": [
                    "delegate_bounded_technology_analysis",
                    "synthesize_evidence_complete_technology_review",
                    "escalate_production_security_and_authority_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": prohibited_actions,
                "required_evidence_fields": [
                    "architecture",
                    "data_handling",
                    "dependencies",
                    "integration",
                    "observability",
                    "reliability",
                    "rollback",
                    "security",
                    "sources",
                    "tests",
                ],
                "required_specialist_positions": ["lead_architect", "vp_engineering"],
                "self_approval_allowed": False,
            }
        )
    elif hardened and position_key == "vp_engineering":
        contract.update(
            {
                "capabilities": [
                    "assess_delivery_readiness",
                    "assess_test_reliability_observability_and_rollback_evidence",
                    "raise_engineering_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": prohibited_actions,
                "required_evidence_fields": [
                    "dependencies",
                    "observability",
                    "reliability",
                    "rollback",
                    "sources",
                    "tests",
                ],
                "required_output_fields": [
                    "confidence",
                    "delivery_readiness",
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
    elif hardened and position_key == "lead_architect":
        contract.update(
            {
                "capabilities": [
                    "assess_architecture_security_data_and_integration_evidence",
                    "assess_reversibility",
                    "raise_architecture_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": prohibited_actions,
                "required_evidence_fields": [
                    "architecture",
                    "data_handling",
                    "integration",
                    "rollback",
                    "security",
                    "sources",
                ],
                "required_output_fields": [
                    "confidence",
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
    duplicate = op.get_bind().execute(
        sa.text(
            "SELECT work_item_id, delegate_position_key, COUNT(*) AS duplicate_count "
            "FROM delegation_records GROUP BY work_item_id, delegate_position_key "
            "HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    if duplicate is not None:
        raise RuntimeError(
            "Cannot enforce delegation uniqueness while duplicate work/delegate rows exist"
        )
    op.create_index(
        "uq_delegation_work_delegate",
        "delegation_records",
        ["work_item_id", "delegate_position_key"],
        unique=True,
    )
    for position_key in ("cto", "vp_engineering", "lead_architect"):
        _update_contract(
            position_key,
            before=_contract_json(position_key, hardened=False),
            after=_contract_json(position_key, hardened=True),
        )


def downgrade() -> None:
    for position_key in ("cto", "vp_engineering", "lead_architect"):
        _update_contract(
            position_key,
            before=_contract_json(position_key, hardened=True),
            after=_contract_json(position_key, hardened=False),
        )
    op.drop_index("uq_delegation_work_delegate", table_name="delegation_records")

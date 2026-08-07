"""Harden the bounded CISO/Security runtime contract.

Revision ID: 0065_security_runtime_contract
Revises: 0064_product_runtime_contract
Create Date: 2026-08-07
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "0065_security_runtime_contract"
down_revision = "0064_product_runtime_contract"
branch_labels = None
depends_on = None


PROHIBITED_SECURITY_ACTIONS = [
    "authority.submit",
    "client.external_send",
    "contract.sign",
    "deployment.production",
    "infrastructure.mutate",
    "payment.initiate",
    "policy.publish",
    "position.suspend",
    "production.irreversible",
    "secrets.access",
    "vendor.commit",
]


def _contract_json(position_key: str, *, hardened: bool) -> str:
    contract = {
        "audit_required": True,
        "evidence_required": True,
        "may_act_within": "L3" if position_key == "ciso" else "L2",
        "must_escalate_above": "L3" if position_key == "ciso" else "L2",
    }
    if hardened and position_key == "ciso":
        contract.update(
            {
                "capabilities": [
                    "delegate_bounded_security_analysis",
                    "synthesize_evidence_complete_security_review",
                    "escalate_security_policy_and_organization_wide_suspension_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_SECURITY_ACTIONS,
                "required_evidence_fields": [
                    "attack_surface",
                    "controls",
                    "impact",
                    "policy_alignment",
                    "provenance",
                    "risks",
                    "signals",
                    "sources",
                    "threat_evidence",
                ],
                "required_specialist_positions": ["security_lead", "threat_analyst"],
                "self_approval_allowed": False,
            }
        )
    elif hardened and position_key == "security_lead":
        contract.update(
            {
                "capabilities": [
                    "assess_security_controls_and_policy_alignment",
                    "assess_attack_surface_and_impact",
                    "raise_security_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_SECURITY_ACTIONS,
                "required_evidence_fields": [
                    "attack_surface",
                    "controls",
                    "impact",
                    "policy_alignment",
                    "risks",
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
                    "security_assessment",
                ],
                "self_approval_allowed": False,
            }
        )
    elif hardened and position_key == "threat_analyst":
        contract.update(
            {
                "capabilities": [
                    "assess_threat_evidence_and_attack_patterns",
                    "detect_prompt_injection_jailbreak_and_compromised_agent_signals",
                    "raise_threat_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_SECURITY_ACTIONS,
                "required_evidence_fields": [
                    "signals",
                    "sources",
                    "threat_evidence",
                ],
                "required_output_fields": [
                    "confidence",
                    "dissent",
                    "escalation_required",
                    "evidence_basis",
                    "evidence_gaps",
                    "material_risks",
                    "recommendation",
                    "threat_assessment",
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


def _insert_position(position_key: str) -> None:
    title, department, reports_to, authority, role_card = {
        "ciso": (
            "Chief Information Security Officer Agent",
            "Security",
            "ceo",
            "L3",
            "CISO.md",
        ),
        "security_lead": (
            "Security Lead Agent",
            "Security",
            "ciso",
            "L2",
            "Security_Lead.md",
        ),
        "threat_analyst": (
            "Threat Analyst Agent",
            "Security",
            "ciso",
            "L2",
            "Threat_Analyst.md",
        ),
    }[position_key]
    now = datetime.now(timezone.utc)
    positions = sa.table(
        "organization_positions",
        sa.column("id", sa.String()),
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
            created_by="migration",
            created_at=now,
            updated_at=now,
        )
    )


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
    for position_key in ("ciso", "security_lead", "threat_analyst"):
        if _position_exists(position_key):
            _update_contract(
                position_key,
                before=_contract_json(position_key, hardened=False),
                after=_contract_json(position_key, hardened=True),
            )
        else:
            _insert_position(position_key)


def downgrade() -> None:
    for position_key in ("ciso", "security_lead", "threat_analyst"):
        if _position_exists(position_key):
            _update_contract(
                position_key,
                before=_contract_json(position_key, hardened=True),
                after=_contract_json(position_key, hardened=False),
            )

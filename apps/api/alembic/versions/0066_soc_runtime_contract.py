"""Harden the bounded SOC runtime contract.

Revision ID: 0066_soc_runtime_contract
Revises: 0065_security_runtime_contract
Create Date: 2026-08-07
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "0066_soc_runtime_contract"
down_revision = "0065_security_runtime_contract"
branch_labels = None
depends_on = None


PROHIBITED_SOC_ACTIONS = [
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
        "may_act_within": "L2",
        "must_escalate_above": "L2",
    }
    if hardened and position_key == "soc_lead":
        contract.update(
            {
                "capabilities": [
                    "monitor_agent_behavior_and_audit_trails",
                    "triage_security_incidents_and_anomalies",
                    "raise_soc_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_SOC_ACTIONS,
                "required_evidence_fields": [
                    "agent_activity",
                    "audit_logs",
                    "incident_history",
                    "monitored_signals",
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
                    "soc_assessment",
                ],
                "self_approval_allowed": False,
            }
        )
    elif hardened and position_key == "soc_analyst":
        contract.update(
            {
                "capabilities": [
                    "analyze_audit_logs_for_anomalies",
                    "detect_compromised_agent_and_prompt_injection_indicators",
                    "raise_soc_dissent_and_material_risk",
                ],
                "delegated_action_authority": ["internal.analysis"],
                "direct_action_authority": [],
                "external_action_authorized": False,
                "prohibited_direct_actions": PROHIBITED_SOC_ACTIONS,
                "required_evidence_fields": [
                    "agent_outputs",
                    "audit_logs",
                    "signals",
                    "sources",
                ],
                "required_output_fields": [
                    "anomaly_assessment",
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
        "soc_lead": (
            "SOC Lead Agent",
            "Security Operations",
            "ciso",
            "L2",
            "SOC_Lead.md",
        ),
        "soc_analyst": (
            "SOC Analyst Agent",
            "Security Operations",
            "ciso",
            "L2",
            "SOC_Analyst.md",
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
            created_by="system",
            created_at=now,
            updated_at=now,
        )
    )


def upgrade() -> None:
    for position_key in ("soc_lead", "soc_analyst"):
        if not _position_exists(position_key):
            _insert_position(position_key)


def downgrade() -> None:
    positions = sa.table(
        "organization_positions",
        sa.column("position_key", sa.String()),
    )
    op.execute(
        positions.delete().where(
            positions.c.position_key.in_(["soc_lead", "soc_analyst"])
        )
    )

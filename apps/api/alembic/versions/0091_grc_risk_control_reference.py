"""Allow a governed risk to own an explicit control or policy reference.

Revision ID: 0091_grc_risk_control_reference
Revises: 0090_reviewed_decision_output
"""

from alembic import op
import sqlalchemy as sa


revision = "0091_grc_risk_control_reference"
down_revision = "0090_reviewed_decision_output"
branch_labels = None
depends_on = None


_OLD_ROLE = "reference_role IN ('authoritative_outcome','affected_subject','evidence','caused_by','supports','contradicts')"
_NEW_ROLE = "reference_role IN ('authoritative_outcome','affected_subject','evidence','caused_by','supports','contradicts','governance_mapping')"
_OLD_TARGET = (
    "target_type IN ('lead','profile','application','corporate_mobility_case','pathway_comparison_assessment',"
    "'eligibility_assessment','source_snapshot','official_source','external_validation_run',"
    "'external_validation_finding','agent_run','automation_event','audit_log','regulatory_change','verified_rule',"
    "'mobility_pathway_version','agency_submission','corporate_compliance_event','mobility_timeline_milestone')"
)
_NEW_TARGET = _OLD_TARGET[:-1] + (
    ",'organization_control','capability_autonomy_promotion_policy',"
    "'capability_autonomy_evidence_evaluation_policy')"
)
_OWNER_PREFIX = (
    "(CASE WHEN activity_id IS NOT NULL THEN 1 ELSE 0 END + "
    "CASE WHEN contribution_id IS NOT NULL THEN 1 ELSE 0 END + "
    "CASE WHEN work_item_id IS NOT NULL THEN 1 ELSE 0 END + "
    "CASE WHEN decision_id IS NOT NULL THEN 1 ELSE 0 END + "
    "CASE WHEN blocker_id IS NOT NULL THEN 1 ELSE 0 END + "
    "CASE WHEN human_action_request_id IS NOT NULL THEN 1 ELSE 0 END + "
    "CASE WHEN human_action_id IS NOT NULL THEN 1 ELSE 0 END"
)
_OLD_OWNER = _OWNER_PREFIX + ") = 1"
_NEW_OWNER = _OWNER_PREFIX + " + CASE WHEN risk_escalation_id IS NOT NULL THEN 1 ELSE 0 END) = 1"


def upgrade() -> None:
    with op.batch_alter_table("organization_record_references") as batch:
        batch.add_column(sa.Column("risk_escalation_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_org_reference_risk_escalation", "risk_escalations",
            ["risk_escalation_id"], ["id"],
        )
        for name in (
            "ck_org_record_reference_role",
            "ck_org_record_reference_target_type",
            "ck_org_record_reference_one_owner",
        ):
            batch.drop_constraint(name, type_="check")
        batch.create_check_constraint("ck_org_record_reference_role", _NEW_ROLE)
        batch.create_check_constraint("ck_org_record_reference_target_type", _NEW_TARGET)
        batch.create_check_constraint("ck_org_record_reference_one_owner", _NEW_OWNER)
        batch.create_index("ix_organization_record_references_risk_escalation_id", ["risk_escalation_id"])


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text(
        "SELECT COUNT(*) FROM organization_record_references WHERE risk_escalation_id IS NOT NULL "
        "OR reference_role = 'governance_mapping' "
        "OR target_type IN ('organization_control','capability_autonomy_promotion_policy',"
        "'capability_autonomy_evidence_evaluation_policy')"
    )).scalar_one():
        raise RuntimeError("Cannot discard governed risk-control mappings")
    with op.batch_alter_table("organization_record_references") as batch:
        batch.drop_index("ix_organization_record_references_risk_escalation_id")
        for name in (
            "ck_org_record_reference_role",
            "ck_org_record_reference_target_type",
            "ck_org_record_reference_one_owner",
        ):
            batch.drop_constraint(name, type_="check")
        batch.create_check_constraint("ck_org_record_reference_role", _OLD_ROLE)
        batch.create_check_constraint("ck_org_record_reference_target_type", _OLD_TARGET)
        batch.create_check_constraint("ck_org_record_reference_one_owner", _OLD_OWNER)
        batch.drop_constraint("fk_org_reference_risk_escalation", type_="foreignkey")
        batch.drop_column("risk_escalation_id")

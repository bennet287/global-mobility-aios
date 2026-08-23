from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    AuditLog,
    BoardPacket,
    DelegationRecord,
    ExecutiveCouncilConsultation,
    ExecutiveDecision,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationPosition,
    OrganizationalWorkItem,
    RiskEscalation,
)
from app.services import organization_governance as organization_service
from app.services.external_action_gates import assert_registered_executor
from app.services.organization_governance import classify_authority
from app.tasks.organization_tasks import (
    execute_organization_work_item_task,
    scan_ceo_decisions_task,
    scan_organization_work_task,
)


def _headers(role: str = "admin", user: str = "human-owner") -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _account(client) -> dict:
    response = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": "Phase 13 Employer", "primary_country": "Austria"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _case(client, account_id: str) -> dict:
    response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account_id}/cases",
        json={"case_reference": "ORG-CASE-001", "destination_country": "Germany"},
    )
    assert response.status_code == 201, response.text
    return response.json()


OPERATIONS_CASE_DELEGATES = {
    "sales_summary",
    "operations_coordination",
    "business_intelligence",
    "application_readiness",
}
TECHNOLOGY_DELEGATES = {"vp_engineering", "lead_architect"}
PRODUCT_DELEGATES = {"product_manager", "design_agent"}
SECURITY_DELEGATES = {"security_lead", "threat_analyst"}
SECURITY_OPERATIONS_DELEGATES = {"soc_lead", "soc_analyst"}
MARKETING_DELEGATES = {"creative_director", "marketing_manager"}
FINANCE_DELEGATES = {"financial_analyst", "accounting_lead"}
COMMUNICATIONS_DELEGATES = {"pr_comms_lead", "government_relations_lead"}
PEOPLE_DELEGATES = {"hr_lead", "culture_recruitment_lead"}
LEGAL_DELEGATES = {"general_counsel", "public_policy_compliance_lead"}


def _technology_context() -> dict:
    return {
        "technology_review_type": "delivery_readiness",
        "facts": {
            "change_scope": "internal platform readiness review",
            "dependencies": ["API test suite", "migration validation"],
        },
        "evidence": {
            "architecture": ["architecture-decision-record:phase-13"],
            "data_handling": ["data-classification:internal"],
            "integration": ["integration-contract:organization-api"],
            "tests": ["quality-gate:447-passing"],
            "reliability": ["reliability-review:bounded-runtime"],
            "security": ["external-actions:fail-closed"],
            "rollback": "Revert the internal configuration and replay the bounded review.",
            "observability": ["audit-ledger", "execution-attempt-ledger"],
            "sources": ["repository:apps/api", "repository:docs/ROADMAP.md"],
        },
    }


def _product_context() -> dict:
    return {
        "product_review_type": "feature_scope",
        "facts": {
            "change_scope": "internal product readiness review",
            "dependencies": ["roadmap-alignment", "design-review"],
        },
        "evidence": {
            "user_evidence": ["user-interview:3", "feedback-ticket:12"],
            "market_evidence": ["market-note:competitor-comparison"],
            "scope": ["feature-scope:bounded-product-runtime"],
            "dependencies": ["controlled-agents", "role-cards"],
            "roadmap_alignment": ["roadmap:phase-13-product"],
            "success_metrics": ["metric:adoption", "metric:confidence"],
            "design_principles": ["design-system:accessibility-first"],
            "ux_research": ["ux-study:operator-workflow"],
            "accessibility": ["wcag:2.1-aa-checklist"],
            "sources": ["repository:agents/role_cards", "repository:docs/ROADMAP.md"],
            "risks": ["risk:evidence-gaps-must-be-recorded"],
        },
    }


def _security_context() -> dict:
    return {
        "security_review_type": "threat_and_controls_review",
        "facts": {
            "change_scope": "internal security posture review",
            "dependencies": ["security-lead", "threat-analyst"],
        },
        "evidence": {
            "attack_surface": ["surface:api-gateway", "surface:agent-context"],
            "controls": ["control:input-validation", "control:output-review"],
            "impact": ["impact:client-data-exposure"],
            "policy_alignment": ["policy:ai-organization-v13"],
            "provenance": ["audit:controlled-agent-runs"],
            "risks": ["risk:prompt-injection", "risk:compromised-agent"],
            "signals": ["signal:anomalous-delegation-request"],
            "sources": ["repository:agents/role_cards", "repository:docs/ROADMAP.md"],
            "threat_evidence": ["threat:prompt-injection-attempt"],
        },
    }


def _security_operations_context() -> dict:
    return {
        "soc_review_type": "agent_behavior_and_audit_review",
        "facts": {
            "change_scope": "internal SOC posture review",
            "dependencies": ["soc-lead", "soc-analyst"],
        },
        "evidence": {
            "agent_activity": ["activity:agent-run-count", "activity:delegation-count"],
            "agent_outputs": ["output:client-drafting-agent", "output:eligibility-agent"],
            "audit_logs": ["audit:controlled-agent-runs", "audit:position-suspension"],
            "incident_history": ["incident:none-recent"],
            "monitored_signals": ["signal:anomalous-delegation-request"],
            "signals": ["signal:repeated-failed-login"],
            "sources": ["repository:audit-logs", "repository:agent-runs"],
        },
    }


def _marketing_context() -> dict:
    return {
        "marketing_review_type": "brand_and_campaign_readiness",
        "facts": {
            "change_scope": "internal marketing readiness review",
            "dependencies": ["creative_director", "marketing_manager"],
        },
        "evidence": {
            "audience_evidence": ["audience:founders", "audience:enterprise"],
            "brand_guidelines": ["brand:voice-and-tone-v3"],
            "budget_constraints": ["budget:annual-marketing-allocation"],
            "campaign_plan": ["campaign:q3-launch-outline"],
            "channel_strategy": ["channel:linkedin", "channel:webinars"],
            "creative_assets": ["asset:hero-creative-v2"],
            "messaging": ["messaging:value-proposition-v4"],
            "risks": ["risk:brand-approval-pending"],
            "sources": ["repository:agents/role_cards", "repository:docs/ROADMAP.md"],
            "success_metrics": ["metric:lead-quality", "metric:brand-awareness"],
        },
    }


def _finance_context() -> dict:
    return {
        "finance_review_type": "financial_and_accounting_readiness",
        "facts": {
            "change_scope": "internal finance readiness review",
            "dependencies": ["financial_analyst", "accounting_lead"],
        },
        "evidence": {
            "ap_ar_aging": ["ap_ar:current-quarter-aging"],
            "audit_trail": ["audit:reconciliation-q3"],
            "budget_constraints": ["budget:annual-operating-plan"],
            "chart_of_accounts": ["coa:phase-13-accounts"],
            "compliance_controls": ["control:segregation-of-duties"],
            "cost_structure": ["cost:cac-breakdown", "cost:operating-expenses"],
            "pricing_model": ["pricing:fee-schedule-v2"],
            "reconciliation": ["reconciliation:month-end-q3"],
            "revenue_model": ["revenue:service-fees", "revenue:consulting-fees"],
            "risks": ["risk:fx-exposure", "risk:runway-sensitivity"],
            "scenario_parameters": ["scenario:base-case", "scenario:stress-case"],
            "sources": ["repository:agents/role_cards", "repository:docs/ROADMAP.md"],
            "tax_treaty_implications": ["tax:treaty-withholding-analysis"],
        },
    }


def _communications_context() -> dict:
    return {
        "communications_review_type": "messaging_and_government_relations_readiness",
        "facts": {
            "change_scope": "internal communications readiness review",
            "dependencies": ["pr_comms_lead", "government_relations_lead"],
        },
        "evidence": {
            "brand_guidelines": ["brand:guidelines-v2"],
            "channel_strategy": ["channel:owned-media", "channel:earned-media"],
            "crisis_scenarios": ["crisis:reputational-risk-playbook"],
            "engagement_plan": ["engagement:regulatory-liaison-plan"],
            "government_stakeholder_map": ["stakeholder:regulators", "stakeholder:legislators"],
            "jurisdiction_scope": ["jurisdiction:AT", "jurisdiction:DE"],
            "legislative_timeline": ["timeline:upcoming-immigration-bill"],
            "media_plan": ["media:pr-plan-q4"],
            "messaging": ["messaging:key-narrative-v1"],
            "policy_landscape": ["policy:skilled-migration-policy"],
            "regulatory_agenda": ["regulatory:labour-market-authority"],
            "risks": ["risk:misalignment-with-regulatory-position"],
            "sources": ["repository:agents/role_cards", "repository:docs/ROADMAP.md"],
            "stakeholder_map": ["stakeholder:clients", "stakeholder:media"],
        },
    }


def _people_context() -> dict:
    return {
        "people_review_type": "workforce_and_culture_readiness",
        "facts": {
            "change_scope": "internal people readiness review",
            "dependencies": ["hr_lead", "culture_recruitment_lead"],
        },
        "evidence": {
            "brand_guidelines": ["brand:guidelines-v2"],
            "compensation_framework": ["compensation:framework-2026"],
            "compliance_requirements": ["compliance:gdpr", "compliance:labour-law"],
            "culture_metrics": ["culture:engagement-score", "culture:values-alignment"],
            "diversity_inclusion_plan": ["di:target-2026"],
            "employee_feedback": ["feedback:pulse-q2"],
            "employer_value_proposition": ["evp:global-mobility-aios"],
            "headcount_forecast": ["headcount:plan-2026"],
            "onboarding_plan": ["onboarding:90-day-program"],
            "org_design": ["org:phase-13-structure"],
            "performance_data": ["performance:review-cycle"],
            "recruitment_plan": ["recruitment:engineer-pipeline"],
            "retention_data": ["retention:voluntary-turnover"],
            "risks": ["risk:skills-gap-in-ai-operations"],
            "sources": ["repository:agents/role_cards", "repository:docs/ROADMAP.md"],
            "talent_pipeline": ["talent:shortlist-visa-specialists"],
            "training_plan": ["training:compliance-2026"],
            "workforce_plan": ["workforce:plan-2026"],
        },
    }


def _legal_context() -> dict:
    return {
        "legal_review_type": "legal_and_compliance_readiness",
        "facts": {
            "change_scope": "internal legal and compliance readiness review",
            "dependencies": ["general_counsel", "public_policy_compliance_lead"],
        },
        "evidence": {
            "audit_findings": ["audit:contract-review-q3"],
            "compliance_framework": ["compliance:gdpr", "compliance:immigration-advice"],
            "contract_portfolio": ["contract:client-terms-v3", "contract:vendor-dpa"],
            "corporate_governance": ["governance:board-charter"],
            "ethics_integrity_controls": ["ethics:conflict-of-interest-policy"],
            "government_relations_context": ["gov_relations:regulatory-liaison-plan"],
            "jurisdiction_scope": ["jurisdiction:AT", "jurisdiction:DE"],
            "legal_exposure": ["exposure:client-liability-assessment"],
            "litigation_disputes": ["litigation:none-active"],
            "policy_landscape": ["policy:skilled-migration-policy"],
            "regulatory_interpretation": ["regulatory:labour-market-authority-guidance"],
            "regulatory_change_register": ["regulatory_change:q4-2026-watchlist"],
            "risks": ["risk:unqualified-immigration-advice"],
            "sources": ["repository:agents/role_cards", "repository:docs/ROADMAP.md"],
            "training_records": ["training:compliance-certification-2026"],
        },
    }


def _high_risk_security_operations_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material SOC review",
            "objective": "Coordinate evidence-backed internal Security Operations analysis within the CEO mandate.",
            "department": "Security Operations",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _security_operations_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_operations_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material operating remediation",
            "objective": "Coordinate an evidence-backed internal remediation within the CEO mandate.",
            "department": "Operations",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": {"scope": "internal", "external_action_authorized": False},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = raw_client.get("/api/v1/organization/decisions")
    assert decision.status_code == 200, decision.text
    matching = [item for item in decision.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_technology_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material technology readiness review",
            "objective": "Coordinate evidence-backed internal Technology analysis within the CEO mandate.",
            "department": "Technology",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _technology_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_product_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material product readiness review",
            "objective": "Coordinate evidence-backed internal Product analysis within the CEO mandate.",
            "department": "Product",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _product_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_security_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material security posture review",
            "objective": "Coordinate evidence-backed internal Security analysis within the CEO mandate.",
            "department": "Security",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _security_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_marketing_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material marketing readiness review",
            "objective": "Coordinate evidence-backed internal Marketing analysis within the CEO mandate.",
            "department": "Marketing",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _marketing_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_finance_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material finance readiness review",
            "objective": "Coordinate evidence-backed internal Finance analysis within the CEO mandate.",
            "department": "Finance",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _finance_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_communications_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material communications readiness review",
            "objective": "Coordinate evidence-backed internal Communications analysis within the CEO mandate.",
            "department": "Communications",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _communications_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_people_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material people readiness review",
            "objective": "Coordinate evidence-backed internal People analysis within the CEO mandate.",
            "department": "People",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _people_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def _high_risk_legal_work(raw_client, *, key: str) -> tuple[UUID, UUID]:
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": key,
            "title": "Material legal readiness review",
            "objective": "Coordinate evidence-backed internal Legal analysis within the CEO mandate.",
            "department": "Legal",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": _legal_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decisions = raw_client.get("/api/v1/organization/decisions")
    assert decisions.status_code == 200, decisions.text
    matching = [item for item in decisions.json() if item["work_item_id"] == str(work_id)]
    assert len(matching) == 1
    return work_id, UUID(matching[0]["id"])


def test_foundation_bootstrap_registers_executable_hierarchy(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    response = raw_client.post("/api/v1/organization/bootstrap")
    assert response.status_code == 201, response.text
    assert response.json()["positions_registered"] == 61

    positions = db_session.exec(select(OrganizationPosition)).all()
    by_key = {item.position_key: item for item in positions}
    assert by_key["ceo"].reports_to_position_key == "board"
    assert by_key["coo"].reports_to_position_key == "ceo"
    assert by_key["cto"].reports_to_position_key == "ceo"
    assert by_key["ciso"].reports_to_position_key == "ceo"
    assert by_key["cpo"].reports_to_position_key == "ceo"
    assert by_key["cmo"].reports_to_position_key == "ceo"
    assert by_key["cfo"].reports_to_position_key == "ceo"
    assert by_key["cco"].reports_to_position_key == "ceo"
    assert by_key["cco"].authority_level == "L3"
    assert by_key["cfo"].authority_level == "L3"
    assert by_key["vp_engineering"].reports_to_position_key == "cto"
    assert by_key["vp_engineering"].authority_level == "L2"
    assert by_key["lead_architect"].reports_to_position_key == "cto"
    assert by_key["lead_architect"].authority_level == "L2"
    assert by_key["lead_software_engineer"].reports_to_position_key == "vp_engineering"
    assert by_key["lead_software_engineer"].department == "Application Engineering"
    assert by_key["backend_api_engineer"].reports_to_position_key == "lead_software_engineer"
    assert by_key["frontend_product_engineer"].reports_to_position_key == "lead_software_engineer"
    assert by_key["platform_engineer"].reports_to_position_key == "vp_engineering"
    assert by_key["site_reliability_engineer"].reports_to_position_key == "platform_engineer"
    assert by_key["qa_automation_engineer"].reports_to_position_key == "vp_engineering"
    assert by_key["data_engineer"].reports_to_position_key == "vp_engineering"
    assert by_key["ai_ml_platform_engineer"].reports_to_position_key == "vp_engineering"
    assert by_key["developer_experience_engineer"].reports_to_position_key == "lead_architect"
    assert by_key["security_lead"].reports_to_position_key == "ciso"
    assert by_key["security_lead"].authority_level == "L2"
    assert by_key["threat_analyst"].reports_to_position_key == "ciso"
    assert by_key["threat_analyst"].authority_level == "L2"
    assert by_key["soc_lead"].reports_to_position_key == "ciso"
    assert by_key["soc_lead"].authority_level == "L2"
    assert by_key["soc_analyst"].reports_to_position_key == "ciso"
    assert by_key["soc_analyst"].authority_level == "L2"
    assert by_key["application_security_engineer"].reports_to_position_key == "security_lead"
    assert by_key["iam_engineer"].reports_to_position_key == "security_lead"
    assert by_key["security_grc_lead"].reports_to_position_key == "ciso"
    assert by_key["security_grc_lead"].authority_level == "L2"
    assert by_key["vulnerability_management_engineer"].reports_to_position_key == "security_lead"
    assert by_key["product_manager"].reports_to_position_key == "cpo"
    assert by_key["product_manager"].authority_level == "L2"
    assert by_key["design_agent"].reports_to_position_key == "cpo"
    assert by_key["design_agent"].authority_level == "L2"
    assert by_key["creative_director"].reports_to_position_key == "cmo"
    assert by_key["creative_director"].authority_level == "L2"
    assert by_key["marketing_manager"].reports_to_position_key == "cmo"
    assert by_key["marketing_manager"].authority_level == "L2"
    assert by_key["financial_analyst"].reports_to_position_key == "cfo"
    assert by_key["financial_analyst"].authority_level == "L2"
    assert by_key["accounting_lead"].reports_to_position_key == "cfo"
    assert by_key["accounting_lead"].authority_level == "L2"
    assert by_key["pr_comms_lead"].reports_to_position_key == "cco"
    assert by_key["pr_comms_lead"].authority_level == "L2"
    assert by_key["government_relations_lead"].reports_to_position_key == "cco"
    assert by_key["government_relations_lead"].authority_level == "L2"
    assert by_key["chro"].reports_to_position_key == "ceo"
    assert by_key["chro"].authority_level == "L3"
    assert by_key["hr_lead"].reports_to_position_key == "chro"
    assert by_key["hr_lead"].authority_level == "L2"
    assert by_key["culture_recruitment_lead"].reports_to_position_key == "chro"
    assert by_key["culture_recruitment_lead"].authority_level == "L2"
    assert by_key["sales_summary"].reports_to_position_key == "coo"
    assert by_key["operations_coordination"].reports_to_position_key == "coo"
    assert by_key["business_intelligence"].reports_to_position_key == "coo"
    assert by_key["mobility_operations_lead"].reports_to_position_key == "coo"
    assert by_key["mobility_operations_lead"].department == "Global Mobility Operations"
    assert by_key["case_operations_specialist"].reports_to_position_key == "mobility_operations_lead"
    assert by_key["pathway_operations_specialist"].reports_to_position_key == "mobility_operations_lead"
    assert by_key["document_evidence_operations_lead"].reports_to_position_key == "coo"
    assert by_key["evidence_quality_specialist"].reports_to_position_key == "document_evidence_operations_lead"
    assert by_key["authority_filing_operations_lead"].reports_to_position_key == "coo"
    assert by_key["submission_readiness_specialist"].reports_to_position_key == "authority_filing_operations_lead"
    assert by_key["jurisdiction_research_lead"].reports_to_position_key == "coo"
    assert by_key["regulatory_intelligence_analyst"].reports_to_position_key == "jurisdiction_research_lead"
    assert by_key["evidence_source_certification_lead"].reports_to_position_key == "coo"
    assert by_key["mobility_intelligence_analyst"].reports_to_position_key == "jurisdiction_research_lead"
    assert by_key["immigration_regulatory_counsel"].reports_to_position_key == "clo"
    assert by_key["privacy_data_protection_counsel"].reports_to_position_key == "clo"
    assert by_key["regulatory_assurance_counsel"].reports_to_position_key == "clo"
    assert by_key["board"].authority_level == "L4"
    ceo_contract = json.loads(by_key["ceo"].contract_json)
    assert ceo_contract["external_action_authorized"] is False
    assert ceo_contract["direct_action_authority"] == []
    assert ceo_contract["self_approval_allowed"] is False
    cto_contract = json.loads(by_key["cto"].contract_json)
    assert cto_contract["delegated_action_authority"] == ["internal.analysis"]
    assert cto_contract["direct_action_authority"] == []
    assert cto_contract["external_action_authorized"] is False
    assert set(cto_contract["required_specialist_positions"]) == TECHNOLOGY_DELEGATES
    assert "deployment.production" in cto_contract["prohibited_direct_actions"]
    cpo_contract = json.loads(by_key["cpo"].contract_json)
    assert cpo_contract["delegated_action_authority"] == ["internal.analysis"]
    assert cpo_contract["direct_action_authority"] == []
    assert cpo_contract["external_action_authorized"] is False
    assert set(cpo_contract["required_specialist_positions"]) == PRODUCT_DELEGATES
    assert "policy.publish" in cpo_contract["prohibited_direct_actions"]
    ciso_contract = json.loads(by_key["ciso"].contract_json)
    assert ciso_contract["delegated_action_authority"] == ["internal.analysis"]
    assert ciso_contract["direct_action_authority"] == []
    assert ciso_contract["external_action_authorized"] is False
    assert set(ciso_contract["required_specialist_positions"]) == SECURITY_DELEGATES
    assert "position.suspend" in ciso_contract["prohibited_direct_actions"]
    assert "policy.publish" in ciso_contract["prohibited_direct_actions"]
    cmo_contract = json.loads(by_key["cmo"].contract_json)
    assert cmo_contract["delegated_action_authority"] == ["internal.analysis"]
    assert cmo_contract["direct_action_authority"] == []
    assert cmo_contract["external_action_authorized"] is False
    assert set(cmo_contract["required_specialist_positions"]) == MARKETING_DELEGATES
    assert "policy.publish" in cmo_contract["prohibited_direct_actions"]
    assert "pricing.change" in cmo_contract["prohibited_direct_actions"]
    cfo_contract = json.loads(by_key["cfo"].contract_json)
    assert cfo_contract["delegated_action_authority"] == ["internal.analysis"]
    assert cfo_contract["direct_action_authority"] == []
    assert cfo_contract["external_action_authorized"] is False
    assert set(cfo_contract["required_specialist_positions"]) == FINANCE_DELEGATES
    assert "payment.initiate" in cfo_contract["prohibited_direct_actions"]
    assert "pricing.change" in cfo_contract["prohibited_direct_actions"]
    assert "spend.above_threshold" in cfo_contract["prohibited_direct_actions"]
    cco_contract = json.loads(by_key["cco"].contract_json)
    assert cco_contract["delegated_action_authority"] == ["internal.analysis"]
    assert cco_contract["direct_action_authority"] == []
    assert cco_contract["external_action_authorized"] is False
    assert set(cco_contract["required_specialist_positions"]) == COMMUNICATIONS_DELEGATES
    assert "policy.publish" in cco_contract["prohibited_direct_actions"]
    assert "spend.above_threshold" in cco_contract["prohibited_direct_actions"]
    chro_contract = json.loads(by_key["chro"].contract_json)
    assert chro_contract["delegated_action_authority"] == ["internal.analysis"]
    assert chro_contract["direct_action_authority"] == []
    assert chro_contract["external_action_authorized"] is False
    assert set(chro_contract["required_specialist_positions"]) == PEOPLE_DELEGATES
    assert "hiring.decision" in chro_contract["prohibited_direct_actions"]
    assert "compensation.change" in chro_contract["prohibited_direct_actions"]
    assert "termination.action" in chro_contract["prohibited_direct_actions"]
    assert by_key["clo"].reports_to_position_key == "ceo"
    assert by_key["clo"].authority_level == "L3"
    assert by_key["general_counsel"].reports_to_position_key == "clo"
    assert by_key["general_counsel"].authority_level == "L2"
    assert by_key["public_policy_compliance_lead"].reports_to_position_key == "clo"
    assert by_key["public_policy_compliance_lead"].authority_level == "L2"
    clo_contract = json.loads(by_key["clo"].contract_json)
    assert clo_contract["delegated_action_authority"] == ["internal.analysis"]
    assert clo_contract["direct_action_authority"] == []
    assert clo_contract["external_action_authorized"] is False
    assert set(clo_contract["required_specialist_positions"]) == LEGAL_DELEGATES
    assert "contract.sign" in clo_contract["prohibited_direct_actions"]
    assert "authority.submit" in clo_contract["prohibited_direct_actions"]
    assert "legal.opinion.final" in clo_contract["prohibited_direct_actions"]
    assert "compliance.certify" in clo_contract["prohibited_direct_actions"]

    cards = Path(__file__).parents[3] / "agents" / "role_cards"
    for card in (
        "CEO.md",
        "CTO.md",
        "VP_Engineering.md",
        "Lead_Architect.md",
        "CISO.md",
        "Security_Lead.md",
        "Threat_Analyst.md",
        "CPO.md",
        "Product_Manager.md",
        "Design_Agent.md",
        "COO.md",
        "CMO.md",
        "CFO.md",
        "CCO.md",
        "CHRO.md",
        "CLO.md",
        "General_Counsel.md",
        "Public_Policy_Compliance_Lead.md",
        "Creative_Director.md",
        "Marketing_Manager.md",
        "Financial_Analyst.md",
        "Accounting_Lead.md",
        "PR_Comms_Lead.md",
        "Government_Relations_Lead.md",
        "HR_Lead.md",
        "Culture_Recruitment_Lead.md",
    ):
        assert (cards / card).is_file()


def test_authority_classifier_fails_closed_for_reserved_and_material_actions() -> None:
    assert classify_authority("internal.analysis") == ("L1", "routine")
    assert classify_authority("internal.analysis", {"risk_level": "moderate"}) == ("L2", "moderate")
    assert classify_authority("client.external_send") == ("L3", "high")
    assert classify_authority("authority.submit") == ("L3", "high")
    assert classify_authority("payment.initiate") == ("L3", "high")
    assert classify_authority("deployment.production") == ("L3", "high")
    assert classify_authority("  Deployment.Production  ") == ("L3", "high")
    assert classify_authority("infrastructure.mutate") == ("L3", "high")
    assert classify_authority("secrets.access") == ("L3", "high")
    assert classify_authority("contract.sign") == ("L4", "critical")
    assert classify_authority("market.entry") == ("L4", "critical")
    assert classify_authority("  Vendor.Commit  ") == ("L4", "critical")
    assert classify_authority("anything", {"requires_board_approval": True}) == ("L4", "critical")


def test_external_action_gate_registry_is_complete_and_fails_closed(raw_client) -> None:
    raw_client.headers.update(_headers())
    response = raw_client.get("/api/v1/organization/action-gates")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "fail_closed"
    actions = payload["actions"]
    assert set(actions) == {
        "client.external_send",
        "authority.submit",
        "payment.initiate",
        "contract.sign",
        "deployment.production",
    }
    assert all(policy["fail_closed"] for policy in actions.values())
    assert actions["client.external_send"]["executable"] is True
    assert actions["authority.submit"]["executable"] is True
    for action in ("payment.initiate", "contract.sign", "deployment.production"):
        assert actions[action]["executable"] is False
        with pytest.raises(ValueError, match="no registered executor"):
            assert_registered_executor(action)
    with pytest.raises(ValueError, match="Unknown governed action"):
        assert_registered_executor("external.unregistered")


def test_direct_reserved_work_also_creates_board_decision(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "direct-market-entry-001",
        "title": "Evaluate a new market entry",
        "objective": "Prepare the evidence and options for a human Board decision.",
        "department": "Executive",
        "action": "market.entry",
        "context": {"market": "example"},
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).one()
    assert decision.status == "pending_board"
    assert decision.decision_owner_position == "board"


def test_domain_event_routes_delegated_work_and_executes_routine_lane(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    account = _account(raw_client)
    case = _case(raw_client, account["id"])

    work = db_session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"]))
    ).first()
    assert work is not None
    assert work.authority_level == "L1"
    assert work.status == "queued"
    delegations = db_session.exec(select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)).all()
    assert {item.delegate_position_key for item in delegations} == OPERATIONS_CASE_DELEGATES

    executed = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    governance = output["governance"]
    assert governance["accountable_position_key"] == "coo"
    assert governance["authority_level"] == "L1"
    assert 0.0 < governance["confidence"] <= 1.0
    assert len(governance["organizational_action_output_ids"]) == 4
    assert "no external action" in governance["rollback_posture"].lower()
    assert governance["execution_attempt"] == 1
    assert governance["execution_token"]

    ledger = raw_client.get(f"/api/v1/organization/work-items/{work.id}/outputs")
    assert ledger.status_code == 200, ledger.text
    assert len(ledger.json()) == 4
    persisted = db_session.exec(
        select(OrganizationalActionOutput).where(OrganizationalActionOutput.work_item_id == work.id)
    ).all()
    assert len(persisted) == 4
    for action_output in persisted:
        assert action_output.accountable_position_key == "coo"
        assert action_output.authority_basis
        assert 0.0 < action_output.confidence <= 1.0
        assert action_output.confidence_basis
        assert json.loads(action_output.evidence_json)
        assert json.loads(action_output.impact_json)["client_facing"] is False
        assert "no external side effect" in action_output.rollback_posture.lower()

    repeated = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert repeated.status_code == 409
    db_session.expire_all()
    assert len(db_session.exec(
        select(OrganizationalActionOutput).where(OrganizationalActionOutput.work_item_id == work.id)
    ).all()) == 4
    attempts = db_session.exec(
        select(OrganizationExecutionAttempt).where(OrganizationExecutionAttempt.work_item_id == work.id)
    ).all()
    assert len(attempts) == 1
    assert attempts[0].status == "completed"


def test_board_can_cancel_queued_work_and_replay_is_blocked(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "cancel-queued-work-001",
        "title": "Prepare cancellable internal analysis",
        "objective": "Verify that the Human Board can stop queued organizational work.",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = created.json()["id"]

    raw_client.headers.update(_headers("operator", "operations-user"))
    forbidden = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/cancel",
        json={"reason": "Operator requested cancellation without Board authority."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers())
    cancelled = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/cancel",
        json={"reason": "Human owner stopped this work before execution began."},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancelled_by"] == "human-owner"
    assert cancelled.json()["cancel_requested_at"]
    assert cancelled.json()["cancelled_at"]

    replay = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert replay.status_code == 409
    attempts = raw_client.get(f"/api/v1/organization/work-items/{work_id}/attempts")
    assert attempts.status_code == 200
    assert attempts.json() == []

    audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_id == work_id,
            AuditLog.action == "organization_work_cancelled",
        )
    ).one()
    assert audit.actor == "human-owner"


def test_failed_execution_is_bounded_and_retries_without_replaying_completed_work(
    raw_client,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_client.headers.update(_headers())
    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    work = db_session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"])
        )
    ).one()
    work.max_execution_attempts = 2
    db_session.add(work)
    db_session.commit()

    original_record = organization_service._record_action_output
    calls = 0

    def fail_on_second_output(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated bounded worker failure")
        return original_record(*args, **kwargs)

    monkeypatch.setattr(organization_service, "_record_action_output", fail_on_second_output)
    with pytest.raises(RuntimeError, match="simulated bounded worker failure"):
        organization_service.execute_work_item(db_session, work, actor="test-worker")

    db_session.expire_all()
    failed = db_session.get(OrganizationalWorkItem, work.id)
    assert failed is not None
    assert failed.status == "retry_wait"
    assert failed.execution_attempts == 1
    assert failed.next_retry_at is not None
    assert "simulated bounded worker failure" in (failed.last_error or "")
    first_attempt = db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.work_item_id == work.id
        )
    ).one()
    assert first_attempt.status == "failed"

    completed_before_retry = db_session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == work.id,
            DelegationRecord.status == "completed",
        )
    ).all()
    assert len(completed_before_retry) == 2
    completed_outputs_before_retry = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work.id
        )
    ).all()
    assert len(completed_outputs_before_retry) == 1
    completed_output_id = completed_outputs_before_retry[0].id
    completed_delegation_ids_before_retry = {
        delegation.id for delegation in completed_before_retry
    }
    assert all(
        delegation.result_ref == f"work-item:{work.id}"
        for delegation in completed_before_retry
    )
    assert db_session.exec(select(AgentRun)).all() == []

    early_replay = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert early_replay.status_code == 409
    assert "not due" in early_replay.json()["detail"].lower()

    monkeypatch.setattr(organization_service, "_record_action_output", original_record)
    raw_client.headers.update(_headers("operator", "operations-user"))
    forbidden = raw_client.post(
        f"/api/v1/organization/work-items/{work.id}/retry",
        json={"reason": "Operator attempted to bypass the retry control."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers())
    retried = raw_client.post(
        f"/api/v1/organization/work-items/{work.id}/retry",
        json={"reason": "Human owner approved one bounded retry after reviewing the failure."},
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["status"] == "queued"
    assert retried.json()["execution_attempts"] == 1

    executed = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    assert executed.json()["execution_attempts"] == 2
    attempts = raw_client.get(f"/api/v1/organization/work-items/{work.id}/attempts")
    assert [item["status"] for item in attempts.json()] == ["failed", "completed"]

    completed_delegations_after_retry = db_session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == work.id,
            DelegationRecord.status == "completed",
        )
    ).all()
    assert len(completed_delegations_after_retry) == 4
    assert completed_delegation_ids_before_retry < {
        delegation.id for delegation in completed_delegations_after_retry
    }
    assert db_session.exec(select(AgentRun)).all() == []

    db_session.expire_all()
    completed_output = db_session.get(OrganizationalActionOutput, completed_output_id)
    assert completed_output is not None
    assert json.loads(completed_output.output_json)["note"] != "Previously completed delegation reused during retry."


def test_retry_ceiling_cannot_be_reset_by_board_endpoint(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "retry-ceiling-work-001",
        "title": "Test exhausted work retry",
        "objective": "Confirm that even the Board endpoint cannot silently reset the retry budget.",
        "action": "internal.analysis",
        "max_execution_attempts": 1,
    })
    assert created.status_code == 201, created.text
    work = db_session.get(OrganizationalWorkItem, UUID(created.json()["id"]))
    assert work is not None
    work.status = "failed"
    work.execution_attempts = 1
    work.last_error = "terminal simulated failure"
    db_session.add(work)
    db_session.commit()

    response = raw_client.post(
        f"/api/v1/organization/work-items/{work.id}/retry",
        json={"reason": "Human owner inspected the exhausted retry budget."},
    )
    assert response.status_code == 409
    assert "exhausted" in response.json()["detail"].lower()


def test_work_scanner_dispatches_only_queued_and_due_retries(
    raw_client,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_client.headers.update(_headers())
    work_ids: list[UUID] = []
    for suffix in ("queued", "due", "future"):
        response = raw_client.post("/api/v1/organization/work-items", json={
            "idempotency_key": f"scanner-work-{suffix}-001",
            "title": f"Scanner work {suffix}",
            "objective": "Verify durable retry scheduling selects only eligible organizational work.",
            "action": "internal.analysis",
        })
        assert response.status_code == 201, response.text
        work_ids.append(UUID(response.json()["id"]))

    due = db_session.get(OrganizationalWorkItem, work_ids[1])
    future = db_session.get(OrganizationalWorkItem, work_ids[2])
    assert due is not None and future is not None
    due.status = "retry_wait"
    due.execution_attempts = 1
    due.next_retry_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    future.status = "retry_wait"
    future.execution_attempts = 1
    future.next_retry_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.add(due)
    db_session.add(future)
    db_session.commit()

    dispatched: list[str] = []
    monkeypatch.setattr(
        execute_organization_work_item_task,
        "delay",
        lambda work_id: dispatched.append(work_id),
    )
    result = scan_organization_work_task.run(limit=10)
    assert result["queued"] == 2
    assert set(dispatched) == {str(work_ids[0]), str(work_ids[1])}


def test_missing_work_item_output_ledger_returns_not_found(raw_client) -> None:
    raw_client.headers.update(_headers())
    response = raw_client.get(f"/api/v1/organization/work-items/{UUID(int=0)}/outputs")
    assert response.status_code == 404


def test_l4_event_reaches_human_board_and_records_decision(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    event = raw_client.post(
        "/api/v1/automation/events",
        json={
            "corporate_account_id": account["id"],
            "corporate_mobility_case_id": case["id"],
            "event_type": "case.status_changed",
            "idempotency_key": "phase13-market-entry-event",
            "payload": {"action": "market.entry", "risk_level": "critical"},
        },
    )
    assert event.status_code == 202, event.text
    work = db_session.exec(select(OrganizationalWorkItem).where(OrganizationalWorkItem.idempotency_key == f"organization:event:{event.json()['id']}")).one()
    assert work.authority_level == "L4"
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work.id)).one()
    risk = db_session.exec(select(RiskEscalation).where(RiskEscalation.work_item_id == work.id)).one()
    assert decision.status == "pending_board"
    assert risk.requires_board_attention is True

    packet = raw_client.get("/api/v1/organization/board-packet")
    assert packet.status_code == 200
    assert packet.json()["metrics"]["pending_board"] == 1

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-decision",
        json={"decision": "approved", "reason": "Operator attempted reserved approval."},
    )
    assert forbidden.status_code == 403

    executed = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_board"
    db_session.refresh(decision)
    decision_evidence = json.loads(decision.evidence_json)
    governed_output_evidence = [
        item for item in decision_evidence if item.get("type") == "organizational_action_outputs"
    ]
    assert len(governed_output_evidence) == 1
    assert len(governed_output_evidence[0]["ids"]) == 4
    assert 0.0 < governed_output_evidence[0]["aggregate_confidence"] <= 1.0

    raw_client.headers.update(_headers("admin", "human-owner"))
    approved = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-decision",
        json={"decision": "approved", "reason": "Human owner reviewed the evidence and accepts the exposure."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    assert approved.json()["decided_by"] == "human-owner"


def test_global_pause_holds_and_resume_requeues_work(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    paused = raw_client.post("/api/v1/organization/control", json={"status": "paused", "reason": "Board requested a controlled operating pause."})
    assert paused.status_code == 200, paused.text
    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    work = db_session.exec(select(OrganizationalWorkItem).where(OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"]))).one()
    assert work.status == "held"

    resumed = raw_client.post("/api/v1/organization/control", json={"status": "active", "reason": "Board completed its review and resumed execution."})
    assert resumed.status_code == 200, resumed.text
    db_session.refresh(work)
    assert work.status == "queued"


def test_board_can_override_l3_ceo_decision(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "override-l3-external-send-001",
        "title": "Send client-facing status update",
        "objective": "Communicate a routine case milestone to the client under executive oversight.",
        "department": "Communications",
        "action": "client.external_send",
        "risk_level": "high",
        "context": {"channel": "email", "milestone": "document_received"},
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).one()
    assert decision.authority_level == "L3"
    assert decision.status == "pending_ceo"
    assert decision.decision_owner_position == "ceo"

    board_decision = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-decision",
        json={
            "decision": "approved",
            "reason": "Board must use the explicit override path for an L3 CEO decision.",
        },
    )
    assert board_decision.status_code == 409, board_decision.text
    db_session.refresh(decision)
    assert decision.status == "pending_ceo"
    assert decision.decided_by is None

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-override",
        json={"decision": "approved", "reason": "Operator attempted Board override."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers("admin", "human-owner"))
    overridden = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-override",
        json={"decision": "approved", "reason": "Board overrides CEO lane and accepts the contractual exposure."},
    )
    assert overridden.status_code == 200, overridden.text
    assert overridden.json()["status"] == "approved"
    assert overridden.json()["decided_by"] == "human-owner"

    db_session.refresh(decision)
    audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "executive_decision",
            AuditLog.entity_id == str(decision.id),
            AuditLog.action == "executive_decision_overridden",
        )
    ).one()
    assert audit.actor == "human-owner"


def test_board_override_l4_delegates_to_normal_board_decision(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "override-l4-market-entry-001",
        "title": "Enter a new jurisdiction",
        "objective": "Board must approve market entry.",
        "department": "Executive",
        "action": "market.entry",
        "context": {"jurisdiction": "Singapore"},
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).one()
    assert decision.authority_level == "L4"
    assert decision.status == "pending_board"

    raw_client.headers.update(_headers("admin", "human-owner"))
    overridden = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-override",
        json={"decision": "approved", "reason": "Board approves market entry via override path."},
    )
    assert overridden.status_code == 200, overridden.text
    assert overridden.json()["status"] == "approved"


def test_position_suspend_and_resume(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    raw_client.post("/api/v1/organization/bootstrap")
    position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "sales_summary")
    ).one()

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/positions/{position.id}/suspend",
        json={"reason": "Operator attempted suspension."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers("admin", "human-owner"))
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{position.id}/suspend",
        json={"reason": "Sales intelligence agent paused pending data-quality review."},
    )
    assert suspended.status_code == 200, suspended.text
    assert suspended.json()["status"] == "suspended"
    assert suspended.json()["suspended_by"] == "human-owner"

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{position.id}/resume",
        json={"reason": "Data-quality review completed; agent cleared to operate."},
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["status"] == "active"
    assert resumed.json()["suspended_at"] is None


def test_suspended_position_is_not_delegated_new_work(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    raw_client.post("/api/v1/organization/bootstrap")
    position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "sales_summary")
    ).one()
    raw_client.post(
        f"/api/v1/organization/positions/{position.id}/suspend",
        json={"reason": "Suspend sales intelligence for this test."},
    )

    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    work = db_session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"]))
    ).one()
    delegations = db_session.exec(select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)).all()
    delegate_keys = {item.delegate_position_key for item in delegations}
    assert "sales_summary" not in delegate_keys
    assert "application_readiness" in delegate_keys


def test_suspended_position_holds_existing_delegation_during_execution(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    raw_client.post("/api/v1/organization/bootstrap")
    account = _account(raw_client)
    case = _case(raw_client, account["id"])
    work = db_session.exec(
        select(OrganizationalWorkItem).where(OrganizationalWorkItem.corporate_mobility_case_id == UUID(case["id"]))
    ).one()
    delegations = db_session.exec(select(DelegationRecord).where(DelegationRecord.work_item_id == work.id)).all()
    assert {item.delegate_position_key for item in delegations} == OPERATIONS_CASE_DELEGATES

    position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "sales_summary")
    ).one()
    raw_client.post(
        f"/api/v1/organization/positions/{position.id}/suspend",
        json={"reason": "Suspend sales intelligence after work was already routed."},
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work.id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    delegated_results = {result["agent"]: result for result in output["delegated_results"]}
    assert delegated_results["sales_summary_agent"]["status"] == "held"
    assert delegated_results["application_readiness_agent"]["status"] == "completed"

    db_session.refresh(work)
    held_delegation = db_session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == work.id,
            DelegationRecord.delegate_position_key == "sales_summary",
        )
    ).one()
    assert held_delegation.status == "held"
    assert held_delegation.result_ref == "position:suspended"


def test_direct_operations_objective_is_idempotently_delegated_and_resolved_by_coo(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers())
    payload = {
        "idempotency_key": "operations-objective-001",
        "title": "Review weekly operating health",
        "objective": "Prepare a bounded internal operating review for the COO.",
        "department": "Operations",
        "action": "internal.analysis",
        "context": {"period": "weekly", "scope": "mobility operations"},
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]

    work_id = UUID(first.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == {
        "sales_summary",
        "operations_coordination",
        "business_intelligence",
    }
    assert all(item.delegator_position_key == "coo" for item in delegations)
    assert all("L1 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    assert {item["agent"] for item in output["delegated_results"]} == {
        "sales_summary_agent",
        "operations_coordination_agent",
        "business_intelligence_agent",
    }
    assert output["governance"]["accountable_position_key"] == "coo"
    assert output["governance"]["authority_level"] == "L1"
    assert db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).all() == []


def test_ceo_resolves_evidence_complete_l3_with_coo_consultation(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-coordinate-evidence-complete-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert forbidden.status_code == 403, forbidden.text

    raw_client.headers.update(_headers("admin", "human-owner"))
    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert coordinated.json()["decided_by"] == "ceo-agent"
    assert coordinated.json()["decision_reason"]
    assert coordinated.json()["decided_at"] is not None

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    decision = db_session.get(ExecutiveDecision, decision_id)
    assert work is not None and work.status == "completed"
    assert decision is not None and decision.decision_owner_position == "ceo"
    decision_evidence = json.loads(decision.evidence_json)
    assert any(item.get("type") == "organizational_action_outputs" for item in decision_evidence)
    assert any(item.get("type") == "executive_council_consultations" for item in decision_evidence)

    listed = raw_client.get("/api/v1/organization/executive-consultations")
    assert listed.status_code == 200, listed.text
    consultations = [
        item for item in listed.json() if item["decision_id"] == str(decision_id)
    ]
    assert len(consultations) == 1
    consultation = consultations[0]
    assert consultation["requested_by_position"] == "ceo"
    assert consultation["consulted_position"] == "coo"
    assert consultation["domain"] == "operations"
    assert consultation["status"] == "completed"
    assert consultation["recommendation"]
    assert consultation["confidence"] > 0.0
    assert json.loads(consultation["evidence_json"])

    risk = db_session.exec(
        select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)
    ).one()
    assert risk.escalated_to_position_key == "ceo"
    assert risk.requires_board_attention is False
    snapshot = raw_client.get("/api/v1/organization/board-packet")
    assert snapshot.status_code == 200, snapshot.text
    assert snapshot.json()["metrics"]["pending_ceo"] == 0
    assert snapshot.json()["metrics"]["pending_board"] == 0

    audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "executive_decision",
            AuditLog.entity_id == str(decision_id),
            AuditLog.action == "executive_decision_approved",
        )
    ).one()
    assert audit.actor == "ceo-agent"


def test_ceo_coordination_before_evidence_remains_pending(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-coordinate-before-evidence-001",
    )

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "pending_ceo"
    assert coordinated.json()["decided_by"] is None
    assert coordinated.json()["decided_at"] is None

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    decision = db_session.get(ExecutiveDecision, decision_id)
    assert work is not None and work.status == "queued"
    assert decision is not None and decision.status == "pending_ceo"
    approvals = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "executive_decision",
            AuditLog.entity_id == str(decision_id),
            AuditLog.action == "executive_decision_approved",
        )
    ).all()
    assert approvals == []


def test_ceo_decision_scanner_approves_only_evidence_ready_l3(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    ready_work_id, ready_decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-scanner-ready-001",
    )
    held_work_id, held_decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-scanner-held-001",
    )
    executed = raw_client.post(
        f"/api/v1/organization/work-items/{ready_work_id}/execute"
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"

    result = scan_ceo_decisions_task()
    assert result["examined"] == 2
    assert result["approved"] == [str(ready_decision_id)]
    assert result["held"] == [str(held_decision_id)]
    assert result["escalated"] == []
    assert result["errors"] == []

    db_session.expire_all()
    ready = db_session.get(ExecutiveDecision, ready_decision_id)
    held = db_session.get(ExecutiveDecision, held_decision_id)
    assert ready is not None and ready.status == "approved"
    assert ready.decided_by == "ceo-agent"
    assert held is not None and held.status == "pending_ceo"
    assert held.decided_by is None
    held_work = db_session.get(OrganizationalWorkItem, held_work_id)
    assert held_work is not None and held_work.status == "queued"


def test_still_unimplemented_department_runtime_is_held_without_false_completion(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "legal-runtime-unavailable-001",
            "title": "Review legal positioning",
            "objective": "Exercise a registered department whose action is outside the bounded runtime.",
            "department": "Legal",
            "action": "contract.sign",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "clo"
    assert created.json()["status"] == "held"
    assert "does not execute" in created.json()["last_error"]

    work_id = UUID(created.json()["id"])
    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.work_item_id == work_id
        )
    ).all() == []
    assert db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all() == []


def test_technology_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "technology-internal-analysis-001",
        "title": "Review platform delivery readiness",
        "objective": "Produce a bounded internal technical review from repository evidence.",
        "department": "Technology",
        "action": "internal.analysis",
        "context": _technology_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]
    assert first.json()["status"] == "queued"
    assert first.json()["assigned_position_key"] == "cto"

    work_id = UUID(first.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == TECHNOLOGY_DELEGATES
    assert all(item.delegator_position_key == "cto" for item in delegations)
    assert all("L2 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    assert output["governance"]["accountable_position_key"] == "cto"
    assert output["governance"]["external_action_authorized"] is False
    assert {item["agent"] for item in output["delegated_results"]} == {
        "vp_engineering_agent",
        "lead_architect_agent",
    }
    assert all(item.get("run_id") for item in output["delegated_results"])

    db_session.expire_all()
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert all(item.status == "completed" for item in delegations)
    assert all(item.result_ref and item.result_ref.startswith("agent-run:") for item in delegations)
    action_outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all()
    assert len(action_outputs) == 2
    for action_output in action_outputs:
        assert any(item["type"] == "agent_run" for item in json.loads(action_output.evidence_json))
        assert json.loads(action_output.impact_json)["external_action_authorized"] is False
        specialist_output = json.loads(action_output.output_json)["output"]
        assert specialist_output["deployment_allowed"] is False
        assert specialist_output["external_action_authorized"] is False
    assert len(db_session.exec(select(AgentRun)).all()) == 2

    replay = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert replay.status_code == 409, replay.text
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2
    assert len(db_session.exec(select(AgentRun)).all()) == 2


def test_incomplete_technology_evidence_holds_the_whole_work_item(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "technology-evidence-incomplete-001",
            "title": "Review an undocumented platform change",
            "objective": "Expose missing technical evidence without approving the change.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


def test_suspended_required_technology_specialist_holds_then_resumes_work(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "technology-specialist-suspension-001",
            "title": "Review a reversible platform change",
            "objective": "Require both technical reviewers before the CTO accepts the analysis.",
            "department": "Technology",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _technology_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    architect = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "lead_architect")
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{architect.id}/suspend",
        json={"reason": "Human Board pauses architecture review for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert "lead_architect" in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    assert by_delegate["vp_engineering"].status == "queued"
    assert by_delegate["lead_architect"].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{architect.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2


def test_evidence_complete_technology_l3_hands_off_from_cto_to_ceo(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_technology_work(
        raw_client,
        key="technology-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "Technology analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"
    consultations = db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision_id
        )
    ).all()
    assert len(consultations) == 1
    assert consultations[0].consulted_position == "cto"
    assert consultations[0].domain == "technology"
    assert consultations[0].status == "completed"
    assert consultations[0].confidence >= 0.5
    assert consultations[0].dissent is False


def test_technology_production_action_remains_held_without_execution(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "technology-production-deployment-001",
            "title": "Deploy directly to production",
            "objective": "Verify that the CTO analysis runtime cannot execute a production deployment.",
            "department": "Technology",
            "action": "deployment.production",
            "context": _technology_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "held"
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()
    assert decision.status == "pending_ceo"

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]
    assert db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all() == []
    assert db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.work_item_id == work_id
        )
    ).all() == []
    assert db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "pending_ceo"
    assert coordinated.json()["decided_by"] is None


def test_authoritative_action_cannot_be_spoofed_by_request_context(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    unsafe_context = _technology_context()
    unsafe_context["action"] = "internal.analysis"
    unsafe = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "technology-action-spoof-unsafe-001",
            "title": "Reject a disguised production deployment",
            "objective": "Prove that request context cannot downgrade the governed action.",
            "department": "Technology",
            "action": "  Deployment.Production  ",
            "context": unsafe_context,
        },
    )
    assert unsafe.status_code == 201, unsafe.text
    assert unsafe.json()["authority_level"] == "L3"
    assert unsafe.json()["status"] == "held"
    unsafe_work = db_session.get(
        OrganizationalWorkItem,
        UUID(unsafe.json()["id"]),
    )
    assert unsafe_work is not None
    assert json.loads(unsafe_work.context_json)["action"] == "deployment.production"
    assert db_session.exec(
        select(DelegationRecord).where(
            DelegationRecord.work_item_id == unsafe_work.id
        )
    ).all() == []

    safe_context = _technology_context()
    safe_context["action"] = "deployment.production"
    safe = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "technology-action-spoof-safe-001",
            "title": "Run bounded internal Technology analysis",
            "objective": "Prove that request context cannot upgrade the governed action.",
            "department": "Technology",
            "action": "  Internal.Analysis  ",
            "context": safe_context,
        },
    )
    assert safe.status_code == 201, safe.text
    assert safe.json()["authority_level"] == "L1"
    assert safe.json()["status"] == "queued"
    safe_work_id = UUID(safe.json()["id"])
    safe_work = db_session.get(OrganizationalWorkItem, safe_work_id)
    assert safe_work is not None
    assert json.loads(safe_work.context_json)["action"] == "internal.analysis"
    executed = raw_client.post(
        f"/api/v1/organization/work-items/{safe_work_id}/execute"
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"


def test_board_approval_never_executes_an_unregistered_technology_action(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "technology-board-approval-not-execution-001",
            "title": "Commit to a Technology vendor",
            "objective": "Keep a Board approval distinct from unavailable vendor execution.",
            "department": "Technology",
            "action": "vendor.commit",
            "context": _technology_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    assert created.json()["authority_level"] == "L4"
    assert created.json()["status"] == "held"
    decision = db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()
    approved = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-decision",
        json={
            "decision": "approved",
            "reason": "Human Board approves the proposal, while vendor execution remains separately controlled.",
        },
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None
    assert work.status == "held"
    assert work.completed_at is None
    assert "approval is not execution" in (work.last_error or "")
    assert db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.work_item_id == work_id
        )
    ).all() == []
    assert db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all() == []


def test_cto_contract_mismatch_holds_until_human_board_bootstrap_repairs_it(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    cto = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "cto")
    ).one()
    permissive_contract = json.dumps({"direct_action_authority": ["*"]})
    cto.contract_json = permissive_contract
    db_session.add(cto)
    db_session.commit()
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "technology-contract-repair-001",
            "title": "Review CTO contract enforcement",
            "objective": "Confirm that only the Human Board bootstrap can repair the CTO contract.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": _technology_context(),
        },
    )
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert "Human Board repair" in executed.json()["last_error"]
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    db_session.refresh(cto)
    assert cto.contract_json == permissive_contract

    repaired = raw_client.post("/api/v1/organization/bootstrap")
    assert repaired.status_code == 201, repaired.text
    db_session.expire_all()
    cto = db_session.get(OrganizationPosition, cto.id)
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert cto is not None
    assert json.loads(cto.contract_json)["direct_action_authority"] == []
    assert work is not None and work.status == "queued"
    completed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"


def test_cross_domain_consultation_is_durable_and_fails_closed(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "ceo-cross-domain-consultation-001",
            "title": "Review an internal operating position with legal implications",
            "objective": "Require COO evidence and a distinct Legal executive consultation.",
            "department": "Operations",
            "action": "internal.analysis",
            "risk_level": "high",
            "context": {"required_consultations": ["Legal"]},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()
    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "pending_ceo"
    assert "clo" in coordinated.json()["recommendation"]
    consultations = db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision.id
        )
    ).all()
    assert {item.consulted_position: item.status for item in consultations} == {
        "coo": "completed",
        "clo": "pending",
    }

    replay = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/coordinate-ceo"
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["status"] == "pending_ceo"
    assert len(db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision.id
        )
    ).all()) == 2


def test_ceo_coordination_claim_rejects_overlap_and_recovers_stale_lease(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-coordination-lease-001",
    )
    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text

    decision = db_session.get(ExecutiveDecision, decision_id)
    assert decision is not None
    decision.status = "coordinating_ceo"
    decision.coordination_token = "active-overlap-token"
    decision.coordination_claimed_at = datetime.now(timezone.utc)
    db_session.add(decision)
    db_session.commit()
    overlap = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert overlap.status_code == 409, overlap.text
    assert db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision_id
        )
    ).all() == []

    decision = db_session.get(ExecutiveDecision, decision_id)
    assert decision is not None
    decision.coordination_claimed_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.add(decision)
    db_session.commit()
    recovered = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["status"] == "approved"
    recovery_audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "executive_decision",
            AuditLog.entity_id == str(decision_id),
            AuditLog.action == "ceo_coordination_stale_claim_recovered",
        )
    ).one()
    assert recovery_audit.actor == "ceo-agent"


def test_reclaimed_ceo_lease_fences_the_old_worker(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-coordination-fencing-001",
    )
    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    decision = db_session.get(ExecutiveDecision, decision_id)
    assert decision is not None

    claimed, old_token = organization_service._claim_ceo_decision(
        db_session,
        decision,
        actor="ceo-agent-old",
    )
    assert old_token
    claimed.coordination_claimed_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.add(claimed)
    db_session.commit()
    reclaimed, new_token = organization_service._claim_ceo_decision(
        db_session,
        claimed,
        actor="ceo-agent-new",
    )
    assert new_token and new_token != old_token

    organization_service._release_ceo_claim_after_error(
        db_session,
        decision_id,
        coordination_token=old_token,
        actor="ceo-agent-old",
        reason="A stale worker must not release its successor's lease.",
    )
    db_session.refresh(reclaimed)
    assert reclaimed.status == "coordinating_ceo"
    assert reclaimed.coordination_token == new_token

    with pytest.raises(ValueError, match="lease was lost"):
        organization_service._hold_ceo_decision(
            db_session,
            reclaimed,
            coordination_token=old_token,
            reason="A stale worker attempted a fenced transition.",
            actor="ceo-agent-old",
        )
    current = db_session.get(ExecutiveDecision, decision_id)
    assert current is not None
    assert current.status == "coordinating_ceo"
    assert current.coordination_token == new_token

    organization_service._release_ceo_claim_after_error(
        db_session,
        decision_id,
        coordination_token=new_token,
        actor="ceo-agent-new",
        reason="Test cleanup releases the current lease.",
    )
    db_session.expire_all()
    current = db_session.get(ExecutiveDecision, decision_id)
    assert current is not None
    assert current.status == "pending_ceo"
    assert current.coordination_token is None


def test_ceo_runtime_cannot_repair_its_own_contract(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-contract-owner-boundary-001",
    )
    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text

    ceo = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "ceo")
    ).one()
    permissive_contract = json.dumps({"direct_action_authority": ["*"]})
    ceo.contract_json = permissive_contract
    db_session.add(ceo)
    db_session.commit()

    held = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert held.status_code == 200, held.text
    assert held.json()["status"] == "pending_ceo"
    assert "Human Board repair" in held.json()["recommendation"]
    db_session.refresh(ceo)
    assert ceo.contract_json == permissive_contract

    repaired = raw_client.post("/api/v1/organization/bootstrap")
    assert repaired.status_code == 201, repaired.text
    db_session.refresh(ceo)
    repaired_contract = json.loads(ceo.contract_json)
    assert repaired_contract["direct_action_authority"] == []
    assert repaired_contract["self_approval_allowed"] is False
    approved = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"


def test_ceo_self_requested_l3_escalates_to_board_without_approval(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "ceo-direct-self-request-001",
            "title": "Direct CEO policy request",
            "objective": "Test that the CEO cannot approve a recommendation it requested itself.",
            "department": "Executive",
            "action": "policy.publish",
            "context": {"scope": "internal operating policy"},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()
    assert decision.authority_level == "L3"
    assert decision.requested_by_position == "ceo"
    assert decision.decision_owner_position == "ceo"

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "pending_board"
    assert coordinated.json()["decision_owner_position"] == "board"
    assert coordinated.json()["decided_by"] is None

    db_session.expire_all()
    decision = db_session.get(ExecutiveDecision, decision.id)
    assert decision is not None
    assert decision.status == "pending_board"
    assert decision.decision_owner_position == "board"
    assert decision.decided_by is None
    assert decision.decided_at is None
    assert db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision.id
        )
    ).all() == []
    assert db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "executive_decision",
            AuditLog.entity_id == str(decision.id),
            AuditLog.action == "executive_decision_approved",
        )
    ).all() == []
    risk = db_session.exec(
        select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)
    ).one()
    assert risk.requires_board_attention is True
    assert risk.escalated_to_position_key == "board"
    packet = db_session.exec(
        select(BoardPacket).where(BoardPacket.packet_type == "incident")
    ).one()
    assert packet.status == "published"


def test_ceo_cannot_coordinate_l4_board_reserved_decision(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "ceo-l4-reservation-001",
            "title": "Enter a material market",
            "objective": "Prepare a market-entry recommendation reserved for the human Board.",
            "department": "Executive",
            "action": "market.entry",
            "context": {"jurisdiction": "Singapore"},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()
    assert decision.authority_level == "L4"
    assert decision.status == "pending_board"
    assert decision.decision_owner_position == "board"

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/coordinate-ceo"
    )
    assert coordinated.status_code == 409, coordinated.text

    db_session.refresh(decision)
    assert decision.status == "pending_board"
    assert decision.decision_owner_position == "board"
    assert decision.decided_by is None
    assert decision.decided_at is None


def test_work_item_deadline_and_decision_deadline(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "deadline-work-001",
        "title": "Deadline-bound operating review",
        "objective": "Review operating matter within a deadline.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    due = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat().replace("+00:00", "Z")

    response = raw_client.post(f"/api/v1/organization/work-items/{work_id}/deadline", json={"due_at": due})
    assert response.status_code == 200, response.text
    assert response.json()["due_at"] is not None

    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).first()
    assert decision is None


def test_escalation_moves_work_to_parent_position(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "escalate-work-001",
        "title": "Operational matter requiring CEO attention",
        "objective": "Route an operational matter up to the CEO.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work.assigned_position_key == "coo"

    response = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/escalate",
        json={"reason": "COO requests CEO guidance on operating boundary."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["assigned_position_key"] == "ceo"
    assert response.json()["escalated_at"] is not None

    risk = db_session.exec(select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)).one()
    assert risk.escalated_to_position_key == "ceo"
    assert risk.is_emergency is False


def test_emergency_escalation_reaches_board(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "emergency-work-001",
        "title": "Potential client harm scenario",
        "objective": "Emergency scenario must reach the Board immediately.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Operator attempted emergency escalation."},
    )
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers("admin", "human-owner"))
    response = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Credible risk of client harm; require Board visibility."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["is_emergency"] is True
    assert response.json()["assigned_position_key"] == "board"

    risks = db_session.exec(select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)).all()
    assert any(risk.is_emergency and risk.requires_board_attention for risk in risks)

    audit = db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "organizational_work_item",
            AuditLog.entity_id == str(work_id),
            AuditLog.action == "organization_work_emergency_escalated",
        )
    ).first()
    assert audit is not None
    assert audit.actor == "human-owner"


def test_emergency_promotes_pending_ceo_decision_to_board_idempotently(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-emergency-promotion-001",
    )
    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"

    first = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Credible client-harm risk requires immediate Board containment."},
    )
    assert first.status_code == 200, first.text
    assert first.json()["is_emergency"] is True
    assert first.json()["assigned_position_key"] == "board"
    assert first.json()["status"] == "pending_board"

    audit_count = len(db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "organizational_work_item",
            AuditLog.entity_id == str(work_id),
            AuditLog.action.in_([
                "organization_work_marked_emergency",
                "organization_work_emergency_escalated",
            ]),
        )
    ).all())
    second = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Repeated emergency signal must reuse the existing escalation."},
    )
    assert second.status_code == 200, second.text
    assert second.json()["id"] == first.json()["id"]

    db_session.expire_all()
    decision = db_session.get(ExecutiveDecision, decision_id)
    assert decision is not None
    assert decision.authority_level == "L4"
    assert decision.status == "pending_board"
    assert decision.decision_owner_position == "board"
    assert decision.decided_by is None
    assert decision.decided_at is None

    risks = db_session.exec(
        select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)
    ).all()
    assert len(risks) == 1
    assert risks[0].is_emergency is True
    assert risks[0].requires_board_attention is True
    assert risks[0].escalated_to_position_key == "board"
    packets = db_session.exec(
        select(BoardPacket).where(
            BoardPacket.packet_key == f"packet:incident:{work_id}"
        )
    ).all()
    assert len(packets) == 1
    assert len(db_session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "organizational_work_item",
            AuditLog.entity_id == str(work_id),
            AuditLog.action.in_([
                "organization_work_marked_emergency",
                "organization_work_emergency_escalated",
            ]),
        )
    ).all()) == audit_count

    refused = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert refused.status_code == 409, refused.text


def test_emergency_replay_heals_partial_escalation_and_keeps_risk_open(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_operations_work(
        raw_client,
        key="ceo-emergency-partial-replay-001",
    )
    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text

    work = db_session.get(OrganizationalWorkItem, work_id)
    decision = db_session.get(ExecutiveDecision, decision_id)
    risk = db_session.exec(
        select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)
    ).one()
    assert work is not None and decision is not None
    work.is_emergency = True
    work.authority_level = "L4"
    work.risk_level = "critical"
    work.assigned_position_key = "ceo"
    work.status = "held"
    decision.authority_level = "L4"
    decision.decision_owner_position = "ceo"
    decision.status = "pending_board"
    risk.category = "emergency"
    risk.severity = "critical"
    risk.is_emergency = True
    risk.requires_board_attention = True
    risk.escalated_to_position_key = "ceo"
    db_session.add(work)
    db_session.add(decision)
    db_session.add(risk)
    db_session.commit()

    healed = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Resume and reconcile the interrupted emergency escalation."},
    )
    assert healed.status_code == 200, healed.text
    assert healed.json()["assigned_position_key"] == "board"
    assert healed.json()["status"] == "pending_board"
    db_session.expire_all()
    decision = db_session.get(ExecutiveDecision, decision_id)
    risk = db_session.exec(
        select(RiskEscalation).where(RiskEscalation.work_item_id == work_id)
    ).one()
    assert decision is not None
    assert decision.decision_owner_position == "board"
    assert decision.status == "pending_board"
    assert risk.escalated_to_position_key == "board"
    assert risk.requires_board_attention is True
    assert db_session.exec(
        select(BoardPacket).where(
            BoardPacket.packet_key == f"packet:incident:{work_id}"
        )
    ).one()

    decided = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/board-decision",
        json={
            "decision": "approved",
            "reason": "The Board approves containment while the emergency risk remains tracked.",
        },
    )
    assert decided.status_code == 200, decided.text
    db_session.refresh(risk)
    assert risk.status == "open"
    assert risk.resolved_at is None


def test_overdue_scanner_escalates_work(raw_client, db_session: Session) -> None:
    from app.tasks.organization_tasks import scan_organization_deadlines_task

    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "overdue-work-001",
        "title": "Overdue operating task",
        "objective": "Task with a deadline in the past should be escalated by scanner.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    past_due = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    deadline = raw_client.post(f"/api/v1/organization/work-items/{work_id}/deadline", json={"due_at": past_due})
    assert deadline.status_code == 200, deadline.text

    result = scan_organization_deadlines_task(overdue_seconds=0, reminder_seconds=0)
    assert result["escalated"] >= 1

    db_session.refresh(db_session.get(OrganizationalWorkItem, work_id))
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work.assigned_position_key == "ceo"
    assert work.escalated_at is not None


def test_decision_deadline_sets_reminder_track(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "decision-deadline-001",
        "title": "CEO decision with deadline",
        "objective": "Decision requires a deadline.",
        "department": "Communications",
        "action": "client.external_send",
        "risk_level": "high",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)).one()
    due = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    response = raw_client.post(f"/api/v1/organization/decisions/{decision.id}/deadline", json={"due_at": due})
    assert response.status_code == 200, response.text
    assert response.json()["due_at"] is not None


def test_board_can_create_on_demand_board_packet(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "board-packet-market-entry-001",
        "title": "Enter a new jurisdiction",
        "objective": "Board must review market entry.",
        "department": "Executive",
        "action": "market.entry",
    })
    assert created.status_code == 201, created.text

    raw_client.headers.update(_headers("operator", "department-operator"))
    forbidden = raw_client.post("/api/v1/organization/board-packets", json={"packet_type": "on_demand"})
    assert forbidden.status_code == 403

    raw_client.headers.update(_headers("admin", "human-owner"))
    packet = raw_client.post("/api/v1/organization/board-packets", json={"packet_type": "on_demand"})
    assert packet.status_code == 201, packet.text
    assert packet.json()["packet_type"] == "on_demand"
    assert packet.json()["prepared_by_position"] == "ceo"
    assert packet.json()["status"] == "published"
    content = json.loads(packet.json()["content_json"])
    assert "ceo_recommendation" in content
    assert "approval_requested" in content
    assert "evidence_summary" in content
    assert "alternatives" in content
    assert "expected_impact" in content
    assert "dissenting_views" in content
    assert "cost_or_resource_impact" in content
    assert "urgency" in content
    assert "decisions_for_board" in content
    assert any("market.entry" in item["title"].lower() or "jurisdiction" in item["title"].lower() for item in content["decisions_for_board"])

    listed = raw_client.get("/api/v1/organization/board-packets")
    assert listed.status_code == 200
    assert any(item["id"] == packet.json()["id"] for item in listed.json())

    snapshot = raw_client.get("/api/v1/organization/board-packet")
    assert snapshot.status_code == 200
    assert snapshot.json()["metrics"]["pending_board"] >= 1


def test_emergency_creates_incident_board_packet(raw_client, db_session: Session) -> None:
    raw_client.headers.update(_headers())
    created = raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "emergency-board-packet-001",
        "title": "Client harm risk",
        "objective": "Emergency must trigger incident Board Packet.",
        "department": "Operations",
        "action": "internal.analysis",
    })
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    raw_client.headers.update(_headers("admin", "human-owner"))
    response = raw_client.post(
        f"/api/v1/organization/work-items/{work_id}/emergency",
        json={"reason": "Credible client harm risk; escalate to Board and generate incident packet."},
    )
    assert response.status_code == 200, response.text

    packets = db_session.exec(select(BoardPacket).where(BoardPacket.packet_type == "incident")).all()
    assert len(packets) >= 1
    incident = packets[0]
    content = json.loads(incident.content_json)
    assert content["urgency"] == "immediate"
    assert any(item["work_item_id"] == str(work_id) for item in content["emergencies"])


def test_recurring_board_packet_task_publishes_packet(raw_client, db_session: Session) -> None:
    from app.tasks.organization_tasks import generate_recurring_board_packet_task

    raw_client.headers.update(_headers())
    raw_client.post("/api/v1/organization/work-items", json={
        "idempotency_key": "recurring-packet-001",
        "title": "Routine operating review",
        "objective": "Provide content for a recurring Board Packet.",
        "department": "Operations",
        "action": "internal.analysis",
    })

    result = generate_recurring_board_packet_task("daily")
    assert "packet_id" in result
    packet = db_session.get(BoardPacket, UUID(result["packet_id"]))
    assert packet is not None
    assert packet.packet_type == "daily"
    assert packet.status == "published"

    repeated = generate_recurring_board_packet_task("daily")
    assert repeated["packet_id"] == result["packet_id"]
    assert len(db_session.exec(select(BoardPacket).where(BoardPacket.packet_type == "daily")).all()) == 1


def test_board_packet_recurring_schedules_are_registered() -> None:
    from app.core.celery_app import celery_app

    schedule = celery_app.conf.beat_schedule
    assert schedule["generate-daily-board-packet"]["args"] == ("daily",)
    assert schedule["generate-weekly-board-packet"]["args"] == ("weekly",)


# -----------------------------------------------------------------------------
# Product / CPO bounded runtime coverage
# -----------------------------------------------------------------------------


def test_product_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "product-internal-analysis-001",
        "title": "Review product readiness",
        "objective": "Produce a bounded internal Product review from product evidence.",
        "department": "Product",
        "action": "internal.analysis",
        "context": _product_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]
    assert first.json()["status"] == "queued"
    assert first.json()["assigned_position_key"] == "cpo"

    work_id = UUID(first.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == PRODUCT_DELEGATES
    assert all(item.delegator_position_key == "cpo" for item in delegations)
    assert all("L2 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    assert output["governance"]["accountable_position_key"] == "cpo"
    assert output["governance"]["external_action_authorized"] is False
    assert {item["agent"] for item in output["delegated_results"]} == {
        "product_manager_agent",
        "design_agent_agent",
    }
    assert all(item.get("run_id") for item in output["delegated_results"])

    db_session.expire_all()
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert all(item.status == "completed" for item in delegations)
    assert all(item.result_ref and item.result_ref.startswith("agent-run:") for item in delegations)
    action_outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all()
    assert len(action_outputs) == 2
    for action_output in action_outputs:
        assert any(item["type"] == "agent_run" for item in json.loads(action_output.evidence_json))
        assert json.loads(action_output.impact_json)["external_action_authorized"] is False
        specialist_output = json.loads(action_output.output_json)["output"]
        assert specialist_output["external_action_authorized"] is False
    assert len(db_session.exec(select(AgentRun)).all()) == 2

    replay = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert replay.status_code == 409, replay.text



def test_incomplete_product_evidence_holds_the_whole_work_item(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "product-evidence-incomplete-001",
            "title": "Review an undocumented product change",
            "objective": "Expose missing product evidence without approving the change.",
            "department": "Product",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []



def test_product_pricing_action_remains_held_without_execution(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "product-pricing-change-001",
            "title": "Change pricing for a product tier",
            "objective": "Verify that the CPO analysis runtime cannot execute a pricing change.",
            "department": "Product",
            "action": "pricing.change",
            "context": _product_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "held"
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()
    assert decision.status == "pending_board"

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]
    assert db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all() == []
    assert db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.work_item_id == work_id
        )
    ).all() == []
    assert db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    approved = raw_client.post(
        f"/api/v1/organization/decisions/{decision.id}/board-decision",
        json={
            "decision": "approved",
            "reason": "Board approves the pricing proposal, while execution remains separately controlled.",
        },
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None
    assert work.status == "held"
    assert work.completed_at is None
    assert "approval is not execution" in (work.last_error or "")



def test_evidence_complete_product_l3_hands_off_from_cpo_to_ceo(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_product_work(
        raw_client,
        key="product-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "Product analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"
    consultations = db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision_id
        )
    ).all()
    assert len(consultations) == 1
    assert consultations[0].consulted_position == "cpo"
    assert consultations[0].domain == "product"
    assert consultations[0].status == "completed"
    assert consultations[0].confidence >= 0.5
    assert consultations[0].dissent is False



def test_cpo_contract_mismatch_holds_until_human_board_bootstrap_repairs_it(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    cpo = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "cpo")
    ).one()
    permissive_contract = json.dumps({"direct_action_authority": ["*"]})
    cpo.contract_json = permissive_contract
    db_session.add(cpo)
    db_session.commit()
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "product-contract-repair-001",
            "title": "Review CPO contract enforcement",
            "objective": "Confirm that only the Human Board bootstrap can repair the CPO contract.",
            "department": "Product",
            "action": "internal.analysis",
            "context": _product_context(),
        },
    )
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert "Human Board repair" in executed.json()["last_error"]
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    db_session.refresh(cpo)
    assert cpo.contract_json == permissive_contract

    repaired = raw_client.post("/api/v1/organization/bootstrap")
    assert repaired.status_code == 201, repaired.text
    db_session.expire_all()
    cpo = db_session.get(OrganizationPosition, cpo.id)
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert cpo is not None
    assert json.loads(cpo.contract_json)["direct_action_authority"] == []
    assert work is not None and work.status == "queued"
    completed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"



def test_suspended_required_product_specialist_holds_then_resumes_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "product-specialist-suspension-001",
            "title": "Review a reversible product change",
            "objective": "Require both product reviewers before the CPO accepts the analysis.",
            "department": "Product",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _product_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    design_agent_position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "design_agent")
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{design_agent_position.id}/suspend",
        json={"reason": "Human Board pauses design review for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert "design_agent" in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    assert by_delegate["product_manager"].status == "queued"
    assert by_delegate["design_agent"].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{design_agent_position.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2



def test_security_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "security-internal-analysis-001",
        "title": "Review security posture",
        "objective": "Produce a bounded internal Security review from security evidence.",
        "department": "Security",
        "action": "internal.analysis",
        "context": _security_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]
    assert first.json()["status"] == "queued"
    assert first.json()["assigned_position_key"] == "ciso"

    work_id = UUID(first.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == SECURITY_DELEGATES
    assert all(item.delegator_position_key == "ciso" for item in delegations)
    assert all("L2 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    assert output["governance"]["accountable_position_key"] == "ciso"
    assert output["governance"]["external_action_authorized"] is False
    assert {item["agent"] for item in output["delegated_results"]} == {
        "security_lead_agent",
        "threat_analyst_agent",
    }
    assert all(item.get("run_id") for item in output["delegated_results"])

    db_session.expire_all()
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert all(item.status == "completed" for item in delegations)
    assert all(item.result_ref and item.result_ref.startswith("agent-run:") for item in delegations)
    action_outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all()
    assert len(action_outputs) == 2
    for action_output in action_outputs:
        assert any(item["type"] == "agent_run" for item in json.loads(action_output.evidence_json))
        assert json.loads(action_output.impact_json)["external_action_authorized"] is False
        specialist_output = json.loads(action_output.output_json)["output"]
        assert specialist_output["external_action_authorized"] is False
        assert "position.suspend" in specialist_output["blocked_actions"]
        assert "policy.publish" in specialist_output["blocked_actions"]
    assert len(db_session.exec(select(AgentRun)).all()) == 2

    replay = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert replay.status_code == 409, replay.text


def test_incomplete_security_evidence_holds_the_whole_work_item(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "security-evidence-incomplete-001",
            "title": "Review an undocumented security change",
            "objective": "Expose missing security evidence without approving the change.",
            "department": "Security",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


def test_suspended_required_security_specialist_holds_then_resumes_work(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "security-specialist-suspension-001",
            "title": "Review a reversible security change",
            "objective": "Require both security reviewers before the CISO accepts the analysis.",
            "department": "Security",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _security_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    threat_analyst_position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "threat_analyst")
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{threat_analyst_position.id}/suspend",
        json={"reason": "Human Board pauses threat analysis for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert "threat_analyst" in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    assert by_delegate["security_lead"].status == "queued"
    assert by_delegate["threat_analyst"].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{threat_analyst_position.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2


def test_evidence_complete_security_l3_hands_off_from_ciso_to_ceo(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_security_work(
        raw_client,
        key="security-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "Security analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"
    consultations = db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision_id
        )
    ).all()
    assert len(consultations) == 1
    assert consultations[0].consulted_position == "ciso"
    assert consultations[0].domain == "security"
    assert consultations[0].status == "completed"
    assert consultations[0].confidence >= 0.5
    assert consultations[0].dissent is False


def test_security_position_suspension_action_remains_held_without_execution(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "security-position-suspension-001",
            "title": "Suspend a compromised position",
            "objective": "Verify that the CISO analysis runtime cannot execute a position suspension.",
            "department": "Security",
            "action": "position.suspend",
            "context": _security_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "held"
    work_id = UUID(created.json()["id"])
    decision = db_session.exec(
        select(ExecutiveDecision).where(ExecutiveDecision.work_item_id == work_id)
    ).one()
    assert decision.status == "pending_board"

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]
    assert db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all() == []
    assert db_session.exec(
        select(OrganizationExecutionAttempt).where(
            OrganizationExecutionAttempt.work_item_id == work_id
        )
    ).all() == []
    assert db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all() == []
    assert db_session.exec(select(AgentRun)).all() == []


def test_security_specialists_cannot_be_invoked_for_non_security_work(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "security-specialist-non-security-001",
            "title": "Route non-Security work to Security",
            "objective": "Security specialists must reject non-Security work at delegation time.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": _security_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cto"
    work_id = UUID(created.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == TECHNOLOGY_DELEGATES
    for delegation in delegations:
        assert delegation.delegate_position_key not in SECURITY_DELEGATES


def test_ciso_only_assignment_for_security_work(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "ciso-only-assignment-001",
            "title": "Security work is assigned to CISO",
            "objective": "Confirm Security work is owned by the CISO position.",
            "department": "Security",
            "action": "internal.analysis",
            "context": _security_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "ciso"


def test_security_prohibited_action_enforcement(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    for prohibited_action in ("secrets.access", "policy.publish", "position.suspend"):
        created = raw_client.post(
            "/api/v1/organization/work-items",
            json={
                "idempotency_key": f"security-prohibited-{prohibited_action.replace('.', '-')}-001",
                "title": f"Security prohibited action: {prohibited_action}",
                "objective": "Verify Security runtime fails closed on prohibited actions.",
                "department": "Security",
                "action": prohibited_action,
                "context": _security_context(),
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["status"] == "held"
        work_id = UUID(created.json()["id"])

        executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
        assert executed.status_code == 200, executed.text
        assert executed.json()["status"] == "held"
        assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]


def test_security_operations_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "security-operations-internal-analysis-001",
        "title": "Review SOC posture",
        "objective": "Produce a bounded internal Security Operations review from SOC evidence.",
        "department": "Security Operations",
        "action": "internal.analysis",
        "context": _security_operations_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]
    assert first.json()["status"] == "queued"
    assert first.json()["assigned_position_key"] == "ciso"

    work_id = UUID(first.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == SECURITY_OPERATIONS_DELEGATES
    assert all(item.delegator_position_key == "ciso" for item in delegations)
    assert all("L2 Security Operations internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    assert output["governance"]["accountable_position_key"] == "ciso"
    assert output["governance"]["external_action_authorized"] is False
    assert {item["agent"] for item in output["delegated_results"]} == {
        "soc_lead_agent",
        "soc_analyst_agent",
    }
    assert all(item.get("run_id") for item in output["delegated_results"])

    db_session.expire_all()
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert all(item.status == "completed" for item in delegations)
    assert all(item.result_ref and item.result_ref.startswith("agent-run:") for item in delegations)
    action_outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all()
    assert len(action_outputs) == 2
    for action_output in action_outputs:
        assert any(item["type"] == "agent_run" for item in json.loads(action_output.evidence_json))
        assert json.loads(action_output.impact_json)["external_action_authorized"] is False
        specialist_output = json.loads(action_output.output_json)["output"]
        assert specialist_output["external_action_authorized"] is False
        assert "position.suspend" in specialist_output["blocked_actions"]
        assert "policy.publish" in specialist_output["blocked_actions"]
    assert len(db_session.exec(select(AgentRun)).all()) == 2

    replay = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert replay.status_code == 409, replay.text


def test_incomplete_security_operations_evidence_holds_the_whole_work_item(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "security-operations-evidence-incomplete-001",
            "title": "Review an undocumented SOC change",
            "objective": "Expose missing Security Operations evidence without approving the change.",
            "department": "Security Operations",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


def test_suspended_required_soc_specialist_holds_then_resumes_work(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "soc-specialist-suspension-001",
            "title": "Review a reversible SOC change",
            "objective": "Require both SOC reviewers before the CISO accepts the analysis.",
            "department": "Security Operations",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _security_operations_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    soc_analyst_position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "soc_analyst")
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{soc_analyst_position.id}/suspend",
        json={"reason": "Human Board pauses SOC analysis for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert "soc_analyst" in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    assert by_delegate["soc_lead"].status == "queued"
    assert by_delegate["soc_analyst"].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{soc_analyst_position.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2


def test_evidence_complete_security_operations_l3_hands_off_from_ciso_to_ceo(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_security_operations_work(
        raw_client,
        key="security-operations-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "Security Operations analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"
    consultations = db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision_id
        )
    ).all()
    assert len(consultations) == 1
    assert consultations[0].consulted_position == "ciso"
    assert consultations[0].domain == "security"
    assert consultations[0].status == "completed"
    assert consultations[0].confidence >= 0.5
    assert consultations[0].dissent is False


def test_soc_specialists_cannot_be_invoked_for_non_soc_work(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "soc-specialist-non-soc-001",
            "title": "Route non-SOC work to Security Operations",
            "objective": "SOC specialists must reject non-SOC work at delegation time.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": _security_operations_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cto"
    work_id = UUID(created.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == TECHNOLOGY_DELEGATES
    for delegation in delegations:
        assert delegation.delegate_position_key not in SECURITY_OPERATIONS_DELEGATES


def test_ciso_only_assignment_for_security_operations_work(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "ciso-only-soc-assignment-001",
            "title": "Security Operations work is assigned to CISO",
            "objective": "Confirm Security Operations work is owned by the CISO position.",
            "department": "Security Operations",
            "action": "internal.analysis",
            "context": _security_operations_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "ciso"


def test_security_operations_prohibited_action_enforcement(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    for prohibited_action in ("secrets.access", "policy.publish", "position.suspend"):
        created = raw_client.post(
            "/api/v1/organization/work-items",
            json={
                "idempotency_key": f"soc-prohibited-{prohibited_action.replace('.', '-')}-001",
                "title": f"Security Operations prohibited action: {prohibited_action}",
                "objective": "Verify Security Operations runtime fails closed on prohibited actions.",
                "department": "Security Operations",
                "action": prohibited_action,
                "context": _security_operations_context(),
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["status"] == "held"
        work_id = UUID(created.json()["id"])

        executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
        assert executed.status_code == 200, executed.text
        assert executed.json()["status"] == "held"
        assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]


# -----------------------------------------------------------------------------
# Marketing / CMO bounded runtime coverage
# -----------------------------------------------------------------------------


def test_marketing_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "marketing-internal-analysis-001",
        "title": "Review marketing readiness",
        "objective": "Produce a bounded internal Marketing review from marketing evidence.",
        "department": "Marketing",
        "action": "internal.analysis",
        "context": _marketing_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]
    assert first.json()["status"] == "queued"
    assert first.json()["assigned_position_key"] == "cmo"

    work_id = UUID(first.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == MARKETING_DELEGATES
    assert all(item.delegator_position_key == "cmo" for item in delegations)
    assert all("L2 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    assert output["governance"]["accountable_position_key"] == "cmo"
    assert output["governance"]["external_action_authorized"] is False
    assert {item["agent"] for item in output["delegated_results"]} == {
        "creative_director_agent",
        "marketing_manager_agent",
    }
    assert all(item.get("run_id") for item in output["delegated_results"])

    db_session.expire_all()
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert all(item.status == "completed" for item in delegations)
    assert all(item.result_ref and item.result_ref.startswith("agent-run:") for item in delegations)
    action_outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all()
    assert len(action_outputs) == 2
    for action_output in action_outputs:
        assert any(item["type"] == "agent_run" for item in json.loads(action_output.evidence_json))
        assert json.loads(action_output.impact_json)["external_action_authorized"] is False
        specialist_output = json.loads(action_output.output_json)["output"]
        assert specialist_output["external_action_authorized"] is False
    assert len(db_session.exec(select(AgentRun)).all()) == 2

    replay = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert replay.status_code == 409, replay.text


def test_incomplete_marketing_evidence_holds_the_whole_work_item(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "marketing-evidence-incomplete-001",
            "title": "Review an undocumented marketing change",
            "objective": "Expose missing marketing evidence without approving the change.",
            "department": "Marketing",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


def test_suspended_required_marketing_specialist_holds_then_resumes_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "marketing-specialist-suspension-001",
            "title": "Review a reversible marketing change",
            "objective": "Require both marketing reviewers before the CMO accepts the analysis.",
            "department": "Marketing",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _marketing_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    marketing_manager_position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "marketing_manager")
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{marketing_manager_position.id}/suspend",
        json={"reason": "Human Board pauses marketing management review for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert "marketing_manager" in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    assert by_delegate["creative_director"].status == "queued"
    assert by_delegate["marketing_manager"].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{marketing_manager_position.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2


def test_evidence_complete_marketing_l3_hands_off_from_cmo_to_ceo(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_marketing_work(
        raw_client,
        key="marketing-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "Marketing analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"
    consultations = db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision_id
        )
    ).all()
    assert len(consultations) == 1
    assert consultations[0].consulted_position == "cmo"
    assert consultations[0].domain == "marketing"
    assert consultations[0].status == "completed"
    assert consultations[0].confidence >= 0.5
    assert consultations[0].dissent is False


def test_cmo_contract_mismatch_holds_until_human_board_bootstrap_repairs_it(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    cmo = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "cmo")
    ).one()
    permissive_contract = json.dumps({"direct_action_authority": ["*"]})
    cmo.contract_json = permissive_contract
    db_session.add(cmo)
    db_session.commit()
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "marketing-contract-repair-001",
            "title": "Review CMO contract enforcement",
            "objective": "Confirm that only the Human Board bootstrap can repair the CMO contract.",
            "department": "Marketing",
            "action": "internal.analysis",
            "context": _marketing_context(),
        },
    )
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert "Human Board repair" in executed.json()["last_error"]
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    db_session.refresh(cmo)
    assert cmo.contract_json == permissive_contract

    repaired = raw_client.post("/api/v1/organization/bootstrap")
    assert repaired.status_code == 201, repaired.text
    db_session.expire_all()
    cmo = db_session.get(OrganizationPosition, cmo.id)
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert cmo is not None
    assert json.loads(cmo.contract_json)["direct_action_authority"] == []
    assert work is not None and work.status == "queued"
    completed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"


def test_marketing_prohibited_action_enforcement(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    for prohibited_action in ("pricing.change", "policy.publish"):
        created = raw_client.post(
            "/api/v1/organization/work-items",
            json={
                "idempotency_key": f"marketing-prohibited-{prohibited_action.replace('.', '-')}-001",
                "title": f"Marketing prohibited action: {prohibited_action}",
                "objective": "Verify Marketing runtime fails closed on prohibited actions.",
                "department": "Marketing",
                "action": prohibited_action,
                "context": _marketing_context(),
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["status"] == "held"
        work_id = UUID(created.json()["id"])

        executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
        assert executed.status_code == 200, executed.text
        assert executed.json()["status"] == "held"
        assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]


def test_marketing_specialists_cannot_be_invoked_for_non_marketing_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "marketing-specialist-non-marketing-001",
            "title": "Route non-Marketing work to Marketing",
            "objective": "Marketing specialists must reject non-Marketing work at delegation time.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": _marketing_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cto"
    work_id = UUID(created.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == TECHNOLOGY_DELEGATES
    for delegation in delegations:
        assert delegation.delegate_position_key not in MARKETING_DELEGATES


def test_cmo_only_assignment_for_marketing_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "cmo-only-assignment-001",
            "title": "Marketing work is assigned to CMO",
            "objective": "Confirm Marketing work is owned by the CMO position.",
            "department": "Marketing",
            "action": "internal.analysis",
            "context": _marketing_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cmo"



# -----------------------------------------------------------------------------
# Finance / CFO bounded runtime coverage
# -----------------------------------------------------------------------------


def test_finance_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "finance-internal-analysis-001",
        "title": "Review finance readiness",
        "objective": "Produce a bounded internal Finance review from finance evidence.",
        "department": "Finance",
        "action": "internal.analysis",
        "context": _finance_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]
    assert first.json()["status"] == "queued"
    assert first.json()["assigned_position_key"] == "cfo"

    work_id = UUID(first.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == FINANCE_DELEGATES
    assert all(item.delegator_position_key == "cfo" for item in delegations)
    assert all("L2 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"
    output = json.loads(executed.json()["output_json"])
    assert output["governance"]["accountable_position_key"] == "cfo"
    assert output["governance"]["external_action_authorized"] is False
    assert {item["agent"] for item in output["delegated_results"]} == {
        "financial_analyst_agent",
        "accounting_lead_agent",
    }
    assert all(item.get("run_id") for item in output["delegated_results"])

    db_session.expire_all()
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert all(item.status == "completed" for item in delegations)
    assert all(item.result_ref and item.result_ref.startswith("agent-run:") for item in delegations)
    action_outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id == work_id
        )
    ).all()
    assert len(action_outputs) == 2
    for action_output in action_outputs:
        assert any(item["type"] == "agent_run" for item in json.loads(action_output.evidence_json))
        assert json.loads(action_output.impact_json)["external_action_authorized"] is False
        specialist_output = json.loads(action_output.output_json)["output"]
        assert specialist_output["external_action_authorized"] is False
    assert len(db_session.exec(select(AgentRun)).all()) == 2

    replay = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert replay.status_code == 409, replay.text


def test_incomplete_finance_evidence_holds_the_whole_work_item(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "finance-evidence-incomplete-001",
            "title": "Review an undocumented finance change",
            "objective": "Expose missing finance evidence without approving the change.",
            "department": "Finance",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


def test_suspended_required_finance_specialist_holds_then_resumes_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "finance-specialist-suspension-001",
            "title": "Review a reversible finance change",
            "objective": "Require both finance reviewers before the CFO accepts the analysis.",
            "department": "Finance",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _finance_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    accounting_lead_position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "accounting_lead")
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{accounting_lead_position.id}/suspend",
        json={"reason": "Human Board pauses accounting review for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert "accounting_lead" in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    assert by_delegate["financial_analyst"].status == "queued"
    assert by_delegate["accounting_lead"].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{accounting_lead_position.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2


def test_evidence_complete_finance_l3_hands_off_from_cfo_to_ceo(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_finance_work(
        raw_client,
        key="finance-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "Finance analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"
    consultations = db_session.exec(
        select(ExecutiveCouncilConsultation).where(
            ExecutiveCouncilConsultation.decision_id == decision_id
        )
    ).all()
    assert len(consultations) == 1
    assert consultations[0].consulted_position == "cfo"
    assert consultations[0].domain == "finance"
    assert consultations[0].status == "completed"
    assert consultations[0].confidence >= 0.5
    assert consultations[0].dissent is False


def test_cfo_contract_mismatch_holds_until_human_board_bootstrap_repairs_it(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    cfo = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == "cfo")
    ).one()
    permissive_contract = json.dumps({"direct_action_authority": ["*"]})
    cfo.contract_json = permissive_contract
    db_session.add(cfo)
    db_session.commit()
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "finance-contract-repair-001",
            "title": "Review CFO contract enforcement",
            "objective": "Confirm that only the Human Board bootstrap can repair the CFO contract.",
            "department": "Finance",
            "action": "internal.analysis",
            "context": _finance_context(),
        },
    )
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert "Human Board repair" in executed.json()["last_error"]
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    db_session.refresh(cfo)
    assert cfo.contract_json == permissive_contract

    repaired = raw_client.post("/api/v1/organization/bootstrap")
    assert repaired.status_code == 201, repaired.text
    db_session.expire_all()
    cfo = db_session.get(OrganizationPosition, cfo.id)
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert cfo is not None
    assert json.loads(cfo.contract_json)["direct_action_authority"] == []
    assert work is not None and work.status == "queued"
    completed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"


def test_finance_prohibited_action_enforcement(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    for prohibited_action in ("payment.initiate", "pricing.change", "spend.above_threshold"):
        created = raw_client.post(
            "/api/v1/organization/work-items",
            json={
                "idempotency_key": f"finance-prohibited-{prohibited_action.replace('.', '-')}-001",
                "title": f"Finance prohibited action: {prohibited_action}",
                "objective": "Verify Finance runtime fails closed on prohibited actions.",
                "department": "Finance",
                "action": prohibited_action,
                "context": _finance_context(),
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["status"] == "held"
        work_id = UUID(created.json()["id"])

        executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
        assert executed.status_code == 200, executed.text
        assert executed.json()["status"] == "held"
        assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]


def test_finance_specialists_cannot_be_invoked_for_non_finance_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "finance-specialist-non-finance-001",
            "title": "Route non-Finance work to Finance",
            "objective": "Finance specialists must reject non-Finance work at delegation time.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": _finance_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cto"
    work_id = UUID(created.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == TECHNOLOGY_DELEGATES
    for delegation in delegations:
        assert delegation.delegate_position_key not in FINANCE_DELEGATES


def test_cfo_only_assignment_for_finance_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "cfo-only-assignment-001",
            "title": "Finance work is assigned to CFO",
            "objective": "Confirm Finance work is owned by the CFO position.",
            "department": "Finance",
            "action": "internal.analysis",
            "context": _finance_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cfo"



def test_communications_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "communications-internal-analysis-001",
        "title": "Internal Communications readiness review",
        "objective": "Coordinate evidence-backed internal Communications analysis within the CEO mandate.",
        "department": "Communications",
        "action": "internal.analysis",
        "context": _communications_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    work_id = UUID(first.json()["id"])
    assert first.json()["id"] == second.json()["id"]
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == COMMUNICATIONS_DELEGATES
    assert all(item.delegator_position_key == "cco" for item in delegations)
    assert all("L2 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"


def test_incomplete_communications_evidence_holds_the_whole_work_item(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "communications-evidence-incomplete-001",
            "title": "Review undocumented communications change",
            "objective": "Expose missing communications evidence without approving the change.",
            "department": "Communications",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


@pytest.mark.parametrize("suspended_position", sorted(COMMUNICATIONS_DELEGATES))
def test_suspended_required_communications_specialist_holds_then_resumes_work(
    raw_client, db_session: Session, suspended_position
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": f"communications-suspend-{suspended_position}-001",
            "title": "Communications review with suspended specialist",
            "objective": "Confirm a suspended communications specialist holds the work item.",
            "department": "Communications",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _communications_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    specialist_position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == suspended_position)
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{specialist_position.id}/suspend",
        json={"reason": "Human Board pauses communications review for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert suspended_position in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    other_delegate = next(iter(COMMUNICATIONS_DELEGATES - {suspended_position}))
    assert by_delegate[other_delegate].status == "queued"
    assert by_delegate[suspended_position].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{specialist_position.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2


def test_evidence_complete_communications_l3_hands_off_from_cco_to_ceo(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_communications_work(
        raw_client,
        key="communications-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "Communications analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"


def test_communications_prohibited_action_enforcement(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    for prohibited_action in ("policy.publish", "client.external_send"):
        created = raw_client.post(
            "/api/v1/organization/work-items",
            json={
                "idempotency_key": f"communications-prohibited-{prohibited_action}-001",
                "title": f"Communications prohibited action {prohibited_action}",
                "objective": "Confirm Communications runtime holds prohibited actions.",
                "department": "Communications",
                "action": prohibited_action,
                "context": _communications_context(),
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["status"] == "held"
        work_id = UUID(created.json()["id"])

        executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
        assert executed.status_code == 200, executed.text
        assert executed.json()["status"] == "held"
        assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]


def test_communications_specialists_cannot_be_invoked_for_non_communications_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "communications-specialist-non-communications-001",
            "title": "Route non-Communications work to Communications",
            "objective": "Communications specialists must reject non-Communications work at delegation time.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": _communications_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cto"
    work_id = UUID(created.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == TECHNOLOGY_DELEGATES
    for delegation in delegations:
        assert delegation.delegate_position_key not in COMMUNICATIONS_DELEGATES


def test_cco_only_assignment_for_communications_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "cco-only-assignment-001",
            "title": "Communications work is assigned to CCO",
            "objective": "Confirm Communications work is owned by the CCO position.",
            "department": "Communications",
            "action": "internal.analysis",
            "context": _communications_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cco"



def test_people_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "people-internal-analysis-001",
        "title": "Internal People readiness review",
        "objective": "Coordinate evidence-backed internal People analysis within the CEO mandate.",
        "department": "People",
        "action": "internal.analysis",
        "context": _people_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    work_id = UUID(first.json()["id"])
    assert first.json()["id"] == second.json()["id"]
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == PEOPLE_DELEGATES
    assert all(item.delegator_position_key == "chro" for item in delegations)
    assert all("L2 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"


def test_incomplete_people_evidence_holds_the_whole_work_item(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "people-evidence-incomplete-001",
            "title": "Review undocumented people change",
            "objective": "Expose missing people evidence without approving the change.",
            "department": "People",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


@pytest.mark.parametrize("suspended_position", sorted(PEOPLE_DELEGATES))
def test_suspended_required_people_specialist_holds_then_resumes_work(
    raw_client, db_session: Session, suspended_position
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": f"people-suspend-{suspended_position}-001",
            "title": "People review with suspended specialist",
            "objective": "Confirm a suspended people specialist holds the work item.",
            "department": "People",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _people_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    specialist_position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == suspended_position)
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{specialist_position.id}/suspend",
        json={"reason": "Human Board pauses people review for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert suspended_position in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    other_delegate = next(iter(PEOPLE_DELEGATES - {suspended_position}))
    assert by_delegate[other_delegate].status == "queued"
    assert by_delegate[suspended_position].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{specialist_position.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2


def test_evidence_complete_people_l3_hands_off_from_chro_to_ceo(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_people_work(
        raw_client,
        key="people-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "People analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"


def test_people_prohibited_action_enforcement(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    for prohibited_action in ("hiring.decision", "compensation.change", "termination.action"):
        created = raw_client.post(
            "/api/v1/organization/work-items",
            json={
                "idempotency_key": f"people-prohibited-{prohibited_action}-001",
                "title": f"People prohibited action {prohibited_action}",
                "objective": "Confirm People runtime holds prohibited actions.",
                "department": "People",
                "action": prohibited_action,
                "context": _people_context(),
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["status"] == "held"
        work_id = UUID(created.json()["id"])

        executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
        assert executed.status_code == 200, executed.text
        assert executed.json()["status"] == "held"
        assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]


def test_people_specialists_cannot_be_invoked_for_non_people_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "people-specialist-non-people-001",
            "title": "Route non-People work to People",
            "objective": "People specialists must reject non-People work at delegation time.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": _people_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cto"
    work_id = UUID(created.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == TECHNOLOGY_DELEGATES
    for delegation in delegations:
        assert delegation.delegate_position_key not in PEOPLE_DELEGATES


def test_chro_only_assignment_for_people_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "chro-only-assignment-001",
            "title": "People work is assigned to CHRO",
            "objective": "Confirm People work is owned by the CHRO position.",
            "department": "People",
            "action": "internal.analysis",
            "context": _people_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "chro"


def test_legal_internal_analysis_runs_required_specialists_without_a_lead(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    payload = {
        "idempotency_key": "legal-internal-analysis-001",
        "title": "Internal Legal readiness review",
        "objective": "Coordinate evidence-backed internal Legal analysis within the CEO mandate.",
        "department": "Legal",
        "action": "internal.analysis",
        "context": _legal_context(),
    }
    first = raw_client.post("/api/v1/organization/work-items", json=payload)
    second = raw_client.post("/api/v1/organization/work-items", json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    work_id = UUID(first.json()["id"])
    assert first.json()["id"] == second.json()["id"]
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == LEGAL_DELEGATES
    assert all(item.delegator_position_key == "clo" for item in delegations)
    assert all("L2 internal analysis only" in item.authority_basis for item in delegations)

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "completed"


def test_incomplete_legal_evidence_holds_the_whole_work_item(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "legal-evidence-incomplete-001",
            "title": "Review undocumented legal change",
            "objective": "Expose missing legal evidence without approving the change.",
            "department": "Legal",
            "action": "internal.analysis",
            "context": {"facts": {"change_scope": "unknown"}, "evidence": {}},
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "held"
    assert executed.json()["completed_at"] is None
    assert "missing evidence fields" in executed.json()["last_error"]
    assert json.loads(executed.json()["output_json"]) == {}
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


@pytest.mark.parametrize("suspended_position", sorted(LEGAL_DELEGATES))
def test_suspended_required_legal_specialist_holds_then_resumes_work(
    raw_client, db_session: Session, suspended_position
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    raw_client.post("/api/v1/organization/bootstrap")
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": f"legal-suspend-{suspended_position}-001",
            "title": "Legal review with suspended specialist",
            "objective": "Confirm a suspended legal specialist holds the work item.",
            "department": "Legal",
            "action": "internal.analysis",
            "max_execution_attempts": 1,
            "context": _legal_context(),
        },
    )
    assert created.status_code == 201, created.text
    work_id = UUID(created.json()["id"])
    specialist_position = db_session.exec(
        select(OrganizationPosition).where(OrganizationPosition.position_key == suspended_position)
    ).one()
    suspended = raw_client.post(
        f"/api/v1/organization/positions/{specialist_position.id}/suspend",
        json={"reason": "Human Board pauses legal review for an independence check."},
    )
    assert suspended.status_code == 200, suspended.text

    first_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert first_execution.status_code == 200, first_execution.text
    assert first_execution.json()["status"] == "held"
    assert suspended_position in first_execution.json()["last_error"]
    db_session.expire_all()
    by_delegate = {
        item.delegate_position_key: item
        for item in db_session.exec(
            select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
        ).all()
    }
    other_delegate = next(iter(LEGAL_DELEGATES - {suspended_position}))
    assert by_delegate[other_delegate].status == "queued"
    assert by_delegate[suspended_position].status == "held"
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []
    assert db_session.exec(select(AgentRun)).all() == []

    resumed = raw_client.post(
        f"/api/v1/organization/positions/{specialist_position.id}/resume",
        json={"reason": "Human Board completed the independence check and restored the reviewer."},
    )
    assert resumed.status_code == 200, resumed.text
    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "queued"

    second_execution = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert second_execution.status_code == 200, second_execution.text
    assert second_execution.json()["status"] == "completed"
    assert len(db_session.exec(select(OrganizationExecutionAttempt)).all()) == 1
    assert len(db_session.exec(select(AgentRun)).all()) == 2
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 2


def test_evidence_complete_legal_l3_hands_off_from_clo_to_ceo(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    work_id, decision_id = _high_risk_legal_work(
        raw_client,
        key="legal-ceo-handoff-001",
    )

    executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "pending_ceo"
    assert json.loads(executed.json()["output_json"])["governance"][
        "external_action_authorized"
    ] is False

    coordinated = raw_client.post(
        f"/api/v1/organization/decisions/{decision_id}/coordinate-ceo"
    )
    assert coordinated.status_code == 200, coordinated.text
    assert coordinated.json()["status"] == "approved"
    assert "Legal analysis" in coordinated.json()["decision_reason"]
    assert "No external action was authorized" in coordinated.json()["decision_reason"]

    db_session.expire_all()
    work = db_session.get(OrganizationalWorkItem, work_id)
    assert work is not None and work.status == "completed"


def test_legal_prohibited_action_enforcement(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    for prohibited_action in ("contract.sign", "authority.submit", "legal.opinion.final"):
        created = raw_client.post(
            "/api/v1/organization/work-items",
            json={
                "idempotency_key": f"legal-prohibited-{prohibited_action}-001",
                "title": f"Legal prohibited action {prohibited_action}",
                "objective": "Confirm Legal runtime holds prohibited actions.",
                "department": "Legal",
                "action": prohibited_action,
                "context": _legal_context(),
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["status"] == "held"
        work_id = UUID(created.json()["id"])

        executed = raw_client.post(f"/api/v1/organization/work-items/{work_id}/execute")
        assert executed.status_code == 200, executed.text
        assert executed.json()["status"] == "held"
        assert "only bounded internal.analysis is enabled" in executed.json()["last_error"]


def test_legal_specialists_cannot_be_invoked_for_non_legal_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "legal-specialist-non-legal-001",
            "title": "Route non-Legal work to Legal",
            "objective": "Legal specialists must reject non-Legal work at delegation time.",
            "department": "Technology",
            "action": "internal.analysis",
            "context": _legal_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "cto"
    work_id = UUID(created.json()["id"])
    delegations = db_session.exec(
        select(DelegationRecord).where(DelegationRecord.work_item_id == work_id)
    ).all()
    assert {item.delegate_position_key for item in delegations} == TECHNOLOGY_DELEGATES
    for delegation in delegations:
        assert delegation.delegate_position_key not in LEGAL_DELEGATES


def test_clo_only_assignment_for_legal_work(
    raw_client, db_session: Session
) -> None:
    raw_client.headers.update(_headers("admin", "human-owner"))
    created = raw_client.post(
        "/api/v1/organization/work-items",
        json={
            "idempotency_key": "clo-only-assignment-001",
            "title": "Legal work is assigned to CLO",
            "objective": "Confirm Legal work is owned by the CLO position.",
            "department": "Legal",
            "action": "internal.analysis",
            "context": _legal_context(),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["assigned_position_key"] == "clo"

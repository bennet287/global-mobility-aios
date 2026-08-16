from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CapabilityPriority = Literal["tier1", "tier2", "tier3", "future"]
CapabilityStatus = Literal["existing", "planned", "review"]


@dataclass(frozen=True)
class CapabilityPosition:
    position_key: str
    title: str
    authority_level: str
    reports_to_position_key: str
    status: CapabilityStatus
    note: str = ""


@dataclass(frozen=True)
class CapabilityDomain:
    domain_key: str
    name: str
    executive_position: str
    priority: CapabilityPriority
    positions: tuple[CapabilityPosition, ...]
    governance_partners: tuple[str, ...] = ()
    purpose: str = ""


def _existing(key: str, title: str, authority: str, reports_to: str, note: str = "") -> CapabilityPosition:
    return CapabilityPosition(key, title, authority, reports_to, "existing", note)


def _planned(key: str, title: str, authority: str, reports_to: str, note: str = "") -> CapabilityPosition:
    return CapabilityPosition(key, title, authority, reports_to, "planned", note)


def _review(key: str, title: str, authority: str, reports_to: str, note: str) -> CapabilityPosition:
    return CapabilityPosition(key, title, authority, reports_to, "review", note)


TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_ORDER: tuple[str, ...] = (
    "lead_software_engineer",
    "backend_api_engineer",
    "frontend_product_engineer",
    "platform_engineer",
    "site_reliability_engineer",
    "qa_automation_engineer",
    "data_engineer",
    "ai_ml_platform_engineer",
    "developer_experience_engineer",
    "application_security_engineer",
    "iam_engineer",
    "security_grc_lead",
    "vulnerability_management_engineer",
)
TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS = frozenset(
    TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_ORDER
)


# Capability architecture for Phase 13.16.3A.x.
#
# Phase 13.16.3A.1 established this registry as a planning-only inventory.
# Phase 13.16.3A.2 promotes the bounded Technology + Security tranche declared
# above into the runtime foundation while all remaining planned keys stay proposals.
# Promoted capability positions are organizational capacity only: their runtime
# contracts explicitly disable delegated/direct execution until a later reviewed slice.
ORGANIZATION_CAPABILITY_DOMAINS: tuple[CapabilityDomain, ...] = (
    CapabilityDomain(
        "technology.engineering_leadership",
        "Engineering Leadership",
        "cto",
        "tier1",
        (
            _existing("vp_engineering", "Vice President of Engineering", "L2", "cto"),
        ),
        purpose="Own engineering delivery discipline, technical execution quality, and cross-team coordination.",
    ),
    CapabilityDomain(
        "technology.application_engineering",
        "Application Engineering",
        "cto",
        "tier1",
        (
            _existing("lead_software_engineer", "Lead Software Engineer", "L2", "vp_engineering"),
            _existing("backend_api_engineer", "Backend / API Engineer", "L1", "lead_software_engineer"),
            _existing("frontend_product_engineer", "Frontend / Product Engineer", "L1", "lead_software_engineer"),
        ),
        purpose="Build and maintain product applications, APIs, workflows, integrations, and user experiences.",
    ),
    CapabilityDomain(
        "technology.platform_reliability",
        "Platform & Reliability",
        "cto",
        "tier1",
        (
            _existing("platform_engineer", "Platform Engineer", "L2", "vp_engineering"),
            _existing("site_reliability_engineer", "Site Reliability Engineer", "L1", "platform_engineer"),
        ),
        governance_partners=("ciso",),
        purpose="Operate cloud/platform foundations, reliability, observability, deployment safety, and resilience.",
    ),
    CapabilityDomain(
        "technology.quality_engineering",
        "Quality Engineering",
        "cto",
        "tier1",
        (
            _existing("qa_automation_engineer", "QA & Test Automation Engineer", "L1", "vp_engineering"),
        ),
        purpose="Own automated quality evidence, regression confidence, release-readiness validation, and test discipline.",
    ),
    CapabilityDomain(
        "technology.data_ai_engineering",
        "Data & AI Engineering",
        "cto",
        "tier1",
        (
            _existing("data_engineer", "Data Engineer", "L1", "vp_engineering"),
            _existing("ai_ml_platform_engineer", "AI / ML Platform Engineer", "L1", "vp_engineering"),
        ),
        governance_partners=("ciso", "cpo"),
        purpose="Build governed data pipelines, AI/ML platform capabilities, evaluation infrastructure, and trustworthy analytics inputs.",
    ),
    CapabilityDomain(
        "technology.architecture_enablement",
        "Architecture & Engineering Enablement",
        "cto",
        "tier1",
        (
            _existing("lead_architect", "Lead Architect", "L2", "cto"),
            _existing("developer_experience_engineer", "Developer Experience Engineer", "L1", "lead_architect"),
        ),
        governance_partners=("ciso", "cfo"),
        purpose="Define architecture standards, reversibility, integration boundaries, developer enablement, and cost-aware technical standards.",
    ),
    CapabilityDomain(
        "security.security_engineering",
        "Security Engineering & AppSec",
        "ciso",
        "tier1",
        (
            _existing("security_lead", "Security Lead", "L2", "ciso"),
            _existing("application_security_engineer", "Application Security Engineer", "L1", "security_lead"),
        ),
        governance_partners=("cto",),
        purpose="Define and verify security controls across product, application, platform, and software-delivery boundaries.",
    ),
    CapabilityDomain(
        "security.identity_access",
        "Identity & Access Management",
        "ciso",
        "tier1",
        (
            _existing("iam_engineer", "Identity & Access Governance Engineer", "L1", "security_lead"),
        ),
        governance_partners=("cto", "chro"),
        purpose="Own identity lifecycle, authentication, authorization, privileged access, and access-governance evidence.",
    ),
    CapabilityDomain(
        "security.grc",
        "Governance, Risk & Compliance",
        "ciso",
        "tier1",
        (
            _existing("security_grc_lead", "Security GRC Lead", "L2", "ciso"),
        ),
        governance_partners=("clo",),
        purpose="Own security-control governance, security-risk evidence, audit readiness, and control-framework assurance.",
    ),
    CapabilityDomain(
        "security.security_operations",
        "Security Operations & Incident Response",
        "ciso",
        "tier1",
        (
            _existing("soc_lead", "SOC Lead", "L2", "ciso"),
            _existing("soc_analyst", "SOC Analyst", "L2", "ciso"),
        ),
        governance_partners=("cto",),
        purpose="Monitor security signals, triage incidents, preserve evidence, and coordinate bounded incident response.",
    ),
    CapabilityDomain(
        "security.threat_vulnerability",
        "Threat & Vulnerability Management",
        "ciso",
        "tier1",
        (
            _existing("threat_analyst", "Threat Analyst", "L2", "ciso"),
            _existing("vulnerability_management_engineer", "Vulnerability Management Engineer", "L1", "security_lead"),
        ),
        governance_partners=("cto",),
        purpose="Assess threats, attack patterns, vulnerabilities, compromised-agent indicators, and remediation priorities.",
    ),
    CapabilityDomain(
        "operations.global_mobility_operations",
        "Global Mobility Operations",
        "coo",
        "tier1",
        (
            _planned("mobility_operations_lead", "Global Mobility Operations Lead", "L2", "coo"),
            _planned("case_operations_specialist", "Mobility Case Operations Specialist", "L1", "mobility_operations_lead"),
            _planned("pathway_operations_specialist", "Pathway & Eligibility Operations Specialist", "L1", "mobility_operations_lead"),
        ),
        governance_partners=("clo",),
        purpose="Operate mobility cases, pathway execution, milestones, service readiness, and evidence-backed case coordination.",
    ),
    CapabilityDomain(
        "operations.document_evidence",
        "Document & Evidence Operations",
        "coo",
        "tier1",
        (
            _existing("application_readiness", "Application Readiness", "L1", "coo"),
            _planned("document_evidence_operations_lead", "Document & Evidence Operations Lead", "L2", "coo"),
            _planned("evidence_quality_specialist", "Evidence Quality Specialist", "L1", "document_evidence_operations_lead"),
        ),
        governance_partners=("clo",),
        purpose="Coordinate document readiness, evidence completeness, expiry/renewal risk, and application-readiness controls.",
    ),
    CapabilityDomain(
        "operations.authority_filing",
        "Authority & Filing Operations",
        "coo",
        "tier1",
        (
            _planned("authority_filing_operations_lead", "Authority & Filing Operations Lead", "L2", "coo"),
            _planned("submission_readiness_specialist", "Submission Readiness Specialist", "L1", "authority_filing_operations_lead"),
        ),
        governance_partners=("clo",),
        purpose="Coordinate submission readiness and authority-facing operations without creating autonomous filing authority.",
    ),
    CapabilityDomain(
        "operations.client_success",
        "Client Success",
        "coo",
        "tier2",
        (
            _planned("customer_success_lead", "Customer Success Lead", "L2", "coo"),
            _planned("mobility_user_success_specialist", "Mobility User Success Specialist", "L1", "customer_success_lead"),
        ),
        governance_partners=("cco",),
        purpose="Own service experience, adoption, case communication, and outcome-oriented customer coordination.",
    ),
    CapabilityDomain(
        "operations.partner_operations",
        "Partner Operations",
        "coo",
        "tier2",
        (
            _planned("partner_operations_lead", "Partner Operations Lead", "L2", "coo"),
        ),
        governance_partners=("clo", "cfo"),
        purpose="Coordinate agency, partner, external-assignment, and vendor-facing operational relationships.",
    ),
    CapabilityDomain(
        "operations.operational_excellence",
        "Operational Excellence",
        "coo",
        "tier1",
        (
            _existing("operations_coordination", "Operations Coordination", "L1", "coo"),
        ),
        purpose="Own work orchestration, dependencies, service-level risk, blocker visibility, and process-quality discipline.",
    ),
    CapabilityDomain(
        "operations.commercial_operations",
        "Commercial Operations",
        "coo",
        "tier2",
        (
            _review("sales_summary", "Sales Intelligence", "L1", "coo", "Retain for compatibility; review long-term placement under a future Revenue organization."),
            _planned("enterprise_sales_lead", "Enterprise Sales Lead", "L2", "coo"),
            _planned("revenue_operations_analyst", "Revenue Operations Analyst", "L1", "enterprise_sales_lead"),
        ),
        governance_partners=("cmo", "cfo"),
        purpose="Coordinate enterprise pipeline, commercial evidence, revenue operations, and customer acquisition without creating pricing authority.",
    ),
    CapabilityDomain(
        "operations.operational_intelligence",
        "Operational Intelligence",
        "coo",
        "tier1",
        (
            _review("business_intelligence", "Business Intelligence", "L1", "coo", "Keep current runtime; clarify boundary with Data & AI Engineering before any reassignment."),
        ),
        governance_partners=("cto", "cfo"),
        purpose="Translate operating evidence into workload, service, quality, and decision-support signals.",
    ),
    CapabilityDomain(
        "operations.global_mobility_intelligence",
        "Global Mobility Intelligence",
        "coo",
        "tier1",
        (
            _planned("jurisdiction_research_lead", "Jurisdiction Research Lead", "L2", "coo"),
            _planned("regulatory_intelligence_analyst", "Regulatory Intelligence Analyst", "L1", "jurisdiction_research_lead"),
            _planned("evidence_source_certification_lead", "Evidence & Source Certification Lead", "L2", "coo"),
            _planned("mobility_intelligence_analyst", "Mobility Intelligence Analyst", "L1", "jurisdiction_research_lead"),
        ),
        governance_partners=("clo",),
        purpose="Own jurisdiction research, official-source monitoring, evidence provenance, review operations, and mobility-intelligence analysis while legal interpretation remains human-governed.",
    ),
    CapabilityDomain(
        "product.product_management",
        "Product Management",
        "cpo",
        "tier1",
        (
            _existing("product_manager", "Product Manager", "L2", "cpo"),
            _review("head_of_product", "Head of Product", "L2", "cpo", "Potentially redundant with CPO at current scale; retain until a bounded repurpose/removal decision is approved."),
        ),
        purpose="Own product strategy decomposition, scope, sequencing, success criteria, and evidence-backed prioritization.",
    ),
    CapabilityDomain(
        "product.design_research",
        "Product Design & UX Research",
        "cpo",
        "tier1",
        (
            _existing("design_agent", "Design Agent", "L2", "cpo"),
        ),
        purpose="Own product experience quality, UX research, accessibility thinking, and design evidence.",
    ),
    CapabilityDomain(
        "product.product_operations",
        "Product Operations & Analytics",
        "cpo",
        "tier2",
        (
            _planned("product_operations_analyst", "Product Operations & Analytics Specialist", "L1", "cpo"),
        ),
        governance_partners=("cto",),
        purpose="Connect roadmap execution, product evidence, adoption signals, and cross-team product operations.",
    ),
    CapabilityDomain(
        "product.accessibility_content",
        "Accessibility & Content Experience",
        "cpo",
        "tier2",
        (
            _planned("accessibility_content_designer", "Accessibility & Content Experience Designer", "L1", "cpo"),
        ),
        governance_partners=("clo",),
        purpose="Own accessible interaction/content standards and user-facing clarity across professional and mobility-user experiences.",
    ),
    CapabilityDomain(
        "legal.corporate_commercial",
        "Commercial & Corporate Legal",
        "clo",
        "tier1",
        (
            _existing("general_counsel", "General Counsel", "L2", "clo"),
        ),
        governance_partners=("cfo", "coo"),
        purpose="Provide human-governed corporate, commercial, contract, and organizational legal analysis.",
    ),
    CapabilityDomain(
        "legal.mobility_regulatory",
        "Global Mobility / Immigration Regulatory",
        "clo",
        "tier1",
        (
            _planned("immigration_regulatory_counsel", "Global Mobility / Immigration Regulatory Counsel", "L2", "clo"),
        ),
        governance_partners=("coo",),
        purpose="Own human legal interpretation of mobility/immigration regulation and challenge unsupported certainty.",
    ),
    CapabilityDomain(
        "legal.privacy_data_protection",
        "Privacy & Data Protection",
        "clo",
        "tier1",
        (
            _planned("privacy_data_protection_counsel", "Privacy & Data Protection Counsel", "L2", "clo"),
        ),
        governance_partners=("ciso", "cto"),
        purpose="Own legal privacy/data-protection analysis, data-rights interpretation, and legal review of data-processing boundaries.",
    ),
    CapabilityDomain(
        "legal.public_policy",
        "Public Policy & Government Regulation",
        "clo",
        "tier1",
        (
            _existing("public_policy_compliance_lead", "Public Policy / Compliance Lead", "L2", "clo"),
        ),
        governance_partners=("cco",),
        purpose="Assess policy landscapes, regulatory agendas, and compliance implications without authorizing external government action.",
    ),
    CapabilityDomain(
        "legal.regulatory_assurance",
        "Legal Compliance & Regulatory Assurance",
        "clo",
        "tier1",
        (
            _planned("regulatory_assurance_counsel", "Legal Compliance & Regulatory Assurance Counsel", "L2", "clo"),
        ),
        governance_partners=("ciso", "coo"),
        purpose="Provide independent legal/regulatory assurance over evidence-backed operating and publication boundaries.",
    ),
    CapabilityDomain(
        "finance.fp_and_a",
        "FP&A / Business Finance",
        "cfo",
        "tier2",
        (
            _existing("financial_analyst", "Financial Analyst", "L2", "cfo"),
        ),
        purpose="Own planning, forecasting, unit economics, scenario analysis, and evidence-backed business finance.",
    ),
    CapabilityDomain(
        "finance.accounting_controller",
        "Accounting & Controller",
        "cfo",
        "tier2",
        (
            _existing("accounting_lead", "Accounting Lead", "L2", "cfo"),
        ),
        purpose="Own accounting quality, close/readiness controls, reporting discipline, and audit evidence.",
    ),
    CapabilityDomain(
        "finance.tax_treasury",
        "Tax & Treasury",
        "cfo",
        "tier2",
        (
            _planned("tax_treasury_specialist", "Tax & Treasury Specialist", "L1", "cfo"),
        ),
        governance_partners=("clo",),
        purpose="Coordinate corporate tax, treasury, cash/liquidity, and financial-risk analysis within human authority.",
    ),
    CapabilityDomain(
        "finance.procurement_vendor",
        "Procurement & Vendor Management",
        "cfo",
        "tier2",
        (
            _planned("vendor_procurement_manager", "Vendor & Procurement Manager", "L1", "cfo"),
        ),
        governance_partners=("cto", "ciso", "clo"),
        purpose="Coordinate vendor economics, procurement evidence, renewal/TCO analysis, and cross-functional due diligence without autonomous commitment authority.",
    ),
    CapabilityDomain(
        "finance.finops",
        "FinOps / Cloud Economics",
        "cfo",
        "tier2",
        (
            _planned("finops_analyst", "FinOps Analyst", "L1", "cfo"),
        ),
        governance_partners=("cto",),
        purpose="Create cost transparency and cloud/resource optimization evidence across Finance and Engineering.",
    ),
    CapabilityDomain(
        "marketing.product_marketing",
        "Product Marketing",
        "cmo",
        "tier3",
        (
            _planned("product_marketing_manager", "Product Marketing Manager", "L1", "cmo"),
        ),
        governance_partners=("cpo", "coo"),
        purpose="Translate product capability into evidence-backed positioning for mobility users, professionals, corporate clients, and partners.",
    ),
    CapabilityDomain(
        "marketing.growth_demand",
        "Growth & Demand Generation",
        "cmo",
        "tier3",
        (
            _planned("growth_marketing_manager", "Growth & Demand Generation Manager", "L1", "cmo"),
        ),
        purpose="Own ethical demand generation, funnel experiments, acquisition evidence, and growth operations.",
    ),
    CapabilityDomain(
        "marketing.brand_content",
        "Brand & Content",
        "cmo",
        "tier3",
        (
            _existing("creative_director", "Creative Director", "L2", "cmo"),
        ),
        governance_partners=("cco",),
        purpose="Own brand system, creative quality, content standards, and premium product presentation.",
    ),
    CapabilityDomain(
        "marketing.lifecycle_crm",
        "Lifecycle & CRM Marketing",
        "cmo",
        "tier3",
        (
            _planned("lifecycle_crm_marketing_manager", "Lifecycle & CRM Marketing Manager", "L1", "cmo"),
        ),
        governance_partners=("coo",),
        purpose="Own lifecycle communications, CRM journeys, retention/adoption programs, and consent-aware marketing operations.",
    ),
    CapabilityDomain(
        "marketing.operations_analytics",
        "Marketing Operations & Analytics",
        "cmo",
        "tier3",
        (
            _review("marketing_manager", "Marketing Manager", "L2", "cmo", "Retain current role; consider evolving scope toward marketing operations/analytics as specialist roles mature."),
        ),
        purpose="Own campaign operations, measurement, marketing process quality, and cross-channel reporting.",
    ),
    CapabilityDomain(
        "communications.corporate_pr",
        "Corporate Communications & PR",
        "cco",
        "tier3",
        (
            _existing("pr_comms_lead", "PR / Communications Lead", "L2", "cco"),
        ),
        governance_partners=("cmo",),
        purpose="Own corporate reputation, media/PR strategy, external narrative, and communications evidence.",
    ),
    CapabilityDomain(
        "communications.public_affairs",
        "Public Affairs & Government Relations",
        "cco",
        "tier3",
        (
            _existing("government_relations_lead", "Government Relations Lead", "L2", "cco"),
        ),
        governance_partners=("clo",),
        purpose="Own public-affairs strategy and stakeholder coordination while legal/regulatory interpretation remains with CLO.",
    ),
    CapabilityDomain(
        "communications.crisis_issues",
        "Crisis & Issues Communications",
        "cco",
        "tier3",
        (
            _planned("crisis_communications_lead", "Crisis & Issues Communications Lead", "L1", "cco"),
        ),
        governance_partners=("ciso", "clo", "coo"),
        purpose="Coordinate high-trust communications during operational, security, regulatory, or reputational incidents.",
    ),
    CapabilityDomain(
        "communications.executive_stakeholder",
        "Executive & Stakeholder Communications",
        "cco",
        "tier3",
        (
            _planned("executive_communications_manager", "Executive & Stakeholder Communications Manager", "L1", "cco"),
        ),
        purpose="Support Board/CEO communications, stakeholder narratives, and high-sensitivity communication preparation.",
    ),
    CapabilityDomain(
        "people.people_operations",
        "People Operations",
        "chro",
        "tier2",
        (
            _existing("hr_lead", "HR Lead", "L2", "chro"),
        ),
        governance_partners=("cfo", "clo"),
        purpose="Own employee lifecycle operations, HR controls, workforce administration, and people-process evidence.",
    ),
    CapabilityDomain(
        "people.talent_acquisition",
        "Talent Acquisition",
        "chro",
        "tier2",
        (
            _review("culture_recruitment_lead", "Culture / Recruitment Lead", "L2", "chro", "Retain current role; split recruitment and culture/accountability only when scale justifies separate owners."),
        ),
        purpose="Own evidence-backed recruiting, talent pipeline, role design, and hiring-process quality without autonomous hiring authority.",
    ),
    CapabilityDomain(
        "people.learning_performance",
        "Learning & Performance",
        "chro",
        "tier2",
        (
            _planned("learning_performance_lead", "Learning & Performance Lead", "L1", "chro"),
        ),
        purpose="Own learning systems, capability development, performance-process design, and professional-growth evidence.",
    ),
    CapabilityDomain(
        "people.culture_engagement",
        "Culture & Engagement",
        "chro",
        "tier2",
        (
            _planned("people_culture_lead", "People Culture & Engagement Lead", "L1", "chro"),
        ),
        purpose="Own culture signals, engagement, retention context, employee feedback, and organizational-health evidence.",
    ),
    CapabilityDomain(
        "people.workforce_analytics",
        "Workforce Planning & People Analytics",
        "chro",
        "tier2",
        (
            _planned("workforce_planning_analytics_lead", "Workforce Planning & People Analytics Lead", "L1", "chro"),
        ),
        governance_partners=("cfo", "coo"),
        purpose="Model capability demand, workforce capacity, role gaps, organizational load, and people analytics for human decision-making.",
    ),
    CapabilityDomain(
        "board.ai_governance_assurance",
        "Independent AI Governance & Assurance",
        "board",
        "future",
        (
            _planned("ai_governance_assurance_lead", "AI Governance & Assurance Lead", "L2", "board"),
        ),
        governance_partners=("ceo", "ciso", "clo"),
        purpose="Provide future Board-level independent assurance over AIOS governance, controls, evidence, and human-authority boundaries.",
    ),
)


CURRENT_EXECUTIVE_POSITIONS = frozenset({"coo", "cto", "ciso", "cpo", "cfo", "clo", "cmo", "cco", "chro"})
PLANNED_C_SUITE_POSITIONS = frozenset()  # Deliberately no CIO/CRO/extra C-suite in this architecture slice.


def capability_domain_for_position(position_key: str) -> CapabilityDomain | None:
    for domain in ORGANIZATION_CAPABILITY_DOMAINS:
        if any(position.position_key == position_key for position in domain.positions):
            return domain
    return None


def technology_security_foundation_specs() -> tuple[tuple[str, str, str, str, str, None], ...]:
    mapped = capability_position_map()
    specs: list[tuple[str, str, str, str, str, None]] = []
    for position_key in TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_ORDER:
        position = mapped[position_key]
        domain = capability_domain_for_position(position_key)
        if domain is None:
            raise RuntimeError(f"Capability domain missing for foundation tranche position: {position_key}")
        if position.status != "existing":
            raise RuntimeError(f"Foundation tranche position is not promoted to existing: {position_key}")
        specs.append(
            (
                position.position_key,
                position.title,
                domain.name,
                position.reports_to_position_key,
                position.authority_level,
                None,
            )
        )
    return tuple(specs)


def capability_position_map() -> dict[str, CapabilityPosition]:
    positions: dict[str, CapabilityPosition] = {}
    for domain in ORGANIZATION_CAPABILITY_DOMAINS:
        for position in domain.positions:
            if position.position_key in positions:
                raise ValueError(f"Duplicate capability position key: {position.position_key}")
            positions[position.position_key] = position
    return positions


def capability_domains_for_executive(position_key: str) -> tuple[CapabilityDomain, ...]:
    return tuple(domain for domain in ORGANIZATION_CAPABILITY_DOMAINS if domain.executive_position == position_key)


def planned_position_keys() -> frozenset[str]:
    return frozenset(
        position.position_key
        for domain in ORGANIZATION_CAPABILITY_DOMAINS
        for position in domain.positions
        if position.status == "planned"
    )


def review_position_keys() -> frozenset[str]:
    return frozenset(
        position.position_key
        for domain in ORGANIZATION_CAPABILITY_DOMAINS
        for position in domain.positions
        if position.status == "review"
    )

from app.services.organization_capability_architecture import (
    CURRENT_EXECUTIVE_POSITIONS,
    ORGANIZATION_CAPABILITY_DOMAINS,
    MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS,
    PLANNED_C_SUITE_POSITIONS,
    TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS,
    capability_domains_for_executive,
    capability_position_map,
    planned_position_keys,
    review_position_keys,
)
from app.services.organization_governance import POSITION_SPECS


def test_capability_architecture_maps_every_existing_non_executive_foundation_position() -> None:
    foundation_keys = {item[0] for item in POSITION_SPECS}
    foundation_non_exec = foundation_keys - {"board", "ceo"} - set(CURRENT_EXECUTIVE_POSITIONS)
    mapped = capability_position_map()
    mapped_existing_or_review = {
        key for key, position in mapped.items() if position.status in {"existing", "review"}
    }

    assert len(POSITION_SPECS) == 61
    assert foundation_non_exec == mapped_existing_or_review


def test_capability_architecture_keeps_current_executive_council_and_adds_no_new_c_suite() -> None:
    assert CURRENT_EXECUTIVE_POSITIONS == {
        "coo",
        "cto",
        "ciso",
        "cpo",
        "cfo",
        "clo",
        "cmo",
        "cco",
        "chro",
    }
    assert PLANNED_C_SUITE_POSITIONS == frozenset()

    foundation = {item[0]: item for item in POSITION_SPECS}
    assert foundation["ciso"][3] == "ceo"
    assert foundation["cto"][3] == "ceo"
    assert foundation["ciso"][3] != "cto"


def test_tier1_architecture_covers_product_build_run_secure_mobility_and_legal_governance() -> None:
    tier1_names = {domain.name for domain in ORGANIZATION_CAPABILITY_DOMAINS if domain.priority == "tier1"}
    required = {
        "Application Engineering",
        "Platform & Reliability",
        "Quality Engineering",
        "Data & AI Engineering",
        "Architecture & Engineering Enablement",
        "Security Engineering & AppSec",
        "Identity & Access Management",
        "Governance, Risk & Compliance",
        "Security Operations & Incident Response",
        "Global Mobility Operations",
        "Document & Evidence Operations",
        "Authority & Filing Operations",
        "Global Mobility Intelligence",
        "Product Management",
        "Product Design & UX Research",
        "Global Mobility / Immigration Regulatory",
        "Privacy & Data Protection",
        "Legal Compliance & Regulatory Assurance",
    }
    assert required.issubset(tier1_names)


def test_global_mobility_intelligence_is_operationally_owned_by_coo_with_clo_governance() -> None:
    domain = next(
        item
        for item in ORGANIZATION_CAPABILITY_DOMAINS
        if item.domain_key == "operations.global_mobility_intelligence"
    )
    assert domain.executive_position == "coo"
    assert "clo" in domain.governance_partners
    assert {
        "jurisdiction_research_lead",
        "regulatory_intelligence_analyst",
        "evidence_source_certification_lead",
        "mobility_intelligence_analyst",
    }.issubset({position.position_key for position in domain.positions})


def test_cross_functional_boundaries_are_explicit() -> None:
    ciso_domains = {domain.name for domain in capability_domains_for_executive("ciso")}
    cto_domains = {domain.name for domain in capability_domains_for_executive("cto")}
    clo_domains = {domain.name for domain in capability_domains_for_executive("clo")}

    assert "Identity & Access Management" in ciso_domains
    assert "Governance, Risk & Compliance" in ciso_domains
    assert "Platform & Reliability" in cto_domains
    assert "Data & AI Engineering" in cto_domains
    assert "Privacy & Data Protection" in clo_domains
    assert "Global Mobility / Immigration Regulatory" in clo_domains


def test_architecture_flags_existing_overlap_for_review_without_deleting_positions() -> None:
    assert review_position_keys() == {
        "business_intelligence",
        "culture_recruitment_lead",
        "head_of_product",
        "marketing_manager",
        "sales_summary",
    }
    assert "head_of_product" not in planned_position_keys()


def test_planned_positions_are_bounded_below_c_suite_and_unique() -> None:
    mapped = capability_position_map()
    planned = [position for position in mapped.values() if position.status == "planned"]

    assert planned
    assert all(position.authority_level in {"L1", "L2"} for position in planned)
    assert len(mapped) == len({position.position_key for position in mapped.values()})
    assert "cio" not in mapped
    assert "cro" not in mapped


def test_technology_security_tranche_is_promoted_without_promoting_remaining_plan() -> None:
    mapped = capability_position_map()

    assert len(TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS) == 13
    assert all(mapped[key].status == "existing" for key in TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS)
    assert TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS.isdisjoint(planned_position_keys())
    assert len(planned_position_keys()) == 19

    foundation_keys = {item[0] for item in POSITION_SPECS}
    assert TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS.issubset(foundation_keys)


def test_mobility_operations_intelligence_legal_tranche_is_promoted_without_authority_expansion() -> None:
    mapped = capability_position_map()

    assert len(MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS) == 14
    assert all(
        mapped[key].status == "existing"
        for key in MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS
    )
    assert MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS.isdisjoint(
        planned_position_keys()
    )

    foundation_keys = {item[0] for item in POSITION_SPECS}
    assert MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS.issubset(
        foundation_keys
    )
    assert {
        mapped[key].reports_to_position_key
        for key in MOBILITY_OPERATIONS_INTELLIGENCE_LEGAL_FOUNDATION_TRANCHE_KEYS
        if mapped[key].authority_level == "L2"
    }.issubset({"coo", "clo"})

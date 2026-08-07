import pytest

from app.services.role_card_loader import (
    AGENT_OUTPUT_SCHEMA,
    AGENT_ROLE_CARD_MAP,
    build_system_prompt,
    get_agent_output_schema,
    list_role_cards,
    load_role_card,
)


def test_list_role_cards_finds_all_cards():
    cards = list_role_cards()
    expected = {
        "AI_CEO",
        "Document_Officer",
        "Recruitment_Specialist",
        "Sales_Followup_Agent",
        "Sales_Summary_Agent",
        "Operations_Coordination_Agent",
        "Business_Intelligence_Agent",
        "VP_Engineering",
        "Lead_Architect",
        "Application_Readiness_Agent",
        "Study_Abroad_Advisor",
        "Visa_Truth_Agent",
    }
    assert expected.issubset(set(cards.keys()))
    for path in cards.values():
        assert path.suffix == ".md"
        assert path.exists()


@pytest.mark.parametrize(
    "card_name",
    [
        "Visa_Truth_Agent",
        "Document_Officer",
        "Recruitment_Specialist",
        "Sales_Followup_Agent",
        "AI_CEO",
        "Study_Abroad_Advisor",
        "Sales_Summary_Agent",
        "Operations_Coordination_Agent",
        "Business_Intelligence_Agent",
        "VP_Engineering",
        "Lead_Architect",
        "Application_Readiness_Agent",
    ],
)
def test_load_role_card_parses_sections(card_name):
    card = load_role_card(card_name)
    assert card["name"] == card_name
    assert card["title"]
    assert card["mission"]
    assert card["path"].endswith(f"{card_name}.md")


def test_load_role_card_unknown_raises():
    with pytest.raises(FileNotFoundError):
        load_role_card("NonExistent_Agent")


def test_cto_role_card_names_reports_and_prohibits_direct_technology_action():
    card = load_role_card("CTO")
    position_contract = card["raw_sections"]["position contract"]
    controls = card["raw_sections"]["non-delegable controls"]

    assert "Vice President of Engineering Agent" in position_contract
    assert "Lead Architect Agent" in position_contract
    assert "Never mutate production systems or infrastructure" in controls
    assert "Never deploy software" in controls
    assert "initiate spend" in controls
    assert "sign a contract" in controls
    assert "authorize an external action" in controls


def test_agent_role_card_map_covers_all_canonical_agents():
    canonical_agents = {
        "truth_explanation_agent",
        "document_checklist_agent",
        "client_drafting_agent",
        "sales_summary_agent",
        "operations_coordination_agent",
        "business_intelligence_agent",
        "vp_engineering_agent",
        "lead_architect_agent",
        "product_manager_agent",
        "design_agent_agent",
        "application_readiness_agent",
        "eligibility_coach",
        "eligibility_agent",
    }
    assert set(AGENT_ROLE_CARD_MAP.keys()) == canonical_agents


def test_build_system_prompt_contains_key_directives():
    prompt = build_system_prompt("truth_explanation_agent")
    assert "Mission" in prompt
    assert "Universal Safety Rules" in prompt
    assert "Output Format" in prompt
    assert "human_review_required" in prompt
    assert "guaranteed visa" in prompt.lower() or "official" in prompt.lower()


def test_build_system_prompt_returns_json_schema():
    prompt = build_system_prompt("document_checklist_agent")
    assert "missing_documents" in prompt
    assert "verified_documents" in prompt


@pytest.mark.parametrize("agent_name", ["vp_engineering_agent", "lead_architect_agent"])
def test_technology_system_prompts_include_hard_safety_contract(agent_name):
    prompt = build_system_prompt(agent_name)
    assert "deployment_allowed" in prompt
    assert "external_action_authorized" in prompt
    assert "infrastructure_mutation_allowed" in prompt
    assert "secrets_access_allowed" in prompt
    assert "human_review_required" in prompt
    assert "client_facing" in prompt


@pytest.mark.parametrize("agent_name", ["product_manager_agent", "design_agent_agent"])
def test_product_system_prompts_include_hard_safety_contract(agent_name):
    prompt = build_system_prompt(agent_name)
    assert "external_action_authorized" in prompt
    assert "human_review_required" in prompt
    assert "client_facing" in prompt
    assert "blocked_actions" in prompt


def test_get_agent_output_schema_returns_expected_keys():
    schema = get_agent_output_schema("client_drafting_agent")
    assert "draft_subject" in schema
    assert "draft_body" in schema
    assert "send_allowed" in schema


def test_all_canonical_agents_have_output_schema():
    canonical_agents = {
        "truth_explanation_agent",
        "document_checklist_agent",
        "client_drafting_agent",
        "sales_summary_agent",
        "operations_coordination_agent",
        "business_intelligence_agent",
        "vp_engineering_agent",
        "lead_architect_agent",
        "product_manager_agent",
        "design_agent_agent",
        "application_readiness_agent",
        "eligibility_coach",
        "eligibility_agent",
    }
    assert set(AGENT_OUTPUT_SCHEMA.keys()) == canonical_agents

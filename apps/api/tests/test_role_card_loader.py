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


def test_agent_role_card_map_covers_all_canonical_agents():
    canonical_agents = {
        "truth_explanation_agent",
        "document_checklist_agent",
        "client_drafting_agent",
        "sales_summary_agent",
        "application_readiness_agent",
        "eligibility_coach",
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
        "application_readiness_agent",
        "eligibility_coach",
    }
    assert set(AGENT_OUTPUT_SCHEMA.keys()) == canonical_agents

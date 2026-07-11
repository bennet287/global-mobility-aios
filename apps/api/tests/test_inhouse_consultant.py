from __future__ import annotations

import pytest
from sqlmodel import Session

from app.services.inhouse_consultant import _match_lead, consult
from tests.conftest import create_lead


def test_consult_routes_to_draft_agent_when_keywords_match(db_session: Session) -> None:
    lead = create_lead(db_session, name="Drafty Lead")
    result = consult(db_session, message="draft a follow-up email for Drafty Lead")

    decision = result["decision"]
    assert decision.decision == "propose_action"
    assert decision.agent_name == "client_drafting_agent"
    assert decision.lead_id == lead.id
    assert decision.task_template
    assert decision.confidence in {"high", "medium", "low"}
    assert "Drafty Lead" in result["reply"]


def test_consult_asks_for_clarification_when_agent_known_but_lead_missing(db_session: Session) -> None:
    result = consult(db_session, message="draft an email")

    decision = result["decision"]
    assert decision.decision == "ask_clarification"
    assert decision.clarification_question
    assert "lead" in decision.clarification_question.lower()


def test_consult_escalates_when_no_keywords_match(db_session: Session) -> None:
    result = consult(db_session, message="what is the weather today")

    decision = result["decision"]
    assert decision.decision == "wait_for_human"
    assert decision.escalation_reason
    assert decision.confidence == "low"


def test_match_lead_by_email(db_session: Session) -> None:
    lead = create_lead(db_session, name="Email Lead")
    matched = _match_lead([lead], lead.email)
    assert matched is not None
    assert matched.id == lead.id


def test_match_lead_by_uuid(db_session: Session) -> None:
    lead = create_lead(db_session, name="UUID Lead")
    matched = _match_lead([lead], str(lead.id))
    assert matched is not None
    assert matched.id == lead.id


def test_match_lead_by_name_substring(db_session: Session) -> None:
    lead = create_lead(db_session, name="Sub String")
    matched = _match_lead([lead], "sub")
    assert matched is not None
    assert matched.id == lead.id


def test_lead_hint_from_email_in_message(db_session: Session) -> None:
    lead = create_lead(db_session, name="Hint Lead")
    result = consult(db_session, message=f"summarize {lead.email}")

    decision = result["decision"]
    assert decision.decision == "propose_action"
    assert decision.agent_name == "sales_summary_agent"
    assert decision.lead_id == lead.id

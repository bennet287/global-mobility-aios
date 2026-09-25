from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.models.domain import AuditLog
from app.models.runtime_economics import ProviderCallAttempt
from app.services import inhouse_consultant as consultant_module
from app.services.inhouse_consultant import _match_lead, consult
from app.services.llm_client import LLMResponse
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


def test_llm_consult_records_request_owner_completion(monkeypatch, db_session: Session) -> None:
    class Provider:
        name = "deepseek"
        default_model = "deepseek-chat"

        def complete(self, **kwargs):
            return LLMResponse(
                content=(
                    '{"decision":"wait_for_human","escalation_reason":"Human review",'
                    '"confidence":"low"}'
                ),
                provider=self.name,
                model=self.default_model,
            )

    monkeypatch.setattr(consultant_module.settings, "llm_provider", "deepseek")
    monkeypatch.setattr(consultant_module.LLMProviderFactory, "get_provider", lambda: Provider())

    result = consult(db_session, message="review this unusual case")
    assert result["decision"].decision == "wait_for_human"

    db_session.expire_all()
    attempt = db_session.exec(select(ProviderCallAttempt)).one()
    assert attempt.context_kind == "inhouse_consultant_request"
    assert attempt.operation_key is not None
    assert attempt.status == "observed"

    completion = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == "provider_request_operation_finished")
        .where(AuditLog.entity_type == "provider_call_attempt")
        .where(AuditLog.entity_id == str(attempt.id))
    ).one()
    evidence = completion.after_state_json or ""
    assert '"provider_outcome_inferred": false' in evidence
    assert '"billed_cost_known": false' in evidence
    assert '"call_slot_released": false' in evidence

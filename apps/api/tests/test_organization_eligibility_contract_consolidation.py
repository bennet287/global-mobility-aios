from __future__ import annotations

import inspect
from types import SimpleNamespace

from app.models.domain import OrganizationActorType
from app.services import organization_decision_readiness
from app.services import organization_eligibility_effect
from app.services import organization_eligibility_transition_intent
from app.services import organization_eligibility_verification_floor
from app.services import organization_independent_eligibility_verification
from app.services.mobility_domain import mobility_intent_domain
from app.services.organization_command import system_bound_agent_command_context


def test_g4_1_mobility_intent_domain_preserves_accepted_mapping() -> None:
    cases = {
        "study_abroad": "study",
        "study": "study",
        "student": "study",
        "overseas_job": "work",
        "work": "work",
        "job": "work",
        "employment": "work",
        "visa": "visa",
        "permanent": "visa",
        "residency": "visa",
        "immigration": "visa",
        "other": "general",
        None: "general",
    }
    for intent, expected in cases.items():
        assert mobility_intent_domain(SimpleNamespace(intent=intent)) == expected


def test_g4_1_system_bound_agent_context_keeps_position_as_actor() -> None:
    context = system_bound_agent_command_context(
        tenant_key="tenant-a",
        position_key="mobility-eligibility-specialist",
        department="mobility",
        authority_level="specialist",
        correlation_key="trace-1",
    )

    assert context.tenant_key == "tenant-a"
    assert context.actor_id == "mobility-eligibility-specialist"
    assert context.actor_type is OrganizationActorType.agent
    assert context.authenticated_user_id == "system"
    assert context.role == "operator"
    assert context.position_key == "mobility-eligibility-specialist"
    assert context.correlation_key == "trace-1"


def test_g4_1_decision_readiness_no_longer_imports_catalogue_private_blocker() -> None:
    source = inspect.getsource(organization_decision_readiness)

    assert "_publication_evidence_blockers" not in source
    assert "pathway_publication_integrity_blockers" in source
    assert "def _lead_domain(" not in source
    assert "mobility_intent_domain" in source


def test_g4_1_e2_uses_shared_domain_and_system_agent_contracts() -> None:
    source = inspect.getsource(organization_eligibility_transition_intent)

    assert "def _intent_domain(" not in source
    assert "mobility_intent_domain" in source
    assert "def _command_context(" not in source
    assert "system_bound_agent_command_context" in source


def test_g4_1_g1_uses_shared_system_agent_contract() -> None:
    source = inspect.getsource(organization_independent_eligibility_verification)

    assert "def _command_context(" not in source
    assert "system_bound_agent_command_context" in source


def test_g4_1_g3_consumes_public_g2_action_contracts() -> None:
    module_symbols = vars(organization_eligibility_effect)

    assert "_original_e2_payload" not in module_symbols
    assert "_rebuild_action" not in module_symbols
    assert "_command_context" not in module_symbols
    assert "original_eligibility_attempt_payload" in module_symbols
    assert "rebuild_eligibility_action" in module_symbols
    assert "eligibility_command_context" in module_symbols


def test_g4_1_g2_exposes_named_public_action_contracts() -> None:
    assert callable(organization_eligibility_verification_floor.eligibility_command_context)
    assert callable(organization_eligibility_verification_floor.original_eligibility_attempt_payload)
    assert callable(organization_eligibility_verification_floor.rebuild_eligibility_action)

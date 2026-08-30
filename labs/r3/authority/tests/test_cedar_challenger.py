from __future__ import annotations

from pathlib import Path

from labs.r3.authority.cedar_adapter import (
    CedarAdapter,
    _cedar_request_payload,
    run_challenger_corpus,
)
from labs.r3.common.generate_fixtures import build_authority_corpus


def test_cedar_reference_fallback_is_explicit_diagnostic_only() -> None:
    corpus = build_authority_corpus()
    outcomes = run_challenger_corpus(
        scenarios=corpus["scenarios"],
        use_reference_fallback=True,
    )
    assert len(outcomes) == 120
    assert all(outcome["passed"] for outcome in outcomes)
    assert all(outcome["used_reference_fallback"] for outcome in outcomes)
    assert all(not outcome["provider_called"] for outcome in outcomes)


def test_cedar_missing_cli_fails_closed_without_fallback(monkeypatch) -> None:
    adapter = CedarAdapter(use_reference_fallback=False)
    monkeypatch.setattr(adapter, "_cedar_cli_exists", lambda: False)

    observed = adapter.decide(build_authority_corpus()["scenarios"][0]["request"])

    assert observed.decision == "DENY"
    assert observed.reason_class == "ENGINE_UNAVAILABLE"
    assert observed.used_reference_fallback is False
    assert observed.provider_called is False


def test_cedar_payload_uses_canonical_action_metadata() -> None:
    request = next(
        scenario["request"]
        for scenario in build_authority_corpus()["scenarios"]
        if scenario["request"]["action"] == "government_application.submit"
        and scenario["description"].endswith("authorized baseline")
    )
    request = {
        **request,
        "jurisdiction": "DE",
        "human_approval": False,
        "context": {
            **request["context"],
            "authority_required": False,
            "human_approval_required": False,
            "required_jurisdiction": None,
        },
    }

    payload = _cedar_request_payload(request)
    context = payload["context"]

    assert payload["principal"] == 'Agent::"agent:austria-regulatory"'
    assert payload["action"] == 'Action::"government_application.submit"'
    assert payload["resource"] == 'Resource::"case:AT-001"'
    assert context["authority_required"] is True
    assert context["human_approval_required"] is True
    assert context["jurisdiction_valid"] is False
    assert context["human_approval"] is False


def test_real_cedar_policy_is_checked_in() -> None:
    policy = Path("labs/r3/authority/cedar/policy.cedar")
    assert policy.is_file()
    text = policy.read_text(encoding="utf-8")
    assert 'id("aios-r3-authority")' in text
    assert "context.authority_required" in text


def test_cedar_request_json_uses_entity_uid_strings() -> None:
    request = build_authority_corpus()["scenarios"][0]["request"]

    payload = _cedar_request_payload(request)

    assert isinstance(payload["principal"], str)
    assert isinstance(payload["action"], str)
    assert isinstance(payload["resource"], str)
    assert payload["principal"].startswith('Agent::"')
    assert payload["action"].startswith('Action::"')
    assert payload["resource"].startswith('Resource::"')


def test_cedar_diagnostic_fallback_does_not_count_as_provider_call() -> None:
    adapter = CedarAdapter(use_reference_fallback=True)
    observed = adapter.decide(build_authority_corpus()["scenarios"][0]["request"])

    assert observed.provider_called is False
    assert observed.used_reference_fallback is True
    assert observed.diagnostic is None

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog
from app.models.runtime_cost import RuntimeProviderCall
from app.services.llm_client import LLMProviderConfigurationError
from app.services.runtime_costs import (
    RuntimeBudgetExceeded,
    RuntimeProviderCallAlreadyRecorded,
    authorized_exposure_usd,
    configure_controlled_agent_runtime_budget,
    release_runtime_provider_call,
    reserve_runtime_provider_call,
    settle_runtime_provider_call,
)


def _configure_budget(
    session: Session,
    *,
    limit: str = "1.000000",
    reservation: str = "0.100000",
):
    budget = configure_controlled_agent_runtime_budget(
        session,
        limit_usd=Decimal(limit),
        reservation_usd_per_call=Decimal(reservation),
        status="active",
        actor="pytest-admin",
    )
    session.commit()
    session.refresh(budget)
    return budget


def _reserve(session: Session, *, call_key: str):
    return reserve_runtime_provider_call(
        session,
        call_key=call_key,
        agent_run_id=None,
        work_item_id=None,
        agent_name="sales_summary_agent",
        department="Sales",
        provider="deepseek",
        model="deepseek-chat",
        attempt_number=1,
        actor="pytest-runtime",
    )


def test_runtime_budget_reservation_is_hard_authorization_boundary(db_session: Session) -> None:
    budget = _configure_budget(db_session, limit="0.100000", reservation="0.100000")

    first = _reserve(db_session, call_key="hard-boundary:first")

    assert first.status == "reserved"
    assert first.budget_id == budget.id
    assert first.authorized_amount_usd == Decimal("0.100000")
    assert authorized_exposure_usd(db_session, budget.id) == Decimal("0.100000")

    with pytest.raises(RuntimeBudgetExceeded):
        _reserve(db_session, call_key="hard-boundary:second")

    calls = db_session.exec(select(RuntimeProviderCall)).all()
    assert len(calls) == 1
    assert authorized_exposure_usd(db_session, budget.id) == Decimal("0.100000")

    denied = db_session.exec(
        select(AuditLog).where(AuditLog.action == "runtime_budget_denied")
    ).one()
    assert denied.entity_type == "runtime_budget"


def test_budget_limit_cannot_drop_below_authorized_exposure_when_deactivated(
    db_session: Session,
) -> None:
    budget = _configure_budget(db_session, limit="0.200000", reservation="0.100000")
    _reserve(db_session, call_key="inactive-limit-floor")

    with pytest.raises(ValueError, match="below already-authorized exposure"):
        configure_controlled_agent_runtime_budget(
            db_session,
            limit_usd=Decimal("0.050000"),
            reservation_usd_per_call=Decimal("0.050000"),
            status="inactive",
            actor="pytest-admin",
        )
    db_session.rollback()

    db_session.refresh(budget)
    assert budget.limit_usd == Decimal("0.200000")
    assert budget.status == "active"


def test_observed_estimate_never_becomes_actual_cost(db_session: Session) -> None:
    _configure_budget(db_session)
    call = _reserve(db_session, call_key="estimate-only")

    settled = settle_runtime_provider_call(
        db_session,
        call_id=call.id,
        prompt_tokens=100,
        completion_tokens=20,
        total_tokens=120,
        estimated_cost_usd=Decimal("0.001234"),
        actual_cost_usd=None,
        billing_evidence=False,
        actor="pytest-runtime",
    )

    assert settled.status == "observed"
    assert settled.prompt_tokens == 100
    assert settled.total_tokens == 120
    assert settled.estimated_cost_usd == Decimal("0.001234")
    assert settled.actual_cost_usd is None
    assert settled.billing_evidence is False


def test_actual_cost_requires_billing_evidence(db_session: Session) -> None:
    _configure_budget(db_session)
    call = _reserve(db_session, call_key="actual-needs-evidence")

    with pytest.raises(ValueError, match="requires real billing evidence"):
        settle_runtime_provider_call(
            db_session,
            call_id=call.id,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            estimated_cost_usd=Decimal("0.000100"),
            actual_cost_usd=Decimal("0.000090"),
            billing_evidence=False,
            actor="pytest-runtime",
        )
    db_session.rollback()

    persisted = db_session.get(RuntimeProviderCall, call.id)
    assert persisted is not None
    assert persisted.status == "reserved"
    assert persisted.actual_cost_usd is None


def test_pre_boundary_configuration_failure_releases_reservation(db_session: Session) -> None:
    budget = _configure_budget(db_session, limit="0.100000", reservation="0.100000")
    call = _reserve(db_session, call_key="pre-boundary-release")

    released = release_runtime_provider_call(
        db_session,
        call_id=call.id,
        error=LLMProviderConfigurationError("provider configuration unavailable"),
        actor="pytest-runtime",
    )

    assert released.status == "released"
    assert authorized_exposure_usd(db_session, budget.id) == Decimal("0.000000")


def test_missing_budget_blocks_paid_provider_before_external_call(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_calls = {"count": 0}

    class FakeProvider:
        name = "deepseek"
        default_model = "deepseek-chat"

        def complete(self, **kwargs):
            provider_calls["count"] += 1
            raise AssertionError("provider.complete must not run without an active budget")

    monkeypatch.setattr("app.services.controlled_agents._should_use_llm", lambda: True)
    monkeypatch.setattr(
        "app.services.controlled_agents.LLMProviderFactory.get_provider",
        lambda: FakeProvider(),
    )

    response = client.post(
        "/api/v1/controlled-agents/run",
        json={
            "agent_name": "sales_summary_agent",
            "task": "Do not cross the paid boundary without allocation.",
            "context": {},
            "actor": "pytest-runtime",
        },
    )

    assert response.status_code == 200, response.text
    assert provider_calls["count"] == 0
    assert response.json()["output"]["_llm_meta"]["fallback_to_template"] is True

    missing = db_session.exec(
        select(AuditLog).where(AuditLog.action == "runtime_budget_missing")
    ).one()
    assert missing.source == "phase_16_runtime_budget"
    assert db_session.exec(select(RuntimeProviderCall)).all() == []


def test_runtime_budget_api_requires_admin_and_reports_remaining_allocation(
    raw_client: TestClient,
) -> None:
    payload = {
        "limit_usd": "1.000000",
        "reservation_usd_per_call": "0.250000",
        "status": "active",
    }

    raw_client.headers.update(
        {"X-GMAI-Role": "operator", "X-GMAI-User": "pytest-operator"}
    )
    forbidden = raw_client.put("/api/v1/controlled-agents/runtime-budget", json=payload)
    assert forbidden.status_code == 403

    raw_client.headers.update(
        {"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-admin"}
    )
    configured = raw_client.put("/api/v1/controlled-agents/runtime-budget", json=payload)
    assert configured.status_code == 200, configured.text
    body = configured.json()
    assert body["configured"] is True
    assert Decimal(str(body["limit_usd"])) == Decimal("1.0")
    assert Decimal(str(body["reservation_usd_per_call"])) == Decimal("0.25")
    assert Decimal(str(body["remaining_authorized_usd"])) == Decimal("1.0")

    fetched = raw_client.get("/api/v1/controlled-agents/runtime-budget")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "active"


def test_runtime_provider_call_key_is_unique(db_session: Session) -> None:
    _configure_budget(db_session)
    _reserve(db_session, call_key="stable-attempt-key")

    with pytest.raises(RuntimeProviderCallAlreadyRecorded):
        _reserve(db_session, call_key="stable-attempt-key")

    assert len(db_session.exec(select(RuntimeProviderCall)).all()) == 1

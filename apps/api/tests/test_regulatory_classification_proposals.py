from __future__ import annotations

import json
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import AuditLog, RegulatoryChange, RegulatoryClassificationProposal
from app.services.llm_client import LLMProviderFactory


def _create_changed_source(client: TestClient) -> tuple[str, str]:
    onboarded = client.post(
        "/api/v1/regulatory-intelligence/source-onboarding",
        json={
            "jurisdiction_code": "AT",
            "jurisdiction_name": "Austria",
            "jurisdiction_type": "country",
            "region": "Europe",
            "authority_name": "Federal immigration authority test fixture",
            "authority_website_url": "https://www.bmi.gv.at/",
            "source_name": "Skilled permit rules test fixture",
            "source_url": "https://www.bmi.gv.at/example-skilled-permit-rules",
            "source_domain": "visa",
            "source_type": "government",
            "allowed_domains": ["bmi.gv.at"],
        },
    )
    assert onboarded.status_code == 201
    source_id = onboarded.json()["official_source"]["id"]
    baseline = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source_id}/snapshots",
        json={"content_text": "The minimum salary requirement is EUR 40,000."},
    )
    assert baseline.status_code == 201
    changed = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source_id}/snapshots",
        json={"content_text": "The minimum salary requirement is EUR 45,000."},
    )
    assert changed.status_code == 201
    return changed.json()["change"]["id"], changed.json()["classification_proposal"]["id"]


def test_deterministic_proposal_is_evidence_bound_and_review_gated(
    client: TestClient,
    db_session: Session,
) -> None:
    change_id, proposal_id = _create_changed_source(client)

    listed = client.get(
        "/api/v1/regulatory-intelligence/classification-proposals",
        params={"change_id": change_id},
    )
    assert listed.status_code == 200
    proposal = listed.json()["classification_proposals"][0]
    assert proposal["id"] == proposal_id
    assert proposal["method"] == "deterministic"
    assert proposal["proposed_change_type"] == "salary_threshold_change"
    assert proposal["previous_snapshot_id"]
    assert proposal["current_snapshot_id"]
    assert proposal["evidence"]
    assert all(row["line_number"] > 0 and row["text"] for row in proposal["evidence"])

    rejected = client.post(
        f"/api/v1/regulatory-intelligence/classification-proposals/{proposal_id}/review",
        json={
            "decision": "rejected",
            "reviewer": "classification-reviewer",
            "notes": "Generate a revised proposal before regulatory review.",
        },
    )
    assert rejected.status_code == 200
    blocked = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change_id}/review",
        json={
            "decision": "approved",
            "reviewer": "regulatory-reviewer",
            "notes": "Classification has not been accepted.",
        },
    )
    assert blocked.status_code == 400
    assert "accepted classification proposal" in blocked.json()["detail"].lower()

    regenerated = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change_id}/classification-proposals",
        json={"use_model": False, "actor": "classification-operator"},
    )
    assert regenerated.status_code == 201
    accepted = client.post(
        f"/api/v1/regulatory-intelligence/classification-proposals/{regenerated.json()['classification_proposal']['id']}/review",
        json={
            "decision": "accepted",
            "reviewer": "classification-reviewer",
            "notes": "The new and old salary lines support the category.",
        },
    )
    assert accepted.status_code == 200
    change = db_session.get(RegulatoryChange, UUID(change_id))
    assert change is not None
    assert change.change_type == "salary_threshold_change"
    audit_actions = {row.action for row in db_session.exec(select(AuditLog)).all()}
    assert "regulatory_classification_proposed" in audit_actions
    assert "regulatory_classification_reviewed" in audit_actions


def test_model_assisted_proposal_validates_citations_and_preserves_fallback(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    change_id, original_proposal_id = _create_changed_source(client)

    class FakeProvider:
        def complete(self, **_kwargs):
            return SimpleNamespace(
                content=json.dumps({
                    "change_type": "salary_threshold_change",
                    "materiality": "critical",
                    "summary": "The official-source salary threshold increased from EUR 40,000 to EUR 45,000.",
                    "rationale": "The removed and added lines contain different salary amounts.",
                    "confidence": 0.98,
                    "evidence_line_numbers": [4, 5],
                }),
                provider="fake-regulatory-provider",
                model="fake-classifier-v1",
                finish_reason="stop",
                prompt_tokens=120,
                completion_tokens=60,
                total_tokens=180,
                estimated_cost_usd=0.001,
            )

    monkeypatch.setattr(settings, "regulatory_model_classification_enabled", True)
    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(LLMProviderFactory, "get_provider", classmethod(lambda cls: FakeProvider()))

    generated = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change_id}/classification-proposals",
        json={"use_model": True, "actor": "model-classification-operator"},
    )
    assert generated.status_code == 201
    proposal = generated.json()["classification_proposal"]
    assert proposal["method"] == "model_assisted"
    assert proposal["provider"] == "fake-regulatory-provider"
    assert proposal["model"] == "fake-classifier-v1"
    assert proposal["confidence"] == 0.95
    assert proposal["proposed_materiality"] == "critical"
    assert proposal["fallback_reason"] is None
    assert {row["line_number"] for row in proposal["evidence"]} == {4, 5}

    original = db_session.get(RegulatoryClassificationProposal, UUID(original_proposal_id))
    assert original is not None
    assert original.status == "superseded"


def test_invalid_model_output_falls_back_without_blocking_pipeline(
    client: TestClient,
    monkeypatch,
) -> None:
    change_id, _ = _create_changed_source(client)

    class InvalidProvider:
        def complete(self, **_kwargs):
            return SimpleNamespace(content="not-json")

    monkeypatch.setattr(settings, "regulatory_model_classification_enabled", True)
    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(LLMProviderFactory, "get_provider", classmethod(lambda cls: InvalidProvider()))

    generated = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change_id}/classification-proposals",
        json={"use_model": True, "actor": "model-classification-operator"},
    )
    assert generated.status_code == 201
    proposal = generated.json()["classification_proposal"]
    assert proposal["method"] == "deterministic"
    assert "deterministic fallback used" in proposal["fallback_reason"].lower()
    assert proposal["evidence"]

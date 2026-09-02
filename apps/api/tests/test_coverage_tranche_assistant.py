from __future__ import annotations

from unittest.mock import patch

from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import InitialRuleAssertion, SourceRetrievalRun, SourceSnapshot
from app.schemas import CoverageTrancheAssistantPrepareRequest
from app.services.coverage_evidence_batches import coverage_batch_payload, create_coverage_evidence_batch
from app.services.coverage_tranche_assistant import (
    coverage_tranche_assistant_config,
    prepare_coverage_tranche,
)
from app.services.jurisdiction_registry import (
    import_un_m49_registry,
    review_immigration_assessment,
    review_source_certification,
)


SAMPLE_M49 = """
<html><table id="downloadTableEN"><tbody>
<tr><td>001</td><td>World</td><td>142</td><td>Asia</td><td>034</td><td>Southern Asia</td><td></td><td></td><td>Afghanistan</td><td>004</td><td>AF</td><td>AFG</td></tr>
<tr><td>001</td><td>World</td><td>142</td><td>Asia</td><td>145</td><td>Western Asia</td><td></td><td></td><td>State of Palestine</td><td>275</td><td>PS</td><td>PSE</td></tr>
</tbody></table></html>
"""


def _source_item(code: str, name: str) -> dict:
    host = f"{code.lower()}.official.example"
    return {
        "alpha2_code": code,
        "source_onboarding": {
            "authority_name": f"{name} Immigration Authority",
            "authority_type": "immigration_authority",
            "authority_website_url": f"https://{host}/immigration",
            "authority_domains": ["visa"],
            "source_name": f"{name} official immigration portal",
            "source_url": f"https://{host}/immigration",
            "source_domain": "visa",
            "source_type": "government",
            "schedule_minutes": 1440,
            "fetch_method": "http",
            "allowed_domains": [host],
            "max_redirects": 3,
            "parser_profile": "generic",
            "parser_config": {},
            "certification_domains": ["visa"],
            "evidence_notes": "Official authority ownership and primary immigration scope require independent review.",
        },
        "immigration_assessment": {
            "rule_relationship": "independent",
            "parent_code": None,
            "evidence_url": f"https://{host}/immigration/framework",
            "evidence_title": "Official immigration framework",
            "rationale": "Official evidence identifies the directly administering immigration authority.",
        },
    }


def _batch(session: Session):
    import_un_m49_registry(
        session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )
    batch, _ = create_coverage_evidence_batch(
        session,
        name="Tranche assistant test batch",
        notes="Two-jurisdiction official-source package for safe tranche assistant testing.",
        items=[_source_item("AF", "Afghanistan"), _source_item("PS", "Palestine")],
        actor="coverage-proposer",
    )
    return batch


def _approve(session: Session, batch, code: str):
    item = next(row for row in coverage_batch_payload(session, batch)["items"] if row["alpha2_code"] == code)
    review_immigration_assessment(
        session,
        assessment_id=item["immigration_assessment"]["id"],
        decision="approved",
        notes="Official relationship evidence independently reviewed.",
        actor="coverage-reviewer",
    )
    review_source_certification(
        session,
        certification_id=item["source_certification"]["id"],
        decision="approved",
        notes="Official source ownership and primary scope independently reviewed.",
        actor="coverage-reviewer",
    )
    return next(row for row in coverage_batch_payload(session, batch)["items"] if row["alpha2_code"] == code)


def _baseline(session: Session, item: dict, content: str) -> SourceSnapshot:
    snapshot = SourceSnapshot(
        official_source_id=item["source_onboarding"]["official_source_id"],
        previous_snapshot_id=None,
        url=item["source_onboarding"]["source_url"],
        content_hash=("a" if item["alpha2_code"] == "AF" else "b") * 64,
        content_text=content,
        http_status=200,
        retrieval_method="http",
        parser_version="generic-v1",
        status="baseline",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def test_assistant_is_disabled_by_default(db_session: Session) -> None:
    batch = _batch(db_session)
    config = coverage_tranche_assistant_config()
    assert config["enabled"] is False
    payload = CoverageTrancheAssistantPrepareRequest(alpha2_codes=["AF"])
    try:
        prepare_coverage_tranche(
            db_session,
            batch_id=batch.id,
            payload=payload,
            actor="assistant-operator",
        )
    except PermissionError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("Disabled tranche assistant must not run")


def test_dry_run_prepares_constrained_draft_without_database_mutation(
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "coverage_tranche_assistant_enabled", True)
    batch = _batch(db_session)
    item = _approve(db_session, batch, "AF")
    snapshot = _baseline(
        db_session,
        item,
        """Visa & Service\nNavigation\nVisa Navigator\nConsular Services Portal: Apply for visas online\nVisa information\nResidence permit guidance for qualified workers.\nFooter""",
    )
    payload = CoverageTrancheAssistantPrepareRequest(
        alpha2_codes=["af"],
        dry_run=True,
        queue_eligible_baselines=True,
    )
    result = prepare_coverage_tranche(
        db_session,
        batch_id=batch.id,
        payload=payload,
        actor="assistant-operator",
    )
    assert result["dry_run"] is True
    assert result["queued_baselines"] == 0
    assert result["selected_codes"] == ["AF"]
    prepared = result["items"][0]
    assert prepared["stage"] == "baseline_ready_needs_assertion"
    assert prepared["snapshot_analysis"]["snapshot_id"] == snapshot.id
    assert prepared["snapshot_analysis"]["classification"] == "suitable_for_narrow_draft"
    assert "Apply for visas online" in prepared["candidate_assertion"]["evidence_excerpt"]
    assert prepared["candidate_assertion"]["creates_pending_assertion"] is False
    assert db_session.exec(select(InitialRuleAssertion)).all() == []
    assert db_session.exec(select(SourceRetrievalRun)).all() == []


def test_navigation_only_snapshot_is_rejected_for_candidate_drafting(
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "coverage_tranche_assistant_enabled", True)
    batch = _batch(db_session)
    item = _approve(db_session, batch, "AF")
    _baseline(
        db_session,
        item,
        "Navigation\nMain menu\nSearch\nAbout us\nBack to the first navigation level\nFooter\nData privacy",
    )
    result = prepare_coverage_tranche(
        db_session,
        batch_id=batch.id,
        payload=CoverageTrancheAssistantPrepareRequest(alpha2_codes=["AF"]),
        actor="assistant-operator",
    )
    prepared = result["items"][0]
    assert prepared["snapshot_analysis"]["classification"] in {
        "navigation_heavy",
        "insufficient_substantive_text",
    }
    assert prepared["candidate_assertion"] is None


def test_apply_mode_queues_only_explicitly_selected_jurisdiction(
    db_session: Session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "coverage_tranche_assistant_enabled", True)
    batch = _batch(db_session)
    af = _approve(db_session, batch, "AF")
    _approve(db_session, batch, "PS")

    with patch("app.tasks.source_monitor_tasks.run_source_monitor_task.delay") as delay:
        result = prepare_coverage_tranche(
            db_session,
            batch_id=batch.id,
            payload=CoverageTrancheAssistantPrepareRequest(
                alpha2_codes=["AF"],
                dry_run=False,
                queue_eligible_baselines=True,
            ),
            actor="assistant-operator",
        )

    assert result["would_queue_baselines"] == ["AF"]
    assert result["queued_baselines"] == 1
    runs = db_session.exec(select(SourceRetrievalRun)).all()
    assert len(runs) == 1
    assert runs[0].official_source_id == af["source_onboarding"]["official_source_id"]
    delay.assert_called_once()


def test_assistant_api_is_feature_flagged_and_read_only_by_default(client, db_session: Session, monkeypatch) -> None:
    batch = _batch(db_session)
    config = client.get("/api/v1/global-intelligence/registry/coverage-tranche-assistant/config")
    assert config.status_code == 200
    assert config.json()["enabled"] is False

    disabled = client.post(
        f"/api/v1/global-intelligence/registry/coverage-batches/{batch.id}/assistant/prepare",
        json={"alpha2_codes": ["AF"]},
    )
    assert disabled.status_code == 403

    monkeypatch.setattr(settings, "coverage_tranche_assistant_enabled", True)
    enabled = client.post(
        f"/api/v1/global-intelligence/registry/coverage-batches/{batch.id}/assistant/prepare",
        json={"alpha2_codes": ["AF"], "dry_run": True},
    )
    assert enabled.status_code == 200, enabled.text
    assert enabled.json()["dry_run"] is True
    assert enabled.json()["safety"]["creates_assertions"] is False

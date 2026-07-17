from __future__ import annotations

import socket
from unittest.mock import patch

import httpx
from sqlmodel import Session, select

from app.models.domain import SourceRetrievalRun, SourceSnapshot
from app.services.coverage_baseline_capture import (
    coverage_batch_baseline_status,
    queue_coverage_batch_baselines,
)
from app.services.coverage_evidence_batches import coverage_batch_payload, create_coverage_evidence_batch
from app.services.jurisdiction_registry import (
    import_un_m49_registry,
    review_immigration_assessment,
    review_source_certification,
)
from app.services.source_retrieval import execute_source_monitor


SAMPLE_M49 = """
<html><table id="downloadTableEN"><tbody>
<tr><td>001</td><td>World</td><td>142</td><td>Asia</td><td>034</td><td>Southern Asia</td><td></td><td></td><td>Afghanistan</td><td>004</td><td>AF</td><td>AFG</td></tr>
<tr><td>001</td><td>World</td><td>142</td><td>Asia</td><td>145</td><td>Western Asia</td><td></td><td></td><td>State of Palestine</td><td>275</td><td>PS</td><td>PSE</td></tr>
</tbody></table></html>
"""


def _public_resolver(host: str, port: int, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


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
        name="Approved baseline capture batch",
        notes="Official source onboarding and review package for baseline capture testing.",
        items=[
            {
                "alpha2_code": "AF",
                "source_onboarding": {
                    "authority_name": "Afghanistan Immigration Authority",
                    "authority_type": "immigration_authority",
                    "authority_website_url": "https://official.example/immigration",
                    "authority_domains": ["visa"],
                    "source_name": "Afghanistan official immigration portal",
                    "source_url": "https://official.example/immigration",
                    "source_domain": "visa",
                    "source_type": "government",
                    "schedule_minutes": 1440,
                    "fetch_method": "http",
                    "allowed_domains": ["official.example"],
                    "max_redirects": 3,
                    "parser_profile": "generic",
                    "parser_config": {},
                    "certification_domains": ["visa"],
                    "evidence_notes": "Official authority ownership and primary immigration scope require independent review.",
                },
                "immigration_assessment": {
                    "rule_relationship": "independent",
                    "parent_code": None,
                    "evidence_url": "https://official.example/immigration/framework",
                    "evidence_title": "Official immigration framework",
                    "rationale": "Official evidence identifies the directly administering immigration authority.",
                },
            }
        ],
        actor="coverage-proposer",
    )
    return batch


def _approve(session: Session, batch) -> dict:
    payload = coverage_batch_payload(session, batch)
    item = payload["items"][0]
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
    return coverage_batch_payload(session, batch)["items"][0]


def test_baseline_capture_requires_completed_independent_review(db_session: Session) -> None:
    batch = _batch(db_session)
    pending = coverage_batch_baseline_status(db_session, batch.id)
    assert pending["pending_review"] == 1
    assert pending["eligible_to_queue"] == 0

    with patch("app.tasks.source_monitor_tasks.run_source_monitor_task.delay") as delay:
        result = queue_coverage_batch_baselines(
            db_session,
            batch_id=batch.id,
            actor="baseline-operator",
        )
    assert result["queued"] == 0
    assert result["pending_review"] == 1
    delay.assert_not_called()
    assert db_session.exec(select(SourceRetrievalRun)).all() == []


def test_approved_batch_queues_one_idempotent_run_and_captures_baseline(db_session: Session) -> None:
    batch = _batch(db_session)
    item = _approve(db_session, batch)

    ready = coverage_batch_baseline_status(db_session, batch.id)
    assert ready["eligible_to_queue"] == 1
    assert ready["items"][0]["state"] == "ready_to_queue"

    with patch("app.tasks.source_monitor_tasks.run_source_monitor_task.delay") as delay:
        queued = queue_coverage_batch_baselines(
            db_session,
            batch_id=batch.id,
            actor="baseline-operator",
        )
        repeated = queue_coverage_batch_baselines(
            db_session,
            batch_id=batch.id,
            actor="baseline-operator",
        )

    assert queued["queued"] == 1
    assert repeated["queued"] == 0
    delay.assert_called_once()
    runs = db_session.exec(select(SourceRetrievalRun)).all()
    assert len(runs) == 1
    run = runs[0]
    assert run.status == "queued"
    delay.assert_called_once_with(str(item["source_onboarding"]["source_monitor_id"]), str(run.id))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8", "etag": '"baseline-v1"'},
            content=b"<html><body><main><h1>Official immigration guidance</h1><p>Residence and visa information.</p></main></body></html>",
        )

    completed = execute_source_monitor(
        db_session,
        run.monitor_id,
        retrieval_run_id=run.id,
        transport=httpx.MockTransport(handler),
        resolver=_public_resolver,
    )
    assert completed.id == run.id
    assert completed.status == "baseline"
    assert completed.snapshot_id is not None
    assert len(db_session.exec(select(SourceSnapshot)).all()) == 1

    final = coverage_batch_baseline_status(db_session, batch.id)
    assert final["baseline_ready"] == 1
    assert final["eligible_to_queue"] == 0
    assert final["items"][0]["latest_snapshot"]["id"] == completed.snapshot_id


def test_baseline_capture_api_exposes_status_and_queues_approved_source(client, db_session: Session) -> None:
    batch = _batch(db_session)
    _approve(db_session, batch)

    status = client.get(
        f"/api/v1/global-intelligence/registry/coverage-batches/{batch.id}/baseline-status"
    )
    assert status.status_code == 200
    assert status.json()["eligible_to_queue"] == 1
    assert status.json()["safety"]["publishes_verified_rule"] is False

    with patch("app.tasks.source_monitor_tasks.run_source_monitor_task.delay") as delay:
        response = client.post(
            f"/api/v1/global-intelligence/registry/coverage-batches/{batch.id}/capture-baselines"
        )
    assert response.status_code == 202
    assert response.json()["queued"] == 1
    delay.assert_called_once()

from __future__ import annotations

import json
import socket
from datetime import timedelta
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    HumanReview,
    OfficialSource,
    RegulatoryChange,
    SourceMonitor,
    SourceRetrievalRun,
    SourceSnapshot,
    now_utc,
)
from app.services.source_retrieval import FetchResult, execute_source_monitor, parse_source_content
from app.tasks.source_monitor_tasks import enqueue_due_source_monitors
from app.core.config import settings


def _public_resolver(host: str, port: int, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


def _source_and_monitor(
    session: Session,
    *,
    url: str = "https://official.example/policy",
    allowed_domains: list[str] | None = None,
    parser_profile: str = "generic",
    parser_config: dict | None = None,
) -> tuple[OfficialSource, SourceMonitor]:
    source = OfficialSource(
        country="testland",
        domain="visa",
        name="Testland Immigration Authority",
        url=url,
        source_type="government",
    )
    session.add(source)
    session.flush()
    monitor = SourceMonitor(
        official_source_id=source.id,
        schedule_minutes=60,
        fetch_method="http",
        allowed_domains_json=json.dumps(allowed_domains or ["official.example"]),
        max_redirects=2,
        parser_profile=parser_profile,
        parser_config_json=json.dumps(parser_config) if parser_config else None,
        next_check_at=now_utc(),
    )
    session.add(monitor)
    session.commit()
    session.refresh(source)
    session.refresh(monitor)
    return source, monitor


def test_gazette_profile_removes_navigation_and_prefers_article_content() -> None:
    parsed = parse_source_content(
        FetchResult(
            status_code=200,
            final_url="https://gazette.example/notices/1",
            content_type="text/html; charset=utf-8",
            content=b"<html><body><nav>Menu</nav><main><article><h1>Official notice</h1><p>Program opened.</p></article></main><footer>Footer</footer></body></html>",
            etag=None,
            last_modified=None,
        ),
        profile="gazette_html_v1",
    )
    assert parsed.parser_version == "gazette-html-v1"
    assert "Official notice" in parsed.text
    assert "Menu" not in parsed.text
    assert "Footer" not in parsed.text


def test_structured_program_catalog_detects_new_and_retired_programs(
    db_session: Session,
) -> None:
    _, monitor = _source_and_monitor(
        db_session,
        parser_profile="structured_program_catalog_v1",
        parser_config={
            "records_path": "data.programs",
            "id_field": "code",
            "name_field": "label",
            "status_field": "state",
            "summary_field": "description",
        },
    )
    responses = [
        {
            "data": {
                "programs": [
                    {"code": "skilled-work", "label": "Skilled Work Visa", "state": "active", "description": "Initial program"},
                ],
            },
        },
        {
            "data": {
                "programs": [
                    {"code": "skilled-work", "label": "Skilled Work Visa", "state": "closed", "description": "Program closed"},
                    {"code": "talent", "label": "Global Talent Visa", "state": "active", "description": "New talent route"},
                ],
            },
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "application/json"}, json=responses.pop(0))

    transport = httpx.MockTransport(handler)
    first = execute_source_monitor(db_session, monitor.id, transport=transport, resolver=_public_resolver)
    second = execute_source_monitor(db_session, monitor.id, transport=transport, resolver=_public_resolver)
    assert first.status == "baseline"
    assert second.status == "changed"

    changes = db_session.exec(select(RegulatoryChange).order_by(RegulatoryChange.title)).all()
    assert len(changes) == 2
    assert {change.change_type for change in changes} == {"new_program", "program_removed"}
    assert all(change.status == "pending_review" for change in changes)
    assert len(db_session.exec(select(HumanReview)).all()) == 2
    snapshot = db_session.get(SourceSnapshot, second.snapshot_id)
    assert snapshot is not None
    metadata = json.loads(snapshot.metadata_json or "{}")
    assert metadata["parser_profile"] == "structured_program_catalog_v1"
    assert len(metadata["program_catalog"]) == 2


def test_worker_captures_html_and_uses_conditional_request(
    db_session: Session,
) -> None:
    source, monitor = _source_and_monitor(db_session)
    seen_headers: list[httpx.Headers] = []

    def baseline_handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8", "etag": '"policy-v1"'},
            content=b"<html><style>hidden</style><body><h1>Visa policy</h1><p>Minimum salary EUR 40,000.</p></body></html>",
        )

    first = execute_source_monitor(
        db_session,
        monitor.id,
        transport=httpx.MockTransport(baseline_handler),
        resolver=_public_resolver,
    )
    assert first.status == "baseline"
    assert first.bytes_received > 0
    snapshot = db_session.get(SourceSnapshot, first.snapshot_id)
    assert snapshot is not None
    assert "Visa policy" in (snapshot.content_text or "")
    assert "hidden" not in (snapshot.content_text or "")
    db_session.refresh(monitor)
    assert monitor.etag == '"policy-v1"'
    assert "if-none-match" not in seen_headers[0]

    def not_modified_handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return httpx.Response(304, headers={"etag": '"policy-v1"'})

    second = execute_source_monitor(
        db_session,
        monitor.id,
        transport=httpx.MockTransport(not_modified_handler),
        resolver=_public_resolver,
    )
    assert second.status == "not_modified"
    assert seen_headers[1]["if-none-match"] == '"policy-v1"'
    assert len(db_session.exec(select(SourceSnapshot)).all()) == 1


def test_source_fetch_pins_public_address_and_preserves_official_identity(
    db_session: Session,
) -> None:
    _, monitor = _source_and_monitor(
        db_session, url="https://official.example/policy?edition=2",
    )
    requests: list[httpx.Request] = []
    resolutions: list[tuple[str, int]] = []

    def resolver(host: str, port: int, **kwargs):
        resolutions.append((host, port))
        return _public_resolver(host, port, **kwargs)

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/plain"}, text="Official policy")

    with patch("app.services.source_retrieval.httpx.Client", wraps=httpx.Client) as client_cls:
        run = execute_source_monitor(
            db_session, monitor.id,
            transport=httpx.MockTransport(handler), resolver=resolver,
        )

    assert run.status == "baseline"
    assert run.final_url == "https://official.example/policy?edition=2"
    assert resolutions == [("official.example", 443)]
    assert len(requests) == 1
    assert str(requests[0].url) == "https://93.184.216.34/policy?edition=2"
    assert requests[0].headers["host"] == "official.example"
    assert requests[0].extensions["sni_hostname"] == "official.example"
    assert client_cls.call_args.kwargs["trust_env"] is False
    assert client_cls.call_args.kwargs["follow_redirects"] is False


def test_source_redirect_revalidates_and_pins_each_public_host(db_session: Session) -> None:
    _, monitor = _source_and_monitor(db_session)
    requests: list[httpx.Request] = []

    def resolver(host: str, port: int, **kwargs):
        address = "93.184.216.34" if host == "official.example" else "93.184.216.35"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(302, headers={"location": "https://notices.official.example/update"})
        return httpx.Response(200, headers={"content-type": "text/plain"}, text="New policy")

    run = execute_source_monitor(
        db_session, monitor.id,
        transport=httpx.MockTransport(handler), resolver=resolver,
    )
    assert run.status == "baseline"
    assert run.final_url == "https://notices.official.example/update"
    assert [str(request.url) for request in requests] == [
        "https://93.184.216.34/policy",
        "https://93.184.216.35/update",
    ]
    assert [request.headers["host"] for request in requests] == [
        "official.example", "notices.official.example",
    ]
    assert [request.extensions["sni_hostname"] for request in requests] == [
        "official.example", "notices.official.example",
    ]


def test_explicitly_enabled_http_source_is_also_pinned(
    db_session: Session, monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "source_monitor_allow_http", True)
    _, monitor = _source_and_monitor(db_session, url="http://official.example/policy")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/plain"}, text="Public notice")

    run = execute_source_monitor(
        db_session, monitor.id,
        transport=httpx.MockTransport(handler), resolver=_public_resolver,
    )
    assert run.status == "baseline"
    assert run.final_url == "http://official.example/policy"
    assert str(requests[0].url) == "http://93.184.216.34/policy"
    assert requests[0].headers["host"] == "official.example"
    assert "sni_hostname" not in requests[0].extensions


def test_worker_blocks_private_addresses_without_making_request(db_session: Session) -> None:
    _, monitor = _source_and_monitor(
        db_session,
        url="https://private.official.example/policy",
        allowed_domains=["official.example"],
    )
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, headers={"content-type": "text/plain"}, text="unsafe")

    def private_resolver(host: str, port: int, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

    run = execute_source_monitor(
        db_session,
        monitor.id,
        transport=httpx.MockTransport(handler),
        resolver=private_resolver,
    )
    assert run.status == "failed"
    assert run.error_code == "private_address_blocked"
    assert called is False
    db_session.refresh(monitor)
    assert monitor.status == "error"
    assert monitor.last_error


def test_worker_blocks_mixed_public_and_private_answers_before_request(db_session: Session) -> None:
    _, monitor = _source_and_monitor(db_session)
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, headers={"content-type": "text/plain"}, text="unsafe")

    def mixed_resolver(host: str, port: int, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", port)),
        ]

    run = execute_source_monitor(
        db_session, monitor.id,
        transport=httpx.MockTransport(handler), resolver=mixed_resolver,
    )
    assert run.status == "failed"
    assert run.error_code == "private_address_blocked"
    assert called is False


def test_worker_blocks_redirect_outside_allowlist(db_session: Session) -> None:
    _, monitor = _source_and_monitor(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://evil.example/collect"})

    run = execute_source_monitor(
        db_session,
        monitor.id,
        transport=httpx.MockTransport(handler),
        resolver=_public_resolver,
    )
    assert run.status == "failed"
    assert run.error_code == "domain_not_allowed"


def test_worker_enforces_response_size_limit(db_session: Session, monkeypatch) -> None:
    _, monitor = _source_and_monitor(db_session)
    monkeypatch.setattr(settings, "source_monitor_max_bytes", 10)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/plain", "content-length": "100"},
            content=b"x" * 100,
        )

    run = execute_source_monitor(
        db_session,
        monitor.id,
        transport=httpx.MockTransport(handler),
        resolver=_public_resolver,
    )
    assert run.status == "failed"
    assert run.error_code == "response_too_large"


def test_due_monitor_scheduler_leases_and_enqueues(db_session: Session) -> None:
    _, monitor = _source_and_monitor(db_session)
    monitor.next_check_at = now_utc() - timedelta(minutes=1)
    db_session.add(monitor)
    db_session.commit()

    with patch("app.tasks.source_monitor_tasks.run_source_monitor_task.delay") as delay:
        result = enqueue_due_source_monitors.run(limit=10)

    assert result["queued"] == 1
    assert result["monitor_ids"] == [str(monitor.id)]
    delay.assert_called_once_with(str(monitor.id))
    db_session.refresh(monitor)
    assert monitor.next_check_at is not None
    assert monitor.next_check_at > now_utc().replace(tzinfo=None)


def test_monitor_run_api_enqueues_worker(client: TestClient, db_session: Session) -> None:
    _, monitor = _source_and_monitor(db_session)
    with patch("app.routers.official_sources.run_source_monitor_task.delay") as delay:
        delay.return_value.id = "task-123"
        response = client.post(f"/api/v1/regulatory-intelligence/source-monitors/{monitor.id}/run")
    assert response.status_code == 202
    assert response.json()["task_id"] == "task-123"
    delay.assert_called_once_with(str(monitor.id))

    listing = client.get(
        "/api/v1/regulatory-intelligence/retrieval-runs",
        params={"monitor_id": str(monitor.id)},
    )
    assert listing.status_code == 200
    assert listing.json()["total_returned"] == 0


def test_retrieval_runs_record_failures(db_session: Session) -> None:
    _, monitor = _source_and_monitor(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, headers={"content-type": "text/plain"}, text="unavailable")

    run = execute_source_monitor(
        db_session,
        monitor.id,
        transport=httpx.MockTransport(handler),
        resolver=_public_resolver,
    )
    persisted = db_session.exec(select(SourceRetrievalRun).where(SourceRetrievalRun.id == run.id)).one()
    assert persisted.status == "failed"
    assert persisted.http_status is None
    assert persisted.error_code == "http_error"

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import CountryPolicy, OfficialSource, SourceCheckRun, SourceSnapshot, TruthClaim
from app.services import official_sources as official_sources_service


def test_registry_path_resolves_compose_knowledge_mount_without_fixed_parent_depth(
    monkeypatch,
) -> None:
    mounted_registry = Path("/knowledge/official_sources/sources.yaml")
    monkeypatch.setattr(
        official_sources_service,
        "__file__",
        "/app/app/services/official_sources.py",
    )
    monkeypatch.setattr(Path, "exists", lambda candidate: candidate == mounted_registry)

    assert official_sources_service.registry_path() == mounted_registry


def test_official_source_seed_is_idempotent(client: TestClient, db_session: Session) -> None:
    first = client.post("/api/v1/official-sources/seed")
    second = client.post("/api/v1/official-sources/seed")

    assert first.status_code == 200
    assert second.status_code == 200

    germany_sources = db_session.exec(
        select(OfficialSource).where(OfficialSource.country == "germany")
    ).all()
    germany_urls = {source.url for source in germany_sources}
    policies = db_session.exec(select(CountryPolicy)).all()

    assert "https://www.auswaertiges-amt.de/" in germany_urls
    assert len(germany_urls) == len(germany_sources)
    assert any(policy.country == "germany" and policy.domain == "visa" for policy in policies)

    response = client.get("/api/v1/official-sources", params={"country": "Germany", "domain": "visa"})
    assert response.status_code == 200
    assert response.json()["total"] == len(germany_sources)


def test_truth_verify_records_source_check_run(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/truth/verify",
        json={
            "claim": "Germany student visa applicants should check official financial proof requirements.",
            "domain": "visa",
            "country": "Germany",
            "source_urls": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["official_sources"]

    claim = db_session.exec(select(TruthClaim)).first()
    assert claim is not None

    check_run = db_session.exec(select(SourceCheckRun)).first()
    assert check_run is not None
    assert check_run.truth_claim_id == claim.id
    assert check_run.country == "germany"
    assert check_run.domain == "visa"
    assert check_run.evidence_count >= 1

    snapshot = db_session.exec(select(SourceSnapshot)).first()
    assert snapshot is not None
    assert snapshot.status == "referenced"

    check_response = client.get("/api/v1/official-sources/check-runs")
    assert check_response.status_code == 200
    assert check_response.json()["total_returned"] == 1


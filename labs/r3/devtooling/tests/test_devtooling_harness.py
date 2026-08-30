from __future__ import annotations

from labs.r3.devtooling.prepare_packet import build_packet


def test_dev_model_packet_is_provider_neutral() -> None:
    packet = build_packet()

    assert packet["contract_version"] == "gmai.r3.dev-model-benchmark.v1"
    assert "openai" not in str(packet).lower()
    assert "anthropic" not in str(packet).lower()
    assert "gemini" not in str(packet).lower()
    assert packet["evaluation_boundary"]["network"] == "NONE"
    assert packet["evaluation_boundary"]["credentials"] is False


def test_dev_model_packet_preserves_core_governance_boundaries() -> None:
    packet = build_packet()
    task = packet["task"].lower()

    assert "capability is not authority" in task
    assert "verifiedrule" in task
    assert "replay is idempotent" in task
    assert "secrets are redacted" in task
    assert "ui state cannot mutate canonical authority" in task

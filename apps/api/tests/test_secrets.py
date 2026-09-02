from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.secrets import (
    EnvironmentSecretsPort,
    OpenBaoSecretsPort,
    SecretReference,
    SecretResolutionError,
    resolve_runtime_secret,
)


def test_secret_reference_parses_environment_reference():
    assert SecretReference.parse("env://DEEPSEEK_API_KEY") == SecretReference(
        backend="env", locator="DEEPSEEK_API_KEY"
    )


def test_environment_secret_resolution_reads_current_value(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "rotated-key")
    port = EnvironmentSecretsPort()
    assert port.resolve(SecretReference.parse("env://DEEPSEEK_API_KEY")) == "rotated-key"


def test_configured_reference_fails_closed_instead_of_using_plaintext_fallback(monkeypatch):
    monkeypatch.delenv("MISSING_AI_KEY", raising=False)
    with pytest.raises(SecretResolutionError, match="unavailable"):
        resolve_runtime_secret(reference="env://MISSING_AI_KEY", fallback="plaintext-fallback")


def _openbao_port(*, app_env="local"):
    return OpenBaoSecretsPort(
        address="http://openbao.test:8200",
        token="pilot-token",
        mount="secret",
        namespace="aios-pilot",
        allowed_prefix="aios/nonprod/",
        app_env=app_env,
        timeout_seconds=3,
    )


def test_openbao_pilot_rejects_production_resolution_before_network():
    port = _openbao_port(app_env="production")
    with patch("httpx.Client") as client_cls:
        with pytest.raises(SecretResolutionError, match="non-production"):
            port.resolve(SecretReference.parse("openbao://aios/nonprod/llm#api_key"))
    client_cls.assert_not_called()


def test_openbao_pilot_enforces_allowed_path_scope_before_network():
    port = _openbao_port()
    with patch("httpx.Client") as client_cls:
        with pytest.raises(SecretResolutionError, match="outside the allowed pilot scope"):
            port.resolve(SecretReference.parse("openbao://shared/prod/llm#api_key"))
    client_cls.assert_not_called()


def test_openbao_pilot_reads_kv_v2_field_with_namespace():
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"data": {"data": {"api_key": "secret-value"}}}
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False

    with patch("httpx.Client", return_value=client) as client_cls:
        value = _openbao_port().resolve(
            SecretReference.parse("openbao://aios/nonprod/llm/deepseek#api_key")
        )

    assert value == "secret-value"
    client_cls.assert_called_once_with(timeout=3)
    client.get.assert_called_once_with(
        "http://openbao.test:8200/v1/secret/data/aios/nonprod/llm/deepseek",
        headers={"X-Vault-Token": "pilot-token", "X-Vault-Namespace": "aios-pilot"},
    )


def test_openbao_pilot_does_not_cache_rotated_or_revoked_values():
    first = MagicMock()
    first.raise_for_status.return_value = None
    first.json.return_value = {"data": {"data": {"api_key": "v1"}}}
    second = MagicMock()
    second.raise_for_status.return_value = None
    second.json.return_value = {"data": {"data": {"api_key": "v2"}}}
    revoked = MagicMock()
    request = httpx.Request("GET", "http://openbao.test")
    revoked.raise_for_status.side_effect = httpx.HTTPStatusError(
        "forbidden", request=request, response=httpx.Response(403, request=request)
    )

    clients = []
    for response in (first, second, revoked):
        client = MagicMock()
        client.get.return_value = response
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        clients.append(client)

    reference = SecretReference.parse("openbao://aios/nonprod/llm/deepseek#api_key")
    port = _openbao_port()
    with patch("httpx.Client", side_effect=clients):
        assert port.resolve(reference) == "v1"
        assert port.resolve(reference) == "v2"
        with pytest.raises(SecretResolutionError, match="retrieval failed"):
            port.resolve(reference)

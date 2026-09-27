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
        address="https://openbao.test:8200",
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
    client_cls.assert_called_once_with(timeout=3, trust_env=False, follow_redirects=False)
    client.get.assert_called_once_with(
        "https://openbao.test:8200/v1/secret/data/aios/nonprod/llm/deepseek",
        headers={"X-Vault-Token": "pilot-token", "X-Vault-Namespace": "aios-pilot"},
        follow_redirects=False,
    )


def test_openbao_pilot_does_not_cache_rotated_or_revoked_values():
    first = MagicMock()
    first.raise_for_status.return_value = None
    first.json.return_value = {"data": {"data": {"api_key": "v1"}}}
    second = MagicMock()
    second.raise_for_status.return_value = None
    second.json.return_value = {"data": {"data": {"api_key": "v2"}}}
    revoked = MagicMock()
    request = httpx.Request("GET", "https://openbao.test")
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


@pytest.mark.parametrize(
    "locator",
    [
        "aios/nonprod/../prod/key",
        "aios/nonprod/./key",
        "aios/nonprod/%2e%2e/prod/key",
        "aios/nonprod//key",
        "aios/nonprod/..\\prod/key",
    ],
)
def test_openbao_rejects_noncanonical_scope_paths_before_network(locator):
    with patch("httpx.Client") as client_cls:
        with pytest.raises(SecretResolutionError, match="unsafe segments"):
            _openbao_port().resolve(SecretReference.parse(f"openbao://{locator}#api_key"))
    client_cls.assert_not_called()


@pytest.mark.parametrize(
    "address",
    [
        "http://openbao.test:8200",
        "http://10.0.0.5:8200",
        "https://operator:secret@openbao.test:8200",
        "https://openbao.test:8200/base",
        "https://openbao.test:8200?token=secret",
    ],
)
def test_openbao_rejects_unsafe_token_destinations_before_network(address):
    port = _openbao_port()
    port.address = address
    with patch("httpx.Client") as client_cls:
        with pytest.raises(SecretResolutionError, match="OpenBao address|OpenBao HTTP"):
            port.resolve(SecretReference.parse("openbao://aios/nonprod/llm#api_key"))
    client_cls.assert_not_called()


def test_openbao_local_loopback_address_remains_usable_without_redirecting_token():
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(302, headers={"Location": "https://untrusted.test/collect"})

    real_client = httpx.Client
    port = _openbao_port()
    port.address = "http://127.0.0.1:8200"
    with patch(
        "httpx.Client",
        side_effect=lambda **kwargs: real_client(
            transport=httpx.MockTransport(respond), **kwargs
        ),
    ):
        with pytest.raises(SecretResolutionError, match="retrieval failed"):
            port.resolve(SecretReference.parse("openbao://aios/nonprod/llm#api_key"))

    assert len(requests) == 1
    assert requests[0].url.host == "127.0.0.1"
    assert requests[0].headers["X-Vault-Token"] == "pilot-token"

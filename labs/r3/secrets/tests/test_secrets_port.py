from __future__ import annotations

import pytest

from labs.r3.secrets.port import (
    OpenBaoSecretsPort,
    SecretUnavailableError,
)


def test_openbao_port_never_falls_back_to_plaintext() -> None:
    port = OpenBaoSecretsPort(
        base_url="http://127.0.0.1:1",
        token="synthetic",
        timeout_seconds=0.05,
    )

    with pytest.raises(SecretUnavailableError):
        port.read("missing", "key")


def test_secret_port_does_not_store_plaintext_fallback_field() -> None:
    port = OpenBaoSecretsPort(
        base_url="http://127.0.0.1:18200",
        token="synthetic",
    )

    assert not hasattr(port, "fallback")
    assert not hasattr(port, "plaintext")
    assert not hasattr(port, "default_secret")

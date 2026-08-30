from __future__ import annotations

from labs.r3.secrets.persistent_openbao_lab import persistent_config


def test_persistent_config_uses_file_storage_and_no_tls_for_local_lab() -> None:
    config = persistent_config()

    assert config["storage"]["file"]["path"] == "/openbao/file"
    assert config["listener"][0]["tcp"]["tls_disable"] is True

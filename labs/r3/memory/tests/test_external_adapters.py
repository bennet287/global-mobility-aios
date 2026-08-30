from __future__ import annotations

import inspect

from labs.r3.memory.mem0_lab import _config
from labs.r3.memory.openviking_lab import OPENVIKING_LICENSE


def test_mem0_configuration_is_explicitly_local() -> None:
    config = _config(
        ollama_url="http://127.0.0.1:11434",
        llm_model="local-llm",
        embed_model="local-embed",
        embed_dims=768,
        qdrant_path="/tmp/qdrant",
    )

    assert config["llm"]["provider"] == "ollama"
    assert config["embedder"]["provider"] == "ollama"
    assert config["vector_store"]["provider"] == "qdrant"
    assert "openai" not in str(config).lower()


def test_mem0_lab_uses_infer_false_to_avoid_llm_extraction() -> None:
    from labs.r3.memory.mem0_lab import run_mem0

    assert "infer=False" in inspect.getsource(run_mem0)


def test_openviking_license_is_explicit() -> None:
    assert OPENVIKING_LICENSE == "AGPL-3.0"

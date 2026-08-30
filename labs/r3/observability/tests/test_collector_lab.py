from __future__ import annotations

from labs.r3.observability.collector_lab import COLLECTOR_PORT


def test_collector_port_is_nondefault_host_port() -> None:
    assert COLLECTOR_PORT == 14317
    assert COLLECTOR_PORT != 4317

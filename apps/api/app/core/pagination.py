from __future__ import annotations

DEFAULT_QUERY_LIMIT = 100
MAX_QUERY_LIMIT = 500


def clamp_query_limit(value: int | None, *, default: int = DEFAULT_QUERY_LIMIT) -> int:
    if value is None:
        value = default
    return max(1, min(int(value), MAX_QUERY_LIMIT))

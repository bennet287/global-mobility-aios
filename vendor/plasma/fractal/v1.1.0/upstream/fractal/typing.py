"""Type hints for ``fractal``."""

from __future__ import annotations

import os
from typing import Any, Union

__all__ = [
    'PathLike',
    'Row',
]

#: filesystem path accepted at boundaries
PathLike = Union[str, os.PathLike]

#: database row (a sqlite3.Row surfaced as a plain dict)
Row = dict[str, Any]

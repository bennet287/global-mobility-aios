"""Functions for locating the running installation."""

from __future__ import annotations

import os
import pathlib
import shutil
import sys
from typing import Optional

__all__ = []


def bin_dir() -> str:
    """Return the invoking interpreter's script directory."""
    return os.path.dirname(sys.executable)


def console_script(name: str) -> str:
    """Resolve a console script robustly.

    Prefers the script beside the running interpreter -- a dependency's
    console script installs into the same environment -- and falls back to
    the ambient ``PATH``. Ambient-only resolution breaks under pyenv shims:
    an orphaned shim resolves but exits 127 with a confusing "command not
    found" message.

    Args:
        name: Console script name.

    Returns:
        Path of the executable.

    Raises:
        RuntimeError: If no executable exists.

    """
    # prefer the running interpreter's bin dir (the installation's own scripts)
    candidate = pathlib.Path(sys.executable).parent / name
    if candidate.is_file():
        return str(candidate)
    # fall back to the ambient PATH
    found = shutil.which(name)
    if found is not None:
        return found
    raise RuntimeError(
        f'No {name!r} executable found — install it into the running environment.'
    )


def prepend_bin_path(env: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Return an environment with :func:`bin_dir` prepended to ``PATH``.

    Scripts that shell back into the installation's own CLIs must resolve
    them from the invoking installation, not ambient ``PATH``, so a fronted
    foreign install (e.g. the root venv's) cannot answer in this one's
    place.

    Args:
        env: Base environment (defaults to ``os.environ``).

    Returns:
        A fresh environment mapping with the prepended ``PATH``.

    """
    result = dict(os.environ if env is None else env)
    result['PATH'] = os.pathsep.join(filter(None, (bin_dir(), result.get('PATH'))))
    return result

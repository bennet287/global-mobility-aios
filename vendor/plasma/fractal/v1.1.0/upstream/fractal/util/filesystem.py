"""Functions for saving and loading on the file system."""

from __future__ import annotations

import os
import pathlib
import tempfile
from typing import Union

__all__ = []

# probe the process umask once at import, before threads exist -- os.umask is
# process-global, so a per-write zero-and-restore round-trip would race file
# creation in other threads
_UMASK = os.umask(0)
os.umask(_UMASK)


def write_atomic(path: pathlib.Path, data: Union[str, bytes]) -> None:
    """Write ``data`` to ``path`` atomically (unique temp + ``os.replace``).

    A plain ``write_text`` truncates before writing, so a concurrent
    reader can observe an empty or partial file and a crash mid-write
    leaves a torn one. Staging to a dot-prefixed temp file in the
    target's directory and swapping it into place makes every read
    all-or-nothing. Text writes land utf-8 with LF endings verbatim.
    A symlinked destination resolves first, so the swap updates the
    link's target and the link itself survives.
    ``mkstemp`` creates the temp ``0600`` and ``os.replace`` carries
    that mode onto the target, so an existing target's mode is
    preserved explicitly and a fresh file honors the umask.

    Args:
        path: Destination file.
        data: Payload -- ``str`` lands utf-8 with LF endings, ``bytes`` verbatim.

    """
    # resolve so a symlinked destination is written through, not replaced:
    # os.replace swaps the final path component, which would swap out the
    # link itself and strand its target stale
    path = path.resolve()
    fd, tmp = tempfile.mkstemp(
        dir=path.parent,
        prefix=f'.{path.name}-',
        suffix='.tmp',
    )
    try:
        if isinstance(data, bytes):
            with os.fdopen(fd, 'wb') as handle:
                handle.write(data)
        else:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
                handle.write(data)
        if path.exists():
            os.chmod(tmp, path.stat().st_mode & 0o777)
        else:
            os.chmod(tmp, 0o666 & ~_UMASK)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

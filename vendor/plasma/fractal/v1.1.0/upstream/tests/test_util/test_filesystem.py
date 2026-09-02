"""Test the ``fractal.util.filesystem`` module."""

from __future__ import annotations

import os
import pathlib

import pytest

from fractal.util.filesystem import write_atomic

__all__ = [
    'test_write_atomic_writes_text_as_utf8_verbatim',
    'test_write_atomic_writes_raw_bytes',
    'test_write_atomic_preserves_mode',
    'test_write_atomic_writes_through_a_symlink',
    'test_write_atomic_failure_discards_temp',
]


def test_write_atomic_writes_text_as_utf8_verbatim(tmp_path: pathlib.Path) -> None:
    """A text payload lands as its exact utf-8 bytes, newlines unmolested.

    The text branch writes with an explicit newline so a bare LF is never
    reinterpreted (no CRLF reintroduction), and utf-8 encodes a non-ASCII
    character faithfully rather than escaping or replacing it.
    """
    target = tmp_path / 'config.json'
    write_atomic(target, 'café\nβeta\n')
    assert target.read_bytes() == 'café\nβeta\n'.encode()


def test_write_atomic_writes_raw_bytes(tmp_path: pathlib.Path) -> None:
    """A bytes payload lands verbatim, no decoding or newline mapping."""
    target = tmp_path / 'blob.bin'
    write_atomic(target, b'\x00\r\n\xff')
    assert target.read_bytes() == b'\x00\r\n\xff'


def test_write_atomic_preserves_mode(tmp_path: pathlib.Path) -> None:
    """A rewrite keeps the target's permission bits."""
    target = tmp_path / 'config.json'
    write_atomic(target, 'first\n')
    os.chmod(target, 0o600)
    write_atomic(target, 'second\n')
    assert target.read_text(encoding='utf-8') == 'second\n'
    assert target.stat().st_mode & 0o777 == 0o600


def test_write_atomic_writes_through_a_symlink(tmp_path: pathlib.Path) -> None:
    """A symlinked destination updates its target and the link survives.

    The swap must land on the resolved target, never on the link itself --
    replacing the link with a regular file would strand the target stale.
    """
    target = tmp_path / 'real.txt'
    target.write_text('orig\n', encoding='utf-8')
    link = tmp_path / 'link.txt'
    link.symlink_to('real.txt')
    write_atomic(link, 'new\n')
    assert link.is_symlink()
    assert target.read_text(encoding='utf-8') == 'new\n'


def test_write_atomic_failure_discards_temp(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed swap keeps the old contents and leaves no temp file behind."""
    target = tmp_path / 'config.json'
    write_atomic(target, 'original\n')

    # fail the swap after the temp file is fully staged
    staged = []

    def refuse(src: str, dst: pathlib.Path) -> None:
        """Record the staged temp name and fail as if the disk refused."""
        staged.append(pathlib.Path(src).name)
        raise OSError('replace refused')

    monkeypatch.setattr(os, 'replace', refuse)
    with pytest.raises(OSError, match='replace refused'):
        write_atomic(target, 'updated\n')
    # the staged temp was dot-prefixed and is discarded; the target survives
    assert staged[0].startswith('.config.json-')
    assert target.read_text(encoding='utf-8') == 'original\n'
    assert list(tmp_path.iterdir()) == [target]

"""Test the ``fractal.util.system`` module."""

from __future__ import annotations

import os
import pathlib
import sys

import pytest

import fractal.util.system

__all__ = [
    'test_bin_dir_is_the_interpreter_script_directory',
    'test_console_script_prefers_the_interpreter_bin_dir',
    'test_console_script_falls_back_to_ambient_path',
    'test_console_script_raises_when_absent',
    'test_prepend_bin_path_fronts_the_search_path',
]


# ------ console_script


def test_bin_dir_is_the_interpreter_script_directory() -> None:
    """``bin_dir`` names the directory holding the running interpreter."""
    assert fractal.util.system.bin_dir() == os.path.dirname(sys.executable)


def test_console_script_prefers_the_interpreter_bin_dir(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A script beside the interpreter wins over any ambient ``PATH`` entry.

    Ambient-only resolution breaks under pyenv shims -- an orphaned shim
    resolves but exits 127 -- so the interpreter-adjacent script must win.
    """
    # an interpreter dir holding the script, and a PATH decoy elsewhere
    bin_dir = tmp_path / 'venv'
    bin_dir.mkdir()
    (bin_dir / 'tool').write_text('#!/bin/sh\n', encoding='utf-8')
    decoy_dir = tmp_path / 'shims'
    decoy_dir.mkdir()
    (decoy_dir / 'tool').write_text('#!/bin/sh\n', encoding='utf-8')
    python = bin_dir / 'python'
    monkeypatch.setattr(sys, 'executable', f'{python}')
    monkeypatch.setenv('PATH', f'{decoy_dir}')
    tool = bin_dir / 'tool'
    assert fractal.util.system.console_script('tool') == f'{tool}'


def test_console_script_falls_back_to_ambient_path(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no interpreter-adjacent script, the ambient ``PATH`` answers."""
    # a bare interpreter dir; the script lives on PATH (and is executable)
    bare = tmp_path / 'bare'
    bare.mkdir()
    ambient = tmp_path / 'bin'
    ambient.mkdir()
    script = ambient / 'tool'
    script.write_text('#!/bin/sh\n', encoding='utf-8')
    script.chmod(0o755)
    python = bare / 'python'
    monkeypatch.setattr(sys, 'executable', f'{python}')
    monkeypatch.setenv('PATH', f'{ambient}')
    assert fractal.util.system.console_script('tool') == f'{script}'


def test_console_script_raises_when_absent(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A script found nowhere raises a ``RuntimeError`` naming it."""
    bare = tmp_path / 'bare'
    bare.mkdir()
    empty = tmp_path / 'bin'
    empty.mkdir()
    python = bare / 'python'
    monkeypatch.setattr(sys, 'executable', f'{python}')
    monkeypatch.setenv('PATH', f'{empty}')
    with pytest.raises(RuntimeError, match='tool'):
        fractal.util.system.console_script('tool')


# ------ prepend_bin_path


def test_prepend_bin_path_fronts_the_search_path() -> None:
    """``prepend_bin_path`` fronts ``PATH`` with the interpreter's bin dir."""
    bin_dir = fractal.util.system.bin_dir()
    # an explicit base keeps its entries behind the bin dir
    env = fractal.util.system.prepend_bin_path({'PATH': '/usr/bin'})
    assert env['PATH'] == f'{bin_dir}{os.pathsep}/usr/bin'
    # a base with no PATH yields the bin dir alone (no trailing separator)
    assert fractal.util.system.prepend_bin_path({})['PATH'] == bin_dir
    # the default base is a fresh copy of os.environ, never mutated in place
    before = os.environ.get('PATH')
    env = fractal.util.system.prepend_bin_path()
    assert env['PATH'].startswith(f'{bin_dir}{os.pathsep}')
    assert os.environ.get('PATH') == before

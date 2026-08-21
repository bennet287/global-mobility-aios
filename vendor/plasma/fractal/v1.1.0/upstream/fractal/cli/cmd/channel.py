"""Implements ``fractal radio channel`` sub-app commands."""

from __future__ import annotations

from typing import Optional

import typer

from fractal.cli.utils import command, print_rows, resolve_node, resolve_sender

__all__ = [
    'radio_channel_create',
    'radio_channel_delete',
    'radio_channel_list',
]

_CHANNEL_COLUMNS = [
    'channel_id',
    'channel',
    'read_only',
    'write_only',
    'created_at',
]


def radio_channel_create(app: typer.Typer) -> typer.Typer:
    """Register the ``create`` command."""
    # channel name argument
    channel_name_help = 'Channel name to create.'
    channel_name = typer.Argument(..., help=channel_name_help)
    # read-only flag
    read_only_help = 'Only owner can read.'
    read_only = typer.Option(
        False,
        '--read-only/--no-read-only',
        help=read_only_help,
    )
    # write-only flag
    write_only_help = 'Only owner can write.'
    write_only = typer.Option(
        False,
        '--write-only/--no-write-only',
        help=write_only_help,
    )
    # path option
    path_help = 'Worktree directory (default: the calling node, else the cwd).'
    path = typer.Option(None, '--path', help=path_help)

    @command(app, 'create')
    def _create(
        channel_name: str = channel_name,
        read_only: bool = read_only,
        write_only: bool = write_only,
        path: Optional[str] = path,
    ) -> None:
        """Register a custom channel."""
        node = resolve_sender(path)
        node.radio.channel(channel_name, read_only=read_only, write_only=write_only)
        typer.echo(f'Created channel {channel_name}.')

    return app


def radio_channel_delete(app: typer.Typer) -> typer.Typer:
    """Register the ``delete`` command."""
    # channel name argument
    channel_name_help = 'Channel name to delete.'
    channel_name = typer.Argument(..., help=channel_name_help)
    # force flag
    force_help = 'Delete the channel even if it still holds messages.'
    force = typer.Option(False, '--force', '-f', help=force_help)
    # path option
    path_help = 'Worktree directory (default: the calling node, else the cwd).'
    path = typer.Option(None, '--path', help=path_help)

    @command(app, 'delete')
    def _delete(
        channel_name: str = channel_name,
        force: bool = force,
        path: Optional[str] = path,
    ) -> None:
        """Delete a channel (refused if it holds messages; use --force)."""
        node = resolve_sender(path)
        node.radio.channel_delete(channel_name, force=force)
        typer.echo(f'Deleted channel {channel_name}.')

    return app


def radio_channel_list(app: typer.Typer) -> typer.Typer:
    """Register the ``list`` command."""
    # csv flag
    csv_help = 'Force CSV output (already the default when piped / non-TTY).'
    csv = typer.Option(False, '--csv', help=csv_help)
    # path option
    path_help = 'Worktree directory.'
    path = typer.Option('.', '--path', help=path_help)

    @command(app, 'list')
    def _list(
        csv: bool = csv,
        path: str = path,
    ) -> None:
        """List all channels."""
        node = resolve_node(path)
        rows = node.radio.channels()
        print_rows(rows, csv=csv, columns=_CHANNEL_COLUMNS)

    return app

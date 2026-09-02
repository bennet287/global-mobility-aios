"""Implements ``fractal event`` sub-app commands."""

from __future__ import annotations

from typing import Optional

import typer

from fractal.cli.utils import (
    command,
    print_rows,
    require_non_negative,
    resolve_node,
)

__all__ = [
    'event_start',
    'event_end',
    'event_list',
]

_EVENT_COLUMNS = [
    'event_id',
    'step_id',
    'iter_id',
    'run_id',
    'event',
    'status',
    'exit_code',
    'metadata',
    'created_at',
]


def event_start(app: typer.Typer) -> typer.Typer:
    """Register the ``_start`` command."""
    # event argument
    event_help = (
        'Event type (init, spawn, commit, approve, merge, delete,'
        ' finish, stop, kill, pause, resume, retire, unretire).'
    )
    event = typer.Argument(..., help=event_help)
    # metadata option
    metadata_help = 'Metadata string.'
    metadata = typer.Option('', '--metadata', help=metadata_help)
    # run id option
    run_id_help = 'Run the event belongs to (default: the active context).'
    run_id = typer.Option(None, '--run', help=run_id_help)
    # iteration id option
    iter_id_help = 'Iteration the event belongs to.'
    iter_id = typer.Option(None, '--iter', help=iter_id_help)
    # step id option
    step_id_help = 'Step the event belongs to.'
    step_id = typer.Option(None, '--step', help=step_id_help)
    # path option
    path_help = 'Worktree directory.'
    path = typer.Option('.', '--path', help=path_help)

    @command(app, '_start')
    def _start(
        event: str = event,
        metadata: str = metadata,
        run_id: Optional[int] = run_id,
        iter_id: Optional[int] = iter_id,
        step_id: Optional[int] = step_id,
        path: str = path,
    ) -> None:
        """Log an event. Prints event_id."""
        node = resolve_node(path)
        event_id = node.record.event_start(
            event,
            metadata=metadata,
            run_id=run_id,
            iter_id=iter_id,
            step_id=step_id,
        )
        if event_id is not None:
            typer.echo(event_id)

    return app


def event_end(app: typer.Typer) -> typer.Typer:
    """Register the ``_end`` command."""
    # event id argument
    event_id_help = 'Event ID.'
    event_id = typer.Argument(..., help=event_id_help)
    # status option
    status_help = 'Final status.'
    status = typer.Option(..., '--status', help=status_help)
    # exit code option
    exit_code_help = 'Exit code (optional).'
    exit_code = typer.Option(None, '--exit-code', help=exit_code_help)
    # path option
    path_help = 'Worktree directory.'
    path = typer.Option('.', '--path', help=path_help)

    @command(app, '_end')
    def _end(
        event_id: int = event_id,
        status: str = status,
        exit_code: Optional[int] = exit_code,
        path: str = path,
    ) -> None:
        """End an event."""
        node = resolve_node(path)
        node.record.event_end(
            event_id=event_id,
            status=status,
            exit_code=exit_code,
        )

    return app


def event_list(app: typer.Typer) -> typer.Typer:
    """Register the ``_list`` command."""
    # run id argument
    run_id_help = 'Filter by run ID.'
    run_id = typer.Argument(None, help=run_id_help)
    # event option
    event_help = 'Filter by event type.'
    event = typer.Option(None, '--event', help=event_help)
    # status option
    status_help = 'Filter by status.'
    status = typer.Option(None, '--status', help=status_help)
    # limit option
    limit_help = 'Maximum rows to return.'
    limit = typer.Option(None, '--limit', help=limit_help)
    # csv flag
    csv_help = 'Output as CSV.'
    csv = typer.Option(False, '--csv', help=csv_help)
    # path option
    path_help = 'Worktree directory.'
    path = typer.Option('.', '--path', help=path_help)

    @command(app, '_list')
    def _list(
        run_id: Optional[int] = run_id,
        event: Optional[str] = event,
        status: Optional[str] = status,
        limit: Optional[int] = limit,
        csv: bool = csv,
        path: str = path,
    ) -> None:
        """List events."""
        require_non_negative(limit=limit)
        node = resolve_node(path)
        rows = node.record.events(
            run_id=run_id,
            event=event,
            status=status,
            limit=limit,
        )
        print_rows(rows, csv=csv, columns=_EVENT_COLUMNS)

    return app

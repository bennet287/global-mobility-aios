"""Implements ``fractal db`` sub-app commands."""

from __future__ import annotations

import sqlite3

import typer

from fractal.cli.utils import command, print_rows, resolve_node

__all__ = ['db_query']


def db_query(app: typer.Typer) -> typer.Typer:
    """Register the ``_query`` command."""
    # query argument
    query_help = 'SQL query to execute (read-only).'
    query = typer.Argument(..., help=query_help)
    # csv flag
    csv_help = 'Output as CSV.'
    csv = typer.Option(False, '--csv', help=csv_help)
    # path option
    path_help = 'Worktree directory.'
    path = typer.Option('.', '--path', help=path_help)

    @command(app, '_query')
    def _query(
        query: str = query,
        csv: bool = csv,
        path: str = path,
    ) -> None:
        """Execute a read-only SQL query against the central database."""
        # check=False: this command guards existence itself below (a missing
        # node is a clean BadParameter, not the generic resolve_node message)
        node = resolve_node(path, check=False)
        if node.exists():
            try:
                rows = node.db.read(query=query)
            except sqlite3.OperationalError as e:
                if 'readonly database' in str(e):
                    raise typer.BadParameter('Query must be read-only.') from e
                raise
            except sqlite3.ProgrammingError as e:
                # e.g. a multi-statement query -- a usage error (exit 2), not a crash
                raise typer.BadParameter(f'Invalid query: {e}.') from e
            print_rows(rows, csv=csv)
        else:
            raise typer.BadParameter(f'No fractal node at {node.worktree}.')

    return app

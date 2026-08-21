"""Implements ``fractal plan`` sub-app commands."""

from __future__ import annotations

from typing import Optional

import typer

from fractal.cli.utils import command, resolve_node

__all__ = [
    'plan_init',
    'plan_list',
]


def plan_init(app: typer.Typer) -> typer.Typer:
    """Register the ``init`` command."""
    # name option
    name_help = 'Short descriptive slug for the plan (snake_case).'
    name = typer.Option(..., '--name', help=name_help)
    # title option
    title_help = 'Plan title for the H1 (defaults to the de-slugged name).'
    title = typer.Option(None, '--title', help=title_help)
    # iteration reference option (loop-supplied via $ITER_REF)
    iter_ref_help = 'Iteration reference, run.iter (e.g. 12.5).'
    iter_ref = typer.Option(..., '--iter-ref', envvar='ITER_REF', help=iter_ref_help)
    # path option
    path_help = 'Worktree directory.'
    path = typer.Option('.', '--path', help=path_help)

    @command(app, 'init')
    def _init(
        name: str = name,
        title: Optional[str] = title,
        iter_ref: str = iter_ref,
        path: str = path,
    ) -> None:
        """Create a plan file seeded with its H1. Prints the path."""
        node = resolve_node(path)
        result = node.plans.init(
            iter_ref=iter_ref,
            name=name,
            title=title,
        )
        typer.echo(result)

    return app


def plan_list(app: typer.Typer) -> typer.Typer:
    """Register the ``list`` command."""
    # iteration reference option (loop-supplied via $ITER_REF)
    iter_ref_help = 'Iteration reference, run.iter (e.g. 12.5).'
    iter_ref = typer.Option(..., '--iter-ref', envvar='ITER_REF', help=iter_ref_help)
    # path option
    path_help = 'Worktree directory.'
    path = typer.Option('.', '--path', help=path_help)

    @command(app, 'list')
    def _list(
        iter_ref: str = iter_ref,
        path: str = path,
    ) -> None:
        """List this iteration's plan files, one per line."""
        node = resolve_node(path)
        plans = node.plans.list(iter_ref=iter_ref)
        # the notice goes to stderr: stdout is a path-per-line surface, so a
        # piped consumer must never receive the sentence as a path
        if not plans:
            typer.echo('No plans for this iteration.', err=True)
            return
        for plan in plans:
            typer.echo(plan)

    return app

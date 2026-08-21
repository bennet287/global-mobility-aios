``fractal plan``
================

The ``fractal plan`` sub-app manages plan files — per-iteration markdown
documents under the node's data directory (``.fractal/<branch>/plans/``
inside the worktree). During the loop's PLAN step the agent creates a plan
with ``plan init`` and executes against it in the steps that follow; the
REVIEW step finds it again with ``plan list``. :doc:`/guide/plans` covers how
plans fit the iteration, and :doc:`/guide/loop` covers the loop itself.

The commands identify the iteration by its *iteration reference* — a
``run.iter`` pair such as ``10.5`` (run 10, iteration 5). The loop exports it
as the ``ITER_REF`` environment variable, so inside a running loop the
``--iter-ref`` option can be omitted; anyone running these commands by hand
must pass it explicitly.

``plan init``
-------------

.. code-block:: console

   $ fractal plan init --name=<slug> --iter-ref=<run.iter>

Create a plan file and print its absolute path — the caller writes the plan
content below the seeded heading.

.. list-table::
   :header-rows: 1
   :widths: 22 26 52

   * - Option
     - Default
     - Description
   * - ``--name``
     - required
     - Short descriptive slug for the plan, snake_case — letters, digits,
       and underscores only.
   * - ``--title``
     - de-slugged name
     - Title for the H1 heading (``parser_design`` becomes
       ``Parser Design``).
   * - ``--iter-ref``
     - ``ITER_REF`` env var
     - Iteration reference in ``run.iter`` form (e.g. ``10.5``).
   * - ``--path``
     - ``.``
     - Worktree directory of the acting node.

The file is named ``<UTC timestamp>-<run.iter>-<name>.md`` — the timestamp
makes two plans written in the same iteration distinct — and is seeded with a
``# <run.iter> <title>`` heading so the run and iteration stay readable in
the file itself. Creation is exclusive: an exact-name collision errors rather
than replacing the earlier plan.

.. code-block:: console

   $ fractal plan init --name=parser_design --iter-ref=10.5
   /home/user/myproject/.worktrees/main.parser/.fractal/main.parser/plans/2026-01-01T12:00:00.000Z-10.5-parser_design.md

The seeded file:

.. code-block:: markdown

   # 10.5 Parser Design

When the work splits cleanly into separate concerns, run a separate
``plan init`` per concern — ``plan list`` returns them all.

``plan list``
-------------

.. code-block:: console

   $ fractal plan list --iter-ref=<run.iter>

Print the iteration's plan paths, one per line, sorted by filename (and so
chronologically by timestamp). Plans are matched on the ``run.iter`` segment
of the filename, so the listing returns every plan the iteration wrote —
zero, one, or many.

.. list-table::
   :header-rows: 1
   :widths: 22 26 52

   * - Option
     - Default
     - Description
   * - ``--iter-ref``
     - ``ITER_REF`` env var
     - Iteration reference in ``run.iter`` form (e.g. ``10.5``).
   * - ``--path``
     - ``.``
     - Worktree directory of the acting node.

stdout is a pure path-per-line surface for scripting; when the iteration has
no plans, the notice ``No plans for this iteration.`` prints on stderr and
stdout stays empty.

.. code-block:: console

   $ fractal plan list --iter-ref=10.5
   /home/user/myproject/.worktrees/main.parser/.fractal/main.parser/plans/2026-01-01T12:00:00.000Z-10.5-parser_design.md
   /home/user/myproject/.worktrees/main.parser/.fractal/main.parser/plans/2026-01-01T12:30:00.000Z-10.5-error_handling.md

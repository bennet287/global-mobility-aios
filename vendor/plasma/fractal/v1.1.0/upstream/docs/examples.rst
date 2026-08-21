Examples
========

The ``examples/`` directory in the fractal repository holds runnable,
self-contained walkthroughs. Each script builds everything in a scratch
directory and never touches the repository it lives in, so you can run one
against a fresh install without preparing a project first.

The repository ships ``examples/hello.sh``, a guided tour of the full setup
path — scratch repository, ``fractal init``, wiki scaffold commit,
and a capped ``hello`` node with a real mission authored into its ``NODE.md``.
This page walks through what the script does and why; for the concepts behind
each step see :doc:`/guide/getting-started` and :doc:`/guide/architecture`.

The hello walkthrough
---------------------

``hello.sh`` runs the setup end to end and stops at the one step that costs
money. Everything up to ``fractal node start`` runs for real: the script
creates a scratch git repository, initializes fractal in it, commits the wiki
scaffold, creates a capped node, and writes a small mission into the node's
contract. The start, watch, and merge commands are then *printed instead of
run*, because starting the loop invokes the configured agent — the walkthrough
itself is free.

Running the script
~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ bash examples/hello.sh
   $ bash examples/hello.sh --dir=/tmp/hello --agent=claude

The only precondition is that ``fractal`` is on ``PATH``; otherwise the script
exits with a pointer to ``pip install plasma-fractal`` (see
:doc:`/guide/getting-started` for the install options).

Options (both ``--opt=value`` and ``--opt value`` forms are accepted):

``--dir=<path>``
   Directory for the scratch repository. Defaults to a fresh temporary
   directory (``fractal_hello_XXXXXX`` under ``$TMPDIR``); when given, the
   path must be empty or absent. The default name deliberately uses
   underscores and no dots, because ``fractal init`` derives the project name
   from the directory name and rejects characters it cannot map — keep that in
   mind if you pick your own path.

``--agent=<agent>``
   Default agent command that spawned nodes inherit — any supported agent
   name (see :doc:`/guide/agents`). Defaults to ``claude``. This is passed
   straight through to ``fractal init --agent``.

``--help`` / ``-h``
   Print usage and exit.

Step by step
------------

The scratch repository
~~~~~~~~~~~~~~~~~~~~~~

The script first builds a stand-in for your project: ``git init`` on branch
``main``, a one-line ``project.md``, and a single seed commit. It sets a
repo-local git identity (``user.name`` / ``user.email``) so the walkthrough
runs on machines without a global git config — your real repository uses your
own. Nothing here is fractal-specific; the point is that fractal attaches to
an ordinary git repository with at least one commit.

``fractal init``
~~~~~~~~~~~~~~~~

.. code-block:: console

   $ fractal init --agent=claude

This is the one-time repository setup. It creates the **user (root) node** —
the data directory ``.fractal/main/`` holding ``config.json`` and the tree's
central SQLite database — scaffolds the project wiki at ``wiki/``, and writes
the repo-local git exclude so fractal's runtime artifacts stay out of your
commits. At this point the tree exists but consists only of its root, which
never runs a loop: it is the operator's seat (see
:doc:`/guide/architecture`).

Committing the wiki scaffold
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ git add wiki .gitattributes
   $ git commit -m "add project wiki"

A node branches from its parent's *committed* tree, so the wiki scaffold must
be committed on the base branch before any node is created — an uncommitted
wiki would be invisible on the node's branch. The script uses plain git;
``fractal commit "add project wiki" --init`` is the fractal-native way to make
this baseline commit (it is the only commit a user node accepts).

A capped node
~~~~~~~~~~~~~

.. code-block:: console

   $ fractal node init hello --max-iters=2 --max-cost=5.0

This creates the agent node: a branch ``main.hello`` forked from ``main``,
checked out into the worktree ``.worktrees/main.hello/``, with a data
directory at ``.worktrees/main.hello/.fractal/main.hello/`` seeded with
``NODE.md``, the step files, scripts, skills, and ``config.json``.

The caps are the load-bearing part of this command. The script never creates
an uncapped node: the defaults are unlimited, and one iteration is several
agent invocations, so ``--max-iters=2`` and ``--max-cost=5.0`` bound the demo
to two iterations or five dollars, whichever comes first. See
:doc:`/configuration` for the full option surface and :doc:`/cli/node` for
the command reference.

Authoring the mission
~~~~~~~~~~~~~~~~~~~~~

A freshly seeded ``NODE.md`` carries two placeholder comments — one under
``## Instructions``, one under ``## Completion Requirements``. Normally you
open the file in an editor; the script replaces them in place (with ``awk``,
so the run stays unattended) and verifies the injection landed:

.. code-block:: markdown

   ## Instructions

   Write HELLO.md at the worktree root: a two-line greeting from the hello
   node, plus a count of the files in the repo.

   ## Completion Requirements

   HELLO.md exists at the worktree root with both lines. Then run
   `fractal node finish --reason="hello done"`.

The completion requirement demonstrates the loop's central convention: the
node itself signals that it is done by running ``fractal node finish`` from
inside its worktree. Without that signal the loop keeps iterating — and
spending — until a cap ends the run. The script finishes this phase by
printing the authored task contract (the ``## Instructions``-to-``## Rules``
slice of ``NODE.md``) so you can read exactly what the node will be told. See
:doc:`/guide/loop` for how the contract drives each iteration.

The handoff
~~~~~~~~~~~

Everything so far is free. The script ends by printing — not running — the
commands that spend money, along with a reminder that the node is capped at 2
iterations / $5.00:

.. code-block:: console

   $ cd <scratch-dir>
   $ fractal node start hello     # start the loop in tmux
   $ fractal node status hello    # lifecycle status
   $ fractal node activity hello  # what it is doing right now

And once ``fractal node status hello`` reads ``completed``:

.. code-block:: console

   $ fractal node merge hello     # merge the node's branch back

The last line of output names the scratch repository so you can delete it when
you are done.

The states the tree passes through
----------------------------------

Running the printed commands takes the ``hello`` node through the standard
lifecycle (see :doc:`/guide/lifecycle` for the full state machine):

- After ``fractal node init``, the node is ``idle`` — spawned, never started.
  ``fractal node status hello`` prints ``idle``.
- ``fractal node start hello`` launches the iteration loop in a detached tmux
  session and the node becomes ``active``. Watch it with
  ``fractal node status``, ``fractal node activity``, ``fractal node attach``,
  or the :doc:`TUI </tui>`.
- When the node meets its completion requirements and runs
  ``fractal node finish --reason="hello done"``, the run ends after the
  current iteration and the node settles ``completed``.
- If it never signals finish, a cap ends the run instead. Exhausting
  ``--max-iters=2`` with a clean final iteration settles the node
  ``completed`` even though the goal may not be met — check
  ``fractal node activity`` to tell the difference — while ending on the
  $5.00 budget settles it ``exited``. ``fractal node start hello
  --continue`` re-arms it for further iterations (a run that ended on its
  cost budget requires an explicit ``--max-cost`` to continue).
- ``fractal node merge hello`` squash-merges the node's branch back into
  ``main``; the full history stays on ``main.hello``.

Because the whole tree lives in a scratch directory, cleanup is just deleting
it. In a real repository you would instead remove finished nodes with
``fractal node delete`` or tear the tree down with ``fractal reset``.

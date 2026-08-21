Command-Line Interface
======================

The ``fractal`` executable is the operating surface for a fractal tree. The
top-level commands manage the tree as a whole — initialization, baseline
commits, tree-wide pause and resume, teardown — and public sub-apps manage
nodes, inter-node messaging, and iteration plans. Agents inside the tree
run the same commands: every node steers itself and its children through
this CLI, whether driven by an operator at a shell or by the
:doc:`fractal skill </skill>`.

Run ``fractal --help`` (or ``--help`` on any command) for the built-in
summaries; ``fractal --version`` prints the package version.
``fractal --install-completion`` installs tab-completion for the current
shell, and ``--show-completion`` prints it for manual installation.

Command map
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Command group
     - Purpose
   * - :doc:`fractal </cli/fractal>`
     - Tree-level operations: skill install, initialization, baseline
       commits, tree-wide pause and resume, teardown, and the TUI cockpit.
   * - :doc:`fractal node </cli/node>`
     - Node lifecycle and management: create, start, signal, merge, delete,
       inspect, and retune nodes.
   * - ``fractal node time``
     - Time budget introspection: seconds until the next run, iteration, or
       step timeout (documented on the :doc:`node page </cli/node>`).
   * - ``fractal node cost``
     - Cost budget introspection: remaining headroom, recorded spend, and a
       per-node breakdown (documented on the :doc:`node page </cli/node>`).
   * - ``fractal node config``
     - Read and write a node's configuration keys (documented on the
       :doc:`node page </cli/node>`; the key reference is
       :doc:`/configuration`).
   * - :doc:`fractal radio </cli/radio>`
     - Inter-node messaging: send, post, read, reply, react, and subscribe.
   * - ``fractal radio channel``
     - Create, delete, and list custom channels (documented on the
       :doc:`radio page </cli/radio>`).
   * - :doc:`fractal plan </cli/plan>`
     - Create and list per-iteration plan files.

Conventions
-----------

These behaviors are shared by every command; the per-command pages state
only what deviates.

- **Errors.** Core refusals print ``Error: <message>`` on stderr and exit
  with code ``1``. Argument errors raised at the CLI boundary — bad values,
  unknown or ambiguous node names, mutually exclusive flags, missing
  required options — print a usage error (``Invalid value: <message>``) on
  stderr and exit with code ``2``.
- **The caller and the target.** Almost every command takes ``--path``
  (default ``.``), which identifies the *caller's* worktree — the node the
  command runs as. Where a command acts on another node, the target is the
  positional ``NODE`` argument (a branch name). The radio verbs that write
  rows attributed to the caller resolve it env-first instead — an explicit
  ``--path``, else the loop-exported ``_NODE``, else the cwd — and
  ``fractal radio read``'s ``--path`` selects the mailbox being viewed
  (see :doc:`/cli/radio`).
- **Short names.** Branch arguments on ``fractal`` and ``fractal node``
  commands (``node cost`` targets included) resolve a unique trailing
  segment to the full dotted branch (``lexer`` finds ``main.parser.lexer``).
  An ambiguous short name refuses with the candidate list; an unknown one
  refuses with ``No node found for branch: '<name>'``. The ``fractal radio``
  targets (``--node``) take the full branch name only.
- **Listings.** Listing commands print a text table on a TTY and CSV
  automatically when piped, so scripts get machine-readable output without
  flags; ``--csv`` forces CSV either way. Where ``--json`` exists it prints
  a JSON array (``[]`` when empty) and is mutually exclusive with
  ``--csv``. Empty listings still emit the header row.
- **stdout and stderr.** stdout is the parseable surface — UUIDs, tables,
  paths. Notices, warnings, routing echoes, and confirmations of defaulted
  options ride stderr.
- **Numeric caps.** Every ``--max-*`` cap must be at least ``0``; unlimited
  is expressed by omitting the flag, never by a negative or sentinel value.
- **Durations.** Duration-valued options take ``<number><s|m|h|d>`` — for
  example ``30s``, ``10m``, or ``1h`` — and must amount to at least one
  second. Bare numbers are rejected. See :doc:`/configuration`.

Internal commands
-----------------

Fractal's hidden sub-apps and the underscore-prefixed ``fractal node``
commands are internal plumbing invoked by fractal's own scripts — the
in-tmux iteration loop, node seeding, and pre-init configuration writes.
They are hidden from ``--help`` and are not user surface; their effects
appear to users only as the iteration loop's normal behavior (see
:doc:`/guide/loop`).

.. toctree::
   :maxdepth: 2
   :caption: Commands

   fractal
   node
   radio
   plan

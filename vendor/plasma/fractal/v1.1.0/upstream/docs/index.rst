.. Fractal documentation master file.

Fractal Documentation
=====================

Fractal runs trees of autonomous coding-agent nodes inside a git repository.
Each node is an isolated worktree driven by an iteration loop in a tmux
session, with lifecycle, budgets, and inter-node messaging recorded in one
central SQLite database per tree. Developers use it to delegate substantial
coding work to agents; the agents themselves steer their own children
through the same CLI.

.. toctree::
   :maxdepth: 3
   :titlesonly:

   api

.. toctree::
   :maxdepth: 2

   guide/index
   reference
   going-further

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

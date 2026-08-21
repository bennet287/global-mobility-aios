## Continue Mode

This node was continued (`$CONTINUE_MODE` is `true`); the worktree was cleaned
of uncommitted changes before the first iteration, so you start from the last
committed state. Rebuild context from durable sources: memory (`$MEMORY_DIR`),
the project wiki (`$WIKI_DIR`), and prior plans in `$PLANS_DIR`. If you spawned
child nodes previously, decide what to do with each (see the `fractal` skill's
Continue mode section).

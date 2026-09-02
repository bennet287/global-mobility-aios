---
name: configuration/scripts
desc: |
  The three node scripts -- setup, test, and lint: when each runs, what the
  loop and the commit pipeline do with their results, and the rules for
  extending them per node.
created: 2026-07-21T04:48:38Z
updated: 2026-07-21T04:48:38Z
---

# configuration/scripts

[[_index|..]]

***

Every node carries three shell scripts in its data directory's `scripts/` folder
-- `setup.sh`, `test.sh`, and `lint.sh` -- seeded from the package (or from the
parent's live copies with `--inherit=scripts`; see
[[configuration/inheritance]]). These per-node scripts are distinct from the
lifecycle shell scripts in `fractal/_scripts/`
([[features/lifecycle/script_delegation]]). They are the node's project-specific
hooks: the seed versions are deliberately minimal, and each node extends them
for its project.

## setup.sh -- environment setup

The loop runs `setup.sh` at the start of every iteration, from the worktree root
(so relative paths land beside the work), capturing its output to `setup.log` in
the node data directory. It must therefore be idempotent. Package installs
belong here, never inline in a step -- the environment stays reproducible across
iterations, and when the repo's virtualenv exists it is on the PATH so installs
land there.

A failed setup skips the iteration rather than running steps in a broken
environment, and the failure reason carries the tail of the captured log. Three
consecutive failures end the run as `exited` with the honest reason -- a
deterministically broken setup must not crash-loop into a healthy-looking end --
and any success resets the counter.

## test.sh -- the verification gate

The loop never runs `test.sh`; it is the node's own verification tool. The seed
step prompts direct the agent to run it while executing (exit 0 or no-op means
proceed) and to confirm it passes before signalling completion -- a finish over
failing tests would book a false `completed`. The seed version is a no-op
scaffold: extend it with the project's real test command, exiting 0 on success
and non-zero on failure.

## lint.sh -- the commit gate

`fractal commit` runs `lint.sh` as part of its pipeline -- scope check, wiki
index refresh, lint, stage, commit, push -- and a non-zero exit aborts the
commit, so lint failures surface at COMMIT rather than accumulating. The seed
steps also direct the agent to run it during execution to catch issues early.
Force-commits (the loop's backstop saves) bypass the lint gate along with the
scope check: a backstop save must never block.

The seed version validates the node's own surfaces rather than project code: it
checks the skills directory layout and runs the wiki linter over the node's
memory and the project wiki, reporting wiki issues as warnings.

## Extension rules

Extend a script by adding to what the orchestrator seeded, never by replacing or
trimming it -- the seeded content is part of the node's contract. Keep
`setup.sh` idempotent (it runs every iteration), keep `test.sh` and `lint.sh`
honest about their exit codes (the loop and the commit pipeline branch on them,
not on output), and put installs in `setup.sh` rather than running them inline.
The seed scripts run under bash with strict error handling; extensions inherit
that regime, so a failing added command fails the script.

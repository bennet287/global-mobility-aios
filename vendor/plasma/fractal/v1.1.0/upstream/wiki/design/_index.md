---
name: design
desc: |
  Why fractal is shaped the way it is: budget and reserve rationale,
  durability guarantees, commit and merge discipline, and the lifecycle
  status model.
created: 2026-07-21T04:35:35Z
updated: 2026-07-21T11:38:35Z
---

# design

[[_index|..]]

[[design/budgets|budgets]]: Why cost ceilings are soft and checked at boundaries
rather than enforced by hard kills, why every run keeps a reserve as its
wind-down window, how a finish landed in the reserve books its terminal status,
why sync is a billed step, and how the run, iteration, and step cap tiers divide
the enforcement problem.

[[design/commit_discipline|commit_discipline]]: Why every iteration must commit,
how scope enforcement and the always-allowed shared wiki divide the worktree,
why force-commit backstops exist as fail-safes rather than workflow, and why
child work merges with no-fast-forward on the node's mainline but squashes
toward the base.

[[design/durability|durability]]: Why a paused node stays active-like everywhere
but execution, why a parked loop with no tmux session is a normal state rather
than a crash, what the pause and resume events credit back to deadlines, and why
a tree-wide pause latches the root.

[[design/statuses|statuses]]: Why one status vocabulary serves both the node
status file and every database row table, which statuses apply at which level
and why, why exit codes are binary and derived from outcome, and why events are
point-in-time instants with durations always derived.

***

This branch records design rationale — the reasoning behind fractal's shape, as
opposed to the structural facts in the architecture branch. Each page explains
why a behavior exists, the trade-offs behind it, and the failure modes it
prevents; read the relevant page before proposing to change a behavior it
covers.

- [[design/budgets]] — why cost ceilings are soft and checked at boundaries, the
  reserve as a priced wind-down window, how a finish landed there books its
  terminal status, sync as a billed step, and how the run/iteration/step cap
  tiers divide enforcement.
- [[design/durability]] — the pause/resume round-trip guarantee: paused as
  active-like everywhere but execution, parking as a full process exit, deadline
  crediting from pause/resume instants, and the tree-wide latch.
- [[design/commit_discipline]] — why every iteration commits, scope enforcement
  with the always-committable shared wiki, force-commit backstops as fail-safes,
  and the no-fast-forward-in / squash-out merge shapes.
- [[design/statuses]] — one status vocabulary across the status file and the row
  tables, per-level applicability, binary outcome-derived exit codes, and
  point-in-time events with derived durations.

---
name: features/spawning/tree_limits
desc: |
  The three tree caps — children (width), depth, and descendants — plus the
  spawn-time budget check: what each bounds, which ancestor's configuration
  enforces it, and why enforcement needs no agent cooperation.
created: 2026-07-21T04:58:40Z
updated: 2026-07-21T04:58:40Z
---

# features/spawning/tree_limits

[[features/spawning/_index|..]]

***

Child creation is gated at `fractal node init`, on the parent side, just before
the child is registered. Three caps and one budget check apply, and **every
ancestor's configuration is consulted** — a limit set anywhere up the chain
holds even if every agent below it ignores its instructions. There is no
override flag.

- **`max_children` (width)** binds at the direct parent only: it counts that
  parent's *unsettled* direct children (it is the depth-1 case of the
  descendants count).
- **`max_depth`** binds at every ancestor and is *structural*: the child's
  absolute depth minus the ancestor's depth is checked against that ancestor's
  cap. Because it measures shape rather than activity, settled nodes still
  occupy their place in the chain.
- **`max_descendants`** binds at every ancestor: it counts the ancestor's
  unsettled descendants across the whole subtree.
- **Budget**: the child's cost cap must fit within the parent's remaining run
  budget, so a subtree can never promise more spend than its root was given.

Width and descendant caps bound *concurrency*, not lifetime spawn count — what
counts against them and when a slot frees is specified in
[[features/spawning/slot_accounting|slot_accounting]]. Depth is the one
structural cap: finished children still hold their rung.

Re-entry paths that return a node to the unsettled pool — `start --continue` on
a settled node, and an unretire that restores `idle` — re-run the width and
descendant gates only. Depth needs no re-check (the node already sits at its
depth), and the budget check is spawn-time only: each run re-arms the node's own
cost cap instead. A node's *own* caps are also skipped on re-entry — they bound
its subtree, which re-arming does not change.

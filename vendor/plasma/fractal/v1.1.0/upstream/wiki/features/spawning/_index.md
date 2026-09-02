---
name: features/spawning
desc: |
  Child node spawning and tree limits: depth, width, and descendant caps,
  slot accounting, and spawn-time enforcement.
created: 2026-07-21T04:58:40Z
updated: 2026-07-21T04:58:40Z
---

# features/spawning

[[features/_index|..]]

[[features/spawning/slot_accounting|slot_accounting]]: How spawn slots are
counted: unsettled statuses occupy a slot, settled and retired nodes free theirs
automatically, checks serialize under the worktrees lock, and re-entry paths
re-check before re-occupying a slot.

[[features/spawning/tree_limits|tree_limits]]: The three tree caps — children
(width), depth, and descendants — plus the spawn-time budget check: what each
bounds, which ancestor's configuration enforces it, and why enforcement needs no
agent cooperation.

***

Nodes create children, and three configured caps keep the resulting tree bounded
without relying on agent cooperation: a width cap on direct children, a depth
cap, and a descendants cap — plus a budget check that a child's cost cap fits
its parent's remaining run budget. This surface specifies where each cap is
enforced and how slots are counted.

- [[features/spawning/tree_limits|tree_limits]] — the three caps and the budget
  check, which ancestor enforces each, and when each applies.
- [[features/spawning/slot_accounting|slot_accounting]] — what occupies a slot
  (unsettled statuses), when a slot frees, the lock that makes checks race-free,
  and the re-entry re-checks on re-arm and unretire.

The lifecycle statuses this accounting keys on are specified in
[[features/lifecycle/status_machine|status_machine]].

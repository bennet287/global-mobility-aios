---
name: user_flow/finishing
desc: |
  How work concludes: the finish signal and who sends it, what the
  squash-merge does and guards, and how finished work climbs the tree to
  the base branch and the operator's review.
created: 2026-07-21T04:47:43Z
updated: 2026-07-21T04:47:43Z
---

# user_flow/finishing

[[_index|..]]

***

Work concludes in two distinct acts: **finishing** (a node's loop ends
gracefully) and **merging** (its branch's work lands on its parent). They are
separate commands because the operator reviews between them.

## The finish signal

`fractal node finish [<node>] [--reason="..."]` tells a node to stop after its
current iteration — the loop completes the iteration it is in (including its
commit) and exits rather than starting another. The signal fans out to the
node's active descendants children-first, so a manager's subtree winds down with
it. `--cancel` withdraws a pending finish that has not yet taken effect; the
cancel deliberately does not fan out, because a descendant finishing is its
normal completion path, not something to revoke.

Who sends it matters:

- **The node itself.** The designed happy path: NODE.md's Completion
  Requirements name the conditions, and the node runs
  `fractal node finish --reason="..."` in the iteration that meets them, landing
  status `completed`.
- **The operator.** A finish signal sent from outside ends the run at the same
  boundary; use it to conclude work that is good enough, or redirect effort.
  (The blunter siblings: `stop` ends after the current step, `kill` immediately
  — see [[user_flow/continue_resume]] for what each preserves.)
- **The root.** On the user node, finish is a tree-wide broadcast — the user
  node has no loop of its own, so it signals every active node in the tree.

How the run books depends on why it finished. A deliberate finish lands
`completed` — even when the signal arrives during reserve wind-down or the spend
crosses the cap mid-drain, the goal-met landing holds, with the overshoot
recorded on the run row. A budget stop is not a goal-met completion: the run
books `exited` (with exit code 0 — a designed stop, not an abnormal death), so a
parent and `node merge` can tell unfinished work from done. The loop's own
budget phrases are reserved in `--reason` — a reason carrying them classifies
the finish as a budget abort — so a node states its met goal in its own words.

A finished node is settled: its worktree and branch remain, holding its
committed work, ready for review and merge.

## What merge does

`fractal node merge <node>` squash-merges the node's branch into its merge
target — the node's configured base branch when one was set, else the dotted
parent (the branch name minus its last segment). The mechanics an operator
should know:

- **One commit lands.** The target receives a single squash commit named
  `merge <branch>`; the node's full per-iteration history stays on its own
  branch. Review the squash like any commit.
- **The node's machinery does not travel.** The node's `.fractal/<branch>/` seed
  is stripped from the staged merge, so a parent never accumulates its
  children's data directories. Work product only.
- **The wiki merges cleanly.** Generated wiki indexes are refreshed from the
  merged filesystem on the target, so both branches' wiki pages survive side by
  side.
- **Re-merges stay cheap.** After the squash, the child's merge-base is
  advanced, so merging the same node again later only diffs its new work instead
  of re-conflicting on everything already landed.
- **Guards.** Merge refuses while the node is active or paused, while the target
  node is active or paused (a running target's worktree must not be mutated
  under it — except by the target's own loop, which merges its settled children
  as part of its normal iteration), and while the target worktree has
  uncommitted changes. On conflict the target worktree is restored exactly as it
  was.
- **Conflicts finish with `--continue`.** After a conflicted merge, redo the
  squash by hand in the target worktree (`git merge --squash <branch>`), resolve
  and stage the conflicts, then run `fractal node merge <node> --continue`: it
  validates the staged squash came from the node's branch, then runs the merge's
  own tail — seed strip, index refresh, commit, merge-base advance — so a manual
  resolution never hand-rolls those steps or strands seed files in the target
  working tree. Its failure paths leave the staged resolution in place (never
  `reset --hard`); fix and re-run.
- **A resolution against the node does not reach it.** The squash records no
  per-hunk ancestry, so a hunk you resolve in the target's favor stays resolved
  only on the target — the node still carries its own version, and because the
  merge-base advanced, the next merge re-stages it cleanly and silently, undoing
  your decision without a conflict to warn you. A `--continue` therefore ends by
  naming every file where the target kept its content over the node's. Land that
  resolution on the node (or retire/delete it) for the decision to stick. The
  notice is scoped to what the node offered, so hunks you resolved the node's
  way, and content the target owns that the node never had, are not named.
- **Nothing to merge is a clean outcome.** A node whose changes are already on
  the target reports so and exits without committing. A `--continue` whose
  resolution kept the target's own content for every change the node offered
  reports that instead, and still finishes the tail — the squash state is
  cleared and the merge-base advances, so the resolved conflict is not replayed
  on the next merge.

## Reaching the base branch and review

Work climbs the tree the same way at every level. A child finishes; its parent
(a manager node, during its own iterations) reviews the child's branch, merges
it with the same squash machinery, and integrates. At the top of the tree, the
operator plays the parent: a top-level node's merge target is the branch
`fractal init` ran on, and its squash commit lands in the operator's own
checkout of that branch.

The operator's review loop for a finished top-level node:

1. Inspect: `git diff <base>...<branch>` shows the node's work from the merge
   base; the node's radio outbox and its plan files narrate intent.
2. Merge: `fractal node merge <node>` from a settled tree — the squash commit is
   now on your branch, pushable and revertable like any commit.
3. Iterate or clean up: if more work is needed, brief and relaunch the node
   ([[user_flow/continue_resume]]); if the node is done for good, delete it
   ([[user_flow/teardown]]) — the warning on deletion tells you if unmerged
   commits would be lost.

Merging is deliberately not automatic at the top: nothing reaches the base
branch without an operator (or a parent node's explicit iteration decision)
running the merge.

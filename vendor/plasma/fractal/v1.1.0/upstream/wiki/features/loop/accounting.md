---
name: features/loop/accounting
desc: |
  Run, iteration, and step accounting: the row tables and events in the
  tree's central database, the shared status set, exit codes, and how pauses
  credit time back to deadlines.
created: 2026-07-21T05:04:14Z
updated: 2026-07-21T05:04:14Z
---

# features/loop/accounting

[[_index|..]]

***

Every run, iteration, and step the loop executes is booked as a row in the
tree's central SQLite database (one per tree, in the root node's data
directory). The loop-facing persistence API is the record surface in
`fractal/core/record.py`: lifecycle transitions funnel through first-writer-wins
fenced updates, events are point-in-time log entries, and signals are consumable
control rows. Every row carries a `node` column naming its owner, so one
database serves the whole tree.

## The row hierarchy

A **run** row spans one `start`-to-exit lifetime of the loop and carries the
agent, the run's cost cap, status, exit code, and start/end instants. An
**iteration** row belongs to a run and adds the iteration number and the agent,
model, and session that executed it. A **step** row belongs to an iteration and
records the step number and name, the executing agent, model, and session, the
step's cost, and its approval state. Failed step launches retry as fresh step
rows, so attempts are individually accounted. Durations are never stored -- rows
carry start and end instants and duration is derived.

## Statuses, exit codes, and events

One status set (`fractal.constants.STATUSES`) is shared by the node status file
and every row table, though not every status applies at every level: a run that
ends without completing is `exited`, never `failed` -- `failed` belongs to
entity rows like iterations and steps. Exit codes are binary, derived from
outcome: `0` marks a designed landing (a completed finish, a requested stop, or
a budget abort -- exited with exit `0` is how a budget landing is told apart
from an abnormal end; see [[features/cost/budgets|budgets]]) and `1` marks an
abnormal one (timeout, a failed final iteration, an unexpected death). A run
that ends for a reason carries it in the row's metadata, which is what
`fractal node activity` shows. Events are point-in-time entries with optional
step/iteration/run lineage: commits, pauses, resumes, and their kin each land as
one event, a model drop (a step served off its pinned model, see
[[features/loop/steps|steps]]) events against the dropped attempt's row, and
pause/resume event instants credit the paused span back to run and iteration
deadlines, so a paused node is not billed wall-clock time against its budgets
(the credit walk's exact semantics live in
[[features/cost/time_budgets|time_budgets]]). The commit pipeline logs each work
commit as an event keyed on the new sha, tying git history back to the row that
produced it (see [[features/loop/commit_pipeline|commit_pipeline]]).

## Reading the ledger

Row history is append-only in effect: deleting a node removes its registry rows
and subscriptions but all history rows persist. Cost figures on an active row
are provisional -- only a terminal registry status makes a run's figure final.
The `fractal node` CLI surfaces the ledger (status, cost, and time remaining)
without touching the rows directly.

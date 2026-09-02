---
name: features/loop/plans
desc: |
  Plan files: the per-iteration planning artifacts under the node's plans
  directory, the fractal plan CLI that creates and lists them, and how the
  seed steps use them across the iteration.
created: 2026-07-21T04:51:13Z
updated: 2026-07-21T04:51:13Z
---

# features/loop/plans

[[_index|..]]

***

Every iteration records its intent in plan files — markdown documents under the
node's `plans/` directory, created and listed by the `fractal plan` CLI
(`fractal/core/plan.py`, `fractal/cli/cmd/plan.py`).

## Creating plans

`fractal plan init --name=<slug>` creates a plan file and prints its path. The
name is a snake_case slug (letters, digits, underscores only — validated at the
filesystem boundary). The file is named `{timestamp}-{run.iter}-{name}.md`: the
timestamp defaults to the current UTC time, so two plans written in the same
iteration get distinct names, and the `run.iter` segment is the iteration
reference (e.g. `12.5`), taken from `--iter-ref` or the `ITER_REF` environment
variable the loop exports.

The file is seeded with a single H1 heading, `# {run.iter} {title}`, so the run
and iteration are human-readable inside the file; `--title` sets the title,
which otherwise defaults to the de-slugged name. Creation is exclusive: an
exact-name collision surfaces as an error rather than silently replacing the
earlier plan.

## Listing plans

`fractal plan list` prints this iteration's plan files, one per line. It
resolves "this iteration's plans" by globbing the `run.iter` segment of the
filename, so it returns every plan the iteration wrote — zero, one, or many —
sorted by name (chronological by timestamp), without relying on file
modification times. A node with no plans directory yet lists nothing.

## How the loop uses plans

The seed steps (see [[features/loop/steps]]) thread plans through the iteration:

- **PLAN** creates the iteration's plan file with `fractal plan init` and writes
  the plan below the seeded heading, one plan per concern when the work splits
  cleanly. When a prior iteration was interrupted, PLAN adopts its existing plan
  and continues rather than starting fresh.
- **EXECUTE** carries the plan out.
- **REVIEW** appends a post-mortem section — accomplishments, deviations,
  next-iteration notes — to each plan the iteration wrote, found via
  `fractal plan list`; an adopted plan from an interrupted iteration gets the
  post-mortem instead.

Plans live in the node directory, not the work product: they document the node's
own reasoning across iterations and are stripped when work merges up.

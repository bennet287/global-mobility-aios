---
name: fractal
desc: Hierarchical agent loops with recursive self-organization.
tags: []
sources: []
created: 2026-07-12T02:13:53Z
updated: 2026-07-21T04:35:35Z
---

# fractal

[[architecture/_index|architecture/]]: What fractal is and how it fits together:
the node tree model, the worktree-per-node design, the agent-provider seam, the
central per-tree database, and the package layout.

[[configuration/_index|configuration/]]: The complete configuration reference:
every node initialization flag and config key, step files and their frontmatter
overrides, the node scripts, and what children inherit.

[[design/_index|design/]]: Why fractal is shaped the way it is: budget and
reserve rationale, durability guarantees, commit and merge discipline, and the
lifecycle status model.

[[features/_index|features/]]: One sub-branch per feature surface: lifecycle,
the iteration loop, radio, cost accounting, spawning, chat, the TUI, files and
transcripts, agent providers, and the wiki system.

[[source_map|source_map]]: A mapping from source paths to the wiki pages that
document them, so an agent editing a module can find its page in one hop.

[[user_flow/_index|user_flow/]]: End-to-end operator journeys: initializing a
fractal, configuring and launching nodes, monitoring and steering, finishing and
merging, pausing and resuming, and tearing down.

***

Fractal runs trees of autonomous agent loops, each node working in its own git
worktree and merging results back up the tree. This wiki is the descriptive
reference: it explains behavior, contracts, and design for a reader deciding how
to use or extend fractal — not a line-level code walkthrough.

Start from what you are trying to do:

- **Understand the system.** [[architecture/_index|architecture]] explains what
  fractal is and how it fits together: the node tree, worktrees, the
  agent-provider seam, the central database, and the package layout.
  [[design/_index|design]] explains why it is shaped this way: budgets and
  reserves, durability, commit discipline, and the status model.
- **Operate a fractal.** [[user_flow/_index|user_flow]] walks the operator's
  journey end to end: init, configure, launch, monitor, steer, finish, merge,
  and tear down. [[configuration/_index|configuration]] is the complete
  reference for every initialization flag, config key, step override, node
  script, and inheritance rule.
- **Go deep on one surface.** [[features/_index|features]] holds one sub-branch
  per feature surface: lifecycle, loop, radio, cost, spawning, chat, TUI, files,
  agents, and the wiki system.
- **Edit a source module.** [[source_map]] maps source paths to the pages that
  document them, one hop from file to reference.

A new reader gets the fastest orientation from
[[architecture/_index|architecture]] first, then [[user_flow/_index|user_flow]];
the remaining branches are references to dip into as needed.

---
name: features/lifecycle
desc: |
  The node lifecycle: creation, start, finish, stop, kill, pause, resume,
  retire, and delete, and the status machine that ties them together.
created: 2026-07-21T04:58:40Z
updated: 2026-07-21T04:58:40Z
---

# features/lifecycle

[[features/_index|..]]

[[features/lifecycle/commands|commands]]: The behavior contract of each node
lifecycle command: creation, start, finish, stop, kill, pause, resume, retire
and unretire, and delete — their guards, fan-out order across the subtree, and
refusal semantics.

[[features/lifecycle/script_delegation|script_delegation]]: How lifecycle
operations delegate their filesystem and process work to the shell scripts in
the node machinery, and where the lock boundary between database transitions and
script execution sits.

[[features/lifecycle/status_machine|status_machine]]: The node status set and
the rules of movement between statuses: which statuses exist, which apply to
nodes versus history rows, which signals are legal in each status, and how
events record every transition.

***

A fractal node moves through a small set of statuses, driven by lifecycle
commands that combine three ingredients: a status flip recorded in the central
database, an event row that timestamps the transition, and a shell script that
does the filesystem and process work. This surface specifies that machinery.

- [[features/lifecycle/status_machine|status_machine]] — the status set, which
  statuses apply at which level, the event log beside them, and which signals
  are legal in each status.
- [[features/lifecycle/commands|commands]] — the behavior contract of each
  lifecycle command: creation, start, finish, stop, kill, pause, resume,
  retire/unretire, and delete, including fan-out order and refusal semantics.
- [[features/lifecycle/script_delegation|script_delegation]] — how every
  lifecycle operation delegates its filesystem and process work to the shell
  scripts shipped in `fractal/_scripts/`, and where the locking boundary sits.

Child creation and the tree limits that gate it live in the sibling surface
[[features/spawning/_index|spawning]]; the iteration loop that a started node
runs is the [[features/loop/_index|loop]] surface.

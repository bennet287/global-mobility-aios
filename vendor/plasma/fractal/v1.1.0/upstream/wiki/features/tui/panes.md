---
name: features/tui/panes
desc: |
  The cockpit's four-pane grid -- tree, radio, node, and message -- and the
  focus-ring navigation that moves between them and drills into each pane's
  interior zones.
created: 2026-07-21T05:08:54Z
updated: 2026-07-21T05:08:54Z
---

# features/tui/panes

[[features/tui/_index|..]]

***

`fractal open` composes a single screen holding four panes: the tree pane and
radio pane across the top row with the node pane at the right, and the message
(compose) pane at the bottom left. The app shell (`fractal.tui.app`) owns
composition, theming, and key dispatch; each pane module under
`fractal/tui/panes/` owns its own interior, selection state, and key handlers,
and renders purely from the current snapshot (see [[features/tui/polling]]).

## Navigation

Focus moves on a two-level ring: an outer ring across the panes and inner
zone/mode ladders within each pane. `tab` and `shift+tab` step between fields
where a pane exposes them. Every pane renders from the same immutable snapshot,
so moving focus never triggers reads.

## The panes

- **Tree pane** -- a box-drawing view of every live node with a status dot,
  foldable per branch. Pressing `enter` on a row re-scopes the entire cockpit to
  that node: the headline interaction, from which the other panes follow.
- **Node pane** -- the focused node's card: status, the run/iter/step line,
  agent/model/session, measures, and config chips; below it a run -> iteration
  -> step explorer and a unified activity timeline. The card, the explorer, and
  the event log are three sub-zones sharing the pane. A toggle scopes the
  timeline to the node's own events or all descendants merged: a first visit
  defaults the user (root) node to descendants and every other node to its own
  activity, and a toggled choice sticks per node for the session.
- **Radio pane** -- three sources over the scoped node's radio: its own
  messages, the cross-subtree feed (every descendant's public/outbox posts), and
  the archive of saved messages. A zone ladder (source tabs, filters, rows)
  drives selection; opening a row shows a detail view with a Reply / Chat /
  React / Save action bar (see [[features/tui/actions]]).
- **Message pane** -- a segmented composer with two personalities: `chat` shows
  a per-branch transcript and streams agent replies (the cockpit door to the
  [[features/chat/_index|chat]] surface), while `radio` sends real messages -- a
  fresh send or a threaded reply -- through the action layer. Fields navigate as
  a grid, combo fields drop a filtered picker, and `/node`-style slash commands
  set fields straight from the body. Chat runs one turn at a time: a send typed
  while a turn is streaming queues (FIFO) behind it as a pending `you` line and
  dispatches when that turn finishes, against the branch it was typed on even if
  the cockpit has since re-scoped away. `ctrl+g` interrupts the in-flight turn
  from anywhere, the composer included (`ctrl+i` cannot serve, as terminals
  encode it as Tab): a lone queued send goes back into the composer for editing,
  several dispatch at once as one combined turn.

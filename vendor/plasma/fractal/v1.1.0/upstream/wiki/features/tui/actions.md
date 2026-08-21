---
name: features/tui/actions
desc: |
  The node actions available from the cockpit: explicit radio writes acting
  as the user node, a read-only attach onto a node's live tmux session, and
  the chat door into the message pane.
created: 2026-07-21T05:08:54Z
updated: 2026-07-21T05:08:54Z
---

# features/tui/actions

[[features/tui/_index|..]]

***

The cockpit is read-only by construction, with one deliberate write surface:
`fractal.tui.actions`, invoked exclusively from explicit key and submit handlers
-- never on a read or poll path. The acting identity is always the user (root)
node: the human at the cockpit.

## Radio writes

The action layer exposes exactly the radio verbs: **send** a message to any
node's channel, **reply** to a message (routed to its resolved destination,
inheriting the parent's priority unless overridden), **react** +1/-1, **save** a
message into the root's archive, and the **read receipt** stamped only when the
user actually opens a message -- the unread dot clears on the next snapshot. The
radio pane's detail action bar and the message pane's composer (see
[[features/tui/panes]]) are the two entry points.

## Session viewing

A cockpit-level key attaches onto the scoped node's live tmux session from
anywhere on the screen. The attach is read-only -- the node's terminal is a
window, not a control surface -- with `esc` (advertised on the session's status
line) as the way out; the cockpit suspends for the duration and restores on
detach. With no running session the cockpit notifies and stays put; when the
cockpit itself runs inside tmux it switches the client instead of nesting an
attach, and that outer client carries no read-only leash.

## Chat

Chatting with a node is its own surface rather than an action-layer verb: the
message pane's chat mode drives it, and a radio detail row's Chat action
re-scopes to the sender and forks its live session. Semantics -- transports,
seeding, lifecycle gating -- live in [[features/chat/_index|chat]].

## What the cockpit never does

No lifecycle mutations happen from the TUI: pause, resume, kill, spawn, and
config retunes stay on the `fractal` CLI. The cockpit observes the tree and
speaks over radio and chat; it does not operate the loops.

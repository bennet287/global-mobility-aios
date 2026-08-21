---
name: features/chat
desc: |
  The chat surface: sending one prompt to a node's agent and streaming
  the reply, from the CLI or the cockpit, without perturbing the node's
  running loop.
created: 2026-07-21T04:35:35Z
updated: 2026-07-21T04:50:29Z
---

# features/chat

[[features/_index|..]]

[[features/chat/addressing|addressing]]: How a chat turn is addressed and
delivered: the command form, the fresh/fork/resume session modes, prompt
seeding, and what a turn does and does not touch.

[[features/chat/lifecycle_gating|lifecycle_gating]]: Which lifecycle states
admit which chat shapes: chat itself is legal in every state, but the live loop
session exists only while a node is active or paused, and paused is the flagship
interrogation case.

***

Chat is the conversational door onto a node: one prompt in, one streamed agent
reply out. A chat turn always reaches a real agent process — the node's
configured agent, model, and reasoning effort — but leaves no trace in the
node's books: no cost rows, no session-record writes, and never a disturbance to
a running loop, because existing sessions are forked rather than continued
unless a resume is explicitly requested.

The surface has two doors that share one contract. The CLI command
`fractal node chat` resolves, validates, and streams a turn end to end; the
cockpit's chat pane (see [[features/tui/_index|tui]]) builds its invocation
through the same core seam, so validation, prompt seeding, and the wire
protocols cannot drift between the two.

- [[features/chat/addressing|addressing]] — the command form, target resolution,
  and the fresh/fork/resume session modes with their prompt seeding.
- [[features/chat/lifecycle_gating|lifecycle_gating]] — which lifecycle states
  admit which chat shapes, and why paused is the flagship case.

---
name: features/radio
desc: |
  Inter-node messaging: channels, routing and defaults, subscriptions and
  feeds, read receipts, saved messages, and message discipline.
created: 2026-07-21T04:50:25Z
updated: 2026-07-21T14:07:58Z
---

# features/radio

[[features/_index|..]]

[[features/radio/channels|channels]]: The per-node channel model: the four
default channels, the read-only and write-only permission flags that define
them, and custom channel creation and deletion.

[[features/radio/reactions_and_replies|reactions_and_replies]]: Threaded
conversation semantics: reactions as acknowledgements, reply routing and
inheritance, the thread view with its participant exemption, and unsend.

[[features/radio/read_receipts|read_receipts]]: Read state semantics: listings
are passive, the read command writes per-reader receipts for exactly what it
displays, and reacting or replying also marks the parent read.

[[features/radio/routing|routing]]: The message-writing verbs and their routing
contracts: send targets any writable channel and defaults a named target to its
inbox, while post is the quiet publicly readable subset that defaults its
channel by target.

[[features/radio/saved_messages|saved_messages]]: The saved-message archive: an
owned snapshot that survives unsend, serving as a node's cross-iteration action
queue.

[[features/radio/subscriptions_and_feeds|subscriptions_and_feeds]]: How nodes
follow each other: subscription rows, automatic wiring between parent and child,
blind nodes, and the feed that fans reads out across subscriptions.

***

Radio is fractal's inter-node messaging system, implemented by the `Radio` class
in `fractal/core/radio.py` and exposed as the `fractal radio` CLI sub-app
(`fractal/cli/cmd/radio.py`, with channel management in
`fractal/cli/cmd/channel.py`). All state lives in the tree's central database:
messages, channels, subscriptions, read receipts, reactions, and the
saved-message archive.

The surface splits into:

- [[features/radio/channels]] — the default channel set, permission flags,
  custom channels, and channel deletion.
- [[features/radio/routing]] — the `send` and `post` verbs, their routing
  dimensions and channel defaults, and the stderr routing echo.
- [[features/radio/subscriptions_and_feeds]] — subscriptions, auto-wiring at
  node creation, blind nodes, and the merged feed view.
- [[features/radio/read_receipts]] — passive listings versus the receipt-writing
  `read` surface, and per-reader read state.
- [[features/radio/saved_messages]] — the archive as a cross-iteration action
  queue.
- [[features/radio/reactions_and_replies]] — acknowledgement reactions, reply
  routing and inheritance, threads, and unsend.

Messages carry an 8-character uppercase hex UUID (unique across the tree), a
subject, a priority (0-10, validated against shared bounds in
`fractal.constants`), a sender, an optional agent session reference tying the
message to the conversation that wrote it (the acting step's recorded session,
else the sender's live session), and a body. The iteration loop's sync step (see
[[features/loop/_index|loop]]) is the main consumer: it reads inbox and feed
each step, reports outward via the outbox, and — when the parent is the user
node — sends what needs the human's attention (above all, replies to user
messages) to the user's inbox.

---
name: features/radio/saved_messages
desc: |
  The saved-message archive: an owned snapshot that survives unsend,
  serving as a node's cross-iteration action queue.
created: 2026-07-21T04:50:25Z
updated: 2026-07-21T04:50:25Z
---

# features/radio/saved_messages

[[_index|..]]

***

`fractal radio save <uuid>` copies a message into the archive table — an owned
snapshot keyed on (saver, message UUID). Because it is a copy, a saved message
survives the sender's unsend; because of the key, re-saving is idempotent and
each node's archive is its own. Saving respects channel permissions: a non-owner
cannot save from a read-only channel.

`fractal radio unsave <uuid>` removes the caller's archived copy (only the
caller's — the lookup is scoped to the saver) and errors if none exists.

The saved set is listed with `fractal radio messages --saved` (or
`feed --saved`; both list the same archive). `--saved` is mutually exclusive
with the `--read`/`--all` filters — archive rows carry no unread state — and
supports the usual `--channel`, `--limit`, `--since`, `--recent`,
`--csv`/`--json` shaping. Unlike the metadata-only mailbox listings, saved rows
always include the body — the archive is a snapshot, and listing it is reading
your own copies. Rows carry the original sender, channel, and an owner column
naming the message's source host; the feed listing's node-filter keys on that
owner.

By convention (see the node seed's radio guidance), the archive is the
cross-iteration action queue: save what needs later work, review the open set
every sync, and unsave each item when its work is done — read state tracks what
a node has *seen*, the archive tracks what is still *open*.

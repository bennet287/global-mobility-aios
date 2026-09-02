---
name: features/radio/reactions_and_replies
desc: |
  Threaded conversation semantics: reactions as acknowledgements, reply
  routing and inheritance, the thread view with its participant
  exemption, and unsend.
created: 2026-07-21T04:50:25Z
updated: 2026-07-21T04:50:25Z
---

# features/radio/reactions_and_replies

[[_index|..]]

***

## Reactions

`fractal radio react <uuid> <+|->` records a positive or negative reaction.
Reactions are keyed on (message, reactor), so re-reacting changes the value in
place rather than stacking. A reaction also marks the message read for the
reactor — an ack clears it from unread views. Non-owners cannot react into
read-only channels. Every mailbox listing row (`messages`, `feed`, `sent`)
carries live `pos_reacts` and `neg_reacts` counts.

## Replies

`fractal radio reply <uuid> <data>` threads a reply under its parent, located
globally by UUID. The reply inherits the parent's subject as a single canonical
`Re: ` prefix (never stacked) and, unless `--priority` is passed, the parent's
priority; there is no subject option. Replying also marks the parent read for
the replier.

Routing derives from where the parent sits, never from a verb choice:

- a reply to a message in the caller's own inbox is a conversation turn — it
  lands in the original sender's inbox;
- a reply to a message in another node's write-only channel (an outbox broadcast
  seen in a feed) reroutes the same way, to the author's inbox, rather than
  piercing the owner-only channel;
- any other reply threads in place, in the parent's host channel.

The resolved destination echoes on stderr exactly as [[features/radio/routing]]
describes for send — most valuable here, where the destination is derived, not
named. A bystander — neither the parent's host owner nor its sender — cannot
reply into a privately readable channel.

## Threads

Only thread roots (plus replies rerouted across channel-spaces, which are new
mail for their host) appear in mailbox listings; in-place replies stay behind
the parent's live reply count. `fractal radio thread <uuid>` shows the whole
tree — root and every reply, depth-annotated, siblings in creation order — from
any message in it, walking parent links regardless of host, so a rerouted
conversation still renders as one thread. Privately readable channels are
owner-only, but thread participants are exempt: the original sender of a
rerouted conversation can view and continue their own thread whole. A bystander
naming a publicly readable root sees only the rows they are authorized to read.

## Unsend

`fractal radio unsend <uuid>` deletes a sent message — sender-only. A message
with replies is refused unless `--force` deletes the whole thread, since the
cascade (replies, reactions, receipts) also removes other nodes' replies; a
reply arriving mid-delete aborts with a retry hint. Saved copies survive, as
[[features/radio/saved_messages]] describes.

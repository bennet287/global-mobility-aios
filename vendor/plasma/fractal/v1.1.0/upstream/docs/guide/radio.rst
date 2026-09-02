Radio
=====

Radio is fractal's inter-node messaging system. Every node in a tree —
including the user (root) node — owns a mailbox in the tree's central
database, and running agents use radio to report progress upward, receive
directives, and coordinate with their children while the user reads along.
This page explains the model: channels, the two composing verbs, read state,
threads, reactions, saving, and subscriptions. Exact command syntax and the
full option surface live in the :doc:`/cli/radio` reference.

All radio state lives in the tree's one central SQLite database (see
:doc:`/guide/architecture`), so every node — and the user, from any checkout
inside the repository — sees the same messages immediately.

Channels
--------

Each node owns a *channel-space*: a set of named channels other nodes address
messages to. These default channels are seeded when the node is created:

.. list-table::
   :header-rows: 1
   :widths: 12 20 20 48

   * - Channel
     - Who can read
     - Who can write
     - Purpose
   * - ``public``
     - anyone
     - anyone
     - an open board on the node
   * - ``private``
     - owner only
     - owner only
     - the node's notes to itself
   * - ``inbox``
     - owner only
     - anyone
     - incoming mail: directives, questions, replies
   * - ``outbox``
     - anyone
     - owner only
     - the node's broadcasts and status reports

Channel permissions are two flags, and both are *owner-relative*:
``read_only`` means only the owner can read the channel, and ``write_only``
means only the owner can write to it. This is why ``inbox`` is marked
``read_only`` (mail is for the owner's eyes) yet writable by anyone, and why
``outbox`` is marked ``write_only`` (only the owner broadcasts) yet readable
by everyone. The flags have two knock-on effects worth remembering: a
``read_only`` channel cannot be subscribed to, and a message in a
``write_only`` channel cannot be replied to in place — the reply reroutes to
its author's inbox (see `Threads and replies`_).

Custom channels
~~~~~~~~~~~~~~~

``fractal radio channel create <name>`` registers an additional channel in
the acting node's channel-space; ``--read-only`` and ``--write-only`` set the
flags (both default off, so a bare create makes a fully public channel). The
default names are reserved, and an existing channel is never silently
redefined — delete it and recreate it to change its flags.
``fractal radio channel delete <name>`` removes a custom channel (default
channels refuse); a channel that still holds messages requires ``--force``,
which cascades its messages, reactions, receipts, and subscriptions.
``fractal radio channel list`` shows the cwd (or ``--path``) node's channels
and flags. Channel names are scoped per node: two nodes may each define a
``reports`` channel with different flags.

Send and post
-------------

Two verbs write messages, and they differ in channel class and defaults:

- ``fractal radio send`` is the general verb. It writes to any channel its
  write permissions allow, but it requires at least one routing dimension —
  a target node (``--node=<branch>`` or ``--parent``) or a ``--channel``. A
  bare ``send`` is refused and points at ``post``.
- ``fractal radio post`` is the public subset. It writes only to *publicly
  readable* channels (``outbox``, ``public``, and custom channels without the
  ``read_only`` flag) and refuses privately readable ones, pointing back at
  ``send``. A bare ``post`` lands in your own ``outbox`` — the report-upward
  default, since the parent is subscribed to it.

Both require ``--subject`` and ``--priority`` (an integer 0--10). When no
``--channel`` is given, the defaults are:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Command and target
     - Default channel
   * - ``send`` to a named target (the sender's own node included)
     - the target's ``inbox`` — a private self-note is explicit via
       ``--channel=private``
   * - ``post``, bare or to yourself
     - your own ``outbox``
   * - ``post`` to another node
     - the target's ``public`` board (its ``outbox`` is owner-only write)

An explicit ``--channel`` always wins. Writing into another node's
``write_only`` channel is refused (owner only), and the target must be the
tree root or a registered node — a deleted node is no longer addressable.

Both verbs print the new message's UUID on stdout (for scripts) and echo the
resolved routing on stderr; ``send`` additionally names each dimension it
defaulted. Here the first command runs at the tree root and the second inside
the ``main.parser`` worktree, whose bare ``post`` reports to its own outbox:

.. code-block:: console

   $ fractal radio send "focus on error recovery next" --node=main.parser \
         --subject="direction" --priority=6
   <uuid>
   Channel unspecified: sending to main.parser's 'inbox' channel.
   sent to main.parser's 'inbox' channel

   $ fractal radio post "scaffolding done; starting error recovery" \
         --subject="progress" --priority=3
   <uuid>
   sent to main.parser's 'outbox' channel

Every message carries an 8-character uppercase hex UUID, unique across the
whole tree; commands that take a UUID accept it case-insensitively. Messages
also record the sender's branch, a UTC timestamp, and the agent session that
wrote them when one is known — the acting step's recorded session, or the
sender's live session outside a step.

Priorities
~~~~~~~~~~

Priority is a required integer from 0 to 10 and drives the default listing
order (highest first). By convention across the tree:

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Priority
     - Meaning
   * - 0--1
     - ambient chatter
   * - 2--3
     - routine kickoff and progress reports
   * - 4--5
     - milestones and integration notices
   * - 6
     - needs action from the recipient
   * - 7
     - lifecycle exits (matches the loop's own sign-off messages)
   * - 8--10
     - urgent directives

Unsending
~~~~~~~~~

``fractal radio unsend <uuid>`` deletes a sent message — only the sender
can. A message that already has replies is refused unless ``--force`` is
passed, which deletes the whole thread including other nodes' replies,
reactions, and receipts. The cascade is best-effort, not atomic: a reply
arriving mid-unsend is detected and the command asks for a retry. A saved
copy in another node's archive survives an unsend (see `Saving messages`_).

Feeds, listings, and read state
-------------------------------

Radio distinguishes *listing* (metadata, passive) from *reading* (bodies,
receipt-writing). Read state is per reader, with seen-by-you email
semantics: your receipts never change another node's unread view.

Listings are passive
~~~~~~~~~~~~~~~~~~~~

``fractal radio messages`` lists the cwd (or ``--path``) node's mailbox;
``fractal radio feed`` merges the mailboxes it is subscribed to (each row's
``node`` column names its source); ``fractal radio sent`` lists outbound mail
across every recipient (each row's ``node`` column names the recipient, and
replies list first-class). ``messages`` and ``feed`` show metadata only —
sender, channel, subject, priority, UUID, and live
``replies``/``pos_reacts``/``neg_reacts`` counts — never the body;
``sent``, your own outbound mail, includes the body column in its rows. None
of them ever changes read state, so the unread view is stable across calls.

Two defaults narrow a bare ``messages`` call: it shows the ``inbox`` channel
only (``--channel`` selects another) and unread rows only (``--all`` shows
everything, ``--read`` the already-read ones; ``feed`` shares the same
filter). When the default view is empty, the total is disclosed on stderr:
``0 unread (N total; --all shows everything)``. Listings sort by priority
descending, then oldest first; ``--recent`` switches to newest first.
``sent`` is also priority-sorted by default — do not treat its first row as
the latest message.

Mailbox listings show thread roots plus replies that arrived from another
channel-space; a reply that threaded in place hides behind its parent's
``replies`` count and is found with ``thread`` (see below). In ``messages``
and ``feed``, bodies appear only with ``--json --body`` — still passive, no
receipts.

Reading writes receipts
~~~~~~~~~~~~~~~~~~~~~~~

``fractal radio read`` is the body surface: it prints full messages
(header lines for UUID, sender, host node, timestamp, channel, subject, and
priority, then the body) and writes the reader's read receipt for exactly the
rows it printed. It takes explicit UUIDs and/or selectors — ``--channel``
for one channel of a mailbox, ``--feed`` for everything the mailbox is
subscribed to — and ``--unread`` narrows the selectors to unreceipted rows
(explicit UUIDs always return). The routine catch-up is:

.. code-block:: console

   $ fractal radio read --channel=inbox --unread
   $ fractal radio read --feed --unread

Replying to a message and reacting to it also mark it read, so an
acknowledged item stops resurfacing. Reading a privately readable channel you
do not own is refused (owner only), with a participant exemption for
threads described below.

One subtlety on ``read``: ``--path`` selects only the *mailbox viewed*, never
who is reading. The reader is always the node the command runs as (see
`Sender identity`_), and receipts attribute to that reader even when browsing
another node's mailbox. Naming a mailbox in a different tree is refused.

Threads and replies
-------------------

``fractal radio reply <uuid> <data>`` answers a message. There is no
send/post choice to make — the routing is derived from where the parent
message sits:

- A reply to a message in *your own inbox* is a conversation turn: it lands
  in the original sender's inbox.
- A reply to a message in another node's ``write_only`` channel (an
  ``outbox`` broadcast) also reroutes to its author's inbox — the broadcast
  channel itself never carries it.
- Any other reply threads in place, in the parent's host channel (a
  ``public`` post is answered on the same board).

Replies inherit the parent's subject with a single canonical ``Re:`` prefix
(there is no subject option) and its priority unless ``--priority`` is
passed. Replying also marks the parent read for you. A bystander — a node
that is neither the message's host nor its sender — cannot reply into a
privately readable channel.

``fractal radio thread <uuid>`` renders the whole conversation: it climbs
from any message to the thread root and returns the full reply tree, oldest
first, with a depth per row (indented on a TTY). Thread participants — any
node that hosts or sent a row — see the entire tree, so a rerouted
conversation reads whole for both parties even though its turns live in two
inboxes. A bystander is gated by the named message's channel, and rows it may
not read are dropped from the output.

Reactions
---------

``fractal radio react <uuid> +`` (or ``-``) records a one-per-node
acknowledgment: re-reacting changes your vote rather than adding another, and
reacting also marks the message read. Reaction totals surface as the
``pos_reacts``/``neg_reacts`` columns in listings. The convention between
agents: reply when the response carries content, react to acknowledge the
rest.

Saving messages
---------------

Read state tracks what a node has *seen*; saving tracks what is still *open*.
``fractal radio save <uuid>`` copies a message into the node's archive — an
owned snapshot that survives a later unsend; re-saving is idempotent.
``fractal radio unsave <uuid>`` removes your copy when the work is done, and
``fractal radio messages --saved`` (or ``feed --saved``) lists the open set.
Agents run this as a todo loop: read new mail, save the actionable items,
unsave each when handled, and review the saved set every iteration.

Subscriptions and the feed
--------------------------

A subscription makes another node's channel part of your feed. Wiring is
automatic at spawn time: a new node subscribes to its parent's readable
channels, a parent subscribes to each new child's readable channels, and on
re-init a node also picks up its existing direct children. The result is that
a node's feed spans exactly one hop — its parent and its direct children —
so information crosses more levels by relaying: each tier posts to its own
``outbox`` and its parent carries the news upward.

A node created with the ``blind`` configuration key (the
``fractal node init --blind`` flag; see :doc:`/configuration`) subscribes to
nothing — it has no feed — while the parent's subscription to it is
unaffected, so its reports still flow upward.

Beyond the automatic wiring, ``fractal radio sub --node=<branch>`` subscribes
to any registered node: with ``--channel`` it subscribes to that one channel
(which must exist and be readable — ``inbox`` and ``private`` refuse),
without it to every channel readable *at that moment* (a channel created
later is not added automatically). ``fractal radio unsub --node=<branch>``
removes the matching subscriptions (all of them without ``--channel``) and
reports the true count — ``Removed 0 subscriptions.`` still exits 0, and
means nothing matched. ``fractal radio subs`` lists the cwd (or ``--path``)
node's subscriptions.

``fractal radio feed`` fans one query out per subscription, merges the rows,
and re-sorts them; a subscribed channel that has since been deleted or made
owner-only silently drops out, and ``--limit`` applies after the merge. Like
``messages``, the feed defaults to unread rows and never writes receipts —
``fractal radio read --feed --unread`` is the consuming counterpart.

Sender identity
---------------

Radio has no ``--as`` flag: the acting node is resolved from the exported
``_NODE`` environment variable and the working directory. Every verb that
writes a row attributed to the acting node — ``send``, ``post``, ``reply``,
``react``, ``unsend``, ``save``, ``unsave``, ``sub``, ``unsub``, ``channel
create``, ``channel delete`` — acts as an explicit ``--path`` when given,
else as the calling node the loop exported ``_NODE`` for — so a production
write attributes to the node whose loop is running, wherever the CLI call
runs from — else as the node owning the working directory. ``read``
resolves its actor env-first the same way, minus ``--path`` (the reader
its receipts attribute to): its ``--path`` picks only the mailbox viewed,
and receipts still attribute to the actual reader. The pure listings
(``messages``, ``sent``, ``feed``, ``thread``, ``subs``, ``channel list``)
take ``--path`` as a subject selector — whose mailbox or rows are viewed —
defaulting to the working directory's node.

Every message is stamped with its sender's branch and, when one is known, the
agent session that wrote it (the acting step's recorded session, or the live
session outside a step) — so a message is traceable to the exact conversation
that produced it, and the :doc:`TUI </tui>` can fork that session to ask the
author about it.

Radio in the agent loop
-----------------------

Running agents do not poll radio ad hoc: when the ``sync`` configuration key
is enabled (the default), the loop runs a sync pass before every step (see
:doc:`/guide/loop`). In that pass the agent reads its unread inbox and feed,
acts on parent directives first, replies or reacts to what it read, posts
progress to its ``outbox``, steers its children through their inboxes, and
maintains its saved set. Because reply and react clear unread state, an item
the agent acknowledges stops resurfacing at every sync — and an item it
merely lists does not.

The seeded conventions agents follow: report upward via the ``outbox`` (the
parent is subscribed), reach a specific node via its ``inbox``, keep bodies
small and operational (bulk content belongs in files or the project wiki,
with a pointer in the message), and use radio for live coordination while
lasting knowledge goes to memory or the wiki.

Reading along as the user
-------------------------

The user (root) node is a full radio participant with no loop — a passive
mailbox. Children report into its feed and inbox, and nothing consumes those
messages until you (or the operating agent acting as the root node) do. From
the repository root:

.. code-block:: console

   $ fractal radio read --channel=inbox --unread
   $ fractal radio read --feed --unread
   $ fractal radio send "wrap up and merge" --node=main.parser \
         --subject="directive" --priority=8

The :doc:`TUI </tui>` cockpit offers the same view interactively: a radio
pane for browsing any node's messages and a composer for sending, replying,
and reacting — always acting as the root node. For scripting, the message
listings print CSV when piped and take ``--json`` (``channel list`` offers
CSV only); see :doc:`/cli/radio` for the exact output contracts. The
messaging internals are documented at `fractal.core.radio.Radio` in the API
reference (:doc:`/api`).

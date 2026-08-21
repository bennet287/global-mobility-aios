---
name: features
desc: |
  One sub-branch per feature surface: lifecycle, the iteration loop, radio,
  cost accounting, spawning, chat, the TUI, files and transcripts, agent
  providers, and the wiki system.
created: 2026-07-21T04:35:35Z
updated: 2026-07-21T05:25:49Z
---

# features

[[_index|..]]

[[features/agents/_index|agents/]]: Agent providers and routes: the supported
agent backends, model and effort overrides, and how a new provider slots in.

[[features/chat/_index|chat/]]: The chat surface: sending one prompt to a node's
agent and streaming the reply, from the CLI or the cockpit, without perturbing
the node's running loop.

[[features/cost/_index|cost/]]: Cost accounting and budgets: how spend is
measured and attributed, how token usage is priced, the run/iteration/step cost
cap tiers with their reserve window, and the time budget tiers with the pause
credit-back.

[[features/files/_index|files/]]: The files and transcript surface: how a node's
work product is listed, diffed, and read, and how agent transcripts resolve.

[[features/lifecycle/_index|lifecycle/]]: The node lifecycle: creation, start,
finish, stop, kill, pause, resume, retire, and delete, and the status machine
that ties them together.

[[features/loop/_index|loop/]]: The iteration loop: the step sequence, prompt
assembly, plans, the commit pipeline, and run and iteration accounting.

[[features/radio/_index|radio/]]: Inter-node messaging: channels, routing and
defaults, subscriptions and feeds, read receipts, saved messages, and message
discipline.

[[features/spawning/_index|spawning/]]: Child node spawning and tree limits:
depth, width, and descendant caps, slot accounting, and spawn-time enforcement.

[[features/tui/_index|tui/]]: The cockpit TUI opened by the fractal open
command: a four-pane live view of the whole tree, radio and chat from the
keyboard, and a read-only window onto any node's session.

[[features/wiki_system/_index|wiki_system/]]: The wiki system: the two knowledge
stores, the wiki CLI, page and index conventions, and how wikis merge across
branches.

***

Each sub-branch documents one feature surface in depth: its commands, its
behavior contracts, and its edge semantics. A surface page answers three
questions -- what can be invoked, what the invocation guarantees, and what
happens at the edges (illegal states, races, budget boundaries, teardown). Pages
describe behavior and design, not implementation: they name modules and
commands, and they stay true through any refactor that preserves behavior.

## How the surfaces group

**Controlling nodes.** [[features/lifecycle/_index|lifecycle]] specifies the
status machine and the `fractal node` commands that drive it -- init, start,
finish, stop, kill, pause, resume, retire, delete -- and which signals are legal
in which status. [[features/spawning/_index|spawning]] covers the tree-shape
side of creation: depth, children, and descendant caps, where each is enforced,
and how slots are accounted. [[features/chat/_index|chat]] is the one-shot
conversational entry point (`fractal node chat`) and the lifecycle states that
accept it.

**Running work.** [[features/loop/_index|loop]] specifies the iteration engine a
started node runs -- the step sequence, prompt assembly, plan files, and the
commit pipeline behind `fractal commit`. [[features/cost/_index|cost]] covers
how every agent invocation is priced and attributed, the budget cap tiers, the
reserve window, and time budgets. [[features/agents/_index|agents]] documents
the provider seam the loop launches through: supported backends, model and
effort overrides, and how a new provider slots in.

**Observing and communicating.** [[features/radio/_index|radio]] is the
inter-node messaging system (`fractal radio`): channels, routing defaults,
subscriptions and feeds, receipts, saves, reactions, and replies.
[[features/tui/_index|tui]] is the cockpit `fractal open` launches -- panes,
navigation, live polling, and the node actions available from it.
[[features/files/_index|files]] is the work-product surface: a node's
contribution listing, anchors and per-file history, path-validation tiers, and
per-agent transcripts.

**Recording knowledge.** [[features/wiki_system/_index|wiki_system]] covers the
`wiki` CLI and the two knowledge stores -- the shared project wiki and per-node
memory -- page conventions, index regeneration, and merge behavior.

Not every surface is a command group: lifecycle, radio, cost, chat, and
wiki_system are CLI-facing; the loop runs in-process inside a started node; tui
is a single entry command; and files and agents are internal facades other
surfaces consume -- their pages document contracts reached through the TUI,
chat, and the loop rather than a dedicated command.

## Reading order and siblings

Start from the surface you are touching; each sub-branch's `_index.md` orients
its own pages. The `architecture` branch explains how these surfaces fit
together structurally; `design` records why they are shaped this way;
`configuration` is the flag-by-flag reference for the knobs these pages mention;
`user_flow` walks operator journeys across several surfaces at once. This branch
is where each individual surface is specified.

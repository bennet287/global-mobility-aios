---
name: features/files/anchors_and_history
desc: |
  How the base, commit, iteration, and run diff anchors resolve from the
  node's own record, and the per-file history walk behind a changed listing.
created: 2026-07-21T04:45:55Z
updated: 2026-07-21T04:51:52Z
---

# features/files/anchors_and_history

[[features/files/_index|..]]

***

Every changed listing, before/after read, archive, and history on the files
surface keys off a `since` anchor — a fixed git ref the surface diffs
`<anchor>...HEAD` against. Four scopes exist:

- **`base`** — the node's fork point: the whole contribution since init.
- **`commit`** — the previous commit (`HEAD`'s parent).
- **`iteration`** / **`run`** — the most recent iteration or run that committed.

## Resolution from the node's own record

Anchors resolve from the node's own record in the central database, not from
branch refs: init stamps the fork sha on the `init` event, and the commit
pipeline logs a `commit` event per save carrying the sha and its run/iter
lineage. That makes every anchor a fixed point in the node's own history that
*survives merges* — a parent-branch anchor would collapse to empty the moment
the parent absorbs the node's commits. Every query is node-scoped (the database
is tree-central, so an unscoped read would anchor on a sibling's commit) and
floored at the node's newest `init` event, so a re-init of a previously deleted
branch name never reads a dead namesake's events.

Fallbacks keep each scope resolvable:

- `base` prefers the fork sha stamped at init; a record without the stamp
  anchors just before the node's first `commit` event; a node that never
  committed falls back to the merge-base of its configured base branch (or the
  dotted parent implied by its branch name) with `HEAD`, pinned to a sha so the
  changed set, the membership probe, and a before-side read all key the same
  fixed point.
- `iteration`/`run` walk the node's own commits (first-parent, no merges,
  bounded at `base`) newest-first and resolve each to a scope: through its
  `commit` event where the pipeline logged one, else by matching the commit's
  author time against the scope rows' start/end windows — so a raw agent commit
  the pipeline never evented still lands on the run that made it. Author time
  survives rebases and amends but is fresh on a squash, so adopted work credits
  the adopting run. The newest resolvable commit names the scope, and the anchor
  sits just before that scope's oldest commit. A commit matching no scope (an
  upload, a between-runs save) is skipped, never misattributed.

A scope with no anchor — `commit` on a root commit, `iteration`/`run` when
nothing attributable was committed — yields an empty changed listing rather than
an error.

## Per-file history

History is the per-file trail behind a changed listing: the same first-parent,
no-merges walk as the listing's membership (see
[[features/files/contribution|contribution]]), scoped to one path, newest first.
It shows exactly the commits that made the file a member — never a merge or a
merged-in side history. Each entry carries the commit sha, its author-time
instant, its subject, and that commit's *own* line counts for the file (`None`
for binary) — unlike the listing's net counts — so the trail sums the work over
time. The default scope is `base`; a scope with no anchor, or a file no own
commit touched, returns an empty trail.

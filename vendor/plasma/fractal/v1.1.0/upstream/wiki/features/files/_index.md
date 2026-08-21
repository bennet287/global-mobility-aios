---
name: features/files
desc: |
  The files and transcript surface: how a node's work product is listed,
  diffed, and read, and how agent transcripts resolve.
created: 2026-07-21T04:35:35Z
updated: 2026-07-21T04:35:35Z
---

# features/files

[[features/_index|..]]

[[features/files/anchors_and_history|anchors_and_history]]: How the base,
commit, iteration, and run diff anchors resolve from the node's own record, and
the per-file history walk behind a changed listing.

[[features/files/contribution|contribution]]: Listing a node's work product: the
full tracked listing, and the changed listing that shows only the node's own
contribution with net line counts.

[[features/files/path_validation|path_validation]]: The two path-validation
tiers of the files surface: the structural tier every path passes, and the
stricter writable tier uploads must pass.

[[features/files/transcripts|transcripts]]: Per-agent transcript resolution: the
sessions facade, the provider-owned transcript layout, and the ownership-gated
fallback discovery.

***

The project-files surface exposes a node's work product to external consumers —
listing, reading, downloading, archiving, uploading, and narrowly committing
files, plus per-file history and per-agent transcripts. It is a facade over the
node's worktree and its record in the central database (the `Files` facade in
`fractal/core/files.py` as `node.files`, and the `Sessions` facade in
`fractal/core/session.py` as `node.sessions`), not a CLI of its own.

[[features/files/contribution|contribution]] covers the two listing modes —
every tracked file, or the node's own contribution under a `since` scope — and
the upload and archive paths.
[[features/files/anchors_and_history|anchors_and_history]] specifies how the
`base`/`commit`/`iteration`/`run` anchors resolve from the node's own record so
diffs survive merges and re-inits, and the per-file history trail.
[[features/files/path_validation|path_validation]] defines the structural and
writable validation tiers every caller-supplied path passes.
[[features/files/transcripts|transcripts]] covers the per-iteration session map
and provider-resolved live transcripts.

---
name: features/files/transcripts
desc: |
  Per-agent transcript resolution: the sessions facade, the provider-owned
  transcript layout, and the ownership-gated fallback discovery.
created: 2026-07-21T04:45:55Z
updated: 2026-07-21T04:51:52Z
---

# features/files/transcripts

[[features/files/_index|..]]

***

Agent transcripts resolve per provider, fronted by the node's sessions facade
(`Sessions` in `fractal/core/session.py`, reached as `node.sessions`). The
facade also keeps the per-iteration agent-to-session map: a small per-node file
recording, for each agent, the real resumable provider session started this
iteration — rewritten atomically on every update (a kill mid-write must not tear
the file resume and continuity depend on) and reset at the start of each
iteration. Session ids also land on the step and iteration rows in the central
database, which is where a transcript caller typically finds them.

## Resolution

A transcript request names an agent and a session id; the facade delegates to
that agent's backend (see the [[features/agents/_index|agents]] surface), which
owns the id validation, the provider's on-disk transcript layout, and fallback
discovery. Providers persist a session as a JSONL file that grows while the
session runs, so polling the same request returns the live transcript. The
result carries the agent, the session id, the resolved path, an existence flag,
and the raw JSONL content (empty while absent).

Edge semantics:

- The session id validates at the boundary: it lands in file paths and globs, so
  anything but a bare id (letters, digits, hyphen, underscore) is rejected — an
  unvalidated id could escape the transcript directory.
- The path may be the *expected* location even while the file does not yet exist
  (`exists` false, empty content) — a poller can wait for it to appear, or tail
  and range-read the file as it grows.
- When the provider's expected layout misses, fallback discovery may locate a
  relocated transcript — but only behind an ownership gate: the session must be
  recorded for *this node* in the central database. An ungated search would
  serve any session of the OS user, from any project. The gate is checked
  lazily, paid only on an expected-path miss.
- Content decodes leniently: the file grows while the session runs, so a poll
  racing a write can catch a torn multi-byte tail — a transient, self-healing
  condition that must not fail the fetch.

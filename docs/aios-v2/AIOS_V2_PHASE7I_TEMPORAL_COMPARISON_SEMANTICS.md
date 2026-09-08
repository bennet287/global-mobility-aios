# AIOS V2 Phase 7I — Temporal Comparison Semantics

## Scope

Phase 7I adds a presentation-only semantic layer to the already sealed replay cursor-to-cursor diff contract. It does not change reconstruction, canonical state, diff production, authority, or persistence.

## Truth scope

Every Phase 7I semantic label has `truthScope: "cursor_interval"`.

The layer may say only what the backend-proven diff supports between two explicit Activity cursors:

- exact `changed` with a proven status field before/after: `Status <before> → <after> between these cursors`
- exact `changed` without a status pair: `Changed between these cursors`
- exact `added`: `Appeared between these cursors`
- exact `removed`: `Not represented at the later cursor`
- unknown change kinds remain literal: `<kind> between these cursors`

## Fail-closed boundaries

`added` is deliberately not rendered as created, started, born, or newly caused. A bounded replay interval proves only that the entity appears in the later reconstructed state.

`removed` is deliberately not rendered as deleted, destroyed, completed, ended, or resolved. A bounded replay interval proves only that the entity is not represented in the later reconstructed state.

A status transition is not classified as improvement, deterioration, success, failure, urgency, causality, physical movement, presence, or authority change unless a separately governed canonical contract explicitly proves such a fact.

Unsupported dimensions, reconstruction posture, cursor coverage, unapplied transitions, and the backend raw `change_kind` remain available as provenance. No current/present-state truth is inferred from either cursor.

## Invariants

- read-only presentation
- no POST / PUT / PATCH / DELETE
- no mutation of replay or organization state
- no re-ordering or re-computation of backend deltas
- exact backend `change_kind` retained as `rawChangeKind`
- semantic rendering is derived only from the returned diff payload

## Acceptance

Phase 7I is acceptable only when repository policy, frontend foundation/types/build, SQLite, PostgreSQL, and browser proof remain green on the exact candidate SHA.

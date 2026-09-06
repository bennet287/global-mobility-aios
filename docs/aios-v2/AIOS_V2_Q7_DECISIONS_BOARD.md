# AIOS V2 Q7 — Decisions / Board Transparency

## Purpose

Q7 makes the Decisions Owner domain a real read-only workspace at `/cockpit/v2/decisions`.
It exposes the canonical Living Organization Decision projection without turning browsing or selection into authority.

## Read contract

Q7 reuses the existing Living Organization transparency scene GET through `getLatestAustriaLivingScene()`.
No backend endpoint, database model, write path or parallel Decision truth source is added.

The workspace consumes only supplied `LivingSceneDecision` fields:

- Decision identity/key/title/question/recommendation
- exact status
- recorded authority level and decision-owner position
- WorkItem relation
- recorded evidence-item count
- record fingerprint and source-object identity/version
- supersedes / superseded-by identity
- `is_current`
- `required_owner_action`
- decided / created / superseded timestamps
- `superseded_in_projection_week`

Evidence items remain opaque in Q7. Their count does not establish evidence quality, legal validity or approval.

## Portfolio grammar

The five-second scan uses literal values only:

- returned Decisions
- current records
- records where owner action is explicitly required
- records linked into supplied supersession lineage

The default ordering uses only supplied `required_owner_action`, `is_current`, and creation time. It is a presentation ordering, not a computed urgency or priority score.

## Selection semantics

Selecting a Decision opens an in-page inspector. Selection changes view context only.

Q7 intentionally contains no Approve, Reject, Execute, Complete, Escalate or mutation controls.
Recorded recommendation text is rendered with the shared `recommendation` truth badge so it cannot visually masquerade as a canonical decision outcome.

## Authority and supersession

Authority styling displays only the supplied `authority_level`. `required_owner_action` is displayed only when the canonical field is true.

Current/superseded posture is not inferred from timestamps. Q7 presents the explicit `is_current`, `supersedes_decision_id`, `superseded_by_decision_id`, and `superseded_in_projection_week` fields independently.

## Source and failure posture

The workspace distinguishes:

- loading
- access/source unavailable
- stale previously loaded data after refresh failure
- Living Organization projection not established
- established empty Decision collection
- established Decision collection

An unavailable or unestablished projection never becomes a zero-Decision claim.

## Search continuity

Already-loaded Decision records register with the Q2 in-memory search registry as `Decision:<decision_id>` identities. Search registration performs no independent network request or persistence.

## Responsive and accessibility posture

Desktop uses a composed portfolio + inspection surface. At narrow widths the inspector stacks below the portfolio rather than shrinking the desktop composition.

Rows are native buttons, focus is visible, selection is keyboard-operable, close restores selection origin, controls retain practical target sizes, and reduced motion is supported without hiding information.

## Truth boundaries

Q7 does not infer:

- approval or rejection
- legal validity
- completion
- urgency or priority
- execution authority
- evidence quality from evidence count
- currentness from timestamps
- authority from styling
- physical presence, location, conversation or collaboration

No POST/PUT/PATCH/DELETE path is introduced.

## Acceptance

Q7 is not sealed by implementation alone. Acceptance requires exact-head design-foundation, request-auth, production build/TypeScript, compiled-auth, focused Chromium at 1280/390 with reduced motion, human visual acceptance, and the four Woodpecker gates.

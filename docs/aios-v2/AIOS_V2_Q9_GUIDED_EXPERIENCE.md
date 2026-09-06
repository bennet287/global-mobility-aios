# AIOS V2 Q9 — Guided Experience

## Purpose

Q9 adds an explicit, presentation-only orientation layer across the seven accepted Owner workspaces. It is designed to answer three questions without changing canonical state:

1. Where should the Owner go next?
2. What should they look for in that workspace?
3. Which truth boundary must remain intact while reading it?

The guide is intentionally user-invoked from the Owner shell. It does not auto-open, persist completion, call a backend, or convert navigation into an operational action.

## Guided sequence

The sequence follows accepted Owner information architecture:

1. Home — five-second situation scan
2. Organization — structure, roster and Living Organization context
3. Missions — governed Mission portfolio and inspection
4. Intelligence — current governed signals versus aggregate memory
5. Evidence — recorded Evidence and grounding references
6. Decisions — recorded Executive Decision state and supersession
7. History — semantic Activity replay and explicit cursor comparison

Only enabled Owner workspaces participate. Q9 reuses the existing `ownerNavigation` registry rather than maintaining a second route registry.

## Interaction contract

- `Guide` appears beside Search / Command in the Owner shell.
- Opening the guide uses a modal dialog and focuses the close control.
- Escape closes the guide and restores focus to the Guide trigger.
- Tab focus remains bounded inside the modal.
- Previous / Next changes guide context only.
- `Open <workspace>` is an explicit Next.js navigation link.
- The active workspace is labelled `You are here`.
- Reopening the guide starts at the currently active workspace.
- No guide completion or progress is persisted.

## Truth boundaries

The guide repeats domain-specific reading constraints rather than summarizing them away:

- Organization roster is not presence, location, travel, conversation or collaboration.
- Mission selection and counts do not prove completion, health, success, urgency or execution authority.
- Aggregate memory is visualization-only and is not prediction or current authority.
- Evidence reference presence does not prove source content, legal validity, approval, freshness, correctness or quality.
- Decisions remain read-only; styling cannot create authority or approval.
- Historical reconstruction is not current state and cursor comparison does not prove causality, improvement or deterioration.

Q9 itself makes no canonical, authority, presence, completion, prediction or causal claim.

## Accessibility and responsive behavior

- Native modal dialog semantics.
- Explicit accessible labels and heading relationships.
- Escape dismissal and trigger focus restoration.
- Tab containment.
- 44px minimum interactive targets.
- Mobile layout reprioritizes the workspace list above step detail instead of shrinking the desktop two-column composition.
- Reduced-motion and forced-colors treatments are included.

## Acceptance

Q9 remains provisional until Q8 is sealed. Final acceptance requires reconstruction directly onto the accepted Q8 merge and exact-head proof for:

- design-foundation
- request-auth
- production build / TypeScript
- compiled-auth
- focused Chromium at 1280 and 390
- human visual acceptance
- Woodpecker repository-policy, backend-sqlite, frontend and postgres-governance 4/4

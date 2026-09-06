# AIOS V2 Q4 — Shared Premium UI Primitives

Status: IMPLEMENTED / CANDIDATE — not sealed or merged.

Accepted base: Q3 merge `e8ff1528e22e89115c1eb945829ecdd3f15599ec`.
Branch: `design/aios-v2-q4-premium-primitives`.

This candidate is a clean reconstruction of the preserved worker implementation
`29718bf842584b5c9921d34c6324f6eacf32b3bc` directly onto the accepted Q3 merge.
Temporary recovery notes from `agents/PROJECT_STATE.md`, `agents/SESSION_HANDOFF.md`,
`docs/ROADMAP.md`, and `docs/CHANGELOG.md` were deliberately not carried into the
reconstructed candidate because they described transient worktree/CI state rather
than the Q4 product contract.

## Purpose

Q4 establishes the reusable presentation grammar required before Missions,
Evidence, Decisions and History become full V2 workspaces. It removes repeated
special-case heading/state treatments from the current Mission Room and Employee
Inspector and provides bounded shared primitives without adding a backend read,
domain model, persistence layer, dependency, authority action or canonical write.

## Public component contract

The shared module is `apps/web/components/v2/ui/V2Primitives.tsx`, with scoped
styles in `V2Primitives.module.css`.

- `V2Surface` — base, raised, inset, floating and authority material hierarchy.
- `V2PageHeader` / `V2SectionHeader` — consistent semantic heading hierarchy,
  supporting copy and action slots.
- `V2StateBadge` — caller-supplied state label and visual tone; no state inference.
- `V2TruthBadge` — explicit canonical/recommendation/historical/memory/prediction/
  simulation/unsupported truth class.
- `V2AuthorityBadge` — displays recorded or required authority supplied by the
  caller; presentation never grants permission.
- `V2ObjectRow` — typed static, navigation or selection row. Selection uses a
  button and never becomes a submit action.
- `V2ProvenanceDisclosure` — native keyboard-accessible `<details>` disclosure,
  collapsed by default.
- `V2DataState` — explicit loading, empty, error, unavailable, partial and stale
  read states. Unavailable is not silently converted into empty.
- `V2Inspector` — named inline inspector with linked heading and named close
  control. Modal focus containment remains a later responsive/accessibility task.
- `V2TimelineRow` — supplied timestamp/coverage with explicit selection.
- `V2EvidenceChip` — supplied evidence label/state with optional internal link.

## Truth and authority boundaries

- Styling cannot create canonical truth, completion, approval or authority.
- State text is supplied by typed callers and is not semantically inferred by the
  primitive layer.
- Missing/invalid timestamps do not fall back to the current clock.
- Partial reads name unavailable sources and explicitly state that completeness is
  unknown.
- Stale reads retain the supplied last-load timestamp and warn that records may no
  longer reflect current state.
- Employee roster identity remains explicitly distinct from physical presence.
- Mission Room remains read-only and does not infer conversation, presence or
  handoff completion.
- The primitive layer adds no backend fetch, mutation, storage, approval/rejection
  action or workflow authority.

## Current integration

Q4 consumes the shared grammar in two already-accepted V2 surfaces:

1. Mission Room — shared section header, loading state and Mission state badge.
2. Employee Inspector — shared section header, authority badge, state badge and
   provenance disclosure while preserving presence/locomotion/mutation caveats.

Future Q5–Q8 workspaces may reuse these primitives, but Q4 does not enable those
routes or claim those workspaces are implemented.

## Worker-source validation

The preserved source candidate reported the following local validation under
Node 24.18.0 before reconstruction:

- 346 design-foundation tests passed.
- 7 request-auth tests passed.
- TypeScript, production build and compiled-auth passed.
- 2 focused Chromium fixture tests passed at 1280 and 390 px with reduced motion,
  including Mission selection, Employee Inspector, authority text, keyboard
  provenance disclosure, explicit non-mutation truth, close behavior, no
  horizontal overflow and zero API writes.

Those results are useful implementation evidence but are not exact-head acceptance
proof for the reconstructed commit. The reconstructed Q4 candidate still requires
normal local gates, browser review where appropriate, and exact-head Woodpecker
`repository-policy`, `backend-sqlite`, `frontend` and `postgres-governance` 4/4
before sealing or merge.

Q5–Q16 remain separate unfinished programme phases.

# AIOS V2 Q10 — Themes

## Status

Q10 adds presentation-only light/dark theming to the accepted Owner experience. During provisional implementation it is stacked on the current Q9 candidate and must be reconstructed onto the accepted Q9 merge before final acceptance.

## Contract

AIOS V2 exposes three presentation preferences:

- `System` — follow `prefers-color-scheme`
- `Light` — explicit premium daylight presentation
- `Dark` — explicit architectural-night presentation

The default is `System`. An explicit preference is stored locally under `aios-v2-theme`; no backend request, canonical write, account setting, or organization mutation is involved.

## Design intent

Dark remains the existing architectural black / warm-metal V2 identity. Light is not a generic white inversion: it uses warm gallery stone, paper-white raised surfaces, restrained bronze, and darker semantic hues so hierarchy and contrast remain deliberate.

Both themes preserve the same spacing, typography, information hierarchy, components, records, authority labels, truth badges, semantic states, and interaction model.

## Truth boundary

Theme is presentation only.

Changing theme must never:

- change canonical data or source coverage
- change authority or permission
- change a Mission, Evidence, Decision, History, Activity, employee, blocker, or attention state
- promote or demote severity
- turn unknown/unavailable state into certainty
- create presence, movement, collaboration, completion, approval, freshness, validity, health, urgency, or success claims

Semantic colors are retuned for contrast in light mode, but their semantic meaning is invariant.

## Architecture

- `tokens.css` remains the default dark V2 token baseline.
- `themes.css` supplies the explicit light palette and the system-light override while remaining scoped to `.aios-v2-root`.
- `V2Shell` owns only the local presentation preference and adds `data-theme` to the V2 root.
- `V2ThemeControl` provides a keyboard-native `System / Light / Dark` selector.
- legacy product styles and the document `<html data-theme>` contract are not modified.

## Accessibility and responsive behavior

- native select semantics and keyboard behavior are retained
- explicit focus-visible treatment
- `color-scheme` is declared for native controls
- forced-colors remains supported
- reduced-motion behavior is unchanged
- the control compacts at 760px and 560px without removing the actual choice

## Acceptance

Required final proof after Q9 is sealed and Q10 is reconstructed directly onto the accepted Q9 merge:

1. exact-head `test:design-foundation`
2. exact-head `test:request-auth`
3. exact-head TypeScript + production build
4. exact-head `test:compiled-auth`
5. focused Q10 Chromium at 1280px and 390px
6. human visual acceptance of both light and dark presentation
7. Woodpecker exact-head 4/4: repository-policy, backend-sqlite, frontend, postgres-governance

Q10 does not claim acceptance while stacked on an unsealed Q9 candidate.

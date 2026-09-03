# AIOS V2 Accessibility

## Target

WCAG 2.2 AA for structured product UI.

## Required

- skip navigation
- semantic landmarks
- logical headings
- full keyboard operation
- visible focus
- focus restoration
- Escape semantics
- accessible names
- status/error announcements where appropriate
- sufficient contrast
- zoom/scaling support
- no color-only meaning
- no hover-only essential interaction
- reduced motion
- screen-reader structured equivalents
- mobile/touch operability

## Spatial rule

Every essential spatial entity/state has a semantic structured equivalent.

3D failure cannot block:
- Mission inspection
- Employee inspection
- Evidence
- Decisions
- Replay
- blocker/attention understanding

## Motion

`prefers-reduced-motion` is a full design mode.

Replace large travel with:
- short fade/cut
- static relation
- controlled emphasis

## Character accessibility

Character identity must not depend on visual silhouette alone.

Provide:
- name
- role
- department
- state
- accessible description

## Testing

Automated + manual:
- keyboard-only
- screen-reader smoke
- 200% zoom
- reduced motion
- touch
- renderer-disabled fallback

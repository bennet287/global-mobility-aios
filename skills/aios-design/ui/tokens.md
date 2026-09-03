# AIOS V2 Token System

## Goal

Eliminate uncontrolled visual drift and stop adding arbitrary values to legacy global CSS.

## Required token families

### Color
- `color.foundation.*`
- `color.semantic.*`
- `color.truth.*`
- `color.department.*`

### Type
- `type.family.*`
- `type.size.*`
- `type.weight.*`
- `type.tracking.*`
- `type.lineHeight.*`

### Space
- `space.*`

### Geometry
- `radius.*`
- `border.*`

### Depth
- `shadow.*`
- `elevation.*`
- `blur.*`
- `opacity.*`

### Motion
- `motion.duration.*`
- `motion.easing.*`

### Layout
- `layout.content.*`
- `layout.rail.*`
- `layout.inspector.*`
- `layout.breakpoint.*`

### Spatial
- `spatial.hud.*`
- `spatial.selection.*`
- `spatial.depth.*`

## Status

Exact values are not hard contracts until the V2 prototype is visually and performance validated.

## Migration rule

Legacy CSS can coexist during migration.

New V2 components should use V2 semantic tokens rather than introducing arbitrary root hex colors, breakpoints, radius values, and shadows.

## Breakpoints

Use a small mode system:
- mobile
- tablet
- laptop
- desktop
- wide

Exact boundaries are **PROPOSED** until prototype review.

## Spacing

Candidate scale:
`4, 8, 12, 16, 24, 32, 48, 64, 96`

Candidate only; validate before locking.

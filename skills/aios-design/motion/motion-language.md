# AIOS V2 Motion Language

## Purpose

Motion communicates:
- cause
- continuity
- hierarchy
- relationship
- state change
- completion
- transfer
- attention
- spatial orientation

Motion is not decoration.

## Motion domains

### Micro
Hover, press, focus, selection acknowledgement.

### Interface
Inspector, drawer, navigation, disclosure.

### Spatial
Camera focus, room focus, object focus.

### Ambient character
Presentation-only life.

### Semantic character
Canonical state/event expression.

### Temporal
Replay and compare transitions.

## Proposed timing directions

These remain **PROPOSED until prototype measurement**:

- micro: 100–160ms
- standard UI: 180–260ms
- panel: 240–360ms
- navigation: 280–420ms
- spatial focus: 400–700ms
- semantic character clip: natural duration

## Ambient motion

Allowed presentation-only examples:
- breathing
- blink
- glance
- stretch
- coffee
- local desk gesture
- tablet interaction
- local walk

Ambient motion cannot imply:
- real work execution
- canonical conversation
- authority event
- handoff
- blocker resolution
- productivity

## Semantic motion

Requires contract support.

Examples:
- WorkItem assignment → handoff/transfer
- governed conversation → participants orient/gather
- Mission collaboration → participants associated with Mission Room
- blocker → attention behavior
- Owner escalation → Board/authority emphasis
- completion → work object settles/closes

## Common fate

Use shared motion as a relationship language.

Examples:
- multiple employees moving toward one Mission Room
- handoff object moving between employees
- evidence objects converging into decision context

Only when the relationship is supported.

## Reduced motion

Reduced-motion mode must:
- remove unnecessary travel
- replace large camera glides with short fades/cuts
- reduce ambient loops
- remove parallax
- preserve semantic state through static cues

No essential meaning depends on motion.

## Camera safety

Avoid:
- sudden zoom
- excessive rotation
- uncontrolled orbit
- constant drift
- motion that interferes with reading

## Motion tokens

All V2 motion uses centralized duration/easing tokens.

No component-local arbitrary animation curves without documented reason.

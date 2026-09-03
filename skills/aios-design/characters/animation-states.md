# Character Animation States

## Presentation state families

### Neutral / idle
- settled
- attentive idle
- local ambient gesture

### Working presentation
- focused desk/surface interaction

### Waiting
- calm waiting posture
- awaiting Owner variation

### Blocked
- attention posture
- blocker/object focus

### Reviewing
- evidence/source comparison

### Collaborating
- Mission/conversation-oriented stance

### Handoff
- transfer sequence

### Completed
- calm settle/closure

## Rules

Animation state is derived from presentation mapping, not directly from arbitrary renderer logic.

## Transitions

Avoid abrupt state snapping where a short safe transition can preserve continuity.

Transition selection must be deterministic and flow through the governed presentation adapter rather than component-local guesses.

Character motion personality may change the **style and timing** of a transition, but not its semantic meaning. For example, a CEO may settle more deliberately while Operations may move more briskly; both must still represent the same supported canonical transition.

## Local locomotion boundary

Presentation-only local walking is allowed only as bounded ambient motion inside an already-rendered local zone.

Ambient walking must not imply:
- a canonical room change
- a Mission assignment
- a handoff
- physical presence
- travel duration
- collaboration

Long or cross-zone travel that communicates organizational meaning requires supported canonical input and the semantic animation contract.

## Rig and animation-set compatibility

Animation states must resolve through the selected presentation's compatible rig class and versioned animation set.

Renderer components must not assume that every character has every clip.

If a semantic clip is unavailable:
1. preserve the canonical state in structured UI
2. use the defined reduced-motion/static equivalent
3. never fabricate a replacement animation with stronger meaning

## Reduced motion

Use posture/state change without long animation.

Every state family requires an equivalent that preserves meaning without motion. The default character contract is:

```text
mode = posture-and-state-change-only
forbidsLongTravelAnimation = true
```

## Truth

A presentation animation may be expressive but cannot imply unsupported activity.

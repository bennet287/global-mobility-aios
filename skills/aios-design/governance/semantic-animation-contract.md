# Semantic Animation Contract

## Purpose

This contract defines when motion may communicate organizational truth.

> **The organization causes the animation. Animation never causes the organization.**

## Required mapping schema

Every semantic animation defines:

1. canonical input
2. required fields/coverage
3. allowed visual interpretation
4. forbidden implications
5. lifecycle/end state
6. reduced-motion equivalent
7. Replay behavior
8. automated tests

## Example: handoff

Canonical input:
`LivingSceneHandoff`

Required:
- work_item_id
- previous_position_key
- assigned_position_key
- occurred_at
- canonical_basis

Allowed:
- highlight sender and receiver
- animate a bounded transfer object/path
- show assignment direction
- show occurrence time in inspector

Forbidden:
- implying physical transfer duration is canonical
- inventing conversation
- inventing work completion
- inventing dependency resolution
- inventing real-world physical presence

Reduced motion:
- static sender → receiver relation
- brief emphasis change
- no long travel animation

Replay:
- may occur at supported replay cursor/event
- must respect replay coverage

## Example: conversation

Canonical input:
`LivingSceneConversation`

Allowed:
- orient participants
- show active collaboration marker
- open conversation inspector

Forbidden:
- inventing transcript content
- inventing spoken words
- inventing authority effect beyond contract

## Example: blocker

Canonical input:
canonical blocker linked to work/employee/Mission.

Allowed:
- attention posture
- blocker object
- controlled warning cue

Forbidden:
- distress theatrics
- implying severity not present
- implying resolution before canonical resolution

## Example: Board/Owner escalation

Canonical input:
supported HumanActionRequest / decision authority state.

Allowed:
- Board/authority region prominence
- Owner attention object
- relevant employee/decision focus

Forbidden:
- showing approval/rejection before human action

## Negative rule

If required canonical input or coverage is missing:
- semantic animation is forbidden
- use neutral/unsupported presentation

## Presentation-only ambient behavior

Ambient behavior must be explicitly separate and never produce semantic data attributes that imply canonical work state.

## Testing

For each mapping:
- positive supported fixture
- negative unsupported fixture
- authority invariant
- no-mutation assertion
- reduced-motion assertion
- replay assertion if historical

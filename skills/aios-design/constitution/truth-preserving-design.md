# Truth-Preserving Design

## Prime rule

> **Visual clarity must never reduce truth clarity.**

Presentation may simplify structure, but may not convert:
- unknown → known
- unsupported → supported
- recommendation → decision
- memory → live state
- prediction → canonical fact
- projection → authority
- ambient animation → actual work
- historical partial coverage → complete history

## Truth classes

Every relevant V2 surface must be able to distinguish:

- canonical current state
- human-authoritative state
- AI recommendation
- historical reconstruction
- memory / aggregate
- prediction
- simulation
- unavailable
- unsupported
- stale

## Information-depth rule

Primary UI shows operational meaning first.

Technical provenance remains available at deeper levels.

Example:

Preferred:
`Regulatory review complete · 1 issue requires Owner authority`

Then:
`Inspect evidence`

Then:
`Inspect provenance`

Then:
contract/fingerprint/provider details.

Avoid leading normal Owner UX with raw contract booleans or identifiers unless the technical context is the task itself.

## Authority rule

A renderer, animation, character, room, chart, or badge never gains authority from visual prominence.

Living Organization remains a read/presentation layer unless a separately governed structured control is explicitly invoked.

## Memory rule

Environmental Memory must always remain visibly:
- historical/aggregate
- non-authoritative
- non-predictive
- visualization-only

## Replay rule

Replay can visualize only supported reconstructed dimensions.

Unsupported historical dimensions stay unsupported.

## Presence rule

A character appearing in the world is not automatically a claim of literal live presence.

Presence claims must follow the canonical presence contract.

## Error rule

When canonical data and scene/read models disagree:
- stop mixed-state rendering
- show a visible reconciliation/partial-state message
- do not locally synthesize missing truth

## Testing

Truth-sensitive presentation must include positive and negative tests:
- supported input renders
- unsupported input does not render as supported
- no mutation path exists from presentation-only controls

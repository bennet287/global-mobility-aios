# AIOS V2 Component Grammar

## Principle

Implementation primitives may be generic. User-facing product language should be domain-native.

## Foundation primitives

Examples:
- Surface
- Stack
- Cluster
- Grid
- Text
- Control
- Icon
- Disclosure
- Drawer
- Dialog
- Table
- Notice
- Skeleton

These primitives should not dominate product vocabulary.

## Domain objects

### Mission Surface
Purpose, state, participants, blockers, evidence, decisions, next action.

### Work Object
WorkItem identity, lifecycle, owner/employee, blocker/attention, Mission.

### Employee Identity
Persistent role/personality/department/state representation.

### Evidence Object
Source, verification, freshness, jurisdiction, evidence authority.

### Source Object
Official/external source identity, snapshot/fingerprint, freshness.

### Decision Object
Authority, outcome/recommendation, work/evidence, history.

### Authority Gate
Human/Board decision boundary and explicit governed action.

### Handoff Signal
Canonical assignment/transfer relation.

### Friction Signal
Blocker/dependency/attention relation.

### Temporal Lens
Replay cursor, coverage, as-of state, compare state.

### Environmental Pattern Surface
Historical aggregate/memory visualization.

### Provenance Drawer
L3/L4 evidence/provenance inspection.

### Owner Attention Object
One coherent attention vocabulary for owner-required items.

## Required states

Applicable components define:
- default
- hover
- focus
- active
- selected
- disabled
- loading
- empty
- partial
- unavailable
- error
- historical
- memory
- predictive
- authority-required

Do not map all states to generic colored badges.

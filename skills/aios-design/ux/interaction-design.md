# AIOS V2 Interaction Design

## Core interaction verbs

AIOS uses a small stable interaction vocabulary:

- select
- inspect
- open
- filter
- compare
- focus
- review
- approve
- reject
- publish
- activate
- transition
- command
- navigate back

## Selection vs action

Selection changes context.

Action changes domain state.

These must never look identical.

## Inspectors

Use contextual inspectors for:
- employee
- Mission
- Evidence
- Decision
- WorkItem
- Source
- Department

Inspectors should not become giant modal replacements for whole workspaces.

## Confirmation

Use stronger confirmation for:
- authority
- publish
- activate
- external effect
- destructive/retire
- organization control

Routine reversible navigation should not ask for confirmation.

## Error recovery

Where domain allows:
- preserve user input
- explain failed action
- offer retry
- distinguish validation from transport failure
- do not lose context

## Keyboard

All primary interactions must be keyboard-operable.

## Feedback

Every action receives immediate perceptible feedback without fabricating completion.

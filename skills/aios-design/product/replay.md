# Replay V2

## Source

Replay uses existing canonical Activity replay, as-of reconstruction, and temporal diff.

## Main interaction

Timeline cursor:
- selects historical cursor
- reconstructs supported state
- updates structured + spatial representation

## Compare

A/B comparison shows:
- appeared
- disappeared
- changed
- unchanged omitted where contract says so

## Coverage

Always expose:
- coverage start/state
- unsupported dimensions
- partial reconstruction

## No mutation

Historical mode is read-only.

## Spatial

Use temporal continuity without fabricating unsupported historical details.

# Visual Regression

## Canonical screenshot states

Capture:

- Owner Home light/dark
- needs-attention state
- Board pending authority
- Evidence verified/stale/unsupported
- Mission active/blocked
- employee working/waiting/blocked
- Living Organization default
- employee selected
- Mission selected
- reduced-motion
- renderer fallback
- Replay state
- Compare state
- Environmental Memory overlay

## Rules

Visual baselines are reviewed intentionally.

Do not blindly accept snapshot changes.

## Stable data

Use deterministic fixtures for visual regression.

Do not let timestamps/random animation create noisy diffs.

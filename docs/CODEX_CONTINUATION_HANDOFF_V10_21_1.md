# Codex Continuation Handoff — v10.21.1

## Release state

- Database head: `0032_initial_rule_assertions` (no migration)
- Scope: frontend-only tranche draft handoff UX hotfix
- Existing v10.21 assistant safety model: unchanged

## Fixed

The **Copy draft into assertion form** action previously updated React state but gave no visible confirmation and left the operator at the tranche result card. This made the action appear unresponsive even when the lower assertion form had been populated.

The hotfix now:

- shows a copied-state label on the action,
- scrolls to the existing initial-rule assertion form,
- focuses the title field,
- displays an explicit in-form confirmation notice,
- uses `type="button"`, and
- creates or submits no record.

## Safety boundary

Copying a draft remains client-side form population only. Human editing, explicit submission, independent review, and separate publication remain mandatory.

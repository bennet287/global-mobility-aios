# Demo UX Polish v5.7

## Goal

Make the controlled-agent demo flow easier to present after the v5.6 duplicate output guard.

## Changes

- Shows `Review Pending Draft Output` when a lead already has a pending `client_drafting_agent` output.
- Keeps the duplicate guard visible without creating extra pending outputs.
- Adds direct links from the duplicate guard notice to:
  - the existing agent output review detail page
  - the filtered agent review queue for that lead
- Preserves all safety behavior:
  - no automatic sending
  - no automatic conversion
  - no automatic approval
  - no duplicate pending client draft outputs

## Verification

Run:

```powershell
python scripts/check_local_quality.py
```

Expected result:

```text
Local quality gate passed.
```


# Agent Duplicate Output Guard v5.6

## Goal

Prevent accidental duplicate pending client-drafting agent outputs for the same lead during a demo or operator session.

## Behavior

- A `client_drafting_agent` run is still review-gated and internal-only.
- If the same lead already has a pending client-drafting output, the API returns `409`.
- The admin operator console redirects back to the existing pending run and shows a duplicate guard notice.
- Once the existing output is approved, rejected, or converted, a fresh client-drafting output can be generated.

## Safety Rule

This guard does not approve, convert, review, send, or delete anything automatically. It only prevents extra pending review items from being created by repeated clicks.

## Verification

Run:

```powershell
python scripts/check_local_quality.py
```

Expected result:

```text
Local quality gate passed.
```


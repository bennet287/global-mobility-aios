# Truth Resolution Engine v1.2

## Fix

Truth Resolution v1.2 fixes enum-safe truth resolution.

The local data model uses enum-backed truth verdict values:

```text
verified
rejected
needs_review
```

v1/v1.1 accepted workflow/user-facing values such as:

```text
APPROVED
resolved
superseded
```

Those are not valid persisted `TruthClaim.verdict` values, so SQLite/SQLAlchemy rejected them.

## Changes

- Maps `APPROVED`, `resolved`, and `superseded` to persisted verdict `verified`.
- Stores workflow meaning such as `resolved` or `superseded` in explanation / recommended next step text.
- Clears `requires_human_review` after source-backed resolution.
- Clears `red_flags_json` where the model supports it.
- Keeps resolution metadata in supported text fields instead of enum fields.
- Adds clearer error details for review-closing failures.

## Design rule

Truth resolution states are workflow concepts. They must not be written directly into enum-backed verdict columns.

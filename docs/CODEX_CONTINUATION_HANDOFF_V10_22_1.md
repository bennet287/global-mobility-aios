# Codex Continuation Handoff — v10.22.1

## Purpose

v10.22.1 is a scripts-only path-resolution hotfix for the safe multi-jurisdiction tranche operations release.

## Corrected behavior

- Relative manifest paths resolve from the active PowerShell location.
- Relative JSON, CSV, and receipt output paths resolve from the active PowerShell location.
- Absolute paths remain supported.
- The v10.22 review, assertion, publication, immutable-snapshot, and coverage-claim safety boundaries are unchanged.

## Root cause

`System.IO.Path.GetFullPath()` used the host process working directory, which can remain at a parent folder after PowerShell `Set-Location`. The scripts now use PowerShell provider-aware path resolution through `GetUnresolvedProviderPathFromPSPath`.

## Runtime impact

No Docker rebuild, API restart, database migration, or data remediation is required.

## Expected migration head

`0032_initial_rule_assertions (head)`

# Coverage Readiness Receipts v10.20

## Purpose

A verified rule publication changes more than the rule catalogue: it can complete
one jurisdiction's final reviewed evidence gate. This increment makes that
transition explicit, auditable, queryable, and visible in the Coverage workspace
without treating a baseline assertion as a detected regulatory change.

## Publication receipt

Publishing an independently approved initial rule assertion now returns a
coverage receipt containing:

- the exact registry release and jurisdiction;
- evidence-gate state before publication;
- evidence-gate state after publication;
- remaining gaps, if any;
- whether the publication caused the jurisdiction to become coverage-ready;
- registry-wide ready and verified-rule counts; and
- the unchanged global-coverage release-gate state.

The publication endpoint remains idempotent. Repeating a completed publication
returns the existing verified rule and a read-only current receipt. It does not
create another rule, graph projection, or readiness-transition audit event.

## Audit and dashboard reconciliation

Every new assertion-backed rule publication records
`jurisdiction_coverage_readiness_reconciled` with the before and after gate
posture. The existing registry and live dashboard continue to derive counts from
active reviewed records rather than from cached counters.

The Coverage workspace shows a published assertion with either:

- **Jurisdiction coverage ready**, when all reviewed gates pass; or
- **Verified rule published**, followed by the remaining gate names.

The dashboard's verified-rule and coverage-ready totals refresh from the same
registry calculation. Detected-change counts and the Opportunity Radar remain
unchanged because an initial baseline assertion is not a source-change event.

## Read-only API and operator helper

Read one jurisdiction's current receipt:

```text
GET /api/v1/global-intelligence/registry/jurisdictions/{jurisdiction_id}/coverage-receipt
```

PowerShell helper:

```powershell
.\scripts\Get-JurisdictionCoverageReceipt.ps1 -Alpha2Code AT
```

The helper resolves the current registry entry and prints the gate status,
missing evidence, registry-wide ready count, verified-rule count, and global
claim posture. It performs no mutation.

## Evidence-package safety

The Coverage workspace no longer preloads example `official.example` evidence.
The default JSON is an empty array, and the submission action remains disabled
until at least one evidence row is present. This reduces accidental submission
of placeholder authority or source data.

## Safety boundaries

- No readiness state is manually stored or asserted by the caller.
- The receipt is recalculated from approved relationships, reviewed primary
  authority/source certification, monitor freshness, and active verified rules.
- No global coverage claim is enabled unless every required registry entry
  passes every release gate.
- No regulatory change is created by initial-rule publication.
- No duplicate verified rule or duplicate readiness audit is created on retry.
- Database migration head remains `0032_initial_rule_assertions`.

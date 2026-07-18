# Coverage Tranche Operations v10.22

## Purpose

Version 10.22 scales reviewed jurisdiction evidence work without changing the legal-control boundary. It adds a planning and operations layer around the existing coverage worklist, evidence batches, tranche assistant, baseline queue, assertion review, publication, and readiness receipt APIs.

The release does **not** add automatic source certification, legal interpretation, assertion submission, review approval, rule publication, snapshot mutation, regulatory-change creation, or global-coverage claims.

## Tools

### `New-CoverageExpansionPlan.ps1`

Creates a read-only planning file from the existing prioritized coverage worklist. The generated jurisdictions contain blank evidence fields that must be completed through human research.

```powershell
.\scripts\New-CoverageExpansionPlan.ps1 `
  -Count 10 `
  -Region "Europe" `
  -OutputPath ".\coverage-expansion-europe.json" `
  -CsvOutputPath ".\coverage-expansion-europe.csv"
```

The planner never infers an immigration-rule relationship or authority.

### `Test-CoverageTrancheManifest.ps1`

Validates an operations manifest offline before any API request. It checks:

- schema version;
- manifest and group names;
- evidence-batch UUIDs;
- two-letter jurisdiction codes;
- per-group limits;
- empty or malformed groups.

```powershell
.\scripts\Test-CoverageTrancheManifest.ps1 `
  -ManifestPath ".\coverage-operations.json"
```

### `Invoke-CoverageTrancheOperations.ps1`

Prepares multiple existing evidence batches and jurisdiction groups in one controlled run. It always performs a dry-run preflight first.

```powershell
.\scripts\Invoke-CoverageTrancheOperations.ps1 `
  -ManifestPath ".\coverage-operations.json" `
  -OutputDirectory ".\coverage-operations-receipts"
```

The output directory contains:

- `tranche-operations-summary.json`;
- `tranche-operations-summary.csv`;
- `tranche-review-queue.csv`;
- `tranche-baseline-queue.csv`;
- `tranche-assertion-drafts.json`.

The receipts show the exact existing stage and next action for every selected jurisdiction. Candidate assertions remain draft suggestions only.

## Explicit baseline apply mode

Baseline queueing remains optional and confirmation-gated:

```powershell
.\scripts\Invoke-CoverageTrancheOperations.ps1 `
  -ManifestPath ".\coverage-operations.json" `
  -ApplyBaselineQueues `
  -OutputDirectory ".\coverage-operations-receipts"
```

Only jurisdictions that are:

1. explicitly listed in the manifest;
2. part of the identified evidence batch;
3. independently approved by the existing assessment and certification gates; and
4. reported by the API as eligible to queue

can be sent to the existing baseline-capture path.

`-WhatIf` performs the preflight but prevents queueing and receipt writes.

## Operations manifest

```json
{
  "schema_version": "1.0",
  "name": "Regional tranche operations",
  "groups": [
    {
      "label": "Primary evidence batch",
      "batch_id": "00000000-0000-0000-0000-000000000001",
      "alpha2_codes": ["FR", "IT", "ES"]
    },
    {
      "label": "Supplemental source batch",
      "batch_id": "00000000-0000-0000-0000-000000000002",
      "alpha2_codes": ["FR"]
    }
  ]
}
```

The same jurisdiction may appear in a primary batch and a separately reviewed supplemental-source batch. Duplicate codes inside one group are normalized.

## Safety invariants

- Existing batches and evidence records are read, not rewritten.
- Dry-run preparation is mandatory before optional baseline queueing.
- The tools do not call assessment-review, certification-review, assertion-review, or publication endpoints.
- The tools do not persist initial assertions.
- Immutable source snapshots are never modified.
- A failed or weak source remains visible as a blocker.
- Supplemental-source governance from v10.21.2 remains separate from primary-source certification.
- Global coverage remains blocked until every required jurisdiction passes all existing gates.

## Rollback

The release adds scripts, tests, examples, and documentation only. Removing the added files restores the prior runtime behavior. No migration or data rollback is required.

# Coverage Tranche Assistant v10.21

## Purpose

The tranche assistant removes repetitive preparation work from Phase 10B without
replacing the existing evidence, review, publication, or readiness controls. It
is an assistive layer over the working manual workflow, not an autonomous legal
verification system.

## Feature flag

The assistant is disabled by default:

```env
COVERAGE_TRANCHE_ASSISTANT_ENABLED=false
COVERAGE_TRANCHE_ASSISTANT_MAX_ITEMS=25
```

Enable it only in an environment where operators understand that all output is
review material:

```env
COVERAGE_TRANCHE_ASSISTANT_ENABLED=true
```

Rebuild the API container after changing the flag.

## Safe capabilities

For explicitly selected jurisdiction codes in an existing evidence batch, the
assistant can:

- assemble assessment, certification, authority, source, and monitor review packets;
- report the current operational stage and next safe action;
- inspect an immutable baseline snapshot without changing it;
- score content quality and reject navigation-only or low-information pages;
- extract exact candidate evidence lines using deterministic rules;
- prepare a constrained assertion suggestion for human editing;
- dry-run selective baseline queueing;
- queue only explicitly selected, independently approved baseline captures when
  an operator uses apply mode.

## Actions it never performs

The assistant does not:

- create or approve immigration-rule assessments;
- create or approve source certifications;
- decide whether an authority is legally primary;
- create an initial rule assertion;
- review or publish a verified rule;
- modify an immutable source snapshot;
- create a detected regulatory-change event;
- change pathway eligibility or mobility plans;
- declare a jurisdiction or global registry coverage-ready.

Candidate assertion text is deliberately limited to descriptions of exact
headings or service statements found in the snapshot. It must be edited and
independently reviewed before use.

## API

Read feature posture:

```http
GET /api/v1/global-intelligence/registry/coverage-tranche-assistant/config
```

Prepare selected jurisdictions:

```http
POST /api/v1/global-intelligence/registry/coverage-batches/{batch_id}/assistant/prepare
```

Example dry-run request:

```json
{
  "alpha2_codes": ["DE"],
  "dry_run": true,
  "queue_eligible_baselines": false,
  "include_candidate_assertions": true,
  "max_candidate_lines": 8
}
```

Apply mode can queue eligible baselines only when both of these are explicit:

```json
{
  "dry_run": false,
  "queue_eligible_baselines": true
}
```

Selection is enforced server-side, so eligible sources outside the supplied
alpha-2 list are not queued.

## PowerShell workflow

Dry-run one jurisdiction:

```powershell
.\scripts\Prepare-CoverageTranche.ps1 `
  -BatchId "<batch-id>" `
  -Alpha2Code "DE" `
  -WhatIf
```

Prepare a review receipt without mutation:

```powershell
.\scripts\Prepare-CoverageTranche.ps1 `
  -BatchId "<batch-id>" `
  -Alpha2Code "DE","CA" `
  -OutputPath ".\coverage-tranche-review.json"
```

Explicitly queue only selected approved baselines:

```powershell
.\scripts\Prepare-CoverageTranche.ps1 `
  -BatchId "<batch-id>" `
  -Alpha2Code "CA" `
  -ApplyBaselineQueues `
  -Actor "coverage-tranche-operator"
```

## Operator console

The Coverage workspace exposes the same assistant with:

- batch and jurisdiction selection;
- dry-run preparation;
- an explicit selective-baseline apply action;
- current stage and next-action summaries;
- snapshot quality and navigation-ratio indicators;
- a **Copy draft into assertion form** action that fills the existing form but
  does not submit it.

The established proposer, reviewer, and publisher separation remains unchanged.

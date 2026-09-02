# Official Global Coverage Evidence Starter v10.17

## Outcome

The first evidence-backed Phase 10B tranche is packaged for Austria, Germany,
Canada, Australia, and New Zealand. The pack uses current official authority and
immigration portal evidence verified on 2026-07-14.

Submitting the pack does **not** approve any jurisdiction. It atomically creates:

- one active regulatory authority;
- one active HTTPS official source;
- one allowlisted source monitor;
- one pending primary-source certification proposal;
- one pending immigration-rule relationship proposal.

A different authenticated reviewer must approve or reject every proposal. Global
coverage claims remain blocked.

## Evidence scope

| Code | Proposed authority | Primary official source | Relationship proposal |
| --- | --- | --- | --- |
| AT | Federal Ministry of the Interior | `https://www.migration.gv.at/en/` | `independent` |
| DE | Federal Foreign Office | `https://www.auswaertiges-amt.de/en/visa-service` | `independent` |
| CA | Immigration, Refugees and Citizenship Canada | `https://www.canada.ca/en/immigration-refugees-citizenship.html` | `independent` |
| AU | Department of Home Affairs | `https://immi.homeaffairs.gov.au/` | `independent` |
| NZ | Immigration New Zealand | `https://www.immigration.govt.nz/home/` | `independent` |

The relationship values are proposals based on direct national administration of
relevant immigration functions. They remain `pending_review` until decided by a
separate reviewer.

## Provenance improvement

When one batch row contains both source onboarding and an immigration assessment,
the service now onboards the source first and automatically links the pending
assessment to that exact official-source record. A caller-supplied source ID that
does not match the newly onboarded source fails the complete batch.

This keeps the canonical batch hash stable while improving stored assessment
provenance.

## Files

- Evidence pack:
  `knowledge/global_coverage/tranches/v10_17_official_evidence_starter.json`
- Offline validator:
  `scripts/validate_global_coverage_evidence_pack.py`
- PowerShell API submitter:
  `scripts/Submit-GlobalCoverageEvidencePack.ps1`

## Validation

From the repository root:

```bash
python scripts/validate_global_coverage_evidence_pack.py
```

The validator checks:

- valid pack version and evidence date;
- five unique ISO alpha-2 codes;
- HTTPS evidence, authority, and source URLs;
- source-host coverage by the monitor allowlist;
- exact reference-to-onboarding URL agreement;
- `pending_independent_review` state;
- explicit no-coverage-claim and no-auto-approval safety flags.

## Submission

With the local API running, PowerShell can preview the submission:

```powershell
.\scripts\Submit-GlobalCoverageEvidencePack.ps1 -WhatIf
```

Submit as the proposer:

```powershell
.\scripts\Submit-GlobalCoverageEvidencePack.ps1 `
  -Actor "coverage-evidence-proposer"
```

The API returns one idempotent evidence batch with ten pending review records.
A different account must use the Coverage workspace to review them.

## Safety boundary

- Official URLs are not treated as approved simply because they are included in
  this pack.
- The pack does not create source snapshots or verified rules.
- A monitor must successfully retrieve fresh evidence.
- A human-reviewed change must still be published as a verified rule.
- The five-jurisdiction tranche does not support a global coverage claim.

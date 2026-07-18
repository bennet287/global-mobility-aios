# Phase 10B Independent Review Handoff

This packet covers the 15 pending jurisdictions in evidence batches v10.22.20 through
v10.22.22. It creates no review decision, baseline capture, assertion, publication, or
coverage claim.

## Required human action

Open `http://localhost:3000/global-intelligence`, select each jurisdiction below, inspect
the linked official evidence, and independently approve or reject both the immigration
assessment and primary-source certification with substantive review notes.

The reviewer identity must differ from the proposal identities
`coverage-evidence-proposer-v10-22-20`, `coverage-evidence-proposer-v10-22-21`, and
`coverage-evidence-proposer-v10-22-22`.

| Batch | Jurisdictions | Decisions |
| --- | --- | ---: |
| `1c20b390-85d9-4ce0-9e08-f6775b5f66ff` | KR, MY, CL, PE, QA | 10 |
| `c697ab51-e41b-49d2-8e98-528068642184` | SZ, LS, LR, ZM, UG | 10 |
| `db3d7b69-cff4-467c-89c1-0bd837daa9ec` | NA, SL, SO, SN, TZ | 10 |

The detailed queue is in `tranche-review-queue.csv`; the complete immutable preparation
receipt is in `tranche-operations-summary.json`.

## Downstream content-quality findings

Thirteen current snapshots are suitable for narrow assertion drafting after approval.
The current Peru and Qatar snapshots are not.

- Peru (`PE`) current score: 35, `insufficient_substantive_text`. A controlled probe of
  `https://www.gob.pe/12877-solicitar-visa-de-residente-para-trabajador` returned HTTPS
  200 and scored 67, `suitable_for_narrow_draft`.
- Qatar (`QA`) current score: 11, `insufficient_substantive_text`. A controlled probe of
  `https://portal.moi.gov.qa/wps/portal/MOIInternet/services/inquiries/residencypermits/1000`
  returned HTTPS 200 and scored 85, `suitable_for_narrow_draft`.

These narrower pages are remediation candidates only. They have not been certified,
onboarded as supplemental sources, captured as immutable baselines, or used to create an
assertion.

## After the decisions

Run the same manifest through `Invoke-CoverageTrancheOperations.ps1` again. Only approved
items will become eligible for controlled baseline capture. Rejected items must be corrected
and resubmitted; no downstream gate should be weakened.

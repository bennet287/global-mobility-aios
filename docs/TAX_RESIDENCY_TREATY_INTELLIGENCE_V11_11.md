# Tax-Residency and Treaty Intelligence v11.11

## Outcome

Phase 11.11 adds a governed coordination layer for cross-border tax-residency work. It does not decide tax residence, apply a treaty to a client, calculate tax, select a filing position, or replace licensed advice.

The implementation separates two records that must never be conflated:

1. A treaty evidence record states a narrow fact from a dated official-source snapshot.
2. A client assessment organises disclosed facts, controlled documents, evidence gaps, relevant issues, specialist workstreams, and next actions.

## Treaty evidence control

A proposal requires:

- two distinct jurisdictions;
- a defined treaty topic;
- a narrow statement with no client conclusion or guarantee;
- an active official source in the tax domain whose country matches the pair;
- the exact content-addressed snapshot belonging to that source; and
- optional effective-from and effective-to dates.

The proposer cannot publish their own record. Approval by a different authenticated reviewer changes the evidence state from `pending_review` to `published`; rejection makes it unavailable. Every proposal and decision is audited.

A client assessment only accepts published treaty evidence. The selected pair must match the assessment jurisdictions and the evidence must be effective during the selected tax year.

## Client issue map

The immutable assessment links to an existing client and can optionally reference their Family Office or Business & Wealth advisory record. Linked controlled documents must belong to the same client.

Inputs cover:

- current and target claimed or filed residencies;
- citizenships and family locations;
- jurisdiction presence days;
- continuously available homes;
- employment, director/control, and business-structure jurisdictions;
- income categories;
- departure and arrival dates;
- objectives and material constraints;
- coordinating, home, and destination adviser coverage;
- controlled document IDs; and
- independently published treaty evidence IDs.

The output exposes separate scores for fact completeness, controlled evidence, treaty grounding, and specialist coordination. The overall readiness score measures readiness to obtain and coordinate specialist analysis. It is not a residence conclusion, treaty entitlement, approval probability, tax estimate, filing recommendation, or outcome guarantee.

## Issue and workstream model

The issue matrix identifies questions requiring professional conclusions, including:

- domestic residence in each relevant jurisdiction;
- potential dual residence and treaty coordination;
- entity residence, management/control, and permanent-establishment exposure;
- employment, payroll, and social-security coordination; and
- departure, arrival, registration, filing, payment, and retention sequencing.

Five accountable workstreams organise the dated fact pattern, controlled client evidence, treaty and protocol grounding, entity/income/payroll analysis, and specialist/compliance sequence.

## Review and prohibited conduct

Every assessment starts as `specialist_review_required`. Its creator cannot perform the specialist review. The reviewer records either `specialist_reviewed` or `revision_required` with a reason.

Signals involving tax evasion, concealed presence or income, sham residence, backdated leases, false returns, or material misrepresentation prevent operationalization and cap readiness at 10. They remain visible as escalation flags and blockers; the system does not generate instructions to carry them out.

## Interfaces and persistence

- API prefix: `/api/v1/tax-residency`
- Operator workspace: `/tax-residency`
- Migration: `0042_tax_residency_treaty`
- Tables:
  - `tax_treaty_evidence`
  - `tax_treaty_evidence_decisions`
  - `tax_residency_assessments`
  - `tax_residency_assessment_reviews`

The next operational step is real jurisdiction-by-jurisdiction tax and treaty source onboarding through the existing official-source, snapshot, proposal, and independent-publication gates.

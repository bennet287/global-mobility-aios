# Investment Mobility Suitability v11.6

## Purpose

The v11.6 suitability layer compares a client's disclosed situation against independently published investment-mobility program versions. “Suitability” means mobility-route readiness only. It does not mean regulated investment suitability and does not produce an eligibility, authority, return, tax, banking, or capital-preservation conclusion.

## Inputs and provenance

An assessment requires an existing lead and at least one selected published program or target country with published programs. It records available and liquid capital, net worth, currency, risk posture, family size, timeline, capital-preservation requirements, source-of-funds confirmation, disclosed constraints, and optional controlled document references.

Each candidate retains its exact program version, pathway version, official source, and content-addressed source snapshot. Later catalogue changes never rewrite a prior comparison.

## Transparent readiness components

- **Capital coverage:** compares declared available capital with the recorded program threshold only when currencies match.
- **Evidence strength:** measures linked controlled and verified evidence plus explicit source-of-funds confirmation.
- **Family fit:** checks whether the published program version records dependant scope for the declared family size.
- **Risk alignment:** reflects declared risk posture and applies a material blocker where capital preservation is mandatory.

The highest-ranked candidate becomes the overall readiness headline. Every component and blocker remains visible; the aggregate is not an approval probability.

## Fail-closed controls

- No unpublished or superseded program version participates.
- No exchange-rate conversion is inferred when program and client currencies differ.
- Documents must belong to the selected lead.
- A linked Business & Wealth advisory must belong to the same lead.
- Missing controlled evidence and unconfirmed source of funds remain explicit blockers.
- Concealment, deception, evasion, sanctions circumvention, sham arrangements, or material misrepresentation signals cap readiness and prevent operationalization.
- Licensed immigration, tax, banking, sanctions, legal, and regulated investment review remains required before capital commitment.

## Review and audit

Assessments are immutable pending-review records. The generating actor cannot approve their own assessment. Review decisions are append-only, actor-attributed, and audited. Read-only roles cannot create or review comparisons.

## Interface and API

The `/investment-suitability` workspace presents client inputs, published program selection, score components, blockers, provenance, comparison history, and controlled next actions. API operations are exposed beneath `/api/v1/investment-mobility/suitability/assessments`.

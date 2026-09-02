# Governed Investment Mobility Programs v11.5

## Outcome

v11.5 introduces the controlled data and review layer for residence-by-investment, citizenship-by-investment, and investor-entrepreneur programs. It gives operators a structured catalogue that Business & Wealth advisory can rely on without converting a marketing statement, an old threshold, or a capital declaration into an eligibility conclusion.

The software workflow is complete. The catalogue begins empty by design: a jurisdiction is not represented until its current official material is onboarded, captured, linked to a published mobility pathway, and independently reviewed.

## Program version contract

Each immutable version records:

- a published business, entrepreneur, wealth, or investment pathway version;
- an active same-country official source and content-addressed source snapshot;
- minimum recorded commitment and currency;
- qualifying investment structures;
- holding-period and physical-presence context;
- family scope;
- due-diligence and source-of-funds requirements;
- fee context, benefits, and material risks;
- effective dates, proposer, independent reviewer, review notes, and publication time.

Creating a later version does not edit the published record. Independent publication marks the earlier version as superseded and preserves both records.

## Publication controls

Publication fails closed when:

- the selected pathway is missing, retired, not in a business/investment domain, or lacks a published version;
- the program and pathway countries differ;
- the official source is inactive or belongs to another country;
- the snapshot is not linked to that source, lacks a content hash, or has failed/rejected status;
- the draft creator attempts to publish their own work;
- another unresolved draft already exists for the program; or
- the program content promises guaranteed residence, citizenship, or authority approval.

Every create and publish mutation is authenticated, role-controlled, actor-attributed, and added to the audit ledger.

## Advisor integration

Investment-related Business & Wealth assessments now search the published program catalogue for the selected countries. A matching program contributes to the pathway-grounding score and is attached to the relevant strategy option with its exact program version, underlying pathway version, official source, snapshot, currency, and recorded minimum commitment.

The interface labels this state as `published_program_grounded`. It remains decision support: meeting the recorded threshold does not establish eligibility, suitability, lawful source of funds, investment performance, tax treatment, banking acceptance, or authority approval.

## Operator workspace

The `/investment-mobility` workspace provides:

- catalogue status and publication metrics;
- controlled program selection and version inspection;
- clear threshold, qualification-structure, due-diligence, family, and risk presentation;
- pathway/source/snapshot provenance;
- draft creation from already published pathways; and
- independent-review publication with backend-enforced reviewer separation.

The next operational step is jurisdiction evidence onboarding. The next product step is client-specific investment suitability and comparison backed only by independently published program versions.

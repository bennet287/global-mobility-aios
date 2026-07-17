# Supplemental Official Sources v10.21.2

## Purpose

Some jurisdictions have an independently approved primary authority and source, but the broad
primary portal is not suitable for automated monitoring from every deployment environment.
v10.21.2 adds a review-gated supplemental-source path without replacing or superseding the
approved primary certification.

The first operational use is Canada's official IRCC visitor-visa application page on
`ircc.canada.ca`. The broad `canada.ca` IRCC landing page remains the approved primary source;
the supplemental page is scoped to `visa` only.

## Safety model

A supplemental source:

- requires an existing approved `primary_immigration` certification;
- must belong to the same independently approved primary authority;
- requires an approved immigration-rule relationship;
- must use HTTPS;
- must use a `supplemental_<domain>` scope that matches the source domain;
- creates a new pending certification and never supersedes the primary certification;
- remains ineligible for baseline capture until a different reviewer approves it;
- never creates, approves, reviews, or publishes an initial rule automatically;
- never changes an immutable snapshot, pathway, client assessment, or coverage claim.

## Coverage behavior

The primary certification remains the evidence gate for reviewed primary authority and source.
A fresh monitor may be supplied by either:

1. the approved primary source, or
2. an independently approved supplemental source for the same jurisdiction.

A verified rule can be proposed from a supplemental evidence-batch item only after its exact
baseline snapshot exists. The assertion remains pinned to that supplemental source and snapshot.

## Canada pack

The included pack is:

`knowledge/global_coverage/tranches/v10_21_2_canada_supplemental_visa.json`

It creates one new evidence batch containing:

- the existing IRCC authority by exact name;
- a new official source: `https://ircc.canada.ca/english/information/applications/visa.asp`;
- an allowlisted HTTP monitor for `ircc.canada.ca`;
- one pending `supplemental_visa` certification;
- a link to Canada's existing approved immigration assessment.

It does not alter the existing primary IRCC source, certification, failed retrieval history, or
Canada's current coverage status.

## Operator sequence

1. Preview the pack with `Submit-SupplementalCoverageSource.ps1 -WhatIf`.
2. Submit it using the supplemental-source proposer identity.
3. Review the new supplemental certification with a different human reviewer.
4. Queue the new batch baseline capture.
5. Use the tranche assistant against the new batch to inspect the immutable snapshot and copy a
   constrained assertion draft.
6. Independently review and explicitly publish the assertion.
7. Confirm Canada's jurisdiction coverage receipt.

## Rollback

No database migration is introduced. The code can be rolled back without deleting any source,
certification, snapshot, assertion, or rule records. Existing supplemental records remain
ordinary audited evidence records and can be deactivated or rejected through existing controls.

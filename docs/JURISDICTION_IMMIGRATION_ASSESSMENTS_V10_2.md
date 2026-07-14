# Jurisdiction Immigration Assessments v10.2

## Outcome

The global registry now has a human-reviewed workflow for determining how each
jurisdiction's immigration rules relate to another jurisdiction. This prevents the
platform from inferring immigration independence from an ISO code, geographic label,
territory status, or political relationship.

## Controlled classifications

An assessment proposal must use one of these relationships:

- `independent` — the jurisdiction directly administers the relevant immigration rules;
- `parent_inherited` — the reviewed evidence establishes that a parent jurisdiction's rules apply;
- `shared_or_coordinated` — responsibilities or rules are divided or coordinated;
- `not_applicable` — immigration-rule assessment does not apply to the registry area;
- `unclear` — available evidence does not support a conclusive classification.

Inherited and shared proposals require a parent code that already exists in the active
registry. Independent proposals cannot retain a parent code.

## Evidence and review lifecycle

Every proposal requires:

- an HTTPS evidence URL;
- an evidence title;
- an evidence-based rationale;
- the authenticated proposer;
- optional links to an onboarded official source and immutable source snapshot.

New proposals are `pending_review`. The proposer cannot approve or reject their own
proposal. A different authenticated reviewer must record a decision and notes.

An approved replacement supersedes the previous approved assessment without deleting
history. Rejected, superseded, and approved versions remain auditable.

## Coverage-gate integration

Only an approved, conclusive relationship satisfies the immigration-rule-assessment
gate. Pending, rejected, absent, or approved-`unclear` assessments remain visible gaps.

Registry coverage rows now expose:

- the approved relationship and parent code;
- approved assessment provenance;
- any pending assessment awaiting review;
- assessed and pending-review totals;
- updated global release-gate status.

This assessment alone cannot make a jurisdiction coverage-ready. A separately reviewed
primary-authority/source certification, fresh certified-source monitor, and
human-published verified-rule gates must also pass.

## Interfaces

- `GET /api/v1/global-intelligence/registry/immigration-assessments`
- `POST /api/v1/global-intelligence/registry/{jurisdiction_id}/immigration-assessments`
- `POST /api/v1/global-intelligence/registry/immigration-assessments/{assessment_id}/review`
- `/global-intelligence`, Coverage tab, assessment and independent-review workspace

## Persistence

Migration `0018_jurisdiction_immigration_assessments` creates immutable assessment
versions with jurisdiction and registry-entry references, evidence provenance, review
metadata, and supersession links.

## Safety boundary

No jurisdiction was bulk-classified by this migration. The 249-entry registry remains
globally scoped, while its immigration-rule relationships remain unassessed until
official evidence is reviewed jurisdiction by jurisdiction.

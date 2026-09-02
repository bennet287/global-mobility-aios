# Primary Authority and Source Certification v10.3

## Outcome

Global registry coverage now distinguishes source onboarding from human-reviewed
primary-source coverage. Creating an authority, source, or monitor is necessary but no
longer sufficient to satisfy the global coverage release gate.

## Certification scope

Each certification links one active registry jurisdiction to:

- one active regulatory authority belonging to that jurisdiction;
- one active HTTPS official source belonging to that authority and jurisdiction;
- one or more declared regulatory domains;
- evidence notes explaining authority ownership, official status, source scope, and
  why it is the primary immigration source.

The selected source's domain must be included in the certified coverage domains.

## Review lifecycle

New certifications are `pending_review`. The authenticated proposer cannot review their
own certification. A different administrator or reviewer must approve or reject it with
notes.

An approved replacement supersedes the previous primary certification without deleting
history. Certifications are versioned independently for every jurisdiction and scope.

Approval is refused if the authority or source becomes inactive before review.

## Coverage-gate changes

The release gate now requires an approved `primary_immigration` certification for both
the authority and source checks. Raw onboarding remains visible separately.

Monitor freshness is calculated only against the approved certified source. A fresh
monitor on an uncertified secondary source cannot satisfy the jurisdiction gate.

Registry entries expose:

- authority and source onboarding state;
- reviewed primary-authority and primary-source state;
- approved certification provenance;
- pending certification review;
- certified-source monitor freshness;
- entry-level missing controls and aggregate coverage totals.

## Interfaces

- `GET /api/v1/global-intelligence/registry/source-certifications`
- `POST /api/v1/global-intelligence/registry/{jurisdiction_id}/source-certifications`
- `POST /api/v1/global-intelligence/registry/source-certifications/{certification_id}/review`
- `/global-intelligence`, Coverage tab, primary-source proposal and independent-review controls
- `/intelligence`, source onboarding workspace used before certification

## Persistence

Migration `0019_jurisdiction_source_certifications` stores immutable versions,
jurisdiction and registry references, authority/source references, domains, proposal
and review actors, decisions, evidence notes, and supersession links.

## Safety boundary

No source was bulk-certified. Existing onboarded records do not become reviewed merely
because this migration exists. Each of the 243 required registry entries remains a gap
until its evidence is independently approved and all other release gates pass.

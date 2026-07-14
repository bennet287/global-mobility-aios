# Regulatory Intelligence Foundation v7.0

## Outcome

Phase 7 begins the transition from a static official-source registry to a
review-gated regulatory intelligence system. The implementation connects:

```text
Jurisdiction
  -> Regulatory authority
  -> Official source
  -> Source monitor
  -> Immutable source snapshot
  -> Structured regulatory change
  -> Human review
  -> Published verified rule
  -> Supersession or retirement
```

No captured content or machine-detected change becomes an active rule
automatically.

## Data Model

### Jurisdiction

Represents a country, territory, or autonomous immigration jurisdiction. It has a
canonical code, optional parent, region, active state, and extensible metadata.

### Regulatory authority

Represents an official immigration ministry, embassy network, gazette,
legislature, education authority, labour authority, investment agency, tax
authority, or other approved authority. Authorities can own existing official
sources.

### Source monitor

Stores the intended retrieval method and interval plus last/next check state.
Version 7.1 executes due monitors through Celery Beat and dedicated Celery workers.
Each attempt has a durable retrieval-run record and uses ETag and Last-Modified
conditional requests when the authority provides them. Authorized manual snapshot
capture remains available for exceptional sources.

Retrieval controls include HTTPS-by-default, per-monitor domain allowlists,
standard-port enforcement, credential rejection, DNS resolution checks that block
private/link-local/loopback destinations, bounded redirects, response-size limits,
timeouts, content-type restrictions, and visible-text extraction. HTML, plain
text, JSON, XML, and PDF are supported; PDF parsing uses the core `pypdf`
dependency.

### Source snapshot

Each capture is immutable and linked to its predecessor. It stores normalized
content, SHA-256 hash, HTTP state, retrieval method, parser version, metadata, and
one of `baseline`, `unchanged`, or `changed`.

### Regulatory change

A changed snapshot produces a structured event. Supported types include:

- New program
- General rule or policy change
- Program removal
- Processing-time change
- Salary-threshold change
- Age-limit change
- Occupation-list change
- Quota change

Every event begins as `pending_review`. Materiality can be informational,
material, or critical. Critical events create a high-priority review.

### Verified rule publication

A reviewer first approves or rejects a change. Publication is a separate action
and is allowed only for approved changes. The resulting verified rule links the
jurisdiction, authority source, exact source snapshot, regulatory change,
effective dates, reviewer, confidence, and publication time.

Publishing a replacement rule can supersede one active rule in the same
jurisdiction and domain. The previous rule is deactivated, given an effective
end and retirement audit metadata, and linked from the replacement. Reviewers
can also retire an active rule explicitly with a reason and effective end.

## Operator Workspace

The Next.js `/intelligence` workspace gives reviewers one operational surface
for monitor health and freshness, due checks, recent retrieval failures, the
regulatory-change queue, before/after evidence, approval or rejection,
review-gated rule publication, supersession, rule retirement, and immutable
snapshot previews. The workspace never bypasses the API review gates.

Version 7.2 adds controlled source onboarding and coverage operations. A single
audited workflow creates or updates the jurisdiction, authority, official source,
and source monitor. It validates the complete request before committing, accepts
only HTTPS authority URLs on the standard port, rejects credentials and malformed
allowlists, requires the source hostname to be covered by the retrieval allowlist,
and prevents an existing source from being silently reassigned to another
jurisdiction or authority.

The Coverage view reports monitoring coverage and freshness by jurisdiction,
authority, and declared regulatory domain. It also exposes source counts, monitor
errors, pending changes, and active verified rules so gaps are operationally
visible rather than inferred from the source registry.

## Authority Parser Profiles and Program Lifecycle Detection

Version 7.3 adds versioned parser profiles to every source monitor:

- `generic` handles HTML, text, JSON, XML, and PDF evidence.
- `gazette_html_v1` removes navigation and page chrome and prefers the official
  notice content inside `main` or `article`.
- `structured_program_catalog_v1` reads an authority JSON catalogue using a
  per-monitor field mapping and produces a deterministic normalized programme
  ledger.

Structured catalogue configuration supports the record path, identifier, name,
status, summary and effective-date fields, retired status values, and an explicit
`missing_means_retired` policy for complete catalogues. Comparing two normalized
catalogues creates separate `pending_review` events for new programs, changed
programs, status-based retirement, and configured removal from a complete
catalogue. Every event receives its own human-review record and evidence diff;
none is automatically published as a verified rule.

Migration `0010_authority_parser_profiles` adds the parser profile and versioned
configuration to source monitors.

## API Surface

- `POST/GET /api/v1/regulatory-intelligence/jurisdictions`
- `POST/GET /api/v1/regulatory-intelligence/authorities`
- `POST /api/v1/regulatory-intelligence/source-onboarding`
- `GET /api/v1/regulatory-intelligence/dashboard`
- `POST/GET /api/v1/regulatory-intelligence/source-monitors`
- `POST /api/v1/regulatory-intelligence/source-monitors/{monitor_id}/run`
- `GET /api/v1/regulatory-intelligence/retrieval-runs`
- `GET /api/v1/regulatory-intelligence/snapshots`
- `POST /api/v1/regulatory-intelligence/sources/{source_id}/snapshots`
- `GET /api/v1/regulatory-intelligence/changes`
- `POST /api/v1/regulatory-intelligence/changes/{change_id}/review`
- `POST /api/v1/regulatory-intelligence/changes/{change_id}/publish`
- `GET /api/v1/regulatory-intelligence/verified-rules`
- `POST /api/v1/regulatory-intelligence/verified-rules/{rule_id}/retire`

Mutation endpoints are limited to `admin` and `reviewer` roles. Read operations
follow the existing read-role policy.

## Safety and Audit Guarantees

- Initial baselines and unchanged captures do not create regulatory-change noise.
- Every changed snapshot is linked to both old and new evidence.
- Every material change creates a `HumanReview` record.
- Publication before approval is rejected.
- Detection, review, publication, jurisdiction onboarding, authority onboarding,
  and snapshot capture write audit records.
- Publication is idempotent for a regulatory change.
- Supersession and retirement preserve the previous rule and write dedicated
  lifecycle audit records rather than deleting history.
- Retrieval failures never produce snapshots or regulatory changes and persist a
  safe error code for operations.
- Redirect destinations are revalidated against the allowlist and public-address
  policy before retrieval.

## Remaining Increment

- Production egress proxy/network policy to complement application-layer SSRF controls

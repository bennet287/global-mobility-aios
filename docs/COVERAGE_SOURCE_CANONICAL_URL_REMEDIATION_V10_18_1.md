# Coverage Source Canonical URL Remediation v10.18.1

## Outcome

The Austria starter-tranche monitor originally used
`https://www.migration.gv.at/en/`. The upstream service responds with a redirect
to an `http://` URL. The controlled retriever correctly rejects that transport
downgrade with `scheme_not_allowed` instead of weakening its HTTPS policy.

v10.18.1 changes the seed pack to the directly reachable canonical HTTPS page:

`https://www.migration.gv.at/en/welcome/?no_cache=1`

## Existing deployments

`Repair-CoverageSourceCanonicalUrl.ps1` updates the already-onboarded source
record in place so its source ID, approved certification, and evidence-batch
links remain intact. The operation:

- permits HTTPS only;
- requires the hostname to remain unchanged;
- requires the hostname to remain on the monitor allowlist;
- rejects credentials and non-standard ports;
- refuses to alter a source after an immutable snapshot exists;
- clears the prior operational error and makes the monitor eligible for retry;
- writes `coverage_source_canonical_url_corrected` to the audit log.

The script does not change an immigration assessment, certification decision,
verified rule, snapshot, or coverage claim.
## v10.18.2 reporting hotfix

The original remediation helper committed the database transaction and then read
SQLAlchemy-managed attributes after the session had closed. Because mapped
attributes expire on commit by default, the command could report a
`DetachedInstanceError` even though the source URL and monitor reset had already
been committed.

v10.18.2 copies scalar IDs and status values while the session is still open and
prints only the detached-safe result object afterward. A rerun is idempotent: if
the canonical URL is already stored and the monitor is already reset, the command
returns `changed=false` and `already_corrected=true` without creating another
audit event.


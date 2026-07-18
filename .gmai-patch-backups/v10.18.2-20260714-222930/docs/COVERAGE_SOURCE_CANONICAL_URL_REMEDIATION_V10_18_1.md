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

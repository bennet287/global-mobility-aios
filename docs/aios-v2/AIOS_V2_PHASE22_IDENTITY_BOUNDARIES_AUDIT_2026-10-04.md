# AIOS V2 — Phase 22 Identity and Boundaries Audit

**Exact audited integration:** `e6c85ad71ed4f8134264d21a75d6284486da961b` (PR #299).
**Date:** 2026-10-04.
**Scope:** read-only ownership/gap audit and execution contract for `identity_boundaries`. No host operation, login, secret resolution, migration or receipt write is performed by this audit.
**Migration head:** `0100_phase22_release_networking_contract`.

## Decision and canonical owners

Extend the existing Phase 22 deployment run/immutable receipt owner. Do not introduce an identity directory, session store, browser-evidence database or second deployment owner. Foundation v1 remains unable to write `satisfied`; the release/networking v2 writer remains restricted to its existing gate.

| Required fact | Existing owner | Meaningful deployed proof |
| --- | --- | --- |
| Issued session | `apps/api/app/routers/auth.py::login`, `/auth/me` | Actual browser form login at the prepared API HTTPS origin, then authenticated web-origin API access. |
| Signed expiry | `apps/api/app/core/auth.py::create_session_token/parse_session_token` | Observe an actually issued token before and after its real expiry, without changing deployed time or TTL. |
| Role denial | `core/auth.py::auth_middleware`, `core/auth_policy.py::AUTH_RULES/required_roles` | A signed `read_only` session receives 403 on an admin-only GET such as `/debug/controlled-agents`, with paired admin reachability; no mutation is needed. |
| Header bypass disabled | `get_auth_context`, production startup validation, production Compose | No-cookie request with forged `X-GMAI-Role`/user headers still receives 401 on a protected API route. |
| Credentialed CORS | `apps/api/app/main.py::CORSMiddleware` | Approved-origin preflight and real credentialed requests, unauthorized-origin rejection, CORS decoration of 401/403. |
| Cookie scope | `routers/auth.py::login`, `apps/web/lib/request-client.mjs::buildApiRequestInit` | Actual Secure/HttpOnly/SameSite=Lax, host-only scope, lifetime and browser behavior; the compiled web request path uses credentials and excludes production role headers. |
| Default credentials | `core/startup_safety.py::validate_production_settings` | Non-default file-backed bootstrap credential, real default-login rejection and no issued session for failed login. |
| Secret resolution | `Settings.__getattribute__`, `core/secrets.py::SecretsPort/FileSecretsPort` | Bounded deployed references, intended mount scope, fail-closed missing references; values never enter persistent evidence. |
| Gate acceptance | `ProductionDeploymentAcceptanceRun`, `ProductionDeploymentAcceptanceCheckReceipt`, `production_deployment_acceptance.py` | Exact run/host/release identity, fresh gate and one immutable restricted-writer receipt after complete proof. |

## Current implementation and limitations

The login endpoint checks one shared bootstrap username/password and signs the role selected by its holder. This proves enforcement of a signed selected role, not independent per-user role assignment, SSO or an enterprise directory. Do not manufacture another role authority for this gate.

Session tokens carry version, issue time and expiry. `Settings.auth_session_ttl_seconds` defaults to 28,800 seconds and is bounded to 300–86,400. Tests using mocked clocks prove code contracts only. Cookie removal, logout, forged expired tokens and changing production TTL are not substitutes for real issued-session expiry.

The API issues a host-only SameSite=Lax cookie. The web client sends `credentials: include`. The networking contract binds distinct hostnames but does not guarantee that they are browser same-site. A successful API-origin login alone therefore does not prove web-origin access. The deployed browser must demonstrate the real hostname/cookie/CORS combination; incompatible topology remains blocked. Do not guess registrable-domain relationships with a string suffix rule or relax cookie policy merely to obtain a pass.

Production startup requires auth enabled, header-role bypass disabled and non-default mandatory credentials. CORS is the outer response boundary. The login page nevertheless retains local-default credential instructions in production; those are stale messaging, not evidence that default credentials are valid.

Existing `test_auth_roles.py`, `test_cors_auth.py`, `test_startup_safety.py` and `test_secrets.py` establish isolated contracts. CI browser fixtures do not establish live ingress, production credential, session lifetime or credential-isolation facts.

## Concrete secret-mount gap

`docker-compose.prod.yml` defines `x-runtime-secret-volume` as a read-only bind of all `AIOS_SECRETS_DIR` to `/run/secrets/aios`. PostgreSQL, api-migrate, API and worker reuse that mount. Beat already uses a scheduler-only environment with no credential-directory mount. The documented example contains the database password, JWT secret, bootstrap admin password, automation keys, document-token secret, object-store credentials and enabled provider keys under the same root.

Omitting `AUTH_ADMIN_PASSWORD_REF` from worker environment metadata does not prevent filesystem access to `auth/admin_password`. PostgreSQL and api-migrate similarly receive unrelated authentication, storage and provider material. Read-only mounting protects against writes; it does not limit read access. Current code does not establish workload-level credential isolation.

The first bounded implementation prerequisite is therefore **runtime-secret mount isolation by actual workload need**, within the existing Compose/Settings/SecretsPort owner:

- PostgreSQL receives only its database credential scope.
- api-migrate receives only the database material its connection path needs.
- API receives its required application material and bootstrap credential.
- Worker receives its required runtime material, excluding the bootstrap admin password. Beat retains its existing scheduler-only/no-credential-mount topology unless an actual consumer need is established.
- web, ingress and Redis receive no AIOS credential directory.
- Optional provider material remains absent unless that provider is enabled; no new provider, credential or paid execution is activated.

Inspect actual consumer needs before restricting shared JWT, automation, document or storage material. Do not remove a required credential to make a superficial mount check pass. Preserve canonical file references, fail-closed resolution and operational rotation/revocation contracts. Directory/file mount layout must account for atomic host replacement: individual file bind mounts can retain the old inode. Do not silently break existing JWT, webhook, document-token, database or automation-key rotation procedures, duplicate credential values into environment metadata, or adopt a new secrets backend. OpenBao remains a non-production pilot.

## Satisfied-capable identity executor contract

After the concrete prerequisites are closed, implement one distinct internal executor/writer restricted to `identity_boundaries`. No public receipt-write endpoint, new table or migration is justified by this audit.

Before any login or host probe, verify the prepared run and exact host/release/configuration with the existing target-host pattern. Reject an existing identity-gate receipt before execution. Keep synthetic canary constraints, authority/resource ceilings and fresh-run immutable evidence semantics intact.

The complete gate must include:

1. Actual browser login at the prepared API HTTPS origin with a controlled bootstrap credential, followed by authenticated web-origin API access through real ingress. No route interception, fixture API, fake cookie or disabled certificate validation.
2. Actual cookie flags/scope/lifetime plus approved and denied CORS behavior. CORS denial is browser cross-origin access denial; it is not an independent API authorization rule.
3. No-cookie authentication denial, forged-header denial, default/invalid login rejection and signed restricted-role denial on read-only routes.
4. Real issued-session expiry under deployed time and TTL. The executor may run long enough for that configured lifetime, with explicit bounded duration and honest pending status. It must not temporarily shorten TTL, manipulate the server clock or persist a blocked receipt that it later upgrades. After actual expiry, test browser behavior and bounded replay of the original expired token to distinguish browser cookie removal from server expiry enforcement.
5. Bounded secret-surface checks tied to the exact release and observation interval: actual runtime mount/environment scope, client assets and relevant logs. Include embedded URL credentials (for example Redis URLs), rather than checking only conventional secret variable names. Persist surface identifiers, redacted results and limitations; never values, tokens, cookies, environment dumps or credential-bearing traces. A clean finite scan is not universal proof of absence, particularly for transformed/encoded values or unobserved logs.
6. Re-check exact running host/release identity after the potentially long observation. A changed release, unavailable dependency, incomplete surface, failed expiry/denial probe or secret exposure prevents satisfaction.
7. Write one immutable receipt only after complete internally derived evidence. Partial checks remain failed/blocked/unknown as appropriate; none may satisfy the entire gate.

Credentials, cookies and transient comparison buffers must stay in bounded private execution memory. Disable browser traces/HAR/screenshots that could capture secrets; do not retain raw browser storage. Operational provisioning and rotation remain separate authorized host work, not steps secretly performed by the probe.

## Evidence and authority limits

This audit creates no live-host evidence and does not establish a satisfied identity receipt, production readiness, six-gate completion, canary qualification, GRSI promotion, per-user identity, universal secret non-disclosure, credential rotation or paid autonomy.

Operational proof still needs real HTTPS/DNS, exact deployed image/configuration, running production dependencies, isolated synthetic canary, controlled credentials, required browser tooling and enough time for actual expiry. Missing access remains an explicit operational blocker; CI is not a replacement.

## Bounded order

1. Isolate runtime-secret mounts while preserving consumer/rotation contracts; verify resolved Compose scopes and meaningful denial/replacement regressions.
2. Correct production-only login messaging within its existing owner.
3. Implement the complete identity-boundaries executor and restricted receipt writer, with browser and redaction/failure/expiry contracts.
4. Execute real target-host proof when operational prerequisites exist.

The remaining Phase 22 gates are still independently required. GRSI.E remains unsealed; do not start GRSI.F from this audit or a future isolated identity receipt.

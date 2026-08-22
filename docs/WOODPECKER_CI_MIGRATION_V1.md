# Global Mobility AIOS — Woodpecker CI Migration V1

**Status:** IMPLEMENTED FOR PARITY PILOT / NOT YET CANONICAL CI
**Date:** 2026-08-22
**Source control / PR forge:** GitHub remains in place
**CI execution candidate:** Woodpecker CI self-hosted

## Objective

Move expensive CI execution away from GitHub-hosted runners without weakening the V12 Production Proof contract.

The migration preserves the existing four proof lanes:

1. repository policy and constraints;
2. backend regression on SQLite;
3. frontend tests, types and production build;
4. PostgreSQL governance/autonomy contracts.

GitHub remains the repository, pull-request and review surface. Woodpecker receives GitHub webhook events and reports workflow status back to the forge.

## Architecture

```text
GitHub repository / pull request
            |
            | webhook
            v
      Woodpecker server
            |
            v
      self-hosted agent
            |
    +-------+-------+-------+-------+
    |               |               |
repo policy      SQLite         frontend      PostgreSQL
    |               |               |              |
    +---------------+---------------+--------------+
                            |
                            v
                     workflow statuses
                            |
                            v
                          GitHub
```

Woodpecker is CI infrastructure only. It has no AIOS domain authority and cannot change Evidence, VerifiedRules, autonomy, Board authority or canonical application state merely by passing a build.

## Repository files

```text
.woodpecker/
├── repository-policy.yml
├── backend-sqlite.yml
├── frontend.yml
└── postgres-governance.yml

docker-compose.woodpecker.yml
.env.woodpecker.example
```

The initial pilot intentionally runs the same proof lanes on push / pull request events. Path-aware optimization is deferred until parity is demonstrated so that cost reduction cannot hide correctness regressions during migration.

## Local/self-hosted installation

1. Create a GitHub OAuth application for the Woodpecker instance.
2. Set the homepage URL to `WOODPECKER_HOST`.
3. Set the OAuth callback URL to `${WOODPECKER_HOST}/authorize`.
4. Copy `.env.woodpecker.example` to `.env.woodpecker` and fill the OAuth credentials.
5. Generate `WOODPECKER_AGENT_SECRET` locally, for example with `openssl rand -hex 32`.
6. Start Woodpecker:

```bash
docker compose --env-file .env.woodpecker -f docker-compose.woodpecker.yml up -d
```

7. Sign in to Woodpecker with GitHub and activate `bennet287/global-mobility-aios`.
8. Confirm Woodpecker creates the GitHub webhook and can read this private repository.
9. Push a bounded test commit and compare all four Woodpecker results with the same GitHub Actions Production Proof result.

The Woodpecker host used for GitHub integration must be reachable by GitHub webhooks. A local workstation therefore needs a secure externally reachable HTTPS endpoint or an equivalent controlled ingress solution.

## Acceptance gate

Woodpecker does not become canonical CI merely because configuration files exist.

Required parity proof:

```text
exact commit
   |
   +--> GitHub Actions V12 Production Proof ---- PASS 4/4
   |
   +--> Woodpecker parity workflows ----------- PASS 4/4
   |
   +--> result / migration head / test counts -- equivalent
```

Before disabling expensive GitHub-hosted jobs, record at least two representative parity runs:

- one backend / migration / governance-affecting change;
- one frontend-affecting change.

The migration must fail closed on disagreement. If Woodpecker and GitHub Actions disagree, GitHub Actions remains canonical until the reason is understood and fixed.

## Phase 2 — reduce GitHub minutes

Only after parity acceptance:

- retain a minimal GitHub-side integration/status safety check if required by branch/ruleset constraints;
- move full SQLite, frontend and PostgreSQL execution to Woodpecker;
- update required-check enforcement to the accepted Woodpecker statuses only after GitHub confirms those external statuses are usable by the repository ruleset;
- disable or narrow GitHub-hosted duplicate workflows;
- keep an explicit manual/fallback Production Proof path during the transition window.

## Phase 3 — path-aware execution

After migration stability, reduce unnecessary self-hosted compute while preserving full release/seal proof.

Candidate policy:

```text
docs-only
  -> repository policy + documentation consistency

frontend-only
  -> repository policy + frontend

backend application
  -> repository policy + SQLite

migration / governance / autonomy
  -> full four-lane proof

accepted/sealed checkpoint / release candidate
  -> full four-lane proof regardless of paths
```

Woodpecker supports GitHub pull-request events, multiple workflows and path conditions, so this optimization can remain inside the open-source CI layer.

## Security boundaries

The Woodpecker agent uses the host Docker socket. Treat that runner as privileged CI infrastructure:

- run it on a dedicated or trusted machine;
- do not expose the Docker socket over TCP;
- do not place production AIOS credentials in repository files;
- use Woodpecker secrets for CI-only credentials;
- do not allow untrusted repositories to use the same privileged agent;
- keep `WOODPECKER_OPEN=false` and restrict administration;
- review pull-request execution policy before accepting contributions from untrusted forks.

## Cost doctrine

Woodpecker itself introduces no hosted CI-minute charge. Cost becomes local hardware/electricity/storage or the price of any server chosen later.

The goal is not merely lower cost:

> **CI cost may be optimized only while the Production Proof quality floor remains unchanged.**

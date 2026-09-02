# V12.50 — CI Diff-Hygiene Full-History Fix

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** CI source/configuration repair
**Milestone impact:** none — L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

## 1. Failure observed

After the V12.49 documentation correction, GitHub Actions began executing normally rather than failing before runner startup.

Both policy workflows reached the multi-commit diff-hygiene step and failed with:

```text
Diff hygiene setup failed:
V12 diff-hygiene baseline is not present in the CI checkout.
Expected 8624d7f9891a3af6bcbd3693c1286984f5c1fbfd;
increase policy checkout depth rather than fetching unauthenticated history.
```

This is a real CI configuration defect, not an infrastructure-only failure and not a source whitespace failure.

## 2. Root cause

`scripts/check_diff_hygiene.py` deliberately requires the accepted V12 transition baseline:

`8624d7f9891a3af6bcbd3693c1286984f5c1fbfd`

for the long-lived V12 PR path.

The script also deliberately refuses to fetch missing transition history itself because the accepted boundary is:

```text
authenticated CI checkout must contain the declared baseline
!= script performs unauthenticated history fetch
```

However, both GitHub jobs that execute this gate used:

`fetch-depth: 64`

The transition baseline is older than that shallow history window.

Therefore the gate could not evaluate the diff at all.

## 3. Repair

Updated:

`.github/workflows/repo-policy-check.yml`

```yaml
actions/checkout@v4
fetch-depth: 0
```

Updated only the `repository-policy` checkout in:

`.github/workflows/v12-production-proof.yml`

to:

```yaml
fetch-depth: 0
```

Backend, frontend and PostgreSQL jobs keep their existing checkout behavior because they do not execute the multi-commit diff-hygiene transition-baseline gate.

## 4. Regression guard

`scripts/check_repo_policy.py` now requires full-history checkout inside the exact YAML job blocks that execute diff hygiene:

```text
.github/workflows/repo-policy-check.yml
  job: repo-policy-check

.github/workflows/v12-production-proof.yml
  job: repository-policy
```

The guard is scoped to each job block, so an unrelated later checkout cannot satisfy the requirement accidentally.

## 5. Boundaries

This repair does not:

- change the V12 transition baseline;
- grandfather new hygiene debt;
- weaken `git diff --check`;
- allow unauthenticated history fetches from the hygiene script;
- change product/runtime behavior;
- change technology adoption;
- complete professional Austria review;
- seal L;
- start M or N.

## 6. Relationship to local V12.48 failure

The CI shallow-history defect is independent of the local V12.48 clean-worktree failure.

Current two separate issues:

```text
local V12.48 acceptance
  FAIL — additional untracked .local/ state must be inspected

GitHub policy CI
  REPAIRED — policy checkout now carries full history
  CURRENT-HEAD CI RESULT PENDING
```

Do not use one issue to explain away the other.

## 7. Acceptance

The CI repair is not considered proven until:

1. local repository policy passes at the repaired current head;
2. local diff hygiene passes;
3. GitHub policy workflow reaches and passes multi-commit diff hygiene with the transition baseline available;
4. V12 Production Proof repository-policy job passes the same gate.

The genuine independent Austria professional review remains the release-critical external gate after local/CI hygiene is clean.

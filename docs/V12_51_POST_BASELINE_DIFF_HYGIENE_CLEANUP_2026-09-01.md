# V12.51 — Post-Baseline Diff-Hygiene Cleanup

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** documentation hygiene repair exposed by restored CI history
**Milestone impact:** none — L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

## 1. Why this tranche exists

V12.50 repaired the GitHub policy checkout so `check_diff_hygiene.py` could finally see the accepted V12 transition baseline:

`8624d7f9891a3af6bcbd3693c1286984f5c1fbfd`

Once the baseline was available, CI correctly exposed real trailing whitespace introduced after that baseline.

This is different from the earlier shallow-history setup failure.

## 2. CI evidence

The policy job reached:

```text
Diff hygiene base:
8624d7f9891a3af6bcbd3693c1286984f5c1fbfd
(V12 long-lived-branch transition baseline)
```

and reported 22 trailing-whitespace violations across five files.

## 3. Exact cleanup set

Cleaned:

```text
docs/L_AUSTRIA_BLIND_PROFESSIONAL_REVIEW_HANDOFF_2026-08-31.md
docs/TECHNOLOGY_RADAR_V1_3_6.md
docs/TECHNOLOGY_RADAR_WAVE_E2_EVALUATION_HARDENING_2026-08-31.md
docs/TECHNOLOGY_RADAR_WAVE_E3_PROPERTY_INVARIANT_TESTING_2026-08-31.md
docs/TECHNOLOGY_RADAR_WAVE_E4_MUTATION_TESTING_2026-08-31.md
```

Only trailing spaces/tabs were removed.

No semantic wording, status, authority boundary, test behavior, runtime configuration or baseline was changed.

## 4. What was not done

This cleanup did not:

- move the transition baseline;
- expand grandfathered history;
- disable `git diff --check`;
- weaken `check_diff_hygiene.py`;
- ignore Markdown files;
- modify application/runtime source;
- change Technology Radar status;
- change professional-review semantics;
- seal L or start M/N.

## 5. Current acceptance state

```text
V12.47 admin proof at 80deef2...             historical PASS
V12.48 local acceptance at b079428...         FAIL — untracked .local/ state
V12.50 CI full-history repair                 IMPLEMENTED
V12.51 post-baseline whitespace cleanup       IMPLEMENTED
current-head local clean-worktree proof        PENDING
current-head GitHub policy proof               PENDING
genuine professional Austria review            PENDING
```

## 6. Remaining local blocker

The local workstation still needs to identify the untracked content under `.local/` that became visible after removing the broad operator-only exclude.

Do not broaden `.gitignore` or delete unknown files until inspection identifies them.

## 7. Acceptance boundary

V12.51 is complete only when current-head:

1. repository policy passes locally;
2. transition-baseline diff hygiene passes locally;
3. GitHub Repository Policy Check passes multi-commit diff hygiene;
4. V12 Production Proof repository-policy job passes the same gate;
5. local worktree is clean after the `.local/` content is classified/resolved.

# V12.48 — Administration Acceptance Failed on Untracked .local State

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Attempted exact head:** `b079428a0fd607d6fd9491847312869d6802138c`
**Classification:** failed exact-head administration acceptance attempt
**Milestone impact:** none — L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

## 1. Summary

The V12.48 administration/recovery acceptance run did **not** pass.

The repository/documentation checks themselves were green, but the clean-worktree gate correctly failed because Git reported an untracked `.local/` path after the broad operator-local `/.local/` rule was removed from `.git/info/exclude`.

A later unconditional `Write-Host "Stable V12.48 documentation exact-head proof: PASS"` line printed after the thrown exception. That output is not valid proof and must be ignored.

## 2. Observed successful checks

At `b079428a0fd607d6fd9491847312869d6802138c`, the run observed:

```text
local .git/info/exclude broad /.local/ removal      PASS
reviewer packet ignored by repository .gitignore   PASS
reviewer return ignored by repository .gitignore   PASS
administration documentation whitespace             PASS
recovery / authority consistency                    PASS
repository policy                                   PASS
release consistency                                 PASS
Python dependency constraints                       PASS — 27
diff hygiene                                        PASS
git diff --check                                    PASS
start HEAD == end HEAD                              PASS
frozen V11                                          PASS
R3 authority/security/interop refs                  PASS
deep-R3 backup                                      PASS
```

## 3. Failing gate

The clean-worktree check reported:

```text
?? .local/
Worktree is not clean.
```

Therefore:

```text
stable SHA alone
+ green repository gates
+ untracked worktree state
!= exact-head acceptance PASS
```

The run is classified as **FAILED / LOCAL HYGIENE INVESTIGATION REQUIRED**.

## 4. Why this appeared only after the ignore cleanup

Before this run, the local workstation had a broad operator-only rule:

`/.local/`

inside:

`.git/info/exclude`

The repository itself intentionally ignores only:

`.local/professional-review/`

Removing the broad local rule exposed some additional content somewhere under `.local/`.

The reviewer packet and blank reviewer-return template are **not** the cause: `git check-ignore -v` showed both are correctly ignored by the repository-owned narrow rule.

The remaining untracked `.local/` content has not yet been identified.

## 5. Required investigation before any cleanup

Do **not** broaden repository `.gitignore` and do **not** delete `.local/` blindly.

First inspect exactly what Git sees:

```powershell
git status --short --untracked-files=all -- .local
git ls-files --others --exclude-standard -- .local
Get-ChildItem -Force .local -Recurse | Select-Object FullName, Length, LastWriteTime
```

Then classify each untracked item as one of:

```text
reproducible local proof/operator artifact  → add a narrow repository ignore if it is a recurring project workflow
valuable local evidence / work product       → preserve outside ignored scratch or intentionally commit through the correct evidence path
accidental/stale throwaway state             → remove locally after inspection
unknown                                      → do not delete or ignore until understood
```

## 6. Proof correction boundary

The previously recorded V12.47 administration proof at exact head:

`80deef2618038799caa39674ebfc3d92126cfe0f`

remains historical proof for that head.

This V12.48 attempt at `b079428...` is **not** green proof.

## 7. Current project truth

```text
V12.47 administration exact-head proof      PASS at 80deef2...
V12.48 administration acceptance attempt    FAIL — untracked .local state
blind professional-review tooling           LOCALLY PROVEN at d969c7d...
reviewer packet/template generation         COMPLETE / local handoff artifacts
genuine professional Austria review         PENDING
L                                             IMPLEMENTED / ACCEPTANCE PENDING
M                                             NOT STARTED
N                                             NOT STARTED
```

The release-critical external gate remains the qualified independent Austria professional review, but the local `.local/` hygiene issue should be resolved before the next exact-head acceptance run so clean-worktree semantics remain trustworthy.

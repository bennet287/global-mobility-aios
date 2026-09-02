# V12.53 — Secondary Local Artifact Archive Classification

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** local-worktree hygiene / recovery preservation correction
**Milestone impact:** none — L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

## 1. Trigger

The V12.52 local acceptance run successfully moved the five preservation buckets previously classified in `V12_52_LOCAL_ARTIFACT_CLASSIFICATION_2026-09-01.md`, but the clean-worktree check still failed.

Newly exposed untracked state:

```text
.local/archives/
.local/discovery/
.local/13.16.6-owner-inbox-discovery.txt
```

The shell also printed later unconditional `PASS` messages after thrown exceptions. Those prints are not acceptance evidence.

## 2. Observed content

The new `.local/archives/` root contains historical sealed/baseline/runtime ZIPs plus manifests and SHA-256 files, including 13.16.5 through 13.16.10 and pre-Radar/Radar baseline snapshots.

The new `.local/discovery/` root contains historical discovery snapshots, including mobility-user and persistence-source discovery outputs.

The root-level `13.16.6-owner-inbox-discovery.txt` is also a historical discovery note.

These are not cache/temp artifacts.

## 3. Anti-duplication / dependency check

Canonical V12 repository search found no references to:

```text
.local/archives
.local/discovery
13.16.6-owner-inbox-discovery.txt
global-mobility-aios-13.16.10-sealed
13.16.7-mobility-user-discovery
```

Therefore they are not hidden canonical runtime dependencies.

## 4. Classification

All three are:

```text
PRESERVE OUTSIDE REPOSITORY
```

Specifically:

```text
.local/archives/
.local/discovery/
.local/13.16.6-owner-inbox-discovery.txt
```

They should be moved into the already-created dated archive:

`D:\gmai-local-archive-20260901`

Do not add repository ignore rules for these paths and do not delete them.

## 5. Updated local-artifact policy

The complete known local classification is now:

```text
IGNORE IN PLACE
  .local/gmai-dev-cache/
  .local/gmai-dev-temp/
  .local/professional-review/

PRESERVE OUTSIDE WORKTREE
  .local/gmai-legacy-wrapper-artifacts-20260814/
  .local/patches/
  .local/runtime/
  .local/sqlite-backups/
  .local/technology-radar-v1/
  .local/archives/
  .local/discovery/
  .local/13.16.6-owner-inbox-discovery.txt
```

Permanent boundary:

```text
CLEAN WORKTREE != HIDDEN UNKNOWN STATE
RECOVERY MATERIAL != RUNTIME DEPENDENCY
LOCAL ARTIFACT != CANONICAL EVIDENCE
```

## 6. PowerShell acceptance-output correction

The V12.52 operator transcript demonstrated a recurring shell hazard: each pasted PowerShell statement executes independently in the interactive prompt, so a `throw` in one statement can be followed by later pasted `Write-Host "... PASS"` statements.

Therefore future canonical PowerShell acceptance blocks must:

1. run inside one enclosing script block (for example `& { ... }`);
2. set `$ErrorActionPreference = "Stop"`;
3. print final PASS only at the end of the enclosing block;
4. never place unconditional PASS output after a gate that may throw.

A thrown gate means the acceptance run is failed even if later separately pasted statements print PASS.

## 7. V12.52 run classification

Observed green checks at `ecd37345...` included:

- repository policy;
- release consistency;
- Python dependency constraints;
- latest-commit diff hygiene;
- `git diff --check`;
- stable local/origin SHA;
- frozen V11 and R3 refs;
- deep-R3 backup.

But the acceptance failed because:

```text
git ls-files --others --exclude-standard -- .local
→ returned additional untracked history/recovery files

git status --porcelain
→ ?? .local/
```

Therefore V12.52 is **NOT** exact-head clean-worktree PASS.

## 8. Next local action

1. sync the current V12 head;
2. move `.local/archives/`, `.local/discovery/`, and `.local/13.16.6-owner-inbox-discovery.txt` to `D:\gmai-local-archive-20260901`;
3. verify the archive contains all previously moved preservation buckets plus these three;
4. require no untracked `.local/` content after normal repository ignore rules;
5. run current-head repository gates inside one fail-fast PowerShell block;
6. require start HEAD == end HEAD == origin V12;
7. only then call the local administration/hygiene proof green.

## 9. Milestone boundary

This correction does not change:

```text
K.1  COMPLETE / PASS / SEALED
L    IMPLEMENTED / ACCEPTANCE PENDING
M    NOT STARTED
N    NOT STARTED
```

The genuine qualified independent Austria professional review remains the release-critical external gate after local/CI hygiene is clean.

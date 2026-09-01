# V12.52 — Local Artifact Classification and Narrow Ignore Policy

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** local-worktree hygiene / recovery preservation
**Milestone impact:** none — L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

> **Correction:** the next local run exposed three additional preservation/history items not present in the first inventory: `.local/archives/`, `.local/discovery/`, and `.local/13.16.6-owner-inbox-discovery.txt`. See `docs/V12_53_SECONDARY_LOCAL_ARTIFACT_ARCHIVE_2026-09-01.md`. V12.52's eight-bucket inventory is therefore an initial classification, not the final complete local inventory.

## 1. Trigger

Removing the workstation-only broad `/.local/` rule from `.git/info/exclude` exposed the full contents of the repository-local `.local/` tree.

The inventory showed eight distinct buckets:

```text
.local/gmai-dev-cache/
.local/gmai-dev-temp/
.local/gmai-legacy-wrapper-artifacts-20260814/
.local/patches/
.local/professional-review/
.local/runtime/
.local/sqlite-backups/
.local/technology-radar-v1/
```

A repository search found no canonical V12 references to the seven non-review bucket names. None may therefore be treated as a hidden runtime dependency without new evidence.

## 2. Classification

### IGNORE IN PLACE — reproducible scratch

```text
.local/gmai-dev-cache/
.local/gmai-dev-temp/
```

Observed contents include npm cache, npm debug logs, Node compile cache, pytest temporary directories, GitKraken/GitLens IPC scratch, Pyright/language-server temp files and command-line sentinel files.

These are machine-local, reproducible developer state and are not evidence.

Repository `.gitignore` now owns narrow rules for exactly these two roots.

### ALREADY IGNORED — reviewer handoff scratch

```text
.local/professional-review/
```

This remains the reproducible blind reviewer packet / blank-return handoff directory and is already covered by the repository-owned narrow ignore rule.

It is not canonical professional evidence.

### PRESERVE OUTSIDE REPOSITORY — recovery/history material

```text
.local/gmai-legacy-wrapper-artifacts-20260814/
.local/patches/
.local/runtime/
.local/sqlite-backups/
.local/technology-radar-v1/
```

These buckets contain potentially useful recovery/history material:

- old wrapper/coverage artifacts;
- phase 13.16.x patch snapshots and TSX copies;
- historical portal-acceptance DB/JSON runtime artifacts;
- pre-migration SQLite backups;
- a historical Technology Radar application script.

They are not canonical V12 dependencies, but they should not be silently deleted or hidden by a blanket ignore.

The local operator should move them to a dated archive **outside** the Git worktree before the next exact-head acceptance run.

## 3. Permanent boundary

```text
reproducible cache/temp
→ narrow repository ignore

recovery/history artifacts
→ preserve outside worktree

professional-review handoff scratch
→ narrow repository ignore

unknown local state
→ inspect before ignore/delete
```

Do not restore a blanket:

`/.local/`

rule in `.git/info/exclude` or repository `.gitignore`.

## 4. Why archive instead of ignore the five preservation buckets

Ignoring them in place would make the worktree appear clean while keeping potentially meaningful historical/recovery files invisible to normal Git status.

Moving them outside the repository instead preserves the files and restores clean-worktree semantics honestly.

This follows:

```text
CLEAN WORKTREE != HIDDEN UNKNOWN STATE
LOCAL ARTIFACT != CANONICAL EVIDENCE
RECOVERY MATERIAL != RUNTIME DEPENDENCY
```

## 5. Local acceptance prerequisite

Before the next exact-head run:

1. sync current V12;
2. move the five preservation buckets to a dated archive outside `D:\global-mobility-aios`;
3. leave `gmai-dev-cache`, `gmai-dev-temp` and `professional-review` in place;
4. verify those three are ignored by repository-owned rules;
5. require `git status --porcelain` to be empty;
6. run repository policy / release consistency / dependency constraints / multi-commit diff hygiene;
7. require start HEAD == end HEAD == origin V12.

## 6. Milestone boundary

This local-artifact cleanup does not:

- complete professional Austria review;
- alter reviewer findings;
- change Technology Radar adoption;
- merge R3 branches;
- seal L;
- start M or N.

The genuine independent Austria professional review remains the release-critical external gate once local/CI hygiene is green.

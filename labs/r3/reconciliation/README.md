# Technology Radar V1.3.6 — R3 Reconciliation

This directory is the control plane for the final R3 evidence campaign. It does
not merge experimental lane code into the product branch and it does not mark
any candidate adopted.

## Why this exists

The Radar now spans six physical Git branches and ten logical evidence lanes.
Every generated result contains a `git_sha`. Evidence from one implementation
head must not be silently combined with results from another head.

`execution_manifest.v2.json` therefore freezes the campaign snapshot. If a lane
branch changes after the snapshot, either execute the pinned commit in its own
worktree or deliberately create a new manifest version with the new SHA.

## Frozen physical snapshot

```text
authority         radar/r3-authority       4b04c97f911fb263471a614457b3b9f7aac8190c
security          radar/r3-security        d908a8c7ccde463ae0dec097211562e7ef8e86ca
skills            radar/r3-skills          4791546f5e23acbfc375fd8b0cb142e9f7b445a4
interoperability  radar/r3-interop-deep    9637854aeb92dba9805fd807bcd4ea4b7d99120e
infrastructure    radar/r3-infrastructure  654bfdd9816e1fb1242134ed5f6d8f6208a60b07
runtime           radar/r3-runtime         310eda0d4efe4c01c86e6ee21d9e582dd46fc90f
```

## Logical acceptance lanes

The campaign requires all ten:

```text
authority
security
skills
interoperability
observability
secrets
recovery
sandbox
memory
orchestration
```

The manifest further requires meaningful subgroups. Examples: Authority needs
OpenFGA + OPA + Cedar + SpiceDB evidence; Security needs native state-diff plus
external framework evidence; Recovery needs both logical restore/replay and
native WAL-PITR; Orchestration needs native + Temporal + LangGraph + Agno.

## Recommended worktrees

Use exact pinned commits, not moving branch tips during the campaign:

```powershell
git worktree add D:\gmai-r3-authority 4b04c97f911fb263471a614457b3b9f7aac8190c
git worktree add D:\gmai-r3-security d908a8c7ccde463ae0dec097211562e7ef8e86ca
git worktree add D:\gmai-r3-skills 4791546f5e23acbfc375fd8b0cb142e9f7b445a4
git worktree add D:\gmai-r3-interop 9637854aeb92dba9805fd807bcd4ea4b7d99120e
git worktree add D:\gmai-r3-infrastructure 654bfdd9816e1fb1242134ed5f6d8f6208a60b07
git worktree add D:\gmai-r3-runtime 310eda0d4efe4c01c86e6ee21d9e582dd46fc90f
```

Existing worktrees are fine if `git rev-parse HEAD` exactly matches the manifest.

## Evidence collection

Place or copy generated result JSON into one campaign evidence directory after
each real run. Do not edit result JSON by hand. Each result must pass the common
fingerprint verifier.

Then run:

```powershell
python -m labs.r3.reconciliation.reconcile_programme `
  --evidence-root D:\gmai-r3-evidence `
  --worktree authority=D:\gmai-r3-authority `
  --worktree security=D:\gmai-r3-security `
  --worktree skills=D:\gmai-r3-skills `
  --worktree interoperability=D:\gmai-r3-interop `
  --worktree infrastructure=D:\gmai-r3-infrastructure `
  --worktree runtime=D:\gmai-r3-runtime `
  --output D:\gmai-r3-evidence\programme-reconciliation.json
```

Exit `2` means R3 evidence is still pending, blocked, failed, invalid, or mixed
across heads. Exit `0` means the frozen campaign is **eligible for a Human Owner
R4 decision**. It does not mean production adoption.

## Grand Integration Trial

The current Grand Trial is a ten-lane gate. It explicitly attacks these
boundaries:

```text
MEMORY != VERIFIED RULE
MCP/A2A CAPABILITY != AUTHORITY
SKILL != AUTHORITY
SANDBOX AVAILABLE != EXECUTION AUTHORIZED
SANDBOX STATE != CANONICAL STATE
SECURITY FINDING != CANONICAL TRUTH
TELEMETRY != CANONICAL TRUTH
UI INTENT != AUTHORITY
SECRET OUTAGE -> FAIL CLOSED
```

Run it only after lane artifacts exist and against the pinned runtime head. The
reconciliation validator additionally requires its `git_sha` to match the frozen
runtime head and requires the Grand Trial to report ten evidence lanes.

## Decision boundary

```text
IMPLEMENTED
  != EXECUTED
  != EVIDENCE PASS
  != R4 DECISION
  != PRODUCTION ADOPTION
```

The validator never emits production authorization. Production integration,
real credentials, personal data, authority changes, legal correctness claims,
and hosted commitments remain separately governed.

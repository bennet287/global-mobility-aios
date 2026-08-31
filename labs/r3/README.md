# Technology Radar V1.3.6 R3 Labs

This tree contains isolated, synthetic experiments. Nothing here is production
architecture, canonical organization truth, authority, Evidence, Activity or an
accepted dependency merely because a lab passes.

```text
NO CANDIDATE SURVIVES ON THEORY ALONE.
NO CANDIDATE SURVIVES ON MOCKS ALONE.
NO TEST COUNT SUBSTITUTES FOR EVIDENCE DEPTH.

Aggressive on: uncertainty, adversarial testing, evidence and elimination.
Conservative on: production, credentials, personal data, authority and truth.
```

## Evidence-depth vocabulary

R3 labs use T0–T8 evidence tiers:

```text
T0 contract/mock/serialization
T1 real component correctness
T2 native feature depth
T3 stateful lifecycle
T4 adversarial/security
T5 chaos/failure/recovery
T6 concurrency/scale/property
T7 cross-component integration
T8 historical replay/restore/retirement
```

A lane is not "deep R3 verified" merely because many T0/T1 cases pass.

## Structure

```text
common/             versioned contracts, fixtures, assertions and evidence tools
authority/          OpenFGA, OPA and bounded challenger experiments
interoperability/   MCP, A2A and hostile-provider fixtures
security/           Inspect AI, Promptfoo and garak experiments
skills/             AIOS Skill Registry fixtures
observability/      OpenTelemetry experiments
secrets/            SecretsPort/OpenBao experiments
recovery/           backup, restore and PITR-style experiments
integration/        cross-lane stress scenarios
```

Every executable run must carry an `r3_run_id`, use synthetic data, emit a
machine-readable result first, and fingerprint its corpus, configuration and
results. A finding is an observation until independently reproduced and accepted.

## Common proof

```bash
python -m pytest labs/r3/common/tests -q
python -m labs.r3.common.run_common --output .test-tmp/r3-common-results.json
python -m labs.r3.common.generate_fixtures --check
```

## Deep-proof rule

Mocks validate adapters. Real components validate components. Native feature
tests validate the reason the candidate exists. Lifecycle/chaos/property tests
validate resilience. Cross-lane tests validate architecture.

Security effects must eventually come from actual before/after state
measurements. A canned `ZERO_EFFECTS` contract is T0 smoke evidence only.

## Permanent boundaries

```text
CAN DO != MAY DO
SKILL != AUTHORITY
MEMORY != EVIDENCE
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
PROVIDER OUTPUT != AUTHORITY
R3 PASS != PRODUCTION ADOPTION
```


## Programme execution

The R3 implementation surface is executed from the `radar/r3-runtime`
worktree with a worktree-aware runner. Dedicated branches remain pinned for
current-head evidence while the runtime worktree is resolved dynamically at
execution time.

List the core R4 evidence steps:

```powershell
python -m labs.r3.run_programme --list
```

Dry-run the complete core programme without executing candidates:

```powershell
python -m labs.r3.run_programme --dry-run
```

Execute a single lane:

```powershell
python -m labs.r3.run_programme --lane authority
```

Execute all core lanes and then invoke the hardened Grand Integration Trial:

```powershell
python -m labs.r3.run_programme --grand-trial
```

Include comparative candidates such as Cedar/SpiceDB, external red-team tools,
Langfuse/Phoenix, Mem0/OpenViking, Temporal/LangGraph/Agno and CopilotKit:

```powershell
python -m labs.r3.run_programme --comparative --grand-trial
```

The runner discovers Git worktrees automatically and writes evidence to
`.test-tmp/r3-programme/` by default. It never installs dependencies, injects
credentials, creates production authority, or treats a missing prerequisite as
PASS.

Optional lane-specific Python executables can be supplied through environment
variables such as:

```text
GMAI_R3_PYTHON_AUTHORITY
GMAI_R3_PYTHON_INTEROPERABILITY
GMAI_R3_PYTHON_SECURITY
GMAI_R3_PYTHON_MEMORY
GMAI_R3_PYTHON_ORCHESTRATION
GMAI_R3_PYTHON_UI
```

Execution status is intentionally three-way:

```text
PASS     = command succeeded and artifact fingerprint/head validated
BLOCKED  = prerequisite/candidate/worktree unavailable
FAIL     = execution or artifact integrity failure
```

Only the Grand Trial may produce `R4_ELIGIBLE`, and only after all eleven
runtime lanes satisfy their minimum evidence-depth requirements.

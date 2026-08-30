
# External Security Tool Shootout

This layer integrates three external security/evaluation frameworks without
allowing any of them to redefine AIOS security truth.

```text
Inspect AI / Promptfoo / garak
          ↓
framework execution evidence
          ↓
AIOS owned synthetic target
          ↓
before/after canonical-state diff
          ↓
unauthorized canonical effects
```

The owned 36-attack corpus remains the canonical comparison fixture.

## Inspect AI

`inspect_task.py` uses a real Inspect Task, Dataset, custom Solver and exact
Scorer. The solver calls the AIOS state-diff target directly and does not call
an LLM, so model credits are not required.

## Promptfoo

Promptfoo is wired through its HTTP provider to the local state-diff target.
The generated configuration contains all 36 owned attacks. Install the CLI
separately; if it is absent the result is `execution_blocked=true`.

Current upstream package baseline observed during implementation:
`promptfoo 0.122.2`.

## garak

garak uses its real REST generator against the same local target. Its native
prompt-injection/DAN probes are supplemental adversarial generation rather than
a replacement for the owned corpus.

Current upstream development baseline observed during implementation:
`garak 0.16.1.pre1`. Record the installed version in every real run.

## Run

```powershell
python -m labs.r3.security.run_external_tools `
  --run-id security-tools-20260831-001 `
  --output labs/r3/security/results/security-tools-20260831-001.json
```

Exit 2 means one or more external tools were unavailable. Exit 1 means an
executed tool exposed unauthorized canonical effects or failed its framework
run. No missing tool is converted into a synthetic PASS.

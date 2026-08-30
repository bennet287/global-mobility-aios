# AG-UI governed interaction depth

Candidate: `ag-ui-protocol==0.1.21`.

This is a real protocol-model experiment, not a CopilotKit runtime claim.

The lab exercises real AG-UI event models for:

- run start/error/finish;
- state snapshots and RFC 6902-style state deltas;
- tool-call start/arguments/results;
- human-review interrupts;
- serialization using the upstream Pydantic models.

Permanent boundary:

```text
AG-UI STATE != CANONICAL ORGANIZATION STATE
AG-UI TOOL CALL != COMMAND AUTHORIZATION
AG-UI INTERRUPT RESPONSE != HUMAN OWNER RECEIPT
```

Protected state fields such as authority, human approval, VerifiedRule, Evidence,
canonical status and canonical revision are never accepted from AG-UI state
events. Only a canonical server receipt can reconcile those fields, and stale
revisions are ignored.

Run:

```powershell
python -m pip install -r labs/r3/integration/requirements-agui.txt
python -m pytest labs/r3/integration/tests/test_agui_governance.py -q

python -m labs.r3.integration.agui_lab `
  --run-id agui-governed-20260831-001 `
  --output labs/r3/integration/results/agui-governed-20260831-001.json
```

A CopilotKit-specific runtime fixture remains a separate candidate experiment.
AG-UI protocol proof must not be reported as CopilotKit proof.

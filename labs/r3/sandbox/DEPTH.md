# Microsandbox depth R3

This second sandbox experiment closes the local state/isolation depth that the
baseline lab intentionally left open.

It exercises real Microsandbox 0.6.16 APIs:

- named-volume persistence from one microVM to another;
- read-only/noexec/nosuid/nodev remount enforcement;
- stopped-sandbox snapshot creation;
- fresh sandbox fork from the snapshot;
- preservation of `Network.none()` after snapshot restore;
- four concurrent microVMs with unique guest markers;
- synthetic secret placeholder behavior.

The credential probe deliberately uses a synthetic canary. Microsandbox's SDK
documents that raw `Secret.env(..., value=...)` values are persisted in the
sandbox config, so the lab records that fact as a **non-production pattern**.
Production credentials are prohibited. Allowed-host TLS substitution and secret
rotation remain separate depth and are not claimed here.

```powershell
python -m labs.r3.sandbox.microsandbox_depth_lab `
  --run-id sandbox-depth-20260831-001 `
  --output labs/r3/sandbox/results/sandbox-depth-20260831-001.json
```

Permanent invariant:

```text
SANDBOX AVAILABLE != EXECUTION AUTHORIZED
SANDBOX STATE != CANONICAL ORGANIZATION STATE
```

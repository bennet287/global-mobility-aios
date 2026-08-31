# R3 Sandbox Lane

Candidate: Microsandbox 0.6.16 from `superradcompany/microsandbox`, Apache-2.0.

The experiment requires local hardware virtualization. Windows support is
upstream-preview and requires WHP; Linux requires KVM; Apple Silicon uses the
upstream local runtime.

```powershell
python -m pip install -r labs/r3/sandbox/requirements.txt
python -m pytest labs/r3/sandbox/tests -q

python -m labs.r3.sandbox.microsandbox_lab `
  --run-id sandbox-microsandbox-20260830-001 `
  --output labs/r3/sandbox/results/sandbox-microsandbox-20260830-001.json
```

The base real-microVM test exercises startup identity, command execution, guest
filesystem, `Network.none()` egress denial, command timeout, metrics and
ephemeral cleanup. Named-volume, snapshot/fork, concurrency and synthetic-secret
depth is implemented separately in `microsandbox_depth_lab.py`; production
credential scoping remains outside R3.

Permanent invariant:

```text
SANDBOX AVAILABLE != EXECUTION AUTHORIZED
```


## Microsandbox depth

```powershell
python -m labs.r3.sandbox.microsandbox_depth_lab `
  --run-id sandbox-microsandbox-depth-20260831-001 `
  --output labs/r3/sandbox/results/sandbox-microsandbox-depth-20260831-001.json
```

# R3 Memory / Context Shootout

Candidates:

- AIOS-native continuity reference.
- Mem0 OSS 2.0.19 with explicit local Ollama embedding and embedded Qdrant.
- OpenViking 0.4.9 with local storage/local embedding and memory extraction
  disabled for the zero-credit vectors-only experiment.

Permanent invariant:

```text
MEMORY != EVIDENCE
RETRIEVAL != VERIFIED RULE
MEMORY CANNOT GRANT AUTHORITY
```

## Mem0

This lab does not use Mem0's default OpenAI configuration. It constructs explicit
Ollama/Qdrant configuration and uses `infer=False` so CRUD proof requires no LLM
fact-extraction call.

```powershell
python -m pip install -r labs/r3/memory/requirements-mem0.txt
ollama pull nomic-embed-text

python -m labs.r3.memory.mem0_lab `
  --run-id memory-mem0-20260830-001 `
  --output labs/r3/memory/results/memory-mem0-20260830-001.json
```

If Ollama or the embedding model is absent the artifact is
`execution_blocked=true` and the command exits 2.

## OpenViking

OpenViking's full server depends on MCP <2 while the separate interop lane pins
MCP 2.1.1. Run the OpenViking server in a separate virtual environment.

```powershell
python -m venv .venv-openviking
.\.venv-openviking\Scripts\Activate.ps1
python -m pip install openviking==0.4.9
$env:OPENVIKING_CONFIG_FILE="labs/r3/memory/openviking-r3.json"
openviking-server --config labs/r3/memory/openviking-r3.json
```

In the main lab environment install only the lightweight client:

```powershell
python -m pip install openviking-sdk>=0.1.9

python -m labs.r3.memory.openviking_lab `
  --run-id memory-openviking-20260830-001 `
  --output labs/r3/memory/results/memory-openviking-20260830-001.json
```

The zero-credit experiment uses local embedding, vectors-only resource ingestion,
Viking URI inspection and session context. VLM memory extraction, trajectory
inspection, multi-tenant authenticated isolation and snapshots remain deeper
experiments. OpenViking remains AGPL-3.0 and cannot advance to adoption without
license review.

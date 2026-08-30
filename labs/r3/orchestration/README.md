
# R3 Durable Orchestration Shootout

Candidates:

- AIOS-native semantic reference
- Temporal Python 1.32.0
- LangGraph 1.2.11
- Agno 3.0.2

The common synthetic lifecycle is:

```text
case open
→ request documents
→ source version changes
→ human-review gate
→ resume
→ guarded completion
```

Framework state is never canonical organization truth.

Temporal uses the real SDK test server and a real Worker. Worker #1 is stopped
while the workflow waits for Human Owner approval; Worker #2 then resumes the
same workflow. The synthetic activity fails its first attempt to exercise retry.
If the Temporal test server cannot start, the artifact is
`execution_blocked=true` rather than a simulated PASS.

LangGraph uses a real StateGraph, InMemorySaver checkpointing and
`interrupt` / `Command(resume=...)`. Agno uses real callable Steps,
InMemoryDb and native HITL confirmation without model calls.

```powershell
python -m labs.r3.orchestration.native_lab --run-id orchestration-native-20260831-001 --output labs/r3/orchestration/results/orchestration-native-20260831-001.json

python -m pip install -r labs/r3/orchestration/requirements-temporal.txt
python -m labs.r3.orchestration.temporal_lab --run-id orchestration-temporal-20260831-001 --output labs/r3/orchestration/results/orchestration-temporal-20260831-001.json

python -m pip install -r labs/r3/orchestration/requirements-langgraph.txt
python -m labs.r3.orchestration.langgraph_lab --run-id orchestration-langgraph-20260831-001 --output labs/r3/orchestration/results/orchestration-langgraph-20260831-001.json

python -m pip install -r labs/r3/orchestration/requirements-agno.txt
python -m labs.r3.orchestration.agno_lab --run-id orchestration-agno-20260831-001 --output labs/r3/orchestration/results/orchestration-agno-20260831-001.json
```

Later execution depth includes persistent LangGraph/Agno stores, Temporal
versioning/cancellation chaos, concurrency and operational-cost measurement.

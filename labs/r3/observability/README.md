# R3 Observability Lane

OpenTelemetry is tested as diagnostic infrastructure, never canonical truth.

Pin:

```text
opentelemetry-sdk==1.44.0
```

Run:

```powershell
python -m pip install -r labs/r3/observability/requirements.txt
python -m pytest labs/r3/observability/tests -q

python -m labs.r3.observability.otel_lab `
  --run-id otel-lab-20260830-001 `
  --output labs/r3/observability/results/otel-lab-20260830-001.json

python -m labs.r3.common.verify_results labs/r3/observability/results/*.json
```

This tranche proves trace hierarchy/correlation, synthetic sensitive-attribute
redaction, exporter-failure independence and the permanent telemetry/truth
boundary. Real OTLP Collector transport/restart/chaos is implemented in
`collector_lab.py`; sampling economics and sustained volume/cost remain future depth.


## Secondary observability candidates

After the OpenTelemetry baseline, V1.3.6 can compare local self-hosted Langfuse
and Phoenix without granting either canonical truth.

Current pins:

```text
langfuse==4.15.1
arize-phoenix==20.4.0
```

The experiment refuses cloud endpoints. If a local service is absent it emits
`execution_blocked=true` instead of falling back to a hosted service.

```powershell
python -m pip install -r labs/r3/observability/requirements-secondary.txt

python -m labs.r3.observability.secondary_candidates `
  --candidate langfuse `
  --run-id observability-langfuse-20260831-001 `
  --output labs/r3/observability/results/observability-langfuse-20260831-001.json

python -m labs.r3.observability.secondary_candidates `
  --candidate phoenix `
  --run-id observability-phoenix-20260831-001 `
  --output labs/r3/observability/results/observability-phoenix-20260831-001.json
```

Langfuse must prove trace ingestion/readback and a non-model numeric boundary
score. Phoenix must prove OTLP/HTTP ingestion and queryable spans. Both must keep
the synthetic secret canary out of exported data and neither may change the
canonical DENY result.

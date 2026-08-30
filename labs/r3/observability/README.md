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
boundary. OTLP Collector transport, sampling, restart and volume/cost remain
explicit later depth.

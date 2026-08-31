# R3 Secrets Lane

Real candidate: OpenBao 2.6.2, disposable dev mode, synthetic secrets only.

```powershell
docker compose -f labs/r3/infrastructure-compose.yml up -d openbao

python -m pytest labs/r3/secrets/tests -q

python -m labs.r3.secrets.openbao_lab `
  --run-id secrets-openbao-20260830-001 `
  --output labs/r3/secrets/results/secrets-openbao-20260830-001.json

python -m labs.r3.common.verify_results labs/r3/secrets/results/*.json
```

The lab proves real KV v2 versioning, a read-only ACL policy, bounded child-token
TTL, denied writes, rotation, historical version reads, token revocation, audit
device enablement and fail-closed service outage.

The `OpenBaoSecretsPort` has no plaintext/config fallback. Persistent restart and
audit-depth proof is implemented separately in `persistent_openbao_lab.py`.
Dynamic database credentials remain future depth. Dev mode is never production
evidence.


## Persistent OpenBao depth

```powershell
python -m labs.r3.secrets.persistent_openbao_lab `
  --run-id secrets-openbao-persistent-20260831-001 `
  --output labs/r3/secrets/results/secrets-openbao-persistent-20260831-001.json
```

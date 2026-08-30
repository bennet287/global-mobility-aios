# Persistent OpenBao R3 depth

This is separate from the disposable dev-mode ACL lab.

The lab starts a non-dev OpenBao 2.6.2 container with filesystem storage on a
fresh Docker named volume. It performs real init/unseal, writes a synthetic KV
secret, enables a persistent file audit device, restarts the container, unseals
with the original recovery material and proves the KV data remains readable.

It also inspects the real audit file and requires:

- the synthetic secret path is present;
- the synthetic secret value is not plaintext;
- the root token is not plaintext;
- audit data persists/grows across restart.

Root/unseal material exists only in process memory and is never written to the
result artifact.

```powershell
python -m labs.r3.secrets.persistent_openbao_lab `
  --run-id openbao-persist-20260831-001 `
  --output labs/r3/secrets/results/openbao-persist-20260831-001.json
```

Dynamic database credentials, HA failover and TLS remain separate depth.
This lab uses only synthetic local secrets and deletes its container and volume
after execution.

# AIOS V2 — Phase 22 External Network Verifier Owner Audit

**Programme:** Phase 22 — Production Operations & Scale
**Dependency consumer:** GRSI.E code/configuration canary evidence
**Audit date:** 2026-10-04
**Exact audited integration head:** `3cc666f250adfbb84d954ae271d07581e090e613`
**Current migration head:** `0100_phase22_release_networking_contract`
**Nature of this slice:** read-only owner/trust-boundary audit. No live scan, rollback, deployment mutation, secret creation, receipt creation, authority change or migration.

---

## 1. Question

The prepared Phase 22 deployment run now binds an immutable networking expectation:

- public web hostname;
- public API hostname;
- one expected globally routable IPv4 address;
- public TCP allowlist limited to 80/443 with optional 22;
- one pinned external-verifier public-key fingerprint.

The remaining question is:

> **What execution boundary should independently observe the public network, where should its Ed25519 signing key live, and which facts can it prove without trusting the target VPS?**

The answer from this audit is:

> **Use a GitHub-hosted workflow as the bounded v1 off-host network verifier only from a verifier ref that is actually protected, with an Ed25519 private key held only in a GitHub Environment secret.**

The current active repository ruleset named `Production proof enforcement` applies only to `refs/heads/main`; it does **not** currently protect `design/aios-v2-complete-redesign`. Therefore the real verifier signing key must not be provisioned to the integration branch as it exists today. Before operational use, either protect the integration/verifier ref or place the trusted verifier workflow on a separately protected ref.

This boundary is independent from the target VPS trust boundary, but it is not a separate administrative trust domain from repository governance. If stronger multi-party or multi-vantage attestation is later required, a separate verifier service/HSM can replace or supplement it.

---

## 2. Existing owners remain authoritative

Do not create a second deployment or networking evidence store.

Reuse:

```text
ProductionDeploymentAcceptanceRun
  → ProductionDeploymentAcceptanceCheckReceipt
```

The prepared run already owns:

- exact release commit/configuration identity;
- rollback release/configuration identity;
- exact canary environment identity;
- networking contract key/version/fingerprint/body;
- pinned external-verifier public-key fingerprint;
- candidate-bound WorkItem and admission Decision.

The target-host foundation executor already owns local host/release observation and can write only fail-closed receipts.

The external verifier must therefore produce portable evidence that is later consumed by the existing Phase 22 owner.

---

## 3. Target-host foundation evidence is intentionally insufficient

The current target-host executor can independently derive:

- deterministic host fingerprint;
- running API/web/worker/beat container image IDs;
- exact release revision label;
- exact release-configuration label.

It cannot independently prove what an unrelated public client can reach through:

- provider firewall/security group;
- NAT/public routing;
- public DNS;
- public certificate/TLS path;
- externally exposed TCP ports.

The networking audit correctly prohibited target-host-only `release_networking=satisfied`.

**Finding:** the external verifier must remain off-host.

---

## 4. GitHub-hosted verifier v1 is the smallest justified off-host boundary

The repository already trusts GitHub Actions for repository policy, CodeQL and V12 CI, but none of those workflows is a live-network verifier.

A new verifier workflow is justified only if it is structurally separated from candidate-controlled execution.

For v1:

- runner: GitHub-hosted `ubuntu-latest`;
- trigger: manual/protected workflow invocation, not `pull_request`;
- workflow definition: executed only from the protected integration branch;
- permissions: minimum read-only repository permissions;
- no deployment credential;
- no VPS SSH credential;
- no database credential;
- no AIOS runtime secret;
- no candidate checkout;
- no execution of scripts from the candidate commit;
- one environment-protected Ed25519 private-key secret;
- output: signed canonical observation manifest plus unsigned human-readable summary.

**Finding:** GitHub Actions is acceptable as an off-host public-network observation boundary only under those restrictions.

### Current repository protection state

Repository ruleset inspection at this audited head found one active branch ruleset:

```text
Production proof enforcement
  include = refs/heads/main
```

It currently enforces deletion/non-fast-forward protection and required production-proof status checks on `main` only.

It does **not** include:

```text
refs/heads/design/aios-v2-complete-redesign
```

This is an operational blocker for provisioning the real verifier signing key to the integration branch.

The verifier implementation may be developed and tested with ephemeral test keys before that repository setting is corrected, but operational signing must remain disabled.

---

## 5. The verifier workflow must never execute from the candidate ref

A code/configuration candidate is exactly what is being tested.

If the verifier checks out or executes verifier code from the candidate commit, the candidate could alter:

- DNS comparison;
- port-scan interpretation;
- TLS validation;
- signature payload;
- success criteria.

That destroys verifier independence.

Permanent rule:

```text
candidate release SHA
!= verifier workflow/script SHA
```

The verifier workflow and verifier implementation must come from a trusted protected integration revision.

The candidate identity is input/evidence only.

---

## 6. GitHub Environment secret is the v1 signing-key authority

The Ed25519 private key must not exist on the target VPS.

Recommended v1 key boundary:

- generate the key outside the VPS;
- store only the private key in a dedicated GitHub Environment secret;
- do not create/provision that operational secret until the selected verifier ref is actually protected;
- restrict that Environment to the protected verifier ref and required human approval where available;
- never expose the private key through workflow output, artifact, logs, cache, repository files or target-host files;
- derive the raw public key and SHA-256 public-key fingerprint inside the verifier;
- include the public key and fingerprint in the signed manifest;
- require the manifest fingerprint to equal the fingerprint already pinned in the prepared networking contract.

The public key is not secret. The private key is.

---

## 7. Key rotation is run-bound, not in-place receipt mutation

A prepared deployment run pins one verifier public-key fingerprint.

Therefore key rotation should be:

1. provision a new verifier private key in the protected GitHub Environment;
2. derive its public-key fingerprint;
3. prepare a **new** deployment acceptance run whose networking contract pins the new fingerprint;
4. use the new key only for manifests bound to that new run;
5. retain old public keys only as needed to verify immutable historical evidence.

Do not mutate an already-prepared run to point at a new verifier key.

---

## 8. Signed manifest identity

The verifier should sign canonical UTF-8 JSON bytes directly with Ed25519.

Recommended v1 manifest identity:

```text
contract_key     = phase22.external-network-verifier
contract_version = 1
```

The signed payload should bind at least:

- deployment run UUID;
- networking-contract fingerprint;
- web hostname;
- API hostname;
- expected public IPv4;
- allowed public TCP ports;
- observation start/completion timestamps;
- verifier contract key/version;
- trusted verifier workflow revision;
- GitHub Actions run ID and attempt;
- DNS observations;
- external TCP observations;
- HTTP redirect observations;
- HTTPS/TLS observations;
- final per-probe statuses;
- overall verifier status.

The signature envelope should carry:

- Ed25519 public key;
- public-key SHA-256 fingerprint;
- Ed25519 signature;
- canonical manifest SHA-256 digest.

---

## 9. Anti-replay requirements

A valid signature alone is insufficient.

Target-host import/aggregation must also require:

- exact deployment run UUID match;
- exact networking-contract fingerprint match;
- exact web/API hostnames match;
- exact expected public IPv4 match;
- exact allowed public TCP set match;
- public-key fingerprint match against the prepared run;
- observation completion after the deployment run was prepared;
- bounded freshness at import time;
- no future-dated observation outside a small clock-skew allowance.

Because deployment-run IDs are unique and receipts are immutable per run/gate, a signed manifest from another run must never satisfy the current run.

---

## 10. Facts the off-host verifier can independently derive

The verifier can truthfully observe without trusting target-host claims:

### DNS

For both prepared hostnames:

- public A-record answers;
- whether the expected IPv4 is the exact permitted answer set for v1;
- DNS resolution failure.

The verifier should not accept an operator-submitted `dns_ok=true`.

### Public TCP exposure

Against the prepared public IPv4:

- externally reachable TCP ports;
- whether the observed reachable set equals the prepared allowlist.

For the v1 single-IPv4 contract, the strongest claim requires an external scan covering TCP 1–65535.

A bounded subset scan can prove specific ports, but cannot truthfully prove that no unexpected TCP port is reachable.

### HTTP redirect behavior

Using the expected public IPv4 plus the prepared Host header:

- TCP/80 reachability when 80 is allowed;
- redirect status;
- redirect target;
- whether redirect leads to the prepared HTTPS hostname.

### HTTPS/TLS

For both prepared hostnames, connecting to the prepared IPv4 while validating SNI/hostname:

- TLS handshake success;
- public trust-chain validation;
- hostname/SAN validation;
- certificate fingerprint;
- certificate validity period;
- HTTPS response status;
- API health-path reachability where the contract specifies it.

Connecting by the prepared IP while validating the prepared hostname avoids treating an unverified second DNS resolution as the trust anchor.

---

## 11. Facts the off-host verifier cannot independently derive

The verifier must not claim:

- machine ID / target-environment fingerprint truth;
- running Docker image labels;
- exact API/web/worker/beat release identity;
- local loopback-only bindings;
- migration revision;
- worker/beat internal health;
- database or Redis state;
- secret rotation/revocation;
- backup/restore state;
- actual restart behavior;
- actual rollback execution;
- post-rollback schema/data compatibility;
- candidate re-restoration after rollback.

Those remain target-host/deployment-owner facts.

---

## 12. External verifier cannot itself write a satisfied Phase 22 receipt

The portable verifier manifest is one evidence class.

A truthful `release_networking=satisfied` receipt still requires the deployment owner to reconcile:

1. prepared run/networking contract;
2. target-host release identity;
3. target-host networking/configuration observations;
4. signed external verifier manifest;
5. startup/restart evidence;
6. actual rollback drill to the prepared rollback release;
7. post-rollback health/compatibility;
8. restoration/revalidation of the candidate release when required by the drill.

The external verifier must not call the AIOS receipt writer directly.

**Finding:** no public receipt-write endpoint is justified.

---

## 13. Portable transfer may be untrusted because the manifest is signed

The signed manifest may be transferred through a channel that is not itself authoritative, for example a GitHub Actions artifact downloaded by an operator.

The later target-host executor must establish authenticity from:

- canonical payload bytes;
- Ed25519 signature;
- supplied public key;
- SHA-256 fingerprint of that public key;
- prepared-run pinned verifier fingerprint.

Therefore an operator copying the manifest cannot alter its evidence without invalidating the signature.

The workflow artifact is transport, not authority.

---

## 14. GitHub-hosted verifier limitations

GitHub-hosted v1 has useful operational independence from the VPS, but its limitations must remain explicit:

- GitHub controls the runner;
- the repository/org controls the workflow;
- it is normally one external vantage, not global multi-vantage monitoring;
- runner public source addresses are ephemeral;
- it is not hardware-backed remote attestation;
- it does not prove cloud-provider firewall configuration directly; it proves observed external reachability;
- repository administrators capable of changing the protected verifier workflow or Environment secret remain in the verifier administrative trust domain.

These limitations do not invalidate the external networking observation. They bound the claim.

---

## 15. Why a separate always-on verifier service is not justified for v1

The current requirement is one bounded canary acceptance observation, not continuous global network monitoring.

A new always-on verifier service would introduce:

- another deployment;
- another secrets runtime;
- another uptime/patching boundary;
- another credential lifecycle;
- another cost/operations surface;
- another production acceptance problem.

The repository does not yet need that complexity.

**Finding:** start with a protected ephemeral GitHub-hosted verifier. Introduce a dedicated verifier service only if later requirements need multi-vantage, scheduled monitoring, stronger administrative separation or hardware-backed keys.

---

## 16. Existing receipt table can remain the durable Phase 22 owner

A new verifier-evidence database table is not justified by this audit.

The stronger target-host `release_networking` executor can store bounded verifier provenance inside the existing immutable receipt semantics, including:

- verifier contract key/version;
- pinned verifier key fingerprint;
- manifest digest;
- signature verification result;
- workflow revision/run identity;
- bounded redacted external observations.

The receipt's existing record fingerprint already covers its evidence digest/reference and redacted details.

If implementation discovers that the signed manifest itself must be retained verbatim beyond the receipt's bounded evidence payload, that should be justified separately rather than automatically adding a generic attestation store.

---

## 17. Cryptographic implementation boundary

The API already depends on `cryptography>=42.0`.

Therefore Ed25519 verification does not require a new cryptographic dependency.

The target-host verifier-import path should use the existing Python cryptography library to:

1. decode a bounded public key/signature envelope;
2. derive SHA-256 over the raw public key;
3. compare that fingerprint to the prepared networking contract;
4. canonicalize the manifest under the verifier contract;
5. verify the Ed25519 signature;
6. verify manifest/run/networking identity and freshness;
7. return a typed verified observation object.

No private verifier key belongs in the API runtime.

---

## 18. Workflow security contract

A future verifier workflow should fail closed unless all of these hold:

- invoked from the protected integration/verifier ref;
- verifier Environment secret is available only on that ref;
- workflow has no write permission to repository contents;
- workflow receives no target-host/VPS credentials;
- workflow receives no AIOS database credentials;
- workflow receives no production application secrets;
- candidate commit is never checked out or executed;
- observation inputs are bounded to the prepared networking contract;
- manifest is signed only after all probes finish;
- failed/partial probes produce a signed failed/blocked manifest, not an absent artifact;
- private-key material is never included in logs or artifacts.

---

## 19. Recommended next implementation order

After this audit is sealed:

0. **Verifier-ref protection prerequisite**
   - protect the selected verifier ref (integration, `main`, or a dedicated verifier branch);
   - restrict the GitHub Environment to that ref;
   - keep the real Ed25519 private key unprovisioned until this is true.

1. **External verifier manifest contract + validator**
   - typed/canonical v1 manifest;
   - Ed25519 envelope verification;
   - exact run/networking identity checks;
   - freshness/replay guards;
   - no receipt write.

2. **Protected GitHub-hosted verifier workflow**
   - off-host DNS/TCP/HTTP/TLS probes;
   - protected Environment signing key;
   - signed manifest artifact;
   - no candidate checkout;
   - no target-host credentials.

3. **Target-host release/networking executor v2**
   - verify exact local release/networking state;
   - import and verify signed external manifest;
   - execute restart/rollback/restoration drill;
   - create one immutable `release_networking` receipt through the existing Phase 22 owner;
   - only this stronger executor may have a path to `satisfied`.

4. Prepare a **fresh** deployment acceptance run and execute the complete contract on the real target host.

---

## 20. Migration decision

This audit does **not** advance the migration head.

The external verifier contract/validator can initially remain code-only.

The existing Phase 22 run/receipt tables are sufficient for the next bounded implementation unless concrete retention semantics prove otherwise.

Current migration head remains:

```text
0100_phase22_release_networking_contract
```

---

## 21. GRSI.E consequence

GRSI.E remains fail-closed.

A signed external network manifest is necessary evidence for a satisfied networking gate, but it is not sufficient for canary qualification.

GRSI.E must continue to require the existing Phase 22 projection and all six acceptance gates satisfied for the exact candidate-bound deployment run.

---

## 22. Audit conclusion

**Chosen v1 verifier boundary:**

> GitHub-hosted off-host verifier workflow from an actually protected verifier ref.

**Current repository blocker:**

> the active ruleset protects `main` only; the current integration branch is not yet protected for operational verifier-key use.

**Private-key boundary:**

> Ed25519 private key in a protected GitHub Environment secret only; never on the VPS or in repository content.

**Independent observations:**

> public DNS, public TCP exposure, HTTP redirect behavior, HTTPS/TLS identity/reachability.

**Still target-host owned:**

> exact running release, restart, rollback, migration/data compatibility and restoration.

**Durable owner:**

> existing Phase 22 deployment run/receipt; no new generic verifier store.

This audit does not claim a satisfied networking receipt, a live canary, production deployment or production readiness.

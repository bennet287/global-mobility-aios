# AIOS V2 — Phase 22 Release / Networking Acceptance Owner Audit

**Programme:** Phase 22 — Production Operations & Scale
**Dependency consumer:** GRSI.E code/configuration canary evidence
**Audit date:** 2026-10-04
**Exact audited integration head:** `f28fe088dee468f389ad2bf51f95d73a76b7f86c`
**Current migration head:** `0099_grsi_canary_dependency_policy`
**Nature of this slice:** read-only owner/gap audit. No deployment, network scan, restart, rollback, target-host mutation, receipt creation, authority change or migration.

---

## 1. Question

PR #291 established the first real Phase 22 target-host evidence writer.

The foundation executor can now:

- derive the prepared target-host fingerprint;
- verify that API, web, worker and beat are running the exact prepared release/configuration identity;
- write immutable receipts through the existing Phase 22 owner;
- fail closed without exposing a public receipt-write endpoint.

Foundation v1 deliberately cannot write a `satisfied` gate.

The next roadmap question is:

> **Can the existing Phase 22 owner now support a truthful satisfied `release_networking` receipt without creating another deployment subsystem?**

Answer:

> **The receipt owner is sufficient, but the prepared deployment run is missing one immutable networking expectation contract and no independent external-network verifier exists.**

A target-host-only probe must therefore remain unable to satisfy `release_networking`.

---

## 2. Existing canonical owner remains correct

Do not create a second release/networking result store.

The canonical durable owner is already:

```text
ProductionDeploymentAcceptanceRun
  → ProductionDeploymentAcceptanceCheckReceipt
```

The versioned acceptance gate is already:

```text
gate_key     = release_networking
gate_version = 1
label        = Release and networking
```

The existing receipt can already preserve:

- exact deployment-run identity;
- observed target-environment fingerprint;
- observed release commit/configuration identity;
- executor contract identity;
- evidence digest/reference;
- bounded redacted observed details;
- immutable status and observation time.

**Finding:** no new receipt table or generic networking-evidence store is justified.

---

## 3. Existing target-host facts that can be reused

The current production topology already gives real executable seams.

### Release identity

`scripts/production_release_identity.py` derives:

- exact clean-checkout Git commit SHA;
- deterministic release-configuration fingerprint;
- image labels for the release contract.

The production application images carry:

```text
org.opencontainers.image.revision
com.global-mobility-aios.release-configuration-fingerprint
com.global-mobility-aios.release-identity-contract
```

PR #291 independently verifies those labels on the running API, web, worker and beat containers.

### Runtime topology

`docker-compose.prod.yml` defines:

- API diagnostic port bound to loopback;
- web diagnostic port bound to loopback;
- PostgreSQL with no published host port;
- Caddy ingress publishing TCP 80/443;
- API/web health checks;
- restart policy;
- migration-before-application startup ordering.

### HTTPS ingress

`infrastructure/deployment/Caddyfile` owns the intended web/API HTTPS reverse-proxy topology.

### Rollback identity

The prepared Phase 22 run already binds:

- exact candidate release SHA/configuration fingerprint;
- exact rollback release SHA/configuration fingerprint.

These are necessary inputs to a real rollback drill.

**Finding:** reuse all of these. Do not invent a parallel release identity, network topology or rollback owner.

---

## 4. Host identity is not network identity

The target-host fingerprint introduced by PR #291 is intentionally bounded to:

- machine ID;
- hostname;
- operating-system identity;
- machine architecture.

It does **not** bind:

- public web hostname;
- public API hostname;
- expected public address;
- intended externally reachable port set;
- DNS answer set;
- certificate/TLS identity;
- external-verifier trust identity.

That is correct for a host identity contract, but insufficient for a satisfied networking claim.

**Finding:** do not overload the host fingerprint with mutable networking policy.

---

## 5. Release-configuration fingerprint does not bind production environment values

The release-configuration fingerprint hashes tracked deployment/build inputs such as:

- production Compose;
- API/web Dockerfiles;
- dependency/build metadata;
- Caddy configuration.

It intentionally does not hash the secret-bearing/local `.env.production` contents.

Therefore the same code/configuration release fingerprint may be deployed with different:

- `WEB_DOMAIN`;
- `API_DOMAIN`;
- host/public address;
- firewall policy;
- external port exposure.

A satisfied `release_networking` receipt cannot infer those expectations from the release fingerprint.

**Finding:** the networking expectation must be separately and immutably bound to the prepared deployment run.

---

## 6. Missing durable networking expectation

Repository/model search found no canonical owner for:

- web/API public hostname;
- expected public address;
- intended public transport/port allowlist;
- independent external-network verifier identity.

The smallest correct addition is not a new owner. It is a **versioned networking expectation contract bound to the existing Phase 22 deployment run**.

Recommended semantic identity:

```text
networking_contract_key
networking_contract_version
networking_contract_fingerprint
networking_contract_json
```

The run record fingerprint and preparation Activity must include that exact contract.

---

## 7. Recommended first networking contract scope

Keep the first contract deliberately narrow for the current single-VPS Compose topology.

A v1 contract should explicitly bind at least:

```text
web_hostname
api_hostname
expected_public_address_set
allowed_public_transport_ports
external_verifier_key_fingerprint
```

The contract must define what “intended externally reachable” means instead of assuming it.

Examples of transport entries:

```text
tcp/22   # only if SSH is intentionally public
tcp/80
tcp/443
```

Do not silently infer SSH or any other administrative exposure.

If IPv6 or UDP exposure is present but the selected verifier cannot prove it, the networking gate remains blocked/unsupported rather than declaring success from IPv4/TCP evidence alone.

---

## 8. Public hostname rules must fail closed

For the first production/canary contract:

- web and API hostnames must be explicit;
- reserved example/local names are invalid;
- embedded schemes/credentials/paths are not hostnames;
- web and API hostnames must be compatible with the deployed Caddy/environment contract;
- the external verifier must observe DNS against the prepared expected address set.

A later multi-host/CDN architecture may require a broader contract. Do not build that abstraction now.

---

## 9. Target-host observation cannot prove external firewall exposure

A process running on the VPS can truthfully inspect:

- Docker port bindings;
- local listeners;
- container health;
- Caddy configuration;
- configured domains;
- candidate image identity;
- local restart behavior;
- rollback/restore behavior;
- HTTPS from the host.

It cannot independently prove:

> **what an unrelated public client can actually reach through the provider firewall/security-group/NAT path.**

Repository search found no existing:

- external port-scanner workflow;
- cloud-firewall verifier;
- repo-owned external networking probe;
- durable external-network attestation owner.

**Finding:** host-local listener/Compose inspection alone must never emit `release_networking=satisfied`.

---

## 10. GitHub Actions is not already an accepted external-network verifier

Existing workflows own:

- repository policy;
- CodeQL;
- V12 repository proof;
- browser/UI proof.

There is no deployment/network workflow that probes the live canary from an independent runner.

Adding such a workflow would be a new verifier contract, not “reuse of V12”.

Permanent rule:

```text
V12 green
!= target-host public networking proven
```

---

## 11. Required evidence split

A truthful satisfied `release_networking` gate needs at least two independent evidence classes.

### A. Target-host executor evidence

Bound to the exact prepared run:

- exact host fingerprint;
- exact candidate release/configuration identity;
- exact configured web/API networking identity;
- expected Docker/public-vs-loopback exposure;
- API/web health;
- HTTPS/TLS against the intended origins;
- startup/restart behavior;
- actual rollback drill to the exact prepared rollback release;
- post-rollback compatibility/health;
- restoration of the candidate release where the drill contract requires it.

### B. External-network verifier evidence

Observed from outside the target host:

- prepared web/API hostname DNS;
- expected public address set;
- HTTPS/TLS reachability from an external vantage;
- externally reachable transport/port set compared with the prepared allowlist;
- observation timestamp;
- verifier contract/version;
- verifier identity/provenance.

The final Phase 22 receipt may aggregate those observations, but neither evidence class substitutes for the other.

---

## 12. Caller-supplied network booleans remain prohibited

Do not add inputs such as:

```text
https_ok = true
firewall_ok = true
rollback_ok = true
ports_ok = true
```

and treat them as evidence.

A human/operator may initiate a probe and define the intended networking contract.

The executor/verifier must independently derive observed results.

---

## 13. External verifier provenance requires a trust root

If an external verifier produces a portable attestation, the target host must be able to establish that the attestation came from the verifier selected by the prepared run.

A bounded v1 may use an asymmetric signing contract, for example:

- external verifier holds an Ed25519 private key that is not present on the target VPS;
- prepared networking contract pins the trusted public-key fingerprint;
- verifier signs a canonical observation manifest;
- target-host executor validates the signature and exact contract/run identities before the receipt service can accept the evidence;
- receipt stores the verifier key fingerprint, manifest digest and bounded redacted observation data.

Do not trust an arbitrary public key bundled with the manifest unless its fingerprint was already pinned by the prepared run.

This audit does not choose key provisioning/rotation mechanics; they remain a separate security detail of the verifier implementation.

---

## 14. Rollback must be executed, not merely available

The prepared run already identifies a rollback release.

A satisfied release/networking gate must not reduce rollback evidence to:

- rollback image tag exists;
- old commit is known;
- rollback command is documented.

A real bounded canary rollback drill must actually:

1. start from the exact prepared candidate release;
2. switch the canary application stack to the exact prepared rollback release;
3. observe migration/data compatibility behavior;
4. prove required health/network behavior after rollback;
5. record failure if the rollback release cannot safely run against the resulting schema/state;
6. restore the candidate release when the drill contract requires continued canary observation;
7. re-prove candidate identity/health after restoration.

The existing migration-before-application Compose ordering is part of this proof. Do not bypass it merely to make rollback appear successful.

---

## 15. Foundation receipts remain immutable

PR #291 intentionally creates one immutable receipt per run/gate.

A foundation run that already recorded:

```text
release_networking = blocked
```

must not be upgraded in place.

Satisfied-capable release/networking evidence must use a fresh prepared deployment run whose gate receipt is produced once from the stronger executor contract.

---

## 16. No new deployment authority

A satisfied networking receipt would mean:

> the versioned release/networking acceptance contract was observed as satisfied for this exact prepared run.

It would not mean:

- deploy to production;
- admit real client data;
- promote the GRSI candidate;
- enable paid autonomous execution;
- grant credentials/tools;
- expand resource or external-action authority.

Existing WorkItem/Decision/policy owners remain authoritative.

---

## 17. Durable-state decision

A new independent durable owner is **not** justified.

However, the existing `ProductionDeploymentAcceptanceRun` lacks networking expectations that must be fixed before a satisfied release/networking receipt can be machine-verifiable.

Therefore the next durable Phase 22 change is justified as an extension of the existing run contract.

If implemented, it should receive the next migration after:

```text
0099_grsi_canary_dependency_policy
```

The migration should add only the networking-contract identity/payload needed by the existing deployment run.

---

## 18. Recommended next bounded implementation

**Phase 22 — prepared release/networking contract binding.**

Implement only:

1. versioned networking-contract key/version;
2. canonical networking-contract JSON;
3. canonical networking-contract fingerprint;
4. exact inclusion in deployment-run fingerprint and preparation Activity;
5. strict validation for the current single-VPS contract;
6. read projection;
7. migration/schema parity and integrity tests.

Do **not** yet:

- write a satisfied networking receipt;
- perform an external network scan;
- execute rollback;
- create a new deployment owner;
- create a public receipt endpoint;
- create a generic cloud/network abstraction.

After the contract binding is sealed:

```text
external verifier contract
  → target-host release/networking executor
  → actual rollback drill
  → fresh run
  → satisfied release_networking receipt
```

Only then proceed to the remaining five acceptance gates.

---

## 19. GRSI.E consequence

GRSI.E remains open.

The code/configuration canary projection must stay false until:

- current qualified shadow evidence;
- current exact canary Decision;
- current satisfied canary dependency policy;
- exact Phase 22 candidate binding;
- all six Phase 22 target-host gates satisfied.

The networking-contract gap is a Phase 22 prerequisite, not a reason to relax GRSI.E.

---

## 20. Audit conclusion

**Reuse:**

- existing Phase 22 deployment run/receipt;
- PR #291 bounded target-host executor pattern;
- exact release/configuration labels;
- production Compose/Caddy topology;
- existing health checks;
- prepared rollback release identity;
- WorkItem/Decision authority lineage.

**Missing but justified connective state:**

> one immutable networking expectation contract on the existing deployment run.

**Missing execution proof after that state exists:**

> an independent external-network verifier plus a target-host restart/rollback executor.

**Current status:**

> `release_networking` must remain fail-closed and cannot truthfully be marked satisfied yet.

This audit does not claim a live canary, production deployment or production readiness.

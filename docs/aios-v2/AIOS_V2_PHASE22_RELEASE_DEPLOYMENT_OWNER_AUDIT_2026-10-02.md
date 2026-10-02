# AIOS V2 — Phase 22 Release / Deployment Owner Audit

**Programme:** Phase 22 — Production Operations & Scale
**Dependency consumer:** GRSI.E code/configuration canary evidence
**Audit date:** 2026-10-02
**Exact audited integration head:** `f9a2bd44141e82096d1eaa00e86e560a88432449`
**Current migration head:** `0097_grsi_admission_dependency_policy`
**Nature of this slice:** read-only duplicate/gap audit. No deployment, target-host mutation, release activation, rollback execution, authority grant or migration.

---

## 1. Question

The sealed GRSI.E code-canary audit established that GRSI must not become a deployment subsystem.

The next question is therefore a Phase 22 ownership question:

> **Which existing canonical production-operations owner can prove one exact application release was deployed to one exact environment/host, accepted through the target-host contract, and rolled back or retained with reconstructable evidence?**

This audit finds:

> **No canonical release/deployment attempt and acceptance-receipt owner exists yet.**

The repository has deployment topology, runbooks, health probes, release-preparation checks and CI evidence. Those are necessary inputs, but none is durable target-host deployment truth.

---

## 2. Phase 22 owns this problem

The roadmap defines Phase 22 as:

- deployment architecture;
- justified PostgreSQL/Redis/worker scaling;
- backup/restore;
- disaster recovery;
- secrets lifecycle;
- observability/alerting;
- load testing;
- privacy/retention;
- tenancy/isolation;
- release/rollback;
- runbooks;
- cost controls.

The missing release/deployment receipt therefore belongs to Phase 22 production operations.

GRSI.E is only a downstream consumer when a candidate caused the release attempt.

---

## 3. Existing production topology owner

The current deployable topology is owned by:

- `docker-compose.prod.yml`;
- `infrastructure/deployment/README.md`;
- `docs/DOCKER_PRODUCTION_PROFILE_V3_3.md`;
- the production Dockerfiles/build targets;
- Caddy ingress configuration;
- Alembic migrations;
- PostgreSQL/Redis/worker/beat/API/web service contracts.

This is real deployment configuration.

It is not a record that a target host actually deployed a specific release.

---

## 4. Application release identity is not canonical today

The production Compose profile builds application services from local source contexts:

```yaml
api-migrate:
  build:
    context: ./apps/api

api:
  build:
    context: ./apps/api

web:
  build:
    context: ./apps/web
    target: production

worker:
  build:
    context: ./apps/api

beat:
  build:
    context: ./apps/api
```

The resolved Compose model does not canonically bind those services to:

- one release ID;
- one exact Git commit;
- one immutable OCI digest set;
- one deployment attempt;
- one target environment;
- one target host;
- one rollback predecessor.

A local source tree can be built, but the system cannot later prove from canonical application state which exact artifact was running on a host.

---

## 5. Infrastructure image tags are not application release identity

The production profile references versioned infrastructure images such as:

- `postgres:16-alpine`;
- `redis:7-alpine`;
- `caddy:2.11.4-alpine`.

Those are infrastructure dependencies.

They do not identify the API/web/worker/beat application release.

Even an application image tag would not be enough by itself; target-host proof should record immutable digest identity.

---

## 6. Current release scripts are repository/package readiness checks

Existing scripts such as:

- `scripts/check_release_consistency.py`;
- `scripts/check_github_release_ready.py`;
- release archive/bundle helpers;

verify repository/package consistency.

They can prove things such as:

- one Alembic head;
- roadmap migration-head consistency;
- required docs/tags/archive entries;
- clean release packaging state.

They do not:

- select a deployment target;
- deploy an application image;
- observe a target-host image digest;
- run target-host acceptance;
- record rollback.

**Finding:** release-preparation state is not deployed-release truth.

---

## 7. Current GitHub Actions workflows are CI/proof workflows

The repository currently has workflows for:

- Repository Policy Check;
- CodeQL;
- V12 Production Proof;
- Living HQ browser proof;
- Mobility browser proofs;
- Operator V2 browser proof.

There is no canonical deployment workflow that:

- chooses an environment/host;
- deploys an immutable release;
- records target-host identity;
- records application image digests;
- records the migration revision on the target;
- executes the production acceptance runbook;
- records rollback target/result.

**Finding:** GitHub Actions currently owns CI evidence, not production deployment truth.

---

## 8. V12 remains engineering evidence

The repository explicitly distinguishes V12 from real production acceptance.

V12 can prove:

- exact-head repository behavior;
- isolated SQLite/PostgreSQL migration contracts;
- backend regressions;
- frontend production build/smoke;
- browser proof in the CI environment.

It cannot prove:

- intended VPS deployment;
- live DNS/TLS/firewall state;
- real target-host runtime-secret behavior;
- live object storage;
- real recovery;
- exact deployed image identity;
- live rollback.

**Permanent rule:**

```text
V12 green
!= release deployed
!= target host accepted
!= rollback proven
!= production ready
```

---

## 9. Health checks are components of acceptance, not release truth

The production profile has useful runtime probes:

- PostgreSQL readiness;
- API `/health`;
- web health;
- Compose dependency ordering.

Those prove liveness/readiness at a point in time.

They do not prove:

- release identity;
- candidate identity;
- environment identity;
- migration identity;
- auth/session boundaries;
- ingress/TLS behavior;
- end-to-end workflow correctness;
- persistence/recovery;
- rollback.

A future acceptance receipt should consume these probes, not replace them.

---

## 10. The deployment runbook is the acceptance specification

`infrastructure/deployment/README.md` is already the strongest source for **what must be proven on a real target**.

It requires evidence across:

- release/networking;
- identity/boundaries;
- core product journey;
- documents/integrations;
- failure/recovery;
- operations.

It explicitly states that production is not yet verified on a production host.

That runbook should remain the acceptance specification.

A new durable owner should record execution/results against that specification rather than copying the specification into a GRSI schema.

---

## 11. Manual procedures are not machine-verifiable receipts

The repository documents real commands for:

- Compose configuration validation;
- build/start;
- migrations;
- health checks;
- log inspection;
- stop/restart;
- backup/recovery-related procedures;
- secrets/credential rotations.

Those procedures are valuable.

But a procedure document does not answer:

- who ran the deployment;
- on which host;
- for which release;
- which image digests were observed;
- which migration revision was present;
- which checks passed;
- which checks failed;
- what rollback target was selected;
- whether rollback was exercised.

**Finding:** procedural correctness is not execution evidence.

---

## 12. Existing rollback evidence is domain-specific

The repository contains bounded rollback/recovery procedures for specific operational domains, including:

- database credential rotation;
- encryption-key migration;
- backup/restore;
- document-storage recovery.

Those remain canonical for their own concerns.

There is no general application-release owner that records:

```text
release A
  → deployed to environment E / host H
  → acceptance contract C
  → accepted or rejected
  → rollback target B
  → rollback executed / not required / failed
```

**Finding:** do not reinterpret maintenance rollback procedures as application-release rollback truth.

---

## 13. Existing organization records do not own deployed-release truth

The GRSI.E canary audit already established the relevant boundaries:

- WorkItem = orchestration identity;
- ExecutiveDecision = admission authority;
- OrganizationActivity = semantic/audit event edge;
- OrganizationalActionOutput = action/output state;
- OrganizationRecordReference = evidence linkage;
- GRSI candidate = improvement artifact lineage.

None owns the full target-host release/deployment receipt.

Phase 22 should create the missing production-operations truth once, then all programmes consume it.

---

## 14. Confirmed canonical-owner gap

The repository has no current model/service with the semantic identity:

```text
tenant
environment
deployment attempt
exact release artifact
target host
acceptance execution
rollback identity/result
```

Repository search also finds no canonical fields such as:

- `deployment_id`;
- `release_commit_sha`;
- `deployment_attempt`;
- `rollback_target`;
- application `image_digest` deployment truth.

**Conclusion:** one bounded Phase 22 deployment acceptance owner is justified.

---

## 15. Recommended owner: deployment acceptance run/receipt

The smallest useful owner is a **deployment acceptance run** representing one immutable deployment attempt.

It should own execution identity and observed acceptance state, not release policy.

Recommended semantic identity:

```text
tenant
deployment_run_key
environment_key
execution_mode
release_commit_sha
release_configuration_fingerprint
```

Initial execution modes should stay narrow:

- `canary`;
- later `production_acceptance`.

Do not add Kubernetes, multi-region, percentage traffic, blue/green or fleet abstractions until a real deployment architecture requires them.

---

## 16. Release identity requirements

A deployment run should bind the exact release through machine-verifiable identity such as:

- Git commit SHA;
- application image digests;
- resolved deployment configuration fingerprint;
- migration revision;
- candidate ID/fingerprint when a GRSI candidate caused the release;
- WorkItem when an organizational operation caused the release.

A human label such as “latest”, “candidate”, or a mutable image tag is insufficient.

---

## 17. Environment/host identity requirements

The receipt should identify the target without exposing secrets.

Useful bounded identity may include:

- environment key;
- environment class;
- host/provider resource identity or a stable redacted fingerprint;
- deployment endpoint/origin fingerprints where appropriate;
- Compose/project identity;
- region/location metadata where operationally necessary;
- environment-constraint version.

Do not store private keys, passwords, access tokens or raw secret values.

---

## 18. Acceptance checks must be explicit, versioned and evidentiary

The deployment run should execute a versioned acceptance contract.

Each check needs at minimum:

- check key/version;
- started/completed timestamps;
- status;
- evidence digest/reference;
- redacted observed details;
- failure/blocked reason.

Representative checks should be derived from the existing deployment runbook, including:

- deployed release/image identity;
- migration revision;
- API/web health;
- ingress/TLS;
- authentication/session/role denial;
- synthetic core journey;
- worker/beat behavior;
- persistence across restart;
- storage/document path where enabled;
- backup/recovery evidence where required;
- observability/incident readiness;
- relevant provider/resource posture.

The exact v1 list belongs to the Phase 22 implementation slice.

---

## 19. Caller-supplied pass booleans are prohibited

The owner must not accept:

```text
deployment_ok = true
health_ok = true
rollback_ok = true
production_ready = true
```

as sufficient evidence.

Status must derive from executed checks and observed target-host evidence.

An operator may initiate the run; the system must independently record what it observed.

---

## 20. Rollback belongs to the same deployment owner

Rollback is part of release/deployment lifecycle, not GRSI candidate status.

A deployment run should bind:

- rollback target release identity;
- rollback availability/preparation;
- rollback command/executor identity;
- rollback start/end;
- post-rollback migration/data compatibility checks;
- post-rollback health/acceptance result.

A candidate may be rejected independently of whether rollback was technically required.

---

## 21. Authority remains separate

A deployment receipt is evidence that deployment occurred.

It is not the authorization source.

Existing authority owners remain responsible for:

- deployment admission;
- environment scope;
- consequential external-action limits;
- secrets/tool access;
- resource/spend authorization.

Phase 22 must not infer authority from a successful deployment.

---

## 22. Canary environment constraints

The first canary environment must be explicit and bounded.

For example, the environment contract may declare:

```text
environment_class = canary
real_client_data_allowed = false
external_consequential_actions_allowed = false
paid_autonomous_execution_allowed = false
```

Those constraints describe the environment.

They do not grant the candidate additional permissions.

---

## 23. No traffic-splitting assumption

The current single-stack Compose architecture has no canonical traffic-splitting or deployment-slot owner.

The first canary foundation must therefore not assume:

- percentage traffic;
- Kubernetes;
- service mesh;
- multi-region rollout;
- automatic weighted routing.

A valid initial canary may be a separately addressed synthetic-only stack if the Phase 22 implementation proves isolation.

---

## 24. OrganizationActivity should remain the semantic event edge

A material deployment/rollback should emit canonical OrganizationActivity events tied to the deployment run.

Activity should record semantic facts such as:

- deployment started;
- deployment reached running state;
- acceptance completed;
- rollback started/completed.

Activity should not be the only deployment state; otherwise exact current truth depends on “latest event” interpretation.

Use dedicated durable state plus Activity, following existing policy-owner patterns.

---

## 25. WorkItem and Decision remain reusable orchestration/authority owners

When a deployment is initiated through organizational work:

- WorkItem identifies the bounded operation;
- ExecutiveDecision/HumanAction supplies required authorization;
- deployment acceptance run owns execution evidence;
- Activity/Audit own semantic/audit lineage.

Do not create a second work scheduler or second decision system inside Phase 22.

---

## 26. GRSI.E consumption after Phase 22 exists

Once the deployment owner exists, GRSI.E should remain read-only.

Expected chain:

```text
candidate
  → exact canary WorkItem
  → authorized Decision
  → current GRSI.D review
  → current GRSI admission dependency policy
  → exact Phase 22 deployment acceptance run
  → canary evidence projection
```

GRSI.E should answer whether the exact candidate ran and whether the bounded canary contract passed.

It should not duplicate deployment checks.

---

## 27. Production-readiness consumption beyond GRSI

The same Phase 22 owner is also needed for ordinary whole-product production validation.

It should support future evidence that:

- an intended VPS actually runs the release;
- the deployed release is exact and dated;
- live acceptance ran;
- recovery/rollback is proven;
- deployment evidence remains queryable after the session.

That is why this owner belongs to production operations rather than recursive improvement.

---

## 28. Current live-host limitation

The canonical deployment runbook still records that the required production-host proof has not been executed from the current workspace.

Current repository truth does not establish:

- a deployed production VPS;
- live DNS/TLS acceptance;
- final target firewall evidence;
- live release image digests;
- live object-storage/recovery acceptance;
- a completed application rollback drill.

Therefore a future implementation may define the owner/executor contract, but it must not prepopulate a passed production or canary receipt.

---

## 29. Durable-state decision

A deployment acceptance run is genuine durable production-operations state.

No existing table has the required semantics.

If implemented in the application database, the foundation should receive the next migration after:

```text
0097_grsi_admission_dependency_policy
```

The migration belongs to Phase 22, not GRSI.

This audit itself does not advance the migration head.

---

## 30. Recommended next bounded implementation

**Phase 22 — deployment acceptance foundation v1.**

Keep the first implementation deliberately narrow:

1. one durable deployment-run identity;
2. exact release commit/configuration identity;
3. bounded canary environment contract;
4. versioned acceptance-check receipt records or a structurally equivalent immutable receipt contract;
5. rollback target/status fields;
6. Human/operator initiation with existing authority lineage;
7. OrganizationActivity + AuditLog emission;
8. read-only projection;
9. no deployment automation yet;
10. no “passed” state from caller-supplied booleans.

After that foundation is sealed:

- add a target-host executor that actually gathers evidence;
- execute it on the intended host;
- add GRSI.E read-only candidate binding;
- only then consider GRSI.F promotion semantics.

---

## 31. What not to build

Do not add:

- a generic GRSI canary executor;
- a second WorkItem system;
- a second approval/decision system;
- a Kubernetes abstraction without Kubernetes;
- percentage-traffic semantics without a traffic owner;
- a generic external-evidence blob store;
- mutable “current release” text without immutable receipt lineage;
- target-host secrets in the database;
- optimistic production-ready flags.

---

## 32. Audit conclusion

**Existing owners to reuse:**

- Docker production profile for topology;
- deployment runbook for acceptance specification;
- Git commit/image identity for release identity;
- WorkItem for orchestration;
- ExecutiveDecision/HumanAction for authority;
- Activity/Audit for semantic/audit lineage;
- existing health, backup/recovery and operational checks.

**Missing canonical owner:**

> one Phase 22 deployment acceptance run/receipt that binds exact release, exact environment/host, executed acceptance evidence and rollback lineage.

**GRSI.E consequence:**

> code/configuration canary remains blocked until Phase 22 provides that owner and real target-host evidence exists.

This audit does not claim live production readiness and does not seal GRSI.E.

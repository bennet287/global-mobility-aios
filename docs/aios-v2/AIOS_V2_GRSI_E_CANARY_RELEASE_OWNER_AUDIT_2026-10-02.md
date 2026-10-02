# AIOS V2 — GRSI.E Code Canary / Release Owner Audit

**Programme:** Governed Recursive Self-Improvement (GRSI)  
**Slice:** GRSI.E code/configuration canary owner audit  
**Audit date:** 2026-10-02  
**Exact audited integration head:** `71ca0cfd5485dd930cd328d721e536b50e420bbe`  
**Current migration head:** `0097_grsi_admission_dependency_policy`  
**Nature of this slice:** read-only owner/gap audit. No deployment, candidate activation, canary execution, production mutation, authority change, migration or target-host claim.

---

## 1. Question

GRSI.E requires **Shadow and Canary Evidence**.

The code/configuration shadow path is now bounded and machine-verifiable from existing owners:

```text
candidate lineage
  → independent evaluation
  → current GRSI.D review
  → exact GRSI.E WorkItem
  → current authorized Decision
  → current Board dependency policy
  → exact-head CI / dependency resolvers
  → bounded non-active shadow qualification
```

The remaining question is:

> **Which canonical owner can prove that an exact code/configuration candidate was actually admitted into a bounded target-host canary, under existing authority, with exact release identity, health/acceptance evidence and a real rollback path?**

This audit finds that **no such canonical runtime owner exists yet**.

That is a production-operations gap. It must not be filled by pretending that CI, Docker Compose configuration, a deployment document or a GRSI row is live canary truth.

---

## 2. Permanent boundary

The roadmap states:

```text
shadow with no canonical/external mutation
  → bounded canary inside existing authority ceiling
  → evidence review
  → governed promotion OR rejection
  → monitoring
  → rollback/demotion
```

It also prohibits a candidate from silently altering production or bypassing the existing release/deployment boundary.

Therefore:

> **GRSI may qualify and bind canary evidence. It must not become the deployment system of record.**

Release/deployment/rollback belong to the owning production runtime and Phase 22 production-operations boundary.

GRSI.E should consume those receipts later.

---

## 3. Existing production topology owner

The canonical Docker production-profile owner is:

```text
docs/DOCKER_PRODUCTION_PROFILE_V3_3.md
docker-compose.prod.yml
```

The production profile defines:

- PostgreSQL 16;
- a one-shot Alembic migration gate;
- Redis;
- FastAPI API;
- Next.js production web;
- Caddy ingress;
- Celery worker and beat;
- health checks;
- bounded runtime-secret mount;
- production startup dependencies;
- loopback diagnostic ports and public ingress ports.

This is real deployability configuration.

It is **not** evidence that any target host is currently running a specific candidate.

---

## 4. Compose does not currently bind application runtime identity to an immutable candidate artifact

The application services use local build contexts:

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

There is no current canonical field that binds those built images to:

- one exact GRSI candidate ID;
- one candidate fingerprint;
- one Git commit SHA;
- immutable OCI image digests;
- one release identity;
- one target host;
- one deployment attempt.

A human procedure can record those values externally, but GRSI cannot infer them from Compose configuration.

**Finding:** production Compose is the runtime topology owner, not a durable deployed-release identity owner.

---

## 5. Base images are not sufficient application release identity

The production profile references infrastructure images such as:

- `postgres:16-alpine`;
- `redis:7-alpine`;
- `caddy:2.11.4-alpine`.

Even where a tag is versioned, a tag is not the application candidate identity.

The API/web/worker/beat application images are built from source instead of selected by an immutable application image digest.

**Finding:** repository image/build configuration cannot establish that a target host is running the exact candidate artifact.

---

## 6. Existing health checks prove liveness, not candidate identity or canary acceptance

The production profile has real service health checks, including:

- PostgreSQL readiness;
- API `/health`;
- web HTTP health.

These checks are valuable runtime evidence.

They do not prove:

- exact release/candidate identity;
- migration identity;
- ingress/DNS/TLS correctness;
- browser authentication boundaries;
- core synthetic workflow completion;
- document storage behavior;
- failure/recovery behavior;
- rollback viability;
- canary-specific traffic or isolation.

**Finding:** health status is one future canary receipt component, not canary truth by itself.

---

## 7. The deployment runbook explicitly says production is unverified

`infrastructure/deployment/README.md` currently states:

> **Status: NOT YET VERIFIED ON A PRODUCTION HOST.**

It explicitly distinguishes V12 CI from target-host production evidence.

The required live-host gates include:

1. release and networking;
2. identity and boundaries;
3. core journey;
4. documents and integrations;
5. failure and recovery;
6. operations.

The runbook requires exact deployed commit/image identity, HTTPS, intended ports, startup/restart/rollback, real browser/auth behavior, durable state across restart, recovery drills, storage proof and dated host evidence.

It also records that no production VPS/configuration/Docker engine is available in the current execution workspace.

**Finding:** repository CI cannot truthfully satisfy the missing code canary.

---

## 8. Existing deployment procedures are procedural evidence, not durable deployment truth

The Docker production-profile document contains real procedures that require operators to:

- record deployed commit and image identities;
- take/verify backups;
- stop/restart services;
- test application/database connectivity;
- exercise synthetic journeys;
- preserve rollback material;
- capture redacted command exit states and host evidence.

These procedures are useful and should be reused.

However, the repository has no canonical durable object that records a completed application deployment attempt and its evidence lineage.

A Markdown statement or operator note cannot become a machine-verifiable GRSI canary receipt merely because it describes the correct procedure.

---

## 9. Existing rollback procedures do not constitute a general application-release rollback owner

The production profile documents bounded rollback/recovery behavior for specific maintenance operations, including:

- PostgreSQL credential rotation;
- connector encryption-key migration;
- database backup/restore;
- document-storage recovery contracts.

Those owners should remain canonical for their domains.

There is no current general application-release state that says:

```text
release X deployed to host H
  → canary admitted
  → acceptance evidence E
  → rollback target Y
  → rollback executed / available / proven
```

**Finding:** do not reinterpret domain-specific maintenance rollback procedures as candidate release rollback truth.

---

## 10. No deployment workflow currently owns target-host execution

The current GitHub workflows are repository/CI/browser proof workflows.

There is no canonical production deployment workflow that:

- selects a target host;
- deploys an immutable release artifact;
- records exact target-host identity;
- records application image digests;
- applies migrations under a release identity;
- runs target-host acceptance gates;
- records rollback target and rollback result.

**Finding:** GitHub Actions currently owns CI execution, not production canary execution.

---

## 11. No traffic-splitting or parallel candidate runtime exists

The production Compose profile represents one application stack.

This audit found no existing code/configuration runtime owner for:

- percentage traffic splitting;
- candidate-vs-active parallel API/web stack;
- request cohort pinning;
- isolated canary hostname;
- deployment slot identity;
- automatic canary rollback;
- candidate-specific live metrics.

That does not mean a future canary must use percentage traffic.

For the initial single-VPS architecture, a valid bounded canary could instead be an isolated synthetic-only release slot or separately addressed canary stack **if** the production owner explicitly supports it and proves isolation.

**Finding:** do not hard-code Kubernetes-style or percentage-traffic canary semantics into GRSI.

---

## 12. Canary admission must not grant new authority

Any future code canary must remain inside already-authorized production authority.

Candidate admission must not itself:

- create credentials;
- expose new ports;
- enable a paid provider;
- increase call/spend allocations;
- loosen auth/CORS/session boundaries;
- weaken secret policy;
- admit real client data;
- enable consequential automation;
- expand external-action authority.

A canary deployment receipt is evidence that an authorized deployment happened.

It is not the authorization source.

---

## 13. Canary evidence must be exact-candidate evidence

A valid GRSI.E code canary projection eventually needs an exact chain similar to:

```text
GRSI candidate id + fingerprint
  → immutable release artifact identity
  → target environment / host identity
  → authorized deployment attempt
  → deployed release/image digests
  → migration result
  → target-host acceptance receipts
  → canary-specific observation window
  → rollback target / recovery evidence
```

If any identity edge is ambiguous, candidate canary evidence is not proven.

---

## 14. The missing owner is broader than GRSI

The missing durable truth is not “a GRSI canary table”.

The project needs a canonical **production release/deployment evidence owner** for ordinary production operations even if recursive improvement did not exist.

That owner belongs with Phase 22 production operations and should represent releases/deployments independently of who proposed the code.

GRSI.E can later bind a candidate to a release/deployment receipt using exact artifact identity.

**Finding:** do not create candidate-specific deployment truth inside `organization_improvement_*` merely to complete GRSI.E.

---

## 15. Minimal Phase 22 owner semantics that GRSI will eventually need

A future production-release/deployment owner should be designed from Phase 22 requirements, but GRSI needs at least these semantics to consume it safely:

```text
release identity
source commit / artifact identity
application image digests
deployment environment / target identity
deployment attempt identity
deployment status
migration identity/result
health/acceptance evidence references
rollback target
rollback availability/result
operator / authorized decision lineage
timestamps
```

The owner should distinguish at minimum:

- prepared;
- deployed;
- accepted;
- rejected/failed;
- rolled_back;

without allowing a status string alone to fabricate evidence.

Exact status vocabulary must come from the Phase 22 design, not this GRSI audit.

---

## 16. Target-host acceptance must remain an evidence projection

The deployment runbook already defines the live acceptance categories.

Do not duplicate those test results into a generic GRSI evidence warehouse.

A future canary projection should consume canonical release/deployment evidence such as:

- image/build digest receipts;
- Alembic/release identity;
- ingress/TLS checks;
- API/web health;
- synthetic end-to-end journey;
- authorization/denial behavior;
- storage preflight and document journey where applicable;
- restart/persistence checks;
- backup/recovery receipts;
- incident/rollback evidence;
- observed cost/resource posture where applicable.

The source systems remain authoritative.

---

## 17. No canary qualification from V12

Permanent rule for code/configuration candidates:

```text
V12 green
!= target-host deployed
!= canary admitted
!= live-host accepted
!= rollback proven
!= production promotion
```

V12 remains a prerequisite engineering signal.

The current GRSI.E shadow projection correctly consumes CI only as shadow evidence.

Do not extend it to return `canary_qualified=true` from the same workflows.

---

## 18. Current GRSI.E status

### Shadow

**Implemented and evidence-capable for code/configuration.**

The current projection can return bounded shadow qualification only when:

- the candidate/proposal lineage is valid/current;
- GRSI.D review is complete;
- the exact WorkItem Decision is approved;
- a current Board dependency policy exists;
- every required dependency resolver is satisfied;
- exact-head repository CI is complete.

This remains authority-neutral.

### Canary

**Blocked — no canonical target-host release/deployment evidence owner exists yet.**

The blocker is architectural/operational, not a missing boolean.

No code change inside the shadow service can truthfully remove it.

---

## 19. Required next dependency

Before implementing code/configuration canary evidence, establish the minimal Phase 22 release/deployment evidence boundary.

The sequence should be:

```text
Phase 22 release/deployment owner audit
  → minimal exact-release identity / deployment-attempt contract
  → target-host acceptance evidence projection
  → rollback identity/evidence
  → real deployment on intended VPS
  → dated synthetic acceptance proof
  → GRSI.E candidate-to-release binding/projection
```

Do not reverse this order.

---

## 20. Migration boundary

This audit adds no migration.

A future GRSI canary slice should also avoid new durable state if Phase 22 provides the needed release/deployment identity.

If Phase 22 proves that a new deployment owner is genuinely missing, that owner receives durable state under its own production-operations boundary, not as a GRSI workaround.

The current migration head remains:

```text
0097_grsi_admission_dependency_policy
```

---

## 21. GRSI.E cannot be sealed yet

GRSI.E code/configuration shadow is materially implemented.

GRSI.E code/configuration canary is not.

Therefore:

> **GRSI.E remains open.**

The next justified work is the Phase 22 release/deployment owner audit and foundation needed by canary evidence.

This audit must not be interpreted as approval to deploy the current integration branch or to admit production/client traffic.

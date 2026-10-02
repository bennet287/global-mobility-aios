# AIOS V2 — GRSI.E Code/Configuration Canary Owner Audit

**Programme:** Governed Recursive Self-Improvement (GRSI)
**Slice:** GRSI.E code/configuration canary owner audit
**Audit date:** 2026-10-02
**Exact audited integration head:** `71ca0cfd5485dd930cd328d721e536b50e420bbe`
**Current migration head:** `0097_grsi_admission_dependency_policy`
**Nature of this slice:** read-only duplicate/gap audit. No deployment, canary execution, target-host mutation, authority grant or migration.

---

## 1. Question

The GRSI roadmap allows bounded shadow and canary evidence only when the real target artifact has a safe execution seam.

The sealed code/configuration shadow path now proves an exact candidate commit through repository CI, current GRSI.D review, an exact WorkItem Decision and Board-authored dependency policy. That is still repository shadow evidence.

The next question is:

> **What canonical owner can prove that an exact code/configuration candidate was deployed into a bounded canary environment, exercised through real runtime dependencies, observed, and rolled back without silently converting that execution into production promotion?**

The answer from this audit is:

> **No canonical deployment/canary receipt owner exists yet.**

The repository does have a real deployment contract and real organization-governance owners. Those should be connected, not duplicated.

---

## 2. The real code/configuration execution seam is deployment, not an AI agent executor

For a code/configuration candidate, the artifact is an exact Git commit and the real effect boundary is the deployed application stack.

The current production profile is owned by:

- `docker-compose.prod.yml`;
- `infrastructure/deployment/README.md`;
- `docs/DOCKER_PRODUCTION_PROFILE_V3_3.md`;
- the API/web/worker/beat/ingress container contracts;
- Alembic migrations;
- the actual target host and configured external dependencies.

The deployment acceptance runbook already requires evidence tied to:

- exact deployed commit;
- image/build identities;
- migration state;
- target host;
- HTTPS/ingress behavior;
- authentication and role denial;
- real web → API → PostgreSQL → worker/beat → web journey;
- restart behavior;
- backup/restore and recovery;
- real document/provider integrations where enabled;
- operational health, logs, metrics, incidents and costs;
- rollback.

This is the correct execution seam for a code/configuration canary.

**Finding:** do not create a generic GRSI canary executor that bypasses deployment ownership.

---

## 3. V12 remains shadow/repository evidence, not canary deployment evidence

`V12 Production Proof` verifies repository code, isolated database contracts, container builds and browser journeys.

The canonical deployment runbook explicitly states that V12:

- does not deploy the complete product to a VPS;
- may use fixture API responses;
- must not be described as proof that AIOS is operating in production.

Therefore the sealed GRSI.E shadow path is correct to treat V12 as exact-head repository evidence only.

**Finding:** V12 cannot become a code canary receipt merely because the candidate commit passes it.

---

## 4. OrganizationalWorkItem is the correct orchestration identity, not the deployment receipt

`OrganizationalWorkItem` already supports:

- tenant;
- work type and phase;
- source object type/id/version;
- risk level;
- authority level;
- assigned canonical position;
- parent/child work lineage;
- idempotency.

A future code-canary operation should therefore be represented by an exact candidate-bound WorkItem such as:

```text
work_type = grsi_code_canary
phase_key = GRSI.E
source_object_type = organization_improvement_candidate
source_object_id = <candidate id>
source_object_version = <candidate fingerprint>
```

That WorkItem is orchestration identity only.

It does not prove:

- what image was deployed;
- where it was deployed;
- that the host actually ran it;
- what migrations were applied;
- what probes were executed;
- what external dependencies were live;
- whether rollback occurred;
- whether the target recovered.

**Finding:** reuse WorkItem, but do not overload it with deployment truth.

---

## 5. ExecutiveDecision remains the admission authority owner

Existing `ExecutiveDecision` can bind to:

- exact WorkItem;
- exact candidate source object/version;
- authority level;
- supersession;
- approved/rejected state.

That is the correct owner for an authorized decision to admit a bounded canary WorkItem.

The decision still cannot prove that deployment or rollback happened.

**Finding:** reuse Decision for canary admission. A deployment receipt must never imply its own authorization.

---

## 6. OrganizationalActionOutput is not authoritative deployment evidence

`OrganizationalActionOutput` already carries:

- WorkItem;
- accountable position;
- authority basis;
- evidence JSON;
- impact JSON;
- rollback posture;
- output JSON;
- completion status.

This is useful preparation/output state, but the repository's organization semantics deliberately distinguish action output from verified authoritative outcome.

It also lacks the exact durable deployment identity and integrity contract needed here:

- target environment identity;
- host identity/fingerprint;
- candidate commit;
- image digest set;
- deployment configuration fingerprint;
- migration head observed on the target;
- probe/acceptance receipts;
- rollback target and rollback receipt;
- start/end timestamps for the deployment observation window;
- live dependency declarations.

**Finding:** do not treat an ActionOutput with `rollback_posture` as proof that a canary was deployed or rolled back.

---

## 7. OrganizationActivity is the correct semantic event edge, but not sufficient state alone

A real deployment/canary transition should emit durable `OrganizationActivity` events because it is material operational evidence.

Activity can bind:

- tenant;
- WorkItem;
- actor/position/authority;
- exact source object and source version;
- causation;
- supersession;
- immutable canonical payload fingerprint.

But Activity is an event ledger. It is not by itself a good canonical current deployment receipt because exact reconciliation would otherwise depend on interpreting arbitrary payloads and “latest event” semantics.

Existing policy foundations use dedicated immutable state plus Activity. The same principle should apply here.

**Finding:** a deployment receipt should emit/reconcile to Activity, but Activity alone should not be the only deployment truth.

---

## 8. OrganizationRecordReference cannot currently own a deployment receipt

`OrganizationRecordReference` links canonical organization owners to a bounded allowlist of target types.

Its current target-type allowlist contains domain and governance records such as:

- official sources;
- audit logs;
- automation events;
- external validation;
- organization control;
- capability-autonomy policies.

It has no deployment/release acceptance target type.

Even if extended, a reference is still a link, not the authoritative deployment receipt.

**Finding:** reference linkage may be useful after a deployment receipt exists, but it is not the missing owner.

---

## 9. ExternalValidationRun is a different product concern

`ExternalValidationRun` and its reviews/findings/evidence are designed for external human/product validation scenarios.

They are not infrastructure deployment acceptance and do not bind:

- exact deployed commit;
- image digests;
- target-host identity;
- migration state;
- Compose/release configuration;
- rollback.

**Finding:** do not reuse product external-validation state for infrastructure canary evidence.

---

## 10. Existing release scripts are packaging/static gates

The repository contains scripts such as:

- `check_release_consistency.py`;
- `check_github_release_ready.py`;
- `check_demo_release.py`;
- MVP release bundle/archive helpers.

Those prove repository/package properties.

They do not establish a live deployed target.

**Finding:** do not infer canary execution from release-ready/package-ready status.

---

## 11. The deployment runbook is the canonical acceptance specification

`infrastructure/deployment/README.md` already owns the whole-product production acceptance requirements and explicitly keeps missing target-host evidence unverified.

That specification should remain the source of truth for **what a deployment receipt must prove**.

The GRSI programme should consume a deployment-owned receipt that implements that contract for a bounded canary scope.

GRSI must not copy the runbook requirements into a second GRSI-specific acceptance schema and allow them to drift.

---

## 12. Confirmed gap

A real connective infrastructure gap remains:

> **There is no canonical, immutable deployment acceptance receipt that binds one exact release/candidate to one exact environment and records what target-host checks actually ran and what rollback occurred.**

This gap is broader than GRSI. It also blocks the project's standing requirement for whole-product real-world production validation.

Therefore the missing owner should belong to **deployment/release acceptance**, not GRSI.

---

## 13. Recommended canonical owner boundary

The smallest justified durable owner is a bounded **deployment acceptance run/receipt**.

It should not be a generic orchestrator.

Recommended semantic identity:

```text
tenant
environment_key
deployment_run_key
release_commit_sha
release_configuration_fingerprint
execution_mode
```

For the first scope, execution mode may support:

- `canary`;
- later `production_acceptance`.

Do not add blue/green, Kubernetes or multi-region concepts before a real owner needs them.

A run should bind immutable observed identity such as:

- exact Git commit SHA;
- exact candidate ID/fingerprint when GRSI-caused;
- exact WorkItem ID;
- target environment key;
- target-host evidence identity/fingerprint without exposing secrets;
- image digest(s);
- resolved deployment/configuration fingerprint;
- migration revision observed after deployment;
- acceptance contract version;
- start/end timestamps;
- terminal status.

---

## 14. Evidence must come from an execution boundary, not caller booleans

The receipt must not accept:

```text
health_ok = true
rollback_ok = true
production_ready = true
```

from a caller as sufficient proof.

Instead, the deployment executor or target-host acceptance command must emit machine-verifiable evidence for explicit checks.

Examples:

- service/container image digest observation;
- migration revision query;
- HTTP(S) health response receipt;
- auth/session/role-denial probe result;
- synthetic web/API/database journey receipt;
- worker/beat execution receipt;
- backup/restore receipt;
- external dependency probe receipts where enabled;
- rollback command/target identity and post-rollback health receipt.

Each check should retain:

- check key/version;
- status;
- started/completed time;
- evidence digest/reference;
- redacted details;
- failure reason.

---

## 15. Canary must not equal production promotion

A successful deployment canary receipt means only:

> the exact candidate/release was exercised inside the bounded environment contract and its required acceptance checks passed.

It does not mean:

- active version changed;
- candidate was promoted;
- production traffic was permanently shifted;
- autonomy increased;
- credentials/tools were granted;
- monetary authority increased;
- external action became authorized.

GRSI.F must still own promotion/rejection/rollback decision semantics.

---

## 16. Canary environment must be explicit and bounded

The first code/configuration canary must not silently deploy onto an unspecified “production” target.

The environment identity must explicitly state its scope, for example:

```text
environment_class = canary
real_client_data_allowed = false
external_consequential_actions_allowed = false
paid_autonomous_execution_allowed = false
```

These are environment constraints, not candidate permissions.

The current production runbook already requires real client data and consequential paid capabilities to remain disabled until their independent gates pass.

---

## 17. Rollback belongs to the deployment artifact owner

GRSI should request/observe rollback, but the actual rollback must be implemented through the same deployment/release owner that performed the canary.

For the current Docker Compose deployment target, rollback ultimately means restoring a known release/image/configuration state and proving post-rollback health/data compatibility.

Do not model rollback as merely changing GRSI candidate status.

Candidate lineage and deployment state are distinct.

---

## 18. Candidate-bound GRSI projection after a receipt exists

Once deployment owns a canonical receipt, GRSI.E can remain read-only and project:

```text
candidate
  → exact canary WorkItem
  → approved admission Decision
  → current GRSI.D review
  → current GRSI admission dependency policy
  → deployment acceptance receipt for exact candidate commit/environment
  → canary evidence status
```

GRSI.E should not duplicate the receipt contents.

It should answer:

- did the exact candidate run?
- under which environment contract?
- are all required checks satisfied?
- did rollback complete where required?
- is the receipt current for this exact candidate/configuration?
- what remains failed/pending/unknown?

---

## 19. No automatic live deployment can be implemented from this workspace today

The current canonical deployment runbook states:

- no production VPS is available in the execution workspace;
- no production configuration/live Docker target exists here;
- live DNS/TLS/host firewall evidence is absent;
- real object-store and recovery evidence remain incomplete;
- target-host secret rotation/revocation evidence remains incomplete.

Therefore no implementation in this repository session can truthfully produce a **passed live canary receipt**.

Repository code can define the owner and executor contract, but live evidence remains absent until the intended target host exists and the acceptance command is executed there.

---

## 20. Recommended next bounded programme slice

The next implementation should be treated as **deployment acceptance foundation**, consumed by GRSI.E but not owned by it.

Recommended order:

1. **Deployment acceptance contract v1**
   - exact release/candidate/environment identity;
   - immutable run/check receipt model;
   - explicit canary environment constraints;
   - no caller-supplied pass booleans.

2. **Target-host acceptance executor v1**
   - invoked manually by a Human Board/operator on the intended target host;
   - gathers real Compose/image/migration/health receipts;
   - synthetic data only;
   - no production promotion.

3. **Rollback proof v1**
   - restore prior release identity;
   - prove post-rollback health and schema compatibility.

4. **GRSI.E canary projection**
   - read-only consumption of the deployment-owned receipt;
   - exact candidate binding;
   - still authority-neutral.

5. Only after real target-host execution:
   - mark the bounded canary receipt passed;
   - proceed to GRSI.F promotion/rejection/rollback decision work.

---

## 21. Migration decision

This audit does **not** advance the migration head.

A deployment acceptance receipt is genuine durable state and, if implemented in the application database, would require the next migration after:

```text
0097_grsi_admission_dependency_policy
```

But implementation should occur under the deployment/release owner rather than as a GRSI-specific table.

The audit found no existing canonical table with the required release/environment/execution/rollback semantics.

---

## 22. Audit conclusion

**Reuse:**

- Git commit identity for the code artifact;
- current deployment runbook and Docker production profile for acceptance requirements;
- WorkItem for orchestration identity;
- ExecutiveDecision for canary admission authority;
- Activity for semantic deployment/rollback events;
- existing audit/logging and infrastructure checks;
- existing backup/restore and health probes.

**Do not reuse as deployment truth:**

- V12 CI;
- OrganizationalActionOutput;
- ExternalValidationRun;
- OrganizationRecordReference;
- GRSI candidate status.

**Real gap:**

> one deployment-owned, exact-release, exact-environment acceptance receipt/executor boundary.

This audit does **not** seal GRSI.E and does not claim live production readiness.

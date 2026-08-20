# V1.3-C.4 — Board/Cockpit Transparency Read Contract

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**State:** **IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING**

## Purpose

C.4 gives the first governed material-action transparency chain a bounded product-facing read contract under the existing organization API namespace.

C.1–C.3 established durable trace reconstruction, visibility of non-executing attempts and explicit governance→effect causation. C.4 turns that substrate into a Board/Cockpit-consumable API without exposing internal/raw Activity payloads.

## API surface

Added under the existing organization namespace:

```text
GET /api/v1/organization/transparency/traces/{trace_id}
GET /api/v1/organization/transparency/work-items/{work_item_id}
```

The router is registered through the canonical `router_registry.py` and does not create a second application or organization API namespace.

## Current access boundary

C.4 is intentionally Board-only using the existing trusted organization auth context:

```text
role = admin
position_key = board
```

Other authenticated roles receive `403`.

This is a bounded first product contract, **not** the final sensitivity/retention/privilege policy. Broader professional/operator visibility must be introduced explicitly when sensitivity-tier rules are implemented rather than being inferred from this endpoint.

## Safe projection

C.4 does not return raw governance payload JSON.

The trace endpoint exposes a whitelisted governance decision projection including:

- action type;
- capability;
- gateway outcome/reason;
- effective risk tier;
- consequence class;
- human-review reason;
- post-review requirement;
- constitutional activity class;
- actor/department/position/authority context;
- WorkItem/source identity;
- action fingerprint;
- idempotency key;
- occurred timestamp.

Trace records expose bounded Activity metadata including:

- role (`GOVERNANCE`, `ORGANIZATION_EFFECT`, `SUPPORTING`);
- physical/constitutional class;
- Board-inspectability/retention-lineage policy projection;
- activity type/title/summary;
- actor and organizational context;
- source identity/version;
- WorkItem link;
- trace identity;
- explicit `causation_activity_id`;
- timestamp.

Arbitrary payload content is not part of the API response schema.

## Tenant isolation

Both endpoints are tenant-bound by authenticated `OrganizationCommandContext`.

A trace identifier from another tenant returns the same non-disclosing `404` as a missing trace.

A WorkItem must exist in the authenticated tenant before its transparency history can be read.

## Fail-closed durable-data handling

The API reuses the C.1 transparency reconstruction service.

Malformed or ambiguous durable governance data returns a safe:

```text
409 Organization transparency data is inconsistent.
```

Persistence/internal exception detail is not returned to clients.

## Files

Added:

```text
apps/api/app/schemas_organization_transparency.py
apps/api/app/routers/organization_transparency.py
apps/api/tests/test_organization_transparency_api.py
```

Updated:

```text
apps/api/app/core/router_registry.py
```

## Focused tests

Five API-level tests cover:

1. Board trace read returns whitelisted governance fields and explicit effect causation;
2. transparency endpoints reject non-Board authenticated roles;
3. trace reads are tenant-scoped and non-disclosing;
4. WorkItem transparency history is Board-safe and rejects foreign/missing WorkItems;
5. malformed governance payloads fail closed with safe `409` output.

## Non-claims

C.4 does not yet implement:

- a Cockpit UI panel;
- generalized organization-wide transparency search;
- final GDPR/privilege/sensitivity-tier field policy;
- Evidence/VerifiedRule/SourceSnapshot decision lineage;
- ToolActionRecord;
- AgentConversation / AgentMessage APIs;
- arbitrary Activity graph traversal;
- a database migration;
- canonical repository PASS;
- GitHub CI PASS.

## Acceptance gate

From the canonical Windows V12 checkout:

```text
pytest apps/api/tests/test_coverage_tranche_operations_script.py::test_v10_22_documentation_and_roadmap_are_present -q

pytest apps/api/tests/test_organization_governance_kernel.py \
       apps/api/tests/test_organization_governed_work.py \
       apps/api/tests/test_organization_transparency.py \
       apps/api/tests/test_organization_transparency_attempts.py \
       apps/api/tests/test_organization_transparency_causation.py \
       apps/api/tests/test_organization_transparency_api.py -q

python scripts/check_repo_policy.py --root .
pytest apps/api/tests -q
python scripts/check_database_migrations.py
python scripts/check_local_db_schema.py --database-url "sqlite:///D:/global-mobility-aios/gmai.db"
git diff --check
git status -sb
```

Only canonical results may move C.4 to PASS.

## Direction after C.4

If C.4 passes, the low-level C foundation is sufficient for the first governed action to be inspected through a real product/API boundary.

The next move should be chosen between:

1. **V1.3-D Context & Agent Identity** prerequisites for persistent governed agent runs; or
2. a very small Cockpit transparency consumer only if it materially improves current owner-led Phase 13.17 acceptance.

Do not continue expanding generic transparency machinery without a concrete vertical/product consumer.

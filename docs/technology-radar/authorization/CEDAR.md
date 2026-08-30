# Cedar — AIOS Authorization Research

**State:** RESEARCH / R2
**Reviewed pin:** `cedar-policy/cedar@468eaef41a4fd27c17a02cef48b58bce7f2034fc`
**License:** Apache-2.0
**Primary source:** `https://docs.cedarpolicy.com/`

## Fit

Cedar's principal/action/resource/context request model aligns closely with a typed AIOS CommandRequest. Its schema and policy validation are attractive for embedded or service-wrapped contextual authorization.

## Risks

- a separate integration/runtime layer is still required;
- AIOS organization relationships must be projected into Cedar entities safely;
- policy/schema evolution and historical replay need exact versioning;
- the current AIOS ecosystem fit is less direct than OpenFGA/OPA;
- operational and multi-tenant service patterns need R3 evidence.

## R3 trigger

Run Cedar only if the OpenFGA/OPA lab exposes a material gap in typed schema validation, embedded evaluation or policy analyzability. Reuse the identical fixture and receipt contract.

## Decision

Retain as a strong challenger; no immediate lab or adoption.

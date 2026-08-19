# Global Mobility AIOS — V12 Active Changelog

This changelog records delivery on the active branch:

```text
roadmap/global-mobility-aios-v12
```

The complete frozen V11 checkpoint remains available on:

```text
roadmap/global-mobility-aios-v11
@ dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

V11 preserves its own README, Roadmap V11.5, V1.3 architecture checkpoint, and active changelog exactly as they existed when V12 was created. Earlier history also remains available through Git history and the existing archived changelog snapshots.

> **V11 is the frozen reference. V12 is the active implementation line.**

---

## 2026-08-19 — V12 ROADMAP / README ALIGNMENT — ACTIVE IMPLEMENTATION LINE CLARIFIED

### Status

**Documentation / branch-alignment checkpoint only. No runtime implementation or acceptance-state change is claimed.**

### Why this correction was needed

V12 was created directly from the frozen V11 checkpoint. That correctly preserved all files, but it also meant that the inherited `README.md` and `docs/ROADMAP.md` initially still described V11 as the current development line.

That created a naming ambiguity:

- **Git branch V11 / V12** describes repository-development generations;
- **architecture V1.3** describes the Human-Like High-Autonomy Organization architecture version;
- **Roadmap V11.5 / V12.0** describes roadmap-document generations.

These version systems are related but are not the same thing.

V1.3 was designed and frozen on V11 before V12 was created. Therefore it is correct that the frozen V11 checkpoint contains V1.3 architecture documentation. What was incorrect was allowing V12's inherited roadmap metadata to continue calling V11 the active development branch.

### V11 remains unchanged

Frozen branch:

```text
roadmap/global-mobility-aios-v11
```

Frozen checkpoint:

```text
dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

V11 continues to preserve:

- its V11 README;
- Roadmap V11.5;
- the V1.3 architecture documentation checkpoint;
- Phase 13.16.10 accepted product baseline;
- Phase 13.17 owner-led human acceptance state;
- the V1.3-era changelog as of the frozen checkpoint.

No V11 file was modified by the V12 alignment work.

### V12 README alignment

Commit:

```text
4a347d418408a199198832e211f13555cf1ee5e9
```

Message:

```text
docs: align v12 readme with v1.3 direction
```

The V12 README now opens with the active project definition:

> **A governed, transparent, high-autonomy digital organization for global mobility.**

It explicitly identifies:

- `roadmap/global-mobility-aios-v12` as the active development line;
- V11 at `dd2f2cd` as the frozen predecessor/reference checkpoint;
- V1.3 as the active architecture direction;
- the Organizational Immune System;
- Earned Autonomy;
- Board Transparency;
- Decision Lineage;
- persistent AI employees;
- risk-tiered verification;
- the V1.3-A → V1.3-N implementation direction.

### V12 Roadmap V12.0

Commit:

```text
dac2529f4dee279cddc738c9310960afb32cc139
```

Message:

```text
docs: establish v12 implementation roadmap
```

`docs/ROADMAP.md` is now explicitly:

```text
Global Mobility AIOS — Active V12 Implementation Roadmap
Roadmap generation: V12.0
Active branch: roadmap/global-mobility-aios-v12
Frozen predecessor: roadmap/global-mobility-aios-v11 @ dd2f2cd
```

The V12 roadmap deliberately changes role from the frozen V11.5 document:

- **V11.5** records the checkpoint and architecture direction frozen on V11;
- **V12.0** is the active implementation roadmap for proving and realizing that direction.

The V12 roadmap retains the project vision and complete V1.3 implementation direction while putting greater emphasis on implementation evidence, real vertical workflows, external validation, legal/data-governance maturity, operational maturity, and the V1.3-A → V1.3-N runtime programme.

### V12 roadmap priorities

The active implementation sequence remains:

```text
V1.3-A  Constitutional Contracts
V1.3-B  Minimal Governance Kernel
V1.3-C  Transparency Foundation
V1.3-D  Context & Agent Identity
V1.3-E  First Governed Vertical Workflow
V1.3-F  Decision Readiness
V1.3-G  Independent Verification
V1.3-H  Organizational Immune System
V1.3-I  Earned Autonomy
V1.3-J  Agent Organization Runtime
V1.3-K  Execution / Coworker Runtime
V1.3-L  Live Organization
V1.3-M  Board Transparency Experience
V1.3-N  Learning & Optimization
```

The roadmap additionally makes the first governed vertical workflow a central proof point so architecture does not continue expanding without implementation evidence.

### Product validation emphasis

V12 explicitly recognizes that architecture/engineering maturity is currently ahead of independent product validation.

The validation direction is:

```text
owner-led acceptance
        ↓
external professional usability
        ↓
real mobility workflow / real case
        ↓
first external cases
        ↓
repeatable jurisdiction workflow
        ↓
first paying professional / organization
        ↓
measured demand
```

This does not reduce the long-term project ambition. It is intended to turn architecture quality into external evidence.

### Runtime truth unchanged

This README/Roadmap alignment does **not**:

- modify application/runtime code;
- change database schema;
- change Alembic head;
- mutate preserved `gmai.db`;
- implement Decision Readiness;
- implement the Organizational Immune System;
- implement earned autonomy;
- implement the Transparency Layer;
- integrate Munder Difflin or OpenWorker;
- resolve Phase 13.17 findings;
- change Technology Radar adoption state;
- rerun or claim a new API/web/design regression;
- claim GitHub CI PASS.

Latest accepted runtime evidence remains carried forward:

```text
API regression                873 passed / 5 skipped / 0 failed
Next.js production build      41 / 41 pages
Design foundation             28 / 28 passed
Alembic head                  0076_organization_position_active_identity
Preserved gmai.db             unchanged at accepted checkpoint
```

---

## 2026-08-19 — V12 DEVELOPMENT BRANCH OPENED / V11 FROZEN

### Status

**Repository isolation / branch-governance checkpoint only.**

A new active development branch was created from the frozen V11 checkpoint:

```text
roadmap/global-mobility-aios-v11
@ dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
        │
        └── roadmap/global-mobility-aios-v12
```

GitHub comparison at creation confirmed:

```text
V11 ↔ V12
status: identical
ahead: 0
behind: 0
starting SHA: dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

The branch split exists so ambitious V1.3 implementation can proceed without disturbing the clean V11 checkpoint.

### First V12 documentation checkpoint

Commit:

```text
2120ba7f509d9f556534d859628755e2608d2955
```

Message:

```text
docs: record v12 development branch transition
```

This recorded:

- V11 as frozen reference/recovery state;
- V12 as the active implementation branch;
- V1.3-A → V1.3-N as the continuing architecture programme;
- Phase 13.17 as a parallel feedback stream;
- no runtime/test/migration/acceptance-state change from the branch split itself.

---

## History before V12

For the exact state before V12 work began, use:

```text
Branch: roadmap/global-mobility-aios-v11
Commit: dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

That checkpoint contains the detailed V1.3 architecture change record, Roadmap V11.5, README state, and links to earlier archived changelog history.

Existing repository archives remain authoritative for older sealed history, including:

- `docs/archive/CHANGELOG_THROUGH_C192E7D_2026-08-19.md`;
- `docs/archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md`.

Git history remains the immutable source for exact historical diffs and commit lineage.

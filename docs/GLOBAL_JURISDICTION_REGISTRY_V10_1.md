# Global Jurisdiction Registry v10.1

## Outcome

Phase 10B now has a canonical, versioned registry that separates geographic scope
from verified immigration coverage. The active release contains 249 ISO-coded
country and area entries:

- 193 United Nations member states;
- two United Nations observer states;
- 43 territories or other ISO-coded areas;
- 11 entries typed as autonomous jurisdictions;
- 243 entries requiring immigration-coverage review;
- six special or unpopulated areas retained in scope but excluded from the coverage denominator.

The registry does not claim that a listed territory has independent immigration
rules. Every imported entry starts with `immigration_rule_status=unassessed`.

## Authoritative scope

The importer retrieves the fixed allowlisted United Nations Statistics Division
M49 English table:

- `https://unstats.un.org/unsd/methodology/m49/overview/`

M49 supplies the canonical name, numeric M49 code, ISO alpha-2 and alpha-3 code,
region, and subregion. The source is reconciled with ISO 3166-1 scope because ISO
Part 1 includes countries, dependencies, and other areas of geopolitical interest:

- `https://www.iso.org/iso-3166-country-codes.html`

The canonical normalized payload—not mutable page markup—is SHA-256 hashed. Importing
the same payload is idempotent. A changed payload creates a new immutable release and
marks the previous release `superseded`.

## Data model

`jurisdiction_registry_releases` records:

- release version and status;
- canonical dataset SHA-256;
- source and retrieval time;
- expected and imported entry counts;
- release actor and time.

`jurisdiction_registry_entries` snapshots every entry for that release, including:

- canonical codes and name;
- membership and jurisdiction type;
- region and subregion;
- parent and independent-immigration-rule review states;
- coverage requirement;
- immutable row hash.

Operational `Jurisdiction` records are upserted by alpha-2 code, while previous
registry releases remain queryable as immutable snapshots.

## Coverage release gate

The registry API reports these independent checks:

1. Complete registry release with 193 members and two observers.
2. Reviewed immigration authority for every required jurisdiction.
3. Active official immigration source for every required jurisdiction.
4. Fresh active monitor for every required jurisdiction.
5. Active human-published verified rule for every required jurisdiction.
6. Reviewed independent/inherited immigration-rule status.

`global_coverage_claim_ready` becomes true only when all six checks pass. The active
release currently passes the registry-scope check and deliberately fails the evidence
coverage checks.

## Interfaces

- `GET /api/v1/global-intelligence/registry` returns the active release, counts,
  regional rollups, entry-level gaps, and release gate.
- `POST /api/v1/global-intelligence/registry/import-un-m49` imports a new release for
  an authorized reviewer or administrator.
- `python scripts/seed_global_jurisdiction_registry.py` performs the same controlled
  import for a configured local or deployment database.
- `/global-intelligence`, Coverage tab, provides release metrics, regional posture,
  evidence-gate state, search, type filtering, gap filtering, and the 249-entry ledger.

## Safety boundaries

- Registry inclusion is not immigration coverage.
- ISO/UN categorization is not a political or legal-status determination.
- Autonomous-jurisdiction typing does not confirm independent immigration rules.
- A missing rule or monitor is shown as a gap, never interpreted as “no requirements.”
- The global coverage label remains blocked until the complete evidence gate passes.

## Verification

Automated tests cover canonical table parsing, version hashing, idempotent import,
member/observer/territory typing, autonomous typing, evidence gap calculation, and
the no-release API state. The registry schema begins at migration
`0017_global_jurisdiction_registry`; the v10.2 assessment workflow extends it without
mutating the active 249-entry release.

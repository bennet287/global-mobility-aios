# AIOS V2 programme execution

User authorization: implement the complete Master Plan v1.1; reiterated after the
initial shell slice. This is the execution ledger, not an acceptance record.

Starting HEAD: `8682f25a604a009f8e3db72e2b3c7f81b0872e78`.
Branch: `design/aios-v2-premium-shell`; earlier uncommitted shell work is retained.
The user's pre-existing `apps/web/tsconfig.json` modification remains preserved.

| Plan area | Implementation | Remaining proof/work |
|---|---|---|
| Design Skill v2 / Q0 | Existing design bootstrap and Q0 shell audit | Consolidated reference/quality reviews |
| Q1 shell/navigation | Seven domains, desktop/mobile navigation | Cross-route browser proof |
| Q2 command/search | Workspace navigation and scoped loaded-record registry | Entity selection, recent destinations, keyboard proof |
| Q3 Owner Home | Attention-first composition; mobile structured snapshot | Real fixture and light/dark visual proof |
| Q4/Q5 primitives/object grammar | Truth/status, states, disclosure, fields, headers and rows | Cross-domain visual review |
| Q6 Missions | Purpose, state, participants, work, blockers, conversations and links | API-fixture E2E and continuity |
| Q7 Evidence | Rules, official sources, exact snapshot joins and provenance | Missing/partial/retired/link tests |
| Q8 Decisions | Paginated records, references, outcomes and explicit Board action | Authority, failure, supersession, refresh tests |
| Q9 Intelligence | Monitored changes, source/review/freshness/coverage, classified signals | Fixture and filter proof |
| Q10 History | Timeline, reconstruction, compare and aggregate memory | Cursor/coverage/memory fixture proof |
| Q11 source states | Read helper rejects obsolete requests; explicit stale/error states | Race and refresh regression |
| Q12/Q13 responsive/accessibility | Labelled native controls; mobile structured organization | Width/zoom/reduced-motion/keyboard and screen-reader review |
| Q14/Q15 motion/themes | Scoped light/dark/system; bounded recorded handoff emphasis | All-theme visual review |
| Q16 visual regression | Initial shell screenshots | Expanded fixture states and baseline |
| Q17 / Wave 10 acceptance | Not accepted | Exact-head CI, independent review, usability and release proof |
| Track A 2N | Existing HQ/character integration | Original 2N exact-head/visual gate remains distinct |
| Track A 2O handoff | Existing descriptor plus selected-event renderer | Semantic negative/browser proof |
| Track A conversation/collaboration | Canonical participant/lifecycle relations | Spatial emphasis and no-invented-transcript proof |
| Track A Board/blocker/object | Canonical attention, blocker and smart-object inspection | Spatial-object interaction review |
| Track A temporal integration | Supported structured replay and memory | Historical spatial projection; no unsupported dimension inference |
| Track A world/art/camera | Existing original art/HQ, structured fallback, bounded zoom | Mature asset/rig/LOD, directed focus, world polish and measured performance |
| Operator / Mobility User migration | Existing functional structured routes retained | Experience navigation and full route/state migration audit |
| Guided Experience / Wave 7 | Driver.js package intake reviewed | Adapter, contextual steps, accessibility/no-mutation tests |

Rows remain open until both the requirement and its relevant proof exist. A
route or a successful compiler check is not whole-programme completion.

## Driver.js intake

The master plan selects Driver.js for the guided experience. Reviewed package:
`driver.js@1.8.0`, repository `https://github.com/nilbuild/driver.js` (the previous
upstream URL redirects there), MIT license. Published package has no runtime
dependencies and no install lifecycle hooks; installation nevertheless used
`--ignore-scripts`. npm reported zero vulnerabilities after installation.

Pinned integrity:
`sha512-+8/IO7h1v14IzWh2GP60N7T3PFZweXwdn5e5POuxRSBoCYUojsBxzqawPeXh3YZIibRy7EehYNEyxe7slwwtdg==`.

Source checks: installed package metadata, MIT license and runtime bundle;
no `fetch`, `XMLHttpRequest`, `sendBeacon`, localStorage or sessionStorage calls
were found in the main published runtime bundle. This bounded source inspection
is not a comprehensive security audit. MIT notice must remain in distributions.

Allowed use: dynamically loaded, explicitly started V2 guidance over stable DOM
anchors, static first-party text and presentation-only navigation. It owns no
case data, evidence, authority, domain state, workflow or event truth. No tour
auto-executes actions or sends records to another service.

References: [official installation](https://driverjs.com/docs/installation),
[configuration](https://driverjs.com/docs/configuration),
[upstream license](https://github.com/nilbuild/driver.js/blob/master/license).

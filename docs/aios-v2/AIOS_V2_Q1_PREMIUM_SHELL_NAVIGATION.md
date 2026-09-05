# AIOS V2 Q0 / Q1 — Shell and workspace navigation

Date: 2026-09-05

Status: IMPLEMENTED / FOCUSED LOCAL VALIDATION PASS / ACCEPTANCE PENDING.

Starting HEAD: `8682f25a604a009f8e3db72e2b3c7f81b0872e78`.
Local branch: `design/aios-v2-premium-shell`.
Origin: `https://github.com/bennet287/global-mobility-aios.git` (actual git remote).
This slice is stacked on the Phase 2N candidate, not evidence that 2N was accepted.
The pre-existing `apps/web/tsconfig.json` local change is outside this slice.

## Q0 observed baseline

The Owner wants to reach an organizational workspace and understand current
context even while organization data or spatial presentation is unavailable.
Navigation changes presentation context; backend authorization remains unchanged.

| Area | Observed repository state | Smallest required change |
|---|---|---|
| Routes | `/cockpit/v2` and `/cockpit/v2/organization` are the two implemented V2 routes | Preserve both; mark the other five domains as planned |
| Shell | `V2Shell.tsx` is composed by Owner Home and Organization | Keep its existing props; isolate shell styling |
| Legacy reuse | `/cockpit`, `/cockpit/decisions`, `/cockpit/live-organization` exist | Offer clearly named structured destinations |
| State | Hooks own canonical reads; `selectedPositionKey` owns employee selection | Shell owns only collapse, modal and query state |
| CSS | `foundation.css` combines shell and domain rules | Remove obsolete shell selectors; use a shell CSS module |
| Tokens | Scoped V2 color, type, spacing, radius, motion and layout tokens exist | Add control minimum, compact rail, topbar and skip-link layer tokens |
| Typography | Geist from the root layout; V2 type scale | Reuse; no font download/dependency added by this slice |
| Icons | Single letters, including letters as the only visible tablet navigation | Original consistent outline SVG registry with accessible labels |
| Keyboard | Disabled command button; no collapse/menu; skip target not focusable | Native modal, focus restoration, skip focus and Ctrl/Meta+K |
| Responsive | Labels hidden below 980px, four-column icon grid | Labelled navigation dialog; preserve workspace width |
| Loading/errors | Existing Owner/Organization loading and partial-source UI | Navigation works independently of data; health remains unavailable until observed |
| Motion | V2 reduced-motion tokens already exist | Shell requires no animation or spatial renderer |
| Test coverage | Static foundation tests; no V2 shell browser suite | Executable route/search tests and Chromium interaction tests |
| Remaining prototype debt | Owner Home explanatory text, theme refinement and domain pages | Q3 and subsequent domain/theme phases |

## Implementation contract

The seven-domain Owner mental model is shared by desktop and mobile navigation.
Only Home and Organization are enabled as V2 destinations. Planned entries have
visible text, no links and `aria-disabled`. A compact desktop rail preserves
accessible link names. Owner workspace is a product context, not a claim about
the signed-in user's authorization or identity.

The command entry provides bounded **workspace navigation**, an initial part of
Q2. It filters five explicit existing destinations, including clearly described
structured workspaces. It does not search cases, employees, private records or
remote APIs, and it cannot approve or execute material actions. No new runtime
dependency, storage, API call, authority state or notification count is added.

The native dialog supplies modal semantics and focus containment. Escape and
the close button restore focus; Tab operates native controls; arrow keys select
command links; Enter follows the selected destination. Search has an explicit
label, empty results and a result-count announcement. A single overlay state
prevents stacking the menu and command palette.

Chromium tests exposed initial focus and Tab-boundary gaps in native dialog
behavior. The shell now explicitly focuses search after opening, wraps Tab at
the first/last control and closes on Escape even when a search input has text.

Unavailable-source browser review also exposed an existing Owner Home defect:
failed attention reads were described as a canonical zero state. The attention
surface now receives explicit source availability, marks its count incomplete,
and distinguishes unknown attention from a successful empty response. Available
items remain inspectable when other attention sources fail.

Shell-only styles move out of the foundation file. Domain styles and canonical
HQ/employee selection contracts retain their existing ownership. Below 980px,
the rail gives way to a labelled modal. At narrow mobile widths the health text
gets its own line. Touch targets are at least 44px high. Reduced motion retains
all navigation meaning; forced-color active navigation has an outline.

## Review and risk boundaries

- Task clarity: route context, two usable V2 destinations, explicit planned state.
- Truth: online means the existing health hook returned `status=ok`; otherwise
  status is unavailable. No inferred owner identity, presence or authority.
- Visual hierarchy: workspace remains primary; shell uses restrained warm accents.
- Accessibility: native controls, labels, skip focus and keyboard modal behavior.
- Performance: no renderer or data fetch is imported by the navigation layer.
- Remaining risks: human screen-reader review, theme modes, full cross-view visual
  acceptance and exact-current-head CI remain separate acceptance gates.

## Validation

Observed under Node `v24.18.0`, against local changes on stable starting/ending
HEAD `8682f25a604a009f8e3db72e2b3c7f81b0872e78`:

| Gate | Observed result |
|---|---|
| Locked frontend and E2E `npm ci` | PASS; both reported zero vulnerabilities |
| Design foundation | PASS: 74 + 210 tests |
| Request auth | PASS: 7 tests |
| TypeScript `tsc --noEmit` | PASS |
| Production build | PASS, including final focus/Escape fixes |
| Compiled auth | PASS |
| Repository policy | PASS |
| Release consistency | PASS |
| Diff whitespace | PASS |
| Focused Chromium suite | PASS: 4 tests, 7.2 seconds, exit code 0 |

Chromium proof uses the built app and unavailable-API fixtures. It covers
navigation without data, attention unavailability, active links, planned routes,
rail collapse, skip focus, search/empty results, keyboard selection, Escape,
focus restoration, modal Tab boundaries, 390px/768px reduced-motion layouts and
no API writes. It does not prove live data, full product E2E or human acceptance.

The normal port 3000 was occupied. An ignored local config retained the repository
Chromium project and started the built app on port 3016; the checked-in suite and
CI config still use the normal port. The pinned browser was installed in
`.local/gmai-dev-cache/playwright`. Final screenshots in
`.local/gmai-dev-temp/v2-shell-browser-results` were inspected for desktop shell,
mobile shell and tablet menu. Earlier focus/Escape failures were repaired before
the final passing run. The in-app Browser runtime reported no available browser;
this proof comes from the repository Playwright test runner.

These are local working-tree results, not clean committed exact-head acceptance
or remote CI. No CI run, merge, full backend/PostgreSQL regression, screen-reader
acceptance or all-theme visual baseline is claimed. Phase 2N, the V2 programme
and milestone M are not sealed by this slice.

## Next sequence

1. Review this shell with real Owner/Organization data and complete exact-head CI.
2. Reconcile Phase 2N proof and visual acceptance independently.
3. Consolidate Design Skill v2 review/reference material without blind third-party installation.
4. Continue Q2 entity/attention navigation only against proven client-side contracts.
5. Implement Q3 Owner Home and the subsequent domain slices from the accepted base.

The supplied master plan's remaining waves and acceptance gates stay open.

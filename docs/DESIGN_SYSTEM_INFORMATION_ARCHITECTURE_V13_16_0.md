# Phase 13.16.0 Design System and Information Architecture Foundation

**Implementation status:** Complete; independent internal rendered acceptance PASS; Phase 13.16.0 CLOSED / PASS
**Baseline:** `195423ce8b5f63bd6d7fd199a2df491465e2e116`
**Scope:** Presentation, interaction, responsive behavior, and information architecture only

## 1. Purpose

This foundation gives Global Mobility AIOS one coherent visual and interaction
grammar while preserving every regulated decision, lifecycle, certification,
authorization, audit, and publication boundary. It normalizes the six critical
review surfaces without implementing the role-specific shells or broader product
redesigns scheduled for later Phase 13.16 slices.

## 2. Design principles

1. Put the decision and its reliance boundary before implementation detail.
2. Put blockers and next actions before supporting inventories.
3. Preserve material warnings in the primary reading flow.
4. Make provenance available, copyable, and progressively disclosed.
5. Use plain language first and governed technical terminology second.
6. Use shared semantic tokens across light and dark themes.
7. Make state legible through words and structure, not color alone.
8. Prefer a small set of real product primitives over a large abstract library.

## 3. Typography

The shared scale is defined in `app/globals.css`:

- `--type-display`: high-emphasis hero statements;
- `--type-page-title`: the single page `h1`;
- `--type-section-title`: major `h2` sections;
- `--type-card-title`: card and action titles;
- `--type-body`: ordinary user and operator content;
- `--type-body-secondary`: supporting explanation;
- `--type-label`: field labels and useful eyebrows;
- `--type-caption`: secondary metadata;
- `--type-status`: compact state text; and
- `--type-technical`: identifiers and code-like values.

Normal body content does not become microscopic to solve density. Uppercase is
reserved for source-provided or genuinely compact governed statuses, not entire
informational blocks.

## 4. Geist Sans and Geist Mono

The root layout loads Geist Sans and Geist Mono through `next/font/google`, with
no raw font binaries stored in the repository. Geist Sans is the product font.
Geist Mono is restricted to `code`, `pre`, `.monospace`, `.technical-value`, and
identifier values inside technical provenance.

Dates, prices, labels, headings, ordinary status text, and prose remain Geist
Sans. A value does not become monospaced merely because it appears in an
operator workspace.

## 5. Spacing scale

The shared spacing scale runs from `--space-0` through `--space-16`, using a
four-pixel base and intentional larger intervals. Page padding, section gaps,
grid gaps, card padding, control gaps, and disclosure spacing consume this scale.
Page-specific layout can compose the scale but should not introduce arbitrary
spacing when a shared value fits.

## 6. Layout and container system

- `--content-readable`: regulated decision and long-form reading surfaces;
- `--content-operator`: wide operator and governance workspaces;
- `--page-padding`: fluid horizontal padding from mobile through desktop;
- `--section-gap`: vertical separation between major tasks; and
- `--grid-gap`: shared card and layout spacing.

The application shell provides one `main` landmark. Eligibility retains its
purpose-built standalone shell but uses the same readable container and skip
link. Sticky operator areas become ordinary flow when the viewport no longer
supports the wide layout.

## 7. Color and state semantics

Both themes use the same state contracts:

| State | Purpose | Non-color cue |
|---|---|---|
| Neutral/information | context and secondary state | visible label and bordered surface |
| Success | verified, complete, approved | explicit state text and status marker |
| Warning/pending | unresolved or pending review | warning wording and left-border treatment |
| Danger/blocking | action cannot safely proceed | blocker heading, required/missing wording |
| Draft | lifecycle not published | `Draft` text |
| Simulation-only | internal-only assessment context | persistent simulation banner and text |
| Unpublished | not available for production reliance | `Unpublished` text |
| Disabled | unavailable control | disabled HTML state and reduced opacity |
| Loading | asynchronous work | status text plus skeleton treatment |

Light and dark themes remap these semantic variables rather than maintaining
unrelated component palettes.

## 8. Shared component inventory

- `WorkspaceShell`: sidebar, mobile navigation, skip link, main landmark, and
  Escape-to-close behavior.
- `Topbar`: page heading, live load status, and refresh action.
- `.panel`: shared surface/card primitive using common border, radius, and
  elevation tokens.
- `SectionTitle`: section eyebrow, heading, and supporting description.
- `StatusBadge`: text-labelled, non-color-only state presentation.
- `InlineNotice`: polite status or assertive error presentation.
- `ActionCard`: outcome-oriented linked action.
- `.blocker-list` and `.planning-blockers`: material blocking requirement.
- `.planning-next-actions` and `.next-action-section`: prioritized actions.
- `.button` plus native form controls: normalized controls and touch targets.
- `MetricPill`: metric/value presentation.
- `.responsive-table-region`: keyboard-focusable horizontal table region when
  a stacked alternative is not appropriate.
- `EmptyState`: shared empty state with status semantics.
- `Skeleton`: non-announced visual loading placeholder paired with status text.
- `TechnicalDisclosure`: native accessible provenance disclosure.

This list evolves existing primitives; it is not a general-purpose component
framework.

## 9. Decision and context hierarchy

Regulated decision surfaces use this order:

1. **Decision/context** — what the assessment is and its reliance boundary.
2. **Blockers** — requirements that prevent progress.
3. **Next actions** — what the user or operator should do.
4. **Supporting evidence** — requirements, documents, candidates, risks, and
   source status needed to understand the decision.
5. **Technical provenance** — raw identifiers, hashes, snapshots, rules, and
   internal version metadata.

The sequence governs emphasis, not data deletion. A material pending
certification warning stays visible before provenance is opened.

## 10. Progressive disclosure rules

- Never collapse a blocker, non-reliance warning, pending material certification,
  draft status, simulation-only status, or unpublished state.
- Collapse raw identifiers and long evidence chains when they are not required
  for the immediate task.
- Use native `details` and `summary` so keyboard and assistive-technology behavior
  remains available without JavaScript.
- Give the summary a meaningful label and a short description of its contents.
- Preserve the content in the document and keep identifiers copyable.

## 11. Technical provenance rules

Technical provenance includes UUIDs, source IDs, snapshot IDs, rule IDs,
certification IDs, hashes, audit IDs, and internal version identifiers. It uses
Geist Mono, wraps safely, and appears under a `Technical provenance` disclosure.
Human-readable source names, evidence state, and material certification warnings
remain outside the disclosure when they affect the decision.

## 12. Mobility User architecture

Mental model: **My case and what I need to do next.**

The future mobility-user shell should prioritize case status, safe pathway
context, blockers, next actions, documents, progress, and relevant appointments
or timeline. Phase numbers, backend health, raw identifiers, certification
administration, publication controls, and agent runtime controls are not primary
mobility-user navigation.

Phase 13.16.0 prepares this architecture through the Eligibility hierarchy and
shared primitives. It does not implement the full Phase 13.16.7 redesign.

## 13. Professional and Operator architecture

Mental model: **What decision or work requires attention, and what evidence
supports it?**

The future operator shell should prioritize cases, eligibility, pathway
comparison, evidence, documents, timelines, authority work, validation,
provenance, and professional-depth lifecycle/certification state. Phase 13.16.0
normalizes Profiles, Planning, Validation, and Agent Console foundations but
does not implement the full Phase 13.16.8 redesign.

## 14. Owner and Board architecture

Mental model: **What is happening, what is blocked, and what requires my
decision?**

The future owner shell should prioritize organization health, meaningful
outcomes, blockers, decisions, risks, validation state, human attention, and
governance. Phase 13.16.0 normalizes Board Room typography, landmarks, states,
and responsive behavior. The Owner Control Center remains Phase 13.16.3.

## 15. Responsive requirements

- Small mobile: one-column critical flow, full-width primary actions, no page
  overflow, and technical values wrapping within their container.
- Large mobile: the same reading order with efficient card grouping.
- Tablet: two-column metrics where space permits; sticky side panels return to
  document flow when needed.
- Standard desktop: readable decision width with supporting operator columns.
- Wide desktop: operator content may use the wide container without stretching
  decision prose beyond the readable measure.
- Dense tables either stack using existing responsive rules or remain inside a
  labelled, keyboard-focusable horizontal region.

## 16. Accessibility requirements

- one primary `main` landmark and sensible heading order;
- a skip-to-content link;
- `aria-current` for current navigation;
- `aria-expanded` and `aria-controls` for mobile navigation;
- Escape closes the open mobile navigation;
- visible focus is never globally disabled;
- alert/status semantics for asynchronous notices;
- labelled native controls and minimum practical touch targets;
- words and structural cues in addition to color;
- native keyboard-accessible disclosure;
- wrapping identifiers and scalable text; and
- `prefers-reduced-motion` disables non-essential movement.

## 17. Round 6 findings

| Finding | Phase 13.16.0 response | Current status |
|---|---|---|
| `R6-MU-01` | Renamed the percentages as internal assessment signals, removed probability-like rings, and states that they do not estimate approval probability. The calculations are unchanged. | Resolved / rendered PASS |
| `R6-MU-02` | Plain-language decision context, blockers, actions, evidence, then provenance; governed warnings retained. | Resolved / rendered PASS |
| `R6-MU-03` | Production and internal-simulation selector states differ, with a persistent accessible banner whenever draft simulation is selected or rendered. Authorization is unchanged. | Resolved / rendered PASS |
| `R6-MU-04` | Blocking material requirements and immediate next actions precede document and evidence inventories. | Resolved / rendered PASS |
| `R6-PRO-001` | Six critical routes received a focused professional rendered pass. | Resolved / rendered PASS |
| `R6-PRO-002` | Planning separates potential alternatives from explicitly excluded routes while retaining excluded-route evidence. | Resolved / rendered PASS |

## 18. Explicitly deferred

- Phase 13.16.1 durable contribution and activity model;
- Phase 13.16.2 role-based shells and navigation;
- Phase 13.16.3 Owner Control Center;
- Phase 13.16.4 department workspace implementation;
- Phase 13.16.5 dependency and blocker view;
- Phase 13.16.6 owner inbox;
- Phase 13.16.7 full mobility-user redesign;
- Phase 13.16.8 full professional/operator redesign;
- Phase 13.16.9 evidence/provenance consolidation programme;
- Phase 13.16.10 integrated responsive/accessibility acceptance;
- Phase 13.17 genuine external-human acceptance; and
- Phase 14 scale work.

## 19. Rendered acceptance matrix

Independent internal rendered acceptance passed. This evidence is not genuine
external-human acceptance and does not satisfy Phase 13.17.

| Surface or behavior | Result |
|---|---|
| Desktop acceptance surfaces | PASS |
| Eligibility responsive at 390px | PASS |
| Planning responsive at 390px | PASS |
| Agent Console responsive at 390px | PASS |
| Planning dark theme | PASS |
| Eligibility dark theme | PASS |
| Board Room acronyms | PASS |
| Validation form control | PASS |
| Agent Console Leads | PASS |
| Agent Console Recent agent runs | PASS |
| Technical provenance visible focus | PASS |
| Technical provenance keyboard activation with Enter/Space | PASS |
| Technical provenance identifier wrapping | PASS |
| Page-level horizontal overflow in tested narrow surfaces | NONE / PASS |
| `/icon.svg` | HTTP 200 / PASS |
| Normal Agent Console console state | No errors / PASS |
| Final Planning redundant country-ranking 404 | RESOLVED / PASS |

Phase 13.16.0 is closed. Phase 13.16.1 is unlocked but not started; broader
cross-role implementation and integrated acceptance remain in their later slices.

## 20. Safety and governance preservation

Phase 13.16.0 must not change eligibility calculation, matching, points, evidence
gaps, fees, cost inheritance, evidence selection, snapshots, rules,
certifications, pathway lifecycle, publication, simulation authorization,
authentication, RBAC, CORS, audit behavior, validation decisions, database
schema, migrations, or API contracts.

Austria v4 remains draft, `simulation_candidate`, `INTERNAL_SIMULATION_ONLY`,
not a production recommendation, simulation-only, unpublished, and not
publication-ready. The national and regional 2026 occupation certifications
remain `pending_review`; the distinct core certification remains approved.
Presentation can clarify these facts. It cannot change them.

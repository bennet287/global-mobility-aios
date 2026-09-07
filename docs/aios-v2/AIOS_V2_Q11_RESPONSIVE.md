# AIOS V2 Q11 — Responsive Reprioritization

Q11 hardens the accepted Owner experience across desktop, tablet and phone widths without changing the truth model or shrinking desktop layouts into miniature replicas.

## Product rule

**Responsive = reprioritization, not shrinking.**

The same governed state remains available at every viewport. Layout may stack, scroll within an intentional navigation rail, or move secondary presentation below primary content, but responsive behavior must not manufacture, suppress, reinterpret or downgrade canonical meaning.

## Implemented behavior

- Shared Owner shell keeps the desktop rail above 980px.
- Tablet widths convert the rail into a compact top navigation surface with all seven Owner domains available.
- Phone widths convert Owner navigation into a horizontal, keyboard-focusable task rail with 48px targets rather than compressing seven items into an unreadable grid.
- Guide, Theme and Search controls remain available in the top line; compact phone presentation preserves their accessible names and 44px interaction targets.
- Shared premium primitives stack page/section actions and metric groups when the available width no longer supports the desktop hierarchy.
- The Guided Experience uses a horizontal step rail on phones so the active sequence remains primary while detailed content stays readable below it.
- Existing route-specific Mission, Evidence, Intelligence, Decision, History, Situation Room and Organization breakpoints remain authoritative for their domain layouts.
- Long governed identifiers and recorded text can wrap instead of forcing page-level horizontal overflow.

## Truth boundary

Q11 is presentation-only. Viewport width does not change canonical data, source coverage, authority, permission, Mission state, Evidence meaning, Decision meaning, historical reconstruction, presence, location, travel, collaboration, completion, health, urgency, validity, freshness, approval or success semantics.

No new backend request, persistence, mutation or canonical write path is introduced.

## Acceptance contract

Static coverage verifies responsive CSS load order, breakpoint policy, touch targets, task-rail behavior, route-level collapse rules, and absence of scale/zoom or horizontal clipping shortcuts.

Focused Chromium coverage sweeps all seven Owner routes at 1280px, 768px and 390px with reduced motion, verifying:

- active route identity remains accessible;
- page/document/root do not overflow the viewport;
- Guide, Theme and Search stay available;
- phone navigation targets remain at least 44px;
- phone navigation scroll is contained within the navigation surface;
- no non-GET backend requests are emitted;
- no page errors are produced.

A separate phone check verifies the Guided Experience step rail is horizontally scrollable while the page itself remains overflow-free.

Human visual acceptance should inspect at least Home, Organization, Missions, Decisions and History at 1280px, ~768px and 390px in both accepted theme families before sealing Q11.

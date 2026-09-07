# AIOS V2 Phase 7F — Owner / Board Escalation Integration

## Purpose

Phase 7F makes canonical Owner and Board attention evidence visible in AIOS V2 without converting governance records into theatrical physical behavior.

The slice remains read-only and presentation-only. It does not create, acknowledge, resolve, approve, escalate, or otherwise mutate canonical organization records.

## Canonical inputs

Phase 7F consumes existing `LivingOrganizationScene` deterministic records only.

### Human actions

Supported coverage is exactly:

`organization_human_action_request_open_records`

The backend scene projection includes active `OrganizationHumanActionRequest` records with statuses `required`, `acknowledged`, or `in_progress` when linked to the scene's WorkItems, decisions, or blockers.

The frontend preserves the exact `required_role`, status, priority, instructions, authority level, linkage IDs, and timestamps. It does not infer a role from nearby employees or a room.

### Risk escalations

Supported coverage is exactly:

`risk_escalation_open_records`

The backend scene projection excludes `resolved` risks. Phase 7F preserves exact:

- accountable position key
- escalated-to position key
- status
- category
- severity
- `requires_board_attention`
- `is_emergency`
- WorkItem linkage
- canonical basis and evidence context

Severity alone never establishes Board attention. A `critical` risk with `requires_board_attention=false` remains explicitly not a Board-attention risk.

### Decision attention

Phase 7F consumes the backend-derived `LivingSceneDecision.required_owner_action` flag rather than re-deriving governance policy in the renderer.

The backend establishes that flag only for a current Board-owned decision in the supported pending states. The renderer presents that evidence and does not infer approval, rejection, or a decision outcome.

## Shared projection

`apps/web/lib/v2/visible-owner-board-escalation.ts` is the single frontend projection for Phase 7F.

It:

- accepts only the exact human-action and risk-escalation coverage sources
- keeps decision attention, human action, and risk escalation as separate evidence classes
- binds risk accountable/escalated positions to employee presentation only through a unique exact `position_key`
- fails closed for duplicate roster position keys
- returns `boardAttentionCount=null` when either governed attention coverage plane is unavailable, rather than presenting a partial count as canonical zero
- computes Board attention from exact decision attention + active human actions + risks explicitly marked for Board attention when both governed coverage planes are supported

## Visible surfaces

### Organization — Spatial

A renderer-independent Owner / Board attention card appears above Living HQ. It presents bounded exact evidence and does not drive character locomotion, room entry, meeting animation, or approval animation.

### Organization — Structured / reduced motion

The same shared projection is rendered without mounting Living HQ. Reduced motion therefore preserves all Phase 7F meaning without animation.

### Mission Room

Mission Room scopes Phase 7F records by exact Mission WorkItem IDs. It exposes:

- linked decisions
- active human actions
- unresolved risk escalation routes
- mission-scoped Board-attention count when governed coverage is complete

Unavailable coverage remains `Unavailable`; it is never rendered as numeric zero.

### Employee Inspector

Employee Inspector exposes a risk escalation only when the employee's exact position key is either:

- `accountable_position_key`, or
- `escalated_to_position_key`.

Shared WorkItems, Mission membership, severity, architectural wing placement, and visual proximity do not create an escalation relationship.

## Truth boundaries

Phase 7F explicitly does **not** claim:

- a Board meeting occurred or is occurring
- Board or Owner physical attendance
- physical location or room presence
- locomotion toward a Board Room
- approval, rejection, or authority outcome unless separately proven by canonical decision state
- that severity implies escalation destination or Board attention
- that a human-action request is assigned to a specific employee unless the canonical record says so
- canonical mutation

The architectural Board Room remains presentation architecture only. A routed record may point to `board` even when no roster employee exists with that position key; in that case AIOS displays the exact canonical key rather than fabricating a person.

## Acceptance

Phase 7F requires:

1. pure projection regression proving exact coverage and no severity-based Board inference
2. full design-foundation suite
3. TypeScript and production build
4. Chromium Spatial proof
5. Chromium Structured/reduced-motion proof
6. unavailable-coverage proof with no false zero
7. screenshot inspection
8. full V12 hardening suite including earlier Phase 7A–7E proofs
9. Repository Policy exact-head PASS
10. clean one-commit candidate on the sealed Phase 7E merge before promotion

## Deferred

Phase 7F does not implement explicit completion/resolution event rendering or replay-specific semantic rendering. Those remain successor semantic slices.

# AIOS V2 Phase 13G.1H — Photorealistic Living HQ acceptance target

Status: ACTIVE OWNER VISUAL TARGET
Date: 2026-09-11

## Owner-approved direction

The Living HQ must converge on a premium contemporary-office visual language: realistic architectural proportions, glass meeting rooms, warm timber and stone, dark exposed ceiling infrastructure, linear practical lighting, planted foreground depth, believable desks/chairs/screens/lounge furniture, city-window depth, and restrained translucent HUD surfaces embedded into the world.

The HQ must read first as one coherent workplace and only second as an interface. It must not read as a collection of cards, square rooms, pixel/tile geometry, or a cartoon employee dashboard.

## Workforce finish

Employee presentation must target realistic miniature-human proportions and professional finish. Avoid oversized heads, mascot/baby proportions, flat CSS-stick figures, repeated generic creatures, saturated department-colored bodies, and toy-like furniture. Department/state identity should come primarily from restrained HUD/state cues rather than recoloring the whole person.

Long-term high-fidelity character/world assets may be authored as lightweight optimized 3D assets, but runtime cost is subordinate to AIOS execution, canonical truth, and Cockpit responsiveness. No heavy game-engine runtime is required.

## World composition

The desktop hero view should establish a cinematic office camera with clear foreground/midground/background depth. Operations, Technology, Evidence, Board and every additional canonical department are spatial identities inside one world. Smaller/new departments use modular neighborhoods rather than new card containers.

Mission/Evidence/Board/department information uses compact glass HUDs or architectural signage anchored to the relevant zone. Large opaque room cards are not the target.

## Canonical dynamics

Real-time means canonical AIOS state change -> Living Organization projection -> scene refresh -> world reaction. Working, blocked, awaiting-owner, queued and completed states remain governed presentation mappings. Cross-department links require canonical handoff/conversation/governed records. Shared Mission membership alone never implies transfer. Board reactions require canonical decision/escalation/human-action evidence.

No random walking, fake meetings, invented occupancy, fake coffee breaks, fake conversation, fake handoff, invented work, or unsupported Board action.

Permanent invariants remain:

- presentationOnly = true
- presenceClaimed = false
- locomotionAllowed = false
- physical character placement is presentation, not a physical-location claim
- Selection changes view focus only; it cannot mutate AIOS.

## Performance order

1. AIOS agent execution and results
2. canonical truth/governance
3. Cockpit responsiveness
4. Living HQ rendering
5. cinematic polish

Visual quality degrades before execution, truth, or responsiveness. Use shared assets/materials, instancing where applicable, LOD, culling, compressed textures, lazy loading, reduced-motion handling, and a lightweight fallback. Ambient effects must remain cheap and non-semantic.

## Acceptance gate

Automated CI is necessary but insufficient. Phase 13G.1H is visually accepted only after fresh desktop and phone browser artifacts demonstrate:

- one coherent premium office world;
- workforce visibly integrated into the workplace;
- substantially more realistic human and furniture finish than the prior CSS/cartoon implementation;
- restrained world-anchored HUDs rather than dominant cards;
- readable canonical state changes without page reload;
- no unsupported truth claims;
- no unacceptable layout overflow or obvious performance regression.

Do not seal Phase 13G.2 solely because tests are green.
/**
 * AIOS V2 — Character Presentation Registry (frontend-only)
 * =========================================================
 *
 * Phase 2C — design/aios-v2-character-registry-fable
 *
 * PRESENTATION ONLY.
 *
 * This registry describes HOW canonical AIOS roles are visually presented
 * (silhouette, wardrobe, motion personality, behavior presentation cues).
 *
 * It MUST NEVER define or redefine WHAT a canonical role is. In particular,
 * these presentation records cannot redefine:
 *
 *   - canonical role
 *   - authority
 *   - reporting line
 *   - WorkItem
 *   - presence
 *   - semantic state
 *   - department
 *
 * Canonical truth for all of the above lives exclusively in the AIOS
 * organization layer (e.g. the canonical organization model that backs
 * `LivingSceneEmployee`). This file contains no backend, API, CSS, or
 * generated-3D-asset content and performs no writes of any kind.
 *
 * Governing documents:
 *   - skills/aios-design/characters/CHARACTER_BIBLE.md
 *   - skills/aios-design/characters/executive-roles.md
 *   - skills/aios-design/characters/specialist-roles.md
 *   - skills/aios-design/characters/animation-states.md
 *   - skills/aios-design/governance/semantic-animation-contract.md
 *
 * > The organization causes the animation. Animation never causes the
 * > organization.  (semantic-animation-contract.md)
 */

/* ------------------------------------------------------------------ */
/* Contract constants                                                  */
/* ------------------------------------------------------------------ */

export const CHARACTER_PRESENTATION_REGISTRY_CONTRACT = Object.freeze({
  registryId: "aios-v2.character-presentation-registry",
  contractVersion: "1.0.0",
  presentationOnly: true,
  presenceClaimed: false,
  canonicalStateWritable: false,
  semanticActivationPolicy: "capability-declaration-only",
  forbiddenRedefinitions: Object.freeze([
    "canonical role",
    "authority",
    "reporting line",
    "WorkItem",
    "presence",
    "semantic state",
    "department",
  ]),
} as const);

export type CharacterForbiddenRedefinition =
  "canonical role" | "authority" | "reporting line" | "WorkItem" | "presence" | "semantic state" | "department";

/* ------------------------------------------------------------------ */
/* Vocabulary (closed unions — strongly typed presentation metadata)   */
/* ------------------------------------------------------------------ */

export type CharacterRoleFamily =
  "executive" | "technology-leadership" | "security" | "regulatory-compliance" | "operations" | "neutral-fallback";

export type CharacterRegistrationKind = "exact-position" | "role-family-fallback" | "neutral-fallback";

export type CharacterSilhouette =
  "tailored-executive" | "architectural-technical" | "evidence-researcher" | "practical-operator" | "neutral-professional";

export type CharacterHeadShape =
  "soft-rounded-adult" | "angular-architectural" | "balanced-oval-adult" | "neutral-professional-adult";

export type CharacterFacialLanguage =
  "calm-measured" | "analytical-alert" | "focused-precise" | "open-collaborative" | "neutral-attentive";

export type CharacterHairLanguage = "neat-contemporary" | "practical-short" | "tidy-researcher" | "simple-professional";

export type CharacterWardrobe =
  "contemporary-tailored-executive" | "architectural-technical-overshirt" | "evidence-research-attire" | "practical-contemporary-operator" | "neutral-professional-attire";

export type CharacterFootwear =
  "polished-executive-shoes" | "modern-technical-shoes" | "practical-research-shoes" | "durable-operator-shoes" | "neutral-professional-shoes";

export type CharacterAccessory =
  "slim-tablet" | "compact-technical-device" | "reading-glasses" | "identity-badge" | "evidence-folder" | "field-organizer" | "none";

export type CharacterSignatureObject =
  "strategy-briefing-folio" | "system-architecture-tablet" | "evidence-source-folder" | "operations-case-tablet" | "neutral-professional-tablet";

export type CharacterPosture =
  "calm-upright" | "kinetic-thinking" | "deliberate-reading" | "ready-collaborative" | "neutral-professional";

export type CharacterGazeBehavior =
  "steady-room-aware" | "focused-scan" | "detail-anchored" | "team-oriented" | "neutral-attentive";

export type CharacterMotionPersonality =
  "slower-deliberate" | "quicker-analytical" | "precise-methodical" | "brisk-practical" | "neutral-steady";

export type CharacterRigClass = "rig-hero-humanoid-v1" | "rig-standard-humanoid-v1";

export type CharacterLodClass = "lod-hero" | "lod-standard" | "lod-background";

export type CharacterAnimationSetKey = `aios-v2:animation-set:${string}`;

export type CharacterAmbientGesture =
  "breathe" | "blink" | "glance" | "stretch" | "local-desk-gestures" | "tablet-interaction" | "coffee" | "local-walking";

export type CharacterGestureCue = CharacterAmbientGesture |
  "measured-hand-emphasis" | "analytical-hand-emphasis" | "evidence-comparison" | "source-reading" |
  "system-surface-interaction" | "case-object-carry" | "collaborative-stance" | "calm-waiting" |
  "attention-posture" | "brief-transfer-emphasis" | "calm-settle" | "research-table-interaction";

export type CharacterSemanticAnimationCapability =
  "handoff" | "governed-conversation" | "blocker-response" | "owner-escalation" | "board-interaction" | "completion";

export type CharacterBehaviorActivationPolicy = "ambient-presentation-only" | "requires-canonical-state-input";

/* ------------------------------------------------------------------ */
/* Structural record types                                             */
/* ------------------------------------------------------------------ */

export interface CharacterBehaviorProfile {
  readonly summary: string;
  readonly cues: readonly CharacterGestureCue[];
  readonly activationPolicy: CharacterBehaviorActivationPolicy;
}

export interface CharacterReducedMotionEquivalent {
  readonly summary: string;
  readonly mode: "posture-and-state-change-only";
  readonly forbidsLongTravelAnimation: true;
}

export type CharacterRegistration =
  | { readonly kind: "exact-position"; readonly canonicalPositionKey: string }
  | { readonly kind: "role-family-fallback"; readonly roleFamily: Exclude<CharacterRoleFamily, "neutral-fallback">; readonly presentationPositionKey: string }
  | { readonly kind: "neutral-fallback"; readonly requestedPositionKey?: string };

export interface CharacterPresentationRecord {
  readonly registration: CharacterRegistration;
  readonly canonicalPositionKey: string | null;
  readonly roleFamily: CharacterRoleFamily;
  readonly silhouette: CharacterSilhouette;
  readonly headShape: CharacterHeadShape;
  readonly facialLanguage: CharacterFacialLanguage;
  readonly hairLanguage: CharacterHairLanguage;
  readonly wardrobe: CharacterWardrobe;
  readonly footwear: CharacterFootwear;
  readonly accessories: readonly CharacterAccessory[];
  readonly signatureObject: CharacterSignatureObject;
  readonly defaultPosture: CharacterPosture;
  readonly gazeBehavior: CharacterGazeBehavior;
  readonly locomotionPersonality: CharacterMotionPersonality;
  readonly idleBehavior: CharacterBehaviorProfile;
  readonly workBehavior: CharacterBehaviorProfile;
  readonly reviewBehavior: CharacterBehaviorProfile;
  readonly waitingBehavior: CharacterBehaviorProfile;
  readonly blockerBehavior: CharacterBehaviorProfile;
  readonly conversationBehavior: CharacterBehaviorProfile;
  readonly authorityBehavior: CharacterBehaviorProfile;
  readonly handoffBehavior: CharacterBehaviorProfile;
  readonly completionBehavior: CharacterBehaviorProfile;
  readonly reducedMotionEquivalent: CharacterReducedMotionEquivalent;
  readonly accessibilityDescription: string;
  readonly lodClass: CharacterLodClass;
  readonly rigClass: CharacterRigClass;
  readonly animationSetKey: CharacterAnimationSetKey;
  readonly supportedSemanticAnimationCapabilities: readonly CharacterSemanticAnimationCapability[];
  readonly presentationOnly: true;
  readonly presenceClaimed: false;
  readonly canonicalStateWritable: false;
}

export interface CharacterPresentationRegistry {
  readonly registryId: string;
  readonly contractVersion: string;
  readonly presentationOnly: true;
  readonly records: readonly CharacterPresentationRecord[];
  readonly notes: readonly string[];
}

function freezePresentationRecord(record: CharacterPresentationRecord): CharacterPresentationRecord {
  Object.freeze(record.registration);
  Object.freeze(record.accessories);
  Object.freeze(record.supportedSemanticAnimationCapabilities);
  Object.freeze(record.reducedMotionEquivalent);
  for (const behavior of [
    record.idleBehavior,
    record.workBehavior,
    record.reviewBehavior,
    record.waitingBehavior,
    record.blockerBehavior,
    record.conversationBehavior,
    record.authorityBehavior,
    record.handoffBehavior,
    record.completionBehavior,
  ]) {
    Object.freeze(behavior.cues);
    Object.freeze(behavior);
  }
  return Object.freeze(record);
}

/* ------------------------------------------------------------------ */
/* Hard invariants                                                     */
/* ------------------------------------------------------------------ */

export const CHARACTER_PRESENTATION_INVARIANTS = Object.freeze({
  registryCannotRedefine: CHARACTER_PRESENTATION_REGISTRY_CONTRACT.forbiddenRedefinitions,
  registryCannotActivateSemanticAnimation: true,
  semanticActivationRequiresCanonicalInputsElsewhere: true,
  ambientBehaviorMayNotClaim: Object.freeze([
    "canonical work",
    "physical presence",
    "conversation",
    "handoff",
    "Mission collaboration",
    "authority action",
  ]),
} as const);

const BEHAVIOR_AMBIENT: CharacterBehaviorActivationPolicy = "ambient-presentation-only";
const BEHAVIOR_CANONICAL: CharacterBehaviorActivationPolicy = "requires-canonical-state-input";

/* ------------------------------------------------------------------ */
/* Hero archetype 1 — CEO (exact canonical position key: "ceo")        */
/* ------------------------------------------------------------------ */

const CEO_PRESENTATION = freezePresentationRecord({
  registration: { kind: "exact-position", canonicalPositionKey: "ceo" },
  canonicalPositionKey: "ceo",
  roleFamily: "executive",
  silhouette: "tailored-executive",
  headShape: "soft-rounded-adult",
  facialLanguage: "calm-measured",
  hairLanguage: "neat-contemporary",
  wardrobe: "contemporary-tailored-executive",
  footwear: "polished-executive-shoes",
  accessories: ["identity-badge"],
  signatureObject: "strategy-briefing-folio",
  defaultPosture: "calm-upright",
  gazeBehavior: "steady-room-aware",
  locomotionPersonality: "slower-deliberate",
  idleBehavior: {
    summary: "Calm attentive idle with slow breathing, blinks and brief room glances; measured local desk gestures only.",
    cues: ["breathe", "blink", "glance", "local-desk-gestures"],
    activationPolicy: BEHAVIOR_AMBIENT,
  },
  workBehavior: {
    summary: "When a supported working state is canonical, presents calm strategy review over the briefing folio.",
    cues: ["measured-hand-emphasis", "tablet-interaction"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reviewBehavior: {
    summary: "Presents unhurried briefing comparison when a supported review state is canonical.",
    cues: ["measured-hand-emphasis", "source-reading"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  waitingBehavior: {
    summary: "Calm upright waiting posture when a supported waiting state is canonical; no fidget theatrics.",
    cues: ["calm-waiting", "breathe"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  blockerBehavior: {
    summary: "Controlled attention posture toward a canonically supported blocker; never performs distress.",
    cues: ["attention-posture"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  conversationBehavior: {
    summary: "Orients toward governed conversation participants when a supported conversation exists.",
    cues: ["collaborative-stance"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  authorityBehavior: {
    summary: "Calm measured emphasis during canonically supported authority presentation moments; never presents approval or rejection before a recorded human decision and never impersonates the Board.",
    cues: ["measured-hand-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  handoffBehavior: {
    summary: "Bounded sender-receiver emphasis only when a supported handoff event provides canonical inputs.",
    cues: ["brief-transfer-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  completionBehavior: {
    summary: "Quiet settle-and-close posture only when a supported completion state is canonical.",
    cues: ["calm-settle"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reducedMotionEquivalent: {
    summary: "Static calm upright posture with brief emphasis changes instead of motion sequences.",
    mode: "posture-and-state-change-only",
    forbidsLongTravelAnimation: true,
  },
  accessibilityDescription: "Stylized miniature adult executive in contemporary tailoring holding a strategy briefing folio; reads as a calm senior company leader through upright posture and slow, measured pacing; all live state signals are conveyed by accessible UI rather than by this figure.",
  lodClass: "lod-hero",
  rigClass: "rig-hero-humanoid-v1",
  animationSetKey: "aios-v2:animation-set:hero-ceo",
  supportedSemanticAnimationCapabilities: ["handoff", "governed-conversation", "blocker-response", "board-interaction", "completion"],
  presentationOnly: true,
  presenceClaimed: false,
  canonicalStateWritable: false,
} as const);

/* ------------------------------------------------------------------ */
/* Hero archetype 2 — CTO (exact canonical position key: "cto")        */
/* ------------------------------------------------------------------ */

const CTO_PRESENTATION = freezePresentationRecord({
  registration: { kind: "exact-position", canonicalPositionKey: "cto" },
  canonicalPositionKey: "cto",
  roleFamily: "technology-leadership",
  silhouette: "architectural-technical",
  headShape: "angular-architectural",
  facialLanguage: "analytical-alert",
  hairLanguage: "practical-short",
  wardrobe: "architectural-technical-overshirt",
  footwear: "modern-technical-shoes",
  accessories: ["identity-badge", "compact-technical-device"],
  signatureObject: "system-architecture-tablet",
  defaultPosture: "kinetic-thinking",
  gazeBehavior: "focused-scan",
  locomotionPersonality: "quicker-analytical",
  idleBehavior: {
    summary: "Attentive idle with quicker analytical local gestures and brief glances at the compact technical device.",
    cues: ["breathe", "blink", "glance", "local-desk-gestures"],
    activationPolicy: BEHAVIOR_AMBIENT,
  },
  workBehavior: {
    summary: "When a supported working state is canonical, presents system-surface interaction on the architecture tablet.",
    cues: ["system-surface-interaction", "analytical-hand-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reviewBehavior: {
    summary: "Presents fast structured diagram comparison when a supported review state is canonical.",
    cues: ["evidence-comparison", "analytical-hand-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  waitingBehavior: {
    summary: "Kinetic thinking stance held in place when a supported waiting state is canonical.",
    cues: ["calm-waiting", "breathe"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  blockerBehavior: {
    summary: "Sharp but controlled attention posture toward a canonically supported blocker; never performs panic.",
    cues: ["attention-posture"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  conversationBehavior: {
    summary: "Orients toward governed conversation participants with engaged analytical stance when supported.",
    cues: ["collaborative-stance"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  authorityBehavior: {
    summary: "Quicker analytical emphasis during canonically supported authority presentation moments; never presents approvals and never overrides governance outcomes visually.",
    cues: ["analytical-hand-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  handoffBehavior: {
    summary: "Bounded sender-receiver emphasis only when a supported handoff event provides canonical inputs.",
    cues: ["brief-transfer-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  completionBehavior: {
    summary: "Brief settle posture only when a supported completion state is canonical.",
    cues: ["calm-settle"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reducedMotionEquivalent: {
    summary: "Static kinetic-thinking posture with brief emphasis changes instead of motion sequences.",
    mode: "posture-and-state-change-only",
    forbidsLongTravelAnimation: true,
  },
  accessibilityDescription: "Stylized miniature adult technologist in an architectural overshirt with a compact device on the belt and an architecture tablet; reads as an analytical technical leader through quick, precise gesture rhythm and system-surface focus; all live state signals are conveyed by accessible UI rather than by this figure.",
  lodClass: "lod-hero",
  rigClass: "rig-hero-humanoid-v1",
  animationSetKey: "aios-v2:animation-set:hero-cto",
  supportedSemanticAnimationCapabilities: ["handoff", "governed-conversation", "blocker-response", "completion"],
  presentationOnly: true,
  presenceClaimed: false,
  canonicalStateWritable: false,
} as const);

/* ------------------------------------------------------------------ */
/* Hero archetype 3 — Regulatory / Compliance (role-family fallback)   */
/* ------------------------------------------------------------------ */

const REGULATORY_COMPLIANCE_FAMILY_PRESENTATION = freezePresentationRecord({
  registration: { kind: "role-family-fallback", roleFamily: "regulatory-compliance", presentationPositionKey: "role-family:regulatory-compliance" },
  canonicalPositionKey: null,
  roleFamily: "regulatory-compliance",
  silhouette: "evidence-researcher",
  headShape: "balanced-oval-adult",
  facialLanguage: "focused-precise",
  hairLanguage: "tidy-researcher",
  wardrobe: "evidence-research-attire",
  footwear: "practical-research-shoes",
  accessories: ["reading-glasses", "evidence-folder", "identity-badge"],
  signatureObject: "evidence-source-folder",
  defaultPosture: "deliberate-reading",
  gazeBehavior: "detail-anchored",
  locomotionPersonality: "precise-methodical",
  idleBehavior: {
    summary: "Quiet precise idle with occasional glances over reading glasses and small source-checking gestures.",
    cues: ["breathe", "blink", "glance", "local-desk-gestures"],
    activationPolicy: BEHAVIOR_AMBIENT,
  },
  workBehavior: {
    summary: "When a supported working state is canonical, presents careful source reading and annotation at the research table.",
    cues: ["source-reading", "research-table-interaction"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reviewBehavior: {
    summary: "Presents side-by-side evidence comparison when a supported review state is canonical.",
    cues: ["evidence-comparison", "source-reading", "research-table-interaction"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  waitingBehavior: {
    summary: "Deliberate reading posture held patiently when a supported waiting state is canonical.",
    cues: ["calm-waiting", "breathe"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  blockerBehavior: {
    summary: "Precise attention posture toward a canonically supported blocker; flags visually without alarm theatrics.",
    cues: ["attention-posture"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  conversationBehavior: {
    summary: "Orients toward governed conversation participants with careful, document-anchored stance when supported.",
    cues: ["collaborative-stance"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  authorityBehavior: {
    summary: "Deliberate documentation emphasis during canonically supported authority presentation moments; never issues approvals visually and never resolves escalations on its own.",
    cues: ["measured-hand-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  handoffBehavior: {
    summary: "Bounded sender-receiver emphasis only when a supported handoff event provides canonical inputs.",
    cues: ["brief-transfer-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  completionBehavior: {
    summary: "Orderly folder-close settle only when a supported completion state is canonical.",
    cues: ["calm-settle"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reducedMotionEquivalent: {
    summary: "Static deliberate-reading posture with brief emphasis changes instead of motion sequences.",
    mode: "posture-and-state-change-only",
    forbidsLongTravelAnimation: true,
  },
  accessibilityDescription: "Stylized miniature adult researcher in tidy evidence-review attire with reading glasses and a source folder; reads as a deliberate compliance and regulatory specialist through precise, comparison-focused gestures; all live state signals are conveyed by accessible UI rather than by this figure.",
  lodClass: "lod-standard",
  rigClass: "rig-standard-humanoid-v1",
  animationSetKey: "aios-v2:animation-set:family-regulatory-compliance",
  supportedSemanticAnimationCapabilities: ["handoff", "governed-conversation", "blocker-response", "completion"],
  presentationOnly: true,
  presenceClaimed: false,
  canonicalStateWritable: false,
} as const);

/* ------------------------------------------------------------------ */
/* Hero archetype 4 — Operations (role-family fallback)                */
/* ------------------------------------------------------------------ */

const OPERATIONS_FAMILY_PRESENTATION = freezePresentationRecord({
  registration: { kind: "role-family-fallback", roleFamily: "operations", presentationPositionKey: "role-family:operations" },
  canonicalPositionKey: null,
  roleFamily: "operations",
  silhouette: "practical-operator",
  headShape: "soft-rounded-adult",
  facialLanguage: "open-collaborative",
  hairLanguage: "simple-professional",
  wardrobe: "practical-contemporary-operator",
  footwear: "durable-operator-shoes",
  accessories: ["identity-badge", "field-organizer", "slim-tablet"],
  signatureObject: "operations-case-tablet",
  defaultPosture: "ready-collaborative",
  gazeBehavior: "team-oriented",
  locomotionPersonality: "brisk-practical",
  idleBehavior: {
    summary: "Light practical idle with slightly higher local motion frequency: local walking loops near the desk, tablet checks and a coffee cue.",
    cues: ["breathe", "blink", "glance", "local-walking", "tablet-interaction", "coffee"],
    activationPolicy: BEHAVIOR_AMBIENT,
  },
  workBehavior: {
    summary: "When a supported working state is canonical, presents case handling on the operations tablet with collaborative stance.",
    cues: ["case-object-carry", "collaborative-stance"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reviewBehavior: {
    summary: "Presents quick case-evidence comparison when a supported review state is canonical.",
    cues: ["evidence-comparison", "tablet-interaction"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  waitingBehavior: {
    summary: "Ready collaborative stance held in place when a supported waiting state is canonical.",
    cues: ["calm-waiting", "breathe"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  blockerBehavior: {
    summary: "Clear attention posture toward a canonically supported blocker; flags visually without alarm theatrics.",
    cues: ["attention-posture"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  conversationBehavior: {
    summary: "Orients toward governed conversation participants with an open, team-oriented stance when supported.",
    cues: ["collaborative-stance"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  authorityBehavior: {
    summary: "Efficient coordinating emphasis during canonically supported authority presentation moments; never resolves governance decisions visually and never approves on behalf of others.",
    cues: ["measured-hand-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  handoffBehavior: {
    summary: "Bounded sender-receiver emphasis only when a supported handoff event provides canonical inputs.",
    cues: ["brief-transfer-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  completionBehavior: {
    summary: "Brief case-close settle only when a supported completion state is canonical.",
    cues: ["calm-settle"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reducedMotionEquivalent: {
    summary: "Static ready-collaborative posture with brief emphasis changes instead of motion sequences.",
    mode: "posture-and-state-change-only",
    forbidsLongTravelAnimation: true,
  },
  accessibilityDescription: "Stylized miniature adult operations coordinator in practical contemporary clothing with a field organizer and a slim case tablet; reads as a mobile, collaborative operations specialist through brisk local pacing and team-oriented gaze; all live state signals are conveyed by accessible UI rather than by this figure.",
  lodClass: "lod-standard",
  rigClass: "rig-standard-humanoid-v1",
  animationSetKey: "aios-v2:animation-set:family-operations",
  supportedSemanticAnimationCapabilities: ["handoff", "governed-conversation", "blocker-response", "completion"],
  presentationOnly: true,
  presenceClaimed: false,
  canonicalStateWritable: false,
} as const);

/* ------------------------------------------------------------------ */
/* Registry                                                            */
/* ------------------------------------------------------------------ */

const REGISTRY_NOTES: readonly string[] = Object.freeze([
  "Presentation records never redefine canonical role, authority, reporting line, WorkItem, presence, semantic state, or department.",
  "Exact-position registrations exist only for position keys that are canonically guaranteed in this phase: 'ceo' and 'cto'.",
  "Role-family fallback records use presentation-only placeholder keys prefixed with 'role-family:' and never assert a canonical position key.",
  "Records may only DECLARE supported semantic animation capabilities; activation always requires canonical inputs elsewhere.",
  "Ambient cues are presentation-only and never produce semantic data attributes or canonical claims.",
]);

export const characterPresentationRegistry: CharacterPresentationRegistry = Object.freeze({
  registryId: CHARACTER_PRESENTATION_REGISTRY_CONTRACT.registryId,
  contractVersion: CHARACTER_PRESENTATION_REGISTRY_CONTRACT.contractVersion,
  presentationOnly: true,
  records: Object.freeze([
    CEO_PRESENTATION,
    CTO_PRESENTATION,
    REGULATORY_COMPLIANCE_FAMILY_PRESENTATION,
    OPERATIONS_FAMILY_PRESENTATION,
  ]),
  notes: REGISTRY_NOTES,
} as const);

/* ------------------------------------------------------------------ */
/* Indexes (module-private, immutable, deterministic)                  */
/* ------------------------------------------------------------------ */

const exactPositionIndexMutable = new Map<string, CharacterPresentationRecord>();
const roleFamilyFallbackIndexMutable = new Map<string, CharacterPresentationRecord>();

for (const record of characterPresentationRegistry.records) {
  if (record.registration.kind === "exact-position") {
    exactPositionIndexMutable.set(record.registration.canonicalPositionKey, record);
  } else if (record.registration.kind === "role-family-fallback") {
    roleFamilyFallbackIndexMutable.set(record.registration.roleFamily, record);
  }
}

const exactPositionIndex: ReadonlyMap<string, CharacterPresentationRecord> = exactPositionIndexMutable;
const roleFamilyFallbackIndex: ReadonlyMap<string, CharacterPresentationRecord> = roleFamilyFallbackIndexMutable;

/* ------------------------------------------------------------------ */
/* Neutral professional fallback                                       */
/* ------------------------------------------------------------------ */

const NEUTRAL_PRESENTATION_TEMPLATE = freezePresentationRecord({
  registration: { kind: "neutral-fallback" },
  canonicalPositionKey: null,
  roleFamily: "neutral-fallback",
  silhouette: "neutral-professional",
  headShape: "neutral-professional-adult",
  facialLanguage: "neutral-attentive",
  hairLanguage: "simple-professional",
  wardrobe: "neutral-professional-attire",
  footwear: "neutral-professional-shoes",
  accessories: ["none"],
  signatureObject: "neutral-professional-tablet",
  defaultPosture: "neutral-professional",
  gazeBehavior: "neutral-attentive",
  locomotionPersonality: "neutral-steady",
  idleBehavior: {
    summary: "Plain attentive idle with breathing and blinking only.",
    cues: ["breathe", "blink", "glance"],
    activationPolicy: BEHAVIOR_AMBIENT,
  },
  workBehavior: {
    summary: "Plain surface focus when a supported working state is canonical.",
    cues: ["local-desk-gestures"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reviewBehavior: {
    summary: "Plain document focus when a supported review state is canonical.",
    cues: ["source-reading"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  waitingBehavior: {
    summary: "Plain standing wait when a supported waiting state is canonical.",
    cues: ["calm-waiting", "breathe"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  blockerBehavior: {
    summary: "Plain attention posture toward a canonically supported blocker.",
    cues: ["attention-posture"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  conversationBehavior: {
    summary: "Plain orientation toward governed conversation participants when supported.",
    cues: ["collaborative-stance"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  authorityBehavior: {
    summary: "Neutral stillness during canonically supported authority presentation moments; never presents decisions.",
    cues: [],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  handoffBehavior: {
    summary: "Bounded sender-receiver emphasis only when a supported handoff event provides canonical inputs.",
    cues: ["brief-transfer-emphasis"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  completionBehavior: {
    summary: "Plain settle only when a supported completion state is canonical.",
    cues: ["calm-settle"],
    activationPolicy: BEHAVIOR_CANONICAL,
  },
  reducedMotionEquivalent: {
    summary: "Static neutral posture with brief emphasis changes instead of motion sequences.",
    mode: "posture-and-state-change-only",
    forbidsLongTravelAnimation: true,
  },
  accessibilityDescription: "Stylized miniature adult professional in neutral contemporary clothing; deliberately unmarked so that role specifics come from accessible UI labels; all live state signals are conveyed by accessible UI rather than by this figure.",
  lodClass: "lod-standard",
  rigClass: "rig-standard-humanoid-v1",
  animationSetKey: "aios-v2:animation-set:neutral-professional",
  supportedSemanticAnimationCapabilities: [],
  presentationOnly: true,
  presenceClaimed: false,
  canonicalStateWritable: false,
} as const);

export function createNeutralPresentationFallback(positionKey: string): CharacterPresentationRecord {
  return freezePresentationRecord({
    ...NEUTRAL_PRESENTATION_TEMPLATE,
    registration: Object.freeze({ kind: "neutral-fallback", requestedPositionKey: positionKey }),
    animationSetKey: "aios-v2:animation-set:neutral-professional" as CharacterAnimationSetKey,
  });
}

/* ------------------------------------------------------------------ */
/* Resolvers                                                           */
/* ------------------------------------------------------------------ */

export function getCharacterPresentationForPosition(positionKey: string): CharacterPresentationRecord {
  const exact = exactPositionIndex.get(positionKey);
  if (exact) {
    return exact;
  }
  return createNeutralPresentationFallback(positionKey);
}

export function getCharacterPresentationForRoleFamily(roleFamily: CharacterRoleFamily): CharacterPresentationRecord {
  if (roleFamily === "neutral-fallback") {
    return createNeutralPresentationFallback("role-family:neutral-fallback");
  }
  const fallback = roleFamilyFallbackIndex.get(roleFamily);
  if (fallback) {
    return fallback;
  }
  return createNeutralPresentationFallback(`role-family:${roleFamily}`);
}

export function hasExactPositionRegistration(positionKey: string): boolean {
  return exactPositionIndex.has(positionKey);
}

export interface PreferredPresentationInput {
  readonly positionKey?: string | null;
  readonly roleFamily?: CharacterRoleFamily | null;
}

export function getPreferredCharacterPresentation(input: PreferredPresentationInput): CharacterPresentationRecord {
  if (input.positionKey) {
    const exact = exactPositionIndex.get(input.positionKey);
    if (exact) {
      return exact;
    }
  }
  if (input.roleFamily && input.roleFamily !== "neutral-fallback") {
    const fallback = roleFamilyFallbackIndex.get(input.roleFamily);
    if (fallback) {
      return fallback;
    }
  }
  return createNeutralPresentationFallback(input.positionKey ?? "unknown");
}

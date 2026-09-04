/**
 * AIOS V2 — Phase 2L
 * Living HQ Atmosphere & Lighting Presentation V1
 *
 * Presentation-only lighting contract for the Phase 2I Living HQ.
 * The five Phase 2I wings are selectable. Decision Chamber and Collaboration
 * Deck remain decorative architectural fields and can never become selection.
 */

export const HQ_ATMOSPHERE_CONTRACT = deepFreeze({
  registryId: "aios-v2.hq-atmosphere-presentation",
  contractVersion: "1.1.0",
  presentationOnly: true,
  canonicalStateWritable: false,
  semanticAnimationActive: false,
} as const);

export type V2HqAtmosphereTheme =
  | "neutral"
  | "focused"
  | "low-stimulation"
  | "presentation";

export type V2HqAtmosphereEmphasis = "calm" | "balanced" | "defined";

export type V2HqAtmosphereZone =
  | "executive"
  | "regulatory"
  | "atrium"
  | "technology"
  | "operations";

export type V2HqAtmosphereDecorativeField =
  | "decision-chamber"
  | "collaboration-deck";

export type V2HqAtmosphereDepthClass =
  | "depth-architectural-balanced"
  | "depth-architectural-defined"
  | "depth-architectural-flat"
  | "depth-architectural-layered";

export type V2HqAtmosphereIlluminationClass =
  | "illumination-ambient-soft"
  | "illumination-directional-soft"
  | "illumination-dim-even"
  | "illumination-presentation-soft";

export type V2HqAtmosphereContrastClass =
  | "contrast-balanced"
  | "contrast-elevated"
  | "contrast-reduced"
  | "contrast-refined-elevated";

export type V2HqAtmosphereGlassClass =
  | "glass-subtle"
  | "glass-defined"
  | "glass-minimal"
  | "glass-polished";

export type V2HqAtmosphereFloorGlowClass =
  | "floor-glow-even"
  | "floor-glow-focused"
  | "floor-glow-muted"
  | "floor-glow-presentation-even";

export type V2HqAtmosphereZoneIllumination =
  | "warm-neutral-precision"
  | "cool-teal-clarity"
  | "cool-metallic-restraint"
  | "warm-practical-neutral"
  | "balanced-central-illumination";

export type V2HqAtmosphereDecorativeIllumination =
  | "formal-restrained-contrast"
  | "soft-neutral-shared-light";

export type V2HqAtmosphereAccentClass =
  | "accent-warm-neutral"
  | "accent-cool-teal"
  | "accent-cool-metallic"
  | "accent-warm-practical"
  | "accent-balanced-central"
  | "accent-formal-contrast"
  | "accent-soft-shared";

export type V2HqAtmosphereIntensity = "low" | "medium" | "high";

export interface V2HqAtmosphereTruth {
  readonly canonicalStateWritable: false;
  readonly physicalPresenceClaimed: false;
  readonly physicalLocationClaimed: false;
  readonly workActivityClaimed: false;
  readonly urgencyClaimed: false;
  readonly collaborationClaimed: false;
  readonly conversationClaimed: false;
  readonly semanticAnimationActive: false;
}

export interface V2HqAtmosphereEnvironment {
  readonly depthClass: V2HqAtmosphereDepthClass;
  readonly illuminationClass: V2HqAtmosphereIlluminationClass;
  readonly contrastClass: V2HqAtmosphereContrastClass;
  readonly glassClass: V2HqAtmosphereGlassClass;
  readonly floorGlowClass: V2HqAtmosphereFloorGlowClass;
}

export interface V2HqAtmosphereZonePresentation {
  readonly zone: V2HqAtmosphereZone;
  readonly illumination: V2HqAtmosphereZoneIllumination;
  readonly accent: V2HqAtmosphereAccentClass;
  readonly intensity: V2HqAtmosphereIntensity;
  readonly emphasis: V2HqAtmosphereEmphasis;
  readonly selected: boolean;
  readonly selectedHalo: "none" | "soft-halo";
  readonly outline: "none" | "defined-outline";
  readonly selectionEligible: true;
}

export interface V2HqAtmosphereDecorativePresentation {
  readonly field: V2HqAtmosphereDecorativeField;
  readonly illumination: V2HqAtmosphereDecorativeIllumination;
  readonly accent: V2HqAtmosphereAccentClass;
  readonly intensity: V2HqAtmosphereIntensity;
  readonly selected: false;
  readonly selectionEligible: false;
}

export interface V2HqAtmosphereMotion {
  readonly mode: "transition-only" | "opacity-only" | "static";
  readonly hoverTransitionMs: number;
  readonly selectionTransitionMs: number;
  readonly ambientAnimation: "none";
  readonly parallax: false;
  readonly glowSweep: false;
}

export interface V2HqAtmosphereReducedMotion {
  readonly enabled: boolean;
  readonly transformAtmosphereRemoved: boolean;
  readonly parallaxRemoved: boolean;
  readonly glowSweepRemoved: boolean;
  readonly staticSelectionContrast: boolean;
  readonly informationLoss: false;
}

export interface V2HqAtmospherePresentationDescriptor {
  readonly kind: "hq-atmosphere-presentation";
  readonly contract: Readonly<{ registryId: string; contractVersion: string }>;
  readonly theme: V2HqAtmosphereTheme;
  readonly emphasis: V2HqAtmosphereEmphasis;
  readonly selectedZone: V2HqAtmosphereZone | null;
  readonly presentationOnly: true;
  readonly truth: V2HqAtmosphereTruth;
  readonly environment: V2HqAtmosphereEnvironment;
  readonly zones: readonly V2HqAtmosphereZonePresentation[];
  readonly decorativeFields: readonly V2HqAtmosphereDecorativePresentation[];
  readonly motion: V2HqAtmosphereMotion;
  readonly reducedMotion: V2HqAtmosphereReducedMotion;
  readonly limitations: readonly string[];
}

export interface V2HqAtmospherePresentationInput {
  readonly theme: V2HqAtmosphereTheme;
  readonly selectedZone: V2HqAtmosphereZone | null;
  readonly emphasis: V2HqAtmosphereEmphasis;
  readonly reducedMotion: boolean;
}

function deepFreeze<T>(value: T): T {
  if (value === null || typeof value !== "object" || Object.isFrozen(value)) {
    return value;
  }
  Object.freeze(value);
  const container = value as unknown as Record<PropertyKey, unknown>;
  for (const key of Reflect.ownKeys(container)) {
    deepFreeze(container[key]);
  }
  return value;
}

export const HQ_ATMOSPHERE_THEMES: readonly V2HqAtmosphereTheme[] = deepFreeze([
  "neutral",
  "focused",
  "low-stimulation",
  "presentation",
] as const);

export const HQ_ATMOSPHERE_EMPHASIS_MODES: readonly V2HqAtmosphereEmphasis[] =
  deepFreeze(["calm", "balanced", "defined"] as const);

export const HQ_ATMOSPHERE_ZONES: readonly V2HqAtmosphereZone[] = deepFreeze([
  "executive",
  "regulatory",
  "atrium",
  "technology",
  "operations",
] as const);

export const HQ_ATMOSPHERE_DECORATIVE_FIELDS: readonly V2HqAtmosphereDecorativeField[] =
  deepFreeze(["decision-chamber", "collaboration-deck"] as const);

const THEME_ENVIRONMENTS: Readonly<
  Record<V2HqAtmosphereTheme, V2HqAtmosphereEnvironment>
> = deepFreeze({
  neutral: {
    depthClass: "depth-architectural-balanced",
    illuminationClass: "illumination-ambient-soft",
    contrastClass: "contrast-balanced",
    glassClass: "glass-subtle",
    floorGlowClass: "floor-glow-even",
  },
  focused: {
    depthClass: "depth-architectural-defined",
    illuminationClass: "illumination-directional-soft",
    contrastClass: "contrast-elevated",
    glassClass: "glass-defined",
    floorGlowClass: "floor-glow-focused",
  },
  "low-stimulation": {
    depthClass: "depth-architectural-flat",
    illuminationClass: "illumination-dim-even",
    contrastClass: "contrast-reduced",
    glassClass: "glass-minimal",
    floorGlowClass: "floor-glow-muted",
  },
  presentation: {
    depthClass: "depth-architectural-layered",
    illuminationClass: "illumination-presentation-soft",
    contrastClass: "contrast-refined-elevated",
    glassClass: "glass-polished",
    floorGlowClass: "floor-glow-presentation-even",
  },
});

const ZONE_SPECS = deepFreeze({
  executive: {
    zone: "executive",
    illumination: "warm-neutral-precision",
    accent: "accent-warm-neutral",
    baseIntensity: "medium",
  },
  regulatory: {
    zone: "regulatory",
    illumination: "cool-teal-clarity",
    accent: "accent-cool-teal",
    baseIntensity: "low",
  },
  atrium: {
    zone: "atrium",
    illumination: "balanced-central-illumination",
    accent: "accent-balanced-central",
    baseIntensity: "high",
  },
  technology: {
    zone: "technology",
    illumination: "cool-metallic-restraint",
    accent: "accent-cool-metallic",
    baseIntensity: "low",
  },
  operations: {
    zone: "operations",
    illumination: "warm-practical-neutral",
    accent: "accent-warm-practical",
    baseIntensity: "medium",
  },
} satisfies Record<
  V2HqAtmosphereZone,
  {
    readonly zone: V2HqAtmosphereZone;
    readonly illumination: V2HqAtmosphereZoneIllumination;
    readonly accent: V2HqAtmosphereAccentClass;
    readonly baseIntensity: V2HqAtmosphereIntensity;
  }
>);

const DECORATIVE_SPECS = deepFreeze({
  "decision-chamber": {
    field: "decision-chamber",
    illumination: "formal-restrained-contrast",
    accent: "accent-formal-contrast",
    intensity: "low",
    selected: false,
    selectionEligible: false,
  },
  "collaboration-deck": {
    field: "collaboration-deck",
    illumination: "soft-neutral-shared-light",
    accent: "accent-soft-shared",
    intensity: "medium",
    selected: false,
    selectionEligible: false,
  },
} satisfies Record<
  V2HqAtmosphereDecorativeField,
  V2HqAtmosphereDecorativePresentation
>);

function isTheme(value: unknown): value is V2HqAtmosphereTheme {
  return (
    value === "neutral" ||
    value === "focused" ||
    value === "low-stimulation" ||
    value === "presentation"
  );
}

function isEmphasis(value: unknown): value is V2HqAtmosphereEmphasis {
  return value === "calm" || value === "balanced" || value === "defined";
}

function isZone(value: unknown): value is V2HqAtmosphereZone {
  return (
    value === "executive" ||
    value === "regulatory" ||
    value === "atrium" ||
    value === "technology" ||
    value === "operations"
  );
}

function intensityForEmphasis(
  baseIntensity: V2HqAtmosphereIntensity,
  emphasis: V2HqAtmosphereEmphasis,
): V2HqAtmosphereIntensity {
  if (emphasis === "calm") return "low";
  if (emphasis === "defined") return baseIntensity === "low" ? "medium" : "high";
  return baseIntensity;
}

function truthBlock(): V2HqAtmosphereTruth {
  return deepFreeze({
    canonicalStateWritable: false,
    physicalPresenceClaimed: false,
    physicalLocationClaimed: false,
    workActivityClaimed: false,
    urgencyClaimed: false,
    collaborationClaimed: false,
    conversationClaimed: false,
    semanticAnimationActive: false,
  });
}

export function buildV2HqAtmospherePresentation(
  input: V2HqAtmospherePresentationInput,
): V2HqAtmospherePresentationDescriptor {
  const request = input as unknown as
    | {
        readonly theme?: unknown;
        readonly selectedZone?: unknown;
        readonly emphasis?: unknown;
        readonly reducedMotion?: unknown;
      }
    | null
    | undefined;

  const limitations: string[] = [];
  const theme: V2HqAtmosphereTheme = isTheme(request?.theme)
    ? request.theme
    : "neutral";
  if (!isTheme(request?.theme) && request?.theme != null) {
    limitations.push("unknown-theme-treated-as-neutral");
  }

  const emphasis: V2HqAtmosphereEmphasis = isEmphasis(request?.emphasis)
    ? request.emphasis
    : "balanced";
  if (!isEmphasis(request?.emphasis) && request?.emphasis != null) {
    limitations.push("unknown-emphasis-treated-as-balanced");
  }

  const requestedZone = request?.selectedZone;
  const selectedZone: V2HqAtmosphereZone | null =
    requestedZone == null
      ? null
      : isZone(requestedZone)
        ? requestedZone
        : null;
  if (requestedZone != null && !isZone(requestedZone)) {
    limitations.push("unknown-selected-zone-ignored");
  }

  const reducedMotionEnabled = request?.reducedMotion === true;
  if (
    request?.reducedMotion != null &&
    typeof request.reducedMotion !== "boolean"
  ) {
    limitations.push("reduced-motion-flag-not-boolean");
  }

  const zones = deepFreeze(
    HQ_ATMOSPHERE_ZONES.map((zone) => {
      const spec = ZONE_SPECS[zone];
      const selected = zone === selectedZone;
      return deepFreeze({
        zone: spec.zone,
        illumination: spec.illumination,
        accent: spec.accent,
        intensity: intensityForEmphasis(spec.baseIntensity, emphasis),
        emphasis,
        selected,
        selectedHalo: selected ? "soft-halo" : "none",
        outline: selected ? "defined-outline" : "none",
        selectionEligible: true,
      } satisfies V2HqAtmosphereZonePresentation);
    }),
  );

  const decorativeFields = deepFreeze(
    HQ_ATMOSPHERE_DECORATIVE_FIELDS.map((field) =>
      deepFreeze({ ...DECORATIVE_SPECS[field] }),
    ),
  );

  const motion: V2HqAtmosphereMotion = deepFreeze(
    reducedMotionEnabled
      ? theme === "low-stimulation"
        ? {
            mode: "static",
            hoverTransitionMs: 0,
            selectionTransitionMs: 0,
            ambientAnimation: "none",
            parallax: false,
            glowSweep: false,
          }
        : {
            mode: "opacity-only",
            hoverTransitionMs: 120,
            selectionTransitionMs: 150,
            ambientAnimation: "none",
            parallax: false,
            glowSweep: false,
          }
      : {
          mode: "transition-only",
          hoverTransitionMs: 200,
          selectionTransitionMs: 350,
          ambientAnimation: "none",
          parallax: false,
          glowSweep: false,
        },
  );

  const reducedMotion: V2HqAtmosphereReducedMotion = deepFreeze({
    enabled: reducedMotionEnabled,
    transformAtmosphereRemoved: reducedMotionEnabled,
    parallaxRemoved: reducedMotionEnabled,
    glowSweepRemoved: reducedMotionEnabled,
    staticSelectionContrast: reducedMotionEnabled,
    informationLoss: false,
  });

  return deepFreeze({
    kind: "hq-atmosphere-presentation",
    contract: {
      registryId: HQ_ATMOSPHERE_CONTRACT.registryId,
      contractVersion: HQ_ATMOSPHERE_CONTRACT.contractVersion,
    },
    theme,
    emphasis,
    selectedZone,
    presentationOnly: true,
    truth: truthBlock(),
    environment: THEME_ENVIRONMENTS[theme],
    zones,
    decorativeFields,
    motion,
    reducedMotion,
    limitations,
  });
}

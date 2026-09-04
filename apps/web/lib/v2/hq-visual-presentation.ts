/**
 * AIOS V2 — HQ Visual Presentation (Phase 2I)
 *
 * Pure presentation adapter for the Living HQ visual stage.
 * It consumes presentation assignments only and never derives canonical facts.
 */

export const HQ_VISUAL_PRESENTATION_CONTRACT = Object.freeze({
  contractId: "aios-v2.hq-visual-presentation",
  contractVersion: "1.1.0",
  presentationOnly: true,
  physicalLocationClaimed: false,
  presenceClaimed: false,
  canonicalStateWritable: false,
} as const);

export type HqWingKey =
  | "executive"
  | "regulatory"
  | "atrium"
  | "technology"
  | "operations";

export type HqDensity = "sparse" | "standard" | "dense";
export type HqScale = "scale-sm" | "scale-md" | "scale-lg";

export type HqWingMetricInput = {
  readonly wingKey: string;
  readonly departmentCount: number;
  readonly employeeCount: number;
  readonly workItemCount: number;
  readonly activeBlockerCount: number;
};

export type HqWingCharacterInput = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
  readonly presentationWing: HqWingKey | null;
};

export type HqWingVisualCharacter = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
  readonly presentationWing: HqWingKey;
};

export type HqUnplacedVisualCharacter = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
  readonly presentationWing: null;
  readonly limitation: "presentation-wing-unassigned-or-unknown";
  readonly presentationOnly: true;
  readonly physicalLocationClaimed: false;
  readonly presenceClaimed: false;
};

export type HqWingVisualLayout = {
  readonly wingKey: HqWingKey;
  readonly label: string;
  readonly shortLabel: string;
  readonly order: number;
  readonly isHub: boolean;
  readonly density: HqDensity;
  readonly scale: HqScale;
  readonly elevation: number;
  readonly accentClass: string;
  readonly departmentCount: number;
  readonly employeeCount: number;
  readonly workItemCount: number;
  readonly activeBlockerCount: number;
  readonly characters: readonly HqWingVisualCharacter[];
};

export type HqVisualStageLayout = {
  readonly zones: readonly HqWingVisualLayout[];
  readonly hubZone: HqWingVisualLayout;
  readonly unplacedCharacters: readonly HqUnplacedVisualCharacter[];
  readonly totalCharacterCount: number;
  readonly totalUnplacedCharacterCount: number;
  readonly totalWorkItemCount: number;
  readonly totalBlockerCount: number;
  readonly presentationOnly: true;
  readonly physicalLocationClaimed: false;
  readonly presenceClaimed: false;
  readonly canonicalStateWritable: false;
};

export type HqVisualZoneOrderEntry = {
  readonly wingKey: HqWingKey;
  readonly order: number;
};

const WING_ORDER: readonly HqWingKey[] = Object.freeze([
  "executive",
  "regulatory",
  "atrium",
  "technology",
  "operations",
]);

const WING_META: Readonly<
  Record<
    HqWingKey,
    {
      readonly label: string;
      readonly shortLabel: string;
      readonly isHub: boolean;
      readonly elevation: number;
      readonly accentClass: string;
    }
  >
> = Object.freeze({
  executive: Object.freeze({
    label: "Executive Terrace",
    shortLabel: "Executive",
    isHub: false,
    elevation: 3,
    accentClass: "accent-executive",
  }),
  regulatory: Object.freeze({
    label: "Regulatory & Evidence",
    shortLabel: "Regulatory",
    isHub: false,
    elevation: 2,
    accentClass: "accent-regulatory",
  }),
  atrium: Object.freeze({
    label: "Central Mission Hub",
    shortLabel: "Mission Hub",
    isHub: true,
    elevation: 5,
    accentClass: "accent-atrium",
  }),
  technology: Object.freeze({
    label: "Technology & Security",
    shortLabel: "Technology",
    isHub: false,
    elevation: 2,
    accentClass: "accent-technology",
  }),
  operations: Object.freeze({
    label: "Operations Studio",
    shortLabel: "Operations",
    isHub: false,
    elevation: 2,
    accentClass: "accent-operations",
  }),
});

const HUB_KEY: HqWingKey = "atrium";

function safeCount(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.floor(value));
}

function computeDensity(
  departmentCount: number,
  employeeCount: number,
  workItemCount: number,
): HqDensity {
  const load = departmentCount * 3 + employeeCount + workItemCount;
  if (load <= 2) return "sparse";
  if (load <= 10) return "standard";
  return "dense";
}

function computeScale(density: HqDensity, isHub: boolean): HqScale {
  if (isHub) return "scale-lg";
  return density === "sparse" ? "scale-sm" : "scale-md";
}

function metricForKey(
  metrics: readonly HqWingMetricInput[] | undefined,
  wingKey: HqWingKey,
): {
  readonly departmentCount: number;
  readonly employeeCount: number;
  readonly workItemCount: number;
  readonly activeBlockerCount: number;
} {
  const match = metrics?.find((metric) => metric.wingKey === wingKey);
  if (!match) {
    return Object.freeze({
      departmentCount: 0,
      employeeCount: 0,
      workItemCount: 0,
      activeBlockerCount: 0,
    });
  }

  return Object.freeze({
    departmentCount: safeCount(match.departmentCount),
    employeeCount: safeCount(match.employeeCount),
    workItemCount: safeCount(match.workItemCount),
    activeBlockerCount: safeCount(match.activeBlockerCount),
  });
}

function freezePlacedCharacter(
  character: HqWingCharacterInput,
  wingKey: HqWingKey,
): HqWingVisualCharacter {
  return Object.freeze({
    positionKey: character.positionKey,
    title: character.title,
    department: character.department,
    presentationWing: wingKey,
  });
}

function freezeUnplacedCharacter(
  character: HqWingCharacterInput,
): HqUnplacedVisualCharacter {
  return Object.freeze({
    positionKey: character.positionKey,
    title: character.title,
    department: character.department,
    presentationWing: null,
    limitation: "presentation-wing-unassigned-or-unknown",
    presentationOnly: true,
    physicalLocationClaimed: false,
    presenceClaimed: false,
  });
}

function charactersForWing(
  characters: readonly HqWingCharacterInput[] | undefined,
  wingKey: HqWingKey,
): readonly HqWingVisualCharacter[] {
  const filtered = (characters ?? [])
    .filter((character) => character.presentationWing === wingKey)
    .map((character) => freezePlacedCharacter(character, wingKey))
    .sort((a, b) => a.positionKey.localeCompare(b.positionKey));

  return Object.freeze(filtered);
}

function unplacedCharacters(
  characters: readonly HqWingCharacterInput[] | undefined,
): readonly HqUnplacedVisualCharacter[] {
  const unplaced = (characters ?? [])
    .filter(
      (character) =>
        character.presentationWing === null ||
        !isKnownWingKey(String(character.presentationWing)),
    )
    .map(freezeUnplacedCharacter)
    .sort((a, b) => a.positionKey.localeCompare(b.positionKey));

  return Object.freeze(unplaced);
}

export function resolveHqZoneOrder(): readonly HqVisualZoneOrderEntry[] {
  return Object.freeze(
    WING_ORDER.map((wingKey, order) => Object.freeze({ wingKey, order })),
  );
}

export function resolveHqVisualStageLayout(input: {
  readonly metrics?: readonly HqWingMetricInput[];
  readonly characters?: readonly HqWingCharacterInput[];
}): HqVisualStageLayout {
  let totalCharacterCount = 0;
  let totalWorkItemCount = 0;
  let totalBlockerCount = 0;
  let hubZone: HqWingVisualLayout | null = null;

  const zones: HqWingVisualLayout[] = WING_ORDER.map((wingKey, order) => {
    const meta = WING_META[wingKey];
    const metric = metricForKey(input.metrics, wingKey);
    const characters = charactersForWing(input.characters, wingKey);
    const density = computeDensity(
      metric.departmentCount,
      metric.employeeCount,
      metric.workItemCount,
    );

    totalCharacterCount += characters.length;
    totalWorkItemCount += metric.workItemCount;
    totalBlockerCount += metric.activeBlockerCount;

    const zone = Object.freeze({
      wingKey,
      label: meta.label,
      shortLabel: meta.shortLabel,
      order,
      isHub: meta.isHub,
      density,
      scale: computeScale(density, meta.isHub),
      elevation: meta.elevation,
      accentClass: meta.accentClass,
      departmentCount: metric.departmentCount,
      employeeCount: metric.employeeCount,
      workItemCount: metric.workItemCount,
      activeBlockerCount: metric.activeBlockerCount,
      characters,
    }) satisfies HqWingVisualLayout;

    if (meta.isHub) hubZone = zone;
    return zone;
  });

  const frozenZones = Object.freeze(zones);
  const resolvedHub = hubZone ?? frozenZones[2];
  const unplaced = unplacedCharacters(input.characters);

  return Object.freeze({
    zones: frozenZones,
    hubZone: resolvedHub,
    unplacedCharacters: unplaced,
    totalCharacterCount,
    totalUnplacedCharacterCount: unplaced.length,
    totalWorkItemCount,
    totalBlockerCount,
    presentationOnly: true,
    physicalLocationClaimed: false,
    presenceClaimed: false,
    canonicalStateWritable: false,
  });
}

export function isKnownWingKey(value: string): value is HqWingKey {
  return (WING_ORDER as readonly string[]).includes(value);
}

export function getHubWingKey(): HqWingKey {
  return HUB_KEY;
}

export function getWingOrder(): readonly HqWingKey[] {
  return WING_ORDER;
}

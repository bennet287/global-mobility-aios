import type {
  LivingOrganizationScene,
  LivingSceneSmartObject,
} from "./live-organization";

export const LIVING_ORGANIZATION_LENS_KEYS = [
  "organization",
  "mission",
  "flow",
  "risk",
  "autonomy",
  "cost",
  "evidence",
  "blockers",
  "decisions",
  "performance",
  "incident",
] as const;

export type LivingOrganizationLensKey = (typeof LIVING_ORGANIZATION_LENS_KEYS)[number];
export type LivingOrganizationLensAvailability =
  | "available"
  | "partial"
  | "unavailable"
  | "planned";

export type LivingOrganizationLens = {
  key: LivingOrganizationLensKey;
  label: string;
  availability: LivingOrganizationLensAvailability;
  count: number | null;
  summary: string;
  canonicalBasis: string;
};

export const OWNER_LENS_VIEW_COMMANDS = [
  { label: "Show mission work", lens: "mission" },
  { label: "Show routing flow", lens: "flow" },
  { label: "Show open risks", lens: "risk" },
  { label: "Show current blockers", lens: "blockers" },
  { label: "Show Board attention", lens: "decisions" },
  { label: "Show evidence state", lens: "evidence" },
] as const satisfies readonly { label: string; lens: LivingOrganizationLensKey }[];

function smartObject(
  scene: LivingOrganizationScene,
  objectType: string,
): LivingSceneSmartObject | null {
  return scene.deterministic.smart_objects.find((item) => item.object_type === objectType) ?? null;
}

function coverageAvailable(value: string): boolean {
  return !value.startsWith("unavailable_");
}

export function isLivingOrganizationLensSelectable(lens: LivingOrganizationLens): boolean {
  return lens.availability === "available" || lens.availability === "partial";
}

export function isLivingOrganizationLensFocused(
  activeLens: LivingOrganizationLensKey,
  tags: readonly LivingOrganizationLensKey[],
): boolean {
  return activeLens === "organization" || tags.includes(activeLens);
}

export function smartObjectLensTags(objectType: string): readonly LivingOrganizationLensKey[] {
  switch (objectType) {
    case "mission_board":
      return ["mission", "flow"];
    case "evidence_shelf":
    case "regulatory_monitor":
      return ["evidence"];
    case "blocker_wall":
      return ["blockers", "risk"];
    case "board_desk":
      return ["decisions", "risk"];
    case "owner_inbox":
      return ["decisions", "blockers", "risk"];
    case "risk_beacon":
      return ["risk"];
    case "cost_display":
      return ["cost"];
    case "incident_beacon":
      return ["incident"];
    default:
      return [];
  }
}

export function buildLivingOrganizationLenses(
  scene: LivingOrganizationScene,
): LivingOrganizationLens[] {
  const evidence = smartObject(scene, "evidence_shelf");
  const cost = smartObject(scene, "cost_display");
  const incident = smartObject(scene, "incident_beacon");

  return [
    {
      key: "organization",
      label: "Organization",
      availability: "available",
      count: scene.deterministic.employees.length + scene.deterministic.work_items.length,
      summary: "Whole canonical scene projection: people, work, rooms and relationships.",
      canonicalBasis: "living-organization-scene.v3 deterministic plane",
    },
    {
      key: "mission",
      label: "Mission",
      availability: coverageAvailable(scene.coverage.missions) ? "available" : "unavailable",
      count: scene.deterministic.missions.length,
      summary: "Mission topology, assigned work and participant context.",
      canonicalBasis: scene.coverage.missions,
    },
    {
      key: "flow",
      label: "Flow",
      availability: "available",
      count: scene.deterministic.work_items.length + scene.deterministic.handoffs.length,
      summary: "Structured directed WorkItem topology, lifecycle signals and governed handoffs. GPU fluid/field remains a separate trial.",
      canonicalBasis: "living-organization-scene.v4 WorkItems + organization.work.assigned.v1 projection",
    },
    {
      key: "risk",
      label: "Risk",
      availability: coverageAvailable(scene.coverage.risk_escalations) ? "available" : "unavailable",
      count: scene.deterministic.risk_escalations.length,
      summary: "Open canonical RiskEscalation attention and related friction.",
      canonicalBasis: scene.coverage.risk_escalations,
    },
    {
      key: "autonomy",
      label: "Autonomy",
      availability: "planned",
      count: null,
      summary: "Not projected by scene v3. Authority levels are not treated as autonomy.",
      canonicalBasis: "No scene-safe canonical autonomy-profile lens in M.7.2",
    },
    {
      key: "cost",
      label: "Cost",
      availability: cost && cost.state !== "unavailable" ? "partial" : "unavailable",
      count: cost?.metric_value ?? null,
      summary: cost && cost.state !== "unavailable"
        ? "Available bounded cost signal only; not a complete organization spend ledger."
        : "No canonical organization runtime-cost ledger is available to this scene.",
      canonicalBasis: cost?.canonical_basis ?? scene.coverage.runtime_costs,
    },
    {
      key: "evidence",
      label: "Evidence",
      availability: evidence && evidence.state !== "unavailable" ? "available" : "unavailable",
      count: evidence?.metric_value ?? null,
      summary: "Evidence, VerifiedRules and SourceSnapshot provenance without freshness overclaim.",
      canonicalBasis: evidence?.canonical_basis ?? "Evidence lens source unavailable",
    },
    {
      key: "blockers",
      label: "Blockers",
      availability: coverageAvailable(scene.coverage.blockers) ? "available" : "unavailable",
      count: scene.deterministic.blockers.length,
      summary: "Canonical OrganizationBlocker friction and linked human attention.",
      canonicalBasis: scene.coverage.blockers,
    },
    {
      key: "decisions",
      label: "Decisions",
      availability: "available",
      count: scene.deterministic.decisions.length,
      summary: "ExecutiveDecision authority, supersession, provenance and Owner attention.",
      canonicalBasis: "ExecutiveDecision read-only scene projection",
    },
    {
      key: "performance",
      label: "Performance",
      availability: "planned",
      count: null,
      summary: "No canonical performance aggregate is projected by scene v3; activity volume is not productivity.",
      canonicalBasis: "No M.7.2 canonical performance lens contract",
    },
    {
      key: "incident",
      label: "Incident",
      availability: incident && incident.state !== "unavailable" ? "partial" : "unavailable",
      count: incident?.metric_value ?? null,
      summary: incident && incident.state !== "unavailable"
        ? "Available incident projection."
        : "No canonical Incident model is available to this scene.",
      canonicalBasis: incident?.canonical_basis ?? scene.coverage.incidents,
    },
  ];
}

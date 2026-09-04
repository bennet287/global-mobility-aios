import type { LivingSceneEmployee } from "../live-organization";
import type {
  V2ArchitectureWingKey,
  V2ArchitectureZone,
} from "./owner-organization";

export type V2HqCharacterPlacement = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
  readonly authorityLevel: string;
  readonly semanticState: string;
  readonly wingKey: V2ArchitectureWingKey;
  readonly zoneLabel: string;
  readonly matchedDepartmentKey: string;
  readonly matchedDepartmentLabel: string;
  readonly placementBasis: "canonical-department-zone-mapping";
  readonly presentationOnly: true;
  readonly physicalLocationClaimed: false;
  readonly presenceClaimed: false;
};

export type V2HqUnplacedReason =
  | "unmapped-department"
  | "ambiguous-department-mapping";

export type V2HqUnplacedEmployee = {
  readonly positionKey: string;
  readonly title: string;
  readonly department: string;
  readonly reason: V2HqUnplacedReason;
  readonly limitation: string;
  readonly presentationOnly: true;
  readonly physicalLocationClaimed: false;
  readonly presenceClaimed: false;
};

export type V2HqCharacterLayout = {
  readonly placements: readonly V2HqCharacterPlacement[];
  readonly unplaced: readonly V2HqUnplacedEmployee[];
  readonly presentationOnly: true;
  readonly physicalLocationClaimed: false;
  readonly presenceClaimed: false;
};

type ZoneDepartmentMatch = {
  readonly zone: V2ArchitectureZone;
  readonly department: V2ArchitectureZone["departments"][number];
};

type ZoneMatchResult =
  | { readonly kind: "matched"; readonly match: ZoneDepartmentMatch }
  | { readonly kind: "unmapped" }
  | { readonly kind: "ambiguous"; readonly matchCount: number };

function normalizedDepartment(value: string): string {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function freezePlacement(
  placement: V2HqCharacterPlacement,
): V2HqCharacterPlacement {
  return Object.freeze(placement);
}

function freezeUnplaced(
  employee: V2HqUnplacedEmployee,
): V2HqUnplacedEmployee {
  return Object.freeze(employee);
}

function findMappedZone(
  employee: LivingSceneEmployee,
  zones: readonly V2ArchitectureZone[],
): ZoneMatchResult {
  const employeeDepartment = normalizedDepartment(employee.department);
  if (!employeeDepartment) return Object.freeze({ kind: "unmapped" });

  const matches: ZoneDepartmentMatch[] = [];
  for (const zone of zones) {
    for (const department of zone.departments) {
      const key = normalizedDepartment(department.key);
      const label = normalizedDepartment(department.label);
      if (employeeDepartment === key || employeeDepartment === label) {
        matches.push(Object.freeze({ zone, department }));
      }
    }
  }

  if (matches.length === 0) return Object.freeze({ kind: "unmapped" });
  if (matches.length > 1) {
    return Object.freeze({
      kind: "ambiguous",
      matchCount: matches.length,
    });
  }
  return Object.freeze({ kind: "matched", match: matches[0] });
}

export function buildV2HqCharacterLayout(
  employees: readonly LivingSceneEmployee[],
  zones: readonly V2ArchitectureZone[],
): V2HqCharacterLayout {
  const placements: V2HqCharacterPlacement[] = [];
  const unplaced: V2HqUnplacedEmployee[] = [];

  const sortedEmployees = [...employees].sort((a, b) =>
    a.position_key.localeCompare(b.position_key),
  );

  for (const employee of sortedEmployees) {
    const zoneMatch = findMappedZone(employee, zones);

    if (zoneMatch.kind !== "matched") {
      const ambiguous = zoneMatch.kind === "ambiguous";
      unplaced.push(
        freezeUnplaced({
          positionKey: employee.position_key,
          title: employee.title,
          department: employee.department,
          reason: ambiguous
            ? "ambiguous-department-mapping"
            : "unmapped-department",
          limitation: ambiguous
            ? `Canonical department matched ${zoneMatch.matchCount} presentation-zone mappings. AIOS will not choose a spatial room from an ambiguous mapping.`
            : "No exact canonical department-to-zone mapping matched this rostered employee. AIOS will not invent a spatial room.",
          presentationOnly: true,
          physicalLocationClaimed: false,
          presenceClaimed: false,
        }),
      );
      continue;
    }

    const { zone, department } = zoneMatch.match;
    placements.push(
      freezePlacement({
        positionKey: employee.position_key,
        title: employee.title,
        department: employee.department,
        authorityLevel: employee.authority_level,
        semanticState: employee.semantic_state,
        wingKey: zone.wingKey,
        zoneLabel: zone.label,
        matchedDepartmentKey: department.key,
        matchedDepartmentLabel: department.label,
        placementBasis: "canonical-department-zone-mapping",
        presentationOnly: true,
        physicalLocationClaimed: false,
        presenceClaimed: false,
      }),
    );
  }

  return Object.freeze({
    placements: Object.freeze(placements),
    unplaced: Object.freeze(unplaced),
    presentationOnly: true,
    physicalLocationClaimed: false,
    presenceClaimed: false,
  });
}

export function getV2HqPlacementsForWing(
  layout: V2HqCharacterLayout,
  wingKey: V2ArchitectureWingKey,
): readonly V2HqCharacterPlacement[] {
  return Object.freeze(
    layout.placements.filter((placement) => placement.wingKey === wingKey),
  );
}

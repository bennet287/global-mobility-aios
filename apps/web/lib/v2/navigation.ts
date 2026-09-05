export type OwnerNavLabel =
  | "Home"
  | "Organization"
  | "Missions"
  | "Intelligence"
  | "Evidence"
  | "Decisions"
  | "History";

export type V2NavigationIcon =
  | "home"
  | "organization"
  | "missions"
  | "intelligence"
  | "evidence"
  | "decisions"
  | "history";

export type OwnerNavigationItem = {
  readonly label: OwnerNavLabel;
  readonly icon: V2NavigationIcon;
  readonly href: string | null;
  readonly enabled: boolean;
  readonly description: string;
};

export const ownerNavigation: readonly OwnerNavigationItem[] = Object.freeze([
  { label: "Home", icon: "home", href: "/cockpit/v2", enabled: true, description: "Owner situation and attention" },
  { label: "Organization", icon: "organization", href: "/cockpit/v2/organization", enabled: true, description: "Living HQ, employees and Mission Rooms" },
  { label: "Missions", icon: "missions", href: null, enabled: false, description: "Mission workspace — planned successor slice" },
  { label: "Intelligence", icon: "intelligence", href: null, enabled: false, description: "Intelligence workspace — planned successor slice" },
  { label: "Evidence", icon: "evidence", href: null, enabled: false, description: "Evidence workspace — planned successor slice" },
  { label: "Decisions", icon: "decisions", href: null, enabled: false, description: "Decisions workspace — planned successor slice" },
  { label: "History", icon: "history", href: null, enabled: false, description: "History workspace — planned successor slice" },
]);

export const navigationCommands = Object.freeze([
  { label: "Home", icon: "home" as const, href: "/cockpit/v2", description: "Open AIOS V2 Owner Home" },
  { label: "Organization", icon: "organization" as const, href: "/cockpit/v2/organization", description: "Open the Living Organization workspace" },
  { label: "Structured Cockpit", icon: "organization" as const, href: "/cockpit", description: "Open the existing operational workspace" },
  { label: "Decision Explorer", icon: "decisions" as const, href: "/cockpit/decisions", description: "Inspect decisions in the structured workspace" },
  { label: "Live Organization & Replay", icon: "history" as const, href: "/cockpit/live-organization", description: "Open the existing live and temporal workspace" },
]);

export function filterNavigationCommands(query: string) {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return navigationCommands.filter((item) => {
    const text = `${item.label} ${item.description}`.toLocaleLowerCase();
    return words.every((word) => text.includes(word));
  });
}

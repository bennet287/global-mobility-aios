export type OwnerNavLabel = "Home" | "Organization" | "Missions" | "Intelligence" | "Evidence" | "Decisions" | "History";

export const ownerNavigation = [
  { label: "Home", icon: "home", href: "/cockpit/v2", description: "Owner situation and attention" },
  { label: "Organization", icon: "organization", href: "/cockpit/v2/organization", description: "Living HQ, employees and Mission Rooms" },
  { label: "Missions", icon: "missions", href: "/cockpit/v2/missions", description: "Open missions workspace" },
  { label: "Intelligence", icon: "intelligence", href: "/cockpit/v2/intelligence", description: "Open intelligence workspace" },
  { label: "Evidence", icon: "evidence", href: "/cockpit/v2/evidence", description: "Open evidence workspace" },
  { label: "Decisions", icon: "decisions", href: "/cockpit/v2/decisions", description: "Open decisions workspace" },
  { label: "History", icon: "history", href: "/cockpit/v2/history", description: "Open history workspace" },
] as const;

// Explicit existing destinations only. Navigation grants no backend authority.
export const navigationCommands = [
  ...ownerNavigation.filter((item) => item.href !== null),
  { label: "Structured Cockpit", icon: "organization", href: "/cockpit", description: "Open the existing operational workspace" },
  { label: "Decision Explorer", icon: "decisions", href: "/cockpit/decisions", description: "Inspect decisions in the structured workspace" },
  { label: "Live Organization & Replay", icon: "history", href: "/cockpit/live-organization", description: "Open the existing live and temporal workspace" },
] as const;

export function filterNavigationCommands(query: string) {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return navigationCommands.filter((item) => {
    const text = `${item.label} ${item.description}`.toLocaleLowerCase();
    return words.every((word) => text.includes(word));
  });
}

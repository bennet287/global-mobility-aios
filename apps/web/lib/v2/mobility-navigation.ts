export type MobilityNavLabel = "Overview" | "My Case" | "Documents" | "Timeline" | "Messages";

export type MobilityNavigationIcon = "home" | "work" | "evidence" | "history" | "communication";

export type MobilityNavigationItem = Readonly<{
  label: MobilityNavLabel;
  icon: MobilityNavigationIcon;
  href: string | null;
  enabled: boolean;
  description: string;
}>;

export const mobilityNavigation: readonly MobilityNavigationItem[] = Object.freeze([
  {
    label: "Overview",
    icon: "home",
    href: "/my-mobility",
    enabled: true,
    description: "Case-first overview, next action and privacy-safe journey context",
  },
  {
    label: "My Case",
    icon: "work",
    href: "/portal",
    enabled: true,
    description: "Secure access to protected personal case records and reviewed mobility state",
  },
  {
    label: "Documents",
    icon: "evidence",
    href: "/portal/documents",
    enabled: true,
    description: "Secure client-safe document room and evidence status",
  },
  {
    label: "Timeline",
    icon: "history",
    href: "/portal/timeline",
    enabled: true,
    description: "Client-safe milestones, dated records and waiting states",
  },
  {
    label: "Messages",
    icon: "communication",
    href: "/portal/messages",
    enabled: true,
    description: "Secure communication guidance with explicit delivered-history boundaries",
  },
]);
